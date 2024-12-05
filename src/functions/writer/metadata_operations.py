from typing import Dict, Any, Optional
from pathlib import Path
import yaml
import logging
import re
from .exceptions import (
    WriterError,
    FileValidationError,
    FilePermissionError,
)
from .constants import (
    MD_EXTENSION,
)
from .errors import (
    ERROR_EMPTY_FILE,
    ERROR_FILE_NOT_FOUND,
    ERROR_INVALID_FILE_FORMAT,
    ERROR_INVALID_METADATA_CHOICE,
    ERROR_INVALID_METADATA_FORMAT,
    ERROR_INVALID_METADATA_PATTERN,
    ERROR_INVALID_METADATA_TYPE,
    ERROR_METADATA_ABOVE_MAX,
    ERROR_METADATA_BELOW_MIN,
    ERROR_METADATA_VALIDATION_FAILED,
    ERROR_MISSING_REQUIRED_METADATA,
    ERROR_PERMISSION_DENIED_PATH,
    ERROR_PERMISSION_DENIED_WRITE,
)
from .logs import (
    LOG_DEFAULT_METADATA_VALIDATION_FAILED,
    LOG_EMPTY_FILE_DETECTED,
    LOG_ENCODING_ERROR,
    LOG_FILE_NOT_FOUND,
    LOG_FILE_READ_ERROR,
    LOG_INVALID_FILE_FORMAT,
    LOG_INVALID_METADATA_CHOICE,
    LOG_INVALID_METADATA_PATTERN,
    LOG_INVALID_METADATA_TYPE,
    LOG_INVALID_YAML_METADATA,
    LOG_METADATA_ABOVE_MAX,
    LOG_METADATA_BELOW_MIN,
    LOG_METADATA_VALIDATION_FAILED,
    LOG_MISSING_METADATA_FIELDS,
    LOG_NO_METADATA_BLOCK,
    LOG_NO_READ_PERMISSION,
    LOG_NO_WRITE_PERMISSION,
)
from .file_io import validate_file_access
from .file_io import read_file, atomic_write
from .config import WriterConfig
from .validation_constants import ValidationKeys
from .metadata_utils import format_metadata_block
from .patterns import FRONTMATTER_MARKER
from .file_validation import validate_file_inputs

logger = logging.getLogger(__name__)

class MetadataOperations:
    """Handles metadata operations with consistent configuration."""
    
    def __init__(self, config: Optional[WriterConfig] = None):
        """
        Initialize with optional configuration.
        
        Args:
            config: Optional configuration object. If not provided, uses default config.
        """
        self.config = config or WriterConfig()
        # Precompile regex patterns from validation rules
        self.compiled_patterns = {
            field: re.compile(rules[ValidationKeys.PATTERN])
            for field, rules in self.config.metadata_validation_rules.items()
            if ValidationKeys.PATTERN in rules
        }
    
    def _validate_file_access(self, file_path: Path, require_write: bool = False) -> None:
        """
        Validate file access permissions and format.
        
        Args:
            file_path: Path to validate
            require_write: Whether write permission is required
            
        Raises:
            WriterError: If validation fails
        """
        try:
            validate_file_inputs(
                file_path,
                self.config,
                require_write=require_write,
                check_extension=True,
                extension=MD_EXTENSION
            )
        except (FileValidationError, FilePermissionError, FileNotFoundError) as e:
            logger.error(f"File validation failed: {str(e)}")
            # Convert the specific error message to a WriterError
            if isinstance(e, FilePermissionError):
                raise WriterError("Permission denied")
            elif isinstance(e, FileNotFoundError):
                raise WriterError("File does not exist")
            else:
                raise WriterError(str(e))
    
    def get_metadata(self, file_name: str) -> Dict[str, Any]:
        """
        Extract metadata from a markdown file's YAML front matter.
        """
        file_path = Path(file_name)
        
        # Validate file access
        self._validate_file_access(file_path, require_write=False)
        
        try:
            content = read_file(file_path, self.config.default_encoding)
        except UnicodeError as e:
            logger.error(LOG_ENCODING_ERROR.format(
                path=file_path, 
                encoding=self.config.default_encoding, 
                error=e
            ))
            raise WriterError(str(e))
        except Exception as e:
            logger.error(LOG_FILE_READ_ERROR.format(path=file_name, error=str(e)))
            raise WriterError(str(e))
                
        if not content.strip():
            logger.warning(LOG_EMPTY_FILE_DETECTED)
            raise WriterError(ERROR_EMPTY_FILE)
        
        metadata_match = content.split(FRONTMATTER_MARKER, 2)
        if len(metadata_match) < 3:
            logger.warning(LOG_NO_METADATA_BLOCK.format(path=file_name))
            if self.config.initialize_missing_metadata:
                # Initialize with configured defaults
                metadata = self.config.metadata_defaults.copy()
                # Add required fields with None if not in defaults
                for field, rules in self.config.metadata_validation_rules.items():
                    if rules.get(ValidationKeys.REQUIRED, False) and field not in metadata:
                        metadata[field] = None
                try:
                    self.validate_metadata(metadata)
                    return metadata
                except WriterError:
                    logger.warning(LOG_DEFAULT_METADATA_VALIDATION_FAILED)
                    return {}
            return {}
            
        try:
            metadata = yaml.safe_load(metadata_match[1])
            if metadata is None:
                metadata = {}
            if not isinstance(metadata, dict):
                raise WriterError(ERROR_INVALID_METADATA_FORMAT)
        except yaml.YAMLError as e:
            logger.error(LOG_INVALID_YAML_METADATA.format(error=str(e)))
            raise WriterError(ERROR_INVALID_METADATA_FORMAT)
            
        self.validate_metadata(metadata)
        return metadata
    
    def update_metadata(self, file_name: str, new_metadata: Dict[str, Any]) -> None:
        """
        Update metadata in a markdown file while preserving content.
        
        Args:
            file_name: Path to the markdown file
            new_metadata: New metadata to write
        """
        file_path = Path(file_name)
        
        # Validate file access
        self._validate_file_access(file_path, require_write=True)
        
        # Read existing content
        content = read_file(file_path, self.config.default_encoding)
        
        # Split content
        parts = content.split(FRONTMATTER_MARKER, 2)
        if len(parts) < 3:
            # No existing metadata, create new
            new_content = format_metadata_block(new_metadata, content)
        else:
            # Replace existing metadata
            new_content = format_metadata_block(new_metadata, parts[2])
        
        # Write updated content
        atomic_write(file_path, new_content, self.config.default_encoding, self.config.temp_dir)
    
    def validate_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        Validate metadata against configuration rules.
        
        Args:
            metadata: Metadata to validate
        
        Raises:
            WriterError: If metadata is invalid
        """
        # Check required fields
        required_fields = {
            field for field, rules in self.config.metadata_validation_rules.items()
            if rules.get(ValidationKeys.REQUIRED, False)
        }
        missing_fields = required_fields - set(metadata.keys())
        if missing_fields:
            logger.error(LOG_MISSING_METADATA_FIELDS.format(fields=', '.join(missing_fields)))
            raise WriterError(ERROR_MISSING_REQUIRED_METADATA.format(
                fields=', '.join(missing_fields)
            ))
        
        # Apply custom validation rules
        for field, rules in self.config.metadata_validation_rules.items():
            if field in metadata:
                value = metadata[field]
                
                # Type validation
                if ValidationKeys.TYPE in rules:
                    expected_type = rules[ValidationKeys.TYPE]
                    if not isinstance(value, expected_type):
                        logger.error(LOG_INVALID_METADATA_TYPE.format(
                            field=field,
                            expected=expected_type.__name__,
                            actual=type(value).__name__
                        ))
                        raise WriterError(ERROR_INVALID_METADATA_TYPE.format(
                            field=field,
                            expected=expected_type.__name__,
                            actual=type(value).__name__
                        ))
                
                # Pattern validation with fallback
                if ValidationKeys.PATTERN in rules and isinstance(value, str):
                    pattern = self.compiled_patterns.get(field) or re.compile(rules[ValidationKeys.PATTERN])
                    if not pattern.match(value):
                        logger.error(LOG_INVALID_METADATA_PATTERN.format(field=field))
                        raise WriterError(ERROR_INVALID_METADATA_PATTERN.format(field=field))
                
                # Value range validation
                if ValidationKeys.MIN in rules and value < rules[ValidationKeys.MIN]:
                    logger.error(LOG_METADATA_BELOW_MIN.format(
                        field=field,
                        min_value=rules[ValidationKeys.MIN]
                    ))
                    raise WriterError(ERROR_METADATA_BELOW_MIN.format(
                        field=field,
                        min_value=rules[ValidationKeys.MIN]
                    ))
                if ValidationKeys.MAX in rules and value > rules[ValidationKeys.MAX]:
                    logger.error(LOG_METADATA_ABOVE_MAX.format(
                        field=field,
                        max_value=rules[ValidationKeys.MAX]
                    ))
                    raise WriterError(ERROR_METADATA_ABOVE_MAX.format(
                        field=field,
                        max_value=rules[ValidationKeys.MAX]
                    ))
                
                # Choices validation
                if ValidationKeys.CHOICES in rules and value not in rules[ValidationKeys.CHOICES]:
                    logger.error(LOG_INVALID_METADATA_CHOICE.format(
                        field=field,
                        choices=', '.join(str(c) for c in rules[ValidationKeys.CHOICES])
                    ))
                    raise WriterError(ERROR_INVALID_METADATA_CHOICE.format(
                        field=field,
                        choices=', '.join(str(c) for c in rules[ValidationKeys.CHOICES])
                    ))
                
                # Custom validation function
                if ValidationKeys.VALIDATE in rules:
                    try:
                        rules[ValidationKeys.VALIDATE](value)
                    except Exception as e:
                        logger.error(LOG_METADATA_VALIDATION_FAILED.format(
                            field=field,
                            error=str(e)
                        ))
                        raise WriterError(ERROR_METADATA_VALIDATION_FAILED.format(
                            field=field,
                            error=str(e)
                        ))
    
    def merge_metadata(self, base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge two metadata dictionaries according to configuration rules.
        
        Args:
            base: Base metadata
            updates: Updates to apply
        
        Returns:
            Merged metadata dictionary
        """
        merged = base.copy()
        merged.update(updates)
        
        # Validate merged result
        self.validate_metadata(merged)
        
        return merged
