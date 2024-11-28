from typing import Final

# Operation status logs
LOG_OPERATION_FAILED: Final = "Operation failed: {error}"
LOG_UNEXPECTED_ERROR: Final = "Unexpected error: {error}"
LOG_RETRY_ATTEMPT: Final = "Failed after {attempts} attempts. Last error: {error}"
LOG_IMAGE_VALIDATION: Final = "Validating image source: {source}"
LOG_MODEL_VALIDATION: Final = "Validating model configuration: {model}"
LOG_ANALYSIS_STARTED: Final = "Starting image analysis with model: {model}"
LOG_ANALYSIS_COMPLETED: Final = "Image analysis completed successfully"

# Error messages
ERROR_OPERATION_FAILED: Final = "Failed to complete operation: {error}"
ERROR_UNEXPECTED: Final = "Unexpected error during operation: {error}"
ERROR_RETRY_FAILED: Final = "Failed to analyze image after {attempts} attempts: {error}"
ERROR_MODEL_CONFIG: Final = "Invalid model configuration: {error}"
ERROR_MODEL_CAPABILITY: Final = "Model {name} does not support vision capabilities"
ERROR_TOKEN_LIMIT: Final = "max_tokens ({tokens}) exceeds model limit ({limit})"
ERROR_IMAGE_SOURCE: Final = "Image source not found: {source}"
ERROR_IMAGE_FORMAT: Final = "Unsupported image format: {format}"
ERROR_IMAGE_SIZE: Final = "Image size exceeds the limit of {limit}MB"
ERROR_MIME_TYPE: Final = "Unsupported MIME type {mime_type}. Supported types: {supported}"
ERROR_API: Final = "Error analyzing image: {error}" 