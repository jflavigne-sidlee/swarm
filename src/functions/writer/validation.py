from pathlib import Path
import subprocess
import logging
from typing import Tuple, List
import re
import mdformat
from mdformat.renderer import MDRenderer

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
)

logger = logging.getLogger(__name__)

ERROR_MESSAGES = {
    'invalid_spacing': 'Invalid spacing in task list marker',
    'invalid_marker': 'Invalid task list marker',
    'invalid_format': 'Invalid task list format'
}

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
        
        # Validate file extension
        if file_path.suffix != '.md':
            raise WriterError("Invalid file format: File must have .md extension")
            
        validate_file(file_path)
        
        if file_path.stat().st_size == 0:
            logger.warning("Empty markdown file detected")
            return False, ["File is empty"]
            
        errors = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Validate GFM task lists
        errors.extend(validate_gfm_task_lists(content))
        
        # Validate markdown formatting with GFM support
        try:
            mdformat.text(
                content,
                options={
                    "check": True,
                    "number": True,
                    "wrap": "no"
                },
                extensions=["gfm", "tables"]
            )
        except ValueError as e:
            errors.append(f"Markdown formatting error: {str(e)}")
            
        # Check for broken links and images
        content_errors = validate_content(file_path)
        errors.extend(content_errors)
        
        # Run pandoc compatibility check
        try:
            result = subprocess.run(
                ['pandoc', '--from', PANDOC_FROM_FORMAT, '--to', PANDOC_TO_FORMAT,
                 str(file_path)],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode != 0:
                errors.append(f"Pandoc compatibility error: {result.stderr}")
                return False, errors  # Return immediately on pandoc error
        except subprocess.CalledProcessError as e:
            errors.append(f"Pandoc compatibility error: {str(e)}")
            return False, errors  # Return immediately on pandoc error
            
        return len(errors) == 0, errors
        
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        raise WriterError(f"Failed to validate markdown: {str(e)}")

def parse_remark_errors(error_output: str) -> List[str]:
    """Parse remark-lint error output into readable messages with suggestions."""
    errors = []
    for line in error_output.splitlines():
        if not line.strip():  # Skip empty lines
            continue
            
        if ':' in line:
            parts = line.split(':', 2)
            if len(parts) >= 3:
                line_num = parts[1].strip()
                message = parts[2].strip()
                error_msg = f"Line {line_num}: {message}"
                
                # Add suggestion if available
                for rule, suggestion in ERROR_SUGGESTIONS.items():
                    if rule.lower() in message.lower():
                        error_msg += f"\nSuggestion: {suggestion}"
                        break
                        
                errors.append(error_msg)
    return errors

def parse_markdownlint_errors(error_output: str) -> List[str]:
    """Parse markdownlint error output into readable messages with suggestions."""
    errors = []
    for line in error_output.splitlines():
        if not line.strip():  # Skip empty lines
            continue
            
        if ':' in line:
            match = re.match(r'.*:(\d+):\s*(MD\d+)\s*(.+)', line)
            if match:
                line_num = match.group(1)
                rule = match.group(2)
                message = match.group(3)
                # Keep the rule ID in the error message
                error_msg = f"Line {line_num}: {rule} {message}"
                
                # Add suggestion if available
                if rule in ERROR_SUGGESTIONS:
                    error_msg += f"\nSuggestion: {ERROR_SUGGESTIONS[rule]}"
                    
                errors.append(error_msg)
    return errors

def validate_content(file_path: Path) -> List[str]:
    """Validate document content for broken links and images."""
    errors = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        validated_paths = set()
            
        # Check for broken image links
        image_links = re.finditer(r'!\[([^\]]*)\]\(([^)]+)\)', content)
        for match in image_links:
            image_path = match.group(2)
            if not image_path.startswith(('http://', 'https://')):
                if not (file_path.parent / image_path).exists():
                    error_msg = f"Broken image link: {image_path}"
                    error_msg += f"\nSuggestion: {ERROR_SUGGESTIONS['broken_image']}"
                    errors.append(error_msg)
                validated_paths.add(image_path)
                
        # Check for broken local file links
        file_links = re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', content)
        for match in file_links:
            link_path = match.group(2)
            if (link_path not in validated_paths and 
                not link_path.startswith(('http://', 'https://', '#'))):
                if not (file_path.parent / link_path).exists():
                    error_msg = f"Broken file link: {link_path}"
                    error_msg += f"\nSuggestion: {ERROR_SUGGESTIONS['broken_link']}"
                    errors.append(error_msg)
                    
    except Exception as e:
        errors.append(f"Content validation error: {str(e)}")
        
    return errors

def validate_gfm_task_lists(content: str) -> List[str]:
    """Validate GitHub-Flavored Markdown task lists."""
    errors = []
    line_number = 0
    
    print("\n=== Approach 1: Pattern-based Validation ===")
    # First approach: Pattern-based validation
    valid_pattern = re.compile(r'^(\s*)-\s+\[([ xX])\](\s+.*)?$')
    empty_brackets_pattern = re.compile(r'-\s+\[\]')
    
    for line in content.splitlines():
        line_number += 1
        print(f"\nLine {line_number}: '{line}'")
        
        if empty_brackets_pattern.search(line):
            print(f"  A1: Empty brackets detected")
            error_msg = f"Line {line_number}: {ERROR_MESSAGES['invalid_spacing']}"
            error_msg += f"\nSuggestion: {ERROR_SUGGESTIONS['task-list-marker']}"
            errors.append(error_msg)
            continue
            
        if valid_pattern.match(line):
            print(f"  A1: Valid task list")
            continue
            
        if re.search(r'-.*\[.*\]', line):
            print(f"  A1: Invalid task list format")
            error_msg = f"Line {line_number}: {ERROR_MESSAGES['invalid_format']}"
            error_msg += f"\nSuggestion: {ERROR_SUGGESTIONS['task-list-marker']}"
            errors.append(error_msg)
    
    print("\n=== Approach 2: Component-based Validation ===")
    # Second approach: Component-based validation
    line_number = 0
    for line in content.splitlines():
        line_number += 1
        print(f"\nLine {line_number}: '{line}'")
        
        # Skip non-task-list lines
        if not line.strip().startswith('-'):
            print(f"  A2: Not a list item")
            continue
            
        parts = line.strip().split('[', 1)
        if len(parts) != 2:
            print(f"  A2: No opening bracket")
            continue
            
        prefix, rest = parts
        if not prefix.strip() == '-':
            print(f"  A2: Invalid prefix: '{prefix.strip()}'")
            errors.append(f"Line {line_number}: {ERROR_MESSAGES['invalid_marker']}")
            continue
            
        if not ']' in rest:
            print(f"  A2: No closing bracket")
            errors.append(f"Line {line_number}: {ERROR_MESSAGES['invalid_marker']}")
            continue
            
        marker = rest.split(']')[0]
        if marker not in [' ', 'x', 'X']:
            print(f"  A2: Invalid marker: '{marker}'")
            errors.append(f"Line {line_number}: {ERROR_MESSAGES['invalid_marker']}")

    print("\n=== Approach 3: State Machine Validation ===")
    # Third approach: State machine validation
    line_number = 0
    for line in content.splitlines():
        line_number += 1
        print(f"\nLine {line_number}: '{line}'")
        
        state = 'START'
        char_pos = 0
        chars = list(line.strip())
        
        while char_pos < len(chars) and state != 'ERROR':
            char = chars[char_pos]
            
            if state == 'START':
                if char == '-':
                    state = 'DASH'
                else:
                    state = 'ERROR'
                    
            elif state == 'DASH':
                if char.isspace():
                    state = 'SPACE_AFTER_DASH'
                else:
                    state = 'ERROR'
                    
            elif state == 'SPACE_AFTER_DASH':
                if char == '[':
                    state = 'OPEN_BRACKET'
                else:
                    state = 'ERROR'
                    
            elif state == 'OPEN_BRACKET':
                if char in [' ', 'x', 'X']:
                    state = 'VALID_MARKER'
                else:
                    state = 'ERROR'
                    
            elif state == 'VALID_MARKER':
                if char == ']':
                    state = 'CLOSED_BRACKET'
                else:
                    state = 'ERROR'
                    
            char_pos += 1
            
        print(f"  A3: Final state: {state}")
        if state != 'CLOSED_BRACKET' and re.search(r'-.*\[.*\]', line):
            print(f"  A3: Invalid task list detected")
            errors.append(f"Line {line_number}: {ERROR_MESSAGES['invalid_marker']}")
    
    print("\n=== Approach 4: Position Scanning with Context ===")
    line_number = 0
    for line in content.splitlines():
        line_number += 1
        print(f"\nLine {line_number}: '{line}'")
        
        # Skip non-list lines early
        if '-' not in line:
            print(f"  A4: No dash found")
            continue
            
        # Find all dash positions and validate their context
        positions = []
        for i, char in enumerate(line):
            if char == '-':
                positions.append(i)
                
        for pos in positions:
            print(f"  A4: Checking dash at position {pos}")
            
            # Look behind: should be start of line or newline
            if pos > 0 and not line[pos-1].isspace():
                print(f"  A4: Invalid spacing before dash")
                errors.append(f"Line {line_number}: {ERROR_MESSAGES['invalid_spacing']}")
                continue
                
            # Look ahead: validate the task list structure
            try:
                # Check space after dash
                if not line[pos+1].isspace():
                    print(f"  A4: No space after dash")
                    errors.append(f"Line {line_number}: {ERROR_MESSAGES['invalid_marker']}")
                    continue
                    
                # Find opening bracket
                bracket_pos = line.find('[', pos)
                if bracket_pos == -1 or not all(c.isspace() for c in line[pos+1:bracket_pos]):
                    print(f"  A4: Invalid content before bracket")
                    continue
                    
                # Check marker character
                marker_pos = bracket_pos + 1
                if marker_pos >= len(line) or line[marker_pos] not in ' xX':
                    print(f"  A4: Invalid marker character")
                    errors.append(f"Line {line_number}: {ERROR_MESSAGES['invalid_marker']}")
                    continue
                    
                # Check closing bracket
                if marker_pos + 1 >= len(line) or line[marker_pos + 1] != ']':
                    print(f"  A4: Missing or misplaced closing bracket")
                    errors.append(f"Line {line_number}: {ERROR_MESSAGES['invalid_marker']}")
                    continue
                    
                print(f"  A4: Valid task list item found")
                
            except IndexError:
                print(f"  A4: Incomplete task list structure")
                errors.append(f"Line {line_number}: {ERROR_MESSAGES['invalid_marker']}")
    
    print("\n=== Approach 5: Token-based Parser ===")
    line_number = 0
    for line in content.splitlines():
        line_number += 1
        print(f"\nLine {line_number}: '{line}'")
        
        # Skip non-task lines early
        if not line.strip().startswith('-'):
            print(f"  A5: Not a task line")
            continue
            
        # Tokenize the line
        tokens = []
        current_token = ''
        in_brackets = False
        
        for char in line:
            if char == '[':
                if in_brackets:
                    print(f"  A5: Nested brackets not allowed")
                    tokens.append('ERROR')
                    break
                in_brackets = True
                if current_token:
                    tokens.append(current_token)
                current_token = '['
            elif char == ']':
                if not in_brackets:
                    print(f"  A5: Closing bracket without opening")
                    tokens.append('ERROR')
                    break
                in_brackets = False
                current_token += char
                tokens.append(current_token)
                current_token = ''
            else:
                current_token += char
        
        if current_token:
            tokens.append(current_token)
            
        print(f"  A5: Tokens: {tokens}")
        
        # Validate token structure
        if len(tokens) < 3:
            print(f"  A5: Invalid token count")
            continue
            
        # Check dash and spacing
        if not (tokens[0].strip() == '-' and tokens[0].endswith(' ')):
            print(f"  A5: Invalid dash or spacing")
            errors.append(f"Line {line_number}: {ERROR_MESSAGES['invalid_marker']}")
            continue
            
        # Check bracket content
        bracket_token = tokens[1]
        if not (bracket_token.startswith('[') and bracket_token.endswith(']')):
            print(f"  A5: Invalid bracket format")
            errors.append(f"Line {line_number}: {ERROR_MESSAGES['invalid_marker']}")
            continue
            
        # Check marker
        marker = bracket_token[1:-1]
        if marker not in [' ', 'x', 'X']:
            print(f"  A5: Invalid marker: '{marker}'")
            errors.append(f"Line {line_number}: {ERROR_MESSAGES['invalid_marker']}")
            continue
            
        # Check content after brackets
        if len(tokens) > 2 and not tokens[2].startswith(' '):
            print(f"  A5: Missing space after brackets")
            errors.append(f"Line {line_number}: {ERROR_MESSAGES['invalid_marker']}")
    
    return errors