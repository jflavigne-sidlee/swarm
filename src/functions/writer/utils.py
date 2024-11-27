"""Utility functions for system-related constraints."""
import shutil
from typing import List
from pathlib import Path

def get_system_min_file_size() -> int:
    """Get minimum allowed file size based on system."""
    # Most systems have a minimum block size of 512 bytes
    return 512

def get_available_disk_space(path: Path = None) -> int:
    """Get available disk space in bytes.
    
    Args:
        path: Path to check space for. Defaults to current directory.
    
    Returns:
        Available space in bytes
    """
    if path is None:
        path = Path.cwd()
    try:
        return shutil.disk_usage(path).free
    except Exception as e:
        # Fallback to a reasonable default if we can't get disk space
        return 1024 * 1024 * 1024  # 1GB

def get_max_compression_level() -> int:
    """Get maximum compression level supported by the system."""
    # Most compression algorithms use levels 1-9
    return 9

def get_supported_extensions() -> List[str]:
    """Get list of supported file extensions."""
    return [".md", ".markdown", ".txt"] 