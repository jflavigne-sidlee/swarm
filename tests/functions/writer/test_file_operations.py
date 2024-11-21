import pytest
from pathlib import Path
import yaml
from datetime import datetime

from src.functions.writer.file_operations import create_document
from src.functions.writer.config import WriterConfig
from src.functions.writer.exceptions import WriterError

@pytest.fixture
def test_config(tmp_path):
    """Create a test configuration using temporary directory."""
    return WriterConfig.from_dict({
        "temp_dir": tmp_path / "temp",
        "drafts_dir": tmp_path / "drafts",
        "finalized_dir": tmp_path / "finalized",
        "create_directories": True
    })

@pytest.fixture
def valid_metadata():
    """Return valid metadata for testing."""
    return {
        "title": "Test Document",
        "author": "Test Author",
        "date": datetime.now().strftime("%Y-%m-%d")
    }

class TestCreateDocument:
    def test_create_document_success(self, test_config, valid_metadata):
        """Test successful document creation with valid inputs."""
        file_name = "test_doc.md"
        file_path = create_document(file_name, valid_metadata, test_config)
        
        # Verify file exists
        assert file_path.exists()
        
        # Verify content structure
        content = file_path.read_text(encoding=test_config.default_encoding)
        assert content.startswith('---\n')  # Has YAML front matter
        
        # Parse YAML front matter
        yaml_content = yaml.safe_load(content.split('---')[1])
        assert yaml_content == valid_metadata
    
    def test_create_document_adds_md_extension(self, test_config, valid_metadata):
        """Test that .md extension is added if missing."""
        file_name = "test_doc"  # No extension
        file_path = create_document(file_name, valid_metadata, test_config)
        assert file_path.suffix == '.md'
        
    def test_create_document_file_exists(self, test_config, valid_metadata):
        """Test error when file already exists."""
        file_name = "existing_doc.md"
        
        # Create file first time
        create_document(file_name, valid_metadata, test_config)
        
        # Attempt to create again should raise error
        with pytest.raises(WriterError, match="File already exists"):
            create_document(file_name, valid_metadata, test_config)
    
    def test_create_document_missing_metadata(self, test_config):
        """Test error when required metadata is missing."""
        incomplete_metadata = {
            "title": "Test Document"
            # Missing author and date
        }
        
        with pytest.raises(WriterError, match="Missing required metadata fields"):
            create_document("test_doc.md", incomplete_metadata, test_config)
    
    def test_create_document_default_config(self, valid_metadata, tmp_path, monkeypatch):
        """Test document creation with default configuration."""
        # Temporarily set environment variable for drafts directory
        monkeypatch.setenv("WRITER_DRAFTS_DIR", str(tmp_path / "drafts"))
        
        file_path = create_document("test_doc.md", valid_metadata)
        assert file_path.exists()
        assert tmp_path in file_path.parents
    
    def test_create_document_invalid_permissions(self, test_config, valid_metadata):
        """Test error when directory cannot be created or written to."""
        # Make drafts directory read-only
        test_config.drafts_dir.mkdir(parents=True, exist_ok=True)
        test_config.drafts_dir.chmod(0o444)  # Read-only
        
        with pytest.raises(WriterError, match="Failed to create document"):
            create_document("test_doc.md", valid_metadata, test_config) 
    
    def test_create_document_invalid_filename(self, test_config, valid_metadata):
        """Test error when filename contains invalid characters."""
        invalid_filenames = [
            "test/doc.md",  # Contains path separator
            "",  # Empty string
            "test\0doc.md"  # Contains null character
        ]
        
        for filename in invalid_filenames:
            with pytest.raises(WriterError, match="Invalid filename"):
                create_document(filename, valid_metadata, test_config)
    
    def test_create_document_invalid_metadata_types(self, test_config):
        """Test error when metadata contains invalid types."""
        invalid_metadata = {
            "title": ["Not", "A", "String"],  # List instead of string
            "author": "Test Author",
            "date": datetime.now()  # datetime object instead of string
        }
        
        with pytest.raises(WriterError, match="Invalid metadata type"):
            create_document("test_doc.md", invalid_metadata, test_config)
    
    def test_create_document_directory_creation_failure(self, test_config, valid_metadata):
        """Test error when directory cannot be created."""
        # Remove the drafts directory if it exists
        if test_config.drafts_dir.exists():
            test_config.drafts_dir.rmdir()
            
        # Create a file where the directory should be
        with open(test_config.drafts_dir, 'w') as f:
            f.write('blocking file')
        
        with pytest.raises(WriterError, match="Cannot create directory"):
            create_document("test_doc.md", valid_metadata, test_config)
    
    def test_create_document_yaml_error(self, test_config):
        """Test error when metadata cannot be serialized to YAML."""
        class UnserializableObject:
            pass
        
        invalid_metadata = {
            "title": "Test Document",
            "author": "Test Author",
            "date": UnserializableObject()  # This object can't be serialized to YAML
        }
        
        with pytest.raises(WriterError, match="Invalid metadata type"):
            create_document("test_doc.md", invalid_metadata, test_config)
            
            
# pytest tests/functions/writer/test_file_operations.py