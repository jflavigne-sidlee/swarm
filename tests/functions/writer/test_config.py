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
    ALLOWED_EXTENSIONS
)

# Configure logging for tests
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# Fixtures
@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for testing."""
    temp = tmp_path / "temp"
    temp.mkdir(parents=True, exist_ok=True)
    return temp

@pytest.fixture
def path_handler():
    """Create a PathHandler instance with logging."""
    return PathHandler(logger)

@pytest.fixture
def basic_config(tmp_path):
    """Create a basic configuration with temporary paths."""
    return {
        "temp_dir": tmp_path / "temp",
        "drafts_dir": tmp_path / "drafts",
        "finalized_dir": tmp_path / "finalized",
        "section_marker_template": DEFAULT_SECTION_MARKER,
        "lock_timeout": DEFAULT_LOCK_TIMEOUT,
        "max_file_size": DEFAULT_MAX_FILE_SIZE,
        "allowed_extensions": ALLOWED_EXTENSIONS,
        "compression_level": 5
    }

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

    def test_process_path_permissions(self, path_handler, temp_dir):
        """Test path permission validation."""
        test_dir = temp_dir / "test_perms"
        test_dir.mkdir(parents=True)
        
        # Make directory read-only
        os.chmod(test_dir, 0o444)
        
        with pytest.raises(PathValidationError, match=".*write permission.*"):
            path_handler.process_path(
                test_dir,
                "test_dir",
                check_permissions=True
            )

    def test_validate_relationships_no_nesting(self, path_handler, temp_dir):
        """Test that validate_relationships prevents nested directories."""
        parent = temp_dir / "parent"
        child = parent / "child"
        parent.mkdir(parents=True)
        child.mkdir(parents=True)
        
        with pytest.raises(ConfigurationError, match="Directories cannot be nested"):
            path_handler.validate_relationships({
                "parent": parent,
                "child": child
            }, allow_nesting=False)

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
        with pytest.raises(ConfigurationError, match=".*must be positive.*"):
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

            with pytest.raises(PathValidationError, match=r"Path '.*' does not have write permission: .*"):
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
        with pytest.raises(ConfigurationError, match=".*must be positive.*"):
            WriterConfig(**basic_config)

    def test_string_representation(self, basic_config):
        """Test string representation of configuration."""
        config = WriterConfig(**basic_config)
        str_repr = str(config)
        assert "Configuration:" in str_repr
        assert str(basic_config["temp_dir"]) in str_repr

    @pytest.mark.order(before="test_path_validation")
    def test_initial_directory_state(self, basic_config, tmp_path):
        """Test that directories are properly initialized with correct permissions."""
        # Create separate directories
        temp_dir = tmp_path / "temp"
        drafts_dir = tmp_path / "drafts"
        finalized_dir = tmp_path / "finalized"
        
        try:
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
                
        finally:
            # Clean up
            for path in [temp_dir, drafts_dir, finalized_dir]:
                try:
                    if path.exists():
                        os.chmod(path, 0o755)  # Ensure we can delete it
                        path.rmdir()
                except (PermissionError, OSError) as e:
                    print(f"Cleanup warning for {path}: {e}")
            
            try:
                tmp_path.rmdir()
            except OSError:
                pass  # Directory might not be empty or already removed