from dotenv import load_dotenv
import os
import pytest
from pathlib import Path
from openai import AzureOpenAI
from swarm import Swarm, Agent
from functions.file_search import FileSearchManager
from functions.config import FileSearchConfig

# Load environment variables
load_dotenv()

# Test Constants
TEST_FILE_CONTENT = """
This is a test document about artificial intelligence and its applications in modern technology.
AI has revolutionized many fields including healthcare, finance, and transportation.
Machine learning, a subset of AI, enables computers to learn from data without explicit programming.
"""

TEST_QUESTION = "What fields has AI revolutionized according to the document?"
EXPECTED_FIELDS = ["healthcare", "finance", "transportation"]

# File paths
TEST_FILES_DIR = Path("tests/test_files")
TEST_FILE_NAME = "sample.txt"
TEST_FILE_PATH = TEST_FILES_DIR / TEST_FILE_NAME

# Custom configuration for testing
TEST_CONFIG = FileSearchConfig(
    assistant_name="Test File Analysis Assistant",
    assistant_instructions="You are a test assistant analyzing documents. Be concise and specific in your answers.",
    vector_store_expiration_days=1,
    max_retries=5,
    retry_delay=0.5
)

@pytest.fixture(scope="module")
def azure_client():
    """Creates an Azure OpenAI client for testing."""
    return AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2024-05-01-preview",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )

@pytest.fixture(scope="module")
def file_manager(azure_client):
    """Creates a FileSearchManager instance with test configuration."""
    return FileSearchManager(azure_client, config=TEST_CONFIG)

@pytest.fixture(scope="module")
def setup_test_environment(file_manager):
    """Sets up the test environment and cleans up after tests."""
    # Create test directory and file
    TEST_FILES_DIR.mkdir(parents=True, exist_ok=True)
    with open(TEST_FILE_PATH, "w", encoding="utf-8") as f:
        f.write(TEST_FILE_CONTENT)
    
    yield
    
    # Cleanup after tests - only remove the test file
    if TEST_FILE_PATH.exists():
        TEST_FILE_PATH.unlink()  # Remove the test file

def test_file_search_agent(azure_client, file_manager, setup_test_environment):
    """Tests the complete file search agent workflow."""
    print("\nRunning File Search Agent Test...")

    try:
        # Initialize Swarm
        client = Swarm(client=azure_client)
        print("✓ Swarm client initialized")

        # Create file search agent
        file_search_agent = Agent(
            name="File Search Agent",
            instructions="""You are a file search agent that can:
            1. Upload files
            2. Answer questions about uploaded files
            
            Important:
            - When given a file name, use upload_file() to process it
            - When asked a question, use ask_question() to search the uploaded files
            - Provide concise, specific answers based on the file content
            - Do not generate responses - use the functions""",
            functions=[file_manager.upload_file, file_manager.ask_question],
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        )
        print("✓ File search agent created")

        # Initialize context variables with vector store and assistant information
        context_variables = {
            "vector_store_name": "Test Vector Store",
            "assistant_name": TEST_CONFIG.assistant_name,
            "assistant_instructions": TEST_CONFIG.assistant_instructions,
            "model_name": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        }

        # Step 1: Upload file
        print(f"\nAttempting to upload file: {TEST_FILE_PATH}")
        print(f"File exists: {TEST_FILE_PATH.exists()}")
        print(f"File path type: {type(TEST_FILE_PATH)}")

        response = client.run(
            agent=file_search_agent,
            messages=[
                {"role": "user", "content": f"Upload this file: {TEST_FILE_PATH}"}
            ],
            context_variables=context_variables
        )

        # Save the updated context variables which should now include vector_store_id and assistant_id
        context_variables = response.context_variables
        print(f"Updated context variables: {context_variables}")
        print(f"Response content: {response.messages[-1]['content']}")
        assert "success" in response.messages[-1]["content"].lower(), "File upload failed"
        print("✓ File uploaded successfully")

        # Step 2: Ask a question
        response = client.run(
            agent=file_search_agent,
            messages=[
                {"role": "user", "content": TEST_QUESTION}
            ],
            context_variables=response.context_variables
        )
        answer = response.messages[-1]["content"].lower()
        
        # Verify the answer contains the expected fields
        for field in EXPECTED_FIELDS:
            assert field in answer, f"Expected field '{field}' not found in answer"
        print("✓ Question answered correctly")

        print("\n✓ All tests passed successfully")
        
    except Exception as e:
        print(f"\n✗ Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 