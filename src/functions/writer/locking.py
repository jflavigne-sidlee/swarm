from datetime import datetime, timedelta
from pathlib import Path
import json
import logging
from filelock import FileLock, Timeout
from typing import Optional

from .config import WriterConfig
from .exceptions import (
    WriterError,
    SectionNotFoundError,
    LockAcquisitionError,
    FileValidationError
)
from .file_operations import validate_filename, section_exists
from .constants import (
    DEFAULT_LOCK_TIMEOUT,
    LOCK_FILE_SUFFIX,
    LOCK_METADATA_FORMAT
)

logger = logging.getLogger(__name__)

class SectionLock:
    """Context manager for handling section locks."""
    
    def __init__(
        self,
        file_path: Path,
        section_title: str,
        timeout: int = DEFAULT_LOCK_TIMEOUT
    ):
        self.file_path = file_path
        self.section_title = section_title
        self.timeout = timeout
        self.lock_file = Path(
            str(file_path) + f".{section_title}" + LOCK_FILE_SUFFIX
        )
        self.file_lock = FileLock(str(self.lock_file), timeout=timeout)
        
    def __enter__(self):
        try:
            self.file_lock.acquire()
            self._write_lock_metadata()
            return self
        except Timeout:
            raise LockAcquisitionError(
                f"Failed to acquire lock for section '{self.section_title}'"
            )
            
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.file_lock.release()
            self._cleanup_lock_files()
        except Exception as e:
            logger.error(f"Error releasing lock: {str(e)}")
            
    def _write_lock_metadata(self):
        """Write lock metadata to the lock file."""
        metadata = {
            "section": self.section_title,
            "timestamp": datetime.now().isoformat(),
            "expires": (
                datetime.now() + timedelta(seconds=self.timeout)
            ).isoformat()
        }
        self.lock_file.write_text(json.dumps(metadata))
        
    def _cleanup_lock_files(self):
        """Remove lock files after release."""
        try:
            self.lock_file.unlink(missing_ok=True)
        except Exception as e:
            logger.error(f"Failed to cleanup lock files: {str(e)}")

def lock_section(
    file_name: str,
    section_title: str,
    config: Optional[WriterConfig] = None
) -> bool:
    """Lock a section for exclusive access.
    
    Args:
        file_name: Name of the Markdown file
        section_title: Title of the section to lock
        config: Optional configuration object
        
    Returns:
        bool: True if lock was acquired, False if section is already locked
        
    Raises:
        WriterError: If file validation fails
        SectionNotFoundError: If the specified section doesn't exist
        LockAcquisitionError: If lock cannot be acquired
    """
    if config is None:
        config = WriterConfig()
        
    try:
        # Validate filename and get full path
        file_path = validate_filename(file_name, config)
        
        # Check if section exists
        if not section_exists(file_name, section_title, config):
            raise SectionNotFoundError(section_title)
            
        # Attempt to acquire lock
        try:
            lock = SectionLock(file_path, section_title, config.lock_timeout)
            lock.__enter__()
            return True
        except LockAcquisitionError:
            return False
            
    except FileValidationError as e:
        logger.error(f"File validation error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in lock_section: {str(e)}")
        raise WriterError(str(e)) 