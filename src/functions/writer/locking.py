"""Module for managing section-level locking in markdown documents.

Provides thread-safe locking mechanisms for concurrent access to document sections,
with support for automatic cleanup of stale locks, configurable timeouts, and
agent identification.

Classes:
    SectionLock: Context manager for exclusive section locks
    LockCleanupManager: Manager for cleaning up stale locks
"""

from datetime import datetime
from pathlib import Path
import json
import logging
from filelock import FileLock, Timeout
from typing import Optional, Union
import random

from .config import WriterConfig
from .constants import (
    DEFAULT_ACQUIRE_TIMEOUT,
    DEFAULT_LOCK_TIMEOUT,
    LOCK_CLEANUP_BATCH_SIZE,
    LOCK_CLEANUP_DEFAULT_AGE,
    LOCK_CLEANUP_PROBABILITY,
    LOCK_FILE_PATTERN,
    LOCK_FILE_PREFIX,
    LOCK_FILE_SUFFIX,
    LOCK_METADATA_AGENT,
    LOCK_METADATA_FILE,
    LOCK_METADATA_SECTION,
    LOCK_METADATA_TIMESTAMP,
    MIN_ACQUIRE_TIMEOUT,
    MAX_ACQUIRE_TIMEOUT
)
from .errors import (
    ERROR_INVALID_BATCH_SIZE,
    ERROR_INVALID_CLEANUP_AGE,
    ERROR_INVALID_PROBABILITY,
    ERROR_INVALID_TIMEOUT,
    ERROR_LOCK_ACQUISITION,
    ERROR_LOCK_CLEANUP,
    ERROR_LOCK_METADATA,
    ERROR_LOCK_RELEASE,
    ERROR_SECTION_NOT_FOUND,
    ERROR_UNEXPECTED_LOCK,
    ERROR_INVALID_ACQUIRE_TIMEOUT
)
from .logs import (
    LOG_CLEANUP_COMPLETE,
    LOG_CLEANUP_ERROR,
    LOG_CLEANUP_START,
    LOG_CONFIG_ERROR,
    LOG_CONFIG_VALIDATED,
    LOG_CONFIG_VALIDATION,
    LOG_INVALID_LOCK_FILE,
    LOG_LOCK_ACQUIRED,
    LOG_LOCK_AGE_CHECK_FAILED,
    LOG_LOCK_EXISTS,
    LOG_LOCK_FAILED,
    LOG_LOCK_RELEASED,
    LOG_LOCK_REMOVAL_FAILED,
    LOG_STALE_LOCK_REMOVED,
)
from .exceptions import (
    WriterError,
    SectionNotFoundError,
    LockAcquisitionError,
    FileValidationError
)
from .file_operations import (
    validate_file,
    section_exists,
    get_config,
)

from .file_io import validate_file_access, resolve_path_with_config

logger = logging.getLogger(__name__)

class SectionLock:
    """Context manager for handling exclusive section locks.
    
    Provides thread-safe locking with automatic expiration and cleanup.
    Can be used as a context manager or with explicit acquire/release calls.
    
    Attributes:
        file_path (Path): Document path
        section_title (str): Section to lock
        timeout (int): Lock expiry timeout in seconds
        agent_id (Optional[str]): Agent identifier
        acquire_timeout (float): Maximum wait time for acquisition
        is_locked (bool): Current lock status
        
    Example:
        >>> with SectionLock("doc.md", "Introduction") as lock:
        ...     # Modify section content
        ...     pass  # Lock automatically released
    """
    
    def __init__(
        self,
        file_path: Path,
        section_title: str,
        timeout: int = DEFAULT_LOCK_TIMEOUT,
        agent_id: Optional[str] = None,
        acquire_timeout: float = DEFAULT_ACQUIRE_TIMEOUT
    ):
        """Initialize a section lock.
        
        Args:
            file_path: Document path
            section_title: Section to lock
            timeout: Lock expiry timeout in seconds
            agent_id: Optional agent identifier
            acquire_timeout: Maximum acquisition wait time in seconds
            
        Raises:
            ValueError: If acquire_timeout is outside allowed range
        """
        if not MIN_ACQUIRE_TIMEOUT <= acquire_timeout <= MAX_ACQUIRE_TIMEOUT:
            raise ValueError(ERROR_INVALID_ACQUIRE_TIMEOUT.format(
                min_timeout=MIN_ACQUIRE_TIMEOUT,
                max_timeout=MAX_ACQUIRE_TIMEOUT
            ))
            
        self.file_path = Path(file_path)
        self.section_title = section_title
        self.timeout = timeout
        self.agent_id = agent_id
        self.acquire_timeout = acquire_timeout
        self.lock_file = self.file_path.parent / f"{LOCK_FILE_PREFIX}{section_title}{LOCK_FILE_SUFFIX}"
        self._lock = FileLock(str(self.lock_file))
        self._locked = False
        
    def __enter__(self) -> 'SectionLock':
        """Enter the context manager.
        
        Returns:
            self: The lock instance
            
        Raises:
            LockAcquisitionError: If the lock cannot be acquired
        """
        if not self.acquire():
            raise LockAcquisitionError(ERROR_LOCK_ACQUISITION.format(section=self.section_title))
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context manager and release the lock.
        
        Args:
            exc_type: Type of exception that occurred, if any
            exc_val: Exception instance that occurred, if any
            exc_tb: Exception traceback, if any
            
        Note:
            Exceptions are not suppressed and will propagate to the caller
        """
        self.release()
        return False  # Don't suppress exceptions
        
    def is_expired(self) -> bool:
        """Check if the lock has expired.
        
        Returns:
            bool: True if lock exists and has exceeded timeout
        """
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
        """Attempt to acquire the lock.
        
        Waits up to acquire_timeout seconds for lock acquisition.
        Cleans up expired locks if encountered.
        
        Returns:
            bool: True if acquired, False if timeout or valid lock exists
        """
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
            self._lock.acquire(timeout=self.acquire_timeout)
            self._locked = True
            self._write_metadata()
            logger.debug(LOG_LOCK_ACQUIRED.format(section=self.section_title))
            return True
        except Timeout:
            logger.debug(LOG_LOCK_FAILED.format(
                section=self.section_title,
                timeout=self.acquire_timeout
            ))
            return False
        except Exception as e:
            logger.error(ERROR_LOCK_ACQUISITION.format(section=self.section_title))
            if self._locked:
                self.release()
            return False
            
    def release(self) -> None:
        """Release the lock if currently held.
        
        Removes the lock file and updates internal state.
        Safe to call multiple times.
        """
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
    """Manager for cleaning up stale lock files."""
    
    def __init__(self, config: WriterConfig):
        """Initialize the cleanup manager."""
        self.config = LockConfig(config)
        
    def maybe_cleanup(self) -> None:
        """Perform probabilistic cleanup of stale locks."""
        if random.random() < self.config.cleanup_probability:
            try:
                self.cleanup_stale_locks()
            except Exception as e:
                logger.warning(LOG_CLEANUP_ERROR.format(error=e))
    
    def cleanup_stale_locks(self, directory: Optional[Path] = None) -> int:
        """Clean up stale lock files."""
        directory = directory or self.config.drafts_dir
        cleaned_count = 0
        
        try:
            logger.info(LOG_CLEANUP_START.format(directory=directory))
            validate_file_access(directory, require_write=True, check_exists=True)
            
            for lock_file in directory.glob(LOCK_FILE_PATTERN):
                try:
                    if self._is_stale_lock(lock_file):
                        self._remove_lock(lock_file)
                        cleaned_count += 1
                        
                    if cleaned_count >= self.config.cleanup_batch_size:
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
            return age > self.config.cleanup_age
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
    file_path: Union[Path, str],
    section_title: str,
    config: Optional[WriterConfig] = None,
    agent_id: Optional[str] = None,
    acquire_timeout: Optional[float] = None
) -> bool:
    """Acquire an exclusive lock on a document section."""
    config = get_config(config)
        
    # Use config value if not explicitly provided
    if acquire_timeout is None:
        acquire_timeout = getattr(config, 'acquire_timeout', DEFAULT_ACQUIRE_TIMEOUT)
        
    try:
        LockCleanupManager(config).maybe_cleanup()
        
        # Resolve path early using the utility function
        resolved_path = resolve_path_with_config(file_path, config.drafts_dir)
        
        try:
            # Pass resolved Path object instead of string
            validate_file(resolved_path, require_write=True)
        except WriterError as e:
            raise FileValidationError(str(e))
        
        # Pass full Path object instead of just the name
        if not section_exists(resolved_path, section_title, config):
            raise SectionNotFoundError(ERROR_SECTION_NOT_FOUND.format(
                section_title=section_title
            ))
            
        lock = SectionLock(
            resolved_path,  # Pass resolved Path
            section_title,
            config.lock_timeout,
            agent_id,
            acquire_timeout
        )
        return lock.acquire()
        
    except (FileValidationError, SectionNotFoundError):
        raise
    except Exception as e:
        logger.error(ERROR_UNEXPECTED_LOCK.format(error=e))
        raise FileValidationError(str(e))

class LockConfig:
    """Helper class for managing lock-related configuration."""
    
    def __init__(self, config: WriterConfig):
        """Initialize lock configuration."""
        logger.debug(LOG_CONFIG_VALIDATION)
        try:
            self.lock_timeout = self._get_validated_timeout(config)
            self.acquire_timeout = self._get_validated_acquire_timeout(config)
            self.cleanup_age = self._get_validated_cleanup_age(config)
            self.cleanup_batch_size = self._get_validated_batch_size(config)
            self.cleanup_probability = self._get_validated_probability(config)
            self.drafts_dir = config.drafts_dir
            logger.debug(LOG_CONFIG_VALIDATED)
        except ValueError as e:
            logger.error(LOG_CONFIG_ERROR.format(param="lock configuration", error=str(e)))
            raise
        
    def _get_validated_timeout(self, config: WriterConfig) -> int:
        """Get and validate lock timeout."""
        timeout = getattr(config, 'lock_timeout', DEFAULT_LOCK_TIMEOUT)
        if timeout <= 0:
            raise ValueError(ERROR_INVALID_TIMEOUT.format(
                min_timeout=MIN_ACQUIRE_TIMEOUT,
                max_timeout=MAX_ACQUIRE_TIMEOUT
            ))
        return timeout
        
    def _get_validated_acquire_timeout(self, config: WriterConfig) -> float:
        """Get and validate acquisition timeout."""
        timeout = getattr(config, 'acquire_timeout', DEFAULT_ACQUIRE_TIMEOUT)
        if not MIN_ACQUIRE_TIMEOUT <= timeout <= MAX_ACQUIRE_TIMEOUT:
            raise ValueError(ERROR_INVALID_TIMEOUT.format(
                min_timeout=MIN_ACQUIRE_TIMEOUT,
                max_timeout=MAX_ACQUIRE_TIMEOUT
            ))
        return timeout
        
    def _get_validated_cleanup_age(self, config: WriterConfig) -> int:
        """Get and validate cleanup age."""
        age = getattr(config, 'lock_cleanup_age', LOCK_CLEANUP_DEFAULT_AGE)
        if age <= 0:
            raise ValueError(ERROR_INVALID_CLEANUP_AGE)
        return age
        
    def _get_validated_batch_size(self, config: WriterConfig) -> int:
        """Get and validate cleanup batch size."""
        size = getattr(config, 'lock_cleanup_batch_size', LOCK_CLEANUP_BATCH_SIZE)
        if size <= 0:
            raise ValueError(ERROR_INVALID_BATCH_SIZE)
        return size
        
    def _get_validated_probability(self, config: WriterConfig) -> float:
        """Get and validate cleanup probability."""
        prob = getattr(config, 'lock_cleanup_probability', LOCK_CLEANUP_PROBABILITY)
        if not 0 <= prob <= 1:
            raise ValueError(ERROR_INVALID_PROBABILITY)
        return prob