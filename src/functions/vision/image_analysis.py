from typing import List, Optional, Union, Dict, Any
from pathlib import Path
import base64
from pydantic import Field, HttpUrl, field_validator
from instructor import OpenAISchema, patch
from instructor.multimodal import Image as InstructorImage
import instructor
import os
import mimetypes
from instructor.exceptions import InstructorRetryException

from ...models.config import get_model, ModelProvider
from ...models.base import ModelConfig
from ...exceptions.vision import ImageValidationError, APIError, ImageAnalysisError

MAX_IMAGE_SIZE = 20 * 1024 * 1024  # 20MB
SUPPORTED_IMAGE_FORMATS = {".jpg", ".jpeg", ".png", ".gif"}
DEFAULT_MAX_TOKENS = 2000
MIN_MAX_TOKENS = 100


def encode_image_to_base64(image_path: Union[str, Path]) -> str:
    """Convert an image file to base64 string.

    Args:
        image_path: Path to the image file

    Returns:
        base64 encoded string of the image
    """
    with open(str(image_path), "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def validate_image_file(image_path: Union[str, Path]) -> bool:
    """Validate image file size and format."""
    path = Path(image_path)
    if not path.exists():
        raise ValueError(f"Image file not found: {image_path}")
    if path.suffix.lower() not in SUPPORTED_IMAGE_FORMATS:
        raise ValueError(f"Unsupported image format: {path.suffix}")
    if path.stat().st_size > MAX_IMAGE_SIZE:
        raise ValueError(
            f"Image file too large: {path.stat().st_size / 1024 / 1024:.1f}MB"
        )
    return True

def validate_image_source(
    image_path: Union[str, Path], supported_mime_types: List[str]
) -> None:
    """
    Validates image source for format and size.
    Raises ImageValidationError if validation fails.

    Args:
        image_path: Path or URL of the image.
        supported_mime_types: List of MIME types supported by the model.

    Raises:
        ImageValidationError: If the image is invalid or unsupported.
    """
    path = Path(image_path)
    if not path.exists() and not str(image_path).startswith("http"):
        raise ImageValidationError(f"Image source not found: {image_path}")

    if not str(image_path).startswith("http"):
        # Validate local file
        if path.suffix.lower() not in SUPPORTED_IMAGE_FORMATS:
            raise ImageValidationError(f"Unsupported image format: {path.suffix}")
        if path.stat().st_size > MAX_IMAGE_SIZE:
            raise ImageValidationError(
                f"Image size exceeds the limit of {MAX_IMAGE_SIZE / (1024 * 1024)}MB"
            )
        # Validate MIME type
        mime_type = mimetypes.guess_type(str(path))[0]
        if mime_type not in supported_mime_types:
            raise ImageValidationError(
                f"Unsupported MIME type {mime_type}. Supported types: {', '.join(supported_mime_types)}"
            )
    else:
        # For URLs, validate MIME type (e.g., using mimetypes or HTTP headers)
        mime_type = mimetypes.guess_type(str(image_path))[0]
        if mime_type not in supported_mime_types:
            raise ImageValidationError(
                f"Unsupported MIME type {mime_type} for URL {image_path}. "
                f"Supported types: {', '.join(supported_mime_types)}"
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


async def analyze_images(
    client,
    images: Union[str, Path, HttpUrl, List[Union[str, Path, HttpUrl]]],
    prompt: Optional[str] = None,
    max_tokens: Optional[int] = None,
    model_name: Optional[str] = None,
) -> SingleImageAnalysis:
    """Analyzes one or more images with optional custom prompt."""
    # Get model configuration
    model_name = model_name or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
    try:
        model_config = get_model(model_name, provider=ModelProvider.AZURE)
    except ValueError as e:
        raise ImageValidationError(f"Invalid model configuration: {e}")

    # Validate model capabilities
    if not model_config.capabilities.supports_vision:
        raise ImageValidationError(
            f"Model {model_config.name} does not support vision capabilities"
        )

    # Token validation
    if max_tokens is None:
        max_tokens = model_config.capabilities.max_output_tokens or DEFAULT_MAX_TOKENS
    elif max_tokens > model_config.capabilities.max_output_tokens:
        raise ImageValidationError(
            f"max_tokens ({max_tokens}) exceeds model limit "
            f"({model_config.capabilities.max_output_tokens})"
        )

    # Convert to list if single image
    if not isinstance(images, list):
        images = [images]

    # Validate and convert images to instructor format
    instructor_images = []
    for img in images:
        validate_image_source(img, model_config.supported_mime_types)
        if str(img).startswith("http"):
            instructor_images.append(instructor.Image.from_url(str(img)))
        else:
            instructor_images.append(instructor.Image.from_path(str(img)))

    default_prompt = (
        "Analyze this image in detail and provide a structured response including:\n"
        "- Detailed description\n"
        "- Main objects identified\n"
        "- Scene type (indoor/outdoor)\n"
        "- Dominant colors\n"
        "- Image quality assessment"
    )

    try:
        patched_client = patch(client)
        completion = patched_client.chat.completions.create(
            model=model_config.deployment_name or model_config.name,
            messages=[
                {
                    "role": "user",
                    "content": [prompt or default_prompt],
                    "images": instructor_images,
                }
            ],
            max_tokens=max_tokens,
            temperature=model_config.capabilities.default_temperature,
            response_model=SingleImageAnalysis,
        )

        return completion

    except Exception as e:
        raise APIError(f"Error analyzing image: {str(e)}")

async def interpretImages(
    client, images: List[Union[str, Path, HttpUrl]], prompt: Optional[str] = None
) -> List[SingleImageAnalysis]:
    """Analyzes multiple images individually."""
    results = []
    for image in images:
        # Added await here for testing purposes
        result = await analyze_images(client, image, prompt)
        results.append(result)
    return results


async def interpretImageSet(
    client,
    images: List[Union[str, Path, HttpUrl]],
    prompt: Optional[str] = None,
    model_name: Optional[str] = None,
) -> ImageSetAnalysis:
    """Analyzes multiple images as a set.

    Args:
        client: The OpenAI client instance
        images: List of images to analyze
        prompt: Optional custom prompt
        model_name: Specific model to use. If None, uses environment default
    """
    # Get model configuration
    model_name = model_name or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4-vision")
    try:
        model_config = get_model(model_name, provider=ModelProvider.AZURE)
    except ValueError as e:
        raise ImageValidationError(f"Invalid model configuration: {e}")

    # Validate model capabilities
    if not model_config.capabilities.supports_vision:
        raise ImageValidationError(
            f"Model {model_config.name} does not support vision capabilities"
        )

    patched_client = patch(client)

    # Convert all images to instructor format with validation
    instructor_images = []
    for img in images:
        if isinstance(img, (str, Path)) and (
            Path(img).exists() or str(img).startswith("http")
        ):
            # Validate file type against model's supported formats
            if not str(img).startswith("http"):
                file_type = mimetypes.guess_type(str(img))[0]
                if file_type not in model_config.supported_mime_types:
                    raise ImageValidationError(
                        f"Unsupported image type {file_type}. "
                        f"Supported types: {', '.join(model_config.supported_mime_types)}"
                    )

            if str(img).startswith("http"):
                instructor_images.append(instructor.Image.from_url(str(img)))
            else:
                instructor_images.append(instructor.Image.from_path(str(img)))
        else:
            raise ImageValidationError(f"Invalid image source: {img}")

    default_prompt = (
        "Analyze these images as a set and provide a comparative analysis including:\n"
        "- Overall summary of all images\n"
        "- Common objects or themes\n"
        "- Unique features of each image\n"
        "- Detailed comparison between images"
    )

    try:
        completion = patched_client.chat.completions.create(
            model=model_config.deployment_name or model_config.name,
            messages=[
                {
                    "role": "user",
                    "content": [prompt or default_prompt],
                    "images": instructor_images,
                }
            ],
            max_tokens=model_config.capabilities.max_output_tokens,
            temperature=model_config.capabilities.default_temperature,
            response_model=ImageSetAnalysis,
        )

        return completion

    except Exception as e:
        raise APIError(f"Error analyzing image set: {str(e)}")
