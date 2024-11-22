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
    """
    with open(file_path, "r", encoding=encoding) as f:
        return f.read()

def write_file(file_path: Path, content: str, encoding: str) -> None:
    """Write content to file with strict content preservation.
    
    Rules:
    - Write content exactly as provided
    - No content modification
    - No whitespace normalization
    - No newline manipulation
    """
    with open(file_path, "w", encoding=encoding) as f:
        f.write(content)

def atomic_write(file_path: Path, content: str, encoding: str, temp_dir: Path) -> None:
    """Write content atomically using a temporary file.
    
    Rules:
    - Same content preservation rules as write_file
    - Uses temporary file for safety
    - Atomic replacement of target file
    """
    temp_file = temp_dir / f"temp_{file_path.name}"
    try:
        # Write to temporary file
        write_file(temp_file, content, encoding)
        # Atomic replace
        temp_file.replace(file_path)
    except Exception as e:
        # Clean up temp file if something goes wrong
        if temp_file.exists():
            temp_file.unlink()
        raise e 