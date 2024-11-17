from dotenv import load_dotenv
import os
from swarm import Swarm, Agent
from src.azure_client import AzureClientWrapper

# Load environment variables
load_dotenv()

# Initialize Azure OpenAI client with wrapper
azure_client = AzureClientWrapper.create(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

# Initialize Swarm with wrapped client
client = Swarm(client=azure_client)

def test_context_variables():
    def instructions(context_variables):
        user_name = context_variables["user_name"]
        return f"Help the user, {user_name}, do whatever they want."

    agent = Agent(
        instructions=instructions,
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    )

    response = client.run(
        agent=agent,
        messages=[{"role": "user", "content": "Hi!"}],
        context_variables={"user_name": "John"}
    )

    print("\nTest Context Variables:")
    print(f"Response: {response.messages[-1]['content']}")
    
    assert "John" in response.messages[-1]["content"], "Context variable not used in response" 