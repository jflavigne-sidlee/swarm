"""Constants for the writer module configuration."""
from enum import Enum, auto
from typing import Set, List, Dict, Type, Final

# Metadata keys
METADATA_KEY_VALIDATION: Final = "validation"
METADATA_KEY_DEFAULT: Final = "default"
METADATA_KEY_HELP: Final = "help"
METADATA_KEY_EXAMPLE: Final = "example"
METADATA_KEY_CONSTRAINTS: Final = "constraints"
METADATA_KEY_TYPE: Final = "type"
METADATA_KEY_REQUIRED: Final = "required"
METADATA_KEY_IS_PATH: Final = "is_path"

# Path-related
DEFAULT_BASE_PATH: Final = "data"
DEFAULT_PATHS: Final[Dict[str, str]] = {
    "temp": f"{DEFAULT_BASE_PATH}/temp",
    "drafts": f"{DEFAULT_BASE_PATH}/drafts",
    "finalized": f"{DEFAULT_BASE_PATH}/finalized",
}

# Markdown settings
DEFAULT_METADATA_FIELDS: Final[List[str]] = ["title", "author", "date"]
DEFAULT_SECTION_MARKER: Final = "<!-- Section: {section_title} -->"
DEFAULT_ENCODING: Final = "utf-8"
VALID_MARKDOWN_FLAVORS: Final[Set[str]] = {"github", "commonmark", "strict"}
MIN_HEADER_DEPTH: Final = 1
MAX_HEADER_DEPTH: Final = 6

# File operations
DEFAULT_MAX_FILE_SIZE_MB: Final = 10.0
DEFAULT_MAX_FILE_SIZE: Final = int(DEFAULT_MAX_FILE_SIZE_MB * 1024 * 1024)  # Convert MB to bytes
ALLOWED_EXTENSIONS: Final[List[str]] = [".md", ".markdown"]
EXTENSION_PATTERN: Final = r'^\.[a-zA-Z0-9]+$'

# Version control
DEFAULT_VERSION_FORMAT: Final = "{base_name}_v{version}{ext}"
MIN_VERSIONS: Final = 1
DEFAULT_VERSIONS: Final = 5

# Locking
DEFAULT_LOCK_TIMEOUT: Final = 300  # 5 minutes
MIN_LOCK_RETRIES: Final = 1
DEFAULT_LOCK_RETRIES: Final = 3
MIN_RETRY_DELAY: Final = 0
DEFAULT_RETRY_DELAY: Final = 5

# Path validation
PATH_MUST_EXIST: Final = True
PATH_MUST_BE_DIRECTORY: Final = True
PATH_CHECK_PERMISSIONS: Final = True

# Error message templates
ERROR_REQUIRED_FIELD: Final = "Required field '{name}' is not set."
ERROR_INVALID_TYPE: Final = "Invalid type for '{name}': got {got}, expected {expected}."
ERROR_VALUE_TOO_SMALL: Final = "Value for '{name}' is too small: {value}. Minimum allowed: {min}."
ERROR_VALUE_TOO_LARGE: Final = "Value for '{name}' is too large: {value}. Maximum allowed: {max}."
ERROR_NO_ZERO: Final = "Zero is not allowed for '{name}'."
ERROR_PATTERN_MISMATCH: Final = "Invalid format for '{name}': '{value}'. Must match pattern: {pattern}"
ERROR_INVALID_CHOICE: Final = "Invalid value for '{name}': '{value}'. Must be one of: {choices}"
ERROR_CUSTOM_VALIDATION: Final = "Custom validation failed for '{name}'. Value: {value}. Error: {error}"

# Version format validation
VERSION_FORMAT_PLACEHOLDERS: Final[List[str]] = ["{version}", "{base_name}", "{ext}"]
ALLOWED_VERSION_PLACEHOLDERS: Final[Set[str]] = {"version", "base_name", "ext"}
VERSION_PLACEHOLDER_PATTERN: Final = r"{([^{}:]+)(?::[^}]+)?}"
VERSION_FORMAT_SPEC_PATTERN: Final = r"{([^{}:]+):([^}]+)}"
VERSION_PADDING_PATTERN: Final = r"^0>[1-9][0-9]*$"

# Validation keys
VALIDATION_KEY_TYPE: Final = "type"
VALIDATION_KEY_MIN_VALUE: Final = "min_value"
VALIDATION_KEY_MAX_VALUE: Final = "max_value"
VALIDATION_KEY_PATTERN: Final = "pattern"
VALIDATION_KEY_CHOICES: Final = "choices"
VALIDATION_KEY_ALLOW_ZERO: Final = "allow_zero"
VALIDATION_KEY_ELEMENT_TYPE: Final = "element_type"
VALIDATION_KEY_VALIDATE: Final = "validate"

class MetadataKeys(str, Enum):
    """Enumeration of metadata keys."""
    VALIDATION = "validation"
    DEFAULT = "default"
    HELP = "help"
    EXAMPLE = "example"
    CONSTRAINTS = "constraints"
    TYPE = "type"
    REQUIRED = "required"
    IS_PATH = "is_path"

class ValidationKeys(str, Enum):
    """Enumeration of validation keys."""
    TYPE = "type"
    MIN = "min_value"
    MAX = "max_value"
    PATTERN = "pattern"
    CHOICES = "choices"
    ALLOW_ZERO = "allow_zero"
    ELEMENT_TYPE = "element_type"
    VALIDATE = "validate"
    REQUIRED = "required"

# Configuration keys and messages
CONFIG_HEADER: Final = "Configuration:"
CONFIG_INDENT: Final = "  "

# Factory messages
FACTORY_PREFIX: Final = "Factory: "

# Path messages
PATH_CONVERSION_MSG: Final = "Converted to absolute path: {path}"
PATH_CREATION_MSG: Final = "Creating directory: {path}"
PATH_OPTIONAL_MSG: Final = "Optional path {name} is not set"
PATH_REQUIRED_MSG: Final = "Required path {name} is not set"

# Error messages
ERROR_PATH_NOT_DIR: Final = "{name} is not a directory: {path}"
ERROR_PATH_NOT_EXIST: Final = "{name} does not exist: {path}"
ERROR_PATH_NO_READ: Final = "No read permission for {name}: {path}"
ERROR_PATH_NO_WRITE: Final = "No write permission for {name}: {path}"
ERROR_PATH_PROCESS: Final = "Failed to process {name}: {error}"
ERROR_UNKNOWN_FIELD: Final = "Unknown configuration fields: {fields}"
ERROR_VALIDATION_FAILED: Final = "Validation failed for {name}: {error}"
ERROR_UNEXPECTED: Final = "Unexpected error validating {name}: {error}"
ERROR_GET_DEFAULT: Final = "Failed to get default for {name}: {error}"
ERROR_INVALID_CONFIG: Final = "Invalid configuration: {error}"
ERROR_UNKNOWN_FIELD_NAME: Final = "Unknown field: {name}"

# Log messages
LOG_BACKUP_ENABLED: Final = "Backup functionality is disabled"
LOG_BACKUP_WARNING: Final = "Backup directory is set but backup_enabled is False. The directory will not be used."
LOG_BACKUP_VALIDATED: Final = "Backup directory validated: {path}"
LOG_DIR_RELATIONSHIPS: Final = "Validating directory relationships"

# Field info
NO_DESCRIPTION: Final = "No description available"

# Field info messages
FIELD_INFO_TYPE: Final = "type"
FIELD_INFO_NAME: Final = "name"
FIELD_INFO_HELP: Final = "help"
FIELD_INFO_REQUIRED: Final = "required"
FIELD_INFO_DEFAULT: Final = "default"
FIELD_INFO_FACTORY: Final = "factory"
FIELD_INFO_CONSTRAINTS: Final = "constraints"
FIELD_INFO_EXAMPLE: Final = "example"
FIELD_INFO_VALUE: Final = "value"

# Constraint format strings
CONSTRAINT_TYPE_FORMAT: Final = "type={}"
CONSTRAINT_MIN_FORMAT: Final = ">= {}"
CONSTRAINT_MAX_FORMAT: Final = "<= {}"
CONSTRAINT_PATTERN_FORMAT: Final = "matches pattern: {}"
CONSTRAINT_CHOICES_FORMAT: Final = "one of: {}"
CONSTRAINT_JOIN_STR: Final = " and "

# Dictionary key strings
KEY_MIN_VALUE: Final = "min_value"
KEY_MAX_VALUE: Final = "max_value"
KEY_PATTERN: Final = "pattern"
KEY_CHOICES: Final = "choices"
KEY_CONSTRAINTS: Final = "constraints"