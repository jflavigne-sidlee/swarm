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

def force_remove(path):
    """Recursively force remove a path."""
    try:
        # First make the current path fully accessible
        os.chmod(path, 0o777)
        
        if path.is_dir():
            # Then handle contents
            for item in path.iterdir():
                force_remove(item)
            # Finally remove the empty directory
            path.rmdir()
        else:
            path.unlink()
    except Exception as e:
        print(f"Warning: Could not remove {path}: {e}")

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

def clean_stale_test_dirs():
    """Clean up any stale test directories from previous failed runs."""
    pytest_tmp = Path('/tmp/pytest-of-' + os.getenv('USER', 'unknown'))
    if not pytest_tmp.exists():
        return
        
    def force_remove(path):
        """Recursively force remove a path."""
        try:
            if path.is_file():
                os.chmod(path, 0o666)
                path.unlink()
            elif path.is_dir():
                for item in path.iterdir():
                    force_remove(item)
                os.chmod(path, 0o777)
                path.rmdir()
        except Exception as e:
            print(f"Warning: Could not remove {path}: {e}")

    # Clean up any garbage-* directories
    for garbage_dir in pytest_tmp.glob('garbage-*'):
        force_remove(garbage_dir)
        time.sleep(0.1)  # Small delay between removals
    
    # Also clean up any pytest-* directories older than 1 hour
    current_time = time.time()
    for test_dir in pytest_tmp.glob('pytest-*'):
        try:
            if (current_time - test_dir.stat().st_mtime) > 3600:  # 1 hour
                force_remove(test_dir)
                time.sleep(0.1)
        except Exception as e:
            print(f"Warning: Could not check/remove {test_dir}: {e}")

def pytest_configure(config):
    """Run cleanup before tests start."""
    clean_stale_test_dirs()

@pytest.fixture(scope="session", autouse=True)
def cleanup_after_tests():
    """Clean up after all tests complete."""
    yield
    clean_stale_test_dirs()