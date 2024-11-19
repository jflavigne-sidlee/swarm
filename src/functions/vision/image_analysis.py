from typing import List, Optional, Union
from pathlib import Path
import base64
from pydantic import Field, HttpUrl
from instructor import OpenAISchema
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


class SingleImageAnalysis(OpenAISchema):
    """Analysis results for a single image."""

    description: str = Field(
        ..., description="Detailed description of the image content"
    )
    objects: List[str] = Field(
        default_factory=list, description="Main objects identified in the image"
    )
    scene_type: Optional[str] = Field(
        None, description="Type of scene (indoor, outdoor, etc.)"
    )
    colors: List[str] = Field(
        default_factory=list, description="Dominant colors in the image"
    )
    quality: Optional[str] = Field(None, description="Assessment of image quality")
    metadata: dict = Field(
        default_factory=dict, description="Additional analysis metadata"
    )


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
    model_name: Optional[str] = None
) -> SingleImageAnalysis:
    """Analyzes one or more images with optional custom prompt.

    Args:
        client: The OpenAI client instance
        images: Single image or list of images to analyze
        prompt: Optional custom prompt for analysis
        max_tokens: Maximum tokens for response. If None, uses model default
        model_name: Specific model to use. If None, uses environment default

    Returns:
        SingleImageAnalysis object containing the analysis results
    """
    # Get model configuration
    model_name = model_name or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4-vision")
    try:
        model_config = get_model(model_name, provider=ModelProvider.AZURE)
    except ValueError as e:
        raise ImageValidationError(f"Invalid model configuration: {e}")

    # Validate model capabilities
    if not model_config.capabilities.vision:  # Check vision capability
        raise ImageValidationError(
            f"Model {model_config.name} does not support vision capabilities"
        )

    # Use model's token limits for validation
    if max_tokens is None:
        max_tokens = model_config.capabilities.max_output_tokens or 2000
    elif max_tokens > model_config.capabilities.max_output_tokens:
        raise ImageValidationError(
            f"max_tokens ({max_tokens}) exceeds model limit "
            f"({model_config.capabilities.max_output_tokens})"
        )

    # Convert to list if single image
    if not isinstance(images, list):
        images = [images]

    # Convert images to instructor format
    instructor_images = []
    for img in images:
        if isinstance(img, (str, Path)) and (Path(img).exists() or str(img).startswith('http')):
            # Validate file type against model's supported formats
            if not str(img).startswith('http'):
                file_type = mimetypes.guess_type(str(img))[0]
                if file_type not in model_config.supported_mime_types:
                    raise ImageValidationError(
                        f"Unsupported image type {file_type}. "
                        f"Supported types: {', '.join(model_config.supported_mime_types)}"
                    )

            if str(img).startswith('http'):
                instructor_images.append(instructor.Image.from_url(str(img)))
            else:
                instructor_images.append(instructor.Image.from_path(str(img)))
        else:
            raise ImageValidationError(f"Invalid image source: {img}")

    default_prompt = (
        "Analyze this image in detail and provide a structured response including:\n"
        "- Detailed description\n"
        "- Main objects identified\n"
        "- Scene type (indoor/outdoor)\n"
        "- Dominant colors\n"
        "- Image quality assessment"
    )

    try:
        patched_client = instructor.patch(client)
        completion = patched_client.chat.completions.create(
            model=model_config.deployment_name or model_config.name,
            messages=[
                {
                    "role": "user",
                    "content": [prompt or default_prompt] + instructor_images,
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
    if not model_config.capabilities.vision:
        raise ImageValidationError(
            f"Model {model_config.name} does not support vision capabilities"
        )

    patched_client = instructor.patch(client)

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
                    "content": [prompt or default_prompt] + instructor_images,
                }
            ],
            max_tokens=model_config.capabilities.max_output_tokens,
            temperature=model_config.capabilities.default_temperature,
            response_model=ImageSetAnalysis,
        )

        return completion

    except Exception as e:
        raise APIError(f"Error analyzing image set: {str(e)}")
