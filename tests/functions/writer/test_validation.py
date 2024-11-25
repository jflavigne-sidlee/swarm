import pytest
from pathlib import Path
from unittest.mock import patch, Mock
from src.functions.writer.validation import validate_markdown, validate_gfm_task_lists
from src.functions.writer.exceptions import WriterError
from src.functions.writer.constants import ERROR_SUGGESTIONS
import os
import stat
import shutil
import subprocess

def remove_readonly(func, path, _):
    """Clear the readonly bit and reattempt the removal"""
    os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # 0777
    func(path)

@pytest.fixture(autouse=True)
def cleanup_temp_files(tmp_path):
    """Ensure temporary files are removable after tests."""
    yield
    try:
        shutil.rmtree(tmp_path, onerror=remove_readonly)
    except Exception as e:
        print(f"Warning: Failed to cleanup {tmp_path}: {e}")

def test_validate_markdown_with_mdformat(tmp_path):
    """Test validation using mdformat."""
    content = """# Test Document
    
    Invalid indentation
        Wrong spacing after header
    """
    file_path = tmp_path / "test.md"
    file_path.write_text(content)
    file_path.chmod(0o644)
    
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
    file_path.chmod(0o644)
    
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
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd='pandoc',
            stderr="Error parsing latex math"
        )
        
        is_valid, errors = validate_markdown(str(file_path))
        
        assert not is_valid
        assert "Pandoc compatibility error: Error parsing latex math" in errors

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

def test_validate_header_nesting_valid(tmp_path):
    """Test validation of valid header nesting."""
    content = """# Main Title
## Section 1
### Subsection 1.1
### Subsection 1.2
## Section 2
### Subsection 2.1
"""
    file_path = tmp_path / "valid_headers.md"
    file_path.write_text(content)
    
    is_valid, errors = validate_markdown(str(file_path))
    
    assert is_valid
    assert len(errors) == 0

def test_validate_header_nesting_invalid_start(tmp_path):
    """Test validation of headers not starting at level 1."""
    content = """## Invalid Start
### Section 1
#### Subsection 1.1
"""
    file_path = tmp_path / "invalid_start.md"
    file_path.write_text(content)
    file_path.chmod(0o644)  # Set proper file permissions
    
    is_valid, errors = validate_markdown(str(file_path))
    
    assert not is_valid
    assert any("should start with a level 1 header" in error for error in errors)

def test_validate_header_nesting_invalid_jump(tmp_path):
    """Test validation of invalid header level jumps."""
    content = """# Main Title
## Section 1
#### Invalid Jump
## Section 2
"""
    file_path = tmp_path / "invalid_jump.md"
    file_path.write_text(content)
    
    is_valid, errors = validate_markdown(str(file_path))
    
    assert not is_valid
    assert any("Header level jumps from 2 to 4" in error for error in errors)
    assert any("Suggestion: Use ###" in error for error in errors)

def test_validate_header_nesting_too_deep(tmp_path):
    """Test validation of headers exceeding maximum depth."""
    content = """# Main Title
## Section 1
### Subsection 1
#### Sub-subsection 1
##### Level 5
###### Level 6
####### Invalid Level 7
"""
    file_path = tmp_path / "too_deep.md"
    file_path.write_text(content)
    
    is_valid, errors = validate_markdown(str(file_path))
    
    assert not is_valid
    assert any("exceeds maximum allowed level of 6" in error for error in errors)

def test_validate_header_nesting_mixed_issues(tmp_path):
    """Test validation of multiple header nesting issues."""
    content = """## Invalid Start
# Late Title
### Section 1
##### Invalid Jump
####### Too Deep
"""
    file_path = tmp_path / "mixed_issues.md"
    file_path.write_text(content)
    
    is_valid, errors = validate_markdown(str(file_path))
    
    assert not is_valid
    # Should find all three issues
    assert len([e for e in errors if "header" in e.lower()]) >= 3
    assert any("should start with a level 1 header" in error for error in errors)
    assert any("Header level jumps" in error for error in errors)
    assert any("exceeds maximum allowed level" in error for error in errors)

def test_validate_header_nesting_empty_headers(tmp_path):
    """Test validation of empty headers."""
    content = """# Valid Title
## 
### Section 1
"""
    file_path = tmp_path / "empty_headers.md"
    file_path.write_text(content)
    os.chmod(file_path, stat.S_IRWXU)  # Make file readable/writable
    
    is_valid, errors = validate_markdown(str(file_path))
    
    assert not is_valid
    assert any("empty header" in error.lower() for error in errors)
