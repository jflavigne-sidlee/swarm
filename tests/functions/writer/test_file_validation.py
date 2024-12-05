import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import os

from src.functions.writer.file_validation import (
    validate_file_inputs,
    is_valid_filename,
    ensure_valid_markdown_file
)
from src.functions.writer.exceptions import FileValidationError, FilePermissionError
from src.functions.writer.config import WriterConfig

@pytest.fixture
def mock_config():
    return Mock(spec=WriterConfig, create_directories=True)

class TestFileValidation:
    def test_is_valid_filename_valid_cases(self):
        assert is_valid_filename("test.md") is True
        assert is_valid_filename("my-file.md") is True
        assert is_valid_filename("document_1.md") is True

    def test_is_valid_filename_invalid_cases(self):
        assert is_valid_filename("") is False
        assert is_valid_filename("CON.md") is False  # Windows reserved
        assert is_valid_filename("file?.md") is False  # Invalid character
        assert is_valid_filename("file ") is False  # Trailing space
        assert is_valid_filename("file.") is False  # Trailing dot
        assert is_valid_filename(".") is False
        assert is_valid_filename("..") is False

    @patch('src.functions.writer.file_validation.validate_file_access')
    def test_validate_file_inputs_valid(self, mock_validate_access, mock_config):
        test_path = Path("test.md")
        validate_file_inputs(test_path, mock_config)
        mock_validate_access.assert_called_once_with(
            test_path,
            require_write=True,
            create_parents=False,
            check_exists=True
        )

    def test_validate_file_inputs_invalid_extension(self, mock_config):
        test_path = Path("test.txt")
        with pytest.raises(FileValidationError, match="File must have .md extension"):
            validate_file_inputs(test_path, mock_config)

    def test_validate_file_inputs_invalid_filename(self, mock_config):
        test_path = Path("CON.md")  # Windows reserved name
        with pytest.raises(FileValidationError, match="Invalid filename"):
            validate_file_inputs(test_path, mock_config)

    @patch('src.functions.writer.file_validation.validate_file_access')
    def test_validate_file_inputs_permissions(self, mock_validate_access, tmp_path):
        """Test file permission validation in validate_file_inputs."""
        config = Mock(spec=WriterConfig)
        test_file = tmp_path / "test.md"
        test_file.touch()
        
        # Configure mock to raise FilePermissionError
        mock_validate_access.side_effect = FilePermissionError(
            f"Permission denied: No write permission for path: {test_file}"
        )
        
        # Test read-only file
        test_file.chmod(0o444)
        with pytest.raises(FilePermissionError):
            validate_file_inputs(test_file, config, require_write=True)
        
        mock_validate_access.assert_called_once_with(
            test_file,
            require_write=True,
            create_parents=False,
            check_exists=True
        )

    @patch('src.functions.writer.file_validation.validate_file_access')
    def test_validate_file_inputs_parent_creation(self, mock_validate_access, tmp_path):
        """Test parent directory creation in validate_file_inputs."""
        config = Mock(spec=WriterConfig)
        test_file = tmp_path / "subdir" / "test.md"
        
        validate_file_inputs(test_file, config, create_parents=True)
        mock_validate_access.assert_called_with(
            test_file,
            require_write=True,
            create_parents=True,
            check_exists=False
        )

    def test_validate_file_inputs_missing_file(self, tmp_path):
        """Test handling of missing files in validate_file_inputs."""
        config = Mock(spec=WriterConfig)
        non_existent = tmp_path / "missing.md"
        
        with pytest.raises(FileNotFoundError):
            validate_file_inputs(non_existent, config, require_write=False)

# pytest -v tests/functions/writer/test_file_validation.py