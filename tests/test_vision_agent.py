from dotenv import load_dotenv
import os
import pytest
from pathlib import Path
from swarm import Swarm, Agent
from src.aoai.client import AOAIClient
from src.functions.vision import ImageAnalysisResponse

# Load environment variables
load_dotenv()

@pytest.fixture
def ai_client():
    """Fixture to create Azure OpenAI client."""
    return AOAIClient.create(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    )

@pytest.fixture
def vision_agent(ai_client):
    """Fixture to create vision agent."""
    return Agent(
        name="Vision Agent",
        instructions="You are a vision analysis agent. You can analyze images and provide detailed descriptions.",
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    )

@pytest.mark.asyncio
async def test_vision_analysis(ai_client, vision_agent):
    """Test vision analysis functionality."""
    print("\nInitializing Vision Analysis Test...")

    # Initialize Swarm
    client = Swarm(client=ai_client)
    print("✓ Swarm client initialized")
    
    # Test image paths
    image_paths = [
        Path("tests/test_images/test_image.png"),
        "https://example.com/test.jpg"  # Example URL
    ]
    print(f"✓ Testing with images: {', '.join(str(p) for p in image_paths)}")
    
    try:
        # Run analysis
        response = client.run(
            agent=vision_agent,
            messages=[{
                "role": "user", 
                "content": f"Please analyze these images: {', '.join(str(p) for p in image_paths)}"
            }],
            context_variables={"image_paths": [str(p) for p in image_paths]}
        )
        
        result = ImageAnalysisResponse.model_validate_json(response.messages[-1]["content"])
        
        # Assertions
        assert isinstance(result, ImageAnalysisResponse), "Result should be an ImageAnalysisResponse"
        assert result.description, "Description should not be empty"
        assert len(result.objects) > 0, "Should identify at least one object"
        assert result.scene_type in ['indoor', 'outdoor', None], "Invalid scene type"
        assert len(result.colors) > 0, "Should identify at least one color"
        
        print("\n✓ Vision Analysis Results:")
        print(f"Description: {result.description}")
        print(f"Objects: {', '.join(result.objects)}")
        print(f"Scene Type: {result.scene_type}")
        print(f"Colors: {', '.join(result.colors)}")
        print(f"Quality: {result.quality}")
        print("\n✓ Vision analysis test passed")
        
    except Exception as e:
        print(f"\n✗ Vision analysis test failed: {str(e)}")
        raise

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
