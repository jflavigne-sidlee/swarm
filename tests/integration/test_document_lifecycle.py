import pytest
from datetime import datetime
from pathlib import Path

from src.functions.writer.file_operations import (
    create_document,
    append_section,
    edit_section,
    get_section,
    section_exists,
    validate_markdown
)
from src.functions.writer.validation import validate_markdown

def test_basic_document_lifecycle(test_environment):
    """Test basic document lifecycle from creation to editing.
    
    Tests:
    1. Document creation with metadata
    2. Section management (append, edit, retrieve)
    3. Content validation
    """
    # 1. Create document with metadata
    metadata = {
        "title": "Test Integration Document",
        "author": "Integration Test",
        "date": datetime.now().strftime("%Y-%m-%d")
    }
    doc_path = Path(test_environment["root_dir"]) / "lifecycle_test.md"
    create_document(doc_path, metadata)
    
    # 2. Append sections
    sections = [
        ("Introduction", "Test introduction content"),
        ("Methods", "Test methods content"),
        ("Results", "Test results content")
    ]
    
    for title, content in sections:
        append_section(doc_path, title, content)
        assert section_exists(doc_path, title)
    
    # 3. Edit a section
    new_content = "Updated methods content"
    edit_section(doc_path, "Methods", new_content)
    assert new_content in get_section(doc_path, "Methods")
    
    # 4. Validate content
    assert validate_markdown(doc_path)