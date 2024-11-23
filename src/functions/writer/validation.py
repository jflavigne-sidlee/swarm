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
    """Validate Markdown document structure and syntax.
    
    Args:
        file_path: Path to the Markdown file
        config: Optional configuration settings
        
    Returns:
        ValidationResult containing success status and any validation errors
        
    Raises:
        WriterError: If file validation fails
    """
    config = get_config(config)
    errors: List[ValidationError] = []
    
    try:
        # Validate file exists and is readable
        validate_file(file_path, require_write=False)
        
        # Read file content
        with open(file_path, 'r', encoding=config.default_encoding) as f:
            content = f.read()
            
        # Initialize Markdown parser
        md = MarkdownIt('commonmark', {'html': True})
        
        # Validate YAML frontmatter
        frontmatter_errors = validate_frontmatter(content)
        errors.extend(frontmatter_errors)
        
        # Validate header hierarchy
        header_errors = validate_header_hierarchy(content)
        errors.extend(header_errors)
        
        # Validate section markers (using existing function)
        try:
            validate_section_markers(content)
        except WriterError as e:
            errors.append(ValidationError(
                line_number=get_error_line(content, str(e)),
                error_type="Section Marker Error",
                message=str(e),
                suggestion="Ensure each header has a matching section marker"
            ))
        
        # Validate links and references
        link_errors = validate_links(content, md)
        errors.extend(link_errors)
        
        # Validate tables
        table_errors = validate_tables(content)
        errors.extend(table_errors)
        
        # Validate code blocks
        code_block_errors = validate_code_blocks(content)
        errors.extend(code_block_errors)
        
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
        level = len(header) - len(header.lstrip('#'))
        
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
    """Validate links and image references in the document.
    
    Checks:
    - Link syntax is valid
    - Image references are properly formatted
    - No broken relative links (if path exists)
    """
    errors = []
    
    # Parse document to get tokens
    tokens = md.parse(content)
    
    for token in tokens:
        if token.type == 'link_open':
            # Get link href from attrs
            href = dict(token.attrs).get('href', '')
            line_num = get_line_number(content, token.map[0])
            
            # Validate link syntax
            if not href:
                errors.append(ValidationError(
                    line_number=line_num,
                    error_type="Link Error",
                    message="Empty link reference",
                    suggestion="Add valid URL or path to link"
                ))
            
            # Check relative file paths
            elif not href.startswith(('http://', 'https://', '#', 'mailto:')):
                path = Path(href)
                if not path.exists():
                    errors.append(ValidationError(
                        line_number=line_num,
                        error_type="Broken Link",
                        message=f"Relative link not found: {href}",
                        suggestion="Update path or ensure file exists"
                    ))
                    
        elif token.type == 'image':
            # Get image source
            src = dict(token.attrs).get('src', '')
            line_num = get_line_number(content, token.map[0])
            
            if not src:
                errors.append(ValidationError(
                    line_number=line_num,
                    error_type="Image Error",
                    message="Empty image source",
                    suggestion="Add valid image path or URL"
                ))
            
            # Check relative image paths
            elif not src.startswith(('http://', 'https://')):
                path = Path(src)
                if not path.exists():
                    errors.append(ValidationError(
                        line_number=line_num,
                        error_type="Broken Image",
                        message=f"Image file not found: {src}",
                        suggestion="Update path or ensure image exists"
                    ))
    
    return errors

def validate_tables(content: str) -> List[ValidationError]:
    """Validate table syntax and structure.
    
    Checks:
    - Table has header row
    - Alignment row is properly formatted
    - All rows have same number of columns
    """
    errors = []
    
    # Find table blocks using regex
    table_pattern = r'(\|[^\n]+\|\n\|[-:| ]+\|\n(?:\|[^\n]+\|\n?)*)'
    for match in re.finditer(table_pattern, content, re.MULTILINE):
        table = match.group(0)
        lines = table.strip().split('\n')
        line_num = get_line_number(content, match.start())
        
        if len(lines) < 2:
            errors.append(ValidationError(
                line_number=line_num,
                error_type="Table Error",
                message="Table must have header and alignment rows",
                suggestion="Add header row and alignment row with |---|"
            ))
            continue
            
        # Validate alignment row
        align_row = lines[1]
        if not re.match(r'\|[-:| ]+\|', align_row):
            errors.append(ValidationError(
                line_number=line_num + 1,
                error_type="Table Format",
                message="Invalid table alignment row",
                suggestion="Use only |, -, :, and space characters"
            ))
        
        # Check column count consistency
        header_cols = len([col for col in lines[0].split('|') if col.strip()])
        for i, row in enumerate(lines[2:], start=2):
            cols = len([col for col in row.split('|') if col.strip()])
            if cols != header_cols:
                errors.append(ValidationError(
                    line_number=line_num + i,
                    error_type="Table Structure",
                    message=f"Row has {cols} columns, expected {header_cols}",
                    suggestion="Ensure all rows have same number of columns"
                ))
    
    return errors

def validate_code_blocks(content: str) -> List[ValidationError]:
    """Validate code block syntax and structure.
    
    Checks:
    - Code blocks are properly fenced
    - Language identifiers are present
    - No unclosed code blocks
    """
    errors = []
    
    # Find code blocks
    code_pattern = r'```(\w*)\n(.*?)```'
    open_pattern = r'```\w*\n'
    
    # Check for unclosed code blocks
    open_matches = list(re.finditer(open_pattern, content, re.MULTILINE))
    close_matches = list(re.finditer(r'```\n', content, re.MULTILINE))
    
    if len(open_matches) > len(close_matches):
        # Find the unclosed block
        for open_match in open_matches[len(close_matches):]:
            line_num = get_line_number(content, open_match.start())
            errors.append(ValidationError(
                line_number=line_num,
                error_type="Code Block",
                message="Unclosed code block",
                suggestion="Add closing ``` delimiter"
            ))
    
    # Validate complete code blocks
    for match in re.finditer(code_pattern, content, re.DOTALL):
        line_num = get_line_number(content, match.start())
        language = match.group(1)
        
        if not language:
            errors.append(ValidationError(
                line_number=line_num,
                error_type="Code Block",
                message="Missing language identifier",
                suggestion="Add language after opening ```"
            ))
        
        # Check for common language misspellings
        common_languages = {'python', 'javascript', 'typescript', 'java', 'cpp', 'csharp'}
        if language.lower() not in common_languages and language:
            errors.append(ValidationError(
                line_number=line_num,
                error_type="Code Block",
                message=f"Uncommon language identifier: {language}",
                suggestion="Verify language name is correct"
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
