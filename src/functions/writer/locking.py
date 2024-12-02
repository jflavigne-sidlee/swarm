from datetime import datetime, timedelta
from pathlib import Path
import json
import logging
from filelock import FileLock, Timeout
from typing import Optional, Dict

from .config import WriterConfig
from .exceptions import (
    WriterError,
    SectionNotFoundError,
    LockAcquisitionError,
    FileValidationError
)
from .file_operations import (
    validate_file,
    validate_filename,
    section_exists,
)

logger = logging.getLogger(__name__)

class SectionLock:
    """Context manager for handling section locks."""
    
    def __init__(
        self,
        file_path: Path,
        section_title: str,
        timeout: int = 5
    ):
        self.file_path = Path(file_path)
        self.section_title = section_title
        self.timeout = timeout
        self.lock_file = self.file_path.parent / f".{section_title}.lock"
        # Create a new FileLock without timeout
        self._lock = FileLock(str(self.lock_file))
        self._locked = False
        
    def __enter__(self) -> 'SectionLock':
        """Context manager entry.
        
        Returns:
            self: The lock instance
            
        Raises:
            LockAcquisitionError: If lock cannot be acquired
        """
        if not self.acquire():
            raise LockAcquisitionError(f"Failed to acquire lock for section: {self.section_title}")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.release()
        
    def acquire(self) -> bool:
        """Attempt to acquire the lock."""
        if self.lock_file.exists():
            logger.debug(f"Lock file exists for section: {self.section_title}")
            return False
            
        try:
            # Try to acquire with zero timeout
            self._lock.acquire(timeout=0)
            self._locked = True
            self._write_metadata()
            logger.debug(f"Lock acquired for section: {self.section_title}")
            return True
        except Timeout:
            logger.debug(f"Lock acquisition failed (timeout) for section: {self.section_title}")
            return False
        except Exception as e:
            logger.error(f"Error acquiring lock: {e}")
            if self._locked:
                self.release()
            return False
            
    def release(self) -> None:
        """Release the lock if held."""
        if self._locked:
            try:
                self._lock.release()
                self._cleanup()
                logger.debug(f"Lock released for section: {self.section_title}")
            except Exception as e:
                logger.error(f"Error releasing lock: {e}")
            finally:
                self._locked = False
                
    def _write_metadata(self) -> None:
        """Write lock metadata to the lock file."""
        metadata = {
            "section": self.section_title,
            "timestamp": datetime.now().isoformat(),
            "file": str(self.file_path)
        }
        try:
            self.lock_file.write_text(json.dumps(metadata))
        except Exception as e:
            logger.error(f"Failed to write lock metadata: {e}")
            self.release()
            raise LockAcquisitionError(f"Failed to write lock metadata: {e}")
            
    def _cleanup(self) -> None:
        """Remove lock file."""
        try:
            if self.lock_file.exists():
                self.lock_file.unlink()
        except Exception as e:
            logger.error(f"Failed to cleanup lock file: {e}")
            
    @property
    def is_locked(self) -> bool:
        """Check if lock is currently held."""
        return self._locked

def lock_section(
    file_name: str,
    section_title: str,
    config: Optional[WriterConfig] = None
) -> bool:
    """
    Lock a section for exclusive access.
    
    Args:
        file_name: Name of the markdown file (relative to drafts_dir)
        section_title: Title of the section to lock
        config: Optional configuration
        
    Returns:
        bool: True if lock was acquired, False if section is already locked
        
    Raises:
        FileValidationError: If file doesn't exist or isn't writable
        SectionNotFoundError: If section doesn't exist
        WriterError: For other unexpected errors
    """
    if config is None:
        config = WriterConfig()
        
    try:
        # First validate the base filename (without path)
        validate_filename(Path(file_name).name, config)
        
        # Then construct and validate the full path
        file_path = Path(config.drafts_dir) / file_name
        try:
            validate_file(file_path, require_write=True)
        except WriterError as e:
            raise FileValidationError(str(e))
        
        # Check if section exists using the file path
        if not section_exists(file_path.name, section_title, config):
            raise SectionNotFoundError(f"Section '{section_title}' not found in {file_name}")
            
        # Create lock and attempt to acquire it
        lock = SectionLock(file_path, section_title, config.lock_timeout)
        acquired = lock.acquire()
        
        # Important: Don't release the lock if acquired successfully
        if not acquired:
            lock.release()
            
        return acquired
        
    except (FileValidationError, SectionNotFoundError):
        raise
    except Exception as e:
        logger.error(f"Unexpected error in lock_section: {e}")
        raise FileValidationError(str(e))