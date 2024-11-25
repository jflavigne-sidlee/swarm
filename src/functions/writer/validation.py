from pathlib import Path
import subprocess
import logging
from typing import Tuple, List, Optional
import re
import os
import stat
import tempfile

from .exceptions import WriterError
from .file_operations import validate_file
from .constants import (
    PANDOC_FROM_FORMAT,
    PANDOC_TO_FORMAT,
    ERROR_SUGGESTIONS,
    FILE_MODE_READ,
    DEFAULT_ENCODING,
    MD_EXTENSION,
    ERROR_MARKDOWN_FORMATTING,
    ERROR_PANDOC_COMPATIBILITY,
    ERROR_CONTENT_VALIDATION,
    ERROR_BROKEN_IMAGE,
    ERROR_BROKEN_FILE,
    LOG_EMPTY_FILE_DETECTED,
    ERROR_EMPTY_FILE,
    ERROR_VALIDATION_FAILED,
    ERROR_RESTORE_PERMISSIONS,
    ERROR_MARKDOWN_VALIDATION,
    ERROR_INVALID_FILE_FORMAT,
    MDFORMAT_OPTIONS,
    MDFORMAT_EXTENSIONS,
    PANDOC_COMMAND,
    PANDOC_FROM_ARG,
    PANDOC_TO_ARG,
    ERROR_LINE_MESSAGE,
    ERROR_SUGGESTION_FORMAT,
    HTTP_PREFIX,
    HTTPS_PREFIX,
    URL_PREFIXES,
    SECTION_HEADER_PREFIX,
    PATTERN_IMAGE_LINK,
    PATTERN_FILE_LINK,
    SUGGESTION_BROKEN_IMAGE,
    SUGGESTION_BROKEN_LINK,
    ERROR_TASK_LIST_INVALID_MARKER,
    SUGGESTION_TASK_LIST_FORMAT,
    ERROR_HEADER_EMPTY,
    ERROR_HEADER_LEVEL_EXCEEDED,
    ERROR_HEADER_INVALID_START,
    ERROR_HEADER_LEVEL_SKIP,
    SUGGESTION_HEADER_LEVEL,
    ERROR_TASK_LIST_MISSING_SPACE,
    ERROR_TASK_LIST_EXTRA_SPACE,
    ERROR_TASK_LIST_MISSING_SPACE_AFTER,
    MAX_HEADER_DEPTH,
    SECTION_HEADER_PREFIX,
    ERROR_PANDOC_MISSING,
    ERROR_PANDOC_EXECUTION,
)
from .file_io import read_file, write_file, atomic_write, validate_path_permissions, ensure_file_readable

logger = logging.getLogger(__name__)


def validate_markdown(file_name: str) -> Tuple[bool, List[str]]:
    """Validate the Markdown document for syntax and structural issues."""
    try:
        file_path = Path(file_name)

        # First validate file extension before checking existence
        if file_path.suffix != MD_EXTENSION:
            raise WriterError(ERROR_INVALID_FILE_FORMAT)

        # Then validate file properties and permissions
        ensure_file_readable(file_path)
        validate_file(file_path)

        # Check for empty files early
        if file_path.stat().st_size == 0:
            logger.warning(LOG_EMPTY_FILE_DETECTED)
            return False, [ERROR_EMPTY_FILE]

        # Read file content using file_io utility with default encoding
        content = read_file(file_path, encoding=DEFAULT_ENCODING)

        errors = []
        try:
            # Validate markdown formatting using mdformat
            try:
                import mdformat

                mdformat.text(content)
            except ValueError as e:
                errors.append(f"Markdown formatting error: {str(e)}")
            except ImportError:
                logger.warning("mdformat not installed, skipping format validation")

            # Validate GFM features
            try:
                if "~~" in content:  # Strikethrough validation
                    import mdformat

                    mdformat.text(content, extensions=["gfm"])
            except ValueError as e:
                errors.append(f"GFM validation error: {str(e)}")
            except ImportError:
                logger.warning("mdformat-gfm not installed, skipping GFM validation")

            # Add other validations
            errors.extend(validate_markdown_content(content))
            errors.extend(validate_content(content, file_path))
            errors.extend(validate_pandoc_compatibility(content, file_path))

        except subprocess.CalledProcessError as e:
            errors.append(ERROR_PANDOC_COMPATIBILITY.format(error=e.stderr))
            logger.warning(f"Pandoc validation failed: {e.stderr}")

        return len(errors) == 0, errors

    except Exception as e:
        error_msg = ERROR_VALIDATION_FAILED.format(error=str(e))
        logger.error(error_msg)
        raise WriterError(error_msg)


def validate_task_list(line: str, line_num: int) -> List[str]:
    """
    Validate a task list line for proper formatting.

    Args:
        line: The line content to validate
        line_num: The line number for error reporting

    Returns:
        List[str]: List of validation errors for this line
    """
    errors = []
    stripped = line.strip()
    error_template = ERROR_LINE_MESSAGE + ERROR_SUGGESTION_FORMAT

    # Check for missing space between dash and bracket (-[ ] instead of - [ ])
    if stripped.startswith("-["):
        errors.append(
            error_template.format(
                line=line_num,
                message=ERROR_TASK_LIST_MISSING_SPACE,
                suggestion=SUGGESTION_TASK_LIST_FORMAT,
            )
        )
        return errors  # Early return since this is a critical formatting error

    # Check for extra spaces after dash (-  [ ] instead of - [ ])
    if stripped.startswith("-  "):
        errors.append(
            error_template.format(
                line=line_num,
                message=ERROR_TASK_LIST_EXTRA_SPACE,
                suggestion=SUGGESTION_TASK_LIST_FORMAT,
            )
        )

    # Validate the task list marker format (must be [ ] or [x])
    if "[]" in stripped:
        errors.append(
            error_template.format(
                line=line_num,
                message=ERROR_TASK_LIST_INVALID_MARKER,
                suggestion=SUGGESTION_TASK_LIST_FORMAT,
            )
        )

    # Ensure there's a space after the closing bracket before the task text
    bracket_end = stripped.find("]")
    if bracket_end != -1 and bracket_end + 1 < len(stripped):
        if not stripped[bracket_end + 1 :].startswith(" "):
            errors.append(
                error_template.format(
                    line=line_num,
                    message=ERROR_TASK_LIST_MISSING_SPACE_AFTER,
                    suggestion=SUGGESTION_TASK_LIST_FORMAT,
                )
            )

    return errors


def validate_header(
    line: str, line_num: int, current_level: int, last_header: Optional[str]
) -> Tuple[List[str], int, Optional[str]]:
    """Validate a header line for proper formatting and nesting."""
    errors = []
    level = len(re.match(r"^#+", line).group())  # Count leading #s
    header_text = line.lstrip("#").strip()

    # Validate empty headers first
    if not header_text:
        errors.append(ERROR_HEADER_EMPTY.format(line=line_num))
        return errors, level, None

    # Check if header level exceeds maximum allowed depth
    if level > MAX_HEADER_DEPTH:
        errors.append(ERROR_HEADER_LEVEL_EXCEEDED.format(line=line_num, level=level))
        return errors, level, None

    # Validate that document starts with h1
    if current_level == 0 and level != 1:
        errors.append(ERROR_HEADER_INVALID_START.format(line=line_num, level=level))
        return errors, level, None

    # Only validate header nesting if this isn't the first header
    if current_level > 0:
        # Headers should only increment by 1 level at a time
        if level > current_level + 1:
            suggested_level = current_level + 1
            suggested_header = "#" * suggested_level
            errors.append(
                ERROR_HEADER_LEVEL_SKIP.format(
                    line=line_num, current=current_level, level=level
                )
                + SUGGESTION_HEADER_LEVEL.format(
                    suggested=suggested_header, current="#" * level
                )
            )

    return errors, level, header_text


def validate_markdown_content(content: str) -> List[str]:
    """Validate markdown content for proper formatting."""
    errors = []
    current_level = 0
    last_header = None
    in_code_block = False
    first_header_found = False

    for line_num, line in enumerate(content.splitlines(), 1):
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            continue

        # Track code blocks to avoid validating their content
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue

        # Skip validation inside code blocks
        if in_code_block:
            continue

        # Header validation
        if stripped.startswith("#"):
            header_errors, level, header_text = validate_header(
                stripped, line_num, current_level, last_header
            )
            errors.extend(header_errors)
            if not header_errors:  # Only update tracking if header was valid
                if not first_header_found:
                    first_header_found = True
                    if level != 1:
                        errors.append(
                            ERROR_HEADER_INVALID_START.format(
                                line=line_num, level=level
                            )
                        )
                current_level = level
                last_header = header_text

        # Task list validation
        elif stripped.startswith("-"):
            errors.extend(validate_task_list(stripped, line_num))

    return errors


def check_pandoc_installation() -> bool:
    """Check if Pandoc is installed and accessible.

    Returns:
        bool: True if Pandoc is installed and accessible, False otherwise
    """
    try:
        # Try to execute pandoc --version to check installation
        result = subprocess.run(
            [PANDOC_COMMAND, "--version"],
            capture_output=True,
            text=True,
            check=False,  # Don't raise exception on non-zero exit
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def validate_pandoc_compatibility(content: str, file_path: Path) -> List[str]:
    """Run pandoc compatibility check using content string."""
    errors = []

    try:
        # Check if pandoc is installed
        subprocess.run([PANDOC_COMMAND, "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("Pandoc is not installed or not accessible")

    try:
        # Use a temporary file for pandoc processing
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as temp_file:
            temp_file.write(content)
            temp_file.flush()

            try:
                result = subprocess.run(
                    [
                        PANDOC_COMMAND,
                        PANDOC_FROM_ARG,
                        PANDOC_FROM_FORMAT,
                        PANDOC_TO_ARG,
                        PANDOC_TO_FORMAT,
                        temp_file.name,
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                # Check if the error is related to latex math
                if "Error parsing latex math" in e.stderr:
                    errors.append(
                        "Pandoc compatibility error: Error parsing latex math"
                    )
                else:
                    errors.append(ERROR_PANDOC_COMPATIBILITY.format(error=e.stderr))
                logger.warning(f"Pandoc validation failed: {e.stderr}")
    except Exception as e:
        if (
            isinstance(e, subprocess.CalledProcessError)
            and "Error parsing latex math" in e.stderr
        ):
            errors.append("Pandoc compatibility error: Error parsing latex math")
        else:
            errors.append(ERROR_PANDOC_EXECUTION.format(error=str(e)))
    finally:
        try:
            os.unlink(temp_file.name)
        except:
            pass

    return errors


def restore_file_permissions(file_path: Path):
    """Restore reasonable file permissions."""
    try:
        os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
    except Exception:
        pass


def parse_remark_errors(error_output: str) -> List[str]:
    """Parse remark-lint error output into readable messages with suggestions."""
    errors = []
    for line in error_output.splitlines():
        if not line.strip():  # Skip empty lines
            continue

        if ":" in line:
            parts = line.split(":", 2)
            if len(parts) >= 3:
                line_num = parts[1].strip()
                message = parts[2].strip()
                error_msg = ERROR_LINE_MESSAGE.format(line=line_num, message=message)

                # Add suggestion if available
                for rule, suggestion in ERROR_SUGGESTIONS.items():
                    if rule.lower() in message.lower():
                        error_msg += ERROR_SUGGESTION_FORMAT.format(
                            suggestion=ERROR_SUGGESTIONS[rule]
                        )
                        break

                errors.append(error_msg)
    return errors


def parse_markdownlint_errors(error_output: str) -> List[str]:
    """Parse markdownlint error output into readable messages with suggestions."""
    errors = []
    for line in error_output.splitlines():
        if not line.strip():  # Skip empty lines
            continue

        if ":" in line:
            match = re.match(r".*:(\d+):\s*(MD\d+)\s*(.+)", line)
            if match:
                line_num = match.group(1)
                rule = match.group(2)
                message = match.group(3)
                # Keep the rule ID in the error message
                error_msg = ERROR_LINE_MESSAGE.format(line=line_num, message=message)

                # Add suggestion if available
                if rule in ERROR_SUGGESTIONS:
                    error_msg += ERROR_SUGGESTION_FORMAT.format(
                        suggestion=ERROR_SUGGESTIONS[rule]
                    )

                errors.append(error_msg)
    return errors


def is_valid_link(link_path: str, file_path: Path) -> bool:
    """
    Validate if a link (image or file) is accessible.

    Args:
        link_path: The path to the linked resource
        file_path: The path to the markdown file containing the link

    Returns:
        bool: True if the link is valid, False otherwise
    """
    # Handle web URLs
    if link_path.startswith(URL_PREFIXES):
        return True  # Skip validation of external URLs

    try:
        # Convert relative path to absolute
        if not link_path.startswith("/"):
            link_path = str(file_path.parent / link_path)

        # Check if file exists and is accessible
        return Path(link_path).exists()
    except Exception:
        return False


def validate_content(content: str, file_path: Path) -> List[str]:
    """Validate content for broken links and images."""
    errors = []

    # Extract all image and file links from content
    image_links = re.findall(PATTERN_IMAGE_LINK, content)
    file_links = re.findall(PATTERN_FILE_LINK, content)

    # Validate image links
    for _, image_path in image_links:
        if not is_valid_link(image_path, file_path):
            errors.append(ERROR_BROKEN_IMAGE.format(path=image_path))

    # Validate file links
    for _, link_path in file_links:
        if not is_valid_link(link_path, file_path):
            errors.append(ERROR_BROKEN_FILE.format(path=link_path))

    return errors


def is_valid_task_list_marker(text: str) -> bool:
    """Check if the text contains a valid task list marker."""
    return bool(re.match(r"^- \[([ xX])\] ", text))


def get_header_level(text: str) -> int:
    """Get the header level from a line of text."""
    return len(text) - len(text.lstrip("#"))
