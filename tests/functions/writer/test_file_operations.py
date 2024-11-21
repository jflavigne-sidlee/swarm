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
        try:
            # Make drafts directory read-only
            test_config.drafts_dir.mkdir(parents=True, exist_ok=True)
            test_config.drafts_dir.chmod(0o444)  # Read-only
            
            with pytest.raises(WriterError, match="Permission denied"):
                create_document("test_doc.md", valid_metadata, test_config)
        finally:
            # Restore permissions for cleanup
            try:
                test_config.drafts_dir.chmod(0o755)
            except Exception:
                pass
    
    def test_create_document_permission_error_on_exists_check(self, test_config, valid_metadata):
        """Test error when checking file existence fails due to permissions."""
        try:
            # Create directory structure but make it unreadable
            test_config.drafts_dir.mkdir(parents=True, exist_ok=True)
            test_config.drafts_dir.chmod(0o000)  # No permissions
            
            with pytest.raises(WriterError, match="Permission denied"):
                create_document("test_doc.md", valid_metadata, test_config)
        finally:
            # Restore permissions for cleanup
            try:
                test_config.drafts_dir.chmod(0o755)
            except Exception:
                pass
    
    def test_create_document_invalid_filename(self, test_config, valid_metadata):
        """Test error when filename contains invalid characters or patterns."""
        invalid_filenames = [
            # Empty or too long
            "",  # Empty string
            "a" * 256,  # Too long (>255 chars)
            
            # Forbidden characters
            "test/doc.md",  # Forward slash
            "test\\doc.md",  # Backslash
            "test:doc.md",  # Colon
            "test*doc.md",  # Asterisk
            "test?doc.md",  # Question mark
            "test\"doc.md",  # Quote
            "test<doc.md",  # Less than
            "test>doc.md",  # Greater than
            "test|doc.md",  # Pipe
            "test\0doc.md",  # Null character
            
            # Reserved Windows filenames
            "CON.md",
            "PRN.md",
            "AUX.md",
            "NUL.md",
            "COM1.md",
            "COM2.md",
            "COM3.md",
            "COM4.md",
            "LPT1.md",
            "LPT2.md",
            "LPT3.md",
            "LPT4.md",
            
            # Trailing characters
            "test ",  # Space at end
            "test.",  # Dot at end
            "test.md ",  # Space after extension
            "test.md."  # Dot after extension
        ]
        
        for filename in invalid_filenames:
            with pytest.raises(WriterError, match="Invalid filename"):
                create_document(filename, valid_metadata, test_config)
    
    def test_create_document_valid_filename(self, test_config, valid_metadata):
        """Test that valid filenames are accepted."""
        valid_filenames = [
            "test.md",
            "test_doc.md",
            "test-doc.md",
            "test123.md",
            "Test Doc.md",  # Spaces in middle are ok
            "test.doc.md",  # Multiple dots ok
            "._test.md",    # Leading dot/underscore ok
            "UPPERCASE.md",
            "αβγ.md",       # Unicode ok
        ]
        
        for filename in valid_filenames:
            try:
                file_path = create_document(filename, valid_metadata, test_config)
                assert file_path.exists()
                assert file_path.name == filename
            except WriterError as e:
                pytest.fail(f"Valid filename '{filename}' was rejected: {str(e)}")
    
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
    
    def test_create_document_preserves_metadata_order(self, test_config):
        """Test that metadata order is preserved in the YAML frontmatter."""
        ordered_metadata = {
            "title": "Test Document",
            "author": "Test Author",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "category": "Test",
            "tags": "test, example"
        }
        
        file_path = create_document("test_doc.md", ordered_metadata, test_config)
        
        # Read the created file
        content = file_path.read_text(encoding=test_config.default_encoding)
        yaml_content = content.split('---')[1].strip()
        
        # Check that fields appear in the same order
        expected_order = list(ordered_metadata.keys())
        actual_order = [line.split(':')[0].strip() for line in yaml_content.split('\n')]
        
        assert actual_order == expected_order, "Metadata fields are not in the expected order"
            
            
# pytest tests/functions/writer/test_file_operations.py