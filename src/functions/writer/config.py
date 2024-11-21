from dataclasses import (
    dataclass,
    field,
    fields,
    MISSING
)
from pathlib import Path
from typing import List, Dict, Optional, Union, Pattern, Any
import logging
from .exceptions import ConfigurationError, PathValidationError
import os
import re
from .constants import *
from .utils import (
    get_system_min_file_size,
    get_available_disk_space,
    get_max_compression_level,
    get_supported_extensions
)

def validate_field_metadata(name: str, value: Any, metadata: Dict[str, Any]) -> None:
    """Validate a field value against its metadata constraints."""
    validation = metadata.get(MetadataKeys.VALIDATION, {})
    
    # Handle None values for optional fields
    if value is None:
        if validation.get(ValidationKeys.REQUIRED, False):
            raise ConfigurationError(f"Required field '{name}' is not set")
        return  # Skip further validation for None values in optional fields
    
    # Type validation
    expected_type = validation.get(ValidationKeys.TYPE)
    if expected_type and not isinstance(value, expected_type):
        raise ConfigurationError(
            ERROR_INVALID_TYPE.format(
                name=name,
                got=type(value).__name__,
                expected=expected_type.__name__
            )
        )
    
    # Numeric constraints
    if isinstance(value, (int, float)):
        min_value = validation.get(ValidationKeys.MIN)
        if min_value is not None and value < min_value:
            if min_value == 1 and value <= 0:
                raise ConfigurationError(f"{name} must be positive")
            else:
                raise ConfigurationError(
                    ERROR_VALUE_TOO_SMALL.format(
                        name=name,
                        value=value,
                        min=min_value
                    )
                )
    
    # Required field validation
    if validation.get(ValidationKeys.REQUIRED) and value is None:
        raise ConfigurationError(f"Required field '{name}' is not set")
    
    # Zero validation
    if not validation.get(ValidationKeys.ALLOW_ZERO, True) and value == 0:
        raise ConfigurationError(ERROR_NO_ZERO.format(name=name))
    
    # Pattern validation for strings
    if isinstance(value, str):
        pattern = validation.get(ValidationKeys.PATTERN)
        if pattern and not re.match(pattern, value):
            raise ConfigurationError(
                ERROR_PATTERN_MISMATCH.format(
                    name=name,
                    value=value,
                    pattern=pattern
                )
            )
    
    # Choices validation
    choices = validation.get(ValidationKeys.CHOICES)
    if choices and value not in choices:
        raise ConfigurationError(
            ERROR_INVALID_CHOICE.format(
                name=name,
                value=value,
                choices=", ".join(map(str, choices))
            )
        )
    
    # List element type validation
    if isinstance(value, list) and ValidationKeys.ELEMENT_TYPE in validation:
        element_type = validation[ValidationKeys.ELEMENT_TYPE]
        for item in value:
            if not isinstance(item, element_type):
                raise ConfigurationError(
                    f"Invalid type in list '{name}': got {type(item).__name__}, "
                    f"expected {element_type.__name__}"
                )

class PathHandler:
    """Utility class for handling path operations."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def process_path(
        self,
        path: Optional[Path],
        name: str,
        required: bool = True,
        allow_creation: bool = False,
        check_permissions: bool = True
    ) -> Path:
        """Process and validate a path."""
        self.logger.debug(
            f"Processing path '{name}': path={path}, required={required}, "
            f"check_permissions={check_permissions}"
        )
        
        if path is None:
            if required:
                raise ConfigurationError(PATH_REQUIRED_MSG.format(name=name))
            return None

        try:
            # Convert to Path
            path = Path(path) if isinstance(path, str) else path
            
            # Convert to absolute path
            if not path.is_absolute():
                path = path.resolve()
                self.logger.debug(PATH_CONVERSION_MSG.format(path=path))
            
            # Check existence after potential creation
            if required and not path.exists():
                if allow_creation:
                    try:
                        path.mkdir(parents=True, exist_ok=True)
                    except PermissionError:
                        raise PathValidationError(
                            f"Cannot create directory '{name}': Permission denied"
                        )
                else:
                    raise PathValidationError(f"{name} does not exist: {path}")
            
            # Check if it's a directory
            if path.exists() and not path.is_dir():
                raise PathValidationError(f"{name} is not a directory: {path}")
            
            # Check permissions using os.access first
            if check_permissions and path.exists():
                if not os.access(path, os.R_OK):
                    raise PathValidationError(
                        f"Path '{name}' does not have read permission: {path}"
                    )
                if not os.access(path, os.W_OK):
                    raise PathValidationError(
                        f"Path '{name}' does not have write permission: {path}"
                    )
                
                # Double-check with actual file operation only if os.access passes
                try:
                    test_file = path / ".write_test"
                    test_file.touch()
                    test_file.unlink()
                except (PermissionError, OSError) as e:
                    self.logger.warning(
                        f"Permission check failed for {name} despite os.access: {e}"
                    )
                    raise PathValidationError(
                        f"Path '{name}' does not have write permission: {path}"
                    )
            
            return path
            
        except Exception as e:
            if isinstance(e, (ConfigurationError, PathValidationError)):
                raise
            raise PathValidationError(f"Failed to process {name}: {str(e)}")
    
    def validate_relationships(self, paths: Dict[str, Path], allow_nesting: bool = True) -> None:
        """Validate relationships between paths."""
        try:
            # First check if paths exist and collect valid ones
            valid_paths = []
            for name, path in paths.items():
                if path is not None:
                    try:
                        if path.exists():
                            valid_paths.append((name, path))
                    except (PermissionError, OSError):
                        # If we can't check existence due to permissions,
                        # assume the path exists and add it
                        valid_paths.append((name, path))
            
            # Check for nesting if not allowed
            if not allow_nesting:
                for name1, path1 in valid_paths:
                    for name2, path2 in valid_paths:
                        if name1 != name2:
                            try:
                                if self._is_nested(path1, path2):
                                    raise ConfigurationError(
                                        f"Directories cannot be nested: '{name1}' and '{name2}'"
                                    )
                            except (PermissionError, OSError):
                                # If we can't check nesting due to permissions,
                                # that's okay - the permission error will be caught
                                # elsewhere during actual usage
                                pass
                            
        except Exception as e:
            self.logger.error(f"Error validating path relationships: {str(e)}")
            raise
    
    def _is_nested(self, path1: Path, path2: Path) -> bool:
        """Check if path1 is nested within path2."""
        try:
            return path1 in path2.parents or path2 in path1.parents
        except (PermissionError, OSError):
            # If we can't check nesting due to permissions,
            # that's okay - the permission error will be caught
            # elsewhere during actual usage
            return False

@dataclass
class WriterConfig:
    """Configuration for the Markdown Document Management System."""
    
    # Add create_directories field with default value
    create_directories: bool = field(
        default=True,
        metadata={
            MetadataKeys.VALIDATION: {
                ValidationKeys.TYPE: bool,
                ValidationKeys.REQUIRED: False
            },
            MetadataKeys.HELP: "Whether to create directories if they don't exist"
        }
    )
    
    # Backup settings
    backup_enabled: bool = field(
        default=False,
        metadata={
            MetadataKeys.VALIDATION: {
                ValidationKeys.TYPE: bool,
                ValidationKeys.REQUIRED: True
            },
            MetadataKeys.HELP: "Enable backup functionality"
        }
    )
    
    backup_dir: Optional[Path] = field(
        default=None,
        metadata={
            MetadataKeys.VALIDATION: {
                ValidationKeys.TYPE: Path,
                ValidationKeys.REQUIRED: False,
                "is_path": True
            },
            MetadataKeys.HELP: "Directory for backups (required if backup_enabled is True)"
        }
    )
    
    # Base paths
    temp_dir: Path = field(
        default_factory=lambda: Path(DEFAULT_PATHS["temp"]),
        metadata={
            MetadataKeys.IS_PATH: True,
            MetadataKeys.VALIDATION: {
                ValidationKeys.TYPE: Path,
                ValidationKeys.REQUIRED: True
            },
            MetadataKeys.HELP: "Directory for temporary files"
        }
    )
    
    drafts_dir: Path = field(
        default_factory=lambda: Path(DEFAULT_PATHS["drafts"]),
        metadata={
            MetadataKeys.IS_PATH: True,
            MetadataKeys.VALIDATION: {
                ValidationKeys.TYPE: Path,
                ValidationKeys.REQUIRED: True
            },
            MetadataKeys.HELP: "Directory for draft Markdown files"
        }
    )
    
    finalized_dir: Path = field(
        default_factory=lambda: Path(DEFAULT_PATHS["finalized"]),
        metadata={
            MetadataKeys.IS_PATH: True,
            MetadataKeys.VALIDATION: {
                ValidationKeys.TYPE: Path,
                ValidationKeys.REQUIRED: True
            },
            MetadataKeys.HELP: "Directory for finalized Markdown files"
        }
    )
    
    # Numeric settings
    lock_timeout: int = field(
        default=DEFAULT_LOCK_TIMEOUT,
        metadata={
            MetadataKeys.VALIDATION: {
                ValidationKeys.TYPE: int,
                ValidationKeys.MIN: 1,
                ValidationKeys.ALLOW_ZERO: False
            },
            MetadataKeys.HELP: "Lock timeout in seconds"
        }
    )
    
    max_file_size: int = field(
        default=DEFAULT_MAX_FILE_SIZE,
        metadata={
            MetadataKeys.VALIDATION: {
                ValidationKeys.TYPE: int,
                ValidationKeys.MIN: 1,
                ValidationKeys.ALLOW_ZERO: False
            },
            MetadataKeys.HELP: "Maximum file size in bytes"
        }
    )
    
    # List settings
    allowed_extensions: List[str] = field(
        default_factory=lambda: ALLOWED_EXTENSIONS.copy(),
        metadata={
            MetadataKeys.VALIDATION: {
                ValidationKeys.TYPE: list,
                ValidationKeys.ELEMENT_TYPE: str,
                ValidationKeys.REQUIRED: True
            },
            MetadataKeys.HELP: "List of allowed file extensions"
        }
    )
    
    # Compression settings
    compression_level: int = field(
        default=5,
        metadata={
            MetadataKeys.VALIDATION: {
                ValidationKeys.TYPE: int,
                ValidationKeys.MIN: 0,
                ValidationKeys.MAX: 9
            },
            MetadataKeys.HELP: "Compression level (0-9)"
        }
    )
    
    # String settings with pattern
    section_marker_template: str = field(
        default=DEFAULT_SECTION_MARKER,
        metadata={
            MetadataKeys.VALIDATION: {
                ValidationKeys.TYPE: str,
                ValidationKeys.REQUIRED: True,
                ValidationKeys.PATTERN: r".*\{section_title\}.*"
            },
            MetadataKeys.HELP: "Template for section markers, must contain {section_title}"
        }
    )
    
    # Metadata and encoding configuration
    metadata_keys: List[str] = field(
        default_factory=lambda: DEFAULT_METADATA_FIELDS,
        metadata={
            MetadataKeys.VALIDATION: {
                ValidationKeys.TYPE: list,
                ValidationKeys.ELEMENT_TYPE: str,
                ValidationKeys.REQUIRED: True
            },
            MetadataKeys.HELP: "List of metadata keys for Markdown documents",
            MetadataKeys.EXAMPLE: ["title", "author", "date", "tags"]
        }
    )

    default_encoding: str = field(
        default=DEFAULT_ENCODING,
        metadata={
            MetadataKeys.VALIDATION: {
                ValidationKeys.TYPE: str,
                ValidationKeys.REQUIRED: True,
                ValidationKeys.CHOICES: ["utf-8", "utf-16", "ascii"]
            },
            MetadataKeys.HELP: "Default encoding for Markdown files",
            MetadataKeys.EXAMPLE: "utf-8"
        }
    )
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self.logger = logging.getLogger(__name__)
        # Initialize path handler with logger
        self.path_handler = PathHandler(self.logger)
        
        self._validate_fields()
        self._validate_paths()
        self._validate_backup_config()
    
    def _validate_fields(self) -> None:
        """Validate all fields using their metadata."""
        for field_obj in fields(self):
            value = getattr(self, field_obj.name)
            validate_field_metadata(field_obj.name, value, field_obj.metadata)
    
    def _validate_paths(self) -> None:
        """Validate paths and create directories if needed."""
        self.logger.info("Starting path validation and creation")
        
        # Create required directories first if enabled
        if self.create_directories:
            self.logger.debug("Creating required directories")
            for path_attr in self._get_required_paths():
                path = getattr(self, path_attr)
                if path and not path.exists():
                    try:
                        path.mkdir(parents=True, exist_ok=True)
                        self.logger.debug(f"Created directory: {path}")
                    except Exception as e:
                        raise ConfigurationError(
                            f"Failed to create directory '{path_attr}': {str(e)}"
                        )
        
        # Process required paths
        for path_attr in self._get_required_paths():
            validated_path = self.path_handler.process_path(
                getattr(self, path_attr),
                path_attr,
                required=True,
                allow_creation=self.create_directories,
                check_permissions=True
            )
            setattr(self, path_attr, validated_path)
        
        # Process optional paths
        optional_paths = set(self._get_path_attributes()) - set(self._get_required_paths())
        for path_attr in optional_paths:
            if path_attr == "backup_dir" and not self.backup_enabled:
                continue
            validated_path = self.path_handler.process_path(
                getattr(self, path_attr),
                path_attr,
                required=False,
                allow_creation=self.create_directories,
                check_permissions=True
            )
            if validated_path:
                setattr(self, path_attr, validated_path)
        
        # Validate directory relationships
        self._validate_directory_relationships()
        
        self.logger.info("Path validation and creation completed successfully")
    
    def _validate_directory_relationships(self) -> None:
        """Validate relationships between configured directories."""
        self.logger.debug("Validating directory relationships")
        
        # Collect all configured directories
        directories = {
            "temp_dir": self.temp_dir,
            "drafts_dir": self.drafts_dir,
            "finalized_dir": self.finalized_dir
        }
        
        # Add backup directory if enabled
        if self.backup_enabled and self.backup_dir is not None:
            directories["backup_dir"] = self.backup_dir
        
        # Validate relationships using PathHandler
        try:
            self.path_handler.validate_relationships(
                directories,
                allow_nesting=False
            )
        except ConfigurationError as e:
            raise ConfigurationError(f"Directory validation failed: {str(e)}")
        
        self.logger.info("Directory relationship validation completed successfully")
    
    def _validate_backup_config(self) -> None:
        """Validate backup configuration."""
        if self.backup_enabled:
            # Ensure backup directory is set and valid
            if self.backup_dir is None:
                self._set_default_backup_dir()
            else:
                # Validate existing backup directory
                self.backup_dir = self.path_handler.process_path(
                    self.backup_dir,
                    "backup_dir",
                    required=True,
                    allow_creation=True,
                    must_be_directory=True,
                    check_permissions=True
                )
            
            # Validate directory relationships
            other_dirs = [self.temp_dir, self.drafts_dir, self.finalized_dir]
            if any(self.backup_dir.samefile(dir_path) 
                   for dir_path in other_dirs 
                   if dir_path is not None and dir_path.exists()):
                raise ConfigurationError(
                    f"Backup directory '{self.backup_dir}' cannot be the same as "
                    "temp_dir, drafts_dir, or finalized_dir"
                )
            
            self.logger.info(f"Backup directory validated: {self.backup_dir}")
        else:
            self.logger.info(LOG_BACKUP_ENABLED)
            if self.backup_dir is not None:
                self.logger.warning(LOG_BACKUP_WARNING)
    
    def _set_default_backup_dir(self) -> None:
        """Set default backup directory."""
        self.backup_dir = Path(DEFAULT_PATHS.get("backup", "data/backup"))
    
    def _validate_all(self) -> None:
        """Run all validation checks in the following order:
        1. Basic settings (numeric values, locks, markdown, metadata)
        2. Format settings (version format, section format)
        3. Path settings (directories, backup configuration)
        
        Each validation group is independent and can be run separately if needed.
        """
        validation_steps = [
            self._validate_basic_settings,
            self._validate_format_settings,
            self._validate_path_settings
        ]
        
        for step in validation_steps:
            step()
    
    def _validate_basic_settings(self) -> None:
        """Validate core configuration settings.
        
        Validates:
        - Numeric constraints (min/max values)
        - Lock timeouts and retries
        - Markdown flavor and encoding
        - Required metadata fields
        
        These settings must be valid before proceeding with format and path validation.
        """
        self._validate_numeric_settings()
        self._validate_lock_settings()
        self._validate_markdown_settings()
        self._validate_metadata_settings()
    
    def _validate_format_settings(self) -> None:
        """Validate format string configurations.
        
        Validates:
        - Version format placeholders and specifiers
        - Section marker templates
        - File extension formats
        
        Format validation ensures all templates can be safely used for string formatting.
        """
        self._validate_version_format()
        self._validate_section_format()
    
    def _validate_path_settings(self) -> None:
        """Validate directory configurations and relationships.
        
        Validates:
        - Path existence and permissions
        - Directory hierarchy
        - Backup configuration
        - Path conflicts between directories
        
        Path validation ensures the system can safely read/write to all required locations.
        Requires basic settings to be validated first.
        """
        self._validate_paths()
        self._validate_backup_settings()
    
    def _validate_lock_settings(self) -> None:
        """Validate all lock-related settings."""
        if self.max_lock_retries < MIN_LOCK_RETRIES:
            raise ConfigurationError("max_lock_retries must be at least 1")
        if self.lock_retry_delay < MIN_RETRY_DELAY:
            raise ConfigurationError("lock_retry_delay cannot be negative")
        if self.lock_timeout < 1:
            raise ConfigurationError("lock_timeout must be at least 1 second")
    
    def _validate_markdown_settings(self) -> None:
        """Validate Markdown-specific settings."""
        if self.markdown_flavor not in VALID_MARKDOWN_FLAVORS:
            raise ConfigurationError(
                f"Invalid markdown_flavor: {self.markdown_flavor}. "
                f"Must be one of: {', '.join(VALID_MARKDOWN_FLAVORS)}"
            )
        
        if "{section_title}" not in self.section_marker_template:
            raise ConfigurationError(
                "section_marker_template must contain {section_title} placeholder"
            )
        
        try:
            "test".encode(self.default_encoding)
        except LookupError:
            raise ConfigurationError(f"Invalid encoding: {self.default_encoding}")
        
        if not MIN_HEADER_DEPTH <= self.max_section_depth <= MAX_HEADER_DEPTH:
            raise ConfigurationError(
                f"max_section_depth must be between {MIN_HEADER_DEPTH} and {MAX_HEADER_DEPTH}"
            )
    
    def _validate_file_operations(self) -> None:
        """Validate file operation settings."""
        # Validate file size limit
        if self.max_file_size_mb <= 0:
            raise ConfigurationError("max_file_size_mb must be positive")
        
        # Validate extensions
        for ext in self.allowed_extensions:
            if not ext.startswith('.'):
                raise ConfigurationError(
                    f"Extension must start with '.': {ext}"
                )
            if not re.match(EXTENSION_PATTERN, ext):
                raise ConfigurationError(
                    f"Invalid extension format: {ext}"
                )
    
    def _validate_version_format(self) -> None:
        """Validate version format string."""
        # First check for required placeholders in specific order
        for placeholder in VERSION_FORMAT_PLACEHOLDERS:
            if placeholder not in self.version_format:
                raise ConfigurationError(
                    f"Missing required placeholder '{placeholder}' in version_format"
                )
        
        # Extract all placeholders for further validation
        placeholders = re.findall(VERSION_PLACEHOLDER_PATTERN, self.version_format)
        
        # Check for unknown placeholders
        unknown = set(placeholders) - ALLOWED_VERSION_PLACEHOLDERS
        if unknown:
            raise ConfigurationError(
                f"Unknown placeholder(s) in version_format: {', '.join(unknown)}. "
                f"Allowed placeholders are: {', '.join(ALLOWED_VERSION_PLACEHOLDERS)}"
            )
        
        # Check for duplicates
        duplicates = {p for p in placeholders if placeholders.count(p) > 1}
        if duplicates:
            raise ConfigurationError(
                f"Duplicate placeholder(s) found in version_format: {', '.join(duplicates)}"
            )
        
        # Validate format specifiers
        format_specs = re.findall(VERSION_FORMAT_SPEC_PATTERN, self.version_format)
        for name, spec in format_specs:
            if name != "version":
                raise ConfigurationError(
                    f"Format specifier not allowed for '{name}'. "
                    f"Only the 'version' placeholder can have format specifiers"
                )
            if not re.match(VERSION_PADDING_PATTERN, spec):
                raise ConfigurationError(
                    f"Invalid format specifier '{spec}' for version. "
                    f"Only zero-padding is allowed (e.g., '0>3' for three digits)"
                )
    
    def _validate_settings(self) -> None:
        """Validate general configuration settings."""
        if self.keep_versions < MIN_VERSIONS:
            raise ConfigurationError("keep_versions must be at least 1")
        if self.lock_timeout < 1:
            raise ConfigurationError("lock_timeout must be at least 1 second")
        if self.max_lock_retries < MIN_LOCK_RETRIES:
            raise ConfigurationError("max_lock_retries must be at least 1")
        if self.lock_retry_delay < MIN_RETRY_DELAY:
            raise ConfigurationError("lock_retry_delay cannot be negative")
        if self.max_file_size_mb <= 0:
            raise ConfigurationError("max_file_size_mb must be positive")
    
    def _validate_backup_settings(self) -> None:
        """Validate backup-related settings."""
        self.logger.debug("Validating backup settings")
        
        if self.backup_enabled:
            # Ensure backup directory is set and valid
            if self.backup_dir is None:
                self._set_default_backup_dir()
            else:
                # Validate existing backup directory
                self.backup_dir = self.path_handler.process_path(
                    self.backup_dir,
                    "backup_dir",
                    required=True,
                    allow_creation=self.create_directories,
                    must_be_directory=True,
                    check_permissions=True
                )
            
            # Validate directory relationships
            other_dirs = [self.temp_dir, self.drafts_dir, self.finalized_dir]
            if any(self.backup_dir.samefile(dir_path) 
                   for dir_path in other_dirs 
                   if dir_path is not None and dir_path.exists()):
                raise ConfigurationError(
                    f"Backup directory '{self.backup_dir}' cannot be the same as "
                    "temp_dir, drafts_dir, or finalized_dir"
                )
            
            self.logger.info(f"Backup directory validated: {self.backup_dir}")
        else:
            self.logger.info(LOG_BACKUP_ENABLED)
            if self.backup_dir is not None:
                self.logger.warning(LOG_BACKUP_WARNING)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "WriterConfig":
        """Create configuration from dictionary.
        
        Args:
            config_dict: Dictionary of configuration values
            
        Returns:
            Initialized WriterConfig instance
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        try:
            # Validate field types first
            cls._validate_field_types(config_dict)
            
            # Convert paths after validation
            cls._convert_path_fields(config_dict)
            
            return cls(**config_dict)
        except Exception as e:
            raise ConfigurationError(f"Invalid configuration: {str(e)}")

    @classmethod
    def _validate_field_types(cls, config_dict: Dict) -> None:
        """Validate types and constraints of fields in config dictionary."""
        valid_fields = {f.name: f for f in fields(cls)}
        
        # Check for unknown fields
        unknown_fields = set(config_dict) - set(valid_fields)
        if unknown_fields:
            raise ConfigurationError(f"Unknown configuration fields: {', '.join(unknown_fields)}")
        
        # Validate each field
        for name, value in config_dict.items():
            field = valid_fields[name]
            try:
                validate_field_metadata(name, value, field.metadata)
            except ConfigurationError as e:
                raise ConfigurationError(f"Validation failed for {name}: {str(e)}")
            except Exception as e:
                raise ConfigurationError(
                    f"Unexpected error validating {name}: {str(e)}"
                )

    @classmethod
    def _convert_path_fields(cls, config_dict: Dict) -> None:
        """Convert string paths to Path objects in config dictionary."""
        for key in cls._get_path_attributes():
            if key in config_dict and isinstance(config_dict[key], str):
                config_dict[key] = Path(config_dict[key])
    
    @classmethod
    def _get_path_attributes(cls) -> List[str]:
        """Get all path-related attributes from field metadata."""
        return [
            f.name for f in fields(cls) 
            if f.metadata.get(MetadataKeys.IS_PATH, False)
        ]
    
    @classmethod
    def _get_required_paths(cls) -> List[str]:
        """Get required path attributes from field metadata."""
        return [
            f.name for f in fields(cls)
            if f.metadata.get(MetadataKeys.IS_PATH, False) and f.metadata.get(MetadataKeys.REQUIRED, False)
        ]
    
    @classmethod
    def get_field_info(cls, field_name: str) -> Dict[str, Any]:
        """Get comprehensive information about a configuration field."""
        valid_fields = {f.name: f for f in fields(cls)}
        if field_name not in valid_fields:
            raise ValueError(ERROR_UNKNOWN_FIELD_NAME.format(name=field_name))
        
        field = valid_fields[field_name]
        metadata = field.metadata
        
        info = {
            FIELD_INFO_NAME: field_name,
            FIELD_INFO_TYPE: metadata.get(MetadataKeys.VALIDATION, {}).get(ValidationKeys.TYPE, field.type),
            FIELD_INFO_HELP: metadata.get(MetadataKeys.HELP, NO_DESCRIPTION),
            FIELD_INFO_REQUIRED: metadata.get(MetadataKeys.VALIDATION, {}).get(ValidationKeys.REQUIRED, False)
        }
        
        # Add default value information
        default_info = metadata.get(MetadataKeys.DEFAULT, {})
        if FIELD_INFO_VALUE in default_info:
            info[FIELD_INFO_DEFAULT] = default_info[FIELD_INFO_VALUE]
        elif FIELD_INFO_FACTORY in default_info:
            info[FIELD_INFO_DEFAULT] = f"{FACTORY_PREFIX}{default_info[FIELD_INFO_FACTORY]}"
        elif field.default is not field.default_factory:  # Has explicit default
            info[FIELD_INFO_DEFAULT] = field.default
        
        # Add validation constraints
        validation = metadata.get(MetadataKeys.VALIDATION, {})
        constraints = []
        
        if KEY_MIN_VALUE in validation:
            constraints.append(CONSTRAINT_MIN_FORMAT.format(validation[KEY_MIN_VALUE]))
        if KEY_MAX_VALUE in validation:
            constraints.append(CONSTRAINT_MAX_FORMAT.format(validation[KEY_MAX_VALUE]))
        if KEY_PATTERN in validation:
            constraints.append(CONSTRAINT_PATTERN_FORMAT.format(validation[KEY_PATTERN]))
        if KEY_CHOICES in validation:
            constraints.append(CONSTRAINT_CHOICES_FORMAT.format(
                ", ".join(map(str, validation[KEY_CHOICES]))
            ))
        
        if constraints:
            info[FIELD_INFO_CONSTRAINTS] = CONSTRAINT_JOIN_STR.join(constraints)
        elif KEY_CONSTRAINTS in metadata:
            info[FIELD_INFO_CONSTRAINTS] = metadata[KEY_CONSTRAINTS]
        
        # Add examples if available
        if FIELD_INFO_EXAMPLE in metadata:
            info[FIELD_INFO_EXAMPLE] = metadata[FIELD_INFO_EXAMPLE]
        
        return info
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary.
        
        Returns:
            Dictionary representation of configuration
        """
        result = {}
        for field_obj in fields(self):
            value = getattr(self, field_obj.name)
            
            # Handle Path objects
            if isinstance(value, Path):
                result[field_obj.name] = str(value)
            # Handle other special types that need serialization
            elif isinstance(value, (set, frozenset)):
                result[field_obj.name] = list(value)
            elif isinstance(value, Pattern):
                result[field_obj.name] = value.pattern
            else:
                result[field_obj.name] = value
        
        return result
    
    @classmethod
    def get_default_config(cls) -> Dict[str, Any]:
        """Get default configuration as a dictionary."""
        defaults = {}
        for field_obj in fields(cls):
            # Get default value
            if field_obj.default_factory is not MISSING:
                try:
                    value = field_obj.default_factory()
                except Exception as e:
                    raise ConfigurationError(
                        ERROR_GET_DEFAULT.format(
                            name=field_obj.name,
                            error=str(e)
                        )
                    )
            else:
                value = field_obj.default
            
            # Skip if no default
            if value is MISSING:
                continue
            
            # Convert to serializable format
            if isinstance(value, Path):
                defaults[field_obj.name] = str(value)
            elif isinstance(value, (set, frozenset)):
                defaults[field_obj.name] = list(value)
            elif isinstance(value, Pattern):
                defaults[field_obj.name] = value.pattern
            else:
                defaults[field_obj.name] = value
        
        return defaults
    
    def __str__(self) -> str:
        """Get string representation of configuration."""
        lines = [CONFIG_HEADER]
        for name, value in self.to_dict().items():
            lines.append(f"{CONFIG_INDENT}{name}: {value}")
        return "\n".join(lines)
    
    
                # pytest tests/functions/writer/test_config.py -v -s