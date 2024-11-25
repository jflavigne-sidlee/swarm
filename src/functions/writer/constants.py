"""Constants for the writer module configuration."""

from enum import Enum, auto
from typing import Set, List, Dict, Type, Final
import os
import re

# Metadata keys
METADATA_KEY_VALIDATION: Final = "validation"
METADATA_KEY_DEFAULT: Final = "default"
METADATA_KEY_HELP: Final = "help"
METADATA_KEY_EXAMPLE: Final = "example"
METADATA_KEY_CONSTRAINTS: Final = "constraints"
METADATA_KEY_TYPE: Final = "type"
METADATA_KEY_REQUIRED: Final = "required"
METADATA_KEY_IS_PATH: Final = "is_path"

# Environment variable names
ENV_PREFIX: Final = "WRITER_"
ENV_TEMP_DIR: Final = f"{ENV_PREFIX}TEMP_DIR"
ENV_DRAFTS_DIR: Final = f"{ENV_PREFIX}DRAFTS_DIR"
ENV_FINALIZED_DIR: Final = f"{ENV_PREFIX}FINALIZED_DIR"
ENV_BACKUP_DIR: Final = f"{ENV_PREFIX}BACKUP_DIR"

# Default paths with environment variable support
DEFAULT_BASE_PATH: Final = os.getenv(f"{ENV_PREFIX}BASE_PATH", "data")
DEFAULT_PATHS: Final[Dict[str, str]] = {
    "temp": os.getenv(ENV_TEMP_DIR, f"{DEFAULT_BASE_PATH}/temp"),
    "drafts": os.getenv(ENV_DRAFTS_DIR, f"{DEFAULT_BASE_PATH}/drafts"),
    "finalized": os.getenv(ENV_FINALIZED_DIR, f"{DEFAULT_BASE_PATH}/finalized"),
}

# Markdown settings
DEFAULT_METADATA_FIELDS: Final[List[str]] = ["title", "author", "date"]
DEFAULT_SECTION_MARKER: Final = "<!-- Section: {section_title} -->"
INSERT_AFTER_MARKER: Final = "<!-- Section: {insert_after} -->"
DEFAULT_ENCODING: Final = "utf-8"
VALID_MARKDOWN_FLAVORS: Final[Set[str]] = {"github", "commonmark", "strict"}
MIN_HEADER_DEPTH: Final = 1
MAX_HEADER_DEPTH: Final = 6

# File operations
DEFAULT_MAX_FILE_SIZE_MB: Final = 10.0
DEFAULT_MAX_FILE_SIZE: Final = int(
    DEFAULT_MAX_FILE_SIZE_MB * 1024 * 1024
)  # Convert MB to bytes
ALLOWED_EXTENSIONS: Final[List[str]] = [".md", ".markdown"]
EXTENSION_PATTERN: Final = r"^\.[a-zA-Z0-9]+$"

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
ERROR_VALUE_TOO_SMALL: Final = (
    "Value for '{name}' is too small: {value}. Minimum allowed: {min}."
)
ERROR_VALUE_TOO_LARGE: Final = (
    "Value for '{name}' is too large: {value}. Maximum allowed: {max}."
)
ERROR_NO_ZERO: Final = "Zero is not allowed for '{name}'."
ERROR_PATTERN_MISMATCH: Final = (
    "Invalid format for '{name}': '{value}'. Must match pattern: {pattern}"
)
ERROR_INVALID_CHOICE: Final = (
    "Invalid value for '{name}': '{value}'. Must be one of: {choices}"
)
ERROR_CUSTOM_VALIDATION: Final = (
    "Custom validation failed for '{name}'. Value: {value}. Error: {error}"
)

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
LOG_BACKUP_WARNING: Final = (
    "Backup directory is set but backup_enabled is False. The directory will not be used."
)
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

# File validation constants
MAX_FILENAME_LENGTH: Final = 255
MAX_PATH_LENGTH: Final = 260  # Windows MAX_PATH limit
FORBIDDEN_FILENAME_CHARS: Final = '<>:"/\\|?*\0'
RESERVED_WINDOWS_FILENAMES: Final[Set[str]] = {
    "CON",
    "PRN",
    "AUX",
    "NUL",  # Device names
    "COM1",
    "COM2",
    "COM3",
    "COM4",  # COM ports
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",  # Printer ports
}

# YAML frontmatter markers
YAML_FRONTMATTER_START: Final = "---\n"
YAML_FRONTMATTER_END: Final = "\n---\n"

# Error messages for file operations
ERROR_INVALID_FILENAME: Final = "Invalid filename"
ERROR_INVALID_METADATA_TYPE: Final = "Invalid metadata type"
ERROR_FILE_EXISTS: Final = "File already exists: {path}"
ERROR_PERMISSION_DENIED_PATH: Final = "Permission denied accessing path: {path}"
ERROR_PERMISSION_DENIED_DIR: Final = "Permission denied creating directory: {path}"
ERROR_MISSING_METADATA: Final = "Missing required metadata fields: {fields}"
ERROR_DIR_EXISTS: Final = "Cannot create directory: {path} (file exists)"
ERROR_DIR_CREATION: Final = "Directory creation error: {error}"
ERROR_YAML_SERIALIZATION: Final = "YAML serialization error: {error}"
ERROR_FILE_WRITE: Final = "File writing error: {error}"
ERROR_PERMISSION_DENIED_FILE: Final = "Permission denied writing file: {path}"
ERROR_PATH_TOO_LONG: Final = (
    "Full path exceeds maximum length of {max_length} characters: {path}"
)

# Section marker patterns
SECTION_MARKER_TEMPLATE: Final = "<!-- Section: {section_title} -->"
PATTERN_SECTION_MARKER: Final = r"<!--\s*(?:Section|SECTION):\s*(.+?)\s*-->"
PATTERN_HEADER: Final = r"^(#{1,6})\s+(.+?)$"
PATTERN_HEADER_WITH_NEWLINE: Final = r"^(#{1,6}\s+.+\n)"
PATTERN_NEXT_HEADER: Final = r"^#{1,6}\s+.*$"
PATTERN_UNTIL_NEXT_HEADER: Final = r"^#{1,6}\s"
PATTERN_NEWLINE: Final = r"\n"

# Error messages for section operations
ERROR_SECTION_MARKER_NOT_FOUND: Final = "Section '{section_title}' marker not found"
ERROR_DUPLICATE_SECTION_MARKER: Final = (
    "Duplicate section marker found: '{marker_title}'"
)
ERROR_MISSING_SECTION_MARKER: Final = (
    "Header '{header_title}' is missing its section marker"
)
ERROR_MISMATCHED_SECTION_MARKER: Final = (
    "Section marker for '{header_title}' does not match header title"
)
ERROR_ORPHANED_SECTION_MARKER: Final = (
    "Found marker '{marker_title}' without a corresponding header"
)
ERROR_APPEND_SECTION_FAILED: Final = "Failed to append section: {error}"

# Logging messages
LOG_SECTION_MARKER_VALIDATION: Final = "Starting section marker validation..."
LOG_SECTION_MARKER_VALID: Final = "All section markers are valid"
LOG_SECTION_NOT_FOUND: Final = "Section marker not found: {section_title}"
LOG_APPEND_SECTION_SUCCESS: Final = "Successfully appended section '%s' to %s"
LOG_PERMISSION_DENIED_APPEND: Final = "Permission denied appending to file: %s"
LOG_APPEND_SECTION_ERROR: Final = "Error appending section: %s - %s"

# Section Validation Logs
LOG_VALIDATE_SECTION_START: Final = "Starting section validation for: %s"
LOG_SECTION_UPDATE_START: Final = "Updating section '%s' in %s"
LOG_SECTION_VALIDATION_ERROR: Final = "Section validation failed: %s"
LOG_MISSING_MARKER: Final = "Missing marker for header: {header_title}"
LOG_MISMATCHED_MARKER: Final = (
    "Mismatched marker for header '{header_title}': expected '{expected}', found '{found}'"
)
LOG_ORPHANED_MARKER: Final = "Found marker without header: {marker_title}"
LOG_DUPLICATE_MARKER: Final = "Duplicate section marker found: '{marker_title}'"

# File content formatting
DEFAULT_NEWLINE: Final = "\n"
DOUBLE_NEWLINE: Final = "\n\n"

# Regular expression patterns
HEADER_NEXT_PATTERN: Final = r"^#{1,6}\s+.*$"  # For finding next header
SECTION_CONTENT_PATTERN: Final = (
    r"<!--\s*(?:Section|SECTION):"  # For checking marker format
)

# Additional log messages
LOG_APPEND_SECTION_SUCCESS: Final = "Successfully appended section '%s' to %s"
LOG_PERMISSION_DENIED_APPEND: Final = "Permission denied appending to file: %s"
LOG_APPEND_SECTION_ERROR: Final = "Error appending section: %s - %s"

# Additional error messages
ERROR_PERMISSION_DENIED_APPEND: Final = "Permission denied when writing to {file_path}"
ERROR_APPEND_GENERAL: Final = "Failed to append section: {error}"

# File operation constants
DEFAULT_HEADER_LEVEL: Final = 1
HEADER_LEVEL_RANGE: Final = range(1, 7)  # Valid header levels (1-6)
SECTION_CONTENT_SPACING: Final = "\n\n"  # Spacing between sections

# Regular expression patterns
HEADER_PATTERN_MULTILINE: Final = re.compile(PATTERN_HEADER, re.MULTILINE)
MARKER_PATTERN_MULTILINE: Final = re.compile(PATTERN_SECTION_MARKER)
YAML_CONTENT_PATTERN: Final = r"^---\n.*?\n---\n"  # For finding YAML frontmatter

# Additional logging messages
LOG_VALIDATE_FILENAME: Final = "Invalid filename rejected: {filename}"
LOG_ADDED_EXTENSION: Final = "Added .md extension: {filename}"
LOG_PATH_TOO_LONG: Final = "Path too long: {path}"
LOG_YAML_SERIALIZATION: Final = "Serializing metadata to YAML"
LOG_WRITING_FILE: Final = "Writing {count} characters to file: {path}"
LOG_CREATING_DIRECTORY: Final = "Creating directory: {path}"
LOG_DIR_CREATION_ERROR: Final = "Directory creation error: {path} - {error}"

# File operation constants
MD_EXTENSION: Final = ".md"
YAML_DUMP_SETTINGS: Final[Dict[str, bool]] = {
    "default_flow_style": False,
    "sort_keys": False,
}

# Additional error messages
ERROR_DIRECTORY_EXISTS: Final = "Cannot create directory (file exists): %s"
ERROR_DIRECTORY_PERMISSION: Final = "Permission denied creating directory: %s"
ERROR_DIRECTORY_CREATION_FAILED: Final = "Directory creation error: %s"

# Regular Expression Patterns
SECTION_START_PATTERN: Final = r"^#{1,6}\s+.*$"  # For finding section headers
SECTION_END_PATTERN: Final = r"\n#{1,6}\s+"  # For finding the next section
CONTENT_SPACING_PATTERN: Final = r"\n\n"  # For normalizing spacing between sections
YAML_FRONTMATTER_PATTERN: Final = (
    r"^---\n.*?\n---\n\s*"  # For matching YAML frontmatter
)

# File Operation Messages
LOG_DIRECTORY_VALIDATION: Final = "Validating directory: %s"
LOG_FILE_VALIDATION: Final = "Validating file: %s"
LOG_CONTENT_UPDATE: Final = "Updating content in file: %s"
LOG_SECTION_FOUND: Final = "Found section '%s' in file %s"
LOG_SECTION_UPDATE: Final = "Updating section '%s' in file %s"
LOG_SECTION_REPLACE: Final = "Replacing content in section '%s'"
LOG_CONTENT_WRITE: Final = "Writing updated content to file: %s"

# Error Messages
ERROR_SECTION_UPDATE_FAILED: Final = "Failed to update section: {error}"
ERROR_SECTION_NOT_FOUND: Final = "Section '{section_title}' not found in file"
ERROR_INVALID_SECTION_FORMAT: Final = "Invalid section format in file: {file_path}"
ERROR_CONTENT_UPDATE_FAILED: Final = "Failed to update content: {error}"

# File Operation Constants
DEFAULT_CONTENT_BUFFER: Final = "\n\n"  # Default spacing between sections
SECTION_HEADER_PREFIX: Final = "#"  # Markdown header prefix
MIN_SECTION_LEVEL: Final = 1  # Minimum header level
MAX_SECTION_LEVEL: Final = 6  # Maximum header level
FRONTMATTER_MARKER: Final = "---"  # YAML frontmatter delimiter

# Validation Constants
FILENAME_MAX_LENGTH: Final = 255  # Maximum filename length
PATH_MAX_LENGTH: Final = 4096  # Maximum path length for most filesystems
VALID_HEADER_LEVELS: Final = range(1, 7)  # Valid markdown header levels

# Log messages for section operations
LOG_SECTION_NOT_FOUND: Final = "Section marker not found: {section_title}"

# Validation patterns
HEADER_TITLE_GROUP: Final = 2  # Index of the header title group in regex match
MARKER_TITLE_GROUP: Final = 1  # Index of the marker title group in regex match

# Log messages
LOG_VALIDATE_SECTION_START: Final = "Starting section validation for: %s"
LOG_SECTION_APPEND_SUCCESS: Final = "Successfully appended section '%s' to %s"
LOG_SECTION_UPDATE_START: Final = "Updating section '%s' in %s"
LOG_SECTION_VALIDATION_ERROR: Final = "Section validation failed: %s"

# Error messages
ERROR_SECTION_VALIDATION_FAILED: Final = "Section validation failed: {error}"
ERROR_SECTION_MARKER_MISMATCH: Final = (
    "Section marker mismatch: expected '{expected}', found '{found}'"
)

# Metadata validation logs
LOG_INVALID_METADATA_TYPES: Final = "Invalid metadata types detected in: %s"
LOG_MISSING_METADATA_FIELDS: Final = "Missing required metadata fields: %s"

# Configuration logs
LOG_USING_DEFAULT_CONFIG: Final = "Using default configuration"
LOG_CONFIG_DEBUG: Final = "Debug configuration: %s"

# File Operation Logs
LOG_FILE_EXISTS: Final = "File already exists: %s"
LOG_PERMISSION_ERROR: Final = "Permission error checking path: %s - %s"
LOG_DOCUMENT_CREATED: Final = "Successfully created document: %s"
LOG_CLEANUP_PARTIAL_FILE: Final = "Exception occurred, cleaning up partial file: %s"
LOG_UNEXPECTED_ERROR: Final = "Unexpected error: %s (%s)"

# Error messages for section operations
ERROR_SECTION_NOT_FOUND: Final = "Section '{section_title}' not found in document"

# File I/O log messages
LOG_READING_FILE: Final = "Reading file: {path} with encoding: {encoding}"
LOG_READ_SUCCESS: Final = "Successfully read {count} characters from {path}"
LOG_ENCODING_ERROR: Final = "Encoding error reading {path} with {encoding}: {error}"

ERROR_UNSUPPORTED_ENCODING: Final = "Unsupported encoding: {encoding}"

# File operation log messages
LOG_NO_WRITE_PERMISSION: Final = "No write permission for target file: {path}"
LOG_ENCODING_WRITE_ERROR: Final = (
    "Encoding error writing content with {encoding}: {error}"
)
LOG_PERMISSION_DENIED_TEMP: Final = "Permission denied writing temporary file: {path}"
LOG_TEMP_WRITE_FAILED: Final = "Failed to write temporary file {path}: {error}"
LOG_MOVING_FILE: Final = "Moving {source} to {target}"
LOG_ATOMIC_WRITE_SUCCESS: Final = "Successfully completed atomic write to {path}"
LOG_MOVE_PERMISSION_DENIED: Final = (
    "Permission denied moving temp file to target: {path}"
)
LOG_MOVE_FAILED: Final = "Failed to move temp file to target {path}: {error}"
LOG_TEMP_CLEANUP: Final = "Cleaned up temporary file: {path}"
LOG_CLEANUP_FAILED: Final = "Failed to clean up partial file: {path} - {error}"

# File operation log messages
LOG_WRITING_FILE: Final = "Writing {count} characters to file: {path}"
LOG_WRITE_SUCCESS: Final = "Successfully wrote to {path}"
LOG_ATOMIC_WRITE_START: Final = (
    "Starting atomic write to {target} using temp file: {temp}"
)
LOG_TEMP_DIR_NOT_FOUND: Final = "Temporary directory not found: {path}"
LOG_NO_TEMP_DIR_PERMISSION: Final = (
    "No write permission for temporary directory: {path}"
)
LOG_PARENT_DIR_PERMISSION: Final = (
    "No permission to create parent directory for: {path}"
)
LOG_PARENT_DIR_ERROR: Final = "Failed to create parent directory for {path}: {error}"

# Validation messages
LOG_MISSING_MARKER: Final = "Missing section marker for header: {header_title}"
LOG_MISMATCHED_MARKER: Final = (
    "Mismatched section marker: header '{header_title}' vs marker '{found}' (expected: '{expected}')"
)
LOG_ORPHANED_MARKER: Final = (
    "Found marker '{marker_title}' without a corresponding header"
)
LOG_DUPLICATE_MARKER: Final = "Duplicate section marker found: {marker_title}"
LOG_SECTION_MARKER_VALID: Final = "Section markers validated successfully"

# Section operation errors
ERROR_MISSING_SECTION_MARKER: Final = (
    "Header '{header_title}' is missing its section marker"
)
ERROR_MISMATCHED_SECTION_MARKER: Final = (
    "Section marker for '{header_title}' does not match header title"
)
ERROR_ORPHANED_SECTION_MARKER: Final = (
    "Found marker '{marker_title}' without a corresponding header"
)
ERROR_DUPLICATE_SECTION_MARKER: Final = (
    "Duplicate section marker found: '{marker_title}'"
)

# Path validation errors
ERROR_PATH_NOT_FOUND: Final = "Path does not exist: {path}"
ERROR_NO_WRITE_PERMISSION: Final = "No write permission for Path: {path}"
ERROR_PERMISSION_DENIED: Final = "No write permission for Path: {path}"
ERROR_TEMP_DIR_NOT_FOUND: Final = "Path does not exist: {path}"

# Dependency check messages
ERROR_ATOMIC_MOVE_UNSUPPORTED: Final = (
    "Atomic file operations not fully supported: {error}"
)
ERROR_PERMISSION_CHECK_UNSUPPORTED: Final = (
    "Permission checking not fully supported: {error}"
)
ERROR_ENVIRONMENT_CHECK_FAILED: Final = (
    "Environment compatibility check failed: {error}"
)
ERROR_PYTHON_VERSION: Final = (
    "Python 3.7 or higher is required for proper Path object support"
)

# Warning messages
WARNING_PATH_TOO_LONG: Final = "Path too long: {path}"

# Log messages for file cleanup
LOG_REMOVING_PARTIAL_FILE: Final = "Removing partial file: {path}"
LOG_CLEANUP_FAILED: Final = "Failed to clean up partial file: {path} - {error}"

# Log messages for append_section
LOG_INVALID_CONTENT: Final = "Invalid content provided: {content}"
LOG_INVALID_SECTION_TITLE: Final = "Invalid section title: {title}"
LOG_FILE_NOT_FOUND: Final = "File not found: %s"
LOG_INVALID_FILE_FORMAT: Final = "Invalid file format: %s"
LOG_PERMISSION_ERROR_CHECKING_FILE: Final = "Permission error checking file: %s - %s"

# Error messages for append_section
ERROR_INVALID_CONTENT: Final = "Content must be a non-empty string"
ERROR_INVALID_SECTION_TITLE: Final = "Section title must be a non-empty string"
ERROR_DOCUMENT_NOT_EXIST: Final = "Document does not exist: {file_path}"
ERROR_INVALID_MARKDOWN_FILE: Final = "File must be a Markdown document: {file_path}"
ERROR_PERMISSION_DENIED_ACCESS: Final = "Permission denied when accessing {file_path}"

# Log messages for section operations
LOG_SECTION_EXISTS: Final = "Section already exists: %s in %s"
LOG_APPEND_TO_EXISTING_SECTION: Final = "Appending to existing section: %s"
LOG_INVALID_HEADER_LEVEL: Final = "Invalid header level: %s"
LOG_HEADER_LEVEL_ERROR: Final = "Header level error: %s"
LOG_USING_HEADER_LEVEL: Final = "Using header level %d for section '%s' in %s"

# Error messages for section operations
ERROR_SECTION_EXISTS: Final = "Section '{section_title}' already exists"
ERROR_INVALID_HEADER_LEVEL: Final = "Header level must be an integer between 1 and 6"
ERROR_HEADER_LEVEL: Final = "Header level error: {error}"

# Error messages for section operations
ERROR_SECTION_INSERT_AFTER_NOT_FOUND: Final = "Section to insert after not found: {insert_after}"

# File mode constants
FILE_MODE_READ: Final = "r"
FILE_MODE_WRITE: Final = "w"
FILE_MODE_APPEND: Final = "a"
FILE_MODE_READ_BINARY: Final = "rb"
FILE_MODE_WRITE_BINARY: Final = "wb"
FILE_MODE_APPEND_BINARY: Final = "ab"

# Log messages for section operations
LOG_SECTION_INSERT_SUCCESS: Final = "Successfully inserted section '%s' after '%s' in %s"
LOG_SECTION_APPEND_SUCCESS: Final = "Successfully appended section '%s' to %s"
LOG_PERMISSION_DENIED_APPEND: Final = "Permission denied appending to file: %s"
LOG_ERROR_APPENDING_SECTION: Final = "Error appending section: %s - %s"

# Error messages for file operations
ERROR_PERMISSION_DENIED_WRITE: Final = "Permission denied when writing to {file_path}"
ERROR_FAILED_APPEND_SECTION: Final = "Failed to append section: {error}"

# Section content format
SECTION_CONTENT_FORMAT: Final = "{spacing}{header_prefix} {section_title}\n{section_marker}\n{content}\n"

# Regular expression pattern for section markers
SECTION_MARKER_REGEX: Final = r"<!-- Section: .* -->"

# Markdown header prefix for level 2
HEADER_LEVEL_2_PREFIX: Final = "\n##"

# Log messages for section operations
LOG_SECTION_MARKER_NOT_FOUND: Final = "Section marker not found: {section_title}"
LOG_FOUND_SECTION_BOUNDARIES: Final = "Found section boundaries for '{section_title}': start={start}, end={end}"

# Keys for section data
SECTION_HEADER_KEY: Final = "header"
SECTION_MARKER_KEY: Final = "marker"
SECTION_CONTENT_KEY: Final = "section_content"

# Log messages for file operations
LOG_FILE_OPERATION_ERROR: Final = "File operation error: {error}"

# Message for when no associated header is found
NO_ASSOCIATED_HEADER: Final = "No associated header"

# External tool configurations
REMARK_CONFIG_FILE: Final = ".remarkrc.js"
MARKDOWNLINT_CONFIG_FILE: Final = ".markdownlint.json"
PANDOC_FROM_FORMAT: Final = "markdown"
PANDOC_TO_FORMAT: Final = "html"

# External tool error messages
ERROR_REMARK_VALIDATION: Final = "Syntax validation failed: {error}"
ERROR_MARKDOWNLINT_VALIDATION: Final = "Additional validation failed: {error}"
ERROR_PANDOC_VALIDATION: Final = "Format compatibility check failed: {error}"

# Error suggestions for common markdown issues
ERROR_SUGGESTIONS = {
    # Markdownlint rules
    'MD007': 'Fix list indentation to use 2 spaces',
    'MD022': 'Add blank lines before and after headers',
    'MD031': 'Add blank lines around code blocks',
    'MD032': 'Add blank lines before lists',
    'MD034': 'Use bare URLs in angle brackets <url>',
    'MD037': 'Remove spaces inside emphasis markers',
    
    # Remark-lint rules
    'no-undefined-references': 'Ensure all referenced links and images are defined',
    'no-empty-sections': 'Add content to empty sections or remove them',
    'heading-increment': 'Headers should increment by one level at a time',
    'no-duplicate-headings': 'Use unique heading text within sections',
    
    # Content validation
    'broken_image': 'Ensure image file exists in the specified path',
    'broken_link': 'Verify the linked file exists in the correct location',
    'empty_file': 'Add content to the markdown file',
    
    # GFM-specific suggestions
    'table-pipe-alignment': 'Align table pipes vertically for better readability',
    'table-cell-padding': 'Add single space padding around table cell content',
    'no-undefined-references': 'Define all referenced links at the bottom of the document',
    'heading-increment': 'Headers should only increment by one level at a time',
    'no-duplicate-headings': 'Use unique heading text within each section',
    'task-list-marker': 'Use "[ ]" or "[x]" for task list items',
    'task-list-indent': 'Task lists should be indented with 2 spaces',
    'task-list-empty': 'Task list items should not be empty',
    'task-list-spacing': 'Add a space after the dash: "- [ ]"',
}

# Error messages for validation
ERROR_MESSAGES: Final[Dict[str, str]] = {
    "invalid_spacing": "Invalid spacing in task list marker",
    "invalid_marker": "Invalid task list marker",
    "invalid_format": "Invalid task list format",
}
