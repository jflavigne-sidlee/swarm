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
    help_text = metadata.get(MetadataKeys.HELP, "No description available")
    
    def resolve_constraint(constraint_value: Any) -> Any:
        """Resolve constraint value, handling callables."""
        if callable(constraint_value):
            try:
                return constraint_value()
            except Exception as e:
                raise ConfigurationError(
                    f"Failed to evaluate dynamic constraint for '{name}': {str(e)}"
                )
        return constraint_value
    
    # Pre-resolve all constraints
    try:
        resolved_validation = {
            key: resolve_constraint(value) 
            for key, value in validation.items()
        }
    except ConfigurationError as e:
        raise ConfigurationError(f"Failed to resolve constraints: {str(e)}")
    
    def format_constraints() -> str:
        """Format validation constraints for error messages."""
        constraints = []
        if ValidationKeys.TYPE in resolved_validation:
            constraints.append(f"type={resolved_validation[ValidationKeys.TYPE].__name__}")
        if ValidationKeys.MIN in resolved_validation:
            constraints.append(f"min={resolved_validation[ValidationKeys.MIN]}")
        if ValidationKeys.MAX in resolved_validation:
            constraints.append(f"max={resolved_validation[ValidationKeys.MAX]}")
        if ValidationKeys.PATTERN in resolved_validation:
            constraints.append(f"pattern='{resolved_validation[ValidationKeys.PATTERN]}'")
        if ValidationKeys.CHOICES in resolved_validation:
            constraints.append(f"one of {resolved_validation[ValidationKeys.CHOICES]}")
        return ", ".join(constraints)
    
    # Handle None values
    if value is None:
        if resolved_validation.get(ValidationKeys.REQUIRED, False):
            raise ConfigurationError(
                ERROR_REQUIRED_FIELD.format(name=name) + f"\n"
                f"Description: {help_text}\n"
                f"Constraints: {format_constraints()}"
            )
        return

    # Type validation
    expected_type = resolved_validation.get(ValidationKeys.TYPE)
    if expected_type:
        if not isinstance(value, expected_type):
            raise ConfigurationError(
                ERROR_INVALID_TYPE.format(
                    name=name,
                    got=type(value).__name__,
                    expected=expected_type.__name__
                ) + f"\n"
                f"Value: {value}\n"
                f"Description: {help_text}\n"
                f"Constraints: {format_constraints()}"
            )
    
    # Numeric constraints
    if isinstance(value, (int, float)):
        if ValidationKeys.MIN in resolved_validation:
            min_value = resolved_validation[ValidationKeys.MIN]
            if value < min_value:
                raise ConfigurationError(
                    ERROR_VALUE_TOO_SMALL.format(
                        name=name,
                        value=value,
                        min=min_value
                    ) + f"\n"
                    f"Description: {help_text}\n"
                    f"Constraints: {format_constraints()}"
                )
        
        if ValidationKeys.MAX in resolved_validation:
            max_value = resolved_validation[ValidationKeys.MAX]
            if value > max_value:
                raise ConfigurationError(
                    ERROR_VALUE_TOO_LARGE.format(
                        name=name,
                        value=value,
                        max=max_value
                    ) + f"\n"
                    f"Description: {help_text}\n"
                    f"Constraints: {format_constraints()}"
                )

class PathHandler:
    """Utility class for handling path operations."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def process_path(
        self,
        path: Union[str, Path, None],
        name: str,
        *,
        required: bool = False,
        allow_creation: bool = True,
        must_exist: bool = False,
        must_be_directory: bool = True,
        check_permissions: bool = True,
    ) -> Optional[Path]:
        """Process and validate a path.
        
        Args:
            path: Path to process
            name: Name for error messages
            required: Whether the path is required
            allow_creation: Whether to create directory if missing
            must_exist: Whether the path must exist
            must_be_directory: Whether the path must be a directory
            check_permissions: Whether to check read/write permissions
            
        Returns:
            Validated Path object or None for optional paths
            
        Raises:
            ConfigurationError: For invalid path configurations
            PathValidationError: For path validation failures
        """
        if path is None:
            if required:
                raise ConfigurationError(PATH_REQUIRED_MSG.format(name=name))
            self.logger.debug(PATH_OPTIONAL_MSG.format(name=name))
            return None

        try:
            # Convert to Path
            path = Path(path) if isinstance(path, str) else path
            
            # Convert to absolute path
            if not path.is_absolute():
                path = path.resolve()
                self.logger.debug(PATH_CONVERSION_MSG.format(path=path))
            
            # Check existence
            if must_exist and not path.exists():
                raise PathValidationError(f"{name} does not exist: {path}")
            
            # Create if needed
            if allow_creation and not path.exists():
                self.logger.info(PATH_CREATION_MSG.format(path=path))
                path.mkdir(parents=True, exist_ok=True)
            
            # Validate directory
            if must_be_directory and path.exists() and not path.is_dir():
                raise PathValidationError(f"{name} is not a directory: {path}")
            
            # Check permissions
            if check_permissions and path.exists():
                if not os.access(path, os.R_OK):
                    raise PathValidationError(f"No read permission for {name}: {path}")
                if not os.access(path, os.W_OK):
                    raise PathValidationError(f"No write permission for {name}: {path}")
            
            return path
            
        except Exception as e:
            if isinstance(e, (ConfigurationError, PathValidationError)):
                raise
            raise PathValidationError(f"Failed to process {name}: {str(e)}")
    
    def validate_relationships(
        self,
        paths: Dict[str, Path],
        allow_nesting: bool = False
    ) -> None:
        """Validate relationships between multiple paths.
        
        Args:
            paths: Dictionary of path names to Path objects
            allow_nesting: Whether to allow nested directories
            
        Raises:
            ConfigurationError: If paths overlap or are nested incorrectly
        """
        self.logger.debug("Validating directory relationships")
        
        # Filter out None values and convert to list of tuples
        valid_paths = [(name, path) for name, path in paths.items() 
                      if path is not None and path.exists()]
        
        for i, (name1, path1) in enumerate(valid_paths):
            for name2, path2 in valid_paths[i + 1:]:
                try:
                    # Check for same directory
                    if path1.samefile(path2):
                        raise ConfigurationError(
                            f"Directories cannot be the same: "
                            f"'{name1}' ({path1}) and '{name2}' ({path2})"
                        )
                    
                    # Check for nesting if not allowed
                    if not allow_nesting:
                        if path1 in path2.parents or path2 in path1.parents:
                            raise ConfigurationError(
                                f"Directories cannot be nested: "
                                f"'{name1}' ({path1}) and '{name2}' ({path2})"
                            )
                
                except OSError as e:
                    raise ConfigurationError(
                        f"Error checking relationship between "
                        f"'{name1}' ({path1}) and '{name2}' ({path2}): {str(e)}"
                    )
        
        self.logger.info("Directory relationship validation completed successfully")

@dataclass
class WriterConfig:
    """Configuration for the Markdown Document Management System."""
    
    # Base paths with metadata
    temp_dir: Path = field(
        default_factory=lambda: Path(DEFAULT_PATHS["temp"]),
        metadata={
            MetadataKeys.DEFAULT: {
                "value": "DEFAULT_PATHS['temp']",
                "factory": "Path constructor"
            },
            MetadataKeys.VALIDATION: {
                "type": Path,
                "is_path": True,
                "required": True
            },
            MetadataKeys.HELP: "Directory for temporary files"
        }
    )
    
    # Locking settings with metadata
    lock_timeout: int = field(
        default=DEFAULT_LOCK_TIMEOUT,
        metadata={
            MetadataKeys.DEFAULT: {
                "value": DEFAULT_LOCK_TIMEOUT
            },
            MetadataKeys.VALIDATION: {
                "type": int,
                "min_value": 1,
                "allow_zero": False
            },
            MetadataKeys.HELP: "Timeout in seconds for acquiring locks",
            MetadataKeys.CONSTRAINTS: "Must be positive"
        }
    )
    
    section_marker_template: str = field(
        default=DEFAULT_SECTION_MARKER,
        metadata={
            MetadataKeys.DEFAULT: {
                "value": DEFAULT_SECTION_MARKER
            },
            MetadataKeys.VALIDATION: {
                "type": str,
                "required": True,
                "pattern": r".*\{section_title\}.*"
            },
            MetadataKeys.HELP: "Template for section markers, must contain {section_title}",
            MetadataKeys.EXAMPLE: "## {section_title}"
        }
    )
    
    max_file_size: int = field(
        default=DEFAULT_MAX_FILE_SIZE,
        metadata={
            MetadataKeys.VALIDATION: {
                ValidationKeys.TYPE: int,
                ValidationKeys.MIN: lambda: get_system_min_file_size(),
                ValidationKeys.MAX: lambda: get_available_disk_space() // 2,
                ValidationKeys.ALLOW_ZERO: False
            },
            MetadataKeys.HELP: "Maximum file size in bytes"
        }
    )
    
    allowed_extensions: List[str] = field(
        default_factory=list,
        metadata={
            MetadataKeys.VALIDATION: {
                ValidationKeys.TYPE: list,
                ValidationKeys.ELEMENT_TYPE: str,
                ValidationKeys.CHOICES: get_supported_extensions
            },
            MetadataKeys.HELP: "List of allowed file extensions"
        }
    )
    
    compression_level: int = field(
        default=5,
        metadata={
            MetadataKeys.VALIDATION: {
                ValidationKeys.TYPE: int,
                ValidationKeys.MIN: 1,
                ValidationKeys.MAX: lambda: get_max_compression_level(),
                ValidationKeys.ALLOW_ZERO: False
            },
            MetadataKeys.HELP: "Compression level for file storage"
        }
    )
    
    def __post_init__(self) -> None:
        """Initialize and validate configuration after creation."""
        self.logger = logging.getLogger(__name__)
        self.path_handler = PathHandler(self.logger)
        
        # Set default backup directory before path validation
        self._set_default_backup_dir()
        
        # Validate paths and create directories if needed
        self._validate_and_create_paths()
        
        # Validate all other settings
        self._validate_all()
    
    def _validate_and_create_paths(self) -> None:
        """Validate and create all configured paths."""
        self.logger.info("Starting path validation and creation")
        
        # Process required paths
        for path_attr in self._get_required_paths():
            validated_path = self.path_handler.process_path(
                getattr(self, path_attr),
                path_attr,
                required=True,
                allow_creation=self.create_directories
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
                allow_creation=self.create_directories
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
    
    def _set_default_backup_dir(self) -> None:
        """Set and validate default backup directory if needed."""
        self.logger.debug("Checking backup directory configuration")
        
        if self.backup_dir is None and self.backup_enabled:
            self.logger.info("Setting default backup directory")
            try:
                # Process through PathHandler for consistent validation
                self.backup_dir = self.path_handler.process_path(
                    self.temp_dir / "backups",
                    "backup_dir",
                    required=True,
                    allow_creation=self.create_directories,
                    must_be_directory=True,
                    check_permissions=True
                )
                self.logger.info(f"Default backup directory set to: {self.backup_dir}")
            except Exception as e:
                raise ConfigurationError(f"Failed to set default backup directory: {str(e)}")
    
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