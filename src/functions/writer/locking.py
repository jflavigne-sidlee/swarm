from datetime import datetime
from pathlib import Path
import json
import logging
from filelock import FileLock, Timeout
from typing import Optional
import random

from .config import WriterConfig
from .constants import (
    LOCK_CLEANUP_BATCH_SIZE,
    LOCK_CLEANUP_DEFAULT_AGE,
    LOCK_CLEANUP_PROBABILITY,
    LOCK_FILE_PATTERN,
    LOCK_METADATA_AGENT,
    LOCK_METADATA_FILE,
    LOCK_METADATA_SECTION,
    LOCK_METADATA_TIMESTAMP
)
from .errors import (
    ERROR_LOCK_ACQUISITION,
    ERROR_LOCK_CLEANUP,
    ERROR_LOCK_METADATA,
    ERROR_LOCK_RELEASE,
    ERROR_SECTION_NOT_FOUND,
    ERROR_UNEXPECTED_LOCK,
)
from .logs import (
    LOG_LOCK_ACQUIRED,
    LOG_LOCK_EXISTS,
    LOG_LOCK_FAILED,
    LOG_LOCK_RELEASED,
    LOG_CLEANUP_START,
    LOG_CLEANUP_COMPLETE,
    LOG_CLEANUP_ERROR,
    LOG_STALE_LOCK_REMOVED,
    LOG_INVALID_LOCK_FILE,
    LOG_LOCK_REMOVAL_FAILED,
    LOG_LOCK_AGE_CHECK_FAILED,
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
    validate_path_permissions
)

logger = logging.getLogger(__name__)

class SectionLock:
    """Context manager for handling section locks."""
    
    def __init__(
        self,
        file_path: Path,
        section_title: str,
        timeout: int = 5,
        agent_id: Optional[str] = None
    ):
        self.file_path = Path(file_path)
        self.section_title = section_title
        self.timeout = timeout
        self.agent_id = agent_id
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
        
    def is_expired(self) -> bool:
        """Check if the lock has expired based on metadata."""
        if not self.lock_file.exists():
            return False
        
        try:
            metadata = json.loads(self.lock_file.read_text())
            lock_time = datetime.fromisoformat(metadata[LOCK_METADATA_TIMESTAMP])
            return (datetime.now() - lock_time).total_seconds() > self.timeout
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(ERROR_LOCK_METADATA.format(error=e))
            return False

    def acquire(self) -> bool:
        """Attempt to acquire the lock."""
        if self.lock_file.exists():
            if self.is_expired():
                logger.debug(LOG_STALE_LOCK_REMOVED.format(
                    lock_file=self.lock_file
                ))
                self._cleanup()
            else:
                logger.debug(LOG_LOCK_EXISTS.format(section=self.section_title))
                return False
                
        try:
            self._lock.acquire(timeout=0)
            self._locked = True
            self._write_metadata()
            logger.debug(LOG_LOCK_ACQUIRED.format(section=self.section_title))
            return True
        except Timeout:
            logger.debug(LOG_LOCK_FAILED.format(section=self.section_title))
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
                logger.debug(LOG_LOCK_RELEASED.format(section=self.section_title))
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
        if self.agent_id is not None:
            metadata[LOCK_METADATA_AGENT] = self.agent_id
            
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

class LockCleanupManager:
    """Manages cleanup of stale lock files."""
    
    def __init__(self, config: WriterConfig):
        self.config = config
        self.max_age = getattr(config, 'lock_cleanup_age', LOCK_CLEANUP_DEFAULT_AGE)
        
    def cleanup_stale_locks(self, directory: Optional[Path] = None) -> int:
        """Clean up stale lock files in the specified directory."""
        directory = directory or self.config.drafts_dir
        cleaned_count = 0
        
        try:
            logger.info(LOG_CLEANUP_START.format(directory=directory))
            validate_path_permissions(directory, require_write=True)
            
            for lock_file in directory.glob(LOCK_FILE_PATTERN):
                try:
                    if self._is_stale_lock(lock_file):
                        self._remove_lock(lock_file)
                        cleaned_count += 1
                        
                    if cleaned_count >= LOCK_CLEANUP_BATCH_SIZE:
                        break
                        
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(LOG_INVALID_LOCK_FILE.format(
                        lock_file=lock_file, error=e
                    ))
                    self._remove_lock(lock_file)
                    cleaned_count += 1
                    
        except Exception as e:
            logger.error(LOG_CLEANUP_ERROR.format(error=e))
            
        logger.info(LOG_CLEANUP_COMPLETE.format(count=cleaned_count))
        return cleaned_count
        
    def _is_stale_lock(self, lock_file: Path) -> bool:
        """Check if a lock file is stale."""
        try:
            metadata = json.loads(lock_file.read_text())
            lock_time = datetime.fromisoformat(metadata[LOCK_METADATA_TIMESTAMP])
            age = (datetime.now() - lock_time).total_seconds()
            return age > self.max_age
        except Exception as e:
            logger.error(LOG_LOCK_AGE_CHECK_FAILED.format(
                lock_file=lock_file, error=e
            ))
            return True
            
    def _remove_lock(self, lock_file: Path) -> None:
        """Safely remove a lock file."""
        try:
            lock_file.unlink()
            logger.info(LOG_STALE_LOCK_REMOVED.format(lock_file=lock_file))
        except Exception as e:
            logger.error(LOG_LOCK_REMOVAL_FAILED.format(
                lock_file=lock_file, error=e
            ))

def lock_section(
    file_name: str,
    section_title: str,
    config: Optional[WriterConfig] = None,
    agent_id: Optional[str] = None
) -> bool:
    """Lock a section for exclusive access."""
    if config is None:
        config = WriterConfig()
        
    try:
        # Probabilistic cleanup to avoid overhead on every call
        if random.random() < LOCK_CLEANUP_PROBABILITY:
            try:
                LockCleanupManager(config).cleanup_stale_locks()
            except Exception as e:
                logger.warning(LOG_CLEANUP_ERROR.format(error=e))
        
        validate_filename(Path(file_name).name, config)
        
        file_path = Path(config.drafts_dir) / file_name
        try:
            validate_file(file_path, require_write=True)
        except WriterError as e:
            raise FileValidationError(str(e))
        
        if not section_exists(file_path.name, section_title, config):
            raise SectionNotFoundError(ERROR_SECTION_NOT_FOUND.format(
                section_title=section_title
            ))
            
        lock = SectionLock(file_path, section_title, config.lock_timeout, agent_id)
        acquired = lock.acquire()
        
        if not acquired:
            lock.release()
            
        return acquired
        
    except (FileValidationError, SectionNotFoundError):
        raise
    except Exception as e:
        logger.error(ERROR_UNEXPECTED_LOCK.format(error=e))
        raise FileValidationError(str(e))