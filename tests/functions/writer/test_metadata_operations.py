import pytest
from pathlib import Path
import yaml
from unittest.mock import Mock, patch
from src.functions.writer.metadata_operations import MetadataOperations
from src.functions.writer.exceptions import WriterError
from src.functions.writer.config import WriterConfig
from src.functions.writer.constants import DEFAULT_ENCODING
from datetime import date
from src.functions.writer.validation_constants import ValidationKeys
from src.functions.writer.exceptions import (
    WriterError,
    FileValidationError,
    FilePermissionError,
)

@pytest.fixture
def temp_md_file(tmp_path):
    """Create a temporary markdown file with metadata."""
    file_path = tmp_path / "test.md"
    content = """---
title: Test Document
author: Test Author
date: 2024-01-01
---
# Test Content
This is test content.
"""
    file_path.write_text(content, encoding=DEFAULT_ENCODING)
    return file_path

@pytest.fixture
def metadata_ops():
    """Create a MetadataOperations instance with default config."""
    return MetadataOperations()

class TestMetadataOperations:
    def test_get_metadata_valid_file(self, metadata_ops, temp_md_file):
        """Test getting metadata from a valid markdown file."""
        metadata = metadata_ops.get_metadata(str(temp_md_file))
        assert metadata == {
            'title': 'Test Document',
            'author': 'Test Author',
            'date': date(2024, 1, 1)
        }

    def test_get_metadata_missing_file(self, metadata_ops, tmp_path):
        """Test getting metadata from a non-existent file."""
        non_existent = tmp_path / "missing.md"
        with pytest.raises(WriterError, match="File does not exist"):
            metadata_ops.get_metadata(str(non_existent))

    def test_get_metadata_invalid_extension(self, metadata_ops, tmp_path):
        """Test getting metadata from a file with wrong extension."""
        invalid_file = tmp_path / "test.txt"
        invalid_file.touch()
        with pytest.raises(WriterError, match="File must have .md extension"):
            metadata_ops.get_metadata(str(invalid_file))

    def test_get_metadata_no_permissions(self, metadata_ops, temp_md_file):
        """Test getting metadata with no read permissions."""
        with patch('src.functions.writer.metadata_operations.validate_file_inputs',
                  side_effect=FilePermissionError("Permission denied")):
            with pytest.raises(WriterError, match="Permission denied"):
                metadata_ops.get_metadata(str(temp_md_file))

    def test_get_metadata_no_metadata_block(self, metadata_ops, tmp_path):
        """Test getting metadata from file without metadata block."""
        file_path = tmp_path / "no_metadata.md"
        file_path.write_text("# Just content\nNo metadata here.", encoding=DEFAULT_ENCODING)
        metadata = metadata_ops.get_metadata(str(file_path))
        assert metadata == {}

    def test_update_metadata_valid(self, metadata_ops, temp_md_file):
        """Test updating metadata in a valid file."""
        new_metadata = {
            'title': 'Updated Title',
            'author': 'New Author',
            'date': '2024-01-02'
        }
        metadata_ops.update_metadata(str(temp_md_file), new_metadata)
        
        # Verify update
        updated_metadata = metadata_ops.get_metadata(str(temp_md_file))
        assert updated_metadata == new_metadata

    def test_update_metadata_no_write_permission(self, metadata_ops, temp_md_file):
        """Test updating metadata without write permission."""
        with patch('src.functions.writer.metadata_operations.validate_file_inputs',
                  side_effect=FilePermissionError("Permission denied")):
            with pytest.raises(WriterError, match="Permission denied"):
                metadata_ops.update_metadata(str(temp_md_file), {'title': 'New'})

    def test_validate_metadata_missing_required(self, metadata_ops):
        """Test metadata validation with missing required fields."""
        # Set up required fields in config
        metadata_ops.config.metadata_validation_rules = {
            'title': {ValidationKeys.REQUIRED: True},
            'author': {ValidationKeys.REQUIRED: True},
            'date': {ValidationKeys.REQUIRED: True}
        }
        
        incomplete_metadata = {'title': 'Test'}  # Missing required fields
        with pytest.raises(WriterError, match="Missing required metadata fields"):
            metadata_ops.validate_metadata(incomplete_metadata)

    def test_merge_metadata(self, metadata_ops):
        """Test merging two metadata dictionaries."""
        base = {'title': 'Original', 'author': 'Author'}
        updates = {'title': 'Updated', 'date': '2024-01-01'}
        merged = metadata_ops.merge_metadata(base, updates)
        assert merged == {
            'title': 'Updated',
            'author': 'Author',
            'date': '2024-01-01'
        } 

# pytest tests/functions/writer/test_metadata_operations.py -v -s