"""Centralized file I/O operations with strict content preservation rules."""

import logging
from pathlib import Path
import os
import shutil
from typing import Optional
from uuid import uuid4
from datetime import datetime
import errno

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
    logger.info(f"Reading file: {file_path} with encoding: {encoding}")
    try:
        with open(file_path, "r", encoding=encoding) as f:
            content = f.read()
            logger.info(f"Successfully read {len(content)} characters from {file_path}")
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
        
    logger.info(f"Writing {len(content)} characters to file: {file_path}")
    
    try:
        # Ensure parent directory exists
        ensure_parent_directory_exists(file_path)
        
        # Validate write permissions if file exists
        if file_path.exists():
            validate_path_permissions(file_path, require_write=True)
            
        # Write the file
        with open(file_path, "w", encoding=encoding) as f:
            f.write(content)
            logger.info(f"Successfully wrote to {file_path}")
            
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
        logger.error(f"No read permission for path: {path}")
        raise PermissionError(f"No read permission for path: {path}")
        
    if require_write and not os.access(path, os.W_OK):
        logger.error(f"No write permission for path: {path}")
        raise PermissionError(f"No write permission for path: {path}")

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
        FileNotFoundError: If temp_dir doesn't exist or can't create parent directory
        PermissionError: If temp_dir or target location can't be written
        LookupError: If encoding is not supported
        UnicodeError: If content can't be encoded with specified encoding
        OSError: If atomic move fails or other I/O errors occur
    """
    temp_filename = generate_temp_filename(file_path.name)
    temp_file = temp_dir / temp_filename
    
    logger.info(
        f"Starting atomic write to {file_path} "
        f"using temp file: {temp_file}"
    )
    
    try:
        # Validate temp directory
        try:
            validate_path_permissions(temp_dir, require_write=True)
        except FileNotFoundError:
            logger.error(f"Temporary directory not found: {temp_dir}")
            raise
        except PermissionError:
            logger.error(f"No write permission for temporary directory: {temp_dir}")
            raise
            
        # Validate encoding
        if not validate_encoding(encoding):
            logger.error(f"Unsupported encoding: {encoding}")
            raise LookupError(f"Unsupported encoding: {encoding}")
        
        # Ensure parent directory exists
        try:
            ensure_parent_directory_exists(file_path)
        except PermissionError:
            logger.error(f"No permission to create parent directory for: {file_path}")
            raise
        except OSError as e:
            logger.error(f"Failed to create parent directory for {file_path}: {e}")
            raise
            
        # Check target file permissions if it exists
        if file_path.exists():
            try:
                validate_path_permissions(file_path, require_write=True)
            except PermissionError:
                logger.error(f"No write permission for target file: {file_path}")
                raise
                
        # Write to temporary file
        try:
            write_file(temp_file, content, encoding)
        except UnicodeError as e:
            logger.error(f"Encoding error writing content with {encoding}: {e}")
            raise
        except PermissionError:
            logger.error(f"Permission denied writing temporary file: {temp_file}")
            raise
        except OSError as e:
            logger.error(f"Failed to write temporary file {temp_file}: {e}")
            raise
            
        # Atomic move/replace
        try:
            logger.debug(f"Moving {temp_file} to {file_path}")
            shutil.move(str(temp_file), str(file_path))
            logger.info(f"Successfully completed atomic write to {file_path}")
        except PermissionError:
            logger.error(f"Permission denied moving temp file to target: {file_path}")
            raise
        except OSError as e:
            if e.errno == errno.EXDEV:  # Cross-device link error
                # Add fallback for cross-device moves
                shutil.copy2(str(temp_file), str(file_path))
                temp_file.unlink()
            else:
                logger.error(f"Failed to move temp file to target {file_path}: {e}")
                raise
            
    except Exception as e:
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