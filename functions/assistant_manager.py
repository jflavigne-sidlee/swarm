import time
import random
from typing import Optional
from .types import ContextVariables
from .config import FileSearchConfig
from .errors import FileSearchErrors as Errors
from .exceptions import AssistantError
from .azure_client import AzureClientWrapper, MessageRole, RunStatus
from enum import Enum
from .handlers import FileSearchEventHandler

class RunStatus(str, Enum):
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    REQUIRES_ACTION = "requires_action"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"
    FAILED = "failed"
    COMPLETED = "completed"
    EXPIRED = "expired"

class AssistantManager:
    """Manages Azure OpenAI Assistants for file-based Q&A."""
    
    def __init__(
        self, 
        azure_client: AzureClientWrapper, 
        config: Optional[FileSearchConfig] = None
    ) -> None:
        self.client = azure_client
        self.config = config or FileSearchConfig()

    def verify_vector_store_ready(self, vector_store_id: str, max_retries: int = 10, retry_delay: int = 5) -> bool:
        """Verifies that a vector store is ready for use."""
        print(f"\nVerifying vector store {vector_store_id}...")
        
        for attempt in range(max_retries):
            try:
                print(f"Attempt {attempt + 1}/{max_retries} to verify vector store...")
                vector_store = self.client.retrieve_vector_store(vector_store_id)
                
                print(f"Vector store status:")
                print(f"- Total files: {vector_store.file_counts.total}")
                print(f"- In progress: {vector_store.file_counts.in_progress}")
                print(f"- Failed: {vector_store.file_counts.failed}")
                print(f"- Completed: {vector_store.file_counts.completed}")
                
                if vector_store.file_counts.in_progress == 0:
                    print("✓ Vector store is ready!")
                    return True
                
                print(f"Vector store not ready, waiting {retry_delay} seconds...")
                time.sleep(retry_delay)
            except Exception as e:
                print(f"Error verifying vector store: {str(e)}")
                if attempt == max_retries - 1:
                    raise AssistantError(f"Failed to verify vector store readiness: {str(e)}")
                time.sleep(retry_delay)
        return False

    def create_assistant(self, context_variables: ContextVariables) -> str:
        """Creates an assistant and stores its ID in context."""
        try:
            print("\nCreating new assistant...")
            print(f"Context variables: {context_variables}")
            
            # Validate required fields
            if "vector_store_id" not in context_variables:
                raise AssistantError(Errors.NO_VECTOR_STORE)
            
            # Verify vector store is ready
            print("\nVerifying vector store before assistant creation...")
            if not self.verify_vector_store_ready(context_variables["vector_store_id"]):
                raise AssistantError("Vector store not ready after maximum retries")
            
            # Create assistant
            print("\nCreating assistant with following configuration:")
            print(f"- Name: {context_variables.get('assistant_name', self.config.assistant_name)}")
            print(f"- Model: {context_variables.get('model_name', self.config.model_name)}")
            print(f"- Vector Store ID: {context_variables['vector_store_id']}")
            
            assistant = self.client.create_assistant(
                name=context_variables.get("assistant_name", self.config.assistant_name),
                instructions=context_variables.get("assistant_instructions", self.config.assistant_instructions),
                model=context_variables.get("model_name", self.config.model_name),
                tools=[{"type": "file_search"}],
                tool_resources={
                    "file_search": {
                        "vector_store_ids": [context_variables["vector_store_id"]]
                    }
                }
            )
            
            print(f"\nAssistant created with ID: {assistant.id}")
            
            # Verify assistant creation and readiness
            max_retries = 5
            retry_delay = 10
            print("\nVerifying assistant readiness...")
            
            for attempt in range(max_retries):
                try:
                    print(f"Attempt {attempt + 1}/{max_retries} to verify assistant...")
                    verified_assistant = self.client.retrieve_assistant(assistant.id)
                    if verified_assistant:
                        print("✓ Assistant verified and ready!")
                        break
                    print(f"Assistant not ready, waiting {retry_delay} seconds...")
                    time.sleep(retry_delay)
                except Exception as e:
                    print(f"Error verifying assistant: {str(e)}")
                    if attempt == max_retries - 1:
                        raise AssistantError(f"Failed to verify assistant readiness: {str(e)}")
                    time.sleep(retry_delay)
            
            context_variables["assistant_id"] = assistant.id
            return assistant.id

        except Exception as e:
            print(f"\nERROR creating assistant: {str(e)}")
            raise AssistantError(f"Failed to create assistant: {str(e)}")

    def ask_question(self, question: str, context_variables: ContextVariables) -> str:
        """Asks a question using the assistant configured in context."""
        try:
            print("\nProcessing question request...")
            print(f"Question: {question}")
            
            # Validate context
            if "assistant_id" not in context_variables:
                raise AssistantError(Errors.NO_ASSISTANT)
            if "vector_store_id" not in context_variables:
                raise AssistantError(Errors.NO_VECTOR_STORE)

            # Verify vector store is still ready
            print("\nVerifying vector store before asking question...")
            if not self.verify_vector_store_ready(context_variables["vector_store_id"]):
                raise AssistantError("Vector store not ready or expired")

            # Create thread and run with streaming enabled
            print("\nCreating thread and run...")
            handler = FileSearchEventHandler()
            
            try:
                with self.client.create_thread_and_run(
                    assistant_id=context_variables["assistant_id"],
                    thread={
                        "messages": [
                            {"role": MessageRole.USER, "content": question}
                        ]
                    },
                    stream=True,
                    event_handler=handler
                ) as stream:
                    stream.until_done()
            except Exception as e:
                print(f"\nStream error: {str(e)}")
                if "rate_limit_exceeded" in str(e).lower():
                    print("Rate limit exceeded, falling back to polling...")
                    # Implement fallback to polling here if needed
                raise AssistantError(f"Stream failed: {str(e)}")

            if handler.has_error:
                raise AssistantError(f"Run failed: {handler.error}")
            
            if not handler.has_response:
                raise AssistantError("No response received from assistant")

            print(f"\nResponse received: {handler.response[:100]}...")
            return handler.response

        except Exception as e:
            print(f"\nERROR processing question: {str(e)}")
            raise AssistantError(f"Failed to process question: {str(e)}")