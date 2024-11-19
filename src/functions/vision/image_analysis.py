from typing import List, Optional, Union
from pathlib import Path
import base64
from pydantic import Field, HttpUrl
from instructor import OpenAISchema
from instructor.multimodal import Image as InstructorImage
import instructor
import os

MAX_IMAGE_SIZE = 20 * 1024 * 1024  # 20MB
SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.gif'}
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
        raise ValueError(f"Image file too large: {path.stat().st_size / 1024 / 1024:.1f}MB")
    return True

class SingleImageAnalysis(OpenAISchema):
    """Analysis results for a single image."""
    description: str = Field(..., description="Detailed description of the image content")
    objects: List[str] = Field(default_factory=list, description="Main objects identified in the image")
    scene_type: Optional[str] = Field(None, description="Type of scene (indoor, outdoor, etc.)")
    colors: List[str] = Field(default_factory=list, description="Dominant colors in the image")
    quality: Optional[str] = Field(None, description="Assessment of image quality")
    metadata: dict = Field(default_factory=dict, description="Additional analysis metadata")

class ImageSetAnalysis(OpenAISchema):
    """Analysis results for a set of images."""
    summary: str = Field(..., description="Overall summary comparing all images")
    common_objects: List[str] = Field(default_factory=list, description="Objects found across multiple images")
    unique_features: List[str] = Field(default_factory=list, description="Distinctive features of each image")
    comparative_analysis: str = Field(..., description="Detailed comparison between images")
    metadata: dict = Field(default_factory=dict, description="Additional analysis metadata")

async def analyze_images(
    client,
    images: Union[str, Path, HttpUrl, List[Union[str, Path, HttpUrl]]],
    prompt: Optional[str] = None,
    max_tokens: int = 2000
) -> SingleImageAnalysis:
    """Analyzes one or more images with optional custom prompt.
    
    Args:
        client: The OpenAI client instance
        images: Single image or list of images to analyze. Can be local paths or URLs
        prompt: Optional custom prompt for analysis. If None, uses default prompt
        max_tokens: Maximum tokens for response (default: 2000, min: 100, max: 4096)
    
    Returns:
        SingleImageAnalysis object containing the analysis results
        
    Raises:
        ImageValidationError: If image validation fails
        APIError: If API call fails
        ValueError: If parameters are invalid
    """
    try:
        # Validate max_tokens
        if not MIN_MAX_TOKENS <= max_tokens <= 4096:
            raise ValueError(f"max_tokens must be between {MIN_MAX_TOKENS} and 4096")

        patched_client = instructor.patch(client)
        
        # Convert to list if single image
        if not isinstance(images, list):
            images = [images]
        
        # Convert images to instructor format
        instructor_images = []
        for img in images:
            if isinstance(img, (str, Path)) and (Path(img).exists() or str(img).startswith('http')):
                if str(img).startswith('http'):
                    instructor_images.append(instructor.Image.from_url(str(img)))
                else:
                    instructor_images.append(instructor.Image.from_path(str(img)))
            else:
                raise ValueError(f"Invalid image source: {img}")

        default_prompt = (
            "Analyze this image in detail and provide a structured response including:\n"
            "- Detailed description\n"
            "- Main objects identified\n"
            "- Scene type (indoor/outdoor)\n"
            "- Dominant colors\n"
            "- Image quality assessment"
        )

        try:
            completion = patched_client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4-vision"),
                messages=[
                    {
                        "role": "user",
                        "content": [prompt or default_prompt] + instructor_images
                    }
                ],
                max_tokens=max_tokens,
                temperature=0.7,
                response_model=SingleImageAnalysis
            )
            
            return completion

        except Exception as e:
            raise APIError(f"Error analyzing image: {str(e)}")

    except ValueError as e:
        raise ImageValidationError(str(e))
    except Exception as e:
        raise APIError(f"Error analyzing image: {str(e)}")

async def interpretImages(
    client,
    images: List[Union[str, Path, HttpUrl]],
    prompt: Optional[str] = None
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
    prompt: Optional[str] = None
) -> ImageSetAnalysis:
    """Analyzes multiple images as a set."""
    patched_client = instructor.patch(client)
    
    # Convert all images to instructor format
    instructor_images = []
    for img in images:
        if isinstance(img, (str, Path)) and (Path(img).exists() or str(img).startswith('http')):
            if str(img).startswith('http'):
                instructor_images.append(instructor.Image.from_url(str(img)))
            else:
                instructor_images.append(instructor.Image.from_path(str(img)))
        else:
            raise ValueError(f"Invalid image source: {img}")

    default_prompt = (
        "Analyze these images as a set and provide a comparative analysis including:\n"
        "- Overall summary of all images\n"
        "- Common objects or themes\n"
        "- Unique features of each image\n"
        "- Detailed comparison between images"
    )

    try:
        # Create the completion without await
        completion = patched_client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4-vision"),
            messages=[
                {
                    "role": "user",
                    "content": [prompt or default_prompt] + instructor_images
                }
            ],
            max_tokens=2000,
            temperature=0.7,
            response_model=ImageSetAnalysis
        )
        
        # Return the completion directly (no await)
        return completion

    except Exception as e:
        raise Exception(f"Error analyzing image set: {str(e)}")