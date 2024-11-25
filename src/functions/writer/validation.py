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

        # Run unified content validation
        # errors.extend(validate_markdown_formatting(content))
        errors.extend(validate_markdown_content(content))

        # Check for broken links and images
        errors.extend(validate_content(file_path))

        # Run pandoc compatibility check
        errors.extend(validate_pandoc_compatibility(file_path))

        return len(errors) == 0, errors

    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        raise WriterError(ERROR_VALIDATION_FAILED.format(error=str(e)))


def validate_file_extension_and_access(file_path: Path):
    """Validate file extension and ensure file is readable."""
    if file_path.suffix != MD_EXTENSION:
        raise WriterError(ERROR_INVALID_FILE_FORMAT)

    if not os.access(file_path, os.R_OK):
        os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR)


def validate_markdown_content(content: str) -> List[str]:
    """
    Unified function to validate task lists, header nesting, and markdown formatting.
    
    Args:
        content: The Markdown file content as a string.
        
    Returns:
        List[str]: A list of validation error messages.
    """
    errors = []
    current_level = 0
    last_header = None
    error_template = ERROR_LINE_MESSAGE + ERROR_SUGGESTION_FORMAT
    in_code_block = False  # Add tracking for code blocks

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
            # 1. Check for missing space after dash (-[ ] instead of - [ ])
            if stripped.startswith("-["):
                errors.append(
                    error_template.format(
                        line=line_num,
                        message=ERROR_TASK_LIST_MISSING_SPACE,
                        suggestion=SUGGESTION_TASK_LIST_FORMAT
                    )
                )
                continue

            # 2. Check for extra spaces after dash (-  [ ] instead of - [ ])
            if stripped.startswith("-  "):
                errors.append(
                    error_template.format(
                        line=line_num,
                        message=ERROR_TASK_LIST_EXTRA_SPACE,
                        suggestion=SUGGESTION_TASK_LIST_FORMAT
                    )
                )

            # 3. Check for invalid marker format (- [] instead of - [ ])
            if "[]" in stripped:
                errors.append(
                    error_template.format(
                        line=line_num,
                        message=ERROR_TASK_LIST_INVALID_MARKER,
                        suggestion=SUGGESTION_TASK_LIST_FORMAT
                    )
                )

            # 4. Check for missing space after brackets (- [ ]text instead of - [ ] text)
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

        # Header Validation
        elif stripped.startswith(SECTION_HEADER_PREFIX):
            # Count the number of # symbols
            level = len(line.split()[0])
            header_text = line.lstrip(SECTION_HEADER_PREFIX).strip()

            # Check for empty headers
            if not header_text:
                errors.append(ERROR_HEADER_EMPTY.format(line=line_num))
                continue

            # Check if header level is valid (1-6)
            if level > 6:
                errors.append(ERROR_HEADER_LEVEL_EXCEEDED.format(
                    line=line_num,
                    level=level
                ))
                continue

            # First header should be level 1
            if last_header is None and level != 1:
                errors.append(ERROR_HEADER_INVALID_START.format(
                    line=line_num,
                    level=level
                ))

            # Check for skipped levels
            if last_header is not None:
                if level > current_level + 1:
                    error_msg = ERROR_HEADER_LEVEL_SKIP.format(
                        line=line_num,
                        current=current_level,
                        level=level
                    )
                    error_msg += "\n" + SUGGESTION_HEADER_LEVEL.format(
                        suggested=SECTION_HEADER_PREFIX * (current_level + 1),
                        current=SECTION_HEADER_PREFIX * level
                    )
                    errors.append(error_msg)

            current_level = level
            last_header = header_text

        # Markdown Formatting Validation
        try:
            mdformat.text(line, options=MDFORMAT_OPTIONS, extensions=MDFORMAT_EXTENSIONS)
        except ValueError as e:
            errors.append(
                ERROR_MARKDOWN_FORMATTING.format(
                    line=line_num,
                    message=str(e)
                )
            )

    # Final header level check
    if current_level == 0:
        errors.append(ERROR_HEADER_INVALID_START.format(line=1, level=0))

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
