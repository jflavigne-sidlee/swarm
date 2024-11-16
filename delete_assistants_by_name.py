from openai import AzureOpenAI
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def delete_assistants_by_name(name_pattern: str, dry_run: bool = True):
    """
    Delete all assistants whose names match the given pattern.
    
    Args:
        name_pattern: String to match against assistant names
        dry_run: If True, only lists matching assistants without deleting them
    """
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2024-05-01-preview",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )

    try:
        # List all assistants
        assistants = client.beta.assistants.list()
        matching_assistants = [a for a in assistants.data if name_pattern.lower() in a.name.lower()]
        
        print("\n" + "="*80)
        print(f"Found {len(matching_assistants)} assistants matching '{name_pattern}':")
        print("="*80)
        
        for assistant in matching_assistants:
            created_at = datetime.fromtimestamp(assistant.created_at)
            
            print(f"\nAssistant ID: {assistant.id}")
            print(f"Name: {assistant.name}")
            print(f"Model: {assistant.model}")
            print(f"Created: {created_at}")
            
            if not dry_run:
                try:
                    client.beta.assistants.delete(assistant.id)
                    print("✓ DELETED")
                except Exception as e:
                    print(f"✗ Failed to delete: {str(e)}")
            
            print("-"*40)
        
        if dry_run:
            print("\nDRY RUN - No assistants were deleted.")
            print("To delete these assistants, run with dry_run=False")
        else:
            print(f"\nDeleted {len(matching_assistants)} assistants matching '{name_pattern}'")
        
    except Exception as e:
        print(f"Error accessing assistants: {str(e)}")

if __name__ == "__main__":
    # Example usage
    name_to_delete = "Test Assistant"  # Change this to match the assistants you want to delete
    
    # First run in dry-run mode to see what would be deleted
    delete_assistants_by_name("File Search Assistant", dry_run=False)
    
    # Uncomment and run again to actually delete
    # delete_assistants_by_name(name_to_delete, dry_run=False)