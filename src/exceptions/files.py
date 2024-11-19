class FileError(Exception):
    """Base exception for file operations."""
    pass

class FileValidationError(FileError):
    """Raised when file validation fails."""
    pass

class VectorStoreError(FileError):
    """Raised when vector store operations fail."""
    pass 