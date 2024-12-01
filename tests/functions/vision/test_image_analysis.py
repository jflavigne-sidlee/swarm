import pytest
from pathlib import Path
import os
from typing import List
from unittest.mock import MagicMock
from src.functions.vision import (
    SingleImageAnalysis,
    ImageSetAnalysis,
    ImageAnalyzer,
    encode_image_to_base64,
)
from src.aoai.client import AOAIClient
from src.models.base import ModelProvider
from src.models.config import get_model
from src.exceptions.vision import ImageValidationError
from instructor.multimodal import Image as InstructorImage


# Test fixtures and utilities
@pytest.fixture
def ai_client() -> AOAIClient:
    """Fixture to create Azure OpenAI client."""
    return AOAIClient.create(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    )


@pytest.fixture
def analyzer(ai_client: AOAIClient) -> ImageAnalyzer:
    """Fixture to create ImageAnalyzer instance."""
    return ImageAnalyzer(ai_client, model_name="gpt-4o")


@pytest.fixture
def test_images() -> List[Path]:
    """Fixture to provide test image paths."""
    test_image_path = Path(__file__).parent / "test_assets" / "test_scene.jpg"
    assert test_image_path.exists(), f"Test image not found at {test_image_path}"
    return [test_image_path]


@pytest.fixture
def test_image_urls() -> List[str]:
    """Fixture to provide test image URLs."""
    return [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/6/68/Pillars_of_creation_2014_HST_WFC3-UVIS_full-res_denoised.jpg/1280px-Pillars_of_creation_2014_HST_WFC3-UVIS_full-res_denoised.jpg"
    ]


def create_mock_client(response_data: dict) -> MagicMock:
    """Utility to create a mock OpenAI client."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = {
        "choices": [{"message": {"content": response_data}}]
    }
    return mock_client


@pytest.mark.asyncio
async def test_analyze_single_local_image(analyzer: ImageAnalyzer, test_images: List[Path]) -> None:
    """Test analyzing a single local image."""
    result = await analyzer.analyze_single_image(test_images[0])
    assert isinstance(result, SingleImageAnalysis)
    assert result.description, "Should provide a description"
    assert len(result.objects) > 0, "Should identify objects"
    
    # Check that scene_type is a meaningful string, not a template response
    assert result.scene_type, "Scene type should not be empty"
    template_patterns = [
        "type of scene",
        "(indoor/outdoor)",
        "[insert",
        "scene type here",
        "describe scene type"
    ]
    assert not any(pattern.lower() in result.scene_type.lower() for pattern in template_patterns), \
        f"Scene type should be descriptive, not a template. Got: {result.scene_type}"


@pytest.mark.asyncio
async def test_analyze_single_url_image(analyzer: ImageAnalyzer, test_image_urls: List[str]) -> None:
    """Test analyzing a single image from URL."""
    result = await analyzer.analyze_single_image(test_image_urls[0])
    assert isinstance(result, SingleImageAnalysis)
    assert result.description, "Should provide a description"


@pytest.mark.parametrize(
    "model_name, expected_exception, error_message",
    [
        ("gpt-4o", None, None),  # Valid model
        ("gpt-4", ImageValidationError, "does not support vision capabilities"),  # Non-vision model
        ("invalid-model", ImageValidationError, "Invalid model configuration"),  # Invalid model
    ],
)
@pytest.mark.asyncio
async def test_analyze_images_with_various_models(
    ai_client: AOAIClient,
    test_images: List[Path],
    model_name: str,
    expected_exception,
    error_message: str
) -> None:
    """Test image analysis with various models."""
    if expected_exception:
        with pytest.raises(expected_exception) as exc_info:
            analyzer = ImageAnalyzer(ai_client, model_name=model_name)
            await analyzer.analyze_single_image(test_images[0])
        assert error_message in str(exc_info.value)
    else:
        analyzer = ImageAnalyzer(ai_client, model_name=model_name)
        result = await analyzer.analyze_single_image(test_images[0])
        assert isinstance(result, SingleImageAnalysis)
        assert result.description, "Should provide a description"


@pytest.mark.asyncio
async def test_mime_type_validation(analyzer: ImageAnalyzer) -> None:
    """Test MIME type validation."""
    # Resolve the path explicitly
    temp_file = (Path(__file__).parent / "test_assets" / "unsupported_format_image.webp").resolve()
    print(f"Resolved path: {temp_file}")

    # Ensure the file exists
    assert temp_file.exists(), f"Test file not found: {temp_file}"

    # Test the behavior with the unsupported .webp file
    with pytest.raises(ImageValidationError) as exc_info:
        await analyzer.analyze_single_image(temp_file)

    # Update the assertion to match the actual error message
    assert "Unsupported image format: .webp" in str(exc_info.value)


@pytest.mark.asyncio
async def test_token_limit_validation(analyzer: ImageAnalyzer, test_images: List[Path]) -> None:
    """Test token limit validation."""
    model_config = get_model("gpt-4o", provider=ModelProvider.AZURE)
    max_tokens = model_config.capabilities.max_output_tokens

    # Test with tokens within limit
    result = await analyzer.analyze_single_image(test_images[0], max_tokens=1000)
    assert result.description, "Should provide a description"

    # Test with tokens exceeding limit
    with pytest.raises(ImageValidationError) as exc_info:
        await analyzer.analyze_single_image(test_images[0], max_tokens=max_tokens + 1000)
    assert "exceeds model limit" in str(exc_info.value)


@pytest.mark.asyncio
async def test_image_set_analysis(analyzer: ImageAnalyzer, test_images: List[Path]) -> None:
    """Test image set analysis."""
    result = await analyzer.analyze_image_set(test_images)
    assert isinstance(result, ImageSetAnalysis)
    assert result.summary, "Should provide a summary"
    assert len(result.common_objects) > 0, "Should identify common objects"
    assert isinstance(result.comparative_analysis, str), "Should provide comparative analysis"


def test_encode_image_to_base64(test_images: List[Path]) -> None:
    """Test base64 encoding of images."""
    encoded = encode_image_to_base64(test_images[0])
    assert isinstance(encoded, str)
    assert len(encoded) > 0


def test_model_capabilities_access() -> None:
    """Test access to model capabilities."""
    model = get_model("gpt-4o", provider=ModelProvider.AZURE)
    assert model.capabilities.supports_vision is True
    assert isinstance(model.capabilities.max_output_tokens, int)
    assert model.supported_mime_types is not None


@pytest.mark.asyncio
async def test_url_validation_timeouts(analyzer: ImageAnalyzer) -> None:
    """Test URL validation with various timeout scenarios."""
    # Test timeout during URL validation
    with pytest.raises(ImageValidationError) as exc_info:
        await analyzer.analyze_single_image(
            "https://very-slow-domain.com/image.jpg",
            url_timeout=0.001  # Very short timeout
        )
    assert "Timeout while accessing URL" in str(exc_info.value)

    # Test timeout during image download
    with pytest.raises(ImageValidationError) as exc_info:
        await analyzer.analyze_single_image(
            "https://very-slow-domain.com/large-image.jpg",
            download_timeout=0.001  # Very short timeout
        )
    assert "Timeout while accessing URL" in str(exc_info.value)


@pytest.mark.asyncio
async def test_url_content_type_validation(analyzer: ImageAnalyzer) -> None:
    """Test URL content type validation."""
    # Test URL that returns non-image content type
    with pytest.raises(ImageValidationError) as exc_info:
        await analyzer.analyze_single_image("https://example.com/not-an-image.txt")
    assert "URL does not point to an image resource" in str(exc_info.value)


@pytest.mark.asyncio
async def test_concurrent_image_processing(analyzer: ImageAnalyzer, test_images: List[Path]) -> None:
    """Test concurrent processing of multiple images."""
    # Create a list of duplicate images for testing
    multiple_images = test_images * 3
    
    # Test prepare_images method directly
    prepared_images = await analyzer.prepare_images(multiple_images)
    assert len(prepared_images) == len(multiple_images)
    assert all(isinstance(img, InstructorImage) for img in prepared_images)

    # Test analyze_image_set with multiple images
    result = await analyzer.analyze_image_set(multiple_images)
    assert isinstance(result, ImageSetAnalysis)
    assert result.summary
    assert len(result.common_objects) > 0

"""
@pytest.mark.asyncio
async def test_custom_prompts(analyzer: ImageAnalyzer, test_images: List[Path]) -> None:
    custom_prompt = "Focus only on identifying the colors present in this image."
    
    # Test single image analysis with custom prompt
    single_result = await analyzer.analyze_single_image(
        test_images[0],
        prompt=custom_prompt
    )
    assert single_result.colors, "Should identify colors when specifically prompted"
    
    # Test image set analysis with custom prompt
    set_prompt = "Compare only the lighting conditions in these images."
    set_result = await analyzer.analyze_image_set(
        test_images,
        prompt=set_prompt
    )
    assert "lighting" in set_result.comparative_analysis.lower()
"""

@pytest.mark.asyncio
async def test_corrupted_image_handling(analyzer: ImageAnalyzer, tmp_path: Path) -> None:
    """Test handling of corrupted image files."""
    # Create a corrupted image file
    corrupted_file = tmp_path / "corrupted.jpg"
    corrupted_file.write_bytes(b"Not a valid image content")
    
    with pytest.raises(ImageValidationError) as exc_info:
        await analyzer.analyze_single_image(corrupted_file)
    assert "Failed to process image" in str(exc_info.value)


@pytest.fixture
def corrupted_image(tmp_path: Path) -> Path:
    """Fixture to provide a corrupted image file."""
    corrupted_file = tmp_path / "corrupted.jpg"
    corrupted_file.write_bytes(b"Not a valid image content")
    return corrupted_file

@pytest.fixture
def non_image_url() -> str:
    """Fixture to provide a URL that doesn't point to an image."""
    return "https://example.com/not-an-image.txt"

  #  pytest -v tests/functions/vision/test_image_analysis.py -v