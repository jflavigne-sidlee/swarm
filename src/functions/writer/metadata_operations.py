from typing import Dict, Any, Set, Optional
from pathlib import Path
import yaml
import logging
import re
from .exceptions import WriterError
from .constants import (
    DEFAULT_ENCODING,
    MD_EXTENSION,
)
from .errors import (
    ERROR_INVALID_FILE_FORMAT,
    ERROR_FILE_NOT_FOUND,
    ERROR_EMPTY_FILE,
    ERROR_INVALID_METADATA_FORMAT,
    ERROR_MISSING_REQUIRED_METADATA,
    ERROR_PERMISSION_DENIED_PATH,
    ERROR_PERMISSION_DENIED_WRITE,
)
from .logs import (
    LOG_EMPTY_FILE_DETECTED,
    LOG_FILE_NOT_FOUND,
    LOG_INVALID_FILE_FORMAT,
    LOG_FILE_READ_ERROR,
    LOG_NO_METADATA_BLOCK,
    LOG_INVALID_YAML_METADATA,
    LOG_MISSING_METADATA_FIELDS,
    LOG_NO_READ_PERMISSION,
    LOG_NO_WRITE_PERMISSION,
    LOG_ENCODING_ERROR,
)
from .file_operations import validate_path_permissions
from .file_io import read_file, atomic_write
from .config import WriterConfig

logger = logging.getLogger(__name__)

class MetadataOperations:
    """Handles metadata operations with consistent configuration."""
    
    def __init__(self, config: Optional[WriterConfig] = None):
        """Initialize with optional configuration."""
        self.config = config or WriterConfig()
    
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
            validate_path_permissions(file_path, require_write=require_write)
        except FileNotFoundError:
            logger.error(LOG_FILE_NOT_FOUND.format(path=file_path))
            raise WriterError(ERROR_FILE_NOT_FOUND.format(path=file_path))
        except PermissionError as e:
            if require_write:
                logger.error(LOG_NO_WRITE_PERMISSION.format(path=file_path))
                raise WriterError(ERROR_PERMISSION_DENIED_WRITE.format(file_path=file_path))
            else:
                logger.error(LOG_NO_READ_PERMISSION.format(path=file_path))
                raise WriterError(ERROR_PERMISSION_DENIED_PATH.format(path=file_path))
            
        if file_path.suffix != MD_EXTENSION:
            logger.error(LOG_INVALID_FILE_FORMAT.format(path=file_path))
            raise WriterError(ERROR_INVALID_FILE_FORMAT)
    
    def get_metadata(self, file_name: str) -> Dict[str, Any]:
        """
        Extract metadata from a markdown file's YAML front matter.
        
        Args:
            file_name: Path to the markdown file
            
        Returns:
            Dictionary containing metadata fields and their values. Returns empty dict if no
            metadata block is found.
            
        Raises:
            WriterError: If file doesn't exist, is empty, has invalid metadata format,
                        or is missing required fields
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
        
        metadata_match = content.split('---', 2)
        if len(metadata_match) < 3:
            logger.warning(LOG_NO_METADATA_BLOCK.format(path=file_name))
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
        parts = content.split('---', 2)
        if len(parts) < 3:
            # No existing metadata, create new
            new_content = f"---\n{yaml.dump(new_metadata)}---\n{content}"
        else:
            # Replace existing metadata
            new_content = f"---\n{yaml.dump(new_metadata)}---{parts[2]}"
        
        # Write updated content
        atomic_write(file_path, new_content, self.config.default_encoding, self.config.temp_dir)
    
    def validate_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        Validate metadata against configuration rules.
        
        Args:
            metadata: Metadata to validate
        
        Raises:
            WriterError: If metadata is invalid, with specific error messages for:
                - Missing required fields
                - Invalid field types
                - Pattern mismatches
                - Custom validation failures
        """
        # Check required fields
        missing_fields = self.config.metadata_keys - set(metadata.keys())
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
                if 'type' in rules:
                    expected_type = rules['type']
                    if not isinstance(value, expected_type):
                        raise WriterError(
                            f"Invalid type for {field}: expected {expected_type.__name__}, "
                            f"got {type(value).__name__}"
                        )
                
                # Pattern validation
                if 'pattern' in rules and isinstance(value, str):
                    if not re.match(rules['pattern'], value):
                        raise WriterError(f"Invalid format for {field}")
                
                # Value range validation
                if 'min_value' in rules and value < rules['min_value']:
                    raise WriterError(f"Value for {field} must be >= {rules['min_value']}")
                if 'max_value' in rules and value > rules['max_value']:
                    raise WriterError(f"Value for {field} must be <= {rules['max_value']}")
                
                # Custom validation function
                if 'validator' in rules:
                    try:
                        rules['validator'](value)
                    except Exception as e:
                        raise WriterError(f"Validation failed for {field}: {str(e)}")
    
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
