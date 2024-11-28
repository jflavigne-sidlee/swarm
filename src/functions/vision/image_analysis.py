from typing import List, Optional, Union, Dict, Any, Final
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
    MIN_MAX_TOKENS,
    SUPPORTED_IMAGE_FORMATS,
    LOG_UNEXPECTED_ERROR,
    LOG_RETRY_ATTEMPT,
    LOG_IMAGE_VALIDATION,
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
)

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
        config: Optional[ImageAnalyzerConfig] = None
    ):
        self.config = config or ImageAnalyzerConfig()
        self.client = patch(client)
        self.model_name = model_name or self.config.deployment_name
        self.logger = logger or self._setup_default_logger()
        self.model_config = self._get_model_config()
        
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

    def validate_image(self, image_path: Union[str, Path]) -> None:
        """Validate image file for size, format, and MIME type."""
        path = Path(image_path)
        
        # Skip file system checks for URLs
        if not str(image_path).startswith("http"):
            _check_file_exists(path)
            _check_file_format(path)
            _check_file_size(path)
            _check_mime_type(path, self.model_config.supported_mime_types)

    async def prepare_image(self, image: Union[str, Path, HttpUrl]) -> InstructorImage:
        """Prepare a single image for analysis asynchronously."""
        self.validate_image(image)
        if str(image).startswith("http"):
            return await instructor.Image.from_url_async(str(image))
        return await instructor.Image.from_path_async(str(image))

    async def prepare_images(self, images: List[Union[str, Path, HttpUrl]]) -> List[InstructorImage]:
        """Prepare multiple images concurrently."""
        return await asyncio.gather(*[self.prepare_image(img) for img in images])

    async def analyze_single_image(
        self,
        image: Union[str, Path, HttpUrl],
        prompt: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> SingleImageAnalysis:
        """Analyze a single image."""
        self.logger.info(LOG_ANALYSIS_STARTED.format(model=self.model_name))
        image_content = self.prepare_image(image)
        max_tokens = self._validate_max_tokens(max_tokens)

        default_prompt = (
            "Analyze this image in detail and provide a structured response including:\n"
            "- Detailed description\n"
            "- Main objects identified\n"
            "- Scene type (indoor/outdoor)\n"
            "- Dominant colors\n"
            "- Image quality assessment"
        )

        try:
            completion = self.client.chat.completions.create(
                model=self.model_config.deployment_name or self.model_config.name,
                messages=[{
                    "role": "user",
                    "content": [prompt or default_prompt, image_content]
                }],
                max_tokens=max_tokens,
                temperature=self.model_config.capabilities.default_temperature,
                response_model=SingleImageAnalysis,
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
