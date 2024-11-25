from pathlib import Path
import subprocess
import logging
from typing import Tuple, List, Optional
import re
import mdformat
from mdformat.renderer import MDRenderer
import os
import stat

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
        
        # First validate basic file properties before reading content
        validate_file_extension_and_access(file_path)
        validate_file(file_path)

        # Check for empty files early to avoid unnecessary processing
        if file_path.stat().st_size == 0:
            logger.warning(LOG_EMPTY_FILE_DETECTED)
            return False, [ERROR_EMPTY_FILE]

        errors = []

        # Read file content for validation
        with open(file_path, FILE_MODE_READ, encoding=DEFAULT_ENCODING) as f:
            content = f.read()

        # Validate markdown content structure (headers, task lists, etc)
        errors.extend(validate_markdown_content(content))

        # Check for broken links and images in the content
        errors.extend(validate_content(file_path))

        # Verify pandoc compatibility as final check
        errors.extend(validate_pandoc_compatibility(file_path))

        # Return validation result - valid only if no errors found
        return len(errors) == 0, errors

    except Exception as e:
        error_msg = ERROR_VALIDATION_FAILED.format(error=str(e))
        logger.error(error_msg)
        raise WriterError(error_msg)


def validate_file_extension_and_access(file_path: Path):
    """Validate file extension and ensure file is readable."""
    if file_path.suffix != MD_EXTENSION:
        raise WriterError(ERROR_INVALID_FILE_FORMAT)

    if not os.access(file_path, os.R_OK):
        os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR)


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
                suggestion=SUGGESTION_TASK_LIST_FORMAT
            )
        )
        return errors  # Early return since this is a critical formatting error

    # Check for extra spaces after dash (-  [ ] instead of - [ ])
    if stripped.startswith("-  "):
        errors.append(
            error_template.format(
                line=line_num,
                message=ERROR_TASK_LIST_EXTRA_SPACE,
                suggestion=SUGGESTION_TASK_LIST_FORMAT
            )
        )

    # Validate the task list marker format (must be [ ] or [x])
    if "[]" in stripped:
        errors.append(
            error_template.format(
                line=line_num,
                message=ERROR_TASK_LIST_INVALID_MARKER,
                suggestion=SUGGESTION_TASK_LIST_FORMAT
            )
        )

    # Ensure there's a space after the closing bracket before the task text
    bracket_end = stripped.find("]")
    if bracket_end != -1 and bracket_end + 1 < len(stripped):
        if not stripped[bracket_end + 1:].startswith(" "):
            errors.append(
                error_template.format(
                    line=line_num,
                    message=ERROR_TASK_LIST_MISSING_SPACE_AFTER,
                    suggestion=SUGGESTION_TASK_LIST_FORMAT
                )
            )

    return errors


def validate_header(line: str, line_num: int, current_level: int, last_header: Optional[str]) -> Tuple[List[str], int, Optional[str]]:
    """Validate a header line for proper formatting and nesting."""
    errors = []
    level = get_header_level(line)
    header_text = line.lstrip('#').strip()

    # Validate empty headers first
    if not header_text:
        errors.append(ERROR_HEADER_EMPTY.format(line=line_num))
        return errors, level, None

    # Check if header level exceeds maximum allowed depth (usually 6)
    if level > MAX_HEADER_DEPTH:
        errors.append(ERROR_HEADER_LEVEL_EXCEEDED.format(
            line=line_num,
            level=level
        ))
        return errors, level, None

    # Ensure document starts with h1 header
    if current_level == 0 and level != 1:
        errors.append(ERROR_HEADER_INVALID_START.format(
            line=line_num,
            level=level
        ))

    # Validate header nesting - levels should only increment by 1
    if last_header is not None and level > current_level + 1:
        suggested_level = current_level + 1
        suggested_header = '#' * suggested_level
        errors.append(
            ERROR_HEADER_LEVEL_SKIP.format(
                line=line_num,
                current=current_level,
                level=level
            ) + 
            SUGGESTION_HEADER_LEVEL.format(
                suggested=suggested_header,
                current='#' * level
            )
        )

    return errors, level, header_text


def validate_markdown_content(content: str) -> List[str]:
    """
    Unified function to validate task lists, header nesting, and markdown formatting.
    """
    errors = []
    current_level = 0
    last_header = None
    in_code_block = False

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

        # Task List Validation
        if stripped.startswith("-"):
            errors.extend(validate_task_list(line, line_num))
            continue

        # Header Validation
        if stripped.startswith(SECTION_HEADER_PREFIX):
            header_errors, new_level, new_header = validate_header(
                line, line_num, current_level, last_header
            )
            errors.extend(header_errors)
            current_level = new_level
            last_header = new_header
            continue

        # Markdown Formatting Validation
        try:
            mdformat.text(line, options=MDFORMAT_OPTIONS, extensions=MDFORMAT_EXTENSIONS)
        except ValueError as e:
            errors.append(ERROR_MARKDOWN_FORMATTING.format(
                line=line_num,
                message=str(e)
            ))

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


def is_valid_task_list_marker(text: str) -> bool:
    """Check if the text contains a valid task list marker."""
    return bool(re.match(r'^- \[([ xX])\] ', text))


def get_header_level(text: str) -> int:
    """Get the header level from a line of text."""
    return len(text) - len(text.lstrip('#'))
