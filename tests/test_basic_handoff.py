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


def test_basic_handoff():
    # Create agents
    def transfer_to_agent_b():
        return agent_b

    agent_a = Agent(
        name="Agent A",
        instructions="You are a helpful agent.",
        functions=[transfer_to_agent_b],
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    )

    agent_b = Agent(
        name="Agent B",
        instructions="Only speak in Haikus.",
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    )

    # Test the handoff
    response = client.run(
        agent=agent_a,
        messages=[{"role": "user", "content": "I want to talk to agent B."}],
    )

    print("\nTest Basic Handoff:")
    print(f"Final agent: {response.agent.name}")
    print(f"Response: {response.messages[-1]['content']}")

    assert response.agent.name == "Agent B", "Handoff failed"
