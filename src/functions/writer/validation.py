from pathlib import Path
import re
from typing import Optional, List, NamedTuple
import logging
from markdown_it import MarkdownIt
import yaml

from .config import WriterConfig
from .exceptions import WriterError
from .file_operations import (
    validate_file,
    get_config,
    validate_section_markers,
)
from .constants import (
    YAML_FRONTMATTER_START,
    YAML_FRONTMATTER_END,
    ERROR_INVALID_MARKDOWN_FILE,
    ERROR_YAML_SERIALIZATION,
    PATTERN_HEADER,
    PATTERN_SECTION_MARKER,
)

logger = logging.getLogger(__name__)


class ValidationError(NamedTuple):
    """Represents a validation error in the Markdown document."""

    line_number: int
    error_type: str
    message: str
    suggestion: str


class ValidationResult(NamedTuple):
    """Result of Markdown validation."""

    is_valid: bool
    errors: List[ValidationError]


def validate_markdown(
    file_path: Path, parser: Optional[MarkdownIt] = None, debug: bool = False
) -> ValidationResult:
    """Validate a markdown file."""
    try:
        config = get_config()
        validate_file(file_path, require_write=False)

        with open(file_path, "r", encoding=config.default_encoding) as f:
            content = f.read()

        if not content.strip():
            return ValidationResult(
                is_valid=False,
                errors=[
                    ValidationError(
                        line_number=1,
                        error_type="Document Structure",
                        message="Empty document",
                        suggestion="Add required document content",
                    )
                ],
            )

        # Single parsing step
        if parser is None:
            parser = (
                MarkdownIt("commonmark").enable("table").enable("link").enable("image")
            )

        tokens = parser.parse(content)

        if debug:
            print("\nToken Summary:")
            token_counts = {}
            for token in tokens:
                if token.type in ["link_open", "image", "heading_open", "fence"]:
                    token_counts[token.type] = token_counts.get(token.type, 0) + 1
                    if token.type in ["link_open", "image"]:
                        attrs = dict(token.attrs) if token.attrs else {}
                        print(f"\n{token.type}:")
                        print(f"  href/src: {attrs.get('href') or attrs.get('src')}")
                        print(f"  line: {token.map[0] + 1 if token.map else 'unknown'}")

            print("\nToken Counts:")
            for token_type, count in token_counts.items():
                print(f"  {token_type}: {count}")

        # Collect all validation errors using parsed tokens
        errors = []
        errors.extend(validate_frontmatter(content))  # Still needs raw content for YAML
        errors.extend(validate_header_hierarchy(content, tokens))  # Update to use tokens
        errors.extend(validate_tables(content, tokens))  # Update to use tokens
        errors.extend(validate_code_blocks(content, tokens))  # Update to use tokens
        errors.extend(
            validate_links(content, tokens, base_path=file_path)
        )  # Already uses tokens

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)

    except Exception as e:
        raise WriterError(f"Validation error: {str(e)}")


def validate_frontmatter(content: str) -> List[ValidationError]:
    """Validate YAML frontmatter syntax."""
    errors = []
    if content.startswith(YAML_FRONTMATTER_START):
        try:
            end_pos = content.find(YAML_FRONTMATTER_END)
            if end_pos == -1:
                errors.append(
                    ValidationError(
                        line_number=1,
                        error_type="YAML Frontmatter",
                        message="Unclosed YAML frontmatter block",
                        suggestion="Add closing '---' delimiter",
                    )
                )
                return errors

            frontmatter = content[len(YAML_FRONTMATTER_START) : end_pos]
            yaml.safe_load(frontmatter)

        except yaml.YAMLError as e:
            errors.append(
                ValidationError(
                    line_number=get_yaml_error_line(e),
                    error_type="YAML Syntax",
                    message=str(e),
                    suggestion="Fix YAML syntax in frontmatter",
                )
            )

    return errors


def validate_header_hierarchy(content: str, tokens: Optional[List[dict]] = None) -> List[ValidationError]:
    """Validate header levels follow proper hierarchy."""
    if tokens is None:
        parser = MarkdownIt("commonmark")
        tokens = parser.parse(content)
    
    errors = []
    current_level = 0
    
    for token in tokens:
        if token.type == "heading_open":
            level = int(token.tag[1])  # h1 -> 1, h2 -> 2, etc.
            if level > current_level + 1 and current_level > 0:
                errors.append(
                    ValidationError(
                        line_number=token.map[0] + 1 if token.map else 0,
                        error_type="Header Hierarchy",
                        message=f"Header level jumps from {current_level} to {level}",
                        suggestion=f"Use level {current_level + 1} header instead",
                    )
                )
            current_level = level
    
    return errors


def validate_links(content: str, tokens: Optional[List[dict]] = None, base_path: Optional[Path] = None) -> List[ValidationError]:
    """Validate links in the markdown content."""
    errors: List[ValidationError] = []
    
    if tokens is None:
        parser = MarkdownIt("commonmark").enable("link").enable("image")
        tokens = parser.parse(content)
    
    for token in tokens:
        if token.type == "inline":
            # Inline tokens contain children with the actual links
            for child in token.children:
                if child.type in ["link_open", "image"]:
                    try:
                        attrs = dict(child.attrs) if hasattr(child, 'attrs') and child.attrs else {}
                        href = attrs.get('href') or attrs.get('src')
                        
                        if href and not href.startswith(('http://', 'https://', '#', 'mailto:')):
                            target_path = base_path.parent / href if base_path else Path(href)
                            
                            if not target_path.exists():
                                errors.append(
                                    ValidationError(
                                        line_number=token.map[0] + 1 if token.map else 0,
                                        error_type="Link",
                                        message=f"Broken link: {href}",
                                        suggestion="Ensure the linked file exists",
                                    )
                                )
                    except Exception as e:
                        continue
    
    return errors


def validate_code_blocks(content: str, tokens: Optional[List[dict]] = None) -> List[ValidationError]:
    """Validate code block syntax."""
    errors: List[ValidationError] = []
    
    if tokens is None:
        parser = MarkdownIt("commonmark")
        tokens = parser.parse(content)

    lines = content.splitlines()
    in_code_block = False
    code_block_start = 0
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('```'):
            if not in_code_block:
                in_code_block = True
                code_block_start = i
                if len(stripped) <= 3:  # No language specified
                    errors.append(
                        ValidationError(
                            line_number=i + 1,
                            error_type="Code Block",
                            message="Missing language identifier",
                            suggestion="Add language after opening ```",
                        )
                    )
            else:
                in_code_block = False
    
    if in_code_block:
        errors.append(
            ValidationError(
                line_number=code_block_start + 1,
                error_type="Code Block",
                message="Unclosed code block",
                suggestion="Add closing ``` to the code block",
            )
        )
    
    return errors


def get_line_number(tokens: List[dict], pos: int) -> int:
    """Get line number for a position in the content."""
    return sum(token.map[1] for token in tokens if token.map[0] < pos) + 1


def get_yaml_error_line(error: yaml.YAMLError) -> int:
    """Extract line number from YAML error."""
    if hasattr(error, "problem_mark"):
        return error.problem_mark.line + 1
    return 1


def get_error_line(content: str, error_message: str) -> int:
    """Extract line number from content based on error message context.

    Args:
        content: The full document content
        error_message: The error message that may contain context

    Returns:
        int: Best guess at the line number where the error occurred

    Example:
        >>> content = "line1\\nline2\\n<!-- Section: Test -->\\nline4"
        >>> msg = "Invalid section marker: Test"
        >>> get_error_line(content, msg)
        3  # Returns the line number where "Test" appears
    """
    # Try to extract any quoted text from error message
    quoted_text = re.findall(r'"([^"]*)"', error_message)

    # If we found quoted text, try to find it in the content
    for text in quoted_text:
        pos = content.find(text)
        if pos != -1:
            return get_line_number(content, pos)

    # If no quoted text or text not found, try to find any section marker reference
    if "section" in error_message.lower():
        marker_match = re.search(PATTERN_SECTION_MARKER, content)
        if marker_match:
            return get_line_number(content, marker_match.start())

    # If we can't determine the specific line, return line 1
    return 1


import re
from typing import List
import logging

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG, format="%(message)s")
logger = logging.getLogger(__name__)


class ValidationError:
    def __init__(
        self, line_number: int, error_type: str, message: str, suggestion: str
    ):
        self.line_number = line_number
        self.error_type = error_type
        self.message = message
        self.suggestion = suggestion

    def __repr__(self):
        return (
            f"ValidationError(line_number={self.line_number}, error_type='{self.error_type}', "
            f"message='{self.message}', suggestion='{self.suggestion}')"
        )


def validate_tables(content: str, tokens: Optional[List[dict]] = None) -> List[ValidationError]:
    """Validate table syntax and structure."""
    errors: List[ValidationError] = []
    
    if tokens is None:
        parser = MarkdownIt("commonmark").enable("table")
        tokens = parser.parse(content)
    
    lines = content.splitlines()
    in_table = False
    table_start_line = 0
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('|') and stripped.endswith('|'):
            if not in_table:
                in_table = True
                table_start_line = i
            elif i == table_start_line + 1:
                # Check alignment row
                if not re.match(r'\|(?:\s*:?-+:?\s*\|)+', stripped):
                    errors.append(
                        ValidationError(
                            line_number=i + 1,
                            error_type="Table Format",
                            message="Missing or invalid alignment row",
                            suggestion="Add alignment row (e.g., | --- | --- |)",
                        )
                    )
        else:
            in_table = False
    
    return errors
