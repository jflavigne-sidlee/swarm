import pytest
from datetime import datetime
from pathlib import Path

from src.functions.writer.file_operations import (
    create_document,
    append_section,
    edit_section,
    get_section,
    section_exists,
)
from src.functions.writer.validation import validate_markdown
from src.functions.writer.config import WriterConfig

def test_basic_document_lifecycle(test_environment):
    """Test basic document lifecycle from creation to editing."""
    # Create config using test environment
    config = WriterConfig(
        drafts_dir=test_environment["root_dir"],
        create_directories=True
    )
    
    # 1. Create document with metadata
    metadata = {
        "title": "Test Integration Document",
        "author": "Integration Test",
        "date": datetime.now().strftime("%Y-%m-%d")
    }
    
    doc_path = Path("lifecycle_test.md")
    file_path = create_document(doc_path, metadata, config)
    
    assert file_path.exists()
    assert file_path.suffix == ".md"
    
    # 2. Append sections
    sections = [
        ("Introduction", "Test introduction content"),
        ("Methods", "Test methods content"),
        ("Results", "Test results content")
    ]
    
    for title, content in sections:
        append_section(file_path, title, content, config)
        assert section_exists(file_path, title, config)
    
    # 3. Edit a section
    new_content = "Updated methods content"
    edit_section(file_path, "Methods", new_content, config)
    assert new_content in get_section(file_path, "Methods", config)
    
    # 4. Validate content
    assert validate_markdown(file_path)
