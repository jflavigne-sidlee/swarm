"""Centralized file validation utilities."""

import logging
from pathlib import Path
from typing import Optional

from .config import WriterConfig
from .constants import MD_EXTENSION
from .exceptions import (
    WriterError,
    FileValidationError,
    FilePermissionError
)
from .file_io import validate_path_permissions, ensure_parent_exists
from .validation_constants import (
    MAX_FILENAME_LENGTH,
    MAX_PATH_LENGTH,
    FORBIDDEN_FILENAME_CHARS,
    RESERVED_WINDOWS_FILENAMES,
)

logger = logging.getLogger(__name__)

def validate_file_inputs(
    file_path: Path,
    config: WriterConfig,
    require_write: bool = True,
    create_parents: bool = False,
    check_extension: bool = True,
) -> None:
    """Centralized validation for file-related operations.
    
    Args:
        file_path: Path to validate
        config: Writer configuration
        require_write: Whether write permission is required
        create_parents: Whether to create parent directories
        check_extension: Whether to enforce .md extension
        
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
    if check_extension and file_path.suffix != MD_EXTENSION:
        logger.error(f"Invalid file extension: {file_path.suffix}")
        raise FileValidationError(f"File must have .md extension")

    # Create parent directories if needed
    if create_parents and config.create_directories:
        ensure_parent_exists(file_path)

    # Check file existence and permissions
    if file_path.exists():
        validate_path_permissions(file_path, require_write=require_write)
    elif not require_write:
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File does not exist: {file_path}")


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