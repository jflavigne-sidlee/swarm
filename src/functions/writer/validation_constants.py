from typing import Set, Final
from enum import Enum

class MetadataKeys(str, Enum):
    """Enumeration of metadata keys."""

    VALIDATION = "validation"
    DEFAULT = "default"
    HELP = "help"
    EXAMPLE = "example"
    CONSTRAINTS = "constraints"
    TYPE = "type"
    REQUIRED = "required"
    IS_PATH = "is_path"


class ValidationKeys(str, Enum):
    """Enumeration of validation keys."""

    TYPE = "type"
    MIN = "min_value"
    MAX = "max_value"
    PATTERN = "pattern"
    CHOICES = "choices"
    ALLOW_ZERO = "allow_zero"
    ELEMENT_TYPE = "element_type"
    VALIDATE = "validate"
    REQUIRED = "required"
    DEFAULT = "default"
    HELP = "help"
    EXAMPLE = "example"
    CONSTRAINTS = "constraints"

# Validation keys
VALIDATION_KEY_TYPE: Final = "type"
VALIDATION_KEY_MIN_VALUE: Final = "min_value"
VALIDATION_KEY_MAX_VALUE: Final = "max_value"
VALIDATION_KEY_PATTERN: Final = "pattern"
VALIDATION_KEY_CHOICES: Final = "choices"
VALIDATION_KEY_ALLOW_ZERO: Final = "allow_zero"
VALIDATION_KEY_ELEMENT_TYPE: Final = "element_type"
VALIDATION_KEY_VALIDATE: Final = "validate"
# Keys for section data
SECTION_HEADER_KEY: Final = "header"
SECTION_MARKER_KEY: Final = "marker"
SECTION_CONTENT_KEY: Final = "section_content"

# Path validation
PATH_MUST_EXIST: Final = True
PATH_MUST_BE_DIRECTORY: Final = True
PATH_CHECK_PERMISSIONS: Final = True

# Constraint format strings
CONSTRAINT_TYPE_FORMAT: Final = "type={}"
CONSTRAINT_MIN_FORMAT: Final = ">= {}"
CONSTRAINT_MAX_FORMAT: Final = "<= {}"
CONSTRAINT_PATTERN_FORMAT: Final = "matches pattern: {}"
CONSTRAINT_CHOICES_FORMAT: Final = "one of: {}"
CONSTRAINT_JOIN_STR: Final = " and "

# Dictionary key strings
KEY_MIN_VALUE: Final = "min_value"
KEY_MAX_VALUE: Final = "max_value"
KEY_PATTERN: Final = "pattern"
KEY_CHOICES: Final = "choices"
KEY_CONSTRAINTS: Final = "constraints"

# Validation Constants
FILENAME_MAX_LENGTH: Final = 255  # Maximum filename length
PATH_MAX_LENGTH: Final = 4096  # Maximum path length for most filesystems
# File validation constants
MAX_FILENAME_LENGTH: Final = 255
MAX_PATH_LENGTH: Final = 260  # Windows MAX_PATH limit
FORBIDDEN_FILENAME_CHARS: Final = '<>:"/\\|?*\0'
RESERVED_WINDOWS_FILENAMES: Final[Set[str]] = {
    "CON",
    "PRN",
    "AUX",
    "NUL",  # Device names
    "COM1",
    "COM2",
    "COM3",
    "COM4",  # COM ports
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",  # Printer ports
}

# Markdown format extensions
MARKDOWN_EXTENSION_GFM: Final = "gfm"

# Pandoc error messages
LATEX_MATH_ERROR: Final = "Error parsing latex math"
PANDOC_STDERR_ATTR: Final = 'stderr'

# Task list markers and patterns
TASK_LIST_MARKER_DASH = '-'
TASK_LIST_BRACKET_START = '['
TASK_LIST_DOUBLE_SPACE = '  '

# Code block markers
CODE_BLOCK_MARKER = '```'
# Pandoc command arguments
PANDOC_VERSION_ARG = '--version'

# Common string patterns
COLON_SEPARATOR = ':'
EMPTY_STRING = ''

# LaTeX indicators
LATEX_STRIKETHROUGH = '~~'
GFM_TASK_LIST_MARKER = '- [ ]'
