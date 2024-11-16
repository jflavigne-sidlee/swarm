from openai import AzureOpenAI
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def list_all_assistants():
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2024-05-01-preview",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )

    try:
        # List all assistants
        assistants = client.beta.assistants.list()
        
        print("\n" + "="*80)
        print(f"Found {len(assistants.data)} assistants:")
        print("="*80)
        
        for assistant in assistants.data:
            # Convert created_at timestamp to datetime
            created_at = datetime.fromtimestamp(assistant.created_at)
            
            print(f"\nAssistant ID: {assistant.id}")
            print(f"Name: {assistant.name}")
            print(f"Model: {assistant.model}")
            print(f"Created: {created_at}")
            print(f"Instructions: {assistant.instructions[:100]}..." if len(assistant.instructions) > 100 else assistant.instructions)
            print("-"*40)
        
    except Exception as e:
        print(f"Error listing assistants: {str(e)}")

if __name__ == "__main__":
    list_all_assistants()