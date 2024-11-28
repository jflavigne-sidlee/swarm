from typing import Final, Dict

ERROR_APPEND_SECTION_FAILED: Final = "Failed to append section: {error}"
ERROR_BROKEN_FILE: Final = "Broken file link: {path}"
ERROR_BROKEN_IMAGE: Final = "Broken image link: {path}"
ERROR_CONTENT_UPDATE_FAILED: Final = "Failed to update content: {error}"
ERROR_DIR_CREATION: Final = "Directory creation error: {error}"
ERROR_DIR_EXISTS: Final = "Cannot create directory: {path} (file exists)"
ERROR_DIRECTORY_PERMISSION: Final = "Permission denied creating directory: {path}"
ERROR_DOCUMENT_NOT_EXIST: Final = "Document does not exist: {file_path}"
ERROR_EMPTY_FILE: Final = "File is empty"
ERROR_FAILED_APPEND_SECTION: Final = "Failed to append section: {error}"
ERROR_FILE_EXISTS: Final = "File already exists: {path}"
ERROR_FILE_WRITE: Final = "File writing error: {error}"
ERROR_GET_DEFAULT: Final = "Failed to get default for {name}: {error}"
ERROR_HEADER_LEVEL: Final = "Header level error: {error}"

ERROR_INVALID_CONFIG: Final = "Invalid configuration: {error}"
ERROR_INVALID_CONTENT: Final = "Content must be a non-empty string"
ERROR_INVALID_FILE_FORMAT: Final = "Invalid file format: File must have .md extension"
ERROR_INVALID_FILENAME: Final = "Invalid filename"
ERROR_INVALID_HEADER_LEVEL: Final = "Header level must be an integer between 1 and 6"
ERROR_INVALID_MARKDOWN_FILE: Final = "File must be a Markdown document: {file_path}"
ERROR_INVALID_METADATA_TYPE: Final = "Invalid metadata type"
ERROR_INVALID_SECTION_FORMAT: Final = "Invalid section format in file: {file_path}"
ERROR_INVALID_SECTION_TITLE: Final = "Section title must be a non-empty string"
ERROR_INVALID_TYPE: Final = "Invalid type for '{name}': got {got}, expected {expected}."

ERROR_LINE_MESSAGE: Final = "Line {line}: {message}"
ERROR_MARKDOWN_FORMATTING: Final = "Markdown formatting error: {error}"
ERROR_MARKDOWNLINT_VALIDATION: Final = "Additional validation failed: {error}"
ERROR_MISSING_METADATA: Final = "Missing required metadata fields: {fields}"
ERROR_NO_WRITE_PERMISSION: Final = "No write permission for Path: {path}"
ERROR_NO_ZERO: Final = "Zero is not allowed for '{name}'."
ERROR_PANDOC_COMPATIBILITY: Final = "Pandoc compatibility error: {error}"
ERROR_PANDOC_VALIDATION: Final = "Format compatibility check failed: {error}"
ERROR_PANDOC_MISSING: Final = "Pandoc validation skipped: {suggestion}"
ERROR_PANDOC_EXECUTION: Final = "Error executing Pandoc: {error}"
ERROR_PANDOC_NOT_INSTALLED: Final = "Pandoc is not installed or not accessible"
ERROR_PANDOC_LATEX_MATH: Final = "Invalid LaTeX math expression detected"
ERROR_PATH_NO_READ: Final = "No read permission for {name}: {path}"
ERROR_PATH_NO_WRITE: Final = "No write permission for {name}: {path}"
ERROR_PATH_NOT_DIR: Final = "{name} is not a directory: {path}"
ERROR_PATH_NOT_EXIST: Final = "{name} does not exist: {path}"
ERROR_PATH_NOT_FOUND: Final = "Path does not exist: {path}"
ERROR_PATH_PROCESS: Final = "Failed to process {name}: {error}"
ERROR_PERMISSION_DENIED_DIR: Final = "Permission denied creating directory: {path}"
ERROR_PERMISSION_DENIED_FILE: Final = "Permission denied writing file: {path}"
ERROR_PERMISSION_DENIED_PATH: Final = "Permission denied accessing path: {path}"
ERROR_PERMISSION_DENIED_WRITE: Final = "Permission denied when writing to {file_path}"
ERROR_REMARK_VALIDATION: Final = "Syntax validation failed: {error}"
ERROR_REQUIRED_FIELD: Final = "Required field '{name}' is not set."
ERROR_SECTION_EXISTS: Final = "Section '{section_title}' already exists"
ERROR_SECTION_NOT_FOUND: Final = "Section '{section_title}' not found in document"
ERROR_SECTION_UPDATE_FAILED: Final = "Failed to update section: {error}"
ERROR_SECTION_VALIDATION_FAILED: Final = "Section validation failed: {error}"
ERROR_SUGGESTION_FORMAT: Final = "\nSuggestion: {suggestion}"
ERROR_TASK_LIST_INVALID_MARKER: Final = "Invalid task list marker"
ERROR_UNEXPECTED: Final = "Unexpected error validating {name}: {error}"
ERROR_UNSUPPORTED_ENCODING: Final = "Unsupported encoding: {encoding}"
ERROR_UNKNOWN_FIELD: Final = "Unknown configuration fields: {fields}"
ERROR_UNKNOWN_FIELD_NAME: Final = "Unknown field: {name}"
ERROR_VALIDATION_FAILED: Final = "Validation failed: {error}"
ERROR_YAML_SERIALIZATION: Final = "YAML serialization error: {error}"


ERROR_ATOMIC_MOVE_UNSUPPORTED: Final = (
    "Atomic file operations not fully supported: {error}"
)
ERROR_CUSTOM_VALIDATION: Final = (
    "Custom validation failed for '{name}'. Value: {value}. Error: {error}"
)
ERROR_DUPLICATE_SECTION_MARKER: Final = (
    "Duplicate section marker found: '{marker_title}'"
)
ERROR_ENVIRONMENT_CHECK_FAILED: Final = (
    "Environment compatibility check failed: {error}"
)
ERROR_HEADER_EMPTY: Final = (
    "Line {line}: Empty header detected. Headers must contain text."
)
ERROR_HEADER_INVALID_START: Final = (
    "Line {line}: Document should start with a level 1 header (found level {level})"
)
ERROR_HEADER_LEVEL_EXCEEDED: Final = (
    "Line {line}: Header level {level} exceeds maximum allowed level of 6"
)
ERROR_HEADER_LEVEL_SKIP: Final = (
    "Line {line}: Header level jumps from {current} to {level}. Headers should increment by only one level at a time."
)
ERROR_INVALID_CHOICE: Final = (
    "Invalid value for '{name}': '{value}'. Must be one of: {choices}"
)
ERROR_MISMATCHED_SECTION_MARKER: Final = (
    "Section marker for '{header_title}' does not match header title"
)
ERROR_MISSING_SECTION_MARKER: Final = (
    "Header '{header_title}' is missing its section marker"
)
ERROR_ORPHANED_SECTION_MARKER: Final = (
    "Found marker '{marker_title}' without a corresponding header"
)
ERROR_PATH_TOO_LONG: Final = (
    "Full path exceeds maximum length of {max_length} characters: {path}"
)
ERROR_PATTERN_MISMATCH: Final = (
    "Invalid format for '{name}': '{value}'. Must match pattern: {pattern}"
)
ERROR_PERMISSION_CHECK_UNSUPPORTED: Final = (
    "Permission checking not fully supported: {error}"
)
ERROR_PYTHON_VERSION: Final = (
    "Python 3.7 or higher is required for proper Path object support"
)
ERROR_SECTION_INSERT_AFTER_NOT_FOUND: Final = (
    "Section to insert after not found: {insert_after}"
)
ERROR_SECTION_MARKER_MISMATCH: Final = (
    "Section marker mismatch: expected '{expected}', found '{found}'"
)
ERROR_TASK_LIST_EXTRA_SPACE: Final = (
    "Extra spaces after dash in task list marker (e.g., '-  [ ]' instead of '- [ ]')"
)
ERROR_TASK_LIST_MISSING_SPACE: Final = (
    "Missing space after dash in task list marker (e.g., '-[ ]' instead of '- [ ]')"
)
ERROR_TASK_LIST_MISSING_SPACE_AFTER: Final = (
    "Missing space after closing bracket in task list marker (e.g., '- [ ]text' instead of '- [ ] text')"
)
ERROR_VALUE_TOO_LARGE: Final = (
    "Value for '{name}' is too large: {value}. Maximum allowed: {max}."
)
ERROR_VALUE_TOO_SMALL: Final = (
    "Value for '{name}' is too small: {value}. Minimum allowed: {min}."
)

# Error messages for validation
ERROR_MESSAGES: Final[Dict[str, str]] = {
    "invalid_spacing": "Invalid spacing in task list marker",
    "invalid_marker": "Invalid task list marker",
    "invalid_format": "Invalid task list format",
    "empty_file": "File is empty",  # Added constant for empty file error message
}

ERROR_FILE_NOT_FOUND: Final = "File not found: {path}"
from typing import Final

# Metadata-related errors
ERROR_INVALID_METADATA_FORMAT: Final = "Invalid metadata format: Must be valid YAML dictionary"
ERROR_MISSING_REQUIRED_METADATA: Final = "Missing required metadata fields: {fields}"