from dotenv import load_dotenv
import os
import base64
from swarm import Swarm, Agent
from openai import AzureOpenAI

# Load environment variables
load_dotenv()

# Initialize Azure OpenAI client globally
azure_client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

def encode_image_to_base64(image_path):
    """Convert an image file to base64 string.
    
    Args:
        image_path: Path to the image file
    Returns:
        base64 encoded string of the image
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_image(context_variables, image_path):
    """Analyzes an image and returns a description.
    
    Args:
        context_variables: Contains any context needed
        image_path: Path to the image to analyze
    Returns:
        A description of the image
    """
    try:
        # Get the base64 encoded image
        base64_image = encode_image_to_base64(image_path)
        
        # Create message content with the image
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Describe this image in detail:"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
        
        # Use the global azure_client
        response = azure_client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=messages,
            max_tokens=2000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error analyzing image: {str(e)}"

def test_vision_agent():
    print("\nInitializing Vision Agent Test...")

    # Initialize Swarm with the global Azure client
    client = Swarm(client=azure_client)

    print("Swarm client initialized")

    # Create vision agent
    vision_agent = Agent(
        name="Vision Agent",
        instructions="You are a vision analysis agent. You can analyze images and provide detailed descriptions.",
        functions=[analyze_image],
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    )

    print("Vision agent created")

    # Test image path (adjust this to your image location)
    image_path = "tests/test_images/test_image.png"
    
    print(f"Attempting to analyze image at: {image_path}")

    # Run the vision agent
    try:
        response = client.run(
            agent=vision_agent,
            messages=[
                {"role": "user", "content": f"Please analyze the image at {image_path}"}
            ],
            context_variables={}  # Empty context variables since we're using global client
        )

        print("\nTest Vision Agent:")
        print(f"Response: {response.messages[-1]['content']}")
        
        # Basic assertion to ensure we got a response
        assert len(response.messages[-1]['content']) > 0, "No description generated"
        print("\n✓ Vision agent test passed")
        
    except Exception as e:
        print(f"\n✗ Vision agent test failed: {str(e)}")
    
if __name__ == "__main__":
    test_vision_agent()