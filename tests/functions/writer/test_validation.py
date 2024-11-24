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
        # Mock validation failures with a list of responses for each tool
        mock_run.side_effect = [
            # remark-lint failure
            Mock(returncode=1, 
                 stderr='file.md:1: Invalid header spacing\nfile.md:5: Broken link',
                 stdout=''),
            # markdownlint failure
            Mock(returncode=1,
                 stderr='',
                 stdout='file.md:3: MD007 Unordered list indentation'),
            # pandoc failure
            Mock(returncode=1,
                 stderr='Error parsing markdown: malformed table',
                 stdout='')
        ]
        
        is_valid, errors = validate_markdown(str(invalid_md_file))
        
        assert not is_valid
        assert len(errors) > 0
        assert any('Invalid header spacing' in error for error in errors)
        assert any('MD007' in error for error in errors)
        assert any('malformed table' in error for error in errors)

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

def test_validate_markdown_with_external_tools(valid_md_file):
    with patch('subprocess.run') as mock_run:
        # Mock successful validation for all tools
        mock_run.side_effect = [
            # remark-lint success
            Mock(returncode=0, stderr='', stdout=''),
            # markdownlint success
            Mock(returncode=0, stderr='', stdout=''),
            # pandoc success
            Mock(returncode=0, stderr='', stdout='')
        ]
        
        is_valid, errors = validate_markdown(str(valid_md_file))
        
        assert is_valid
        assert len(errors) == 0
        assert mock_run.call_count == 3

def test_validate_markdown_with_tool_failures(invalid_md_file):
    with patch('subprocess.run') as mock_run:
        # Mock validation failures for each tool
        mock_run.side_effect = [
            # remark-lint failure
            Mock(returncode=1, 
                 stderr='file.md:1: Invalid header spacing\nfile.md:5: Broken link',
                 stdout=''),
            # markdownlint failure
            Mock(returncode=1,
                 stderr='',
                 stdout='file.md:3: MD007 Unordered list indentation\nfile.md:8: MD022 Headers should be surrounded by blank lines'),
            # pandoc failure
            Mock(returncode=1,
                 stderr='Error parsing markdown: malformed table',
                 stdout='')
        ]
        
        is_valid, errors = validate_markdown(str(invalid_md_file))
        
        assert not is_valid
        assert len(errors) > 0
        assert any('Invalid header spacing' in error for error in errors)
        assert any('MD007' in error for error in errors)
        assert any('malformed table' in error for error in errors)
        assert mock_run.call_count == 3

def test_validate_markdown_with_tool_errors():
    with patch('subprocess.run') as mock_run:
        # Mock tool execution errors
        mock_run.side_effect = subprocess.CalledProcessError(
            cmd=['remark'],
            returncode=1,
            output='',
            stderr='Command failed'
        )
        
        with pytest.raises(WriterError) as exc_info:
            validate_markdown("test.md")
            
        assert "Failed to validate markdown" in str(exc_info.value)
