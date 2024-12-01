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

# Default configuration values
DEFAULT_DOWNLOAD_TIMEOUT = 60  # seconds
DEFAULT_ENCODING: Final[str] = "utf-8"
DEFAULT_LOG_FORMAT: Final = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEFAULT_LOG_LEVEL = "WARNING"
DEFAULT_MAX_IMAGE_SIZE = 20 * 1024 * 1024  # 20MB
DEFAULT_MAX_RETRIES = 3
DEFAULT_MAX_TOKENS = 2000
DEFAULT_MODEL_NAME = "gpt-4o"
DEFAULT_RETRY_ATTEMPTS: Final = 3
DEFAULT_RETRY_DELAY = 1
DEFAULT_RETRY_WAIT_SECONDS: Final = 1
DEFAULT_TEMPERATURE: Final = 0.7  # If not provided by model capabilities
DEFAULT_URL_TIMEOUT = 30  # seconds

# Timeouts
MIN_VALIDATION_TIMEOUT: Final = 0.1  # Minimum timeout threshold for URL validation
SUPPORTED_IMAGE_FORMATS = {".jpg", ".jpeg", ".png", ".gif"}

# Error messages
ERROR_API: Final = "API error during analysis: {error}"
ERROR_HTTP_FETCH_FAILED: Final = "Failed to fetch image: HTTP {status}"
ERROR_IMAGE_FORMAT: Final = "Unsupported image format: {format}"
ERROR_IMAGE_PROCESSING: Final = "Failed to process image: {error}"
ERROR_IMAGE_PROCESSING_FAILED: Final = "Failed to process image: {error}"
ERROR_IMAGE_SIZE: Final = "Image file too large (max size: {limit}MB)"
ERROR_IMAGE_SOURCE: Final = "Image file not found: {source}"
ERROR_INVALID_IMAGE_FILE: Final = "Invalid or corrupted image file"
ERROR_INVALID_URL: Final = "Invalid URL format: {url}"
ERROR_MIME_TYPE: Final = "Unsupported MIME type: {mime_type}. Supported types: {supported}"
ERROR_MODEL_CAPABILITY: Final = "Model {name} does not support vision capabilities"
ERROR_MODEL_CONFIG: Final = "Invalid model configuration: {error}"
ERROR_OPERATION_FAILED: Final = "Failed to complete operation: {error}"
ERROR_RETRY_FAILED: Final = "Analysis failed after {attempts} attempts: {error}"
ERROR_TEMPLATE_SCENE_TYPE: Final = "Scene type must be a specific description, not a template. Received: {value}"
ERROR_TOKEN_LIMIT: Final = "Requested tokens ({tokens}) exceeds model limit ({limit})"
ERROR_UNEXPECTED: Final = "Unexpected error during operation: {error}"
ERROR_URL_ACCESS_FAILED: Final = "Failed to access URL {url}: {error}"
ERROR_URL_NOT_ACCESSIBLE: Final = "URL not accessible (status {status}): {url}"
ERROR_URL_NOT_IMAGE: Final = "URL does not point to an image resource: {url}"
ERROR_URL_TIMEOUT: Final = "Timeout while accessing URL: {url} (timeout: {timeout}s)"
ERROR_URL_TIMEOUT_ACCESS: Final = "Timeout while accessing URL: {url}"

# Log messages
LOG_ANALYSIS_COMPLETED: Final = "Image analysis completed successfully"
LOG_ANALYSIS_STARTED: Final = "Starting image analysis with model: {model}"
LOG_IMAGE_VALIDATION: Final = "Validating image source: {source}"
LOG_MODEL_VALIDATION: Final = "Validating model configuration: {model}"
LOG_OPERATION_FAILED: Final = "Operation failed: {error}"
LOG_RETRY_ATTEMPT: Final = "Failed after {attempts} attempts. Last error: {error}"
LOG_UNEXPECTED_ERROR: Final = "Unexpected error: {error}"

SCENE_TYPE_TEMPLATE_PATTERNS: Final[List[str]] = [
    "type of scene",
    "(indoor/outdoor)",
    "[insert",
    "scene type here",
    "describe scene type"
]

# HTTP/URL related constants
HTTP_PREFIX: Final = 'http://'
HTTPS_PREFIX: Final = 'https://'
HTTP_STATUS_OK: Final = 200
CONTENT_TYPE_HEADER: Final[str] = 'content-type'

# Image processing constants
BINARY_READ_MODE: Final[str] = "rb"
IMAGE_CONTENT_TYPE_PREFIX: Final[str] = 'image/'
IMAGE_TYPE_KEY: Final = "type"
IMAGE_TYPE_URL: Final = "image_url"
IMAGE_URL_KEY: Final = "url"
UNKNOWN_MIME_TYPE: Final[str] = "unknown"

# System configuration constants
DATA_URL_PREFIX: Final[str] = "url"
ENV_PREFIX: Final[str] = "IMAGE_ANALYZER_"
LOCAL_FILE_SOURCE_TYPE: Final[str] = "local_file"
PROTECTED_NAMESPACE: Final[str] = "settings_"

# Chat completion constants
CONTENT_KEY: Final[str] = "content"
ROLE_KEY: Final[str] = "role"
USER_ROLE: Final[str] = "user"

DEFAULT_SINGLE_IMAGE_PROMPT: Final[str] = (
    "Analyze this image in detail and provide a structured response including:\n"
    "- Detailed description\n"
    "- Main objects identified\n"
    "- Scene type (indoor/outdoor)\n"
    "- Dominant colors\n"
    "- Image quality assessment"
)

DEFAULT_IMAGE_SET_PROMPT: Final = (
    "Analyze these images as a set and provide a structured response including:\n"
    "- Overall summary comparing all images\n"
    "- Common objects found across multiple images\n"
    "- Distinctive features of each image\n"
    "- Detailed comparison between images"
)






