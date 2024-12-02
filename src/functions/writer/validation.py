from pathlib import Path
import subprocess
import logging
from typing import Tuple, List, Optional
import re
from .exceptions import WriterError
from .constants import (
    DEFAULT_ENCODING,
    MD_EXTENSION,
    PANDOC_COMMAND,
    PANDOC_FROM_ARG,
    PANDOC_FROM_FORMAT,
    PANDOC_TO_ARG,
    PANDOC_TO_FORMAT,
    URL_PREFIXES,
)
from .patterns import (
    PATTERN_FILE_LINK,
    PATTERN_IMAGE_LINK,
    PATTERN_HEADER_LEVEL,
    PATTERN_HEADER_TEXT,
    HEADER_LEVEL_RANGE,
    SECTION_HEADER_PREFIX,
)
from .errors import (
    ERROR_BROKEN_FILE,
    ERROR_BROKEN_IMAGE,
    ERROR_EMPTY_FILE,
    ERROR_HEADER_EMPTY,
    ERROR_HEADER_INVALID_START,
    ERROR_HEADER_LEVEL_EXCEEDED,
    ERROR_HEADER_LEVEL_SKIP,
    ERROR_INVALID_FILE_FORMAT,
    ERROR_LINE_MESSAGE,
    ERROR_PANDOC_COMPATIBILITY,
    ERROR_PANDOC_EXECUTION,
    ERROR_PANDOC_LATEX_MATH,
    ERROR_PANDOC_NOT_INSTALLED,
    ERROR_SUGGESTION_FORMAT,
    ERROR_TASK_LIST_EXTRA_SPACE,
    ERROR_TASK_LIST_INVALID_MARKER,
    ERROR_TASK_LIST_MISSING_SPACE,
    ERROR_TASK_LIST_MISSING_SPACE_AFTER,
    ERROR_VALIDATION_FAILED,
    ERROR_MDFORMAT_NOT_INSTALLED,
    ERROR_MDFORMAT_GFM_NOT_INSTALLED,
    ERROR_MARKDOWN_FORMATTING,
)
from .logs import (
    LOG_EMPTY_FILE_DETECTED,
    LOG_FILE_OPERATION_ERROR,   
)
from .suggestions import (
    ERROR_SUGGESTIONS,
    SUGGESTION_HEADER_LEVEL,
    SUGGESTION_TASK_LIST_FORMAT,
)
from .file_io import read_file

logger = logging.getLogger(__name__)


def check_mdformat_availability(gfm: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Check if mdformat and its extensions are available.
    
    Args:
        gfm: Whether to check for GFM extension support
        
    Returns:
        Tuple containing:
            - Boolean indicating if mdformat is available
            - Error message if not available, None otherwise
    """
    try:
        import mdformat
        if gfm:
            try:
                mdformat.text("test", extensions=["gfm"])
            except ValueError:
                return False, ERROR_MDFORMAT_GFM_NOT_INSTALLED
        return True, None
    except ImportError:
        return False, ERROR_MDFORMAT_NOT_INSTALLED


def validate_markdown_formatting(content: str) -> List[str]:
    """
    Validate markdown formatting using mdformat.
    
    Args:
        content: Markdown content to validate
        
    Returns:
        List of formatting errors
    """
    errors = []
    mdformat_available, mdformat_error = check_mdformat_availability()
    gfm_available = None
    
    # Standard markdown validation
    if mdformat_available:
        try:
            import mdformat
            mdformat.text(content)
        except ValueError as e:
            errors.append(ERROR_MARKDOWN_FORMATTING.format(error=str(e)))
    else:
        logger.warning(ERROR_MDFORMAT_NOT_INSTALLED)

    # GFM feature validation
    if "~~" in content or "- [ ]" in content:  # GFM features detected
        if gfm_available is None:
            gfm_available, gfm_error = check_mdformat_availability(gfm=True)
        
        if gfm_available:
            try:
                import mdformat
                mdformat.text(content, extensions=["gfm"])
            except ValueError as e:
                errors.append(ERROR_MARKDOWN_FORMATTING.format(error=str(e)))
        else:
            logger.warning(LOG_FILE_OPERATION_ERROR.format(error=gfm_error))
            
    return errors


def validate_file_basics(file_path: Path) -> Tuple[str, List[str]]:
    """
    Validate basic file properties and read content.
    
    Args:
        file_path: Path to the markdown file
        
    Returns:
        Tuple containing:
            - File content
            - List of validation errors
    """
    errors = []
    
    # Validate file extension
    if file_path.suffix != MD_EXTENSION:
        raise WriterError(ERROR_INVALID_FILE_FORMAT)
        
    # Read and validate content
    content = read_file(file_path, encoding=DEFAULT_ENCODING)
    
    # Check for empty file
    if not content.strip():
        logger.warning(LOG_EMPTY_FILE_DETECTED)
        errors.append(ERROR_EMPTY_FILE)
        
    return content, errors


def validate_markdown(file_name: str) -> Tuple[bool, List[str]]:
    """Validate the Markdown document for syntax and structural issues."""
    try:
        file_path = Path(file_name)
        errors = []
        
        # Basic file validation
        content, basic_errors = validate_file_basics(file_path)
        errors.extend(basic_errors)
        
        # If file is empty, return early
        if not content.strip():
            return False, errors
            
        # Formatting validation
        errors.extend(validate_markdown_formatting(content))
        
        # Content validation
        errors.extend(validate_markdown_content(content))
        errors.extend(validate_content(content, file_path))
        
        # Pandoc compatibility
        errors.extend(validate_pandoc_compatibility(content, file_path))

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

    # Skip early if not a task list line
    if not stripped.startswith('-'):
        return errors

    # Check for specific error cases in order of precedence
    if stripped.startswith('-['):
        errors.append(
            ERROR_LINE_MESSAGE.format(
                line=line_num,
                message=ERROR_TASK_LIST_MISSING_SPACE
            ) + ERROR_SUGGESTION_FORMAT.format(
                suggestion=SUGGESTION_TASK_LIST_FORMAT
            )
        )
    elif stripped.startswith('-  '):
        errors.append(
            ERROR_LINE_MESSAGE.format(
                line=line_num,
                message=ERROR_TASK_LIST_EXTRA_SPACE
            ) + ERROR_SUGGESTION_FORMAT.format(
                suggestion=SUGGESTION_TASK_LIST_FORMAT
            )
        )
    elif re.match(r'^- \[[ xX]\](?!\s)', stripped):
        errors.append(
            ERROR_LINE_MESSAGE.format(
                line=line_num,
                message=ERROR_TASK_LIST_MISSING_SPACE_AFTER
            ) + ERROR_SUGGESTION_FORMAT.format(
                suggestion=SUGGESTION_TASK_LIST_FORMAT
            )
        )
    elif not re.match(r'^- \[[ xX]\] .+$', stripped):
        errors.append(
            ERROR_LINE_MESSAGE.format(
                line=line_num,
                message=ERROR_TASK_LIST_INVALID_MARKER
            ) + ERROR_SUGGESTION_FORMAT.format(
                suggestion=SUGGESTION_TASK_LIST_FORMAT
            )
        )

    return errors


def validate_header(
    line: str, line_num: int, current_level: int, last_header: Optional[str]
) -> Tuple[List[str], int, Optional[str]]:
    """Validate a header line for proper formatting and nesting."""
    errors = []
    level, header_text = extract_header_info(line)

    # Validate empty headers first
    if not header_text:
        errors.append(ERROR_HEADER_EMPTY.format(line=line_num))
        return errors, level, None

    # Check if header level exceeds maximum allowed depth
    max_header_depth = HEADER_LEVEL_RANGE[-1]
    if level > max_header_depth:
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
            suggested_header = SECTION_HEADER_PREFIX * suggested_level
            errors.append(
                ERROR_HEADER_LEVEL_SKIP.format(
                    line=line_num, current=current_level, level=level
                )
                + SUGGESTION_HEADER_LEVEL.format(
                    suggested=suggested_header, current=SECTION_HEADER_PREFIX * level
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
        if stripped.startswith(SECTION_HEADER_PREFIX):
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
        subprocess.run(
            [PANDOC_COMMAND, "--version"],
            capture_output=True,
            check=True,
            text=True
        )

        # Run the actual pandoc conversion
        subprocess.run(
            [
                PANDOC_COMMAND,
                PANDOC_FROM_ARG,
                PANDOC_FROM_FORMAT,
                PANDOC_TO_ARG,
                PANDOC_TO_FORMAT,
            ],
            input=content,
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        if "Error parsing latex math" in getattr(e, 'stderr', ''):
            errors.append(ERROR_PANDOC_LATEX_MATH)
        else:
            errors.append(ERROR_PANDOC_COMPATIBILITY.format(error=e.stderr))
        logger.warning(f"Pandoc validation failed: {e.stderr}")
    except FileNotFoundError:
        logger.warning("Pandoc is not installed or not accessible")
        errors.append(ERROR_PANDOC_NOT_INSTALLED)
    except Exception as e:
        errors.append(ERROR_PANDOC_EXECUTION.format(error=str(e)))
            
    return errors


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
    return len(text) - len(text.lstrip(SECTION_HEADER_PREFIX))


def extract_header_info(line: str) -> Tuple[int, str]:
    """
    Extract header level and text from a markdown header line.
    
    Args:
        line: The line containing the header
        
    Returns:
        Tuple containing:
            - Header level (number of #)
            - Header text (stripped of #s and whitespace)
            
    Example:
        >>> extract_header_info("### My Header")
        (3, "My Header")
    """
    level_match = re.match(PATTERN_HEADER_LEVEL, line)
    if not level_match:
        return 0, ""
        
    level = len(level_match.group())
    text_match = re.match(PATTERN_HEADER_TEXT, line)
    text = text_match.group(1) if text_match else ""
    
    return level, text
