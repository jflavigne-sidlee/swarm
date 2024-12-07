"""Centralized file validation utilities."""

import logging
import warnings
from pathlib import Path
from typing import Optional, Dict, Any, Union
import os

from .config import WriterConfig
from .constants import MD_EXTENSION
from .exceptions import (
    WriterError,
    FileValidationError,
    FilePermissionError
)
from .file_io import validate_file_access, resolve_path_with_config
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
    file_path: Union[Path, str],
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

def validate_path_length(file_path: Union[Path, str]) -> Path:

    if len(str(file_path)) > MAX_PATH_LENGTH:
        logger.warning(LOG_PATH_TOO_LONG.format(path=file_path))
        raise WriterError(ERROR_PATH_TOO_LONG.format(max_length=MAX_PATH_LENGTH, path=file_path))
    
    return file_path


def is_valid_filename(
    filename: Union[Path, str], 
    extension: Optional[str] = None,
    strict_extension: bool = True
) -> bool:
    """Check if filename is valid and optionally validate extension."""
    # Convert Path to string if needed
    if isinstance(filename, Path):
        filename = filename.name
    
    # Basic validation
    if not filename or len(filename) > MAX_FILENAME_LENGTH:
        return False

    # Check for path-like patterns and separators
    if "/" in filename or "\\" in filename or "." == filename or ".." == filename:
        return False

    # Check for forbidden characters
    if any(char in filename for char in FORBIDDEN_FILENAME_CHARS):
        return False

    # Check for reserved names
    base_name = Path(filename).stem.upper()
    if base_name in RESERVED_WINDOWS_FILENAMES:
        return False

    # Check for trailing spaces or dots
    if filename.endswith((" ", ".")):
        return False

    # Validate extension if specified
    if extension:
        if not extension.startswith('.'):
            extension = f'.{extension}'
            
        if strict_extension:
            return filename.lower().endswith(extension.lower())
        else:
            parts = filename.lower().split(extension.lower())
            return len(parts) > 1 and not parts[0].endswith('.')

    return True

def ensure_valid_markdown_file(
    file_path: Union[Path, str],
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

def validate_file(file_path: Union[Path, str], require_write: bool = False) -> None:
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

def validate_and_resolve_path(
    file_path: Union[Path, str],
    config: WriterConfig,
    require_write: bool = True,
    check_exists: bool = True,
) -> Path:
    """Validate filename, resolve path, and check file permissions."""
    if isinstance(file_path, str):
        warnings.warn(
            f"String path '{file_path}' passed to {validate_and_resolve_path.__name__}. "
            "Consider passing a Path object instead.",
            stacklevel=2
        )
        file_path = Path(file_path)
    
    # Check raw string for path traversal and separators
    path_str = str(file_path)
    
    # If it's not an absolute path, treat it as a filename and validate strictly
    if not file_path.is_absolute():
        if "/" in path_str or "\\" in path_str or "." == path_str or ".." == path_str:
            logger.warning(LOG_VALIDATE_FILENAME.format(filename=path_str))
            raise FileValidationError("Invalid filename")
    
    # First validate basic filename without extension requirements
    file_name = file_path.name
    if not is_valid_filename(file_name):
        logger.warning(LOG_VALIDATE_FILENAME.format(filename=file_name))
        raise FileValidationError("Invalid filename")

    # Handle extension - add if missing
    if file_name and not file_name.lower().endswith(MD_EXTENSION.lower()):
        file_name = file_name + MD_EXTENSION
        logger.debug(LOG_ADDED_EXTENSION.format(filename=file_name))
        file_path = file_path.with_name(file_name)
        
    # Final validation with strict extension check
    if not is_valid_filename(file_path.name, MD_EXTENSION, strict_extension=True):
        logger.warning(LOG_VALIDATE_FILENAME.format(filename=file_path.name))
        raise FileValidationError("Invalid filename")

    # Resolve path
    resolved_path = resolve_path_with_config(file_path, config.drafts_dir)

    # Validate file exists and has correct permissions only if required
    if check_exists:
        validate_file(resolved_path, require_write=require_write)

    return resolved_path

