import pytest
from pathlib import Path
import os
from src.azure_client import AzureClientWrapper
from src.file_manager import FileManager

def test_file_upload(setup_test_environment):
    """Test file upload functionality."""
    client = AzureClientWrapper.create(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2024-05-01-preview",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )
    
    file_manager = FileManager(client)
    print("\n" + "="*80)
    print("Starting File Upload Test")
    print("="*80)

    try:
        print("✓ File manager initialized")

        context_variables = {
            "vector_store_name": "Test Vector Store",
        }

        vector_store_id = file_manager.upload_file(
            setup_test_environment["test_file_path"], 
            context_variables
        )
        print(f"✓ File uploaded: {vector_store_id}")
        assert vector_store_id is not None

    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        raise