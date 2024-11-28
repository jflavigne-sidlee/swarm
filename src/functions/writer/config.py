from dataclasses import dataclass, field, fields, MISSING
from pathlib import Path
from typing import List, Dict, Optional, Union, Pattern, Any, Set
import logging
from .exceptions import ConfigurationError, PathValidationError
import os
import re
from .constants import (
    DEFAULT_ENCODING,
    DEFAULT_LOCK_TIMEOUT,
    DEFAULT_METADATA_FIELDS,
    DEFAULT_PATHS,
    MIN_LOCK_RETRIES,
    MIN_RETRY_DELAY,
    MIN_VERSIONS,


)
from .errors import (
    ERROR_GET_DEFAULT,
    ERROR_INVALID_CHOICE,
    ERROR_INVALID_CONFIG,
    ERROR_INVALID_TYPE,
    ERROR_NO_ZERO,
    ERROR_PATH_NO_READ,
    ERROR_PATH_NO_WRITE,
    ERROR_PATH_NOT_DIR,
    ERROR_PATH_NOT_EXIST,
    ERROR_PATH_PROCESS,
    ERROR_PATTERN_MISMATCH,
    ERROR_UNKNOWN_FIELD_NAME,
    ERROR_VALUE_TOO_LARGE,
    ERROR_VALUE_TOO_SMALL,
)
from .patterns import (
    ALLOWED_VERSION_PLACEHOLDERS,
    SECTION_MARKER_TEMPLATE,
    EXTENSION_PATTERN,
    VERSION_FORMAT_PLACEHOLDERS,
    VERSION_FORMAT_SPEC_PATTERN,
    VERSION_PADDING_PATTERN,
    VERSION_PLACEHOLDER_PATTERN,
    VALID_MARKDOWN_FLAVORS,
    HEADER_LEVEL_RANGE,
)

from .validation_constants import (
    MetadataKeys,
    ValidationKeys,
    KEY_CHOICES,
    KEY_CONSTRAINTS,
    KEY_MAX_VALUE,
    KEY_MIN_VALUE,
    KEY_PATTERN,
    CONSTRAINT_CHOICES_FORMAT,
    CONSTRAINT_JOIN_STR,
    CONSTRAINT_MAX_FORMAT,
    CONSTRAINT_MIN_FORMAT,
    CONSTRAINT_PATTERN_FORMAT,
)
from .logs import (
    CONFIG_HEADER,
    CONFIG_INDENT,
    FACTORY_PREFIX,
    LOG_BACKUP_WARNING,
    LOG_BACKUP_ENABLED,
    NO_DESCRIPTION,
    PATH_CREATION_MSG,
    PATH_OPTIONAL_MSG,
    PATH_REQUIRED_MSG,
    FIELD_INFO_CONSTRAINTS,
    FIELD_INFO_DEFAULT,
    FIELD_INFO_EXAMPLE,
    FIELD_INFO_FACTORY,
    FIELD_INFO_HELP,
    FIELD_INFO_NAME,
    FIELD_INFO_REQUIRED,
    FIELD_INFO_TYPE,
    FIELD_INFO_VALUE, 
)
from .utils import (
    get_system_min_file_size,
    get_available_disk_space,
    get_max_compression_level,
    get_supported_extensions,
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
                name=name, got=type(value).__name__, expected=expected_type.__name__
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
                    ERROR_VALUE_TOO_SMALL.format(name=name, value=value, min=min_value)
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
                ERROR_PATTERN_MISMATCH.format(name=name, value=value, pattern=pattern)
            )

    # Choices validation
    choices = validation.get(ValidationKeys.CHOICES)
    if choices and value not in choices:
        raise ConfigurationError(
            ERROR_INVALID_CHOICE.format(
                name=name, value=value, choices=", ".join(map(str, choices))
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
        check_permissions: bool = True,
    ) -> Path:
        """Process and validate a path.

        Args:
            path: Path to process
            name: Name of the path (for error messages)
            required: Whether the path is required
            allow_creation: Whether to create the directory if it doesn't exist
            check_permissions: Whether to check read/write permissions

        Returns:
            Processed and validated Path object

        Raises:
            PathValidationError: If path validation fails
        """
        if path is None:
            if required:
                raise PathValidationError(PATH_REQUIRED_MSG.format(name=name))
            self.logger.debug(PATH_OPTIONAL_MSG.format(name=name))
            return None

        # Convert to absolute path
        path = Path(path).resolve()

        # Create directory if allowed and needed
        if allow_creation and not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
                self.logger.debug(PATH_CREATION_MSG.format(path=path))
            except Exception as e:
                raise PathValidationError(
                    ERROR_PATH_PROCESS.format(
                        name=name, error=f"Failed to create directory: {str(e)}"
                    )
                )

        # Validate existing path
        if path.exists():
            if not path.is_dir():
                raise PathValidationError(
                    ERROR_PATH_NOT_DIR.format(name=name, path=path)
                )

            if check_permissions:
                if not os.access(path, os.W_OK):
                    raise PathValidationError(
                        ERROR_PATH_NO_WRITE.format(name=name, path=path)
                    )
                if not os.access(path, os.R_OK):
                    raise PathValidationError(
                        ERROR_PATH_NO_READ.format(name=name, path=path)
                    )
        elif required:
            raise PathValidationError(ERROR_PATH_NOT_EXIST.format(name=name, path=path))

        return path

    def validate_relationships(
        self, paths: Dict[str, Path], allow_nesting: bool = True
    ) -> None:
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
                ValidationKeys.REQUIRED: False,
            },
            MetadataKeys.HELP: "Whether to create directories if they don't exist",
        },
    )

    # Backup settings
    backup_enabled: bool = field(
        default=False,
        metadata={
            MetadataKeys.VALIDATION: {
                ValidationKeys.TYPE: bool,
                ValidationKeys.REQUIRED: True,
            },
            MetadataKeys.HELP: "Enable backup functionality",
        },
    )

    backup_dir: Optional[Path] = field(
        default_factory=lambda: (
            Path(os.getenv("WRITER_BACKUP_DIR", ""))
            if os.getenv("WRITER_BACKUP_DIR")
            else None
        ),
        metadata={
            MetadataKeys.VALIDATION: {
                ValidationKeys.TYPE: Path,
                ValidationKeys.REQUIRED: False,
                "is_path": True,
            },
            MetadataKeys.HELP: "Directory for backups (required if backup_enabled is True)",
        },
    )

    # Base paths
    temp_dir: Path = field(
        default_factory=lambda: Path(
            os.getenv("WRITER_TEMP_DIR", DEFAULT_PATHS["temp"])
        ),
        metadata={
            MetadataKeys.IS_PATH: True,
            MetadataKeys.VALIDATION: {
                ValidationKeys.TYPE: Path,
                ValidationKeys.REQUIRED: True,
            },
            MetadataKeys.HELP: "Directory for temporary files",
        },
    )

    drafts_dir: Path = field(
        default_factory=lambda: Path(
            os.getenv("WRITER_DRAFTS_DIR", DEFAULT_PATHS["drafts"])
        ),
        metadata={
            MetadataKeys.IS_PATH: True,
            MetadataKeys.VALIDATION: {
                ValidationKeys.TYPE: Path,
                ValidationKeys.REQUIRED: True,
            },
            MetadataKeys.HELP: "Directory for draft Markdown files",
        },
    )

    finalized_dir: Path = field(
        default_factory=lambda: Path(
            os.getenv("WRITER_FINALIZED_DIR", DEFAULT_PATHS["finalized"])
        ),
        metadata={
            MetadataKeys.IS_PATH: True,
            MetadataKeys.VALIDATION: {
                ValidationKeys.TYPE: Path,
                ValidationKeys.REQUIRED: True,
            },
            MetadataKeys.HELP: "Directory for finalized Markdown files",
        },
    )

    # Numeric settings
    lock_timeout: int = field(
        default=DEFAULT_LOCK_TIMEOUT,
        metadata={
            MetadataKeys.VALIDATION: {
                ValidationKeys.TYPE: int,
                ValidationKeys.MIN: 1,
                ValidationKeys.ALLOW_ZERO: False,
            },
            MetadataKeys.HELP: "Lock timeout in seconds",
        },
    )

    max_file_size: int = field(
        default_factory=get_system_min_file_size,
        metadata={
            MetadataKeys.VALIDATION: {
                ValidationKeys.TYPE: int,
                ValidationKeys.MIN: 1,
                ValidationKeys.REQUIRED: True,
            },
            MetadataKeys.HELP: "Maximum file size in bytes",
        },
    )

    # List settings
    allowed_extensions: List[str] = field(
        default_factory=get_supported_extensions,
        metadata={
            MetadataKeys.VALIDATION: {
                ValidationKeys.TYPE: list,
                ValidationKeys.ELEMENT_TYPE: str,
                ValidationKeys.REQUIRED: True,
            },
            MetadataKeys.HELP: "List of allowed file extensions",
        },
    )

    # Compression settings
    compression_level: int = field(
        default_factory=get_max_compression_level,
        metadata={
            MetadataKeys.VALIDATION: {
                ValidationKeys.TYPE: int,
                ValidationKeys.MIN: 0,
                ValidationKeys.MAX: 9,
                ValidationKeys.REQUIRED: True,
            },
            MetadataKeys.HELP: "Compression level (0-9)",
        },
    )

    # String settings with pattern
    section_marker_template: str = field(
        default=SECTION_MARKER_TEMPLATE,
        metadata={
            MetadataKeys.VALIDATION: {
                ValidationKeys.TYPE: str,
                ValidationKeys.REQUIRED: True,
                ValidationKeys.PATTERN: r".*\{section_title\}.*",
            },
            MetadataKeys.HELP: "Template for section markers, must contain {section_title}",
        },
    )

    # Metadata and encoding configuration
    metadata_keys: Set[str] = field(
        default_factory=lambda: DEFAULT_METADATA_FIELDS,
        metadata={
            MetadataKeys.VALIDATION: {
                ValidationKeys.TYPE: set,
                ValidationKeys.REQUIRED: False,
            },
            MetadataKeys.HELP: "Required metadata fields for documents",
        },
    )

    metadata_validation_rules: Dict[str, Dict] = field(
        default_factory=dict,
        metadata={
            MetadataKeys.VALIDATION: {
                ValidationKeys.TYPE: dict,
                ValidationKeys.REQUIRED: False,
            },
            MetadataKeys.HELP: "Custom validation rules for metadata fields",
        },
    )

    default_encoding: str = field(
        default=DEFAULT_ENCODING,
        metadata={
            MetadataKeys.VALIDATION: {
                ValidationKeys.TYPE: str,
                ValidationKeys.REQUIRED: True,
                ValidationKeys.CHOICES: ["utf-8", "utf-16", "ascii"],
            },
            MetadataKeys.HELP: "Default encoding for Markdown files",
            MetadataKeys.EXAMPLE: "utf-8",
        },
    )

    def __post_init__(self):
        """Initialize after instance creation."""
        # Set up logging
        self.logger = logging.getLogger(__name__)

        # Initialize PathHandler
        self.path_handler = PathHandler(self.logger)

        # Validate all fields
        self._validate_fields()

        # Validate paths (this will also create directories if enabled)
        self._validate_paths()

    def _validate_fields(self) -> None:
        """Validate all configuration fields."""
        # Validate section marker template
        if "{section_title}" not in self.section_marker_template:
            raise ConfigurationError(
                ERROR_PATTERN_MISMATCH.format(
                    name="section_marker_template",
                    value=self.section_marker_template,
                    pattern="{section_title}",
                )
            )

        # Validate lock timeout
        if self.lock_timeout <= MIN_LOCK_RETRIES:
            raise ConfigurationError(
                ERROR_VALUE_TOO_SMALL.format(
                    name="lock_timeout", value=self.lock_timeout, min=MIN_LOCK_RETRIES
                )
            )

        # Validate max file size
        if self.max_file_size <= 0:
            raise ConfigurationError(
                ERROR_VALUE_TOO_SMALL.format(
                    name="max_file_size", value=self.max_file_size, min=1
                )
            )

        # Validate metadata keys
        if not all(isinstance(key, str) for key in self.metadata_keys):
            raise ConfigurationError(
                ERROR_INVALID_TYPE.format(
                    name="metadata_keys", got="mixed types", expected="str"
                )
            )

        # Validate encoding
        try:
            "test".encode(self.default_encoding)
        except LookupError:
            raise ConfigurationError(
                ERROR_INVALID_CONFIG.format(
                    error=f"Invalid value for 'default_encoding': {self.default_encoding}"
                )
            )

        # Validate compression level
        if not 0 <= self.compression_level <= 9:
            raise ConfigurationError(
                ERROR_VALUE_TOO_LARGE.format(
                    name="compression_level", value=self.compression_level, max=9
                )
            )

        # Validate allowed extensions
        if not all(ext.startswith(".") for ext in self.allowed_extensions):
            raise ConfigurationError("All extensions must start with '.'")

        # Add system-specific validations
        available_space = get_available_disk_space(self.temp_dir)
        if self.max_file_size > available_space:
            raise ConfigurationError(
                f"max_file_size ({self.max_file_size} bytes) exceeds available disk space "
                f"({available_space} bytes) in temp_dir"
            )

        max_compression = get_max_compression_level()
        if self.compression_level > max_compression:
            raise ConfigurationError(
                f"compression_level ({self.compression_level}) exceeds system maximum "
                f"({max_compression})"
            )

        supported_extensions = get_supported_extensions()
        unsupported = set(self.allowed_extensions) - set(supported_extensions)
        if unsupported:
            raise ConfigurationError(
                f"Unsupported file extensions: {', '.join(unsupported)}"
            )

    def _validate_paths(self) -> None:
        """Validate all configured paths."""
        self.logger.debug("Validating paths")

        # Process each path with appropriate settings
        self.temp_dir = self.path_handler.process_path(
            self.temp_dir,
            "temp_dir",
            required=True,
            allow_creation=self.create_directories,
        )

        self.drafts_dir = self.path_handler.process_path(
            self.drafts_dir,
            "drafts_dir",
            required=True,
            allow_creation=self.create_directories,
        )

        self.finalized_dir = self.path_handler.process_path(
            self.finalized_dir,
            "finalized_dir",
            required=True,
            allow_creation=self.create_directories,
        )

        # Process backup directory if enabled
        if self.backup_enabled:
            self.backup_dir = self.path_handler.process_path(
                self.backup_dir,
                "backup_dir",
                required=True,
                allow_creation=self.create_directories,
            )
        elif self.backup_dir is not None:
            self.logger.warning(LOG_BACKUP_WARNING)

        # Validate directory relationships
        self._validate_directory_relationships()

    def _validate_directory_relationships(self) -> None:
        """Validate relationships between configured directories."""
        self.logger.debug("Validating directory relationships")

        # Collect all configured directories
        directories = {
            "temp_dir": self.temp_dir,
            "drafts_dir": self.drafts_dir,
            "finalized_dir": self.finalized_dir,
        }

        # Add backup directory if enabled
        if self.backup_enabled and self.backup_dir is not None:
            directories["backup_dir"] = self.backup_dir

        # Validate relationships using PathHandler
        try:
            self.path_handler.validate_relationships(directories, allow_nesting=False)
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
                    allow_creation=self.create_directories,
                    must_be_directory=True,
                    check_permissions=True,
                )

            # Validate directory relationships
            other_dirs = [self.temp_dir, self.drafts_dir, self.finalized_dir]
            if any(
                self.backup_dir.samefile(dir_path)
                for dir_path in other_dirs
                if dir_path is not None and dir_path.exists()
            ):
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
            self._validate_path_settings,
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
        
        min_header_depth = HEADER_LEVEL_RANGE[0]
        max_header_depth = HEADER_LEVEL_RANGE[-1]
        if not min_header_depth <= self.max_section_depth <= max_header_depth:
            raise ConfigurationError(
                f"max_section_depth must be between {min_header_depth} and {max_header_depth}"
            )

    def _validate_file_operations(self) -> None:
        """Validate file operation settings."""
        # Validate file size limit
        if self.max_file_size_mb <= 0:
            raise ConfigurationError("max_file_size_mb must be positive")

        # Validate extensions
        for ext in self.allowed_extensions:
            if not ext.startswith("."):
                raise ConfigurationError(f"Extension must start with '.': {ext}")
            if not re.match(EXTENSION_PATTERN, ext):
                raise ConfigurationError(f"Invalid extension format: {ext}")

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
                    check_permissions=True,
                )

            # Validate directory relationships
            other_dirs = [self.temp_dir, self.drafts_dir, self.finalized_dir]
            if any(
                self.backup_dir.samefile(dir_path)
                for dir_path in other_dirs
                if dir_path is not None and dir_path.exists()
            ):
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
            raise ConfigurationError(
                f"Unknown configuration fields: {', '.join(unknown_fields)}"
            )

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
            f.name for f in fields(cls) if f.metadata.get(MetadataKeys.IS_PATH, False)
        ]

    @classmethod
    def _get_required_paths(cls) -> List[str]:
        """Get required path attributes from field metadata."""
        return [
            f.name
            for f in fields(cls)
            if f.metadata.get(MetadataKeys.IS_PATH, False)
            and f.metadata.get(MetadataKeys.REQUIRED, False)
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
            FIELD_INFO_TYPE: metadata.get(MetadataKeys.VALIDATION, {}).get(
                ValidationKeys.TYPE, field.type
            ),
            FIELD_INFO_HELP: metadata.get(MetadataKeys.HELP, NO_DESCRIPTION),
            FIELD_INFO_REQUIRED: metadata.get(MetadataKeys.VALIDATION, {}).get(
                ValidationKeys.REQUIRED, False
            ),
        }

        # Add default value information
        default_info = metadata.get(MetadataKeys.DEFAULT, {})
        if FIELD_INFO_VALUE in default_info:
            info[FIELD_INFO_DEFAULT] = default_info[FIELD_INFO_VALUE]
        elif FIELD_INFO_FACTORY in default_info:
            info[FIELD_INFO_DEFAULT] = (
                f"{FACTORY_PREFIX}{default_info[FIELD_INFO_FACTORY]}"
            )
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
            constraints.append(
                CONSTRAINT_PATTERN_FORMAT.format(validation[KEY_PATTERN])
            )
        if KEY_CHOICES in validation:
            constraints.append(
                CONSTRAINT_CHOICES_FORMAT.format(
                    ", ".join(map(str, validation[KEY_CHOICES]))
                )
            )

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
                        ERROR_GET_DEFAULT.format(name=field_obj.name, error=str(e))
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
