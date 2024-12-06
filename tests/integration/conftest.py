import pytest
import tempfile
import shutil
from pathlib import Path

@pytest.fixture(scope="session")
def test_environment():
    """Create base test environment with required directories and configurations.
    
    Returns:
        dict: Dictionary containing paths to test directories:
            - root_dir: Root directory for all test files
            - fixtures_dir: Directory containing test fixtures
            - templates_dir: Directory containing document templates
            - sample_docs_dir: Directory containing sample documents
            - expected_outputs_dir: Directory containing expected test outputs
    """
    temp_dir = Path(tempfile.mkdtemp())
    
    # Create directory structure
    fixtures_dir = temp_dir / "fixtures"
    templates_dir = fixtures_dir / "templates"
    sample_docs_dir = fixtures_dir / "sample_docs"
    expected_outputs_dir = fixtures_dir / "expected_outputs"
    
    for directory in [templates_dir, sample_docs_dir, expected_outputs_dir]:
        directory.mkdir(parents=True)
    
    # Create sample templates
    html_template = templates_dir / "template.html"
    html_template.write_text("""
    <!DOCTYPE html>
    <html>
    <head><title>{{ title }}</title></head>
    <body>{{ content }}</body>
    </html>
    """)
    
    # Create sample markdown document
    sample_doc = sample_docs_dir / "sample.md"
    sample_doc.write_text("""---
title: Sample Document
author: Test User
date: 2024-03-20
---
# Introduction
Sample content
""")
    
    env = {
        "root_dir": temp_dir,
        "fixtures_dir": fixtures_dir,
        "templates_dir": templates_dir,
        "sample_docs_dir": sample_docs_dir,
        "expected_outputs_dir": expected_outputs_dir
    }
    
    yield env
    
    # Cleanup after all tests
    shutil.rmtree(temp_dir)

@pytest.fixture
def test_document(test_environment):
    """Create a test document for each test that needs it.
    
    Returns:
        Path: Path to the created test document
    """
    doc_path = test_environment["root_dir"] / "test_document.md"
    doc_path.write_text("""---
title: Test Document
author: Integration Test
date: 2024-03-20
---
# Initial Content
This is a test document.
""")
    
    yield doc_path
    
    # Cleanup after each test
    if doc_path.exists():
        doc_path.unlink()