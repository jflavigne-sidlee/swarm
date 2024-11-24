import pytest
from pathlib import Path
from unittest.mock import patch, Mock
import mdformat
from src.functions.writer.validation import validate_markdown, validate_gfm_task_lists
from src.functions.writer.exceptions import WriterError
from src.functions.writer.constants import ERROR_SUGGESTIONS

def test_validate_markdown_with_mdformat(tmp_path):
    """Test validation using mdformat."""
    content = """# Test Document
    
    Invalid indentation
        Wrong spacing after header
    """
    file_path = tmp_path / "test.md"
    file_path.write_text(content)
    
    with patch('mdformat.text') as mock_mdformat:
        mock_mdformat.side_effect = ValueError("Invalid markdown formatting")
        
        is_valid, errors = validate_markdown(str(file_path))
        
        assert not is_valid
        assert any("Invalid markdown formatting" in error for error in errors)

def test_validate_gfm_task_lists(tmp_path):
    """Test validation of GitHub-Flavored Markdown task lists."""
    content = """# Task List Test
    
- [ ] Valid empty task
- [x] Valid completed task
-[ ] Invalid spacing
-[x] Invalid spacing
- [] Invalid marker
- [X] Valid uppercase X
-  [ ] Invalid indentation
- [ ]Empty task
"""
    file_path = tmp_path / "task_lists.md"
    file_path.write_text(content)
    
    errors = validate_gfm_task_lists(content)
    
    assert any("Invalid task list marker" in error for error in errors), "Should detect invalid task lists"
    assert len([e for e in errors if "Invalid task list marker" in e]) >= 4, "Should detect at least 4 invalid task lists"
    
    assert any(ERROR_SUGGESTIONS['task-list-marker'] in error for error in errors), "Should include task list suggestions"

def test_validate_gfm_task_lists_valid(tmp_path):
    """Test validation of valid GitHub-Flavored Markdown task lists."""
    content = """# Valid Task List

- [ ] Todo item
- [x] Completed item
  - [ ] Nested todo
  - [x] Nested completed
"""
    file_path = tmp_path / "valid_task_lists.md"
    file_path.write_text(content)
    
    errors = validate_gfm_task_lists(content)
    assert len(errors) == 0

def test_validate_markdown_empty_file(tmp_path):
    """Test validation of an empty markdown file."""
    file_path = tmp_path / "empty.md"
    file_path.touch()
    
    is_valid, errors = validate_markdown(str(file_path))
    
    assert not is_valid
    assert len(errors) == 1
    assert "File is empty" in errors[0]

def test_validate_markdown_with_pandoc(tmp_path):
    """Test markdown validation with pandoc compatibility check."""
    content = """# Test Document
This is a valid document.
"""
    file_path = tmp_path / "test.md"
    file_path.write_text(content)
    
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(returncode=0, stderr='')
        
        is_valid, errors = validate_markdown(str(file_path))
        
        assert is_valid
        assert len(errors) == 0

def test_validate_markdown_with_broken_links(tmp_path):
    """Test validation of markdown with broken links and images."""
    content = """# Test Document
![Missing Image](nonexistent.png)
[Broken Link](missing.md)
"""
    file_path = tmp_path / "test.md"
    file_path.write_text(content)
    
    is_valid, errors = validate_markdown(str(file_path))
    
    assert not is_valid
    assert len(errors) > 0
    assert any('Broken image link' in error for error in errors)
    assert any('Broken file link' in error for error in errors)

def test_validate_markdown_invalid_extension():
    """Test validation of file with wrong extension."""
    with pytest.raises(WriterError, match="Invalid file format"):
        validate_markdown("test.txt")

def test_validate_markdown_gfm_tables(tmp_path):
    """Test validation of GFM tables."""
    content = """# Test Tables
    
| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
| Missing  |
"""
    file_path = tmp_path / "tables.md"
    file_path.write_text(content)
    
    with patch('mdformat.text') as mock_mdformat:
        mock_mdformat.side_effect = ValueError("Table has inconsistent columns")
        
        is_valid, errors = validate_markdown(str(file_path))
        
        assert not is_valid
        assert any("Table" in error for error in errors)

def test_validate_markdown_pandoc_failure(tmp_path):
    """Test validation when pandoc conversion fails."""
    content = """# Test Document
Invalid latex: $\invalid$
"""
    file_path = tmp_path / "pandoc_test.md"
    file_path.write_text(content)
    
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(
            returncode=1,
            stderr="Error parsing latex math"
        )
        
        is_valid, errors = validate_markdown(str(file_path))
        
        assert not is_valid
        assert any("pandoc" in error.lower() for error in errors)

def test_validate_markdown_gfm_strikethrough(tmp_path):
    """Test validation of GFM strikethrough syntax."""
    content = """# Test Strikethrough
    
~~Valid strikethrough~~
~Invalid strike~
"""
    file_path = tmp_path / "strikethrough.md"
    file_path.write_text(content)
    
    with patch('mdformat.text') as mock_mdformat:
        mock_mdformat.side_effect = ValueError("Invalid strikethrough syntax")
        
        is_valid, errors = validate_markdown(str(file_path))
        
        assert not is_valid
        assert any("strikethrough" in error.lower() for error in errors)
