# test_azure.py

import os
import asyncio
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

print("\nDebug - Environment Variables:")
print(f"API Version: {os.getenv('AZURE_OPENAI_API_VERSION')}")
print(f"Endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
print(f"Deployment Name: {os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')}")

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

async def test_chat_completion():
    try:
        print("\nDebug - Attempting chat completion:")
        print(f"Using deployment: {os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')}")
        
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello!"},
            ],
            stream=False
        )
        
        print("\nDebug - Response received:")
        print(response.choices[0].message.content)
                
    except Exception as e:
        print(f"\nDebug - Error occurred:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")

if __name__ == "__main__":
    print("\nDebug - Starting script")
    asyncio.run(test_chat_completion())
    print("\nDebug - Script completed")