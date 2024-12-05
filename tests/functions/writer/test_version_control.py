import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.functions.writer.version_control import save_version
from src.functions.writer.exceptions import WriterError
from src.functions.writer.metadata_operations import MetadataOperations
from src.functions.writer.config import WriterConfig

@pytest.fixture
def mock_file(tmp_path):
    """Create a mock Markdown file for testing."""
    file_path = tmp_path / "test_document.md"
    file_path.write_text("---\ntitle: Test Document\nauthor: Test Author\nversion: 1\n---\n# Content")
    return file_path

@pytest.fixture
def mock_metadata_operations():
    """Mock the MetadataOperations class."""
    with patch('src.functions.writer.version_control.MetadataOperations') as MockMetadataOps:
        mock_instance = MockMetadataOps.return_value
        mock_instance.get_metadata.return_value = {'version': '1'}
        yield mock_instance

@pytest.fixture
def config():
    """Provide a WriterConfig instance for testing."""
    return WriterConfig()

def test_save_version_success(mock_file, mock_metadata_operations, config):
    """Test successful version creation."""
    version_path = save_version(mock_file, config)
    assert Path(version_path).exists()
    assert Path(version_path).name == "test_document_v2.md"
    mock_metadata_operations.update_metadata.assert_called_once()

def test_save_version_no_metadata(tmp_path, mock_metadata_operations, config):
    """Test versioning without metadata."""
    file_path = tmp_path / "no_metadata.md"
    file_path.write_text("# Test\nContent")
    mock_metadata_operations.get_metadata.return_value = {}
    version_path = save_version(file_path, config)
    assert Path(version_path).exists()
    assert Path(version_path).name == "no_metadata_v1.md"
    mock_metadata_operations.update_metadata.assert_not_called()

def test_save_version_existing_versions(mock_file, mock_metadata_operations, config):
    """Test handling of existing version files."""
    v2_path = mock_file.parent / "test_document_v2.md"
    v2_path.touch()
    
    version_path = save_version(mock_file, config)
    assert Path(version_path).name == "test_document_v3.md"
    mock_metadata_operations.update_metadata.assert_called_once()

def test_save_version_error_handling(mock_file, mock_metadata_operations, config):
    """Test error handling during version creation."""
    mock_metadata_operations.get_metadata.side_effect = Exception("Metadata error")
    with pytest.raises(WriterError) as excinfo:
        save_version(mock_file, config)
    assert "Failed to create version" in str(excinfo.value)

# pytest tests/functions/writer/test_version_control.py -v
