"""Centralized file I/O operations with strict content preservation rules."""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

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

def write_file(file_path: Path, content: str, encoding: str) -> None:
    """Write content to file with strict content preservation.
    
    Rules:
    - Write content exactly as provided
    - No content modification
    - No whitespace normalization
    - No newline manipulation
    
    Raises:
        PermissionError: If file can't be written
        UnicodeError: If content can't be encoded with specified encoding
    """
    logger.debug(f"Writing {len(content)} characters to file: {file_path}")
    try:
        with open(file_path, "w", encoding=encoding) as f:
            f.write(content)
            logger.debug(f"Successfully wrote to {file_path}")
    except PermissionError:
        logger.error(f"Permission denied writing to file: {file_path}")
        raise
    except UnicodeError as e:
        logger.error(f"Encoding error writing to {file_path} with {encoding}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error writing to {file_path}: {e}")
        raise

def atomic_write(file_path: Path, content: str, encoding: str, temp_dir: Path) -> None:
    """Write content atomically using a temporary file.
    
    Rules:
    - Same content preservation rules as write_file
    - Uses temporary file for safety
    - Atomic replacement of target file
    
    Raises:
        FileNotFoundError: If temp_dir doesn't exist
        PermissionError: If temp_dir or target location can't be written
        UnicodeError: If content can't be encoded with specified encoding
    """
    temp_file = temp_dir / f"temp_{file_path.name}"
    logger.debug(f"Starting atomic write to {file_path} using temp file: {temp_file}")
    
    try:
        # Verify temp directory exists
        if not temp_dir.exists():
            logger.error(f"Temporary directory not found: {temp_dir}")
            raise FileNotFoundError(f"Temporary directory not found: {temp_dir}")
            
        # Write to temporary file
        write_file(temp_file, content, encoding)
        
        # Atomic replace
        logger.debug(f"Replacing {file_path} with {temp_file}")
        temp_file.replace(file_path)
        logger.debug(f"Successfully completed atomic write to {file_path}")
        
    except Exception as e:
        logger.error(f"Error during atomic write to {file_path}: {e}")
        # Clean up temp file if something goes wrong
        if temp_file.exists():
            try:
                temp_file.unlink()
                logger.debug(f"Cleaned up temporary file: {temp_file}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up temporary file {temp_file}: {cleanup_error}")
        raise