import pytest
from pathlib import Path
import os
from typing import List
import aiohttp
import tempfile
from PIL import Image
import io
from unittest.mock import MagicMock, Mock, patch

from src.functions.vision import (
    SingleImageAnalysis,
    ImageSetAnalysis,
    analyze_images,
    interpretImages,
    interpretImageSet,
    encode_image_to_base64
)
from src.aoai.client import AOAIClient
from src.functions.vision.image_analysis import encode_image_to_base64
from src.models.base import ModelProvider
from src.models.config import get_model
from src.exceptions.vision import (
    ImageValidationError,
    APIError,
    ImageAnalysisError
)

# Test fixtures and utilities
@pytest.fixture
def ai_client():
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

# Test cases
@pytest.mark.asyncio
async def test_analyze_single_local_image(ai_client, test_images):
    """Test analyzing a single local image."""
    print("\nTesting single local image analysis...")
    
    try:
        result = await analyze_images(ai_client, test_images[0])  # Note: removed list wrapper
        
        assert isinstance(result, SingleImageAnalysis)  # Changed from ImageAnalysisResponse
        assert result.description, "Should provide a description"
        assert len(result.objects) > 0, "Should identify objects"
        assert result.colors, "Should identify colors"
        assert result.scene_type in ["indoor", "outdoor"], "Should identify scene type"
        assert result.quality, "Should assess image quality"
        
        print(f"✓ Successfully analyzed local image: {test_images[0]}")
        print(f"Description: {result.description[:100]}...")
        print(f"Objects found: {', '.join(result.objects[:5])}...")
        print(f"Scene type: {result.scene_type}")
        print(f"Colors: {', '.join(result.colors[:5])}...")
        print(f"Quality: {result.quality}")
        
    except Exception as e:
        pytest.fail(f"Failed to analyze local image: {str(e)}")

@pytest.mark.asyncio
async def test_analyze_single_url_image(ai_client, test_image_urls):
    """Test analyzing a single image from URL."""
    print("\nTesting single URL image analysis...")
    
    try:
        result = await analyze_images(ai_client, [test_image_urls[0]])
        
        assert isinstance(result, SingleImageAnalysis)
        assert result.description, "Should provide a description"
        
        print(f"✓ Successfully analyzed URL image: {test_image_urls[0]}")
        print(f"Description: {result.description[:100]}...")
        
    except Exception as e:
        pytest.fail(f"Failed to analyze URL image: {str(e)}")

@pytest.mark.asyncio
async def test_analyze_multiple_images(ai_client, test_images, test_image_urls):
    """Test analyzing multiple images of different types."""
    print("\nTesting multiple image analysis...")
    
    try:
        # Test individual analysis
        individual_results = await interpretImages(ai_client, [test_images[0], test_image_urls[0]])
        print("\nIndividual Analysis Results:")
        for i, result in enumerate(individual_results, 1):
            print(f"\nImage {i}:")
            print(f"Description: {result.description[:100]}...")
            print(f"Objects: {', '.join(result.objects[:5])}")
        
        # Test set analysis
        set_result = await interpretImageSet(ai_client, [test_images[0], test_image_urls[0]])
        print("\nSet Analysis Results:")
        print(f"Summary: {set_result.summary[:100]}...")
        print(f"Common Objects: {', '.join(set_result.common_objects)}")
        print(f"Comparative Analysis: {set_result.comparative_analysis[:100]}...")
        
        # Assertions
        assert len(individual_results) == 2, "Should return analysis for both images"
        assert all(isinstance(r, SingleImageAnalysis) for r in individual_results)
        assert isinstance(set_result, ImageSetAnalysis)
        assert set_result.summary, "Should provide a summary"
        assert set_result.comparative_analysis, "Should provide comparison"
        
        print("\n✓ Successfully analyzed images both individually and as a set")
        
    except Exception as e:
        print("\n✗ Test failed with error:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        pytest.fail(f"Failed to analyze multiple images: {str(e)}")

@pytest.mark.asyncio
async def test_invalid_image_path():
    """Test handling of invalid image path."""
    print("\nTesting invalid image path handling...")
    
    # Create a minimal client mock
    mock_client = type('MockClient', (), {
        'chat': type('MockChat', (), {
            'completions': type('MockCompletions', (), {
                'create': lambda *args, **kwargs: None
            })()
        })()
    })()
    
    with pytest.raises(ValueError) as exc_info:
        await analyze_images(mock_client, ["nonexistent.jpg"])
    
    assert "Invalid image source" in str(exc_info.value)
    print("✓ Successfully handled invalid image path")

@pytest.mark.asyncio
async def test_invalid_image_url(ai_client):
    """Test handling of invalid image URL."""
    print("\nTesting invalid image URL handling...")
    
    with pytest.raises(Exception) as exc_info:
        await analyze_images(ai_client, ["https://example.com/nonexistent.jpg"])
    print("✓ Successfully handled invalid image URL")

def test_encode_image_to_base64(test_images):
    """Test base64 encoding of images."""
    print("\nTesting image base64 encoding...")
    
    try:
        encoded = encode_image_to_base64(test_images[0])
        assert isinstance(encoded, str)
        assert len(encoded) > 0
        print("✓ Successfully encoded image to base64")
        
    except Exception as e:
        pytest.fail(f"Failed to encode image: {str(e)}")

@pytest.mark.asyncio
async def test_response_model_validation():
    """Test SingleImageAnalysis model validation."""
    print("\nTesting response model validation...")
    
    # Test valid data
    valid_data = {
        "description": "A test image",
        "objects": ["object1", "object2"],
        "scene_type": "indoor",
        "colors": ["red", "blue"],
        "quality": "high",
        "metadata": {"key": "value"}
    }
    
    response = SingleImageAnalysis(**valid_data)
    assert response.description == valid_data["description"]
    assert response.objects == valid_data["objects"]
    print("✓ Successfully validated response model")

    # Test invalid data
    with pytest.raises(ValueError):
        SingleImageAnalysis(
            description=123,  # Should be string
            objects=["object1"],
            colors=["red"]
        )
    print("✓ Successfully caught invalid data")

@pytest.mark.asyncio
async def test_max_tokens_limit(ai_client, test_images):
    """Test respecting max_tokens parameter."""
    print("\nTesting max tokens limit...")
    
    try:
        # Use a more reasonable minimum token limit
        result_short = await analyze_images(ai_client, test_images[0], max_tokens=200)
        result_normal = await analyze_images(ai_client, test_images[0], max_tokens=2000)
        
        # Compare description lengths
        assert len(result_short.description) < len(result_normal.description), \
            "Short response should have less content than normal response"
        
        print(f"\nShort description ({len(result_short.description)} chars):")
        print(result_short.description[:100] + "...")
        print(f"\nNormal description ({len(result_normal.description)} chars):")
        print(result_normal.description[:100] + "...")
        print("\n✓ Successfully respected max tokens limit")
        
    except Exception as e:
        if "max_tokens length limit" in str(e):
            print("✓ Successfully caught max tokens limit")
            return  # Test passes if we catch the expected error
        pytest.fail(f"Failed to test max tokens limit: {str(e)}")

@pytest.fixture
def test_images():
    """Fixture providing test image paths."""
    current_dir = Path(__file__).parent
    test_data_dir = current_dir / "test_assets"
    return [
        str(test_data_dir / "image1.png"),
        str(test_data_dir / "image2.png")
    ]

@pytest.fixture
def mock_client():
    """Fixture providing a mock OpenAI client."""
    mock = Mock()
    # Mock the chat completions
    mock.chat.completions.create.return_value = Mock(
        content="Test analysis result"
    )
    return mock

@pytest.mark.asyncio
async def test_analyze_images_model_validation(mock_client, test_images):
    """Test model validation in image analysis."""
    print("\nTesting model validation...")
    
    # Test with valid model
    try:
        result = await analyze_images(
            mock_client,
            test_images[0],
            model_name="gpt-4-vision"
        )
        print("✓ Successfully used valid model")
    except Exception as e:
        pytest.fail(f"Failed with valid model: {str(e)}")

    # Test with non-vision model
    with pytest.raises(ImageValidationError) as exc_info:
        await analyze_images(
            mock_client,
            test_images[0],
            model_name="gpt-4"
        )
    assert "does not support vision capabilities" in str(exc_info.value)
    print("✓ Successfully caught non-vision model")

    # Test with invalid model
    with pytest.raises(ImageValidationError) as exc_info:
        await analyze_images(
            mock_client,
            test_images[0],
            model_name="invalid-model"
        )
    assert "Invalid model configuration" in str(exc_info.value)
    print("✓ Successfully caught invalid model")

@pytest.mark.asyncio
async def test_token_limit_validation(mock_client, test_images):
    """Test token limit validation."""
    print("\nTesting token limit validation...")
    
    model_config = get_model("gpt-4-vision", provider=ModelProvider.AZURE)
    max_tokens = model_config.capabilities.max_output_tokens
    
    # Test with tokens within limit
    try:
        result = await analyze_images(
            mock_client,
            test_images[0],
            max_tokens=1000
        )
        print("✓ Successfully used valid token limit")
    except Exception as e:
        pytest.fail(f"Failed with valid token limit: {str(e)}")

    # Test with tokens exceeding limit
    with pytest.raises(ImageValidationError) as exc_info:
        await analyze_images(
            mock_client,
            test_images[0],
            max_tokens=max_tokens + 1000
        )
    assert "exceeds model limit" in str(exc_info.value)
    print("✓ Successfully caught token limit exceeded")

@pytest.mark.asyncio
async def test_mime_type_validation(mock_client):
    """Test MIME type validation."""
    print("\nTesting MIME type validation...")
    
    # Create a temporary unsupported file
    temp_file = Path("test_temp.webp")
    try:
        temp_file.touch()
        
        # Test with unsupported file type
        with pytest.raises(ImageValidationError) as exc_info:
            await analyze_images(
                mock_client,
                str(temp_file)
            )
        assert "Unsupported image type" in str(exc_info.value)
        print("✓ Successfully caught unsupported MIME type")
        
    finally:
        if temp_file.exists():
            temp_file.unlink()

@pytest.mark.asyncio
async def test_image_set_analysis(mock_client, test_images):
    """Test image set analysis with model configuration."""
    print("\nTesting image set analysis...")
    
    # Test with valid configuration
    try:
        result = await interpretImageSet(
            mock_client,
            test_images,
            model_name="gpt-4-vision"
        )
        print("✓ Successfully analyzed image set")
    except Exception as e:
        pytest.fail(f"Failed to analyze image set: {str(e)}")

    # Test with invalid model for image set
    with pytest.raises(ImageValidationError) as exc_info:
        await interpretImageSet(
            mock_client,
            test_images,
            model_name="text-embedding-ada-002"
        )
    assert "does not support vision capabilities" in str(exc_info.value)
    print("✓ Successfully caught invalid model for image set")

@pytest.mark.asyncio
async def test_environment_model_override(mock_client, test_images):
    """Test model override from environment variables."""
    print("\nTesting environment model override...")
    
    # Test with environment override
    os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"] = "gpt-4-vision"
    
    try:
        result = await analyze_images(
            mock_client,
            test_images[0]
        )
        print("✓ Successfully used environment model override")
    except Exception as e:
        pytest.fail(f"Failed with environment override: {str(e)}")
    finally:
        del os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"]

def test_model_capabilities_access():
    """Test access to model capabilities."""
    print("\nTesting model capabilities access...")
    
    model = get_model("gpt-4-vision", provider=ModelProvider.AZURE)
    
    assert model.capabilities.vision == True
    assert model.capabilities.supports_vision == True
    assert isinstance(model.capabilities.max_output_tokens, int)
    assert isinstance(model.capabilities.default_temperature, float)
    assert model.supported_mime_types is not None
    
    print("✓ Successfully accessed model capabilities")

@pytest.mark.asyncio
async def test_model_capabilities_validation(ai_client, test_images):
    """Test model capabilities validation."""
    print("\nTesting model capabilities validation...")

    # Test with model that has all capabilities
    try:
        result = await analyze_images(
            ai_client,
            test_images[0],
            model_name="gpt-4o-realtime-preview"
        )
        print("✓ Successfully used full-capability model")
    except Exception as e:
        pytest.fail(f"Failed with full-capability model: {str(e)}")

    # Test with model that doesn't support vision
    with pytest.raises(ImageValidationError) as exc_info:
        await analyze_images(
            ai_client,
            test_images[0],
            model_name="gpt-35-turbo"  # Non-vision model
        )
    assert "does not support vision capabilities" in str(exc_info.value)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
