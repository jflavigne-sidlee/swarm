class FileSearchError(Exception):
    """Base exception for file search operations."""
    pass

class FileValidationError(FileSearchError):
    """Raised when file validation fails."""
    pass

class VectorStoreError(FileSearchError):
    """Raised when vector store operations fail."""
    pass

class AssistantError(FileSearchError):
    """Raised when assistant operations fail."""
    pass 