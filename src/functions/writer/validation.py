from pathlib import Path
import subprocess
import logging
from typing import Tuple, List
import re

from .exceptions import WriterError
from .file_operations import validate_file

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
        WriterError: If file doesn't exist or isn't accessible
    """
    file_path = Path(file_name)
    errors = []
    
    try:
        # Validate file exists and is readable
        validate_file(file_path, require_write=False)
        
        # Run remark-lint validation
        try:
            result = subprocess.run(
                ['npx', 'remark-cli', str(file_path), '--use', 'remark-lint'],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode != 0:
                errors.extend(parse_remark_errors(result.stderr))
                
        except subprocess.CalledProcessError as e:
            logger.error(f"remark-lint validation failed: {str(e)}")
            errors.append(f"Syntax validation failed: {str(e)}")
            
        # Run markdownlint validation
        try:
            result = subprocess.run(
                ['npx', 'markdownlint-cli', str(file_path)],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode != 0:
                errors.extend(parse_markdownlint_errors(result.stdout))
                
        except subprocess.CalledProcessError as e:
            logger.error(f"markdownlint validation failed: {str(e)}")
            errors.append(f"Additional validation failed: {str(e)}")
            
        # Check for broken links and images
        content_errors = validate_content(file_path)
        errors.extend(content_errors)
        
        return len(errors) == 0, errors
        
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        raise WriterError(f"Failed to validate markdown: {str(e)}")

def parse_remark_errors(error_output: str) -> List[str]:
    """Parse remark-lint error output into readable messages."""
    errors = []
    for line in error_output.splitlines():
        if ':' in line:
            # Extract line number and message
            parts = line.split(':', 2)
            if len(parts) >= 3:
                line_num = parts[1].strip()
                message = parts[2].strip()
                errors.append(f"Line {line_num}: {message}")
    return errors

def parse_markdownlint_errors(error_output: str) -> List[str]:
    """Parse markdownlint error output into readable messages."""
    errors = []
    for line in error_output.splitlines():
        if ':' in line:
            # Extract line number and rule
            match = re.match(r'.*:(\d+):\s*(.+)', line)
            if match:
                line_num = match.group(1)
                message = match.group(2)
                errors.append(f"Line {line_num}: {message}")
    return errors

def validate_content(file_path: Path) -> List[str]:
    """Validate document content for broken links and images.
    
    Args:
        file_path: Path to the markdown file to validate
        
    Returns:
        List[str]: List of validation errors found
    """
    errors = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Track validated paths to avoid duplicate checks
        validated_paths = set()
            
        # Check for broken image links
        image_links = re.finditer(r'!\[([^\]]*)\]\(([^)]+)\)', content)
        for match in image_links:
            image_path = match.group(2)
            if not image_path.startswith(('http://', 'https://')):
                if not (file_path.parent / image_path).exists():
                    errors.append(f"Broken image link: {image_path}")
                validated_paths.add(image_path)
                
        # Check for broken local file links
        file_links = re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', content)
        for match in file_links:
            link_path = match.group(2)
            # Skip already validated paths, anchors, and external links
            if (link_path not in validated_paths and 
                not link_path.startswith(('http://', 'https://', '#'))):
                if not (file_path.parent / link_path).exists():
                    errors.append(f"Broken file link: {link_path}")
                    
    except Exception as e:
        errors.append(f"Content validation error: {str(e)}")
        
    return errors
