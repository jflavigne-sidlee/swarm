from datetime import datetime
from pathlib import Path
import json
import logging
from filelock import FileLock, Timeout
from typing import Optional

from .config import WriterConfig
from .constants import (
    ERROR_LOCK_ACQUISITION,
    ERROR_LOCK_METADATA,
    ERROR_LOCK_CLEANUP,
    ERROR_LOCK_RELEASE,
    ERROR_UNEXPECTED_LOCK,
    DEBUG_LOCK_EXISTS,
    DEBUG_LOCK_ACQUIRED,
    DEBUG_LOCK_FAILED,
    DEBUG_LOCK_RELEASED,
    LOCK_METADATA_SECTION,
    LOCK_METADATA_TIMESTAMP,
    LOCK_METADATA_FILE
)
from .errors import (
    ERROR_SECTION_NOT_FOUND,
)
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
        self._lock = FileLock(str(self.lock_file))
        self._locked = False
        
    def __enter__(self):
        """Enter the context manager."""
        if not self.acquire():
            raise LockAcquisitionError(ERROR_LOCK_ACQUISITION.format(section=self.section_title))
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""
        self.release()
        # Don't suppress exceptions
        return False
        
    def acquire(self) -> bool:
        """Attempt to acquire the lock."""
        if self.lock_file.exists():
            logger.debug(DEBUG_LOCK_EXISTS.format(section=self.section_title))
            return False
            
        try:
            self._lock.acquire(timeout=0)
            self._locked = True
            self._write_metadata()
            logger.debug(DEBUG_LOCK_ACQUIRED.format(section=self.section_title))
            return True
        except Timeout:
            logger.debug(DEBUG_LOCK_FAILED.format(section=self.section_title))
            return False
        except Exception as e:
            logger.error(ERROR_LOCK_ACQUISITION.format(section=self.section_title))
            if self._locked:
                self.release()
            return False
            
    def release(self) -> None:
        """Release the lock if held."""
        if self._locked:
            try:
                self._lock.release()
                self._cleanup()
                logger.debug(DEBUG_LOCK_RELEASED.format(section=self.section_title))
            except Exception as e:
                logger.error(ERROR_LOCK_RELEASE.format(error=e))
            finally:
                self._locked = False
                
    def _write_metadata(self) -> None:
        """Write lock metadata to the lock file."""
        metadata = {
            LOCK_METADATA_SECTION: self.section_title,
            LOCK_METADATA_TIMESTAMP: datetime.now().isoformat(),
            LOCK_METADATA_FILE: str(self.file_path)
        }
        try:
            self.lock_file.write_text(json.dumps(metadata))
        except Exception as e:
            logger.error(ERROR_LOCK_METADATA.format(error=e))
            self.release()
            raise LockAcquisitionError(ERROR_LOCK_METADATA.format(error=e))
            
    def _cleanup(self) -> None:
        """Remove lock file."""
        try:
            if self.lock_file.exists():
                self.lock_file.unlink()
        except Exception as e:
            logger.error(ERROR_LOCK_CLEANUP.format(error=e))
            
    @property
    def is_locked(self) -> bool:
        """Check if lock is currently held."""
        return self._locked

def lock_section(
    file_name: str,
    section_title: str,
    config: Optional[WriterConfig] = None
) -> bool:
    """Lock a section for exclusive access."""
    if config is None:
        config = WriterConfig()
        
    try:
        validate_filename(Path(file_name).name, config)
        
        file_path = Path(config.drafts_dir) / file_name
        try:
            validate_file(file_path, require_write=True)
        except WriterError as e:
            raise FileValidationError(str(e))
        
        if not section_exists(file_path.name, section_title, config):
            raise SectionNotFoundError(ERROR_SECTION_NOT_FOUND.format(section_title=section_title))
            
        lock = SectionLock(file_path, section_title, config.lock_timeout)
        acquired = lock.acquire()
        
        if not acquired:
            lock.release()
            
        return acquired
        
    except (FileValidationError, SectionNotFoundError):
        raise
    except Exception as e:
        logger.error(ERROR_UNEXPECTED_LOCK.format(error=e))
        raise FileValidationError(str(e))