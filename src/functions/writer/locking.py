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
        self._lock = FileLock(str(self.lock_file), timeout=timeout)
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
        try:
            self._lock.acquire(timeout=0.1)  # Short timeout for quick failure
            self._locked = True
            self._write_metadata()
            return True
        except Timeout:
            return False
        except Exception as e:
            logger.error(f"Error acquiring lock: {e}")
            return False
            
    def release(self) -> None:
        """Release the lock if held."""
        if self._locked:
            try:
                self._lock.release()
                self._cleanup()
            finally:
                self._locked = False
                
    def _write_metadata(self) -> None:
        """Write lock metadata to the lock file."""
        now = datetime.now()
        metadata: Dict[str, str] = {
            "section": self.section_title,
            "timestamp": now.isoformat(),
            "expires": (now + timedelta(seconds=self.timeout)).isoformat(),
            "file": str(self.file_path)
        }
        
        try:
            self.lock_file.write_text(json.dumps(metadata, indent=2))
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
        WriterError: If file validation fails
        SectionNotFoundError: If section doesn't exist
        FileValidationError: If file doesn't exist or isn't writable
    """
    if config is None:
        config = WriterConfig()
        
    try:
        # First validate the base filename (without path)
        validate_filename(Path(file_name).name, config)
        
        # Then construct and validate the full path
        file_path = Path(config.drafts_dir) / file_name
        validate_file(file_path, require_write=True)
        
        # Check if section exists using the file path
        if not section_exists(file_path.name, section_title, config):
            raise SectionNotFoundError(f"Section '{section_title}' not found in {file_name}")
            
        # Create and acquire lock
        lock = SectionLock(file_path, section_title, config.lock_timeout)
        return lock.acquire()
        
    except (FileValidationError, SectionNotFoundError) as e:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in lock_section: {e}")
        raise WriterError(str(e))