from datetime import datetime
from pathlib import Path
import yaml
from typing import Dict, Optional
import os
import re

from .config import WriterConfig
from .exceptions import WriterError
from .constants import (
    MAX_FILENAME_LENGTH, FORBIDDEN_FILENAME_CHARS, RESERVED_WINDOWS_FILENAMES,
    YAML_FRONTMATTER_START, YAML_FRONTMATTER_END,
    ERROR_INVALID_FILENAME, ERROR_INVALID_METADATA_TYPE, ERROR_FILE_EXISTS,
    ERROR_PERMISSION_DENIED_PATH, ERROR_PERMISSION_DENIED_DIR, ERROR_MISSING_METADATA,
    ERROR_DIR_EXISTS, ERROR_DIR_CREATION, ERROR_YAML_SERIALIZATION,
    ERROR_FILE_WRITE, ERROR_PERMISSION_DENIED_FILE
)


def create_document(
    file_name: str, metadata: Dict[str, str], config: Optional[WriterConfig] = None
) -> Path:
    """Create a new Markdown document with YAML frontmatter metadata."""
    # Use default config if none provided
    if config is None:
        config = WriterConfig()

    # Validate inputs
    if not file_name or not is_valid_filename(file_name):
        raise WriterError(ERROR_INVALID_FILENAME)

    if not all(isinstance(value, str) for value in metadata.values()):
        raise WriterError(ERROR_INVALID_METADATA_TYPE)

    # Ensure file has .md extension
    if not file_name.endswith(".md"):
        file_name += ".md"

    # Construct full file path
    file_path = config.drafts_dir / file_name

    try:
        # Check if file exists
        if file_path.exists():
            raise WriterError(ERROR_FILE_EXISTS.format(path=file_path))

        # Validate required metadata fields
        missing_fields = [
            field for field in config.metadata_keys if field not in metadata
        ]
        if missing_fields:
            raise WriterError(
                ERROR_MISSING_METADATA.format(fields=', '.join(missing_fields))
            )

        # Create directories if needed
        if config.create_directories:
            try:
                config.drafts_dir.mkdir(parents=True, exist_ok=True)
            except FileExistsError:
                raise WriterError(ERROR_DIR_EXISTS.format(path=config.drafts_dir))
            except PermissionError:
                raise WriterError(ERROR_PERMISSION_DENIED_DIR.format(path=config.drafts_dir))
            except OSError as e:
                raise WriterError(ERROR_DIR_CREATION.format(error=str(e)))

        try:
            # Serialize YAML
            yaml_content = yaml.dump(metadata, default_flow_style=False, sort_keys=False)
            
            # Write to file
            with open(file_path, "w", encoding=config.default_encoding) as f:
                f.write(YAML_FRONTMATTER_START)
                f.write(yaml_content)
                f.write(YAML_FRONTMATTER_END)
                
            return file_path

        except yaml.YAMLError as e:
            raise WriterError(ERROR_YAML_SERIALIZATION.format(error=str(e)))
        except PermissionError:
            raise WriterError(ERROR_PERMISSION_DENIED_FILE.format(path=file_path))
        except OSError as e:
            raise WriterError(ERROR_FILE_WRITE.format(error=str(e)))

    except Exception as e:
        # Clean up if file was partially written
        if isinstance(e, WriterError):
            cleanup_partial_file(file_path)
            raise
        # Re-raise unexpected errors after cleanup
        cleanup_partial_file(file_path)
        raise WriterError(f"Unexpected error: {str(e)}")

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
        - Trailing spaces or dots
    """
    # Check for empty or too long filenames
    if not filename or len(filename) > MAX_FILENAME_LENGTH:
        return False
        
    # Check for common forbidden characters in filenames
    if any(char in filename for char in FORBIDDEN_FILENAME_CHARS):
        return False
        
    # Check for reserved Windows filenames
    if os.path.splitext(os.path.basename(filename))[0].upper() in RESERVED_WINDOWS_FILENAMES:
        return False
        
    # Check for trailing spaces or dots
    if filename.endswith((" ", ".")):
        return False
        
    return True

def cleanup_partial_file(file_path: Path) -> None:
    """Clean up partially written files in case of errors.
    
    Args:
        file_path: Path to the file to clean up
    """
    try:
        # Use os.path.exists instead of Path.exists to avoid permission errors
        if os.path.exists(str(file_path)):
            os.remove(str(file_path))
    except (OSError, PermissionError):
        pass  # Ignore cleanup errors
