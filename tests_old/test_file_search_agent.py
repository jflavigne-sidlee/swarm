from dotenv import load_dotenv
import os
from swarm import Swarm, Agent
from openai import AzureOpenAI
import time
from pathlib import Path
from swarm.file_search import FileSearchManager

# Load environment variables
load_dotenv()

# Constants
TEST_FILE_CONTENT = """
This is a test document about artificial intelligence and its applications in modern technology.
AI has revolutionized many fields including healthcare, finance, and transportation.
Machine learning, a subset of AI, enables computers to learn from data without explicit programming.
"""

TEST_QUESTION = "What fields has AI revolutionized according to the document?"

# File paths
TEST_FILES_DIR = Path("tests/test_files")
TEST_FILE_NAME = "sample.txt"
TEST_FILE_PATH = TEST_FILES_DIR / TEST_FILE_NAME

# Initialize Azure OpenAI client globally
azure_client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-05-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

# Initialize the file search manager
file_manager = FileSearchManager(azure_client)

def setup_test_file():
    """Creates the test file with predefined content."""
    TEST_FILES_DIR.mkdir(parents=True, exist_ok=True)
    with open(TEST_FILE_PATH, "w") as f:
        f.write(TEST_FILE_CONTENT)
    print(f"Created test file at {TEST_FILE_PATH}")

def upload_file(context_variables, file_name):
    """Uploads a file for searching.
    
    Args:
        context_variables: Dictionary to store IDs
        file_name: Name of the file to upload
    Returns:
        Status message
    """
    file_path = TEST_FILES_DIR / file_name
    return file_manager.upload_file(file_path, context_variables)

def ask_question(context_variables, question):
    """Asks a question about the uploaded file.
    
    Args:
        context_variables: Contains assistant_id and vector_store_id
        question: Question to ask about the file
    Returns:
        Answer from the assistant
    """
    return file_manager.ask_question(question, context_variables)

def test_file_search_agent():
    print("\nInitializing File Search Agent Test...")

    # Initialize Swarm
    client = Swarm(client=azure_client)
    print("Swarm client initialized")

    # Create file search agent with simplified instructions
    file_search_agent = Agent(
        name="File Search Agent",
        instructions="""You are a file search agent that can:
        1. Upload files when given a file name
        2. Answer questions about uploaded files
        
        Important:
        - When given a file name, use upload_file() to process it
        - When asked a question, use ask_question() to search the uploaded files
        - Do not generate responses - use the functions""",
        functions=[upload_file, ask_question],
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    )
    print("File search agent created")

    try:
        # Create test file
        setup_test_file()

        # Step 1: Upload file
        response = client.run(
            agent=file_search_agent,
            messages=[
                {"role": "user", "content": f"Upload this file: {TEST_FILE_NAME}"}
            ],
            context_variables={}
        )
        print("\nFile Upload Response:")
        print(response.messages[-1]["content"])

        # Step 2: Ask a question
        response = client.run(
            agent=file_search_agent,
            messages=[
                {"role": "user", "content": TEST_QUESTION}
            ],
            context_variables=response.context_variables
        )
        print("\nQuestion Response:")
        print(response.messages[-1]["content"])
        
        print("\n✓ File search agent test passed")
        
    except Exception as e:
        print(f"\n✗ File search agent test failed: {str(e)}")
        raise e

if __name__ == "__main__":
    test_file_search_agent() 