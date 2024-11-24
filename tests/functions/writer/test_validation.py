import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import yaml
from markdown_it import MarkdownIt

from src.functions.writer.validation import (
    validate_markdown,
    validate_frontmatter,
    validate_header_hierarchy,
    validate_links,
    validate_tables,
    validate_code_blocks,
)
from src.functions.writer.exceptions import WriterError


# Test fixtures
@pytest.fixture
def temp_md_file(tmp_path):
    """Create a temporary markdown file."""
    md_file = tmp_path / "test.md"
    return md_file


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    config = Mock()
    config.default_encoding = "utf-8"
    return config


# Test main validation function
def test_validate_markdown_valid_document(temp_md_file):
    """Test validation of a valid markdown document."""
    content = """---
title: Test Document
author: Test Author
---

# Header 1
<!-- Section: Header 1 -->

## Subheader
<!-- Section: Subheader -->

This is a [valid link](https://example.com).

| Column 1 | Column 2 |
|----------|----------|
| Data 1   | Data 2   |

```python
def test():
    pass
```
"""
    temp_md_file.write_text(content)

    result = validate_markdown(temp_md_file)
    assert result.is_valid
    assert not result.errors


def test_validate_markdown_multiple_errors(temp_md_file):
    """Test validation catching multiple errors."""
    content = """# Header 1
### Wrong Level Header

| Bad | Table |
| Missing | Alignment |

```
Missing language
```

[Broken Link](./nonexistent.md)
"""
    temp_md_file.write_text(content)
    result = validate_markdown(temp_md_file, debug=True)
    
    # Should catch:
    # 1. Header hierarchy error
    # 2. Table format error
    # 3. Code block language error
    # 4. Broken link error
    assert not result.is_valid
    assert len(result.errors) >= 4
    
    error_types = [e.error_type for e in result.errors]
    assert "Header Hierarchy" in error_types
    assert "Table Format" in error_types
    assert "Code Block" in error_types
    assert "Link" in error_types


# Test individual validators
def test_validate_frontmatter():
    """Test YAML frontmatter validation."""
    # Valid frontmatter
    valid_content = """---
title: Test
author: Author
---
# Content
"""
    assert not validate_frontmatter(valid_content)

    # Invalid frontmatter
    invalid_content = """---
title: Test
- invalid: yaml
  indentation
---
"""
    errors = validate_frontmatter(invalid_content)
    assert len(errors) == 1
    assert errors[0].error_type == "YAML Syntax"


def test_validate_header_hierarchy():
    """Test header hierarchy validation."""
    content = """
# H1
## H2
### H3
## H2 Again
"""
    assert not validate_header_hierarchy(content)

    content_with_error = """
# H1
### H3  # Skips H2
"""
    errors = validate_header_hierarchy(content_with_error)
    assert len(errors) == 1
    assert errors[0].error_type == "Header Hierarchy"


def test_validate_links():
    """Test link validation."""
    content = """
[Valid Link](https://example.com)
[Broken Link](nonexistent.md)
![Missing Image](missing.png)
"""
    # Create parser and tokens
    parser = MarkdownIt("commonmark").enable("link").enable("image")
    tokens = parser.parse(content)
    
    errors = validate_links(content, tokens, base_path=Path("."))
    assert len(errors) == 2  # Should catch broken link and missing image
    assert any("Broken link" in e.message for e in errors)
    assert any("missing.png" in e.message for e in errors)


def test_validate_tables():
    """Test table validation."""
    # Valid table
    valid_table = """
| Header 1 | Header 2 |
|----------|----------|
| Data 1   | Data 2   |
"""
    assert not validate_tables(valid_table)

    # Invalid table - missing alignment row
    invalid_table = """
| Bad | Table |
| No | Alignment |
"""
    errors = validate_tables(invalid_table)
    assert len(errors) == 1
    assert errors[0].error_type == "Table Format"
    assert "alignment row" in errors[0].message


def test_validate_code_blocks():
    """Test code block validation."""
    # Valid code block
    valid_blocks = """
```python
def test():
    pass
```
"""
    assert not validate_code_blocks(valid_blocks)

    # Invalid code blocks
    invalid_blocks = """
```
Missing language
```

```python
Unclosed block
"""
    errors = validate_code_blocks(invalid_blocks)
    assert len(errors) == 2  # Should catch missing language and unclosed block


# Test error handling
def test_validate_markdown_file_not_found(temp_md_file):
    """Test validation of non-existent file."""
    with pytest.raises(WriterError):
        validate_markdown(temp_md_file)


def test_validate_markdown_empty_file(temp_md_file):
    """Test validation of empty file."""
    temp_md_file.write_text("")
    result = validate_markdown(temp_md_file)
    assert not result.is_valid
    assert len(result.errors) == 1
    assert "empty" in result.errors[0].message.lower()


# Test edge cases
def test_validate_markdown_large_file(temp_md_file):
    """Test validation of a large file."""
    # Create a large file with repeated content
    content = "# Header\n\nParagraph\n\n" * 1000
    temp_md_file.write_text(content)

    result = validate_markdown(temp_md_file)
    assert result.is_valid  # Should handle large files efficiently


def test_validate_markdown_with_special_characters(temp_md_file):
    """Test validation with special characters and encodings."""
    content = """# Header with émojis 🎉
    
Special characters: àéîøü

```python
# Unicode strings
text = "Hello, 世界"
```
"""
    temp_md_file.write_text(content, encoding="utf-8")

    result = validate_markdown(temp_md_file)
    assert result.is_valid  # Should handle special characters correctly



# pytest -v tests/functions/writer/test_validation.py