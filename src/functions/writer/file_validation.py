"""Centralized file validation utilities."""

import logging
from pathlib import Path
from typing import Optional, Dict, Any

from .config import WriterConfig
from .constants import MD_EXTENSION
from .exceptions import (
    WriterError,
    FileValidationError,
    FilePermissionError
)
from .file_io import validate_file_access
from .validation_constants import (
    MAX_FILENAME_LENGTH,
    MAX_PATH_LENGTH,
    FORBIDDEN_FILENAME_CHARS,
    RESERVED_WINDOWS_FILENAMES,
)
from .logs import (
    LOG_INVALID_METADATA_TYPES,
    LOG_MISSING_METADATA_FIELDS,
    LOG_VALIDATE_FILENAME,
    LOG_PATH_TOO_LONG,
    LOG_ADDED_EXTENSION,
    LOG_FILE_NOT_FOUND,
    LOG_PERMISSION_ERROR,
    LOG_INVALID_FILE_FORMAT,
)
from .errors import (
    ERROR_INVALID_METADATA_TYPE,
    ERROR_MISSING_METADATA,
    ERROR_INVALID_FILENAME,
    ERROR_PATH_TOO_LONG,
    ERROR_DOCUMENT_NOT_EXIST,
    ERROR_INVALID_MARKDOWN_FILE,
)

logger = logging.getLogger(__name__)

def validate_file_inputs(
    file_path: Path,
    config: WriterConfig,
    require_write: bool = True,
    create_parents: bool = False,
    check_extension: bool = True,
    extension: str = MD_EXTENSION
) -> None:
    """Centralized validation for file-related operations.
    
    Args:
        file_path: Path to validate
        config: Writer configuration
        require_write: Whether write permission is required
        create_parents: Whether to create parent directories
        check_extension: Whether to enforce extension check
        extension: File extension to check (defaults to .md)
        
    Raises:
        FileValidationError: If filename is invalid
        FilePermissionError: If permissions are insufficient
        FileNotFoundError: If file doesn't exist and require_write is False
    """
    # Validate filename
    if not is_valid_filename(file_path.name):
        logger.error(f"Invalid filename: {file_path.name}")
        raise FileValidationError(f"Invalid filename: {file_path.name}")

    # Check path length
    if len(str(file_path)) > MAX_PATH_LENGTH:
        logger.error(f"Path too long: {file_path}")
        raise FileValidationError(
            f"Path exceeds maximum length of {MAX_PATH_LENGTH} characters"
        )

    # Validate extension
    if check_extension and file_path.suffix != extension:
        logger.error(f"Invalid file extension: {file_path.suffix}")
        raise FileValidationError(f"File must have {extension} extension")

    # Validate file access using centralized function
    validate_file_access(
        file_path,
        require_write=require_write,
        create_parents=create_parents,
        check_exists=not create_parents
    )

def validate_filename(file_name: str, config: WriterConfig) -> Path:
    """Validate filename and return full path."""
    if not file_name or not is_valid_filename(file_name):
        logger.warning(LOG_VALIDATE_FILENAME.format(filename=file_name))
        raise WriterError(ERROR_INVALID_FILENAME)

    # Ensure .md extension
    if not file_name.endswith(MD_EXTENSION):
        file_name += MD_EXTENSION
        logger.debug(LOG_ADDED_EXTENSION.format(filename=file_name))

    # Check path length
    full_path = config.drafts_dir / file_name
    if len(str(full_path)) > MAX_PATH_LENGTH:
        logger.warning(LOG_PATH_TOO_LONG.format(path=full_path))
        raise WriterError(
            ERROR_PATH_TOO_LONG.format(max_length=MAX_PATH_LENGTH, path=full_path)
        )

    return full_path

def is_valid_filename(filename: str) -> bool:
    """Check if filename is valid.
    
    Args:
        filename: Name to validate
        
    Returns:
        bool: True if filename is valid
    """
    # Check length
    if not filename or len(filename) > MAX_FILENAME_LENGTH:
        return False

    # Check for forbidden characters
    if any(char in filename for char in FORBIDDEN_FILENAME_CHARS):
        return False

    # Check for reserved names
    base_name = Path(filename).stem.upper()
    if base_name in RESERVED_WINDOWS_FILENAMES:
        return False

    # Check for special directory names
    if filename in {".", "..", "./", "../"}:
        return False

    # Check for trailing spaces or dots
    if filename.endswith((" ", ".")):
        return False

    return True

def ensure_valid_markdown_file(
    file_path: Path,
    config: WriterConfig,
    create: bool = False
) -> None:
    """Ensure a valid markdown file exists or can be created.
    
    Args:
        file_path: Path to the file
        config: Writer configuration
        create: Whether to create the file if it doesn't exist
        
    Raises:
        FileValidationError: If file validation fails
        FilePermissionError: If permissions are insufficient
    """
    try:
        validate_file_inputs(
            file_path,
            config,
            require_write=create,
            create_parents=create,
            check_extension=True
        )
        
        if create and not file_path.exists():
            file_path.touch()
            logger.debug(f"Created new markdown file: {file_path}")
            
    except Exception as e:
        logger.error(f"Failed to validate/create markdown file: {str(e)}")
        raise 

def validate_metadata(metadata: Dict[str, Any], config: WriterConfig) -> None:
    """Validate metadata types and required fields.
    
    Args:
        metadata: Dictionary of metadata to validate
        config: Writer configuration containing validation rules
        
    Raises:
        WriterError: If metadata validation fails
    """
    if not isinstance(metadata, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in metadata.items()
    ):
        logger.warning(LOG_INVALID_METADATA_TYPES, metadata)
        raise WriterError(ERROR_INVALID_METADATA_TYPE)

    missing_fields = [field for field in config.metadata_keys if field not in metadata]
    if missing_fields:
        logger.warning(LOG_MISSING_METADATA_FIELDS.format(fields=missing_fields))
        raise WriterError(
            ERROR_MISSING_METADATA.format(fields=", ".join(missing_fields))
        )

def validate_file(file_path: Path, require_write: bool = False) -> None:
    """Validate that the file exists, has the correct format, and meets permission requirements.

    Args:
        file_path: Path object pointing to the file to validate
        require_write: If True, also check for write permissions

    Raises:
        WriterError: If file doesn't exist, has wrong format, or lacks permissions
        FileNotFoundError: If the file doesn't exist
        FilePermissionError: If required permissions are not available
    """
    try:
        # Check if file exists and has correct permissions
        validate_file_access(file_path, require_write=require_write, check_exists=True)

        # Verify file extension
        if file_path.suffix.lower() != MD_EXTENSION:
            logger.error(LOG_INVALID_FILE_FORMAT.format(path=file_path))
            raise WriterError(ERROR_INVALID_MARKDOWN_FILE.format(path=file_path))

    except FileNotFoundError:
        logger.error(LOG_FILE_NOT_FOUND.format(path=file_path))
        raise WriterError(ERROR_DOCUMENT_NOT_EXIST.format(file_path=file_path))
    except PermissionError:
        logger.error(LOG_PERMISSION_ERROR.format(path=file_path))
        raise FilePermissionError(str(file_path))

