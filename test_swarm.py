from dotenv import load_dotenv
import os
from swarm import Swarm, Agent
from openai import AzureOpenAI

# Load environment variables from .env file
load_dotenv()

# Debug: Print configuration (excluding API key)
print("Debug Info:")
print(f"API Version: {os.getenv('AZURE_OPENAI_API_VERSION')}")
print(f"API Base: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
print(f"Deployment Name: {os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')}")

# Initialize Azure OpenAI client
azure_client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

# Test the Azure client directly first
try:
    test_response = azure_client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        messages=[{"role": "user", "content": "Say hello"}]
    )
    print("\nDirect Azure test successful!")
except Exception as e:
    print(f"\nDirect Azure test failed: {str(e)}")

# Initialize Swarm with Azure client
client = Swarm(client=azure_client)

# Create a basic agent
researcher = Agent(
    name="researcher",
    instructions="You are a helpful research assistant.",
    model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
)

# Test run
def main():
    try:
        result = client.run(
            agent=researcher,
            messages=[{"role": "user", "content": "What is the capital of France?"}]
        )
        print("\nSwarm Response:")
        print(result.messages[-1]["content"])
    except Exception as e:
        print(f"\nSwarm test failed: {str(e)}")

if __name__ == "__main__":
    main() 