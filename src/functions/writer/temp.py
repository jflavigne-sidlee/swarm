"""
Solution Attempts Log:
1. Approach: Ensure ValidationError is raised for empty link URLs
   Test Cases: [test_empty_link_url]
   Results: Failed (reason: ValidationError not raised)
2. Approach: Ensure ValidationError is raised for invalid table separators
   Test Cases: [test_invalid_table_separator]
   Results: Failed (reason: ValidationError not raised)
"""

import aiofiles
import yaml
from typing import List, Dict, Optional, Set
from pathlib import Path
import re
import logging
from .constants import (
    PATTERN_SECTION_MARKER,
    PATTERN_HEADER,
    ERROR_MISSING_SECTION_MARKER,
    ERROR_MISMATCHED_SECTION_MARKER,
    ERROR_ORPHANED_SECTION_MARKER,
    ERROR_DUPLICATE_SECTION_MARKER,
    LOG_VALIDATE_SECTION_START,
    LOG_SECTION_MARKER_VALID,
)

class ValidationError(Exception):
    """Base class for validation errors."""
    pass


class MarkdownValidator:
    """Validates markdown document structure and syntax."""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.section_markers: Set[str] = set()
        self.header_titles: Set[str] = set()
        self.required_frontmatter_fields = ["title", "author", "date"]  # Configurable

    async def _read_file_content(self) -> str:
        """Reads the file content asynchronously."""
        async with aiofiles.open(self.file_path, mode="r", encoding="utf-8") as f:
            return await f.read()

    async def _validate_links_and_images(self, content: str) -> None:
        """
        Validates markdown links and image references.
        
        Args:
            content: The markdown document content
            
        Raises:
            ValidationError: If validation fails
        """
        # Link pattern: [text](url)
        link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
        # Image pattern: ![alt](url)
        image_pattern = r'!\[([^\]]*)\]\(([^\)]+)\)'
        
        # Validate links
        for match in re.finditer(link_pattern, content):
            text, url = match.groups()
            logging.debug(f"Validating link: text={text}, url={url}")
            if not url.strip():
                logging.error(f"Empty URL in link: [{text}]()")
                raise ValidationError(f"Empty URL in link: [{text}]()")
            
            # Validate relative file links exist
            if not (url.startswith('http://') or 
                   url.startswith('https://') or 
                   url.startswith('#') or 
                   url.startswith('mailto:')):
                link_path = Path(self.file_path.parent / url)
                if not link_path.exists():
                    logging.error(f"Broken file link: {url}")
                    raise ValidationError(f"Broken file link: {url}")
        
        # Validate images
        for match in re.finditer(image_pattern, content):
            alt, url = match.groups()
            logging.debug(f"Validating image: alt={alt}, url={url}")
            if not url.strip():
                logging.error(f"Empty URL in image: ![{alt}]()")
                raise ValidationError(f"Empty URL in image: ![{alt}]()")
            
            # Validate relative image files exist
            if not (url.startswith('http://') or url.startswith('https://')):
                img_path = Path(self.file_path.parent / url)
                if not img_path.exists():
                    logging.error(f"Broken image link: {url}")
                    raise ValidationError(f"Broken image link: {url}")

    async def _validate_tables(self, content: str) -> None:
        """
        Validates markdown tables for proper formatting.
        
        Args:
            content: The markdown document content
            
        Raises:
            ValidationError: If table validation fails
        """
        # Table pattern matches header row, separator row, and data rows
        table_pattern = r'\|[^\n]+\|\n\|[\s\-\|:]+\|\n(\|[^\n]+\|\n?)*'
        
        for table_match in re.finditer(table_pattern, content, re.MULTILINE):
            table = table_match.group(0)
            rows = table.strip().split('\n')
            
            logging.debug(f"Validating table: {table}")
            
            if len(rows) < 2:
                logging.error("Table must have header and separator rows")
                raise ValidationError("Table must have header and separator rows")
                
            # Get column count from header
            header_cols = len([col for col in rows[0].split('|') if col.strip()])
            
            # Validate separator row
            separator = rows[1]
            logging.debug(f"Validating separator row: {separator}")
            if not re.match(r'^\|(\s*:?-+:?\s*\|)+$', separator):
                logging.error("Invalid table separator row")
                raise ValidationError("Invalid table separator row")
            
            # Validate all rows have same number of columns
            for row in rows[2:]:
                cols = len([col for col in row.split('|') if col.strip()])
                if cols != header_cols:
                    logging.error(f"Inconsistent column count. Expected {header_cols}, got {cols}")
                    raise ValidationError(
                        f"Inconsistent column count. Expected {header_cols}, got {cols}"
                    )

    async def validate(self) -> bool:
        """
        Validates the markdown document.

        Returns:
            bool: True if document is valid, False otherwise

        Raises:
            ValidationError: If validation fails with specific error
        """
        try:
            logging.info(LOG_VALIDATE_SECTION_START, self.file_path)

            # Read file content asynchronously
            content = await self._read_file_content()

            # Validate frontmatter first
            await self._validate_frontmatter(content)

            # Validate section markers and headers
            await self._validate_section_structure(content)

            # Validate links and images
            await self._validate_links_and_images(content)

            # Validate tables
            await self._validate_tables(content)

            # If we get here, validation passed
            logging.info(LOG_SECTION_MARKER_VALID)
            return True

        except Exception as e:
            logging.error(f"Validation failed: {str(e)}")
            raise ValidationError(f"Validation failed: {str(e)}")


async def validate_markdown(file_name: str) -> bool:
    """
    Validates a markdown document for proper structure and syntax.

    Args:
        file_name: Path to the markdown file to validate

    Returns:
        bool: True if document is valid, False otherwise

    Raises:
        ValidationError: If validation fails with specific error
    """
    validator = MarkdownValidator(file_name)
    return await validator.validate()