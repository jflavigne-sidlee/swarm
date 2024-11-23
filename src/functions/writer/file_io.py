"""Centralized file I/O operations with strict content preservation rules."""

import logging
from pathlib import Path
import os
import shutil
from typing import Optional
from uuid import uuid4
from datetime import datetime

logger = logging.getLogger(__name__)

def ensure_directory_exists(directory: Path) -> None:
    """Ensure a directory exists, creating it if necessary.
    
    Args:
        directory: Directory path to ensure exists
        
    Raises:
        PermissionError: If directory can't be created due to permissions
        OSError: If directory creation fails for other reasons
    """
    try:
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {directory}")
    except PermissionError:
        logger.error(f"Permission denied creating directory: {directory}")
        raise
    except OSError as e:
        logger.error(f"Failed to create directory {directory}: {e}")
        raise

def ensure_parent_directory_exists(file_path: Path) -> None:
    """Ensure the parent directory of the file exists.
    
    Args:
        file_path: Path to file whose parent directory should exist
        
    Raises:
        PermissionError: If directory can't be created due to permissions
        OSError: If directory creation fails for other reasons
    """
    parent_dir = file_path.parent
    ensure_directory_exists(parent_dir)

def read_file(file_path: Path, encoding: str) -> str:
    """Read file content with strict content preservation.
    
    Rules:
    - No content modification
    - No whitespace normalization
    - No newline manipulation
    - Return exact content as found in file
    
    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If file can't be accessed
        UnicodeError: If file can't be decoded with specified encoding
    """
    logger.debug(f"Reading file: {file_path} with encoding: {encoding}")
    try:
        with open(file_path, "r", encoding=encoding) as f:
            content = f.read()
            logger.debug(f"Successfully read {len(content)} characters from {file_path}")
            return content
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except PermissionError:
        logger.error(f"Permission denied reading file: {file_path}")
        raise
    except UnicodeError as e:
        logger.error(f"Encoding error reading {file_path} with {encoding}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error reading {file_path}: {e}")
        raise

def validate_encoding(encoding: str) -> bool:
    """Validate if an encoding is supported by Python.
    
    Args:
        encoding: Encoding name to validate
        
    Returns:
        bool: True if encoding is supported, False otherwise
        
    Example:
        >>> validate_encoding('utf-8')
        True
        >>> validate_encoding('invalid-encoding')
        False
    """
    try:
        "test".encode(encoding)
        return True
    except LookupError:
        logger.error(f"Unsupported encoding: {encoding}")
        return False

def write_file(file_path: Path, content: str, encoding: str) -> None:
    """Write content to file with strict content preservation.
    
    Rules:
    - Write content exactly as provided
    - No content modification
    - No whitespace normalization
    - No newline manipulation
    - Creates parent directories if they don't exist
    
    Args:
        file_path: Path to file to write
        content: Content to write
        encoding: File encoding to use
        
    Raises:
        PermissionError: If file can't be written
        UnicodeError: If content can't be encoded with specified encoding
        LookupError: If encoding is not supported
        OSError: If directory creation fails
    """
    if not validate_encoding(encoding):
        raise LookupError(f"Unsupported encoding: {encoding}")
        
    logger.debug(f"Writing {len(content)} characters to file: {file_path}")
    
    try:
        # Ensure parent directory exists
        ensure_parent_directory_exists(file_path)
        
        # Validate write permissions if file exists
        if file_path.exists():
            validate_path_permissions(file_path, require_write=True)
            
        # Write the file
        with open(file_path, "w", encoding=encoding) as f:
            f.write(content)
            logger.debug(f"Successfully wrote to {file_path}")
            
    except PermissionError:
        logger.error(f"Permission denied writing to file: {file_path}")
        raise
    except UnicodeError as e:
        logger.error(f"Encoding error writing to {file_path} with {encoding}: {e}")
        raise
    except OSError as e:
        logger.error(f"Failed to write to {file_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error writing to {file_path}: {e}")
        raise

def generate_temp_filename(original_name: str) -> str:
    """Generate a unique temporary filename.
    
    Uses both UUID and timestamp to ensure uniqueness:
    - UUID for process/thread uniqueness
    - Timestamp for debugging/cleanup purposes
    
    Args:
        original_name: Original filename
        
    Returns:
        Unique temporary filename
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid4())
    return f"temp_{timestamp}_{unique_id}_{original_name}"

def validate_path_permissions(path: Path, require_write: bool = False) -> None:
    """Validate path permissions.
    
    Args:
        path: Path to validate
        require_write: Whether write permission is required
        
    Raises:
        FileNotFoundError: If path doesn't exist
        PermissionError: If required permissions are not available
    """
    if not path.exists():
        logger.error(f"Path not found: {path}")
        raise FileNotFoundError(f"Path not found: {path}")
        
    if not os.access(path, os.R_OK):
        logger.error(f"Path not readable: {path}")
        raise PermissionError(f"Path not readable: {path}")
        
    if require_write and not os.access(path, os.W_OK):
        logger.error(f"Path not writable: {path}")
        raise PermissionError(f"Path not writable: {path}")

def atomic_write(file_path: Path, content: str, encoding: str, temp_dir: Path) -> None:
    """Write content atomically using a temporary file.
    
    Rules:
    - Same content preservation rules as write_file
    - Uses temporary file with UUID for safety
    - Atomic replacement of target file
    - Creates parent directories if they don't exist
    - Handles cross-device moves
    
    Args:
        file_path: Target file path
        content: Content to write
        encoding: File encoding to use
        temp_dir: Directory for temporary files (must exist and be writable)
        
    Raises:
        FileNotFoundError: If temp_dir doesn't exist
        PermissionError: If temp_dir or target location can't be written
        UnicodeError: If content can't be encoded with specified encoding
        OSError: If directory creation or move fails
    """
    temp_filename = generate_temp_filename(file_path.name)
    temp_file = temp_dir / temp_filename
    
    logger.debug(
        f"Starting atomic write to {file_path} "
        f"using temp file: {temp_file}"
    )
    
    # Validate temp directory
    validate_path_permissions(temp_dir, require_write=True)
    
    try:
        # Ensure parent directory exists for target file
        ensure_parent_directory_exists(file_path)
        
        # If target file exists, check if we can write to it
        if file_path.exists():
            validate_path_permissions(file_path, require_write=True)
            
        # Write to temporary file
        write_file(temp_file, content, encoding)
        
        # Atomic move/replace
        logger.debug(f"Moving {temp_file} to {file_path}")
        shutil.move(str(temp_file), str(file_path))
        logger.debug(f"Successfully completed atomic write to {file_path}")
        
    except Exception as e:
        logger.error(f"Error during atomic write to {file_path}: {e}")
        # Clean up temp file if something goes wrong
        if temp_file.exists():
            try:
                temp_file.unlink()
                logger.debug(f"Cleaned up temporary file: {temp_file}")
            except Exception as cleanup_error:
                logger.warning(
                    f"Failed to clean up temporary file {temp_file}: {cleanup_error}"
                )
        raise