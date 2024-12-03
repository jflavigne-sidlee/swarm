import pytest
from pathlib import Path
from unittest.mock import Mock, patch

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

    @patch('src.functions.writer.file_validation.validate_path_permissions')
    def test_validate_file_inputs_valid(self, mock_validate_perms, mock_config):
        test_path = Path("test.md")
        with patch.object(Path, 'exists', return_value=True):
            validate_file_inputs(test_path, mock_config)
            mock_validate_perms.assert_called_once()

    def test_validate_file_inputs_invalid_extension(self, mock_config):
        test_path = Path("test.txt")
        with pytest.raises(FileValidationError, match="File must have .md extension"):
            validate_file_inputs(test_path, mock_config)

    def test_validate_file_inputs_invalid_filename(self, mock_config):
        test_path = Path("CON.md")  # Windows reserved name
        with pytest.raises(FileValidationError, match="Invalid filename"):
            validate_file_inputs(test_path, mock_config)

    @patch('src.functions.writer.file_validation.validate_path_permissions')
    @patch('src.functions.writer.file_validation.ensure_parent_exists')
    def test_ensure_valid_markdown_file_create(
        self, mock_ensure_parent, mock_validate_perms, mock_config
    ):
        test_path = Path("test.md")
        with patch.object(Path, 'exists', return_value=False), \
             patch.object(Path, 'touch') as mock_touch:
            ensure_valid_markdown_file(test_path, mock_config, create=True)
            mock_touch.assert_called_once()

    def test_ensure_valid_markdown_file_invalid(self, mock_config):
        test_path = Path("invalid?.md")
        with pytest.raises(FileValidationError):
            ensure_valid_markdown_file(test_path, mock_config) 

# pytest -v tests/functions/writer/test_file_validation.py