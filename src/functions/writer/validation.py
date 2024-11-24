from pathlib import Path
import subprocess
import logging
from typing import Tuple, List
import re

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
        validate_file(file_path)
        
        # Check for empty file
        if file_path.stat().st_size == 0:
            logger.warning("Empty markdown file detected")
            return False, ["File is empty"]
            
        errors = []

        # Run remark-lint validation
        try:
            result = subprocess.run(
                ['npx', 'remark', str(file_path), '--use', 'remark-lint',
                 '--use', 'remark-validate-links'],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode != 0:
                errors.extend(parse_remark_errors(result.stderr))
                
        except subprocess.CalledProcessError as e:
            logger.error(ERROR_REMARK_VALIDATION.format(error=str(e)))
            errors.append(ERROR_REMARK_VALIDATION.format(error=str(e)))

        # Run markdownlint validation
        try:
            result = subprocess.run(
                ['markdownlint', str(file_path), '--config', MARKDOWNLINT_CONFIG_FILE],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode != 0:
                errors.extend(parse_markdownlint_errors(result.stdout))
                
        except subprocess.CalledProcessError as e:
            logger.error(ERROR_MARKDOWNLINT_VALIDATION.format(error=str(e)))
            errors.append(ERROR_MARKDOWNLINT_VALIDATION.format(error=str(e)))

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
                errors.append(ERROR_PANDOC_VALIDATION.format(error=result.stderr))
                
        except subprocess.CalledProcessError as e:
            logger.error(ERROR_PANDOC_VALIDATION.format(error=str(e)))
            errors.append(ERROR_PANDOC_VALIDATION.format(error=str(e)))

        # Check for broken links and images
        content_errors = validate_content(file_path)
        errors.extend(content_errors)
        
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
