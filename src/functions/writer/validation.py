from pathlib import Path
import subprocess
import logging
from typing import Tuple, List
import re
import mdformat
from mdformat.renderer import MDRenderer
import os
import stat

from .exceptions import WriterError
from .file_operations import validate_file
from .constants import (
    MARKDOWNLINT_CONFIG_FILE,
    PANDOC_FROM_FORMAT,
    PANDOC_TO_FORMAT,
    ERROR_REMARK_VALIDATION,
    ERROR_MARKDOWNLINT_VALIDATION,
    ERROR_PANDOC_VALIDATION,
    ERROR_SUGGESTIONS,
    FILE_MODE_READ,
    DEFAULT_ENCODING,
    MD_EXTENSION,
    ERROR_MESSAGES,
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
)

logger = logging.getLogger(__name__)


def validate_markdown(file_name: str) -> Tuple[bool, List[str]]:
    """Validate the Markdown document for syntax and structural issues.

    Args:
        file_name: The name of the Markdown file to validate

    Returns:
        Tuple containing:
            - bool: True if document is valid, False otherwise
            - List[str]: List of validation errors if any

    Raises:
        WriterError: If file validation fails or external tools cannot be executed
    """
    try:
        file_path = Path(file_name)

        # Validate file extension and readability
        validate_file_extension_and_access(file_path)

        validate_file(file_path)

        if file_path.stat().st_size == 0:
            logger.warning(LOG_EMPTY_FILE_DETECTED)
            return False, [ERROR_EMPTY_FILE]

        errors = []

        with open(file_path, FILE_MODE_READ, encoding=DEFAULT_ENCODING) as f:
            content = f.read()

        # Validate GFM task lists
        errors.extend(validate_gfm_task_lists(content))

        # Validate markdown formatting with GFM support
        errors.extend(validate_markdown_formatting(content))

        # Check for broken links and images
        errors.extend(validate_content(file_path))

        # Run pandoc compatibility check
        errors.extend(validate_pandoc_compatibility(file_path))

        # Add header nesting validation
        errors.extend(validate_header_nesting(content))

        return len(errors) == 0, errors

    except Exception as e:
        logger.error(ERROR_VALIDATION_FAILED.format(error=str(e)))
        raise WriterError(ERROR_MARKDOWN_VALIDATION.format(error=str(e)))
    finally:
        # Ensure we restore reasonable permissions
        try:
            restore_file_permissions(file_path)
        except Exception as e:
            logger.error(ERROR_RESTORE_PERMISSIONS.format(error=str(e)))


def validate_file_extension_and_access(file_path: Path):
    """Validate file extension and ensure file is readable."""
    if file_path.suffix != MD_EXTENSION:
        raise WriterError(ERROR_INVALID_FILE_FORMAT)

    if not os.access(file_path, os.R_OK):
        os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR)


def validate_markdown_formatting(content: str) -> List[str]:
    """Validate markdown formatting with GFM support."""
    errors = []
    try:
        mdformat.text(
            content,
            options=MDFORMAT_OPTIONS,
            extensions=MDFORMAT_EXTENSIONS,
        )
    except ValueError as e:
        errors.append(ERROR_MARKDOWN_FORMATTING.format(error=str(e)))
    return errors


def validate_pandoc_compatibility(file_path: Path) -> List[str]:
    """Run pandoc compatibility check."""
    errors = []
    try:
        result = subprocess.run(
            [
                PANDOC_COMMAND,
                PANDOC_FROM_ARG,
                PANDOC_FROM_FORMAT,
                PANDOC_TO_ARG,
                PANDOC_TO_FORMAT,
                str(file_path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        errors.append(ERROR_PANDOC_COMPATIBILITY.format(error=e.stderr))
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
                        error_msg += ERROR_SUGGESTION_FORMAT.format(suggestion=ERROR_SUGGESTIONS[rule])
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
                    error_msg += ERROR_SUGGESTION_FORMAT.format(suggestion=ERROR_SUGGESTIONS[rule])

                errors.append(error_msg)
    return errors


def validate_content(file_path: Path) -> List[str]:
    """Validate document content for broken links and images."""
    errors = []
    try:
        with open(file_path, FILE_MODE_READ, encoding=DEFAULT_ENCODING) as f:
            content = f.read()

        validated_paths = set()

        # Check for broken image links
        image_links = re.finditer(PATTERN_IMAGE_LINK, content)
        for match in image_links:
            image_path = match.group(2)
            if not image_path.startswith(URL_PREFIXES):
                if not (file_path.parent / image_path).exists():
                    error_msg = ERROR_BROKEN_IMAGE.format(path=image_path)
                    error_msg += ERROR_SUGGESTION_FORMAT.format(suggestion=SUGGESTION_BROKEN_IMAGE)
                    errors.append(error_msg)
                validated_paths.add(image_path)

        # Check for broken local file links
        file_links = re.finditer(PATTERN_FILE_LINK, content)
        for match in file_links:
            link_path = match.group(2)
            if link_path not in validated_paths and not link_path.startswith(
                (HTTP_PREFIX, HTTPS_PREFIX, SECTION_HEADER_PREFIX)
            ):
                if not (file_path.parent / link_path).exists():
                    error_msg = ERROR_BROKEN_FILE.format(path=link_path)
                    error_msg += ERROR_SUGGESTION_FORMAT.format(suggestion=SUGGESTION_BROKEN_LINK)
                    errors.append(error_msg)

    except Exception as e:
        errors.append(ERROR_CONTENT_VALIDATION.format(error=str(e)))

    return errors


def validate_gfm_task_lists(content: str) -> List[str]:
    """Validate GitHub-Flavored Markdown task lists."""
    errors = []
    line_number = 0
    error_template = "Line {}: {}\nSuggestion: {}"

    for line in content.splitlines():
        line_number += 1
        stripped = line.lstrip()

        # Skip non-task list lines
        if not stripped.startswith("-"):
            continue

        # 1. Check for missing space after dash (-[ ] instead of - [ ])
        if stripped.startswith("-["):
            errors.append(
                error_template.format(
                    line_number,
                    ERROR_MESSAGES["invalid_marker"],
                    ERROR_SUGGESTIONS["task-list-marker"],
                )
            )
            continue

        # 2. Check for extra spaces after dash (-  [ ] instead of - [ ])
        if stripped.startswith("-  "):
            errors.append(
                error_template.format(
                    line_number,
                    ERROR_MESSAGES["invalid_marker"],
                    ERROR_SUGGESTIONS["task-list-marker"],
                )
            )

        # 3. Check for invalid marker format (- [] instead of - [ ])
        if "[]" in stripped:
            errors.append(
                error_template.format(
                    line_number,
                    ERROR_MESSAGES["invalid_marker"],
                    ERROR_SUGGESTIONS["task-list-marker"],
                )
            )

        # 4. Check for missing space after brackets (- [ ]text instead of - [ ] text)
        bracket_end = stripped.find("]")
        if bracket_end != -1 and bracket_end + 1 < len(stripped):
            if not stripped[bracket_end + 1 :].startswith(" "):
                errors.append(
                    error_template.format(
                        line_number,
                        ERROR_MESSAGES["invalid_marker"],
                        ERROR_SUGGESTIONS["task-list-marker"],
                    )
                )

    return errors


def validate_header_nesting(content: str) -> List[str]:
    """Validate header nesting and increments in markdown content."""
    errors = []
    current_level = 0
    last_header = None

    for line_num, line in enumerate(content.splitlines(), 1):
        if line.strip().startswith("#"):
            # Count the number of # symbols
            level = len(line.split()[0])
            header_text = line.lstrip("#").strip()

            # Check for empty headers
            if not header_text:
                errors.append(
                    f"Line {line_num}: Empty header detected. Headers must contain text."
                )
                continue

            # Check if header level is valid (1-6)
            if level > 6:
                errors.append(
                    f"Line {line_num}: Header level {level} exceeds maximum allowed level of 6"
                )
                continue

            # First header should be level 1
            if last_header is None and level != 1:
                errors.append(
                    f"Line {line_num}: Document should start with a level 1 header (found level {level})"
                )

            # Check for skipped levels
            if last_header is not None:
                if level > current_level + 1:
                    errors.append(
                        f"Line {line_num}: Header level jumps from {current_level} to {level}. "
                        f"Headers should increment by only one level at a time.\n"
                        f"Suggestion: Use {'#' * (current_level + 1)} instead of {'#' * level}"
                    )

            current_level = level
            last_header = header_text

    return errors
