from datetime import datetime
from pathlib import Path
import yaml
from typing import Dict, Optional
import os
import re
import logging
from types import SimpleNamespace

from .config import WriterConfig
from .exceptions import WriterError
from .constants import (
    ERROR_DIRECTORY_EXISTS,
    ERROR_DIR_CREATION,
    ERROR_DIR_EXISTS,
    ERROR_DIRECTORY_PERMISSION,
    ERROR_DOCUMENT_NOT_EXIST,
    ERROR_DUPLICATE_SECTION_MARKER,
    ERROR_FAILED_APPEND_SECTION,
    ERROR_FILE_EXISTS,
    ERROR_FILE_WRITE,
    ERROR_HEADER_LEVEL,
    ERROR_INVALID_CONTENT,
    ERROR_INVALID_FILENAME,
    ERROR_INVALID_HEADER_LEVEL,
    ERROR_INVALID_MARKDOWN_FILE,
    ERROR_INVALID_METADATA_TYPE,
    ERROR_INVALID_SECTION_TITLE,
    ERROR_MISMATCHED_SECTION_MARKER,
    ERROR_MISSING_METADATA,
    ERROR_MISSING_SECTION_MARKER,
    ERROR_ORPHANED_SECTION_MARKER,
    ERROR_PATH_TOO_LONG,
    ERROR_PERMISSION_DENIED_ACCESS,
    ERROR_PERMISSION_DENIED_DIR,
    ERROR_PERMISSION_DENIED_FILE,
    ERROR_PERMISSION_DENIED_PATH,
    ERROR_PERMISSION_DENIED_WRITE,
    ERROR_SECTION_EXISTS,
    ERROR_SECTION_INSERT_AFTER_NOT_FOUND,
    ERROR_SECTION_MARKER_NOT_FOUND,
    ERROR_SECTION_NOT_FOUND,
    ERROR_YAML_SERIALIZATION,
    FILE_MODE_APPEND,
    FILE_MODE_READ,
    FILE_MODE_WRITE,
    FORBIDDEN_FILENAME_CHARS,
    HEADER_NEXT_PATTERN,
    PATTERN_HEADER,
    HEADER_TITLE_GROUP,
    INSERT_AFTER_MARKER,
    LOG_ADDED_EXTENSION,
    LOG_APPEND_TO_EXISTING_SECTION,
    LOG_CLEANUP_FAILED,
    LOG_CLEANUP_PARTIAL_FILE,
    LOG_CREATING_DIRECTORY,
    LOG_DIR_CREATION_ERROR,
    LOG_DOCUMENT_CREATED,
    LOG_DUPLICATE_MARKER,
    LOG_ERROR_APPENDING_SECTION,
    LOG_FILE_EXISTS,
    LOG_FILE_NOT_FOUND,
    LOG_FILE_VALIDATION,
    LOG_HEADER_LEVEL_ERROR,
    LOG_INVALID_CONTENT,
    LOG_INVALID_FILE_FORMAT,
    LOG_INVALID_HEADER_LEVEL,
    LOG_INVALID_METADATA_TYPES,
    LOG_INVALID_SECTION_TITLE,
    LOG_MISMATCHED_MARKER,
    LOG_MISSING_MARKER,
    LOG_MISSING_METADATA_FIELDS,
    LOG_ORPHANED_MARKER,
    LOG_PATH_TOO_LONG,
    LOG_PERMISSION_ERROR,
    LOG_PERMISSION_ERROR_CHECKING_FILE,
    LOG_PERMISSION_DENIED_APPEND,
    LOG_REMOVING_PARTIAL_FILE,
    LOG_SECTION_APPEND_SUCCESS,
    LOG_SECTION_EXISTS,
    LOG_SECTION_INSERT_SUCCESS,
    LOG_SECTION_MARKER_VALID,
    LOG_SECTION_MARKER_VALIDATION,
    LOG_SECTION_NOT_FOUND,
    LOG_UNEXPECTED_ERROR,
    LOG_USING_DEFAULT_CONFIG,
    LOG_USING_HEADER_LEVEL,
    LOG_VALIDATE_FILENAME,
    LOG_WRITING_FILE,
    LOG_YAML_SERIALIZATION,
    MARKER_TITLE_GROUP,
    MAX_FILENAME_LENGTH,
    MAX_PATH_LENGTH,
    MD_EXTENSION,
    RESERVED_WINDOWS_FILENAMES,
    SECTION_CONTENT_PATTERN,
    SECTION_CONTENT_SPACING,
    SECTION_HEADER_PREFIX,
    PATTERN_SECTION_MARKER,
    SECTION_MARKER_TEMPLATE,
    YAML_FRONTMATTER_END,
    YAML_FRONTMATTER_START,
    SECTION_CONTENT_FORMAT,
    DOUBLE_NEWLINE,
    SECTION_MARKER_REGEX,
    HEADER_LEVEL_2_PREFIX,
    PATTERN_HEADER_WITH_NEWLINE,
    DEFAULT_NEWLINE,
    LOG_SECTION_MARKER_NOT_FOUND,
    LOG_FOUND_SECTION_BOUNDARIES,
    PATTERN_UNTIL_NEXT_HEADER,
    PATTERN_NEWLINE,
    SECTION_HEADER_KEY,
    SECTION_MARKER_KEY,
    SECTION_CONTENT_KEY,
    LOG_FILE_OPERATION_ERROR,
    NO_ASSOCIATED_HEADER,
    LOG_READ_SUCCESS,
)
from .file_io import read_file, write_file, atomic_write, validate_path_permissions

# Set up module logger
logger = logging.getLogger(__name__)


def validate_filename(file_name: str, config: WriterConfig) -> Path:
    """Validate filename and return full path."""
    if not file_name or not is_valid_filename(file_name):
        logger.warning(LOG_VALIDATE_FILENAME, file_name)
        raise WriterError(ERROR_INVALID_FILENAME)

    # Ensure .md extension
    if not file_name.endswith(MD_EXTENSION):
        file_name += MD_EXTENSION
        logger.debug(LOG_ADDED_EXTENSION, file_name)

    # Check path length
    full_path = config.drafts_dir / file_name
    if len(str(full_path)) > MAX_PATH_LENGTH:
        logger.warning(LOG_PATH_TOO_LONG.format(path=full_path))
        raise WriterError(
            ERROR_PATH_TOO_LONG.format(max_length=MAX_PATH_LENGTH, path=full_path)
        )

    return full_path


def validate_metadata(metadata: Dict[str, str], config: WriterConfig) -> None:
    """Validate metadata types and required fields."""
    if not isinstance(metadata, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in metadata.items()
    ):
        logger.warning(LOG_INVALID_METADATA_TYPES, metadata)
        raise WriterError(ERROR_INVALID_METADATA_TYPE)

    missing_fields = [field for field in config.metadata_keys if field not in metadata]
    if missing_fields:
        logger.warning(LOG_MISSING_METADATA_FIELDS, missing_fields)
        raise WriterError(
            ERROR_MISSING_METADATA.format(fields=", ".join(missing_fields))
        )


def ensure_directory_exists(dir_path: Path) -> None:
    """Create directory if it doesn't exist."""
    try:
        logger.debug(LOG_CREATING_DIRECTORY.format(path=dir_path))
        dir_path.mkdir(parents=True, exist_ok=True)
    except FileExistsError:
        logger.error(ERROR_DIRECTORY_EXISTS.format(path=dir_path))
        raise WriterError(ERROR_DIR_EXISTS.format(path=dir_path))
    except PermissionError:
        logger.error(ERROR_DIRECTORY_PERMISSION.format(path=dir_path))
        raise WriterError(ERROR_PERMISSION_DENIED_DIR.format(path=dir_path))
    except OSError as e:
        logger.error(LOG_DIR_CREATION_ERROR.format(path=dir_path, error=str(e)))
        raise WriterError(ERROR_DIR_CREATION.format(error=str(e)))


def write_document(file_path: Path, metadata: Dict[str, str], encoding: str) -> None:
    """Write metadata and frontmatter to file."""
    try:
        logger.debug(LOG_YAML_SERIALIZATION)
        yaml_content = yaml.dump(metadata, default_flow_style=False, sort_keys=False)

        # Calculate total content length
        content = YAML_FRONTMATTER_START + yaml_content + YAML_FRONTMATTER_END

        logger.debug(LOG_WRITING_FILE.format(path=file_path, count=len(content)))
        with open(file_path, "w", encoding=encoding) as f:
            f.write(YAML_FRONTMATTER_START)
            f.write(yaml_content)
            f.write(YAML_FRONTMATTER_END)

    except yaml.YAMLError as e:
        logger.error(ERROR_YAML_SERIALIZATION.format(error=str(e)))
        raise WriterError(ERROR_YAML_SERIALIZATION.format(error=str(e)))
    except PermissionError:
        logger.error(ERROR_PERMISSION_DENIED_FILE.format(path=file_path))
        raise WriterError(ERROR_PERMISSION_DENIED_FILE.format(path=file_path))
    except OSError as e:
        logger.error(ERROR_FILE_WRITE.format(error=str(e)))
        raise WriterError(ERROR_FILE_WRITE.format(error=str(e)))


def create_document(
    file_name: str, metadata: Dict[str, str], config: Optional[WriterConfig] = None
) -> Path:
    """Create a new Markdown document with YAML frontmatter metadata."""
    logger.debug(LOG_FILE_VALIDATION.format(file_name=file_name))

    # Use default config if none provided
    config = get_config(config)

    # Validate inputs
    full_path = validate_filename(file_name, config)  # This returns a Path object
    validate_metadata(metadata, config)


    try:
        # Check if file exists
        try:
            if os.path.exists(str(full_path)):
                logger.warning(LOG_FILE_EXISTS.format(path=full_path))
                raise WriterError(ERROR_FILE_EXISTS.format(path=full_path))
        except (OSError, PermissionError) as e:
            logger.error(LOG_PERMISSION_ERROR.format(path=full_path, error=str(e)))
            raise WriterError(ERROR_PERMISSION_DENIED_PATH.format(path=full_path))

        # Create directories if needed
        if config.create_directories:
            ensure_directory_exists(config.drafts_dir)

        # Write document
        write_document(full_path, metadata, config.default_encoding)
        logger.info(LOG_DOCUMENT_CREATED.format(path=full_path))
        return full_path

    except Exception as e:
        # Clean up if file was partially written
        logger.debug(LOG_CLEANUP_PARTIAL_FILE.format(path=full_path))
        cleanup_partial_file(full_path)

        if isinstance(e, WriterError):
            raise

        # Log and re-raise unexpected errors with original type
        logger.error(LOG_UNEXPECTED_ERROR.format(error=str(e), error_type=type(e).__name__))
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
        - Special directory names (., ..)
        - Trailing spaces or dots
    """
    # Check for empty or too long filenames
    if not filename or len(filename) > MAX_FILENAME_LENGTH:
        return False

    # Prevent special directory names
    if filename in {".", "..", "./", "../"}:
        return False

    # Check for common forbidden characters in filenames
    if any(char in filename for char in FORBIDDEN_FILENAME_CHARS):
        return False

    # Check for reserved Windows filenames
    base_name = os.path.splitext(os.path.basename(filename))[0].upper()
    if base_name in RESERVED_WINDOWS_FILENAMES:
        return False

    # Check for trailing spaces or dots
    if filename.endswith((" ", ".")):
        return False

    return True


def cleanup_partial_file(file_path: Path) -> None:
    """Clean up partially written files in case of errors."""
    try:
        if os.path.exists(str(file_path)):
            logger.debug(LOG_REMOVING_PARTIAL_FILE, file_path)
            os.remove(str(file_path))
    except (OSError, PermissionError) as e:
        logger.warning(LOG_CLEANUP_FAILED, file_path, str(e))


def append_section(
    file_name: str,
    section_title: str,
    content: str,
    config: Optional[WriterConfig] = None,
    allow_append: bool = False,
    header_level: Optional[int] = None,
    insert_after: Optional[str] = None,
) -> None:
    """Append a new section to a Markdown document."""
    config = get_config(config)

    # Validate inputs
    if not content or not isinstance(content, str):
        logger.error(LOG_INVALID_CONTENT, content)
        raise WriterError(ERROR_INVALID_CONTENT)

    if not section_title or not isinstance(section_title, str):
        logger.error(LOG_INVALID_SECTION_TITLE, section_title)
        raise WriterError(ERROR_INVALID_SECTION_TITLE)

    # Validate filename and get full path
    file_path = validate_filename(file_name, config)

    # Validate file exists and is readable/writable
    validate_file(file_path, require_write=True)

    # Create section marker
    section_marker = INSERT_AFTER_MARKER.format(insert_after=section_title)

    try:
        # Read existing content and check for section
        with open(file_path, FILE_MODE_READ, encoding=config.default_encoding) as f:
            content_str = f.read()

        # Use new utility to check if section exists
        section_start, _ = get_section_marker_position(content_str, section_title)
        if section_start != -1:
            if not allow_append:
                logger.error(LOG_SECTION_EXISTS, section_title, file_path)
                raise WriterError(ERROR_SECTION_EXISTS.format(section_title=section_title))
            else:
                logger.info(LOG_APPEND_TO_EXISTING_SECTION, section_title)
                return append_to_existing_section(
                    file_path, section_title, content, content_str, config
                )

        # Determine header level - use explicit level or determine from content
        try:
            final_header_level = (
                header_level if header_level is not None else 2
            )  # Default to level 2
            if (
                not isinstance(final_header_level, int)
                or not 1 <= final_header_level <= 6
            ):
                logger.error(LOG_INVALID_HEADER_LEVEL, final_header_level)
                raise WriterError(ERROR_INVALID_HEADER_LEVEL)
        except ValueError as e:
            logger.error(LOG_HEADER_LEVEL_ERROR, str(e))
            raise WriterError(ERROR_HEADER_LEVEL.format(error=str(e)))

        header_prefix = SECTION_HEADER_PREFIX * final_header_level

        logger.debug(
            LOG_USING_HEADER_LEVEL,
            final_header_level,
            section_title,
            file_path,
        )

        # Format new section content with proper spacing
        new_section = SECTION_CONTENT_FORMAT.format(
            spacing=DOUBLE_NEWLINE,
            header_prefix=header_prefix,
            section_title=section_title,
            section_marker=section_marker,
            content=content.strip()
        )

        # Handle insertion after specific section
        if insert_after:
            # Use new utility to find the section to insert after
            _, marker_end = get_section_marker_position(content_str, insert_after)
            if marker_end == -1:
                logger.error(ERROR_SECTION_INSERT_AFTER_NOT_FOUND.format(insert_after=insert_after))
                raise WriterError(ERROR_SECTION_INSERT_AFTER_NOT_FOUND.format(insert_after=insert_after))

            # Find the start of the next section (if any)
            next_marker_match = re.search(
                SECTION_MARKER_REGEX, content_str[marker_end:]
            )

            # Calculate insertion position
            if next_marker_match:
                # Find the start of the header preceding this marker
                header_start = content_str[
                    marker_end : marker_end + next_marker_match.start()
                ].rfind(HEADER_LEVEL_2_PREFIX)
                if header_start != -1:
                    insert_pos = marker_end + header_start
                else:
                    insert_pos = marker_end + next_marker_match.start()
            else:
                insert_pos = len(content_str)

            # Insert the new section
            updated_content = (
                content_str[:insert_pos].rstrip()
                + new_section
                + content_str[insert_pos:].lstrip()
            )

            # Write updated content
            with open(file_path, FILE_MODE_WRITE, encoding=config.default_encoding) as f:
                f.write(updated_content)

            logger.info(
                LOG_SECTION_INSERT_SUCCESS,
                section_title,
                insert_after,
                file_path,
            )
            return

        # Append the new section
        try:
            with open(file_path, FILE_MODE_APPEND, encoding=config.default_encoding) as f:
                f.write(new_section)

            logger.info(
                LOG_SECTION_APPEND_SUCCESS, section_title, file_path
            )

        except PermissionError:
            logger.error(LOG_PERMISSION_DENIED_APPEND, file_path)
            raise WriterError(ERROR_PERMISSION_DENIED_WRITE.format(file_path=file_path))

        except Exception as e:
            logger.error(LOG_ERROR_APPENDING_SECTION, file_path, str(e))
            if isinstance(e, WriterError):
                raise
            raise WriterError(ERROR_FAILED_APPEND_SECTION.format(error=str(e)))

    except Exception as e:
        logger.error(LOG_ERROR_APPENDING_SECTION, file_path, str(e))
        if isinstance(e, WriterError):
            raise
        raise WriterError(ERROR_FAILED_APPEND_SECTION.format(error=str(e)))


def append_to_existing_section(
    file_path: Path,
    section_title: str,
    new_content: str,
    existing_content: str,
    config: WriterConfig,
) -> None:
    """Append content to an existing section."""
    section_start, section_end = find_section_boundaries(
        existing_content, section_title
    )

    if section_start == -1:
        logger.error(LOG_SECTION_NOT_FOUND.format(section_title=section_title))
        raise WriterError(
            ERROR_SECTION_MARKER_NOT_FOUND.format(section_title=section_title)
        )

    # Insert new content before the next section
    updated_content = (
        existing_content[:section_end]
        + SECTION_CONTENT_SPACING
        + new_content.strip()
        + SECTION_CONTENT_SPACING
        + existing_content[section_end:]
    )

    # Write updated content back to file
    with open(file_path, FILE_MODE_WRITE, encoding=config.default_encoding) as f:
        f.write(updated_content)


def validate_section_markers(content: str) -> None:
    """Validate all section markers in a document.

    Performs several validation checks:
    1. No duplicate section markers
    2. Each header has a matching marker immediately following it
    3. Each marker matches its header's title exactly
    4. No orphaned markers (markers without corresponding headers)

    Args:
        content: The document content to validate

    Raises:
        WriterError: If any validation check fails, with specific error messages for:
            - Duplicate section markers
            - Missing section markers after headers
            - Mismatched section marker titles
            - Orphaned section markers

    Example:
        >>> content = "# Introduction\\n<!-- Section: Introduction -->\\nContent"
        >>> validate_section_markers(content)  # No error raised
        >>> bad_content = "# Intro\\n<!-- Section: Different -->\\nContent"
        >>> validate_section_markers(bad_content)  # Raises WriterError
    """
    logger.debug(LOG_SECTION_MARKER_VALIDATION)

    # Extract headers and markers using utility function
    header_matches = list(re.finditer(PATTERN_HEADER, content, re.MULTILINE))
    marker_positions = find_marker_positions(content, PATTERN_SECTION_MARKER)

    # Check for duplicate markers
    seen_markers = set()
    for start, end in marker_positions:
        marker_match = re.match(PATTERN_SECTION_MARKER, content[start:end])
        marker_title = marker_match.group(MARKER_TITLE_GROUP).strip()
        if marker_title in seen_markers:
            logger.error(LOG_DUPLICATE_MARKER.format(marker_title=marker_title))
            raise WriterError(
                ERROR_DUPLICATE_SECTION_MARKER.format(marker_title=marker_title)
            )
        seen_markers.add(marker_title)

    # Validate markers match their headers
    for header in header_matches:
        header_title = header.group(HEADER_TITLE_GROUP).strip()
        header_position = header.end()

        # Find the marker immediately following the header
        following_content = content[header_position:].strip()
        first_line = following_content.split(DEFAULT_NEWLINE)[0] if following_content else ""

        expected_marker = SECTION_MARKER_TEMPLATE.format(section_title=header_title)

        # Check if any marker format is present
        if not re.match(SECTION_CONTENT_PATTERN, first_line):
            logger.error(LOG_MISSING_MARKER.format(header_title=header_title))
            raise WriterError(
                ERROR_MISSING_SECTION_MARKER.format(header_title=header_title)
            )

        # Check if the marker matches exactly
        if first_line != expected_marker:
            logger.error(
                LOG_MISMATCHED_MARKER.format(
                    header_title=header_title,
                    expected=expected_marker,
                    found=first_line,
                )
            )
            raise WriterError(
                ERROR_MISMATCHED_SECTION_MARKER.format(header_title=header_title)
            )

    # Check for orphaned markers (markers without headers)
    header_titles = {header.group(HEADER_TITLE_GROUP).strip() for header in header_matches}
    
    for start, end in marker_positions:
        marker_match = re.match(PATTERN_SECTION_MARKER, content[start:end])
        marker_title = marker_match.group(MARKER_TITLE_GROUP).strip()
        
        if not any(marker_title == header_title for header_title in header_titles):
            logger.error(LOG_ORPHANED_MARKER.format(marker_title=marker_title))
            raise WriterError(
                ERROR_ORPHANED_SECTION_MARKER.format(marker_title=marker_title)
            )

    logger.info(LOG_SECTION_MARKER_VALID)


def find_section_boundaries(content: str, section_title: str) -> tuple[int, int]:
    """Find the start and end positions of a section in the content.
    
    Args:
        content: The document content to search
        section_title: The title of the section to find

    Returns:
        tuple[int, int]: (section_start, section_end) positions, (-1, -1) if not found

    Note:
        section_start points to the start of the section marker
        section_end points to the start of the next section or end of content
    """
    # Find the section marker position using the new utility
    section_start, marker_end = get_section_marker_position(content, section_title)

    if section_start == -1:
        logger.debug(LOG_SECTION_MARKER_NOT_FOUND.format(section_title=section_title))
        return -1, -1

    # Find the next section marker or EOF
    next_section = re.search(HEADER_NEXT_PATTERN, content[marker_end:])
    section_end = next_section.start() + marker_end if next_section else len(content)

    logger.debug(
        LOG_FOUND_SECTION_BOUNDARIES.format(
            section_title=section_title,
            start=section_start,
            end=section_end,
        )
    )

    return section_start, section_end


def find_section(content: str, section_title: str) -> Optional[re.Match]:
    """Find a section by title in the document content."""
    # First find the exact marker
    marker = SECTION_MARKER_TEMPLATE.format(section_title=section_title)
    marker_match = re.search(re.escape(marker) + PATTERN_NEWLINE, content)
    if not marker_match:
        return None

    # Find the nearest header before the marker
    content_before_marker = content[: marker_match.start()]
    header_pattern = PATTERN_HEADER_WITH_NEWLINE  # Match Markdown headers with newline
    headers = list(re.finditer(header_pattern, content_before_marker, re.MULTILINE))
    if not headers:
        return None

    # Get the last header before the marker
    last_header = headers[-1]
    header_text = content[last_header.start() : last_header.end()]

    # Find the content that follows the marker until the next header
    content_after_marker = content[marker_match.end() :]
    next_header_match = re.search(PATTERN_UNTIL_NEXT_HEADER, content_after_marker, re.MULTILINE)

    # If there's no next header, capture until the end
    if next_header_match:
        section_content = content_after_marker[: next_header_match.start()]
    else:
        section_content = content_after_marker

    # Return a match-like object
    return SimpleNamespace(
        group=lambda x: {
            SECTION_HEADER_KEY: header_text,
            SECTION_MARKER_KEY: marker_match.group(0),
            SECTION_CONTENT_KEY: section_content,
        }[x],
        start=lambda: last_header.start(),
        end=lambda: marker_match.end() + len(section_content),
    )


def edit_section(
    file_name: str, section_title: str, new_content: str, config: WriterConfig
):
    """Edit an existing section in the document."""
    file_path = config.drafts_dir / file_name

    try:
        # Read using centralized function
        content = read_file(file_path, config.default_encoding)

        section_match = find_section(content, section_title)
        if not section_match:
            logger.error(LOG_SECTION_NOT_FOUND.format(section_title=section_title))
            raise WriterError(
                ERROR_SECTION_NOT_FOUND.format(section_title=section_title)
            )

        # Create replacement preserving exact content
        replacement = (
            section_match.group(SECTION_HEADER_KEY) + section_match.group(SECTION_MARKER_KEY) + new_content
        )

        updated_content = (
            content[: section_match.start()]
            + replacement
            + content[section_match.end() :]
        )

        # Validate before writing
        validate_section_markers(updated_content)

        # Write using atomic operation
        atomic_write(
            file_path, updated_content, config.default_encoding, config.temp_dir
        )

    except (OSError, IOError) as e:
        logger.error(LOG_FILE_OPERATION_ERROR.format(error=str(e)))
        raise WriterError(str(e)) from e


def extract_section_titles(content: str) -> list[str]:
    """Extract all section titles from the content.

    Args:
        content: The document content to analyze

    Returns:
        List of section titles found in the document
    """
    marker_pattern = re.compile(PATTERN_SECTION_MARKER)
    matches = marker_pattern.finditer(content)
    return [match.group(MARKER_TITLE_GROUP).strip() for match in matches]


def extract_section_markers(content: str) -> dict[str, str]:
    """Extract all section markers and their associated headers.

    Args:
        content: The document content to analyze

    Returns:
        Dictionary mapping section titles to their headers
    """
    markers = {}

    # Find all section markers
    marker_matches = re.finditer(PATTERN_SECTION_MARKER, content)
    header_matches = re.finditer(PATTERN_HEADER, content)

    # Build marker to header mapping
    for marker in marker_matches:
        marker_title = marker.group(MARKER_TITLE_GROUP).strip()
        marker_pos = marker.start()

        # Find the nearest header before this marker
        nearest_header = None
        nearest_distance = float("inf")

        for header in header_matches:
            header_pos = header.start()
            distance = marker_pos - header_pos

            if 0 <= distance < nearest_distance:
                nearest_distance = distance
                nearest_header = header.group(0).strip()

        markers[marker_title] = nearest_header or NO_ASSOCIATED_HEADER

    return markers


def validate_file(file_path: Path, require_write: bool = False) -> None:
    """Validate that the file exists, has the correct format, and meets permission requirements.
    
    Args:
        file_path: Path object pointing to the file to validate
        require_write: If True, also check for write permissions

    Raises:
        WriterError: If file doesn't exist, has wrong format, or lacks permissions
        FileNotFoundError: If the file doesn't exist
        PermissionError: If required permissions are not available
    """
    try:
        # Check if file exists and has correct permissions
        validate_path_permissions(file_path, require_write=require_write)
        
        # Verify file extension
        if file_path.suffix.lower() != MD_EXTENSION:
            logger.error(LOG_INVALID_FILE_FORMAT.format(path=file_path))
            raise WriterError(ERROR_INVALID_MARKDOWN_FILE.format(path=file_path))

    except FileNotFoundError:
        logger.error(LOG_FILE_NOT_FOUND.format(path=file_path))
        raise WriterError(ERROR_DOCUMENT_NOT_EXIST.format(file_path=file_path))
    except PermissionError:
        logger.error(LOG_PERMISSION_ERROR.format(path=file_path))
        raise WriterError(ERROR_PERMISSION_DENIED_FILE.format(path=file_path))


def create_frontmatter(metadata: Dict[str, str]) -> str:
    """Create YAML frontmatter from metadata.

    Args:
        metadata: Dictionary of metadata key-value pairs to include in frontmatter

    Returns:
        str: Formatted YAML frontmatter string with delimiters (---)

    Raises:
        WriterError: If YAML serialization fails or metadata is invalid
    
    Note:
        The frontmatter is wrapped in triple-dash delimiters (---) as per YAML spec
        Metadata order is preserved using sort_keys=False
    """
    try:
        yaml_content = yaml.dump(metadata, default_flow_style=False, sort_keys=False)
        return f"{YAML_FRONTMATTER_START}{yaml_content}{YAML_FRONTMATTER_END}"
    except yaml.YAMLError as e:
        logger.error(ERROR_YAML_SERIALIZATION.format(error=str(e)))
        raise WriterError(ERROR_YAML_SERIALIZATION.format(error=str(e)))


def find_marker_positions(content: str, marker_pattern: str) -> list[tuple[int, int]]:
    """Find the start and end positions of all markers matching a pattern.

    Args:
        content: The content to search through
        marker_pattern: Regular expression pattern to match markers

    Returns:
        List of tuples containing (start_position, end_position) for each marker found

    Example:
        >>> content = "Some text <!-- Section: Intro --> more text"
        >>> positions = find_marker_positions(content, r"<!-- Section: .* -->")
        >>> positions
        [(10, 32)]  # Start and end positions of the marker
    """
    matches = re.finditer(marker_pattern, content)
    return [(match.start(), match.end()) for match in matches]


def get_section_marker_position(content: str, section_title: str) -> tuple[int, int]:
    """Find the start and end positions of a specific section marker.

    Args:
        content: The document content to search through
        section_title: The title of the section to find

    Returns:
        Tuple of (start_position, end_position), or (-1, -1) if marker not found

    Example:
        >>> content = "# Intro\\n<!-- Section: Intro -->\\nContent"
        >>> start, end = get_section_marker_position(content, "Intro")
        >>> content[start:end]
        '<!-- Section: Intro -->'
    """
    section_marker = SECTION_MARKER_TEMPLATE.format(section_title=section_title)
    start = content.find(section_marker)
    if start == -1:
        return -1, -1
    return start, start + len(section_marker)


def get_config(config: Optional[WriterConfig] = None) -> WriterConfig:
    """Return the provided configuration or the default configuration.
    
    Args:
        config: Optional configuration object
        
    Returns:
        WriterConfig: The provided config or a new default config
    """
    if config is None:
        config = WriterConfig()
        logger.debug(LOG_USING_DEFAULT_CONFIG)
    return config


def get_section(file_name: str, section_title: str, config: Optional[WriterConfig] = None) -> str:
    """Retrieve the content of a specific section from a Markdown document.
    
    Args:
        file_name: Name of the Markdown file to search
        section_title: Title of the section to retrieve
        config: Optional configuration object. Uses default if not provided.
        
    Returns:
        str: The content of the specified section
        
    Raises:
        WriterError: If the section is not found, file doesn't exist, or other errors occur
    """
    config = get_config(config)

    try:
        # Validate filename and get full path
        file_path = validate_filename(file_name, config)
        
        # Validate file exists and is readable
        validate_file(file_path, require_write=False)
        
        # Read file content
        content = read_file(file_path, config.default_encoding)
        logger.debug(LOG_READ_SUCCESS.format(
            count=len(content),
            path=file_path
        ))
        
        # Find section using existing utility
        section_match = find_section(content, section_title)
        if not section_match:
            logger.error(LOG_SECTION_MARKER_NOT_FOUND.format(section_title=section_title))
            raise WriterError(ERROR_SECTION_NOT_FOUND.format(section_title=section_title))
            
        # Extract just the content (excluding header and marker)
        section_content = section_match.group(SECTION_CONTENT_KEY)
        
        # If content is None or empty, return empty string
        if not section_content:
            return ""
            
        return section_content.strip()
        
    except (OSError, IOError) as e:
        logger.error(LOG_FILE_OPERATION_ERROR.format(error=str(e)))
        raise WriterError(str(e)) from e
