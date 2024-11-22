import pytest
from pathlib import Path
import yaml
from datetime import datetime
import re

from src.functions.writer.file_operations import create_document, append_section
from src.functions.writer.config import WriterConfig
from src.functions.writer.exceptions import WriterError
from src.functions.writer.constants import MAX_PATH_LENGTH

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
    
    def test_create_document_special_directory_names(self, test_config, valid_metadata):
        """Test that special directory names are rejected."""
        special_names = [
            ".",
            "..",
            "./",
            "../",
            "./test.md",
            "../test.md",
            "test/./test.md",
            "test/../test.md"
        ]
        
        for filename in special_names:
            with pytest.raises(WriterError, match="Invalid filename"):
                create_document(filename, valid_metadata, test_config)
    
    def test_create_document_valid_dot_filenames(self, test_config, valid_metadata):
        """Test that valid filenames with dots are accepted."""
        valid_dot_filenames = [
            ".test.md",          # Hidden file
            "test.notes.md",     # Multiple dots
            ".hidden.notes.md",  # Hidden with multiple dots
        ]
        
        for filename in valid_dot_filenames:
            try:
                file_path = create_document(filename, valid_metadata, test_config)
                assert file_path.exists()
                assert file_path.name == filename
            except WriterError as e:
                pytest.fail(f"Valid filename '{filename}' was rejected: {str(e)}")
    
    def test_create_document_path_at_limit(self, test_config, valid_metadata):
        """Test that paths exactly at the length limit are accepted."""
        # Calculate available length for filename
        base_path_length = len(str(test_config.drafts_dir)) + 1  # +1 for path separator
        available_length = MAX_PATH_LENGTH - base_path_length
        
        # Create filename that will make the full path exactly MAX_PATH_LENGTH
        filename = f"{'a' * (available_length - 3)}.md"  # -3 for '.md'
        
        try:
            file_path = create_document(filename, valid_metadata, test_config)
            assert file_path.exists()
            assert len(str(file_path)) <= MAX_PATH_LENGTH
        except WriterError as e:
            pytest.fail(f"Valid path length was rejected: {str(e)}")
    
    def test_create_document_path_too_long(self, test_config, valid_metadata):
        """Test error when full path exceeds system limits."""
        # Calculate a length that will exceed MAX_PATH_LENGTH
        base_path_length = len(str(test_config.drafts_dir)) + 1  # +1 for path separator
        excess_length = MAX_PATH_LENGTH - base_path_length + 10  # +10 to exceed limit
        
        filename = f"{'a' * (excess_length - 3)}.md"  # -3 for '.md'
        
        with pytest.raises(WriterError, match="Full path exceeds maximum length"):
            create_document(filename, valid_metadata, test_config)
    
class TestAppendSection:
    @pytest.fixture
    def sample_document(self, test_config, valid_metadata):
        """Create a sample document for testing append operations."""
        file_path = create_document("test_doc.md", valid_metadata, test_config)
        return file_path

    def test_append_section_success(self, sample_document, test_config):
        """Test successful section append with default header level."""
        append_section("test_doc.md", "Test Section", "Test content", test_config)
        
        content = sample_document.read_text(encoding=test_config.default_encoding)
        assert "## Test Section" in content
        assert "<!-- Section: Test Section -->" in content
        assert "Test content" in content

    def test_append_section_with_explicit_header_level(self, sample_document, test_config):
        """Test section append with specified header level."""
        append_section("test_doc.md", "Custom Level", "Content", test_config, header_level=3)
        content = sample_document.read_text()
        assert "### Custom Level" in content

    def test_append_section_to_existing_section(self, sample_document, test_config):
        """Test appending to existing section with allow_append=True."""
        # First append
        append_section("test_doc.md", "Existing", "Original content", test_config)
        # Second append
        append_section("test_doc.md", "Existing", "New content", test_config, allow_append=True)
        
        content = sample_document.read_text()
        assert "Original content" in content
        assert "New content" in content

    def test_append_section_duplicate_error(self, sample_document, test_config):
        """Test error when attempting to add duplicate section."""
        append_section("test_doc.md", "Duplicate", "Content", test_config)
        with pytest.raises(WriterError, match="Section .* already exists"):
            append_section("test_doc.md", "Duplicate", "New content", test_config)

    def test_append_section_invalid_header_level(self, sample_document, test_config):
        """Test error when attempting to use invalid header level."""
        with pytest.raises(WriterError, match="Header level must be an integer between 1 and 6"):
            append_section("test_doc.md", "Invalid", "Content", test_config, header_level=7)

    def test_append_section_file_not_found(self, test_config):
        """Test error when target file doesn't exist."""
        with pytest.raises(WriterError, match="Document does not exist"):
            append_section("nonexistent.md", "Section", "Content", test_config)

    def test_append_section_permission_error(self, sample_document, test_config):
        """Test error when file permissions prevent writing."""
        sample_document.chmod(0o444)  # Read-only
        try:
            with pytest.raises(WriterError, match="Permission denied"):
                append_section("test_doc.md", "Section", "Content", test_config)
        finally:
            sample_document.chmod(0o644)  # Restore permissions

    def test_append_section_header_level_detection(self, sample_document, test_config):
        """Test automatic header level detection based on document structure."""
        # Add a top-level header
        with open(sample_document, "a") as f:
            f.write("\n# Top Level\nContent")
        
        append_section("test_doc.md", "Auto Level", "Content", test_config)
        content = sample_document.read_text()
        assert "## Auto Level" in content  # Should be one level deeper

    def test_append_section_empty_content(self, sample_document, test_config):
        """Test error when attempting to append empty content."""
        with pytest.raises(WriterError, match="Content must be a non-empty string"):
            append_section("test_doc.md", "Empty", "", test_config)

    def test_append_section_empty_title(self, sample_document, test_config):
        """Test error when section title is empty."""
        with pytest.raises(WriterError, match="Section title must be a non-empty string"):
            append_section("test_doc.md", "", "Content", test_config)

    def test_append_section_preserves_existing_content(self, sample_document, test_config):
        """Test that existing document content is preserved when appending."""
        original_content = sample_document.read_text()
        append_section("test_doc.md", "New Section", "New content", test_config)
        new_content = sample_document.read_text()
        assert original_content in new_content

    def test_append_section_proper_spacing(self, sample_document, test_config):
        """Test that proper spacing is maintained between sections."""
        append_section("test_doc.md", "First", "Content 1", test_config)
        append_section("test_doc.md", "Second", "Content 2", test_config)
        content = sample_document.read_text()
        # Check for double newline between sections
        assert "\n\n## First" in content
        assert "\n\n## Second" in content
    
    def test_insert_after_section(self, sample_document, test_config):
        """Test inserting a section after a specific section."""
        # Create initial sections
        append_section("test_doc.md", "First", "Content 1", test_config)
        append_section("test_doc.md", "Last", "Content 3", test_config)
        
        # Insert section between First and Last
        append_section(
            "test_doc.md", 
            "Middle", 
            "Content 2", 
            test_config, 
            insert_after="First"
        )
        
        content = sample_document.read_text()
        sections = re.findall(r'##\s+(.*?)\n', content)
        assert sections == ["First", "Middle", "Last"]

    def test_insert_after_nonexistent_section(self, sample_document, test_config):
        """Test error when inserting after a section that doesn't exist."""
        with pytest.raises(WriterError, match="Section 'Nonexistent' not found"):
            append_section(
                "test_doc.md", 
                "New Section", 
                "Content", 
                test_config, 
                insert_after="Nonexistent"
            )

    def test_insert_after_with_existing_content(self, sample_document, test_config):
        """Test that existing content is preserved when inserting sections."""
        # Create initial content
        append_section("test_doc.md", "First", "Content 1", test_config)
        original_content = sample_document.read_text()
        
        # Insert new section
        append_section(
            "test_doc.md", 
            "Second", 
            "Content 2", 
            test_config, 
            insert_after="First"
        )
        
        new_content = sample_document.read_text()
        assert original_content.strip() in new_content
        assert "Content 2" in new_content

    def test_insert_after_preserves_formatting(self, sample_document, test_config):
        """Test that section formatting is preserved when inserting."""
        # Create sections with specific formatting
        append_section("test_doc.md", "First", "Content 1\n\nWith paragraphs", test_config)
        append_section(
            "test_doc.md", 
            "Middle", 
            "- List item 1\n- List item 2", 
            test_config,
            insert_after="First"
        )
        
        content = sample_document.read_text()
        assert "Content 1\n\nWith paragraphs" in content
        assert "- List item 1\n- List item 2" in content
        
    def test_insert_after_with_nested_sections(self, sample_document, test_config):
        """Test inserting sections with different header levels."""
        # Create nested structure
        append_section("test_doc.md", "Main", "Main content", test_config, header_level=2)
        append_section("test_doc.md", "Sub", "Sub content", test_config, header_level=3)
        
        # Insert between sections
        append_section(
            "test_doc.md",
            "Between",
            "Between content",
            test_config,
            header_level=3,
            insert_after="Main"
        )
        
        content = sample_document.read_text()
        assert "## Main" in content
        assert "### Between" in content
        assert "### Sub" in content

    def test_validate_section_markers(self, sample_document, test_config):
        """Test validation of correctly formatted and placed section markers."""
        # Create a document with multiple properly formatted sections
        content = (
            "---\n"
            "title: Test Document\n"
            "author: Test Author\n"
            "date: 2024-03-21\n"
            "---\n\n"
            "# Introduction\n"
            "<!-- Section: Introduction -->\n"
            "Content of the introduction.\n\n"
            "## Details\n"
            "<!-- Section: Details -->\n"
            "Detailed content.\n"
        )
        
        # Write the content to the test document
        with open(sample_document, "w", encoding=test_config.default_encoding) as f:
            f.write(content)
        
        # Read and validate the content
        with open(sample_document, "r", encoding=test_config.default_encoding) as f:
            document_content = f.read()
        
        # This should not raise any errors
        from src.functions.writer.file_operations import validate_section_markers
        validate_section_markers(document_content)
        
        # Try appending a new section (should work with valid markers)
        append_section(
            "test_doc.md",
            "Conclusion",
            "Final thoughts.",
            test_config
        )
        
        # Verify the new section was added with proper marker
        updated_content = sample_document.read_text()
        assert "## Conclusion" in updated_content
        assert "<!-- Section: Conclusion -->" in updated_content
        assert "Final thoughts." in updated_content

    def test_validate_section_markers_missing_marker(self, sample_document, test_config):
        """Test validation fails when a section header is missing its marker."""
        # Create a document with a missing section marker
        content = (
            "---\n"
            "title: Test Document\n"
            "author: Test Author\n"
            "date: 2024-03-21\n"
            "---\n\n"
            "# Introduction\n"
            "Content of the introduction.\n\n"  # Missing marker here
            "## Details\n"
            "<!-- Section: Details -->\n"
            "Detailed content.\n"
        )
        
        # Write the content to the test document
        with open(sample_document, "w", encoding=test_config.default_encoding) as f:
            f.write(content)
        
        # Read the content
        with open(sample_document, "r", encoding=test_config.default_encoding) as f:
            document_content = f.read()
        
        # Validation should raise an error
        from src.functions.writer.file_operations import validate_section_markers
        with pytest.raises(WriterError, match="Header 'Introduction' is missing its section marker"):
            validate_section_markers(document_content)

# pytest tests/functions/writer/test_file_operations.py