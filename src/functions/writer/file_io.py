"""Centralized file I/O operations with strict content preservation rules.

This module requires:
- Python 3.7+ for Path objects
- shutil.move with atomic operations support
- os.access for permission checks

System requirements:
- File system with atomic rename support
- Permission handling compatible with os.access
"""

import logging
from pathlib import Path
import os
import shutil
from typing import Optional
from uuid import uuid4
from datetime import datetime
import errno
import sys
from .exceptions import FilePermissionError
from .errors import (
    ERROR_ATOMIC_MOVE_UNSUPPORTED,
    ERROR_DIR_CREATION,
    ERROR_ENVIRONMENT_CHECK_FAILED,
    ERROR_FILE_WRITE,
    ERROR_PATH_NO_READ,
    ERROR_PATH_NO_WRITE,
    ERROR_PATH_NOT_EXIST,
    ERROR_PERMISSION_CHECK_UNSUPPORTED,
    ERROR_PERMISSION_DENIED_DIR,
    ERROR_PERMISSION_DENIED_PATH,
    ERROR_PYTHON_VERSION,
    ERROR_UNEXPECTED,
    ERROR_UNSUPPORTED_ENCODING,
    
)
from .logs import (
    LOG_ATOMIC_WRITE_START,
    LOG_ATOMIC_WRITE_SUCCESS,
    LOG_CLEANUP_FAILED,
    LOG_ENCODING_ERROR,
    LOG_ENCODING_WRITE_ERROR,
    LOG_MOVE_FAILED,
    LOG_MOVE_PERMISSION_DENIED,
    LOG_MOVING_FILE,
    LOG_NO_READ_PERMISSION,
    LOG_NO_TEMP_DIR_PERMISSION,
    LOG_NO_WRITE_PERMISSION,
    LOG_PARENT_DIR_ERROR,
    LOG_PARENT_DIR_PERMISSION,
    LOG_PATH_NOT_FOUND,
    LOG_PERMISSION_DENIED_TEMP,
    LOG_READ_SUCCESS,
    LOG_READING_FILE,
    LOG_TEMP_CLEANUP,
    LOG_TEMP_DIR_NOT_FOUND,
    LOG_TEMP_WRITE_FAILED,
    LOG_WRITE_SUCCESS,
    LOG_WRITING_FILE,
    PATH_CREATION_MSG,
)

# Initialize logger
logger = logging.getLogger(__name__)

# Verify Python version for Path support
if sys.version_info < (3, 7):
    raise RuntimeError(ERROR_PYTHON_VERSION)


# Verify shutil atomic move support
def _check_atomic_move_support() -> None:
    """Verify atomic move operations are supported."""
    try:
        # Create test paths
        test_dir = Path("test_atomic")
        test_dir.mkdir(exist_ok=True)
        source = test_dir / "source.txt"
        target = test_dir / "target.txt"

        # Test atomic move
        source.write_text("test")
        shutil.move(str(source), str(target))

        # Cleanup
        target.unlink()
        test_dir.rmdir()
    except Exception as e:
        raise RuntimeError(ERROR_ATOMIC_MOVE_UNSUPPORTED.format(error=str(e))) from e


# Verify permission checking support
def _check_permission_support() -> None:
    """Verify permission checks are supported."""
    try:
        test_file = Path("test_perms.txt")
        test_file.touch()
        os.access(test_file, os.R_OK)
        test_file.unlink()
    except Exception as e:
        raise RuntimeError(
            ERROR_PERMISSION_CHECK_UNSUPPORTED.format(error=str(e))
        ) from e


# Run dependency checks
try:
    _check_atomic_move_support()
    _check_permission_support()
except Exception as e:
    logger.critical(ERROR_ENVIRONMENT_CHECK_FAILED.format(error=str(e)))
    raise


def ensure_directory_exists(directory: Path) -> None:
    """Ensure a directory exists, creating it if necessary.

    Args:
        directory: Directory path to ensure exists

    Raises:
        PermissionError: If directory can't be created due to permissions
        OSError: If directory creation fails for other reasons
    """
    try:
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug(PATH_CREATION_MSG.format(path=directory))
    except PermissionError:
        logger.error(ERROR_PERMISSION_DENIED_DIR.format(path=directory))
        raise
    except OSError as e:
        logger.error(ERROR_DIR_CREATION.format(error=e))
        raise


def ensure_parent_exists(file_path: Path) -> None:
    """Ensure the parent directory of the file exists.

    Args:
        file_path: Path to file whose parent directory should exist

    Raises:
        PermissionError: If directory can't be created due to permissions
        OSError: If directory creation fails for other reasons
    """
    ensure_directory_exists(file_path.parent)


def read_file(file_path: Path, encoding: str) -> str:
    """Read file content with strict content preservation.

    Rules:
    - Read content exactly as stored
    - No content modification
    - No whitespace normalization
    - No newline manipulation
    - Strict encoding adherence

    Args:
        file_path: Path to file to read
        encoding: File encoding to use

    Returns:
        str: File content exactly as stored

    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If file can't be read due to permissions
        UnicodeError: If content can't be decoded with specified encoding
        RuntimeError: If unexpected error occurs during read operation
    """
    logger.info(LOG_READING_FILE.format(path=file_path, encoding=encoding))
    try:
        with open(file_path, "r", encoding=encoding) as f:
            content = f.read()
            logger.info(LOG_READ_SUCCESS.format(count=len(content), path=file_path))
            return content
    except FileNotFoundError:
        logger.error(ERROR_PATH_NOT_EXIST.format(name="File", path=file_path))
        raise FileNotFoundError(
            ERROR_PATH_NOT_EXIST.format(name="File", path=file_path)
        )
    except PermissionError:
        logger.error(ERROR_PERMISSION_DENIED_PATH.format(path=file_path))
        raise PermissionError(ERROR_PERMISSION_DENIED_PATH.format(path=file_path))
    except UnicodeError as e:
        logger.error(
            LOG_ENCODING_ERROR.format(path=file_path, encoding=encoding, error=e)
        )
        raise
    except Exception as e:
        logger.error(ERROR_UNEXPECTED.format(name="file read", error=e))
        raise


def validate_encoding(encoding: str) -> bool:
    """Validate if an encoding is supported by Python.

    Args:
        encoding: Encoding name to validate

    Returns:
        bool: True if encoding is supported, False otherwise

    Example:
        >>> validate_encoding('utf-8')
        True
        >>> validate_encoding('invalid-encoding')
        False
    """
    try:
        "test".encode(encoding)
        return True
    except LookupError:
        logger.error(ERROR_UNSUPPORTED_ENCODING.format(encoding=encoding))
        return False


def write_file(file_path: Path, content: str, encoding: str) -> None:
    """Write content to file with strict content preservation.

    Rules:
    - Write content exactly as provided
    - No content modification
    - No whitespace normalization
    - No newline manipulation
    - Creates parent directories if they don't exist
    - Validates encoding before writing
    - Validates write permissions if file exists

    Args:
        file_path: Path to file to write
        content: Content to write
        encoding: File encoding to use

    Raises:
        LookupError: If encoding is not supported
        PermissionError: If file or parent directory can't be written
        UnicodeError: If content can't be encoded with specified encoding
        OSError: If file write fails for other reasons
        RuntimeError: If unexpected error occurs during write operation
    """
    if not validate_encoding(encoding):
        msg = ERROR_UNSUPPORTED_ENCODING.format(encoding=encoding)
        logger.error(msg)
        raise LookupError(msg)

    logger.info(LOG_WRITING_FILE.format(count=len(content), path=file_path))

    try:
        ensure_parent_exists(file_path)

        if file_path.exists():
            validate_path_permissions(file_path, require_write=True)

        with open(file_path, "w", encoding=encoding) as f:
            f.write(content)
            logger.info(LOG_WRITE_SUCCESS.format(path=file_path))

    except PermissionError:
        msg = ERROR_PERMISSION_DENIED_PATH.format(path=file_path)
        logger.error(msg)
        raise PermissionError(msg)
    except UnicodeError as e:
        logger.error(
            LOG_ENCODING_ERROR.format(path=file_path, encoding=encoding, error=e)
        )
        raise
    except OSError as e:
        msg = ERROR_FILE_WRITE.format(error=e)
        logger.error(msg)
        raise OSError(msg)
    except Exception as e:
        msg = ERROR_UNEXPECTED.format(name="file write", error=e)
        logger.error(msg)
        raise RuntimeError(msg)


def generate_temp_filename(original_name: str) -> str:
    """Generate a unique temporary filename.

    Uses both UUID and timestamp to ensure uniqueness:
    - UUID for process/thread uniqueness
    - Timestamp for debugging/cleanup purposes

    Args:
        original_name: Original filename

    Returns:
        Unique temporary filename
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid4())
    return f"temp_{timestamp}_{unique_id}_{original_name}"


def check_path_exists(path: Path) -> None:
    """Verify path exists.

    Args:
        path: Path to check

    Raises:
        FileNotFoundError: If path does not exist
    """
    if not path.exists():
        msg = ERROR_PATH_NOT_EXIST.format(name="Path", path=path)
        logger.error(msg)
        raise FileNotFoundError(msg)


def check_read_permissions(path: Path) -> None:
    """Verify read permissions for path.

    Args:
        path: Path to check

    Raises:
        PermissionError: If path is not readable
    """
    if not os.access(path, os.R_OK):
        msg = ERROR_PATH_NO_READ.format(name="Path", path=path)
        logger.error(msg)
        raise PermissionError(msg)


def check_write_permissions(path: Path) -> None:
    """Verify write permissions for path.

    Args:
        path: Path to check

    Raises:
        FilePermissionError: If path is not writable
    """
    if not os.access(path, os.W_OK):
        msg = ERROR_PATH_NO_WRITE.format(name="Path", path=path)
        logger.error(msg)
        raise FilePermissionError(msg)


def validate_path_permissions(path: Path, require_write: bool = False) -> None:
    """Validate existence and permissions for path.

    Args:
        path: Path to validate
        require_write: If True, verify write permissions

    Raises:
        FileNotFoundError: If path does not exist
        PermissionError: If required permissions are not available
    """
    check_path_exists(path)
    check_read_permissions(path)

    if require_write:
        check_write_permissions(path)


def atomic_write(file_path: Path, content: str, encoding: str, temp_dir: Path) -> None:
    """Write content atomically using a temporary file.

    Rules:
    - Same content preservation rules as write_file
    - Uses temporary file with UUID for safety
    - Atomic replacement of target file
    - Creates parent directories if they don't exist
    - Handles cross-device moves

    Args:
        file_path: Target file path
        content: Content to write
        encoding: File encoding to use
        temp_dir: Directory for temporary files (must exist and be writable)

    Raises:
        FileNotFoundError: If temp_dir doesn't exist or can't create parent directory
        PermissionError: If temp_dir or target location can't be written
        LookupError: If encoding is not supported
        UnicodeError: If content can't be encoded with specified encoding
        OSError: If atomic move fails or other I/O errors occur
    """
    temp_filename = generate_temp_filename(file_path.name)
    temp_file = temp_dir / temp_filename

    logger.info(LOG_ATOMIC_WRITE_START.format(target=file_path, temp=temp_file))

    try:
        # Validate temp directory
        try:
            validate_path_permissions(temp_dir, require_write=True)
        except FileNotFoundError:
            logger.error(LOG_TEMP_DIR_NOT_FOUND.format(path=temp_dir))
            raise
        except PermissionError:
            logger.error(LOG_NO_TEMP_DIR_PERMISSION.format(path=temp_dir))
            raise

        # Validate encoding
        if not validate_encoding(encoding):
            logger.error(ERROR_UNSUPPORTED_ENCODING.format(encoding=encoding))
            raise LookupError(ERROR_UNSUPPORTED_ENCODING.format(encoding=encoding))

        # Ensure parent directory exists
        try:
            ensure_parent_exists(file_path)
        except PermissionError:
            logger.error(LOG_PARENT_DIR_PERMISSION.format(path=file_path))
            raise
        except OSError as e:
            logger.error(LOG_PARENT_DIR_ERROR.format(path=file_path, error=e))
            raise

        # Check target file permissions if it exists
        if file_path.exists():
            try:
                validate_path_permissions(file_path, require_write=True)
            except PermissionError:
                logger.error(LOG_NO_WRITE_PERMISSION.format(path=file_path))
                raise

        # Write to temporary file
        try:
            write_file(temp_file, content, encoding)
        except UnicodeError as e:
            logger.error(LOG_ENCODING_WRITE_ERROR.format(encoding=encoding, error=e))
            raise
        except PermissionError:
            logger.error(LOG_PERMISSION_DENIED_TEMP.format(path=temp_file))
            raise
        except OSError as e:
            logger.error(LOG_TEMP_WRITE_FAILED.format(path=temp_file, error=e))
            raise

        # Atomic move/replace
        try:
            logger.debug(LOG_MOVING_FILE.format(source=temp_file, target=file_path))
            shutil.move(str(temp_file), str(file_path))
            logger.info(LOG_ATOMIC_WRITE_SUCCESS.format(path=file_path))
        except PermissionError:
            logger.error(LOG_MOVE_PERMISSION_DENIED.format(path=file_path))
            raise
        except OSError as e:
            if e.errno == errno.EXDEV:  # Cross-device link error
                # Add fallback for cross-device moves
                shutil.copy2(str(temp_file), str(file_path))
                temp_file.unlink()
            else:
                logger.error(LOG_MOVE_FAILED.format(path=file_path, error=e))
                raise

    except Exception as e:
        # Clean up temp file if something goes wrong
        if temp_file.exists():
            try:
                temp_file.unlink()
                logger.debug(LOG_TEMP_CLEANUP.format(path=temp_file))
            except Exception as cleanup_error:
                logger.warning(
                    LOG_CLEANUP_FAILED.format(path=temp_file, error=cleanup_error)
                )
        raise


def ensure_file_readable(file_path: Path) -> None:
    """
    Ensure a file is readable, raising appropriate errors if not.

    Args:
        file_path: Path to check

    Raises:
        FileNotFoundError: If path doesn't exist
        PermissionError: If file isn't readable
    """
    try:
        validate_path_permissions(file_path, require_write=False)
    except FileNotFoundError:
        logger.error(LOG_PATH_NOT_FOUND.format(path=file_path))
        raise
    except PermissionError:
        logger.error(LOG_NO_READ_PERMISSION.format(path=file_path))
        raise
