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
)

# Set up module logger
logger = logging.getLogger(__name__)


def validate_filename(file_name: str, config: WriterConfig) -> Path:
    """Validate filename and return full path."""
    if not file_name or not is_valid_filename(file_name):
        logger.warning("Invalid filename rejected: %s", file_name)
        raise WriterError(ERROR_INVALID_FILENAME)

    # Ensure .md extension
    if not file_name.endswith(".md"):
        file_name += ".md"
        logger.debug("Added .md extension: %s", file_name)

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
        logger.warning("Invalid metadata types detected in: %s", metadata)
        raise WriterError(ERROR_INVALID_METADATA_TYPE)

    missing_fields = [field for field in config.metadata_keys if field not in metadata]
    if missing_fields:
        logger.warning("Missing required metadata fields: %s", missing_fields)
        raise WriterError(
            ERROR_MISSING_METADATA.format(fields=", ".join(missing_fields))
        )


def ensure_directory_exists(dir_path: Path) -> None:
    """Create directory if it doesn't exist."""
    try:
        logger.debug("Creating directory: %s", dir_path)
        dir_path.mkdir(parents=True, exist_ok=True)
    except FileExistsError:
        logger.error("Cannot create directory (file exists): %s", dir_path)
        raise WriterError(ERROR_DIR_EXISTS.format(path=dir_path))
    except PermissionError:
        logger.error("Permission denied creating directory: %s", dir_path)
        raise WriterError(ERROR_PERMISSION_DENIED_DIR.format(path=dir_path))
    except OSError as e:
        logger.error("Directory creation error: %s - %s", dir_path, str(e))
        raise WriterError(ERROR_DIR_CREATION.format(error=str(e)))


def write_document(file_path: Path, metadata: Dict[str, str], encoding: str) -> None:
    """Write metadata and frontmatter to file."""
    try:
        logger.debug("Serializing metadata to YAML")
        yaml_content = yaml.dump(metadata, default_flow_style=False, sort_keys=False)

        logger.debug("Writing content to file: %s", file_path)
        with open(file_path, "w", encoding=encoding) as f:
            f.write(YAML_FRONTMATTER_START)
            f.write(yaml_content)
            f.write(YAML_FRONTMATTER_END)

    except yaml.YAMLError as e:
        logger.error("YAML serialization error: %s", str(e))
        raise WriterError(ERROR_YAML_SERIALIZATION.format(error=str(e)))
    except PermissionError:
        logger.error("Permission denied writing file: %s", file_path)
        raise WriterError(ERROR_PERMISSION_DENIED_FILE.format(path=file_path))
    except OSError as e:
        logger.error("File writing error: %s - %s", file_path, str(e))
        raise WriterError(ERROR_FILE_WRITE.format(error=str(e)))


def create_document(
    file_name: str, metadata: Dict[str, str], config: Optional[WriterConfig] = None
) -> Path:
    """Create a new Markdown document with YAML frontmatter metadata."""
    logger.debug("Creating document with filename: %s", file_name)

    # Use default config if none provided
    if config is None:
        config = WriterConfig()
        logger.debug("Using default configuration")

    # Validate inputs
    full_path = validate_filename(file_name, config)
    validate_metadata(metadata, config)

    try:
        # Check if file exists
        try:
            if os.path.exists(str(full_path)):
                logger.warning("File already exists: %s", full_path)
                raise WriterError(ERROR_FILE_EXISTS.format(path=full_path))
        except (OSError, PermissionError) as e:
            logger.error("Permission error checking path: %s - %s", full_path, str(e))
            raise WriterError(ERROR_PERMISSION_DENIED_PATH.format(path=full_path))

        # Create directories if needed
        if config.create_directories:
            ensure_directory_exists(config.drafts_dir)

        # Write document
        write_document(full_path, metadata, config.default_encoding)
        logger.info("Successfully created document: %s", full_path)
        return full_path

    except Exception as e:
        # Clean up if file was partially written
        logger.debug("Exception occurred, cleaning up partial file: %s", full_path)
        cleanup_partial_file(full_path)

        if isinstance(e, WriterError):
            raise

        # Log and re-raise unexpected errors with original type
        logger.error("Unexpected error: %s (%s)", str(e), type(e).__name__)
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
    section_marker = f"<!-- Section: {section_title} -->"
    section_start = existing_content.find(section_marker)

    if section_start == -1:
        logger.error("Section marker not found: %s", section_title)
        raise WriterError(f"Section '{section_title}' marker not found")

    # Find the end of the section (next section marker or EOF)
    next_section = re.search(
        r"<!-- Section: .* -->", existing_content[section_start + len(section_marker) :]
    )
    section_end = (
        next_section.start() + section_start + len(section_marker)
        if next_section
        else len(existing_content)
    )

    # Insert new content before the next section
    updated_content = (
        existing_content[:section_end]
        + f"\n{new_content.strip()}\n"
        + existing_content[section_end:]
    )

    # Write updated content back to file
    with open(file_path, "w", encoding=config.default_encoding) as f:
        f.write(updated_content)


def validate_section_markers(content: str) -> None:
    """
    Validate section markers in the document.

    Args:
        content: Document content to validate

    Raises:
        WriterError: If markers are malformed or misplaced
    """
    logger.debug("Validating section markers...")

    # Find all headers and their markers
    sections = re.finditer(
        r"^(#{1,6})\s+(.+?)\n(<!-- Section: .+? -->)?", content, re.MULTILINE
    )

    for section in sections:
        header_level = len(section.group(1))
        header_title = section.group(2).strip()
        marker = section.group(3)

        if not marker:
            logger.error("Missing marker for header: %s", header_title)
            raise WriterError(f"Header '{header_title}' is missing its section marker")

        expected_marker = f"<!-- Section: {header_title} -->"
        if marker.strip() != expected_marker:
            logger.error(
                "Mismatched marker for header '%s': expected '%s', found '%s'",
                header_title,
                expected_marker,
                marker.strip(),
            )
            raise WriterError(
                f"Section marker for '{header_title}' does not match header title"
            )
