from dotenv import load_dotenv
import os
import pytest
from pathlib import Path
from src.azure_client import AzureClientWrapper
from src.config import FileSearchConfig
from src.file_manager import FileManager
from src.assistant_manager import AssistantManager
import tempfile

# Load environment variables
load_dotenv()

# Test Constants
TEST_CONTENT = """
This is a test document about artificial intelligence and its applications in modern technology.
AI has revolutionized many fields including healthcare, finance, and transportation.
Machine learning, a subset of AI, enables computers to learn from data without explicit programming.
"""

# Test Configuration
TEST_CONFIG = FileSearchConfig(
    assistant_name="Test File Analysis Assistant",
    assistant_instructions="You are a test assistant analyzing documents. Answer in JSON format.",
    vector_store_expiration_days=1,
    max_retries=5,
    retry_delay=0.5
)

@pytest.fixture(scope="session")
def azure_client():
    """Creates an Azure OpenAI client wrapper for testing."""
    return AzureClientWrapper.create(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        # api_version="2024-05-01-preview",
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )

@pytest.fixture
def setup_test_environment():
    """Sets up a temporary test environment with sample files."""
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test file path
        test_file_path = Path(temp_dir) / "sample.txt"
        
        # Test content
        test_content = """
        This is a test document about artificial intelligence and its applications in modern technology.
        AI has revolutionized several fields including healthcare, finance, and transportation.
        The impact of AI continues to grow as technology advances.
        """
        
        # Write content to file
        test_file_path.write_text(test_content)
        
        yield {
            "test_content": test_content,
            "test_file_path": str(test_file_path)
        }

@pytest.fixture(scope="session")
def file_manager(azure_client):
    """Creates a FileManager instance with the wrapped client."""
    return FileManager(azure_client)

@pytest.fixture
def assistant_manager(azure_client):
    """Create an AssistantManager instance for testing."""
    return AssistantManager(azure_client)