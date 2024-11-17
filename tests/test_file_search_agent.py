from dotenv import load_dotenv
import os
import pytest
from pathlib import Path
from openai import AzureOpenAI
from swarm import Swarm, Agent
from functions.file_manager import FileManager
from functions.assistant_manager import AssistantManager
from functions.config import FileSearchConfig
from functions.azure_client import AzureClientWrapper
import json

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
def file_manager(azure_client):
    """Creates a FileSearchManager instance with test configuration."""
    return FileManager(azure_client, config=TEST_CONFIG)

@pytest.fixture(scope="module")
def setup_test_environment(file_manager):
    """Sets up the test environment and cleans up after tests."""
    # Create test directory and file
    TEST_FILES_DIR.mkdir(parents=True, exist_ok=True)
    with open(TEST_FILE_PATH, "w", encoding="utf-8") as f:
        f.write(TEST_FILE_CONTENT)
    
    # Return the test file path instead of using yield alone
    yield {
        "test_file": str(TEST_FILE_PATH)
    }
    
    # Cleanup after tests - only remove the test file
    if TEST_FILE_PATH.exists():
        TEST_FILE_PATH.unlink()  # Remove the test file

def test_file_search_agent(file_manager, assistant_manager, setup_test_environment):
    """Tests the complete file search agent workflow."""
    print("\n" + "="*80)
    print("Starting File Search Agent Test")
    print("="*80)

    assistant_id = None
    try:
        client = Swarm(
            client=AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version="2024-05-01-preview",
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
            )
        )
        print("\n✓ Swarm client initialized")
        
        file_search_agent = Agent(
            name="File Search Agent",
            instructions="""You are a file search agent that can:
            1. Upload files
            2. Answer questions about uploaded files
            
            Important:
            - When given a file name, use upload_file() to process it
            - When asked a question, use ask_question() to search the uploaded files
            - All responses must be in valid JSON format with an 'answer' field without markdown formatting around it.
            - Example response: {"answer": "File uploaded successfully with ID: xyz"}
            - Do not generate responses - use the functions""",
            functions=[file_manager.upload_file, assistant_manager.ask_question],
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        )
        print("✓ File search agent created")

        test_file = setup_test_environment["test_file"]
        context_variables = {
            "vector_store_name": "Test Vector Store",
            "assistant_name": "Test Assistant",
            "assistant_instructions": "You are a test assistant. Answer in JSON format.",
            "model_name": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        }

        response = client.run(
            agent=file_search_agent,
            messages=[
                {"role": "user", "content": f"Upload this file: {test_file}"}
            ],
            context_variables=context_variables
        )

        answer = json.loads(response.messages[-1]["content"])
        assert "answer" in answer, "Response missing 'answer' field"
        print(f"✓ File uploaded: {answer['answer']}")
        
        # Extract assistant_id from context if available
        assistant_id = context_variables.get("assistant_id")
            
    except Exception as e:
        print(f"\n✗ Test failed: {str(e)}")
        raise
    finally:
        # Cleanup assistant if one was created
        if assistant_id:
            try:
                assistant_manager.client.delete_assistant(assistant_id)
                print(f"✓ Assistant cleaned up: {assistant_id}")
            except Exception as e:
                print(f"Warning: Failed to delete assistant {assistant_id}: {str(e)}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 