from datetime import datetime
from pathlib import Path
import yaml
from typing import Dict, Optional
import os
import re
import logging

from .config import WriterConfig
from .exceptions import WriterError
from .constants import (
    MAX_FILENAME_LENGTH, FORBIDDEN_FILENAME_CHARS, RESERVED_WINDOWS_FILENAMES,
    YAML_FRONTMATTER_START, YAML_FRONTMATTER_END,
    ERROR_INVALID_FILENAME, ERROR_INVALID_METADATA_TYPE, ERROR_FILE_EXISTS,
    ERROR_PERMISSION_DENIED_PATH, ERROR_PERMISSION_DENIED_DIR, ERROR_MISSING_METADATA,
    ERROR_DIR_EXISTS, ERROR_DIR_CREATION, ERROR_YAML_SERIALIZATION,
    ERROR_FILE_WRITE, ERROR_PERMISSION_DENIED_FILE, MAX_PATH_LENGTH,
    ERROR_PATH_TOO_LONG
)

# Set up module logger
logger = logging.getLogger(__name__)

def validate_filename(file_name: str, config: WriterConfig) -> Path:
    """Validate filename and return full path."""
    if not file_name or not is_valid_filename(file_name):
        logger.warning("Invalid filename rejected: %s", file_name)
        raise WriterError(ERROR_INVALID_FILENAME)

    # Ensure .md extension
    if not file_name.endswith(".md"):
        file_name += ".md"
        logger.debug("Added .md extension: %s", file_name)

    # Check path length
    full_path = config.drafts_dir / file_name
    if len(str(full_path)) > MAX_PATH_LENGTH:
        logger.warning("Path too long: %s", full_path)
        raise WriterError(
            ERROR_PATH_TOO_LONG.format(max_length=MAX_PATH_LENGTH, path=full_path)
        )
    
    return full_path

def validate_metadata(metadata: Dict[str, str], config: WriterConfig) -> None:
    """Validate metadata types and required fields."""
    if not isinstance(metadata, dict) or not all(
        isinstance(key, str) and isinstance(value, str) 
        for key, value in metadata.items()
    ):
        logger.warning("Invalid metadata types detected in: %s", metadata)
        raise WriterError(ERROR_INVALID_METADATA_TYPE)

    missing_fields = [field for field in config.metadata_keys if field not in metadata]
    if missing_fields:
        logger.warning("Missing required metadata fields: %s", missing_fields)
        raise WriterError(ERROR_MISSING_METADATA.format(fields=', '.join(missing_fields)))

def ensure_directory_exists(dir_path: Path) -> None:
    """Create directory if it doesn't exist."""
    try:
        logger.debug("Creating directory: %s", dir_path)
        dir_path.mkdir(parents=True, exist_ok=True)
    except FileExistsError:
        logger.error("Cannot create directory (file exists): %s", dir_path)
        raise WriterError(ERROR_DIR_EXISTS.format(path=dir_path))
    except PermissionError:
        logger.error("Permission denied creating directory: %s", dir_path)
        raise WriterError(ERROR_PERMISSION_DENIED_DIR.format(path=dir_path))
    except OSError as e:
        logger.error("Directory creation error: %s - %s", dir_path, str(e))
        raise WriterError(ERROR_DIR_CREATION.format(error=str(e)))

def write_document(file_path: Path, metadata: Dict[str, str], encoding: str) -> None:
    """Write metadata and frontmatter to file."""
    try:
        logger.debug("Serializing metadata to YAML")
        yaml_content = yaml.dump(metadata, default_flow_style=False, sort_keys=False)
        
        logger.debug("Writing content to file: %s", file_path)
        with open(file_path, "w", encoding=encoding) as f:
            f.write(YAML_FRONTMATTER_START)
            f.write(yaml_content)
            f.write(YAML_FRONTMATTER_END)
            
    except yaml.YAMLError as e:
        logger.error("YAML serialization error: %s", str(e))
        raise WriterError(ERROR_YAML_SERIALIZATION.format(error=str(e)))
    except PermissionError:
        logger.error("Permission denied writing file: %s", file_path)
        raise WriterError(ERROR_PERMISSION_DENIED_FILE.format(path=file_path))
    except OSError as e:
        logger.error("File writing error: %s - %s", file_path, str(e))
        raise WriterError(ERROR_FILE_WRITE.format(error=str(e)))

def create_document(
    file_name: str, metadata: Dict[str, str], config: Optional[WriterConfig] = None
) -> Path:
    """Create a new Markdown document with YAML frontmatter metadata."""
    logger.debug("Creating document with filename: %s", file_name)
    
    # Use default config if none provided
    if config is None:
        config = WriterConfig()
        logger.debug("Using default configuration")

    # Validate inputs
    full_path = validate_filename(file_name, config)
    validate_metadata(metadata, config)

    try:
        # Check if file exists
        try:
            if os.path.exists(str(full_path)):
                logger.warning("File already exists: %s", full_path)
                raise WriterError(ERROR_FILE_EXISTS.format(path=full_path))
        except (OSError, PermissionError) as e:
            logger.error("Permission error checking path: %s - %s", full_path, str(e))
            raise WriterError(ERROR_PERMISSION_DENIED_PATH.format(path=full_path))

        # Create directories if needed
        if config.create_directories:
            ensure_directory_exists(config.drafts_dir)

        # Write document
        write_document(full_path, metadata, config.default_encoding)
        logger.info("Successfully created document: %s", full_path)
        return full_path

    except Exception as e:
        # Clean up if file was partially written
        logger.debug("Exception occurred, cleaning up partial file: %s", full_path)
        cleanup_partial_file(full_path)
        
        if isinstance(e, WriterError):
            raise
            
        # Log and re-raise unexpected errors with original type
        logger.error("Unexpected error: %s (%s)", str(e), type(e).__name__)
        raise

def is_valid_filename(filename: str) -> bool:
    """Check if the filename is valid based on OS restrictions.
    
    Args:
        filename: The filename to validate
        
    Returns:
        bool: True if filename is valid, False otherwise
        
    Note:
        Validates against:
        - Empty or too long filenames (>255 chars)
        - Forbidden characters (<>:"/\\|?*\0)
        - Reserved Windows filenames (CON, PRN, etc.)
        - Special directory names (., ..)
        - Trailing spaces or dots
    """
    # Check for empty or too long filenames
    if not filename or len(filename) > MAX_FILENAME_LENGTH:
        return False
    
    # Prevent special directory names
    if filename in {".", "..", "./", "../"}:
        return False
        
    # Check for common forbidden characters in filenames
    if any(char in filename for char in FORBIDDEN_FILENAME_CHARS):
        return False
        
    # Check for reserved Windows filenames
    base_name = os.path.splitext(os.path.basename(filename))[0].upper()
    if base_name in RESERVED_WINDOWS_FILENAMES:
        return False
        
    # Check for trailing spaces or dots
    if filename.endswith((" ", ".")):
        return False
        
    return True

def cleanup_partial_file(file_path: Path) -> None:
    """Clean up partially written files in case of errors."""
    try:
        if os.path.exists(str(file_path)):
            logger.debug("Removing partial file: %s", file_path)
            os.remove(str(file_path))
    except (OSError, PermissionError) as e:
        logger.warning("Failed to clean up partial file: %s - %s", file_path, str(e))
