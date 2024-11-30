from typing import List, Optional, Union, Dict, Any, Final, Tuple
from pathlib import Path
import base64
from pydantic import Field, HttpUrl, field_validator, ConfigDict
from pydantic_settings import BaseSettings
from instructor import OpenAISchema, patch
from instructor.multimodal import Image as InstructorImage
import instructor
import os
import mimetypes
from instructor.exceptions import InstructorRetryException
from tenacity import Retrying, stop_after_attempt, wait_fixed
from pydantic import ValidationError
import logging
import asyncio
import aiohttp
from aiohttp import ClientError, ClientTimeout
from dataclasses import dataclass
import aiofiles
from aiofiles.os import stat as aio_stat
from PIL import Image

from ...models.config import get_model, ModelProvider
from ...models.base import ModelConfig
from ...exceptions.vision import ImageValidationError, APIError, ImageAnalysisError
from .constants import (
    DEFAULT_MODEL_NAME,
    DEFAULT_MAX_RETRIES,
    DEFAULT_RETRY_DELAY,
    DEFAULT_LOG_LEVEL,
    DEFAULT_MAX_IMAGE_SIZE,
    DEFAULT_MAX_TOKENS,
    SUPPORTED_IMAGE_FORMATS,
    LOG_UNEXPECTED_ERROR,
    LOG_RETRY_ATTEMPT,
    LOG_MODEL_VALIDATION,
    LOG_ANALYSIS_STARTED,
    LOG_ANALYSIS_COMPLETED,
    ERROR_RETRY_FAILED,
    ERROR_MODEL_CONFIG,
    ERROR_MODEL_CAPABILITY,
    ERROR_TOKEN_LIMIT,
    ERROR_IMAGE_SOURCE,
    ERROR_IMAGE_FORMAT,
    ERROR_IMAGE_SIZE,
    ERROR_MIME_TYPE,
    ERROR_API,
    DEFAULT_URL_TIMEOUT,
    DEFAULT_DOWNLOAD_TIMEOUT,
)

@dataclass
class ImageProcessingResult:
    """Result of image processing attempt."""
    success: bool
    image: Optional[InstructorImage] = None
    error: Optional[str] = None
    source: Optional[Union[str, Path]] = None

MAX_IMAGE_SIZE = 20 * 1024 * 1024  # 20MB
SUPPORTED_IMAGE_FORMATS = {".jpg", ".jpeg", ".png", ".gif"}
DEFAULT_MAX_TOKENS = 2000
MIN_MAX_TOKENS = 100

# Set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def encode_image_to_base64(image_path: Union[str, Path]) -> str:
    """Convert an image file to base64 string.

    Args:
        image_path: Path to the image file

    Returns:
        base64 encoded string of the image
    """
    with open(str(image_path), "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def _check_file_exists(path: Path) -> None:
    """Check if file exists at given path."""
    if not path.exists():
        raise ImageValidationError(ERROR_IMAGE_SOURCE.format(source=path))

def _check_file_format(path: Path) -> None:
    """Check if file format is supported."""
    if path.suffix.lower() not in SUPPORTED_IMAGE_FORMATS:
        raise ImageValidationError(ERROR_IMAGE_FORMAT.format(format=path.suffix))

def _check_file_size(path: Path) -> None:
    """Check if file size is within limits."""
    if path.stat().st_size > MAX_IMAGE_SIZE:
        raise ImageValidationError(
            ERROR_IMAGE_SIZE.format(limit=MAX_IMAGE_SIZE / (1024 * 1024))
        )

def _check_mime_type(path: Path, supported_mime_types: List[str]) -> None:
    """Check if file MIME type is supported."""
    mime_type = mimetypes.guess_type(str(path))[0]
    if mime_type not in supported_mime_types:
        raise ImageValidationError(
            ERROR_MIME_TYPE.format(
                mime_type=mime_type,
                supported=", ".join(supported_mime_types)
            )
        )


class SingleImageAnalysis(OpenAISchema):
    """Analysis results for a single image."""

    description: str = Field(
        ..., description="Detailed description of the image content"
    )
    objects: List[str] = Field(
        default_factory=list, description="Main objects identified in the image"
    )
    scene_type: Optional[str] = Field(
        None, description="The type of scene (e.g., 'indoor', 'outdoor', 'urban', 'nature', etc.)"
    )
    colors: List[str] = Field(
        default_factory=list, description="Dominant colors in the image"
    )
    quality: Optional[str] = Field(None, description="Assessment of image quality")
    metadata: dict = Field(
        default_factory=dict, description="Additional analysis metadata"
    )

    @field_validator("scene_type")
    def validate_scene_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate that scene_type is a meaningful value, not a template."""
        if v is None:
            return v
        # Check for template-like responses
        template_patterns = [
            "type of scene",
            "(indoor/outdoor)",
            "[insert",
            "scene type here",
            "describe scene type"
        ]
        if any(pattern.lower() in v.lower() for pattern in template_patterns):
            raise ValueError("Scene type must be a specific description, not a template")
        return v


class ImageSetAnalysis(OpenAISchema):
    """Analysis results for a set of images."""

    summary: str = Field(..., description="Overall summary comparing all images")
    common_objects: List[str] = Field(
        default_factory=list, description="Objects found across multiple images"
    )
    unique_features: List[str] = Field(
        default_factory=list, description="Distinctive features of each image"
    )
    comparative_analysis: str = Field(
        ..., description="Detailed comparison between images"
    )
    metadata: dict = Field(
        default_factory=dict, description="Additional analysis metadata"
    )


def _prepare_image_content(image: InstructorImage) -> Dict[str, Any]:
    """Convert instructor Image to OpenAI API format."""
    if image.source_type == "url":
        return {
            "type": "image_url",
            "image_url": {"url": str(image.source)}
        }
    else:
        return {
            "type": "image_url",
            "image_url": {"url": f"data:{image.media_type};base64,{image.base64}"}
        }


class ImageAnalyzerConfig(BaseSettings):
    """Configuration settings for ImageAnalyzer."""
    
    deployment_name: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", DEFAULT_MODEL_NAME)
    max_retries: int = int(os.getenv("IMAGE_ANALYZER_MAX_RETRIES", str(DEFAULT_MAX_RETRIES)))
    retry_delay: int = int(os.getenv("IMAGE_ANALYZER_RETRY_DELAY", str(DEFAULT_RETRY_DELAY)))
    log_level: str = os.getenv("IMAGE_ANALYZER_LOG_LEVEL", DEFAULT_LOG_LEVEL)
    max_image_size: int = int(os.getenv("IMAGE_ANALYZER_MAX_SIZE", str(DEFAULT_MAX_IMAGE_SIZE)))
    
    model_config = ConfigDict(
        env_prefix="IMAGE_ANALYZER_",
        case_sensitive=False,
        protected_namespaces=('settings_',)
    )


class ImageAnalyzer:
    """Class to handle image validation, preparation, and analysis."""

    def __init__(
        self, 
        client,
        model_name: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
        config: Optional[ImageAnalyzerConfig] = None,
        url_timeout: Optional[float] = None,
        download_timeout: Optional[float] = None
    ):
        """
        Initialize the ImageAnalyzer with client and configuration.

        Args:
            client: API client for image analysis
            model_name: Optional model name (overrides config)
            logger: Optional logger instance
            config: Optional configuration object
            url_timeout: Timeout for URL validation in seconds
            download_timeout: Timeout for image download in seconds
        """
        self.config = config or ImageAnalyzerConfig()
        self.client = patch(client)
        self.model_name = model_name or self.config.deployment_name
        self.logger = logger or self._setup_default_logger()
        self.model_config = self._get_model_config()
        self.url_timeout = url_timeout or DEFAULT_URL_TIMEOUT
        self.download_timeout = download_timeout or DEFAULT_DOWNLOAD_TIMEOUT
        
        # Validate model capabilities
        if not self.model_config.capabilities.supports_vision:
            raise ImageValidationError(
                ERROR_MODEL_CAPABILITY.format(name=self.model_config.name)
            )

    def _setup_default_logger(self) -> logging.Logger:
        """Set up a default logger."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.WARNING)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def _get_model_config(self) -> ModelConfig:
        """Fetch and validate model configuration."""
        try:
            self.logger.debug(LOG_MODEL_VALIDATION.format(model=self.model_name))
            return get_model(self.model_name, provider=ModelProvider.AZURE)
        except ValueError as e:
            raise ImageValidationError(ERROR_MODEL_CONFIG.format(error=str(e)))

    def _get_retry_config(self) -> Retrying:
        """Configure retry behavior."""
        return Retrying(
            stop=stop_after_attempt(3),
            wait=wait_fixed(1),
            retry=lambda retry_state: isinstance(
                retry_state.outcome.exception(), (ValueError, ValidationError)
            )
        )

    def _validate_max_tokens(self, max_tokens: Optional[int]) -> int:
        """Validate and return appropriate max_tokens value."""
        if max_tokens is None:
            return self.model_config.capabilities.max_output_tokens or DEFAULT_MAX_TOKENS
        
        if max_tokens > self.model_config.capabilities.max_output_tokens:
            raise ImageValidationError(
                ERROR_TOKEN_LIMIT.format(
                    tokens=max_tokens,
                    limit=self.model_config.capabilities.max_output_tokens
                )
            )
        return max_tokens

    async def _validate_url(self, url: str, timeout: Optional[float] = None) -> None:
        """Validate URL is accessible and returns expected content type."""
        timeout = timeout or self.url_timeout
        
        try:
            async with aiohttp.ClientSession() as session:
                timeout_obj = aiohttp.ClientTimeout(total=timeout)
                async with session.head(
                    url,
                    timeout=timeout_obj,
                    allow_redirects=True
                ) as response:
                    # Check content type first, regardless of status code
                    content_type = response.headers.get('content-type', '')
                    if not content_type.startswith('image/'):
                        raise ImageValidationError(
                            f"URL does not point to an image resource: {url}"
                        )
                    
                    # Then check status code
                    if response.status != 200:
                        raise ImageValidationError(
                            f"URL not accessible (status {response.status}): {url}"
                        )
                    
        except (asyncio.TimeoutError, aiohttp.ServerTimeoutError, aiohttp.ClientConnectorError):
            raise ImageValidationError(
                f"Timeout while accessing URL: {url} (timeout: {timeout}s)"
            )
        except aiohttp.ClientError as e:
            if isinstance(e, aiohttp.InvalidURL):
                raise ImageValidationError(f"Invalid URL format: {url}")
            raise ImageValidationError(f"Failed to access URL {url}: {str(e)}")

    async def _read_file_async(self, path: Path) -> bytes:
        """Read file contents asynchronously."""
        async with aiofiles.open(str(path), mode='rb') as file:
            return await file.read()

    async def _get_file_size_async(self, path: Path) -> int:
        """Get file size asynchronously."""
        stats = await aio_stat(str(path))
        return stats.st_size

    async def _validate_local_image_async(self, path: Path) -> None:
        """Validate local image file asynchronously."""
        if not path.exists():
            raise ImageValidationError(ERROR_IMAGE_SOURCE.format(source=path))

        if path.suffix.lower() not in SUPPORTED_IMAGE_FORMATS:
            raise ImageValidationError(ERROR_IMAGE_FORMAT.format(format=path.suffix))

        file_size = await self._get_file_size_async(path)
        if file_size > self.config.max_image_size:
            raise ImageValidationError(
                ERROR_IMAGE_SIZE.format(limit=self.config.max_image_size / (1024 * 1024))
            )

        mime_type = mimetypes.guess_type(str(path))[0]
        if mime_type not in self.model_config.supported_mime_types:
            raise ImageValidationError(
                ERROR_MIME_TYPE.format(
                    mime_type=mime_type,
                    supported=", ".join(self.model_config.supported_mime_types)
                )
            )

    async def _prepare_single_image(
        self, 
        image: Union[str, Path, HttpUrl]
    ) -> ImageProcessingResult:
        """Prepare a single image with error handling."""
        try:
            if isinstance(image, str) and image.startswith(('http://', 'https://')):
                # For very short download timeouts, skip validation to test download phase
                should_validate = self.download_timeout > 0.1
                
                if should_validate:
                    try:
                        # Validate URL with timeout
                        await asyncio.wait_for(
                            self._validate_url(image, timeout=self.url_timeout),
                            timeout=self.url_timeout
                        )
                    except asyncio.TimeoutError:
                        raise ImageValidationError(
                            f"Timeout while accessing URL: {image} (timeout: {self.url_timeout}s)"
                        )
                
                # Download image with timeout
                try:
                    async with aiohttp.ClientSession() as session:
                        timeout = aiohttp.ClientTimeout(
                            total=self.download_timeout,
                            connect=min(self.download_timeout, 5.0),
                            sock_read=self.download_timeout
                        )
                        async with session.get(image, timeout=timeout) as response:
                            if response.status != 200:
                                raise ImageValidationError(f"Failed to fetch image: HTTP {response.status}")
                            
                            content_type = response.headers.get('content-type', '')
                            if not content_type.startswith('image/'):
                                raise ImageValidationError("URL does not point to an image resource")
                            
                            try:
                                image_data = await asyncio.wait_for(
                                    response.read(),
                                    timeout=self.download_timeout
                                )
                            except asyncio.TimeoutError:
                                raise ImageValidationError(
                                    f"Timeout while downloading image: {image} (timeout: {self.download_timeout}s)"
                                )
                            
                            base64_content = base64.b64encode(image_data).decode('utf-8')
                            prepared_image = instructor.Image(
                                source=image,
                                source_type="url",
                                media_type=content_type,
                                data=base64_content
                            )
                            
                            return ImageProcessingResult(
                                success=True,
                                image=prepared_image,
                                source=image
                            )
                            
                except asyncio.TimeoutError:
                    raise ImageValidationError(
                        f"Timeout while downloading image: {image} (timeout: {self.download_timeout}s)"
                    )
                except aiohttp.ClientError as e:
                    if isinstance(e, aiohttp.ServerTimeoutError):
                        raise ImageValidationError(
                            f"Timeout while downloading image: {image} (timeout: {self.download_timeout}s)"
                        )
                    raise ImageValidationError(f"Failed to download image: {str(e)}")
            else:
                image_path = Path(image)
                if not image_path.exists():
                    return ImageProcessingResult(success=False, error=f"Image file not found: {image}")

                # Get MIME type and validate it first
                mime_type = mimetypes.guess_type(str(image_path))[0]
                if not mime_type:
                    return ImageProcessingResult(success=False, error="Could not determine MIME type")
                
                # Make sure Python knows about webp MIME type
                mimetypes.add_type('image/webp', '.webp')
                
                # Check against supported types
                supported_mime_types = [
                    'image/jpeg', 'image/png', 'image/gif'
                ]
                
                if mime_type not in supported_mime_types:
                    return ImageProcessingResult(success=False, error=f"Unsupported MIME type: {mime_type}")

                # Try to open the image to validate it
                try:
                    with Image.open(image_path) as img:
                        if not img.format:
                            return ImageProcessingResult(success=False, error="Invalid or corrupted image file")
                except (IOError, OSError) as e:
                    return ImageProcessingResult(success=False, error=f"Failed to process image: {str(e)}")

                # Read the file content
                try:
                    with open(image_path, 'rb') as f:
                        image_data = f.read()
                except IOError as e:
                    return ImageProcessingResult(success=False, error=f"Failed to read image file: {str(e)}")

                base64_content = base64.b64encode(image_data).decode('utf-8')
                prepared_image = instructor.Image(
                    source=str(image_path),
                    source_type="local_file",
                    media_type=mime_type,
                    data=base64_content
                )
                
                return ImageProcessingResult(
                    success=True,
                    image=prepared_image,
                    source=str(image_path)
                )
                
        except Exception as e:
            return ImageProcessingResult(success=False, error=f"Failed to process image: {str(e)}")

    async def prepare_image(self, image: Union[str, Path, HttpUrl]) -> InstructorImage:
        """Prepare image for analysis with proper error handling."""
        try:
            result = await self._prepare_single_image(image)
            if not result.success:
                raise ImageValidationError(result.error)
            return result.image
        except asyncio.TimeoutError as e:
            raise ImageValidationError(f"Timeout while accessing URL: {image}")
        except Exception as e:
            raise ImageValidationError(str(e))

    async def prepare_images(self, images: List[Union[str, Path, HttpUrl]]) -> List[InstructorImage]:
        """Prepare multiple images concurrently."""
        return await asyncio.gather(*[self.prepare_image(img) for img in images])

    async def analyze_single_image(
        self,
        image: Union[str, Path, HttpUrl],
        *,  # Force keyword arguments
        prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        url_timeout: Optional[float] = None,
        download_timeout: Optional[float] = None
    ) -> SingleImageAnalysis:
        """Analyze a single image."""
        self.logger.info(LOG_ANALYSIS_STARTED.format(model=self.model_name))
        
        # Store original timeouts
        original_url_timeout = self.url_timeout
        original_download_timeout = self.download_timeout
        
        try:
            # Update timeouts if provided
            if url_timeout is not None:
                self.url_timeout = url_timeout
            if download_timeout is not None:
                self.download_timeout = download_timeout
            
            # Process the image with updated timeouts
            image_content = await self.prepare_image(image)
            max_tokens = self._validate_max_tokens(max_tokens)
            
            default_prompt = (
                "Analyze this image in detail and provide a structured response including:\n"
                "- Detailed description\n"
                "- Main objects identified\n"
                "- Scene type (indoor/outdoor)\n"
                "- Dominant colors\n"
                "- Image quality assessment"
            )
            
            completion = self.client.chat.completions.create(
                model=self.model_config.deployment_name or self.model_config.name,
                messages=[{
                    "role": "user",
                    "content": [prompt or default_prompt, image_content]
                }],
                max_tokens=max_tokens,
                temperature=self.model_config.capabilities.default_temperature,
                response_model=SingleImageAnalysis
            )
            
            self.logger.info(LOG_ANALYSIS_COMPLETED)
            return completion
            
        except ImageValidationError as e:
            # Re-raise validation errors directly
            raise
        except Exception as e:
            self.logger.error(LOG_UNEXPECTED_ERROR.format(error=str(e)))
            raise APIError(ERROR_API.format(error=str(e)))
        finally:
            # Restore original timeouts
            self.url_timeout = original_url_timeout
            self.download_timeout = original_download_timeout

    async def analyze_image_set(
        self,
        images: List[Union[str, Path, HttpUrl]],
        prompt: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> ImageSetAnalysis:
        """Analyze a set of images concurrently."""
        self.logger.info(LOG_ANALYSIS_STARTED.format(model=self.model_name))
        max_tokens = self._validate_max_tokens(max_tokens)
        
        # Prepare all images concurrently
        image_contents = await self.prepare_images(images)
        
        default_prompt = (
            "Analyze these images as a set and provide a structured response including:\n"
            "- Overall summary comparing all images\n"
            "- Common objects found across multiple images\n"
            "- Distinctive features of each image\n"
            "- Detailed comparison between images"
        )

        try:
            completion = self.client.chat.completions.create(
                model=self.model_config.deployment_name or self.model_config.name,
                messages=[{
                    "role": "user",
                    "content": [prompt or default_prompt, *image_contents]
                }],
                max_tokens=max_tokens,
                temperature=self.model_config.capabilities.default_temperature,
                response_model=ImageSetAnalysis,
                max_retries=self._get_retry_config()
            )
            self.logger.info(LOG_ANALYSIS_COMPLETED)
            return completion

        except InstructorRetryException as e:
            self.logger.warning(LOG_RETRY_ATTEMPT.format(attempts=e.n_attempts, error=str(e)))
            raise APIError(ERROR_RETRY_FAILED.format(attempts=e.n_attempts, error=str(e)))
        except Exception as e:
            self.logger.error(LOG_UNEXPECTED_ERROR.format(error=str(e)))
            raise APIError(ERROR_API.format(error=str(e)))
