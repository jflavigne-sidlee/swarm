import pytest
from pathlib import Path
import subprocess
from unittest.mock import patch, Mock

from src.functions.writer.validation import (
    validate_markdown,
    parse_remark_errors,
    parse_markdownlint_errors,
    validate_content
)
from src.functions.writer.exceptions import WriterError

@pytest.fixture
def valid_md_file(tmp_path):
    file_path = tmp_path / "valid.md"
    content = """# Test Document
    
This is a valid test document.

## Section
* List item 1
* List item 2

[Valid Link](https://example.com)
"""
    file_path.write_text(content)
    return file_path

@pytest.fixture
def invalid_md_file(tmp_path):
    file_path = tmp_path / "invalid.md"
    content = """#Invalid Header
    
* Invalid list
* items with
*wrong spacing

![Broken Image](missing.jpg)
[Broken Link](nonexistent.md)
"""
    file_path.write_text(content)
    return file_path

def test_validate_markdown_valid_file(valid_md_file):
    with patch('subprocess.run') as mock_run:
        # Mock successful validation
        mock_run.return_value = Mock(returncode=0, stderr='', stdout='')
        
        is_valid, errors = validate_markdown(str(valid_md_file))
        
        assert is_valid
        assert len(errors) == 0

def test_validate_markdown_invalid_file(invalid_md_file):
    with patch('subprocess.run') as mock_run:
        # Mock validation failures
        mock_run.side_effect = [
            Mock(returncode=1, stderr='file.md:1: Invalid header spacing', stdout=''),
            Mock(returncode=1, stderr='', stdout='file.md:3: MD007 Unordered list indentation')
        ]
        
        is_valid, errors = validate_markdown(str(invalid_md_file))
        
        assert not is_valid
        assert len(errors) > 0
        assert any('header' in error.lower() for error in errors)

def test_validate_markdown_nonexistent_file():
    with pytest.raises(WriterError):
        validate_markdown("nonexistent.md")

def test_parse_remark_errors():
    error_output = """
file.md:1: Invalid header
file.md:5: Incorrect list format
"""
    errors = parse_remark_errors(error_output)
    
    assert len(errors) == 2
    assert "Line 1: Invalid header" in errors
    assert "Line 5: Incorrect list format" in errors

def test_parse_markdownlint_errors():
    error_output = """
file.md:1: MD001 Invalid header
file.md:5: MD007 Incorrect list indentation
"""
    errors = parse_markdownlint_errors(error_output)
    
    assert len(errors) == 2
    assert "Line 1: MD001 Invalid header" in errors
    assert "Line 5: MD007 Incorrect list indentation" in errors

def test_validate_content(tmp_path):
    # Create test file with broken links
    file_path = tmp_path / "test.md"
    content = """
# Test Document

![Broken Image](missing.jpg)
[Broken Link](nonexistent.md)
[Valid Link](https://example.com)
[Valid Anchor](#section)
"""
    file_path.write_text(content)
    
    errors = validate_content(file_path)
    
    assert len(errors) == 2
    assert any('missing.jpg' in error for error in errors)
    assert any('nonexistent.md' in error for error in errors)

def test_validate_content_with_valid_links(tmp_path):
    # Create test file and referenced files
    file_path = tmp_path / "test.md"
    image_path = tmp_path / "image.jpg"
    link_path = tmp_path / "valid.md"
    
    # Create the referenced files
    image_path.touch()
    link_path.touch()
    
    content = f"""
# Test Document

![Valid Image](image.jpg)
[Valid Link](valid.md)
[External Link](https://example.com)
"""
    file_path.write_text(content)
    
    errors = validate_content(file_path)
    
    assert len(errors) == 0
