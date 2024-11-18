from dotenv import load_dotenv
import os
from swarm import Swarm, Agent
from src.aoai.client import AOAIClient

# Load environment variables
load_dotenv()

# Initialize Azure OpenAI client
ai_client = AOAIClient.create(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
)

# Initialize Swarm with client
client = Swarm(client=ai_client)


def test_context_variables():
    def instructions(context_variables):
        user_name = context_variables["user_name"]
        return f"Help the user, {user_name}, do whatever they want."

    agent = Agent(
        instructions=instructions, model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    )

    response = client.run(
        agent=agent,
        messages=[{"role": "user", "content": "Hi!"}],
        context_variables={"user_name": "John"},
    )

    print("\nTest Context Variables:")
    print(f"Response: {response.messages[-1]['content']}")

    assert (
        "John" in response.messages[-1]["content"]
    ), "Context variable not used in response"
