from dotenv import load_dotenv
import os
import pytest
from pathlib import Path
from src.aoai.client import AOAIClient
from src.config import FileSearchConfig
from src.file_manager import FileManager
from src.assistant_manager import AssistantManager
import tempfile
import stat
import shutil
import time
import atexit

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
    """Creates an Azure OpenAI client for testing."""
    return AOAIClient.create(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        # api_version="2024-05-01-preview",
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables."""
    # Store original value
    original_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    
    # Set test deployment name
    os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"] = "gpt-4o"
    
    yield
    
    # Restore original value or remove if it wasn't set
    if original_deployment:
        os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"] = original_deployment
    else:
        os.environ.pop("AZURE_OPENAI_DEPLOYMENT_NAME", None)

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
    """Creates a FileManager instance."""
    return FileManager(azure_client)

@pytest.fixture
def assistant_manager(azure_client):
    """Create an AssistantManager instance for testing."""
    return AssistantManager(azure_client)

def force_chmod(path: Path):
    """Recursively change permissions to allow deletion."""
    try:
        if path.is_dir():
            # Make directory and contents writable
            os.chmod(path, 0o755)
            for item in path.iterdir():
                force_chmod(item)
        else:
            os.chmod(path, 0o644)
    except Exception:
        pass

def force_remove(path: Path, retries: int = 3):
    """Remove a path with retries and permission fixes."""
    for attempt in range(retries):
        try:
            if not path.exists():
                return True
                
            # Make everything writable first
            force_chmod(path)
            
            if path.is_file():
                path.unlink()
            else:
                shutil.rmtree(path, ignore_errors=True)
            
            return True
        except Exception:
            if attempt < retries - 1:
                time.sleep(0.1 * (attempt + 1))
    return False

@pytest.fixture(scope="session", autouse=True)
def cleanup_test_files():
    """Clean up test files after all tests are complete."""
    yield
    
    # Get pytest temp directory
    temp_dir = Path('/tmp/pytest-of-' + os.getenv('USER', 'unknown'))
    if temp_dir.exists():
        # Handle each garbage directory
        for garbage_dir in temp_dir.glob('garbage-*'):
            try:
                # First handle special directories
                test_path = garbage_dir / 'test_path_validation0'
                if test_path.exists():
                    for special_dir in ['drafts', 'finalized']:
                        special_path = test_path / 'temp' / special_dir
                        if special_path.exists():
                            force_remove(special_path)
                    
                    # Then remove parent directories
                    force_remove(test_path / 'temp')
                    force_remove(test_path)
                
                # Finally remove the garbage directory
                force_remove(garbage_dir)
            except Exception as e:
                print(f"Warning: Failed to remove {garbage_dir}: {e}")

@pytest.fixture(autouse=True)
def setup_test_permissions():
    """Ensure proper permissions for test execution."""
    original_umask = os.umask(0o022)  # Set default umask to get 755/644
    yield
    os.umask(original_umask)

@pytest.fixture
def test_file(tmp_path):
    """Create a test file with proper permissions."""
    def _create_file(content: str, filename: str = "test.md") -> Path:
        file_path = tmp_path / filename
        file_path.write_text(content)
        os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR)
        return file_path
    return _create_file