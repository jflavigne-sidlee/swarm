from pathlib import Path
import mimetypes
from typing import Optional
from .types import ContextVariables
from .config import FileSearchConfig
from .constants import SUPPORTED_MIME_TYPES
from .errors import FileSearchErrors as Errors
from .exceptions import FileValidationError, VectorStoreError
from .azure_client import AzureClientWrapper

class FileManager:
    """Manages file uploads for Azure OpenAI Assistants."""
    
    def __init__(
        self, 
        azure_client: AzureClientWrapper, 
        config: Optional[FileSearchConfig] = None
    ) -> None:
        """Initialize FileManager with an Azure client wrapper and optional config.
        
        Args:
            azure_client: An instance of AzureClientWrapper (not raw AzureOpenAI client)
            config: Optional configuration for file search
        """
        if not isinstance(azure_client, AzureClientWrapper):
            raise TypeError("azure_client must be an instance of AzureClientWrapper")
        self.client = azure_client
        self.config = config or FileSearchConfig()
    
    def is_valid_file_type(self, file_path: Path) -> bool:
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
        
        return True

    def upload_file(self, file_path: Path, context_variables: ContextVariables) -> str:
        """Uploads a file to a vector store and saves the ID in context."""
        try:
            # Validate file
            file_path = Path(file_path) if isinstance(file_path, str) else file_path
            if not file_path.exists():
                raise FileValidationError(Errors.FILE_NOT_FOUND.format(path=file_path))
            self.is_valid_file_type(file_path)

            # Create vector store if needed
            if "vector_store_id" not in context_variables:
                vector_store = self.client.vector_stores.create(
                    name=context_variables.get("vector_store_name", "default-store"),
                    expires_after={
                        "anchor": "last_active_at",
                        "days": self.config.vector_store_expiration_days
                    }
                )
                context_variables["vector_store_id"] = vector_store.id

            # Upload file to vector store
            with open(file_path, "rb") as file:
                file_batch = self.client.vector_stores.file_batches.upload_and_poll(
                    vector_store_id=context_variables["vector_store_id"],
                    files=[file]
                )

            return context_variables["vector_store_id"]

        except Exception as e:
            raise FileValidationError(f"Failed to upload file: {str(e)}") 