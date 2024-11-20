import pytest
from pathlib import Path
import os
from typing import List
from unittest.mock import MagicMock
from src.functions.vision import (
    SingleImageAnalysis,
    ImageSetAnalysis,
    analyze_images,
    interpretImageSet,
    encode_image_to_base64,
)
from src.aoai.client import AOAIClient
from src.models.base import ModelProvider
from src.models.config import get_model
from src.exceptions.vision import ImageValidationError


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
async def test_analyze_single_local_image(ai_client: AOAIClient, test_images: List[Path]) -> None:
    """Test analyzing a single local image."""
    result = await analyze_images(ai_client, test_images[0])
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
async def test_analyze_single_url_image(ai_client: AOAIClient, test_image_urls: List[str]) -> None:
    """Test analyzing a single image from URL."""
    result = await analyze_images(ai_client, test_image_urls[0])
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
    ai_client: AOAIClient, test_images: List[Path], model_name: str, expected_exception, error_message: str
) -> None:
    """Test image analysis with various models."""
    if expected_exception:
        with pytest.raises(expected_exception) as exc_info:
            await analyze_images(ai_client, test_images[0], model_name=model_name)
        assert error_message in str(exc_info.value)
    else:
        result = await analyze_images(ai_client, test_images[0], model_name=model_name)
        assert isinstance(result, SingleImageAnalysis)
        assert result.description, "Should provide a description"


@pytest.mark.asyncio
async def test_mime_type_validation(ai_client: AOAIClient) -> None:
    """Test MIME type validation."""
    # Resolve the path explicitly
    temp_file = (Path(__file__).parent / "test_assets" / "unsupported_format_image.webp").resolve()
    print(f"Resolved path: {temp_file}")

    # Ensure the file exists
    assert temp_file.exists(), f"Test file not found: {temp_file}"

    # Test the behavior with the unsupported .webp file
    with pytest.raises(ImageValidationError) as exc_info:
        await analyze_images(ai_client, str(temp_file))

    # Assert the exception contains the expected message
    assert "Unsupported image format" in str(exc_info.value), "Expected unsupported image format error"


@pytest.mark.asyncio
async def test_token_limit_validation(ai_client: AOAIClient, test_images: List[Path]) -> None:
    """Test token limit validation."""
    model_config = get_model("gpt-4o", provider=ModelProvider.AZURE)
    max_tokens = model_config.capabilities.max_output_tokens

    # Test with tokens within limit
    result = await analyze_images(ai_client, test_images[0], max_tokens=1000)
    assert result.description, "Should provide a description"

    # Test with tokens exceeding limit
    with pytest.raises(ImageValidationError) as exc_info:
        await analyze_images(ai_client, test_images[0], max_tokens=max_tokens + 1000)
    assert "exceeds model limit" in str(exc_info.value)


@pytest.mark.asyncio
async def test_image_set_analysis(ai_client: AOAIClient, test_images: List[Path]) -> None:
    """Test image set analysis."""
    result = await interpretImageSet(ai_client, test_images, model_name="gpt-4o")
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