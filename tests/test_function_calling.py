from dotenv import load_dotenv
import os
from swarm import Swarm, Agent
from functions.azure_client import AzureClientWrapper

# Load environment variables
load_dotenv()

def test_function_calling():
    """Test function calling with Azure OpenAI wrapper"""
    
    # Initialize Azure OpenAI client with wrapper
    azure_client = AzureClientWrapper.create(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )

    def greet(context_variables, language):
        """Greets the user in the specified language.
        
        Args:
            context_variables: Contains user information
            language: The language to use ('spanish' or 'english')
        """
        user_name = context_variables["user_name"]
        greeting = "Hola" if language.lower() == "spanish" else "Hello"
        return f"{greeting}, {user_name}!"

    # Create agent with deployment name
    agent = Agent(
        name="Greeting Agent",
        instructions="You are a helpful assistant. When asked to greet, use the greet function with 'spanish' as the language.",
        functions=[greet],
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")  # Make sure this matches your deployment
    )

    # Initialize Swarm with wrapped client
    client = Swarm(client=azure_client)

    # Run the test
    print("\nStarting Function Calling Test...")
    response = client.run(
        agent=agent,
        messages=[{"role": "user", "content": "Please greet me"}],
        context_variables={"user_name": "John"}
    )

    print("\nTest Function Calling:")
    print(f"Response: {response.messages[-1]['content']}")
    
    # More flexible assertion that checks if either the function call or result appears
    assert any("Hola, John!" in str(msg) for msg in response.messages), "Function not called correctly"