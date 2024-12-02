import pytest
from pathlib import Path
import yaml
from datetime import datetime
import re
from unittest.mock import patch, mock_open

from src.functions.writer.file_operations import (
    create_document,
    append_section,
    validate_section_markers,
    edit_section,
    find_section,
    find_marker_positions,
    get_section_marker_position,
    get_section,
    section_exists,
)
from src.functions.writer.config import WriterConfig
from src.functions.writer.exceptions import WriterError, SectionNotFoundError, FileValidationError, FilePermissionError
from src.functions.writer.validation_constants import (
    MAX_PATH_LENGTH,
)
from src.functions.writer.patterns import (
    PATTERN_SECTION_MARKER,
)
from src.functions.writer.errors import (
    ERROR_DOCUMENT_NOT_EXIST,
    ERROR_INVALID_SECTION_TITLE,
)

@pytest.fixture
def test_config(tmp_path):
    """Create a test configuration using temporary directory."""
    return WriterConfig.from_dict(
        {
            "temp_dir": tmp_path / "temp",
            "drafts_dir": tmp_path / "drafts",
            "finalized_dir": tmp_path / "finalized",
            "create_directories": True,
        }
    )


@pytest.fixture
def valid_metadata():
    """Return valid metadata for testing."""
    return {
        "title": "Test Document",
        "author": "Test Author",
        "date": datetime.now().strftime("%Y-%m-%d"),
    }


@pytest.fixture
def sample_document(test_config) -> Path:
    """Create a sample document for testing."""
    test_config.drafts_dir.mkdir(parents=True, exist_ok=True)
    return test_config.drafts_dir / "test_doc.md"


class TestCreateDocument:
    def test_create_document_success(self, test_config, valid_metadata):
        """Test successful document creation with valid inputs."""
        file_name = "test_doc.md"
        file_path = create_document(file_name, valid_metadata, test_config)

        # Verify file exists
        assert file_path.exists()

        # Verify content structure
        content = file_path.read_text(encoding=test_config.default_encoding)
        assert content.startswith("---\n")  # Has YAML front matter

        # Parse YAML front matter
        yaml_content = yaml.safe_load(content.split("---")[1])
        assert yaml_content == valid_metadata

    def test_create_document_adds_md_extension(self, test_config, valid_metadata):
        """Test that .md extension is added if missing."""
        file_name = "test_doc"  # No extension
        file_path = create_document(file_name, valid_metadata, test_config)
        assert file_path.suffix == ".md"

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

    def test_create_document_default_config(
        self, valid_metadata, tmp_path, monkeypatch
    ):
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

    def test_create_document_permission_error_on_exists_check(
        self, test_config, valid_metadata
    ):
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
            'test"doc.md',  # Quote
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
            "test.md.",  # Dot after extension
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
            "._test.md",  # Leading dot/underscore ok
            "UPPERCASE.md",
            "αβγ.md",  # Unicode ok
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
            "date": datetime.now(),  # datetime object instead of string
        }

        with pytest.raises(WriterError, match="Invalid type for"):
            create_document("test_doc.md", invalid_metadata, test_config)

    def test_create_document_directory_creation_failure(
        self, test_config, valid_metadata
    ):
        """Test error when directory cannot be created."""
        # Remove the drafts directory if it exists
        if test_config.drafts_dir.exists():
            test_config.drafts_dir.rmdir()

        # Create a file where the directory should be
        with open(test_config.drafts_dir, "w") as f:
            f.write("blocking file")

        with pytest.raises(WriterError, match="Cannot create directory"):
            create_document("test_doc.md", valid_metadata, test_config)

    def test_create_document_yaml_error(self, test_config):
        """Test error when metadata cannot be serialized to YAML."""

        class UnserializableObject:
            pass

        invalid_metadata = {
            "title": "Test Document",
            "author": "Test Author",
            "date": UnserializableObject(),  # This object can't be serialized to YAML
        }

        with pytest.raises(WriterError, match="Invalid type for"):
            create_document("test_doc.md", invalid_metadata, test_config)

    def test_create_document_preserves_metadata_order(self, test_config):
        """Test that metadata order is preserved in the YAML frontmatter."""
        ordered_metadata = {
            "title": "Test Document",
            "author": "Test Author",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "category": "Test",
            "tags": "test, example",
        }

        file_path = create_document("test_doc.md", ordered_metadata, test_config)

        # Read the created file
        content = file_path.read_text(encoding=test_config.default_encoding)
        yaml_content = content.split("---")[1].strip()

        # Check that fields appear in the same order
        expected_order = list(ordered_metadata.keys())
        actual_order = [line.split(":")[0].strip() for line in yaml_content.split("\n")]

        assert (
            actual_order == expected_order
        ), "Metadata fields are not in the expected order"

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
            "test/../test.md",
        ]

        for filename in special_names:
            with pytest.raises(WriterError, match="Invalid filename"):
                create_document(filename, valid_metadata, test_config)

    def test_create_document_valid_dot_filenames(self, test_config, valid_metadata):
        """Test that valid filenames with dots are accepted."""
        valid_dot_filenames = [
            ".test.md",  # Hidden file
            "test.notes.md",  # Multiple dots
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

    def test_append_section_with_explicit_header_level(
        self, sample_document, test_config
    ):
        """Test section append with specified header level."""
        append_section(
            "test_doc.md", "Custom Level", "Content", test_config, header_level=3
        )
        content = sample_document.read_text()
        assert "### Custom Level" in content

    def test_append_section_to_existing_section(self, sample_document, test_config):
        """Test appending to existing section with allow_append=True."""
        # First append
        append_section("test_doc.md", "Existing", "Original content", test_config)
        # Second append
        append_section(
            "test_doc.md", "Existing", "New content", test_config, allow_append=True
        )

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
        with pytest.raises(
            WriterError, match="Header level must be an integer between 1 and 6"
        ):
            append_section(
                "test_doc.md", "Invalid", "Content", test_config, header_level=7
            )

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
        with pytest.raises(
            WriterError, match="Section title must be a non-empty string"
        ):
            append_section("test_doc.md", "", "Content", test_config)

    def test_append_section_preserves_existing_content(
        self, sample_document, test_config
    ):
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
            "test_doc.md", "Middle", "Content 2", test_config, insert_after="First"
        )

        content = sample_document.read_text()
        sections = re.findall(r"##\s+(.*?)\n", content)
        assert sections == ["First", "Middle", "Last"]

    def test_insert_after_nonexistent_section(self, sample_document, test_config):
        """Test error when inserting after a section that doesn't exist."""
        with pytest.raises(WriterError, match="Section to insert after not found: Nonexistent"):
            append_section(
                file_name="test_doc.md",
                section_title="New Section",
                content="Content",
                config=test_config,
                insert_after="Nonexistent"
            )

    def test_insert_after_with_existing_content(self, sample_document, test_config):
        """Test that existing content is preserved when inserting sections."""
        # Create initial content
        append_section("test_doc.md", "First", "Content 1", test_config)
        original_content = sample_document.read_text()

        # Insert new section
        append_section(
            "test_doc.md", "Second", "Content 2", test_config, insert_after="First"
        )

        new_content = sample_document.read_text()
        assert original_content.strip() in new_content
        assert "Content 2" in new_content

    def test_insert_after_preserves_formatting(self, sample_document, test_config):
        """Test that section formatting is preserved when inserting."""
        # Create sections with specific formatting
        append_section(
            "test_doc.md", "First", "Content 1\n\nWith paragraphs", test_config
        )
        append_section(
            "test_doc.md",
            "Middle",
            "- List item 1\n- List item 2",
            test_config,
            insert_after="First",
        )

        content = sample_document.read_text()
        assert "Content 1\n\nWith paragraphs" in content
        assert "- List item 1\n- List item 2" in content

    def test_insert_after_with_nested_sections(self, sample_document, test_config):
        """Test inserting sections with different header levels."""
        # Create nested structure
        append_section(
            "test_doc.md", "Main", "Main content", test_config, header_level=2
        )
        append_section("test_doc.md", "Sub", "Sub content", test_config, header_level=3)

        # Insert between sections
        append_section(
            "test_doc.md",
            "Between",
            "Between content",
            test_config,
            header_level=3,
            insert_after="Main",
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
        append_section("test_doc.md", "Conclusion", "Final thoughts.", test_config)

        # Verify the new section was added with proper marker
        updated_content = sample_document.read_text()
        assert "## Conclusion" in updated_content
        assert "<!-- Section: Conclusion -->" in updated_content
        assert "Final thoughts." in updated_content

    def test_validate_section_markers_missing_marker(
        self, sample_document, test_config
    ):
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

        with pytest.raises(
            WriterError, match="Header 'Introduction' is missing its section marker"
        ):
            validate_section_markers(document_content)

    def test_validate_section_markers_misplaced_marker(
        self, sample_document, test_config
    ):
        """Test validation fails when a section marker is not immediately after its header."""
        # Create a document with a misplaced section marker
        content = (
            "---\n"
            "title: Test Document\n"
            "author: Test Author\n"
            "date: 2024-03-21\n"
            "---\n\n"
            "# Introduction\n"
            "Content of the introduction.\n"
            "<!-- Section: Introduction -->\n\n"  # Marker after content instead of header
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

        with pytest.raises(
            WriterError, match="Header 'Introduction' is missing its section marker"
        ):
            validate_section_markers(document_content)

    def test_validate_section_markers_mismatched_title(
        self, sample_document, test_config
    ):
        """Test validation fails when a section marker title doesn't match its header."""
        # Create a document with a mismatched section marker
        content = (
            "---\n"
            "title: Test Document\n"
            "author: Test Author\n"
            "date: 2024-03-21\n"
            "---\n\n"
            "# Introduction\n"
            "<!-- Section: Intro -->\n"  # Marker doesn't match header title
            "Content of the introduction.\n\n"
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

        with pytest.raises(
            WriterError,
            match="Section marker for 'Introduction' does not match header title",
        ):
            validate_section_markers(document_content)

    def test_validate_section_markers_duplicate_markers(
        self, sample_document, test_config
    ):
        """Test validation fails when duplicate section markers exist."""
        # Create a document with duplicate section markers
        content = (
            "---\n"
            "title: Test Document\n"
            "author: Test Author\n"
            "date: 2024-03-21\n"
            "---\n\n"
            "# Introduction\n"
            "<!-- Section: Introduction -->\n"
            "Content of the introduction.\n\n"
            "# Another Section\n"
            "<!-- Section: Introduction -->\n"  # Duplicate marker
            "Additional content.\n"
        )

        # Write the content to the test document
        with open(sample_document, "w", encoding=test_config.default_encoding) as f:
            f.write(content)

        # Read the content
        with open(sample_document, "r", encoding=test_config.default_encoding) as f:
            document_content = f.read()

        # Validation should raise an error
        from src.functions.writer.file_operations import validate_section_markers

        with pytest.raises(
            WriterError, match="Duplicate section marker found: 'Introduction'"
        ):
            validate_section_markers(document_content)

    def test_validate_section_markers_orphaned_marker(
        self, sample_document, test_config
    ):
        """Test validation fails when a marker exists without a corresponding header."""
        # Create a document with a marker but no header
        content = (
            "---\n"
            "title: Test Document\n"
            "author: Test Author\n"
            "date: 2024-03-21\n"
            "---\n\n"
            "<!-- Section: Introduction -->\n"  # Marker without header
            "Content of the introduction.\n\n"
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

        with pytest.raises(
            WriterError,
            match="Found marker 'Introduction' without a corresponding header",
        ):
            validate_section_markers(document_content)

    def test_validate_section_markers_empty_section(self, sample_document, test_config):
        """Test validation fails when a header has no content or marker."""
        # Create a document with a header but no marker or content
        content = (
            "---\n"
            "title: Test Document\n"
            "author: Test Author\n"
            "date: 2024-03-21\n"
            "---\n\n"
            "# Empty Section\n\n"  # Header with no marker
            "# Another Section\n"
            "<!-- Section: Another Section -->\n"
            "Some content here.\n"
        )

        # Write the content to the test document
        with open(sample_document, "w", encoding=test_config.default_encoding) as f:
            f.write(content)

        # Read the content
        with open(sample_document, "r", encoding=test_config.default_encoding) as f:
            document_content = f.read()

        # Validation should raise an error
        from src.functions.writer.file_operations import validate_section_markers

        with pytest.raises(
            WriterError, match="Header 'Empty Section' is missing its section marker"
        ):
            validate_section_markers(document_content)

    def test_validate_section_markers_nested_headers(
        self, sample_document, test_config
    ):
        """Test validation succeeds with nested header structure."""
        # Create a document with nested headers and their markers
        content = (
            "---\n"
            "title: Test Document\n"
            "author: Test Author\n"
            "date: 2024-03-21\n"
            "---\n\n"
            "# Main Section\n"
            "<!-- Section: Main Section -->\n"
            "Content here.\n\n"
            "## Subsection\n"
            "<!-- Section: Subsection -->\n"
            "More content.\n\n"
            "### Deep Subsection\n"
            "<!-- Section: Deep Subsection -->\n"
            "Even more content.\n\n"
            "## Another Subsection\n"
            "<!-- Section: Another Subsection -->\n"
            "Final content.\n"
        )

        # Write the content to the test document
        with open(sample_document, "w", encoding=test_config.default_encoding) as f:
            f.write(content)

        # Read the content
        with open(sample_document, "r", encoding=test_config.default_encoding) as f:
            document_content = f.read()

        # Validation should succeed without raising any errors
        from src.functions.writer.file_operations import validate_section_markers

        validate_section_markers(document_content)  # Should not raise any exceptions

    def test_validate_section_markers_malformed_marker(
        self, sample_document, test_config
    ):
        """Test validation fails when markers don't follow the expected format."""
        # Create a document with malformed markers
        content = (
            "---\n"
            "title: Test Document\n"
            "author: Test Author\n"
            "date: 2024-03-21\n"
            "---\n\n"
            "# Introduction\n"
            "<!-- SECTION: Introduction -->\n"  # Wrong format (uppercase SECTION)
            "Content here.\n\n"
            "# Details\n"
            "<!-- Section: Details -->\n"  # Correct format for comparison
            "More content.\n"
        )

        # Write the content to the test document
        with open(sample_document, "w", encoding=test_config.default_encoding) as f:
            f.write(content)

        # Read the content
        with open(sample_document, "r", encoding=test_config.default_encoding) as f:
            document_content = f.read()

        # Validation should raise an error
        from src.functions.writer.file_operations import validate_section_markers

        with pytest.raises(
            WriterError,
            match="Section marker for 'Introduction' does not match header title",
        ):
            validate_section_markers(document_content)

    def test_validate_section_markers_empty_document(
        self, sample_document, test_config
    ):
        """Test validation succeeds with a completely empty document."""
        # Create an empty document
        content = ""

        # Write the content to the test document
        with open(sample_document, "w", encoding=test_config.default_encoding) as f:
            f.write(content)

        # Read the content
        with open(sample_document, "r", encoding=test_config.default_encoding) as f:
            document_content = f.read()

        # Validation should succeed without raising any errors
        from src.functions.writer.file_operations import validate_section_markers

        validate_section_markers(document_content)  # Should not raise any exceptions

        # Also test with just whitespace
        content_whitespace = "\n\n  \n\t\n"
        with open(sample_document, "w", encoding=test_config.default_encoding) as f:
            f.write(content_whitespace)

        with open(sample_document, "r", encoding=test_config.default_encoding) as f:
            document_content = f.read()

        # Should also succeed with whitespace-only content
        validate_section_markers(document_content)  # Should not raise any exceptions

    def test_validate_section_markers_large_document(
        self, sample_document, test_config
    ):
        """Test validation performance with a large document containing many sections."""
        # Create a large document with 1000 sections
        sections = []
        sections.append(
            "---\n"
            "title: Large Test Document\n"
            "author: Test Author\n"
            "date: 2024-03-21\n"
            "---\n\n"
        )

        # Generate 1000 sections with proper headers and markers
        for i in range(1000):
            section_title = f"Section {i}"
            sections.extend(
                [
                    f"# {section_title}\n",
                    f"<!-- Section: {section_title} -->\n",
                    f"Content for section {i}.\n\n",
                ]
            )

        content = "".join(sections)

        # Write the large content to the test document
        with open(sample_document, "w", encoding=test_config.default_encoding) as f:
            f.write(content)

        # Read the content
        with open(sample_document, "r", encoding=test_config.default_encoding) as f:
            document_content = f.read()

        # Time the validation
        import time

        start_time = time.time()

        # Validation should succeed without raising any errors
        from src.functions.writer.file_operations import validate_section_markers

        validate_section_markers(document_content)

        end_time = time.time()
        execution_time = end_time - start_time

        # Assert reasonable performance (should complete in under 1 second)
        assert (
            execution_time < 1.0
        ), f"Validation took too long: {execution_time:.2f} seconds"

    def test_validate_section_markers_highly_nested(self, sample_document, test_config):
        """Test validation succeeds with deeply nested header structure (h1 to h6)."""
        # Create a document with headers at every level
        content = (
            "---\n"
            "title: Nested Test Document\n"
            "author: Test Author\n"
            "date: 2024-03-21\n"
            "---\n\n"
            "# Level 1\n"
            "<!-- Section: Level 1 -->\n"
            "Top level content.\n\n"
            "## Level 2\n"
            "<!-- Section: Level 2 -->\n"
            "Second level content.\n\n"
            "### Level 3\n"
            "<!-- Section: Level 3 -->\n"
            "Third level content.\n\n"
            "#### Level 4\n"
            "<!-- Section: Level 4 -->\n"
            "Fourth level content.\n\n"
            "##### Level 5\n"
            "<!-- Section: Level 5 -->\n"
            "Fifth level content.\n\n"
            "###### Level 6\n"
            "<!-- Section: Level 6 -->\n"
            "Deepest level content.\n\n"
            "## Back to Level 2\n"
            "<!-- Section: Back to Level 2 -->\n"
            "Testing level transitions.\n\n"
            "### Another Level 3\n"
            "<!-- Section: Another Level 3 -->\n"
            "Testing sibling sections.\n"
        )

        # Write the content to the test document
        with open(sample_document, "w", encoding=test_config.default_encoding) as f:
            f.write(content)

        # Read the content
        with open(sample_document, "r", encoding=test_config.default_encoding) as f:
            document_content = f.read()

        # Validation should succeed without raising any errors
        from src.functions.writer.file_operations import validate_section_markers

        validate_section_markers(document_content)  # Should not raise any exceptions

    def test_append_section_with_marker_validation(self, sample_document, test_config):
        """Test appending a new section validates and adds markers correctly."""
        # Create initial document with existing sections
        initial_content = (
            "---\n"
            "title: Test Document\n"
            "author: Test Author\n"
            "date: 2024-03-21\n"
            "---\n\n"
            "# Main Section\n"
            "<!-- Section: Main Section -->\n"
            "Initial content.\n\n"
            "## First Subsection\n"
            "<!-- Section: First Subsection -->\n"
            "Some content.\n\n"
        )

        # Write initial content
        with open(sample_document, "w", encoding=test_config.default_encoding) as f:
            f.write(initial_content)

        # Append new section
        append_section(
            file_name=sample_document.name,  # Just the filename, not the full path
            section_title="New Section",
            content="Content for the new section.",
            config=test_config,  # Config contains the directory information
            header_level=2,  # ## level
        )

        # Read the updated content
        with open(sample_document, "r", encoding=test_config.default_encoding) as f:
            updated_content = f.read()

        # Verify the new section was added with correct marker
        expected_new_section = (
            "## New Section\n"
            "<!-- Section: New Section -->\n"
            "Content for the new section.\n"
        )
        assert expected_new_section in updated_content

        # Validate all markers in the updated document
        validate_section_markers(updated_content)  # Should not raise any exceptions

        # Verify the original content is preserved
        assert "# Main Section" in updated_content
        assert "<!-- Section: Main Section -->" in updated_content
        assert "## First Subsection" in updated_content
        assert "<!-- Section: First Subsection -->" in updated_content


class TestEditSection:
    def test_edit_section_basic(self, sample_document, test_config):
        """Test basic section editing functionality."""
        # Create initial document with a section to edit
        initial_content = (
            "---\n"
            "title: Test Document\n"
            "author: Test Author\n"
            "date: 2024-03-21\n"
            "---\n\n"
            "# Introduction\n"
            "<!-- Section: Introduction -->\n"
            "Original content.\n\n"
            "## Methods\n"
            "<!-- Section: Methods -->\n"
            "Old methods content.\n\n"
        )
        sample_document.write_text(initial_content, encoding=test_config.default_encoding)

        # Edit the 'Methods' section
        new_content = "This is the methods section.\n\n"
        edit_section(sample_document.name, "Methods", new_content, test_config)

        # Read the updated content
        updated_content = sample_document.read_text(encoding=test_config.default_encoding)

        # Verify the section was updated correctly
        section_match = find_section(updated_content, "Methods")
        assert section_match is not None, "Section 'Methods' should be found."
        expected_header = "## Methods\n"
        expected_content = "This is the methods section.\n\n"

        assert section_match.group('header') == expected_header, "The header does not match."
        assert section_match.group('section_content') == expected_content, "The content does not match."


class TestFindSection:
    def test_find_section_basic(self):
        """Test that find_section correctly locates a section in the content."""
        content = (
            "# Introduction\n"
            "<!-- Section: Introduction -->\n"
            "Some introduction text.\n\n"
            "## Methods\n"
            "<!-- Section: Methods -->\n"
            "Details about methods.\n\n"
            "## Results\n"
            "<!-- Section: Results -->\n"
            "Results go here.\n\n"
            "# Conclusion\n"
            "<!-- Section: Conclusion -->\n"
            "Conclusion content.\n\n"
        )
        
        section_match = find_section(content, "Methods")
        assert section_match is not None, "Section 'Methods' should be found."
        
        # Test individual components
        assert section_match.group('header') == "## Methods\n"
        assert section_match.group('marker') == "<!-- Section: Methods -->\n"
        assert section_match.group('section_content') == "Details about methods.\n\n"
        
        # Remove backward compatibility test
        # assert section_match.group(1) == "## Methods\n"
        # assert section_match.group(2) == "Details about methods.\n\n"

    def test_find_section_with_special_characters(self):
        """Test finding sections with special characters in title."""
        content = (
            "# Special (Test) Section!\n"
            "<!-- Section: Special (Test)! -->\n"
            "Special content.\n\n"
            "## Next\n"
            "<!-- Section: Next -->\n"
            "Next content.\n\n"
        )

        section_match = find_section(content, "Special (Test)!")
        assert section_match is not None
        assert section_match.group('header') == "# Special (Test) Section!\n"
        assert section_match.group('marker') == "<!-- Section: Special (Test)! -->\n"
        assert section_match.group('section_content').strip() == "Special content."


class TestMarkerUtilities:
    """Tests for marker utility functions."""

    def test_find_marker_positions_basic(self):
        """Test basic marker position finding."""
        content = (
            "# Header\n"
            "<!-- Section: First -->\n"
            "Content 1\n\n"
            "# Another Header\n"
            "<!-- Section: Second -->\n"
            "Content 2"
        )
        
        positions = find_marker_positions(content, PATTERN_SECTION_MARKER)
        assert len(positions) == 2
        
        # Verify first marker position
        start1, end1 = positions[0]
        assert content[start1:end1] == "<!-- Section: First -->"
        
        # Verify second marker position
        start2, end2 = positions[1]
        assert content[start2:end2] == "<!-- Section: Second -->"

    def test_find_marker_positions_no_markers(self):
        """Test when no markers are present."""
        content = "# Header\nJust some content\n# Another header\nMore content"
        positions = find_marker_positions(content, PATTERN_SECTION_MARKER)
        assert positions == []

    def test_find_marker_positions_with_special_chars(self):
        """Test finding markers with special characters."""
        content = (
            "# Header (Test)!\n"
            "<!-- Section: Special (Test)! -->\n"
            "Content with special chars: @#$%"
        )
        
        positions = find_marker_positions(content, PATTERN_SECTION_MARKER)
        assert len(positions) == 1
        start, end = positions[0]
        assert content[start:end] == "<!-- Section: Special (Test)! -->"

    def test_get_section_marker_position_found(self):
        """Test finding a specific section marker."""
        content = (
            "# Introduction\n"
            "<!-- Section: Introduction -->\n"
            "Some content\n\n"
            "# Conclusion\n"
            "<!-- Section: Conclusion -->\n"
            "More content"
        )
        
        start, end = get_section_marker_position(content, "Introduction")
        assert start != -1
        assert end != -1
        assert content[start:end] == "<!-- Section: Introduction -->"

    def test_get_section_marker_position_not_found(self):
        """Test when the requested section marker is not found."""
        content = (
            "# Introduction\n"
            "<!-- Section: Introduction -->\n"
            "Some content"
        )
        
        start, end = get_section_marker_position(content, "NonExistent")
        assert (start, end) == (-1, -1)

    def test_get_section_marker_position_with_duplicates(self):
        """Test that get_section_marker_position finds the first occurrence."""
        content = (
            "# First\n"
            "<!-- Section: Duplicate -->\n"
            "Content 1\n\n"
            "# Second\n"
            "<!-- Section: Duplicate -->\n"
            "Content 2"
        )
        
        start, end = get_section_marker_position(content, "Duplicate")
        assert start != -1
        assert end != -1
        # Should find the first occurrence
        assert content.index("<!-- Section: Duplicate -->") == start


class TestGetSection:
    def test_basic_section_retrieval(self, sample_document, test_config):
        """Test retrieving a section's content."""
        # Create initial content
        content = (
            "---\n"
            "title: Test Document\n"
            "author: Test Author\n"
            "date: 2024-03-21\n"
            "---\n\n"
            "# Introduction\n"
            "<!-- Section: Introduction -->\n"
            "Some introduction text.\n\n"
            "## Methods\n"
            "<!-- Section: Methods -->\n"
            "Details about methods.\n\n"
        )
        
        # Write the content to the test document
        with open(sample_document, "w", encoding=test_config.default_encoding) as f:
            f.write(content)
            
        # Get section content
        result = get_section(sample_document.name, "Methods", test_config)
        assert result == "Details about methods.\n\n"
        
    def test_section_not_found(self, sample_document, test_config):
        """Test error when section doesn't exist."""
        content = (
            "# Introduction\n"
            "<!-- Section: Introduction -->\n"
            "Some content.\n"
        )
        
        with open(sample_document, "w", encoding=test_config.default_encoding) as f:
            f.write(content)
            
        with pytest.raises(SectionNotFoundError):
            get_section(sample_document.name, "NonExistent", test_config)
            
    def test_empty_section(self, sample_document, test_config):
        """Test retrieving empty section content."""
        content = (
            "# Empty Section\n"
            "<!-- Section: Empty Section -->\n"
            "\n\n"
            "# Next Section\n"
        )
        
        with open(sample_document, "w", encoding=test_config.default_encoding) as f:
            f.write(content)
            
        result = get_section(sample_document.name, "Empty Section", test_config)
        assert result == "\n\n"
        
    def test_whitespace_preservation(self, sample_document, test_config):
        """Test exact whitespace preservation."""
        content = (
            "# Whitespace Test\n"
            "<!-- Section: Whitespace Test -->\n"
            "Line with spaces    at end    \n"
            "   Indented line\n"
            "\n"
            "  Mixed   spacing   here  \n"
        )
        
        with open(sample_document, "w", encoding=test_config.default_encoding) as f:
            f.write(content)
            
        result = get_section(sample_document.name, "Whitespace Test", test_config)
        expected = (
            "Line with spaces    at end    \n"
            "   Indented line\n"
            "\n"
            "  Mixed   spacing   here  \n"
        )
        assert result == expected
        
    def test_file_not_found(self, test_config):
        """Test error when file doesn't exist."""
        filename = "nonexistent.md"
        expected_path = test_config.drafts_dir / filename
        with pytest.raises(WriterError) as exc_info:
            get_section(filename, "Any Section", test_config)
        assert ERROR_DOCUMENT_NOT_EXIST.format(file_path=expected_path) in str(exc_info.value)
            
    def test_invalid_file_permissions(self, sample_document, test_config):
        """Test error with unreadable file."""
        content = "# Test\n<!-- Section: Test -->\nContent"
        with open(sample_document, "w", encoding=test_config.default_encoding) as f:
            f.write(content)
            
        # Make file unreadable
        sample_document.chmod(0o000)
        try:
            with pytest.raises(FilePermissionError):
                get_section(sample_document.name, "Test", test_config)
        finally:
            # Restore permissions for cleanup
            sample_document.chmod(0o666)


class TestSectionExists:
    """Tests for section_exists function."""
    
    @pytest.fixture
    def sample_document(self, test_config, valid_metadata):
        """Create a sample document with sections for testing."""
        file_path = create_document("test_doc.md", valid_metadata, test_config)
        append_section("test_doc.md", "Existing Section", "Test content", test_config)
        append_section("test_doc.md", "Another Section", "More content", test_config)
        return file_path

    def test_section_exists_true(self, sample_document, test_config):
        """Test when section exists."""
        assert section_exists("test_doc.md", "Existing Section", test_config) is True

    def test_section_exists_false(self, sample_document, test_config):
        """Test when section doesn't exist."""
        assert section_exists("test_doc.md", "Nonexistent Section", test_config) is False

    def test_section_exists_case_sensitive(self, sample_document, test_config):
        """Test that section matching is case-sensitive."""
        assert section_exists("test_doc.md", "existing section", test_config) is False
        assert section_exists("test_doc.md", "Existing Section", test_config) is True

    def test_section_exists_file_not_found(self, test_config):
        """Test error when file doesn't exist."""
        with pytest.raises(WriterError, match=ERROR_DOCUMENT_NOT_EXIST.format(file_path=test_config.drafts_dir / "nonexistent.md")):
            section_exists("nonexistent.md", "Any Section", test_config)

    def test_section_exists_permission_error(self, sample_document, test_config):
        """Test error when file permissions prevent reading."""
        sample_document.chmod(0o000)
        try:
            with pytest.raises(WriterError, match="Permission denied"):
                section_exists("test_doc.md", "Existing Section", test_config)
        finally:
            sample_document.chmod(0o666)  # Restore permissions for cleanup

    def test_section_exists_with_special_chars(self, sample_document, test_config):
        """Test with section titles containing special characters."""
        append_section("test_doc.md", "Special (Test)!", "Content", test_config)
        assert section_exists("test_doc.md", "Special (Test)!", test_config) is True

    def test_section_exists_empty_title(self, sample_document, test_config):
        """Test with empty section title."""
        with pytest.raises(WriterError, match=ERROR_INVALID_SECTION_TITLE):
            section_exists("test_doc.md", "", test_config)


# pytest tests/functions/writer/test_file_operations.py
