"""Error messages for the swarm package."""

class FileSearchErrors:
    """Error messages for file search operations."""
    FILE_NOT_FOUND = "Error: File not found at {path}"
    UNSUPPORTED_FILE_TYPE = "Error: Unsupported file type: {suffix}. Supported types: {supported_types}"
    MIME_TYPE_UNKNOWN = "Error: Could not determine MIME type for file: {path}"
    INVALID_MIME_TYPE = "Error: Invalid MIME type: {mime_type}. Expected: {expected_type}"
    FILE_SIZE_EXCEEDED = "Error: File size exceeds {max_size}MB limit"
    NO_ASSISTANT = "Error: No assistant found. Please upload a file first."
    NO_VECTOR_STORE = "Error: No vector store found. Please upload a file first."
    RUN_FAILED = "Error: Run failed"
    QUESTION_ERROR = "Error: Error asking question: {error}"
    UPLOAD_ERROR = "Error: Failed to upload file: {error}" 