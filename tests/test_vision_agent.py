from dotenv import load_dotenv
import os
import pytest
from pathlib import Path
from swarm import Swarm, Agent
from src.aoai.client import AOAIClient
from src.functions.vision.image_analysis import SingleImageAnalysis, ImageSetAnalysis
import json

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
        "https://example.com/test.jpg"
    ]
    print(f"✓ Testing with images: {', '.join(str(p) for p in image_paths)}")
    
    try:
        # Use the interpretImageSet function directly
        from src.functions.vision.image_analysis import interpretImageSet
        
        result = await interpretImageSet(
            client=ai_client,
            images=image_paths,
            prompt="Please analyze these images and provide a comparative analysis.",
            model_name=vision_agent.model
        )
        
        # Verify the response
        assert result.summary is not None
        assert isinstance(result.common_objects, list)
        assert isinstance(result.unique_features, list)
        assert result.comparative_analysis is not None

        print("✓ Vision analysis completed successfully")
        return result

    except Exception as e:
        print(f"\n✗ Vision analysis test failed: {str(e)}")
        raise

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
