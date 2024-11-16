from dotenv import load_dotenv
import os
from swarm import Swarm, Agent
from openai import AzureOpenAI

# Load environment variables
load_dotenv()

# Initialize Azure OpenAI client
azure_client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

# Initialize Swarm
client = Swarm(client=azure_client)

def test_function_calling():
    def greet(context_variables, language):
        """Greets the user in the specified language.
        
        Args:
            context_variables: Contains user information
            language: The language to use ('spanish' or 'english')
        """
        user_name = context_variables["user_name"]
        greeting = "Hola" if language.lower() == "spanish" else "Hello"
        return f"{greeting}, {user_name}!"

    agent = Agent(
        instructions="You are a helpful assistant. When asked to greet, use the greet function with 'spanish' as the language.",
        functions=[greet],
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    )

    response = client.run(
        agent=agent,
        messages=[{"role": "user", "content": "Please greet me"}],
        context_variables={"user_name": "John"}
    )

    print("\nTest Function Calling:")
    print(f"Response: {response.messages[-1]['content']}")
    
    # More flexible assertion that checks if either the function call or result appears
    assert any("Hola, John!" in str(msg) for msg in response.messages), "Function not called correctly" 