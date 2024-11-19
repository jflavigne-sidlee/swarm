# Individual test commands:
# pytest tests/functions/vision/test_image_analysis.py::test_analyze_single_local_image -v
# pytest tests/functions/vision/test_image_analysis.py::test_analyze_single_url_image -v
# pytest tests/functions/vision/test_image_analysis.py::test_analyze_multiple_images -v
# pytest tests/functions/vision/test_image_analysis.py::test_invalid_image_path -v
# pytest tests/functions/vision/test_image_analysis.py::test_invalid_image_url -v
# pytest tests/functions/vision/test_image_analysis.py::test_encode_image_to_base64 -v
# pytest tests/functions/vision/test_image_analysis.py::test_response_model_validation -v
# pytest tests/functions/vision/test_image_analysis.py::test_max_tokens_limit -v

# Run all tests in file:
# pytest tests/functions/vision/test_image_analysis.py -v

# Run all tests with print statements:
# pytest tests/functions/vision/test_image_analysis.py -v -s

import pytest
from pathlib import Path
...

import pytest
from pathlib import Path
import os
from typing import List
import aiohttp
import tempfile
from PIL import Image
import io
from unittest.mock import MagicMock

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

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
