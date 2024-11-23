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

def validate_markdown(file_path: Path, config: Optional[WriterConfig] = None) -> ValidationResult:
    """Validate Markdown document structure and syntax."""
    config = get_config(config)
    errors: List[ValidationError] = []
    
    try:
        validate_file(file_path, require_write=False)
        
        with open(file_path, 'r', encoding=config.default_encoding) as f:
            content = f.read()
        
        if not content.strip():
            return ValidationResult(
                is_valid=False,
                errors=[ValidationError(
                    line_number=1,
                    error_type="Document Structure",
                    message="Empty document",
                    suggestion="Add required document content"
                )]
            )
            
        md = MarkdownIt('commonmark', {'html': True})
        
        # Run all validators
        errors.extend(validate_frontmatter(content))
        errors.extend(validate_header_hierarchy(content))
        errors.extend(validate_links(content, md))
        errors.extend(validate_tables(content))
        errors.extend(validate_code_blocks(content))
        
        # Only validate section markers for full document tests
        if "<!-- Section:" in content:  # Only validate if markers are present
            try:
                validate_section_markers(content)
            except WriterError as e:
                errors.append(ValidationError(
                    line_number=1,
                    error_type="Section Marker Error",
                    message=str(e),
                    suggestion="Ensure each header has a matching section marker"
                ))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
        
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        raise WriterError(f"Failed to validate Markdown: {str(e)}")

def validate_frontmatter(content: str) -> List[ValidationError]:
    """Validate YAML frontmatter syntax."""
    errors = []
    if content.startswith(YAML_FRONTMATTER_START):
        try:
            end_pos = content.find(YAML_FRONTMATTER_END)
            if end_pos == -1:
                errors.append(ValidationError(
                    line_number=1,
                    error_type="YAML Frontmatter",
                    message="Unclosed YAML frontmatter block",
                    suggestion="Add closing '---' delimiter"
                ))
                return errors
                
            frontmatter = content[len(YAML_FRONTMATTER_START):end_pos]
            yaml.safe_load(frontmatter)
            
        except yaml.YAMLError as e:
            errors.append(ValidationError(
                line_number=get_yaml_error_line(e),
                error_type="YAML Syntax",
                message=str(e),
                suggestion="Fix YAML syntax in frontmatter"
            ))
    
    return errors

def validate_header_hierarchy(content: str) -> List[ValidationError]:
    """Validate header levels follow proper hierarchy."""
    errors = []
    current_level = 0
    
    for match in re.finditer(PATTERN_HEADER, content, re.MULTILINE):
        header = match.group(0)
        # Count leading '#' characters without modifying the string
        level = 0
        for char in header:
            if char != '#':
                break
            level += 1
        
        # Headers should only increment by one level
        if level > current_level + 1 and current_level > 0:
            line_num = get_line_number(content, match.start())
            errors.append(ValidationError(
                line_number=line_num,
                error_type="Header Hierarchy",
                message=f"Header level jumps from {current_level} to {level}",
                suggestion=f"Use level {current_level + 1} header instead"
            ))
        
        current_level = level
    
    return errors

def validate_links(content: str, md: MarkdownIt) -> List[ValidationError]:
    """Validate links and images in the document."""
    errors = []
    tokens = md.parse(content)
    
    for token in tokens:
        if token.type == 'link_open':
            href = dict(token.attrs).get('href', '')
            line_num = token.map[0] + 1 if token.map else 1
            
            if not href.startswith(('http://', 'https://', '#', '/')):
                errors.append(ValidationError(
                    line_number=line_num,
                    error_type="Broken Link",
                    message=f"Invalid or broken link: {href}",
                    suggestion="Use absolute URLs or valid relative paths"
                ))
        
        elif token.type == 'image':
            src = dict(token.attrs).get('src', '')
            line_num = token.map[0] + 1 if token.map else 1
            
            errors.append(ValidationError(
                line_number=line_num,
                error_type="Image Error",
                message=f"Image not found: {src}",
                suggestion="Ensure image file exists in correct location"
            ))
    
    return errors

def validate_tables(content: str) -> List[ValidationError]:
    """Validate table syntax and structure."""
    errors = []
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line or not line.startswith('|') or not line.endswith('|'):
            continue
            
        # Found potential table header
        if i + 1 >= len(lines):
            continue
            
        header_cols = len([cell for cell in line.split('|')[1:-1] if cell.strip()])
        align_row = lines[i + 1].strip()
        
        # Validate alignment row format
        if not align_row.startswith('|') or not align_row.endswith('|'):
            errors.append(ValidationError(
                line_number=i + 2,
                error_type="Table Format",
                message="Invalid table alignment row",
                suggestion="Use | ---- | format with optional : for alignment"
            ))
            continue
            
        # Validate alignment row cells
        align_cells = [cell.strip() for cell in align_row.split('|')[1:-1]]
        if not all(cell and all(c in ':-' for c in cell) for cell in align_cells):
            errors.append(ValidationError(
                line_number=i + 2,
                error_type="Table Format",
                message="Invalid alignment format",
                suggestion="Use ---- or :---- or ----: or :----:"
            ))
            
        # Check column count matches
        if len(align_cells) != header_cols:
            errors.append(ValidationError(
                line_number=i + 2,
                error_type="Table Structure",
                message=f"Alignment row has {len(align_cells)} columns, expected {header_cols}",
                suggestion="Ensure alignment row matches header column count"
            ))
        
        # Check data rows
        for row_idx in range(i + 2, len(lines)):
            row = lines[row_idx].strip()
            if not row or not row.startswith('|') or not row.endswith('|'):
                break
                
            data_cells = [cell.strip() for cell in row.split('|')[1:-1]]
            if len(data_cells) != header_cols:
                errors.append(ValidationError(
                    line_number=row_idx + 1,
                    error_type="Table Structure",
                    message=f"Row has {len(data_cells)} columns, expected {header_cols}",
                    suggestion="Ensure all rows have same number of columns as header"
                ))
    
    return errors

def validate_code_blocks(content: str) -> List[ValidationError]:
    """Validate code block syntax."""
    errors = []
    lines = content.split('\n')
    in_code_block = False
    block_start_line = 0
    language = ""
    
    for i, line in enumerate(lines):
        if line.startswith('```'):
            if not in_code_block:
                # Opening a code block
                in_code_block = True
                block_start_line = i + 1
                language = line[3:].strip()  # Get language identifier
                if not language:
                    errors.append(ValidationError(
                        line_number=i + 1,
                        error_type="Code Block",
                        message="Missing language identifier",
                        suggestion="Add language after opening ```"
                    ))
            else:
                # Closing a code block
                in_code_block = False
                language = ""
    
    # Check for unclosed block at end of file
    if in_code_block:
        errors.append(ValidationError(
            line_number=block_start_line,
            error_type="Code Block",
            message="Unclosed code block",
            suggestion="Add closing ``` delimiter"
        ))
    
    return errors

def get_line_number(content: str, pos: int) -> int:
    """Get line number for a position in the content."""
    return content.count('\n', 0, pos) + 1

def get_yaml_error_line(error: yaml.YAMLError) -> int:
    """Extract line number from YAML error."""
    if hasattr(error, 'problem_mark'):
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
