from dataclasses import dataclass
from typing import Optional

@dataclass
class FileSearchConfig:
    """Configuration for FileSearchManager.
    
    Attributes:
        assistant_name: Name for created assistants
        assistant_instructions: Instructions for created assistants
        vector_store_expiration_days: Days until vector store expires
        max_retries: Number of retries for API calls
        retry_delay: Delay between retries in seconds
        chunk_size: Size of chunks for text splitting (in tokens)
        chunk_overlap: Overlap between chunks (in tokens)
        max_chunks_in_context: Maximum number of chunks to include in context
        model_name: Name of the Azure OpenAI deployment to use
    """
    assistant_name: str = "File Analysis Assistant"
    assistant_instructions: str = "You are an expert at analyzing documents and answering questions about them."
    vector_store_expiration_days: int = 7
    max_retries: int = 3
    retry_delay: float = 1.0
    chunk_size: int = 800
    chunk_overlap: int = 400
    max_chunks_in_context: int = 20
    model_name: Optional[str] = None 