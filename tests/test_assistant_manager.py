import pytest
from pathlib import Path
import json
from functions.file_manager import FileManager
from functions.azure_client import AzureClientWrapper

TEST_FILES_DIR = Path(__file__).parent / "test_files"
TEST_FILE_NAME = "sample.txt"
TEST_FILE_CONTENT = """
This is a test document about artificial intelligence and its applications in modern technology.
AI has revolutionized several fields including healthcare, finance, and transportation.
The impact of AI continues to grow as technology advances.
"""

TEST_QUESTION = "What fields has AI revolutionized according to the document?"

EXPECTED_FIELDS = ["healthcare", "finance", "transportation"]

def test_assistant_qa(assistant_manager, setup_test_environment):
    """Test assistant creation and question answering."""
    print("\n" + "="*80)
    print("Starting Assistant Q&A Test")
    print("="*80)

    assistant_id = None
    try:
        # First create a file and get a real vector store ID
        if not isinstance(assistant_manager.client, AzureClientWrapper):
            azure_client = AzureClientWrapper(assistant_manager.client)
        else:
            azure_client = assistant_manager.client
            
        file_manager = FileManager(azure_client)
        context_variables = {
            "vector_store_name": "Test Vector Store"
        }
        vector_store_id = file_manager.upload_file(
            setup_test_environment["test_file_path"],
            context_variables
        )
        
        print("✓ Assistant manager initialized")

        context_variables = {
            "assistant_name": "Test Assistant",
            "assistant_instructions": (
                "You are a test assistant analyzing documents. "
                "Provide your answer in the following JSON format without any markdown before or after:\n\n"
                "{\n"
                '  "answer": [Your answer here],\n'
                '  "source": [Source information]\n'
                "}\n"
                "Ensure that the key 'answer' is used for your response. The source key is optional."
            ),
            "model_name": "gpt-4o",
            "vector_store_id": vector_store_id
        }
        
        assistant_id = assistant_manager.create_assistant(context_variables)
        assert assistant_id, "No assistant ID returned"
        print(f"✓ Assistant created: {assistant_id}")

        # Update the context_variables after creating the assistant
        context_variables["assistant_id"] = assistant_id

        response = assistant_manager.ask_question(TEST_QUESTION, context_variables)
        answer = json.loads(response)
        print("\nAnswer received:")
        print(json.dumps(answer, indent=2))
        
        assert "answer" in answer, "Response missing 'answer' field"
        for field in EXPECTED_FIELDS:
            # Convert the list to a string for searching
            answer_text = ' '.join(str(item).lower() for item in answer["answer"])
            assert field in answer_text, f"Expected field '{field}' not found in answer"
            print(f"✓ Found expected field: {field}")
            
    finally:
        # Cleanup
        if assistant_id:
            try:
                assistant_manager.client.delete_assistant(assistant_id)
                print(f"✓ Assistant cleaned up: {assistant_id}")
            except Exception as e:
                print(f"Warning: Failed to delete assistant {assistant_id}: {str(e)}")