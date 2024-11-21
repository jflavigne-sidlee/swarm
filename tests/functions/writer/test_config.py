import pytest
import logging
from pathlib import Path
import os
from src.functions.writer.config import WriterConfig, PathHandler
from src.functions.writer.exceptions import ConfigurationError, PathValidationError
from src.functions.writer.constants import (
    DEFAULT_SECTION_MARKER,
    DEFAULT_LOCK_TIMEOUT,
    DEFAULT_MAX_FILE_SIZE,
    ALLOWED_EXTENSIONS,
    DEFAULT_ENCODING,
    DEFAULT_METADATA_FIELDS,
    ERROR_VALUE_TOO_SMALL,
    ERROR_PATH_NO_WRITE,
    ERROR_INVALID_TYPE,
    ERROR_PATH_NO_READ,
    ERROR_PATH_PROCESS,
    ERROR_PATH_NOT_DIR,
    ERROR_PATH_NOT_EXIST
)
import re
import shutil
from unittest.mock import patch, Mock

# Configure logging for tests
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# Fixtures
@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for testing."""
    temp = tmp_path / "temp"
    temp.mkdir(parents=True, exist_ok=True)
    yield temp
    clean_directory(tmp_path)  # Clean up after test

@pytest.fixture
def path_handler():
    """Create a PathHandler instance with logging."""
    return PathHandler(logger)

@pytest.fixture
def basic_config(tmp_path, cleanup_dirs):
    """Create a basic configuration with temporary paths."""
    temp_dir = tmp_path / "temp"
    drafts_dir = tmp_path / "drafts"
    finalized_dir = tmp_path / "finalized"
    
    # Register all directories for cleanup
    cleanup_dirs(tmp_path, temp_dir, drafts_dir, finalized_dir)
    
    return {
        "temp_dir": temp_dir,
        "drafts_dir": drafts_dir,
        "finalized_dir": finalized_dir,
        "section_marker_template": DEFAULT_SECTION_MARKER,
        "lock_timeout": DEFAULT_LOCK_TIMEOUT,
        "max_file_size": DEFAULT_MAX_FILE_SIZE,
        "allowed_extensions": ALLOWED_EXTENSIONS,
        "compression_level": 5,
        "metadata_keys": DEFAULT_METADATA_FIELDS,
        "default_encoding": DEFAULT_ENCODING,
        "create_directories": True
    }

@pytest.fixture
def cleanup_dirs():
    """Fixture to handle directory cleanup after tests.
    
    Yields a function that can be used to register directories for cleanup.
    Cleanup happens automatically after the test completes.
    """
    dirs_to_clean = set()
    
    def register_for_cleanup(*paths: Path):
        """Register directories for cleanup after test.
        
        Args:
            *paths: Path objects to clean up after test
        """
        dirs_to_clean.update(paths)
    
    yield register_for_cleanup
    
    # Clean up all registered directories in reverse order
    for path in sorted(dirs_to_clean, key=lambda p: len(str(p)), reverse=True):
        clean_directory(path)

# Path Handler Tests
class TestPathHandler:
    def test_process_path_creates_directory(self, path_handler, temp_dir):
        """Test that process_path creates directories when allowed."""
        result = path_handler.process_path(
            temp_dir / "new_dir",
            "test_dir",
            allow_creation=True
        )
        assert result.exists()
        assert result.is_dir()

    def test_process_path_required_missing(self, path_handler):
        """Test that process_path raises error for missing required paths."""
        with pytest.raises(ConfigurationError, match="Required path test_dir is not set"):
            path_handler.process_path(
                None,
                "test_dir",
                required=True
            )

    def test_process_path_permission_denied(self, path_handler, temp_dir, cleanup_dirs):
        """Test handling of permission errors during path processing."""
        test_path = temp_dir / "test_perms"
        test_path.mkdir(parents=True, exist_ok=True)
        
        # Register paths for cleanup
        cleanup_dirs(test_path, temp_dir)
        
        # Mock access to simulate permission issues
        with patch('os.access', return_value=False):
            with pytest.raises(PathValidationError, match=re.escape(ERROR_PATH_NO_WRITE.format(
                name="test_dir",
                path=test_path
            ))):
                path_handler.process_path(
                    test_path,
                    "test_dir",
                    check_permissions=True
                )

    def test_process_path_permission_checks(self, path_handler, temp_dir):
        """Test different permission check scenarios."""
        test_path = temp_dir / "test_perms"
        test_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # Mock access checks for different scenarios
            access_mock = Mock()
            
            # Scenario 1: No read permission
            access_mock.side_effect = lambda path, mode: mode != os.R_OK
            with patch('os.access', access_mock):
                with pytest.raises(PathValidationError, match=re.escape(ERROR_PATH_NO_READ.format(
                    name="test_dir",
                    path=test_path
                ))):
                    path_handler.process_path(
                        test_path,
                        "test_dir",
                        check_permissions=True
                    )
        finally:
            # Restore permissions before cleanup
            os.chmod(test_path, 0o777)
            os.chmod(temp_dir, 0o777)

    def test_process_path_creation_permission_error(self, path_handler, temp_dir):
        """Test handling of permission errors during directory creation."""
        test_path = temp_dir / "test_perms"
        
        with patch('pathlib.Path.mkdir', side_effect=PermissionError("Mocked mkdir error")):
            with pytest.raises(PathValidationError, match=re.escape(ERROR_PATH_PROCESS.format(
                name="test_dir",
                error="Failed to create directory: Mocked mkdir error"
            ))):
                path_handler.process_path(
                    test_path,
                    "test_dir",
                    allow_creation=True
                )

    def test_validate_relationships_no_nesting(self, path_handler, temp_dir):
        """Test that validate_relationships prevents nested directories."""
        parent = temp_dir / "parent"
        child = parent / "child"
        
        try:
            parent.mkdir(parents=True)
            child.mkdir(parents=True)
            
            with pytest.raises(ConfigurationError, match="Directories cannot be nested"):
                path_handler.validate_relationships({
                    "parent": parent,
                    "child": child
                }, allow_nesting=False)
        finally:
            # Restore permissions and clean up
            for path in [child, parent, temp_dir]:
                clean_directory(path)

# Configuration Tests
class TestWriterConfig:
    def test_basic_initialization(self, basic_config):
        """Test basic configuration initialization."""
        config = WriterConfig(**basic_config)
        assert config.temp_dir == basic_config["temp_dir"]
        assert config.section_marker_template == DEFAULT_SECTION_MARKER
        assert config.lock_timeout == DEFAULT_LOCK_TIMEOUT

    def test_invalid_section_marker(self, basic_config):
        """Test validation of section marker template."""
        basic_config["section_marker_template"] = "Invalid Template"
        with pytest.raises(ConfigurationError, match=".*section_title.*"):
            WriterConfig(**basic_config)

    def test_invalid_lock_timeout(self, basic_config):
        """Test validation of lock timeout."""
        basic_config["lock_timeout"] = 0
        expected_error = ERROR_VALUE_TOO_SMALL.format(
            name="lock_timeout",
            value=0,
            min=1
        )
        with pytest.raises(ConfigurationError, match=re.escape(expected_error)):
            WriterConfig(**basic_config)

    def test_from_dict_conversion(self, basic_config):
        """Test configuration creation from dictionary."""
        config = WriterConfig.from_dict(basic_config)
        assert isinstance(config, WriterConfig)
        assert config.temp_dir == basic_config["temp_dir"]

    def test_to_dict_conversion(self, basic_config):
        """Test configuration conversion to dictionary."""
        config = WriterConfig(**basic_config)
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert str(config_dict["temp_dir"]) == str(basic_config["temp_dir"])

    def test_get_field_info(self):
        """Test retrieving field information."""
        info = WriterConfig.get_field_info("temp_dir")
        assert "help" in info
        assert "type" in info
        assert info["type"] == Path

    def test_invalid_field_info(self):
        """Test error on invalid field name."""
        with pytest.raises(ValueError, match=".*Unknown field.*"):
            WriterConfig.get_field_info("nonexistent_field")

    def test_path_validation(self, basic_config, tmp_path):
        """Test path validation during initialization."""
        # Create separate directories instead of nesting
        temp_dir = tmp_path / "temp"
        drafts_dir = tmp_path / "drafts"
        finalized_dir = tmp_path / "finalized"

        try:
            # Ensure parent directory is writable for creation
            tmp_path.chmod(0o755)

            # Create all directories with write permissions first
            temp_dir.mkdir(parents=True, exist_ok=True)
            drafts_dir.mkdir(parents=True, exist_ok=True)
            finalized_dir.mkdir(parents=True, exist_ok=True)

            # Update config with non-nested paths
            basic_config.update({
                "temp_dir": temp_dir,
                "drafts_dir": drafts_dir,
                "finalized_dir": finalized_dir,
                "create_directories": False  # Don't try to create directories
            })

            # Make directories read-only after creation
            logger.debug("Setting permissions to read-only")
            os.chmod(drafts_dir, 0o444)
            os.chmod(finalized_dir, 0o444)
            os.chmod(temp_dir, 0o444)

            # Verify permissions were set correctly
            logger.debug(f"Temp dir permissions: {oct(temp_dir.stat().st_mode)}")
            logger.debug(f"Drafts dir permissions: {oct(drafts_dir.stat().st_mode)}")
            logger.debug(f"Finalized dir permissions: {oct(finalized_dir.stat().st_mode)}")

            expected_error = ERROR_PATH_NO_WRITE.format(
                name="temp_dir",
                path=temp_dir
            )
            with pytest.raises(PathValidationError, match=re.escape(expected_error)):
                config = WriterConfig(**basic_config)

        finally:
            # Recursive function to clean up directory tree
            def clean_directory(path):
                try:
                    if not path.exists():
                        return
                    
                    # First restore write permissions
                    os.chmod(path, 0o755)
                    
                    # Remove all contents recursively
                    for item in path.iterdir():
                        if item.is_file() or item.is_symlink():
                            item.unlink()
                        else:
                            clean_directory(item)
                    
                    # Remove the empty directory
                    path.rmdir()
                except (PermissionError, OSError) as e:
                    print(f"Warning: Failed to clean up {path}: {e}")
            
            # Clean up all directories
            for path in [drafts_dir, finalized_dir, temp_dir]:
                clean_directory(path)
            
            # Try to clean up parent directory
            try:
                if tmp_path.exists():
                    tmp_path.rmdir()
            except OSError as e:
                print(f"Warning: Failed to remove parent directory: {e}")

    def test_default_config(self):
        """Test getting default configuration."""
        defaults = WriterConfig.get_default_config()
        assert isinstance(defaults, dict)
        assert "temp_dir" in defaults
        assert "section_marker_template" in defaults

    def test_validation_constraints(self, basic_config):
        """Test numeric constraint validation."""
        basic_config["max_file_size"] = -1
        expected_error = ERROR_VALUE_TOO_SMALL.format(
            name="max_file_size",
            value=-1,
            min=1
        )
        with pytest.raises(ConfigurationError, match=re.escape(expected_error)):
            WriterConfig(**basic_config)

    def test_string_representation(self, basic_config):
        """Test string representation of configuration."""
        config = WriterConfig(**basic_config)
        str_repr = str(config)
        assert "Configuration:" in str_repr
        assert str(basic_config["temp_dir"]) in str_repr

    @pytest.mark.order(before="test_path_validation")
    def test_initial_directory_state(self, basic_config, tmp_path, cleanup_dirs):
        """Test that directories are properly initialized with correct permissions."""
        temp_dir = tmp_path / "temp"
        drafts_dir = tmp_path / "drafts"
        finalized_dir = tmp_path / "finalized"
        
        # Register all directories for cleanup
        cleanup_dirs(tmp_path, temp_dir, drafts_dir, finalized_dir)
        
        # Create directories with write permissions
        temp_dir.mkdir(parents=True, exist_ok=True)
        drafts_dir.mkdir(parents=True, exist_ok=True)
        finalized_dir.mkdir(parents=True, exist_ok=True)
        
        # Verify directories exist
        assert temp_dir.exists(), "Temp directory was not created"
        assert drafts_dir.exists(), "Drafts directory was not created"
        assert finalized_dir.exists(), "Finalized directory was not created"
        
        # Verify directories are writable (octal 755 = rwxr-xr-x)
        assert oct(temp_dir.stat().st_mode)[-3:] == '755', f"Temp directory has wrong permissions: {oct(temp_dir.stat().st_mode)}"
        assert oct(drafts_dir.stat().st_mode)[-3:] == '755', f"Drafts directory has wrong permissions: {oct(drafts_dir.stat().st_mode)}"
        assert oct(finalized_dir.stat().st_mode)[-3:] == '755', f"Finalized directory has wrong permissions: {oct(finalized_dir.stat().st_mode)}"
        
        # Verify directories are empty
        assert not any(temp_dir.iterdir()), "Temp directory is not empty"
        assert not any(drafts_dir.iterdir()), "Drafts directory is not empty"
        assert not any(finalized_dir.iterdir()), "Finalized directory is not empty"
        
        # Verify we can write to directories
        for dir_path in [temp_dir, drafts_dir, finalized_dir]:
            test_file = dir_path / ".write_test"
            try:
                test_file.touch()
                assert test_file.exists(), f"Could not create test file in {dir_path}"
                test_file.unlink()
                assert not test_file.exists(), f"Could not remove test file in {dir_path}"
            except (PermissionError, OSError) as e:
                pytest.fail(f"Failed to write to {dir_path}: {e}")
                
        # Clean up all directories in reverse creation order
        for path in [finalized_dir, drafts_dir, temp_dir, tmp_path]:
            try:
                os.chmod(path, 0o777)  # Restore permissions
                clean_directory(path)
            except (PermissionError, OSError) as e:
                print(f"Warning: Failed to clean up {path}: {e}")

    def test_metadata_keys_validation(self, basic_config):
        """Test validation of metadata keys."""
        # Test valid metadata keys
        basic_config["metadata_keys"] = ["title", "author", "custom"]
        config = WriterConfig(**basic_config)
        assert config.metadata_keys == ["title", "author", "custom"]
        
        # Test invalid metadata key type
        basic_config["metadata_keys"] = ["title", 123, "author"]
        expected_error = ERROR_INVALID_TYPE.format(
            name="metadata_keys",
            got="mixed types",
            expected="str"
        )
        with pytest.raises(ConfigurationError, match=re.escape(expected_error)):
            WriterConfig(**basic_config)
        
        # Test empty metadata keys list
        basic_config["metadata_keys"] = []
        config = WriterConfig(**basic_config)
        assert config.metadata_keys == []

    def test_encoding_validation(self, basic_config):
        """Test validation of default encoding."""
        # Test valid encoding
        basic_config["default_encoding"] = "utf-8"
        config = WriterConfig(**basic_config)
        assert config.default_encoding == "utf-8"
        
        # Test invalid encoding
        basic_config["default_encoding"] = "invalid-encoding"
        with pytest.raises(ConfigurationError, match="Invalid value for 'default_encoding'"):
            WriterConfig(**basic_config)
        
        # Test default value
        del basic_config["default_encoding"]
        config = WriterConfig(**basic_config)
        assert config.default_encoding == DEFAULT_ENCODING

    def test_default_values(self, basic_config):
        """Test default values for new fields."""
        # Remove optional fields from basic_config
        basic_config = {
            "temp_dir": basic_config["temp_dir"],
            "drafts_dir": basic_config["drafts_dir"],
            "finalized_dir": basic_config["finalized_dir"]
        }
        
        config = WriterConfig(**basic_config)
        
        # Check defaults
        assert config.create_directories is True
        assert config.metadata_keys == DEFAULT_METADATA_FIELDS
        assert config.default_encoding == DEFAULT_ENCODING

    def test_directory_permission_validation(self, basic_config):
        """Test directory permission validation during config initialization."""
        with patch('os.access', return_value=False):
            with pytest.raises(PathValidationError, match=ERROR_PATH_NO_WRITE.format(
                name="temp_dir",
                path=basic_config["temp_dir"]
            )):
                WriterConfig(**basic_config)

def clean_directory(path: Path) -> None:
    """Clean up a directory and its contents, restoring permissions first.
    
    Args:
        path: Directory path to clean
    """
    if not path.exists():
        return
        
    def on_error(func, path, exc_info):
        """Error handler for shutil.rmtree that handles permission errors."""
        try:
            os.chmod(path, 0o777)  # Restore permissions
            func(path)  # Retry the operation
        except Exception as e:
            print(f"Warning: Failed to clean {path}: {e}")
    
    try:
        shutil.rmtree(path, onerror=on_error)
    except Exception as e:
        print(f"Warning: Failed to remove directory {path}: {e}")
