from datetime import datetime
from pathlib import Path
import yaml
from typing import Dict, Optional
import os
import re

from .config import WriterConfig
from .exceptions import WriterError


def create_document(
    file_name: str, metadata: Dict[str, str], config: Optional[WriterConfig] = None
) -> Path:
    """Create a new Markdown document with YAML frontmatter metadata."""
    # Use default config if none provided
    if config is None:
        config = WriterConfig()

    # Validate filename
    if not file_name or not is_valid_filename(file_name):
        raise WriterError("Invalid filename")

    # Validate metadata types
    if not all(isinstance(value, str) for value in metadata.values()):
        raise WriterError("Invalid metadata type")

    # Ensure file has .md extension
    if not file_name.endswith(".md"):
        file_name += ".md"

    # Construct full file path in drafts directory
    file_path = config.drafts_dir / file_name

    # Check if file already exists (handle permission errors)
    try:
        if file_path.exists():
            raise WriterError(f"File already exists: {file_path}")
    except PermissionError:
        raise WriterError(f"Permission denied accessing path: {file_path}")

    # Validate required metadata fields
    missing_fields = [
        field for field in config.metadata_keys if field not in metadata
    ]
    if missing_fields:
        raise WriterError(
            f"Missing required metadata fields: {', '.join(missing_fields)}"
        )

    # Create drafts directory if it doesn't exist
    if config.create_directories:
        try:
            config.drafts_dir.mkdir(parents=True, exist_ok=True)
        except FileExistsError:
            raise WriterError(
                f"Cannot create directory: {config.drafts_dir} (file exists)"
            )
        except PermissionError:
            raise WriterError(
                f"Permission denied creating directory: {config.drafts_dir}"
            )
        except OSError as e:
            raise WriterError(f"Directory creation error: {str(e)}")

    # Write file with YAML frontmatter
    try:
        # First, try to serialize the YAML to catch any serialization errors
        try:
            yaml_content = yaml.dump(metadata, default_flow_style=False, sort_keys=False)
        except yaml.YAMLError as e:
            raise WriterError(f"YAML serialization error: {str(e)}")

        # Then, try to write the file
        try:
            with open(file_path, "w", encoding=config.default_encoding) as f:
                f.write("---\n")
                f.write(yaml_content)
                f.write("---\n\n")
        except PermissionError:
            raise WriterError(f"Permission denied writing file: {file_path}")
        except OSError as e:
            raise WriterError(f"File writing error: {str(e)}")

        return file_path

    except Exception as e:
        # Clean up if file was partially written
        if file_path.exists():
            try:
                file_path.unlink()
            except OSError:
                pass  # Ignore cleanup errors
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
        - Trailing spaces or dots
    """
    # Check for empty or too long filenames
    if not filename or len(filename) > 255:
        return False
        
    # Check for common forbidden characters in filenames
    forbidden_chars = '<>:"/\\|?*\0'
    if any(char in filename for char in forbidden_chars):
        return False
        
    # Check for reserved Windows filenames
    reserved_names = {
        "CON", "PRN", "AUX", "NUL",  # Device names
        "COM1", "COM2", "COM3", "COM4",  # COM ports
        "LPT1", "LPT2", "LPT3", "LPT4"  # Printer ports
    }
    
    # Get base name without extension and convert to uppercase for comparison
    base_name = os.path.splitext(os.path.basename(filename))[0].upper()
    if base_name in reserved_names:
        return False
        
    # Check for trailing spaces or dots
    if filename.endswith((" ", ".")):
        return False
        
    return True
