from pathlib import Path
import os
import time
import mimetypes
from openai import AzureOpenAI
from typing import Tuple, Dict, Any, Optional
from .types import ContextVariables
from .config import FileSearchConfig
from .constants import (
    SUPPORTED_MIME_TYPES,
    MAX_FILE_SIZE_BYTES,
    MAX_FILE_SIZE_MB
)
from .errors import FileSearchErrors as Errors
from .messages import FileSearchMessages as Messages
from .exceptions import (
    FileSearchError,
    FileValidationError,
    VectorStoreError,
    AssistantError
)

class FileSearchManager:
    """Manages file uploads and question-answering using Azure OpenAI's file search capability.
    
    This class handles:
    - File validation and upload
    - Vector store management
    - Question answering using uploaded files
    
    Attributes:
        client: Azure OpenAI client instance
        config: Configuration settings for the manager
    """
    
    def __init__(
        self, 
        azure_client: AzureOpenAI, 
        config: Optional[FileSearchConfig] = None
    ) -> None:
        """Initialize the FileSearchManager.
        
        Args:
            azure_client: Configured Azure OpenAI client
            config: Optional configuration settings
        """
        self.client = azure_client
        self.config = config or FileSearchConfig()
        self.config.model_name = self.config.model_name or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        
    def is_valid_file_type(self, file_path: Path) -> Tuple[bool, str]:
        """Validates if the file type is supported."""
        suffix = file_path.suffix.lower()
        if suffix not in SUPPORTED_MIME_TYPES:
            raise FileValidationError(Errors.UNSUPPORTED_FILE_TYPE.format(
                suffix=suffix,
                supported_types=', '.join(SUPPORTED_MIME_TYPES.keys())
            ))
        
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            raise FileValidationError(Errors.MIME_TYPE_UNKNOWN.format(path=file_path))
        
        allowed_types = SUPPORTED_MIME_TYPES[suffix]
        if isinstance(allowed_types, list):
            if mime_type not in allowed_types:
                raise FileValidationError(Errors.INVALID_MIME_TYPE.format(
                    mime_type=mime_type,
                    expected_type=allowed_types
                ))
        else:
            if mime_type != allowed_types:
                raise FileValidationError(Errors.INVALID_MIME_TYPE.format(
                    mime_type=mime_type,
                    expected_type=allowed_types
                ))
        
        return True, Messages.FILE_TYPE_SUPPORTED
        
    def _create_assistant(self, context_variables: ContextVariables) -> None:
        """Creates an assistant if it doesn't exist."""
        try:
            assistant = self.client.beta.assistants.create(
                name=self.config.assistant_name,
                instructions=self.config.assistant_instructions,
                model=self.config.model_name,
                tools=[{"type": "file_search"}]
            )
            context_variables["assistant_id"] = assistant.id
        except Exception as e:
            raise AssistantError(f"Failed to create assistant: {str(e)}")

    def _create_vector_store(self, file_path: Path, context_variables: ContextVariables) -> None:
        """Creates a vector store for the file."""
        try:
            vector_store = self.client.beta.vector_stores.create(
                name=f"store-{file_path.stem}",
                expires_after={
                    "anchor": "last_active_at",
                    "days": self.config.vector_store_expiration_days
                }
            )
            context_variables["vector_store_id"] = vector_store.id
        except Exception as e:
            raise VectorStoreError(f"Failed to create vector store: {str(e)}")

    def _wait_for_run_completion(self, thread_id: str, run_id: str) -> None:
        """Waits for a run to complete with configured retries."""
        attempts = 0
        while attempts < self.config.max_retries:
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id
            )
            if run.status == "completed":
                return
            elif run.status == "failed":
                raise AssistantError(Errors.RUN_FAILED)
            
            time.sleep(self.config.retry_delay)
            attempts += 1
            
        raise AssistantError(f"Run timed out after {self.config.max_retries} attempts")

    def upload_file(self, file_path: Path, context_variables: ContextVariables) -> str:
        """Uploads a file and prepares it for searching."""
        try:
            if not file_path.exists():
                raise FileValidationError(Errors.FILE_NOT_FOUND.format(path=file_path))

            # Validate file type
            self.is_valid_file_type(file_path)

            # Check file size
            file_size = file_path.stat().st_size
            if file_size > MAX_FILE_SIZE_BYTES:
                raise FileValidationError(Errors.FILE_SIZE_EXCEEDED.format(max_size=MAX_FILE_SIZE_MB))

            # Create assistant if needed
            if "assistant_id" not in context_variables:
                self._create_assistant(context_variables)

            # Create vector store
            self._create_vector_store(file_path, context_variables)

            try:
                # Upload file to vector store
                with open(file_path, "rb") as file:
                    file_batch = self.client.beta.vector_stores.file_batches.upload_and_poll(
                        vector_store_id=context_variables["vector_store_id"],
                        files=[file]
                    )
            except Exception as e:
                raise VectorStoreError(f"Failed to upload file to vector store: {str(e)}")

            try:
                # Update assistant with vector store
                self.client.beta.assistants.update(
                    assistant_id=context_variables["assistant_id"],
                    tool_resources={"file_search": {"vector_store_ids": [context_variables["vector_store_id"]]}}
                )
            except Exception as e:
                raise AssistantError(f"Failed to update assistant: {str(e)}")

            return Messages.FILE_UPLOAD_SUCCESS

        except FileSearchError as e:
            return str(e)
        except Exception as e:
            return Errors.UPLOAD_ERROR.format(error=str(e))

    def ask_question(self, question: str, context_variables: ContextVariables) -> str:
        """Asks a question about the uploaded file."""
        try:
            if "assistant_id" not in context_variables:
                raise AssistantError(Errors.NO_ASSISTANT)
            if "vector_store_id" not in context_variables:
                raise VectorStoreError(Errors.NO_VECTOR_STORE)

            try:
                # Create thread
                thread = self.client.beta.threads.create()

                # Add the question to the thread
                self.client.beta.threads.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=question
                )

                # Create a run
                run = self.client.beta.threads.runs.create(
                    thread_id=thread.id,
                    assistant_id=context_variables["assistant_id"]
                )

                # Wait for the run to complete with retries
                self._wait_for_run_completion(thread.id, run.id)

                # Get the response
                messages = self.client.beta.threads.messages.list(
                    thread_id=thread.id
                )
                return messages.data[0].content[0].text.value

            except Exception as e:
                raise AssistantError(f"Failed to process question: {str(e)}")

        except FileSearchError as e:
            return str(e)
        except Exception as e:
            return Errors.QUESTION_ERROR.format(error=str(e))
