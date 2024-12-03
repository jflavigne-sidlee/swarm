# Log messages
from typing import Final

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

# Field info
NO_DESCRIPTION: Final = "No description available"

# Warning messages
WARNING_PATH_TOO_LONG: Final = "Path too long: {path}"

# Message for when no associated header is found
NO_ASSOCIATED_HEADER: Final = "No associated header"

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

LOG_BACKUP_ENABLED: Final = "Backup functionality is disabled"
LOG_BACKUP_WARNING: Final = (
    "Backup directory is set but backup_enabled is False. The directory will not be used."
)
LOG_BACKUP_VALIDATED: Final = "Backup directory validated: {path}"
LOG_DIR_RELATIONSHIPS: Final = "Validating directory relationships"
LOG_SECTION_MARKER_VALIDATION: Final = "Starting section marker validation..."
LOG_SECTION_MARKER_VALID: Final = "All section markers are valid"
LOG_SECTION_NOT_FOUND: Final = "Section marker not found: {section_title}"
LOG_APPEND_SECTION_SUCCESS: Final = "Successfully appended section '%s' to %s"
LOG_PERMISSION_DENIED_APPEND: Final = "Permission denied appending to file: %s"
LOG_APPEND_SECTION_ERROR: Final = "Error appending section: %s - %s"
LOG_VALIDATE_SECTION_START: Final = "Starting section validation for: %s"
LOG_SECTION_UPDATE_START: Final = "Updating section '%s' in %s"
LOG_MISSING_MARKER: Final = "Missing marker for header: {header_title}"
LOG_MISMATCHED_MARKER: Final = (
    "Mismatched marker for header '{header_title}': expected '{expected}', found '{found}'"
)
LOG_ORPHANED_MARKER: Final = "Found marker without header: {marker_title}"
LOG_DUPLICATE_MARKER: Final = "Duplicate section marker found: '{marker_title}'"
LOG_APPEND_SECTION_SUCCESS: Final = "Successfully appended section '%s' to %s"
LOG_PERMISSION_DENIED_APPEND: Final = "Permission denied appending to file: %s"
LOG_APPEND_SECTION_ERROR: Final = "Error appending section: %s - %s"
LOG_VALIDATE_FILENAME: Final = "Invalid filename rejected: {filename}"
LOG_ADDED_EXTENSION: Final = "Added .md extension: {filename}"
LOG_PATH_TOO_LONG: Final = "Path too long: {path}"
LOG_YAML_SERIALIZATION: Final = "Serializing metadata to YAML"
LOG_WRITING_FILE: Final = "Writing {count} characters to file: {path}"
LOG_CREATING_DIRECTORY: Final = "Creating directory: {path}"
LOG_DIR_CREATION_ERROR: Final = "Directory creation error: {path} - {error}"
# File Operation Messages
LOG_DIRECTORY_VALIDATION: Final = "Validating directory: %s"
LOG_FILE_VALIDATION: Final = "Validating file: %s"
LOG_CONTENT_UPDATE: Final = "Updating content in file: %s"
LOG_SECTION_FOUND: Final = "Found section '%s' in file %s"
LOG_SECTION_UPDATE: Final = "Updating section '%s' in file %s"
LOG_SECTION_REPLACE: Final = "Replacing content in section '%s'"
LOG_CONTENT_WRITE: Final = "Writing updated content to file: %s"
# Log messages for section operations
LOG_SECTION_NOT_FOUND: Final = "Section marker not found: {section_title}"
LOG_VALIDATE_SECTION_START: Final = "Starting section validation for: %s"
LOG_SECTION_APPEND_SUCCESS: Final = "Successfully appended section '%s' to %s"
LOG_SECTION_UPDATE_START: Final = "Updating section '%s' in %s"
# Metadata validation logs
LOG_INVALID_METADATA_TYPES: Final = "Invalid metadata types detected in: %s"
LOG_MISSING_METADATA_FIELDS: Final = "Missing required metadata fields: {fields}"
# Configuration logs
LOG_USING_DEFAULT_CONFIG: Final = "Using default configuration"
LOG_CONFIG_DEBUG: Final = "Debug configuration: %s"

# File Operation Logs
LOG_FILE_EXISTS: Final = "File already exists: %s"
LOG_PERMISSION_ERROR: Final = "Permission error checking path: %s - %s"
LOG_DOCUMENT_CREATED: Final = "Successfully created document: %s"
LOG_CLEANUP_PARTIAL_FILE: Final = "Exception occurred, cleaning up partial file: %s"
LOG_UNEXPECTED_ERROR: Final = "Unexpected error: %s (%s)"
# File I/O log messages
LOG_READING_FILE: Final = "Reading file: {path} with encoding: {encoding}"
LOG_READ_SUCCESS: Final = "Successfully read {count} characters from {path}"
LOG_ENCODING_ERROR: Final = "Encoding error reading {path} with {encoding}: {error}"
LOG_FILE_READ_ERROR: Final = "Error reading file {path}: {error}"
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
# Log messages for append_section
LOG_INVALID_CONTENT: Final = "Invalid content provided: {content}"
LOG_INVALID_SECTION_TITLE: Final = "Invalid section title: {title}"
LOG_FILE_NOT_FOUND: Final = "File not found: %s"
LOG_INVALID_FILE_FORMAT: Final = "Invalid file format: %s"
# Log messages for file cleanup
LOG_REMOVING_PARTIAL_FILE: Final = "Removing partial file: {path}"
LOG_CLEANUP_FAILED: Final = "Failed to clean up partial file: {path} - {error}"
# Log messages for section operations
LOG_SECTION_EXISTS: Final = "Section already exists: %s in %s"
LOG_APPEND_TO_EXISTING_SECTION: Final = "Appending to existing section: %s"
LOG_INVALID_HEADER_LEVEL: Final = "Invalid header level: %s"
LOG_HEADER_LEVEL_ERROR: Final = "Header level error: %s"
LOG_USING_HEADER_LEVEL: Final = "Using header level %d for section '%s' in %s"
LOG_SECTION_INSERT_SUCCESS: Final = (
    "Successfully inserted section '%s' after '%s' in %s"
)
LOG_SECTION_APPEND_SUCCESS: Final = "Successfully appended section '%s' to %s"
LOG_PERMISSION_DENIED_APPEND: Final = "Permission denied appending to file: %s"
LOG_ERROR_APPENDING_SECTION: Final = "Error appending section: %s - %s"
LOG_SECTION_MARKER_NOT_FOUND: Final = "Section marker not found: {section_title}"
LOG_FOUND_SECTION_BOUNDARIES: Final = (
    "Found section boundaries for '{section_title}': start={start}, end={end}"
)
# Log messages for file operations
LOG_FILE_OPERATION_ERROR: Final = "File operation error: {error}"
LOG_PATH_NOT_FOUND: Final = "Path not found: {path}"
LOG_NO_READ_PERMISSION: Final = "No read permission for path: {path}"
# Log messages
LOG_EMPTY_FILE_DETECTED: Final = "Empty markdown file detected"

# Metadata operation messages
LOG_NO_METADATA_BLOCK: Final = "No metadata block found in {path}"

LOG_INVALID_YAML_METADATA: Final = "Invalid YAML in metadata block: {error}"
LOG_MISSING_METADATA_FIELDS: Final = "Missing required metadata fields: {fields}"

LOG_INVALID_METADATA_TYPE = "Invalid type detected for field '{field}': expected {expected}, got {actual}"
LOG_INVALID_METADATA_PATTERN = "Invalid pattern format for field '{field}'"
LOG_METADATA_BELOW_MIN = "Value for '{field}' is below minimum allowed value of {min_value}"
LOG_METADATA_ABOVE_MAX = "Value for '{field}' is above maximum allowed value of {max_value}"
LOG_METADATA_VALIDATION_FAILED = "Validation failed for field '{field}': {error}"

LOG_INVALID_METADATA_CHOICE = "Invalid choice for metadata field '{field}'. Allowed values are: {choices}"

LOG_DEFAULT_METADATA_VALIDATION_FAILED: Final = "Default metadata failed validation, returning empty dict"

# Lock debug messages
LOG_LOCK_EXISTS: Final = "Lock already exists for section '{section}'"
LOG_LOCK_ACQUIRED: Final = "Lock acquired for section '{section}'"
LOG_LOCK_FAILED: Final = "Failed to acquire lock for section '{section}'"
LOG_LOCK_RELEASED: Final = "Lock released for section '{section}'"

# Lock configuration validation
LOG_CONFIG_VALIDATION: Final = "Validating lock configuration"
LOG_CONFIG_VALIDATED: Final = "Lock configuration validated successfully"
LOG_CONFIG_ERROR: Final = "Invalid configuration value for {param}: {error}"

# Lock cleanup messages
LOG_CLEANUP_START: Final = "Starting lock cleanup in directory: {directory}"
LOG_CLEANUP_COMPLETE: Final = "Lock cleanup complete: removed {count} stale locks"
LOG_CLEANUP_ERROR: Final = "Lock cleanup failed: {error}"
LOG_STALE_LOCK_REMOVED: Final = "Removed stale lock: {lock_file}"
LOG_INVALID_LOCK_FILE: Final = "Invalid lock file {lock_file}: {error}"
LOG_LOCK_REMOVAL_FAILED: Final = "Failed to remove lock {lock_file}: {error}"
LOG_LOCK_AGE_CHECK_FAILED: Final = "Error checking lock age for {lock_file}: {error}"