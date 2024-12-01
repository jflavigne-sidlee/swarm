from typing import Final, List
from dataclasses import dataclass

@dataclass(frozen=True)
class ImageAnalysisDescriptions:
    """Constants for image analysis field descriptions."""
    DESCRIPTION: str = "Detailed description of the image content"
    OBJECTS: str = "Main objects identified in the image"
    SCENE_TYPE: str = "The type of scene (e.g., 'indoor', 'outdoor', 'urban', 'nature', etc.)"
    COLORS: str = "Dominant colors in the image"
    QUALITY: str = "Assessment of image quality"
    METADATA: str = "Additional analysis metadata"
    SUMMARY: str = "Overall summary comparing all images"
    COMMON_OBJECTS: str = "Objects found across multiple images"
    UNIQUE_FEATURES: str = "Distinctive features of each image"
    COMPARATIVE_ANALYSIS: str = "Detailed comparison between images"
    SET_METADATA: str = "Additional metadata for image set analysis"


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

IMAGE_TYPE_URL: Final = "image_url"
IMAGE_URL_KEY: Final = "url"
IMAGE_TYPE_KEY: Final = "type"

# Add these new constants
ERROR_URL_NOT_IMAGE: Final = "URL does not point to an image resource: {url}"
ERROR_URL_NOT_ACCESSIBLE: Final = "URL not accessible (status {status}): {url}"
ERROR_URL_TIMEOUT: Final = "Timeout while accessing URL: {url} (timeout: {timeout}s)"
ERROR_INVALID_URL: Final = "Invalid URL format: {url}"
ERROR_URL_ACCESS_FAILED: Final = "Failed to access URL {url}: {error}"
ERROR_HTTP_FETCH_FAILED: Final = "Failed to fetch image: HTTP {status}"
ERROR_INVALID_IMAGE_FILE: Final = "Invalid or corrupted image file"
ERROR_IMAGE_PROCESSING: Final = "Failed to process image: {error}"
ERROR_TEMPLATE_SCENE_TYPE = "Scene type must be a specific description, not a template. Received: {value}"

SCENE_TYPE_TEMPLATE_PATTERNS: Final[List[str]] = [
    "type of scene",
    "(indoor/outdoor)",
    "[insert",
    "scene type here",
    "describe scene type"
]


CONTENT_TYPE_HEADER: Final[str] = 'content-type'
IMAGE_CONTENT_TYPE_PREFIX: Final[str] = 'image/'
BINARY_READ_MODE: Final[str] = "rb"
DEFAULT_ENCODING: Final[str] = "utf-8"
DATA_URL_PREFIX: Final[str] = "url"
UNKNOWN_MIME_TYPE: Final[str] = "unknown"
ENV_PREFIX: Final[str] = "IMAGE_ANALYZER_"
PROTECTED_NAMESPACE: Final[str] = "settings_"
LOCAL_FILE_SOURCE_TYPE: Final[str] = "local_file"
HTTP_PREFIX: Final = 'http://'
HTTPS_PREFIX: Final = 'https://'

ERROR_IMAGE_PROCESSING_FAILED: Final = "Failed to process image: {error}"
ERROR_URL_TIMEOUT_ACCESS: Final = "Timeout while accessing URL: {url}"
