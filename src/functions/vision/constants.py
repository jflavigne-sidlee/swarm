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

# Default configuration values
DEFAULT_MODEL_NAME = "gpt-4o"
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1
DEFAULT_LOG_LEVEL = "WARNING"
DEFAULT_MAX_IMAGE_SIZE = 20 * 1024 * 1024  # 20MB
DEFAULT_MAX_TOKENS = 2000
MIN_MAX_TOKENS = 100

# Timeout settings
DEFAULT_URL_TIMEOUT = 30  # seconds
DEFAULT_DOWNLOAD_TIMEOUT = 60  # seconds

# Supported formats
SUPPORTED_IMAGE_FORMATS = {".jpg", ".jpeg", ".png", ".gif"}

# Log messages
LOG_UNEXPECTED_ERROR = "Unexpected error during analysis: {error}"
LOG_RETRY_ATTEMPT = "Retry attempt {attempts} failed: {error}"
LOG_IMAGE_VALIDATION = "Validating image: {image}"
LOG_MODEL_VALIDATION = "Validating model configuration for {model}"
LOG_ANALYSIS_STARTED = "Starting analysis with model: {model}"
LOG_ANALYSIS_COMPLETED = "Analysis completed successfully"

# Error messages
ERROR_RETRY_FAILED = "Analysis failed after {attempts} attempts: {error}"
ERROR_MODEL_CONFIG = "Invalid model configuration: {error}"
ERROR_MODEL_CAPABILITY = "Model {name} does not support vision capabilities"
ERROR_TOKEN_LIMIT = "Requested tokens ({tokens}) exceeds model limit ({limit})"
ERROR_IMAGE_SOURCE = "Image file not found: {source}"
ERROR_IMAGE_FORMAT = "Unsupported image format: {format}"
ERROR_IMAGE_SIZE = "Image file too large (max size: {limit}MB)"
ERROR_MIME_TYPE = "Unsupported MIME type: {mime_type}. Supported types: {supported}"
ERROR_API = "API error during analysis: {error}"

# Supported formats
SUPPORTED_IMAGE_FORMATS = {".jpg", ".jpeg", ".png", ".gif"} 