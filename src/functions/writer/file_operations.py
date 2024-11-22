from datetime import datetime
from pathlib import Path
import yaml
from typing import Dict, Optional
import os
import re
import logging

from .config import WriterConfig
from .exceptions import WriterError
from .constants import (
    MAX_FILENAME_LENGTH,
    FORBIDDEN_FILENAME_CHARS,
    RESERVED_WINDOWS_FILENAMES,
    YAML_FRONTMATTER_START,
    YAML_FRONTMATTER_END,
    ERROR_INVALID_FILENAME,
    ERROR_INVALID_METADATA_TYPE,
    ERROR_FILE_EXISTS,
    ERROR_PERMISSION_DENIED_PATH,
    ERROR_PERMISSION_DENIED_DIR,
    ERROR_MISSING_METADATA,
    ERROR_DIR_EXISTS,
    ERROR_DIR_CREATION,
    ERROR_YAML_SERIALIZATION,
    ERROR_FILE_WRITE,
    ERROR_PERMISSION_DENIED_FILE,
    MAX_PATH_LENGTH,
    ERROR_PATH_TOO_LONG,
    SECTION_MARKER_TEMPLATE,
    SECTION_MARKER_PATTERN,
    HEADER_PATTERN,
    ERROR_SECTION_MARKER_NOT_FOUND,
    LOG_SECTION_MARKER_VALIDATION,
    HEADER_NEXT_PATTERN,
    SECTION_CONTENT_PATTERN,
    SECTION_CONTENT_SPACING,
    LOG_VALIDATE_FILENAME,
    LOG_ADDED_EXTENSION,
    MD_EXTENSION,
    LOG_MISSING_MARKER,
    LOG_MISMATCHED_MARKER,
    LOG_ORPHANED_MARKER,
    LOG_DUPLICATE_MARKER,
    LOG_SECTION_MARKER_VALID,
    ERROR_MISSING_SECTION_MARKER,
    ERROR_MISMATCHED_SECTION_MARKER,
    ERROR_ORPHANED_SECTION_MARKER,
    ERROR_DUPLICATE_SECTION_MARKER,
    HEADER_TITLE_GROUP,
    MARKER_TITLE_GROUP,
    LOG_CREATING_DIRECTORY,
    ERROR_DIRECTORY_EXISTS,
    ERROR_DIRECTORY_PERMISSION,
    LOG_DIR_CREATION_ERROR,
    LOG_INVALID_METADATA_TYPES,
    LOG_MISSING_METADATA_FIELDS,
    LOG_FILE_VALIDATION,
    LOG_YAML_SERIALIZATION,
    LOG_WRITING_FILE,
    LOG_SECTION_NOT_FOUND,
    LOG_USING_DEFAULT_CONFIG,
    LOG_CONFIG_DEBUG,
    LOG_FILE_EXISTS,
    LOG_PERMISSION_ERROR,
    LOG_DOCUMENT_CREATED,
    LOG_CLEANUP_PARTIAL_FILE,
    LOG_UNEXPECTED_ERROR,
    ERROR_SECTION_NOT_FOUND
)

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
        logger.warning("Path too long: %s", full_path)
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
        logger.error(ERROR_DIRECTORY_EXISTS % dir_path)
        raise WriterError(ERROR_DIR_EXISTS.format(path=dir_path))
    except PermissionError:
        logger.error(ERROR_DIRECTORY_PERMISSION % dir_path)
        raise WriterError(ERROR_PERMISSION_DENIED_DIR.format(path=dir_path))
    except OSError as e:
        logger.error(LOG_DIR_CREATION_ERROR.format(path=dir_path, error=str(e)))
        raise WriterError(ERROR_DIR_CREATION.format(error=str(e)))


def write_document(file_path: Path, metadata: Dict[str, str], encoding: str) -> None:
    """Write metadata and frontmatter to file."""
    try:
        logger.debug(LOG_YAML_SERIALIZATION)
        yaml_content = yaml.dump(metadata, default_flow_style=False, sort_keys=False)

        logger.debug(LOG_WRITING_FILE.format(path=file_path))
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
    logger.debug(LOG_FILE_VALIDATION, file_name)

    # Use default config if none provided
    if config is None:
        config = WriterConfig()
        logger.debug(LOG_USING_DEFAULT_CONFIG)

    # Validate inputs
    full_path = validate_filename(file_name, config)
    validate_metadata(metadata, config)

    try:
        # Check if file exists
        try:
            if os.path.exists(str(full_path)):
                logger.warning(LOG_FILE_EXISTS, full_path)
                raise WriterError(ERROR_FILE_EXISTS.format(path=full_path))
        except (OSError, PermissionError) as e:
            logger.error(LOG_PERMISSION_ERROR, full_path, str(e))
            raise WriterError(ERROR_PERMISSION_DENIED_PATH.format(path=full_path))

        # Create directories if needed
        if config.create_directories:
            ensure_directory_exists(config.drafts_dir)

        # Write document
        write_document(full_path, metadata, config.default_encoding)
        logger.info(LOG_DOCUMENT_CREATED, full_path)
        return full_path

    except Exception as e:
        # Clean up if file was partially written
        logger.debug(LOG_CLEANUP_PARTIAL_FILE, full_path)
        cleanup_partial_file(full_path)

        if isinstance(e, WriterError):
            raise

        # Log and re-raise unexpected errors with original type
        logger.error(LOG_UNEXPECTED_ERROR, str(e), type(e).__name__)
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
            logger.debug("Removing partial file: %s", file_path)
            os.remove(str(file_path))
    except (OSError, PermissionError) as e:
        logger.warning("Failed to clean up partial file: %s - %s", file_path, str(e))


def append_section(
    file_name: str,
    section_title: str,
    content: str,
    config: Optional[WriterConfig] = None,
    allow_append: bool = False,
    header_level: Optional[int] = None,
    insert_after: Optional[str] = None
) -> None:
    """Append a new section to a Markdown document."""
    if config is None:
        config = WriterConfig()

    # Validate inputs
    if not content or not isinstance(content, str):
        logger.error("Invalid content provided: %s", content)
        raise WriterError("Content must be a non-empty string")

    if not section_title or not isinstance(section_title, str):
        logger.error("Invalid section title: %s", section_title)
        raise WriterError("Section title must be a non-empty string")

    # Validate filename and get full path
    file_path = validate_filename(file_name, config)

    # Validate file exists and is readable
    try:
        if not file_path.exists():
            logger.error("File not found: %s", file_path)
            raise WriterError(f"Document does not exist: {file_path}")

        # Verify file is a Markdown file
        if not file_path.suffix.lower() == ".md":
            logger.error("Invalid file format: %s", file_path)
            raise WriterError(f"File must be a Markdown document: {file_path}")

    except (OSError, PermissionError) as e:
        logger.error("Permission error checking file: %s - %s", file_path, str(e))
        raise WriterError(f"Permission denied when accessing {file_path}")

    # Create section marker
    section_marker = f"<!-- Section: {section_title} -->"

    try:
        # Read existing content and check for section
        with open(file_path, "r", encoding=config.default_encoding) as f:
            content_str = f.read()

        if section_marker in content_str:
            if not allow_append:
                logger.error(
                    "Section already exists: %s in %s", section_title, file_path
                )
                raise WriterError(f"Section '{section_title}' already exists")
            else:
                logger.info("Appending to existing section: %s", section_title)
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
                logger.error("Invalid header level: %s", final_header_level)
                raise WriterError("Header level must be an integer between 1 and 6")
        except ValueError as e:
            logger.error("Header level error: %s", str(e))
            raise WriterError(f"Header level error: {str(e)}")

        header_prefix = "#" * final_header_level

        logger.debug(
            "Using header level %d for section '%s' in %s",
            final_header_level,
            section_title,
            file_path,
        )

        # Format new section content with proper spacing
        new_section = (
            f"\n\n{header_prefix} {section_title}\n"
            f"{section_marker}\n"
            f"{content.strip()}\n"
        )

        # Handle insertion after specific section
        if insert_after:
            target_marker = f"<!-- Section: {insert_after} -->"
            target_pos = content_str.find(target_marker)
            
            if target_pos == -1:
                logger.error("Section to insert after not found: %s", insert_after)
                raise WriterError(f"Section '{insert_after}' not found")
                
            # Find the end of the target marker
            marker_end = target_pos + len(target_marker)
            
            # Find the start of the next section (if any)
            next_marker_match = re.search(r'<!-- Section: .* -->', content_str[marker_end:])
            
            # Calculate insertion position
            if next_marker_match:
                # Find the start of the header preceding this marker
                header_start = content_str[marker_end:marker_end + next_marker_match.start()].rfind('\n##')
                if header_start != -1:
                    insert_pos = marker_end + header_start
                else:
                    insert_pos = marker_end + next_marker_match.start()
            else:
                insert_pos = len(content_str)
                
            # Insert the new section
            updated_content = (
                content_str[:insert_pos].rstrip() +
                new_section +
                content_str[insert_pos:].lstrip()
            )
            
            # Write updated content
            with open(file_path, "w", encoding=config.default_encoding) as f:
                f.write(updated_content)
                
            logger.info(
                "Successfully inserted section '%s' after '%s' in %s",
                section_title,
                insert_after,
                file_path,
            )
            return

        # Append the new section
        try:
            with open(file_path, "a", encoding=config.default_encoding) as f:
                f.write(new_section)

            logger.info(
                "Successfully appended section '%s' to %s", section_title, file_path
            )

        except PermissionError:
            logger.error("Permission denied appending to file: %s", file_path)
            raise WriterError(f"Permission denied when writing to {file_path}")

    except Exception as e:
        logger.error("Error appending section: %s - %s", file_path, str(e))
        if isinstance(e, WriterError):
            raise
        raise WriterError(f"Failed to append section: {str(e)}")


def append_to_existing_section(
    file_path: Path,
    section_title: str,
    new_content: str,
    existing_content: str,
    config: WriterConfig,
) -> None:
    """Append content to an existing section."""
    section_start, section_end = find_section_boundaries(existing_content, section_title)
    
    if section_start == -1:
        logger.error(LOG_SECTION_NOT_FOUND.format(section_title=section_title))
        raise WriterError(ERROR_SECTION_MARKER_NOT_FOUND.format(section_title=section_title))

    # Insert new content before the next section
    updated_content = (
        existing_content[:section_end] +
        SECTION_CONTENT_SPACING +
        new_content.strip() +
        SECTION_CONTENT_SPACING +
        existing_content[section_end:]
    )

    # Write updated content back to file
    with open(file_path, "w", encoding=config.default_encoding) as f:
        f.write(updated_content)


def validate_section_markers(content: str) -> None:
    """Validate section markers in the document."""
    logger.debug(LOG_SECTION_MARKER_VALIDATION)

    # Regular expressions to identify headers and markers
    header_pattern = re.compile(HEADER_PATTERN, re.MULTILINE)
    marker_pattern = re.compile(SECTION_MARKER_PATTERN)

    # Extract headers and markers
    headers = list(header_pattern.finditer(content))
    markers = list(marker_pattern.finditer(content))

    # Check for duplicate markers
    seen_markers = set()
    for marker in markers:
        marker_title = marker.group(MARKER_TITLE_GROUP).strip()
        if marker_title in seen_markers:
            logger.error(LOG_DUPLICATE_MARKER.format(marker_title=marker_title))
            raise WriterError(ERROR_DUPLICATE_SECTION_MARKER.format(marker_title=marker_title))
        seen_markers.add(marker_title)

    # Validate markers match their headers
    for header in headers:
        header_title = header.group(HEADER_TITLE_GROUP).strip()
        header_position = header.end()

        # Find the marker immediately following the header
        following_content = content[header_position:].strip()
        first_line = following_content.split("\n")[0] if following_content else ""

        expected_marker = SECTION_MARKER_TEMPLATE.format(section_title=header_title)
        
        # Check if any marker format is present
        if not re.match(SECTION_CONTENT_PATTERN, first_line):
            logger.error(LOG_MISSING_MARKER.format(header_title=header_title))
            raise WriterError(ERROR_MISSING_SECTION_MARKER.format(header_title=header_title))

        # Check if the marker matches exactly
        if first_line != expected_marker:
            logger.error(LOG_MISMATCHED_MARKER.format(
                header_title=header_title,
                expected=expected_marker,
                found=first_line
            ))
            raise WriterError(ERROR_MISMATCHED_SECTION_MARKER.format(header_title=header_title))

    # Check for orphaned markers (markers without headers)
    header_titles = {header.group(HEADER_TITLE_GROUP).strip() for header in headers}
    for marker in markers:
        marker_title = marker.group(MARKER_TITLE_GROUP).strip()
        if marker_title not in header_titles:
            logger.error(LOG_ORPHANED_MARKER.format(marker_title=marker_title))
            raise WriterError(ERROR_ORPHANED_SECTION_MARKER.format(marker_title=marker_title))

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
    section_marker = SECTION_MARKER_TEMPLATE.format(section_title=section_title)
    section_start = content.find(section_marker)
    
    if section_start == -1:
        logger.debug("Section marker not found: %s", section_title)
        return -1, -1
        
    marker_end = section_start + len(section_marker)
    
    # Find the next section marker or EOF
    next_section = re.search(
        HEADER_NEXT_PATTERN,
        content[marker_end:]
    )
    
    section_end = (
        next_section.start() + marker_end
        if next_section
        else len(content)
    )
    
    logger.debug(
        "Found section boundaries for '%s': start=%d, end=%d",
        section_title,
        section_start,
        section_end
    )
    
    return section_start, section_end


def find_section(content: str, section_title: str) -> Optional[re.Match]:
    """Find a section in the document content.
    
    Args:
        content: The document content to search
        section_title: Title of the section to find
        
    Returns:
        Match object if section is found, None otherwise
        
    Note:
        The match groups will contain:
        1. The header line
        2. The section content
    """
    section_pattern = (
        r"(#{1,6} .*?\n)"  # Header
        r"<!-- Section: " + re.escape(section_title) + r" -->\n"  # Marker
        r"(.*?)"  # Content (non-greedy)
        r"(?=\n#{1,6} |$)"  # Until next header or end of file
    )
    
    return re.search(section_pattern, content, re.DOTALL)


def edit_section(
    file_name: str,
    section_title: str,
    new_content: str,
    config: Optional[WriterConfig] = None
) -> None:
    """Edit a specific section in a document."""
    config = config or WriterConfig()
    file_path = config.drafts_dir / file_name
    temp_file = config.temp_dir / f"temp_{file_name}"
    
    try:
        # Read the original content
        with open(file_path, "r", encoding=config.default_encoding) as f:
            content = f.read()
        
        # Find the section to edit
        section_match = find_section(content, section_title)
        if not section_match:
            logger.error(LOG_SECTION_NOT_FOUND, section_title)
            raise WriterError(ERROR_SECTION_NOT_FOUND.format(section_title=section_title))
        
        # Preserve the header
        header = section_match.group(1)
        marker = f"<!-- Section: {section_title} -->"
        
        # Create the replacement text with proper spacing
        replacement = f"{header}{marker}\n{new_content.strip()}\n\n"
        
        # Replace the section while preserving document structure
        updated_content = content[:section_match.start()] + replacement + content[section_match.end():]
        
        # Validate the updated content
        try:
            validate_section_markers(updated_content)
        except WriterError as e:
            logger.error("Edit would break document structure: %s", str(e))
            raise
        
        # Write to temporary file first
        config.temp_dir.mkdir(parents=True, exist_ok=True)
        with open(temp_file, "w", encoding=config.default_encoding) as f:
            f.write(updated_content)
        
        # Move temporary file to final location
        os.replace(temp_file, file_path)
        
    except (OSError, IOError) as e:
        logger.error("File operation error: %s", str(e))
        if temp_file.exists():
            temp_file.unlink()
        raise WriterError(str(e)) from e


def extract_section_titles(content: str) -> list[str]:
    """Extract all section titles from the content.
    
    Args:
        content: The document content to analyze
        
    Returns:
        List of section titles found in the document
    """
    marker_pattern = re.compile(SECTION_MARKER_PATTERN)
    matches = marker_pattern.finditer(content)
    return [
        match.group(MARKER_TITLE_GROUP).strip()
        for match in matches
    ]

def extract_section_markers(content: str) -> dict[str, str]:
    """Extract all section markers and their associated headers.
    
    Args:
        content: The document content to analyze
        
    Returns:
        Dictionary mapping section titles to their headers
    """
    markers = {}
    
    # Find all section markers
    marker_matches = re.finditer(SECTION_MARKER_PATTERN, content)
    header_matches = re.finditer(HEADER_PATTERN, content)
    
    # Build marker to header mapping
    for marker in marker_matches:
        marker_title = marker.group(MARKER_TITLE_GROUP).strip()
        marker_pos = marker.start()
        
        # Find the nearest header before this marker
        nearest_header = None
        nearest_distance = float('inf')
        
        for header in header_matches:
            header_pos = header.start()
            distance = marker_pos - header_pos
            
            if 0 <= distance < nearest_distance:
                nearest_distance = distance
                nearest_header = header.group(0).strip()
        
        markers[marker_title] = nearest_header or "No associated header"
    
    return markers