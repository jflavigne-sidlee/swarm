# Section marker patterns
from typing import Set, List, Dict, Final
import re

SECTION_MARKER_TEMPLATE: Final = "<!-- Section: {section_title} -->"

PATTERN_SECTION_MARKER: Final = r"<!--\s*(?:Section|SECTION):\s*(.+?)\s*-->"
PATTERN_HEADER: Final = r"^(#{1,6})\s+(.+?)$"
PATTERN_HEADER_WITH_NEWLINE: Final = r"^(#{1,6}\s+.+\n)"
PATTERN_NEXT_HEADER: Final = r"^#{1,6}\s+.*$"
PATTERN_UNTIL_NEXT_HEADER: Final = r"^#{1,6}\s"
PATTERN_NEWLINE: Final = r"\n"
SECTION_CONTENT_PATTERN: Final = (
    r"<!--\s*(?:Section|SECTION):"  # For checking marker format
)

PATTERN_HEADER_LEVEL: Final = r"^#+"
PATTERN_HEADER_TEXT: Final = r"^#+\s*(.*?)\s*$"

PATTERN_IMAGE_LINK: Final = r"!\[([^\]]*)\]\(([^)]+)\)"
PATTERN_FILE_LINK: Final = r"\[([^\]]+)\]\(([^)]+)\)"

INSERT_AFTER_MARKER: Final = "<!-- Section: {insert_after} -->"


VERSION_FORMAT_PLACEHOLDERS: Final[List[str]] = ["{version}", "{base_name}", "{ext}"]
ALLOWED_VERSION_PLACEHOLDERS: Final[Set[str]] = {"version", "base_name", "ext"}
VERSION_PLACEHOLDER_PATTERN: Final = r"{([^{}:]+)(?::[^}]+)?}"
VERSION_FORMAT_SPEC_PATTERN: Final = r"{([^{}:]+):([^}]+)}"
VERSION_PADDING_PATTERN: Final = r"^0>[1-9][0-9]*$"

EXTENSION_PATTERN: Final = r"^\.[a-zA-Z0-9]+$"

# Regular expression patterns
HEADER_PATTERN_MULTILINE: Final = re.compile(PATTERN_HEADER, re.MULTILINE)
MARKER_PATTERN_MULTILINE: Final = re.compile(PATTERN_SECTION_MARKER)
YAML_CONTENT_PATTERN: Final = r"^---\n.*?\n---\n"  # For finding YAML frontmatter

# Regular Expression Patterns
SECTION_START_PATTERN: Final = r"^#{1,6}\s+.*$"  # For finding section headers
SECTION_END_PATTERN: Final = r"\n#{1,6}\s+"  # For finding the next section
CONTENT_SPACING_PATTERN: Final = r"\n\n"  # For normalizing spacing between sections
YAML_FRONTMATTER_PATTERN: Final = (
    r"^---\n.*?\n---\n\s*"  # For matching YAML frontmatter
)

# Regular expression pattern for section markers
SECTION_MARKER_REGEX: Final = r"<!-- Section: .* -->"


# Validation patterns
HEADER_TITLE_GROUP: Final = 2  # Index of the header title group in regex match
MARKER_TITLE_GROUP: Final = 1  # Index of the marker title group in regex match

VALID_MARKDOWN_FLAVORS: Final[Set[str]] = {"github", "commonmark", "strict"}

# Header level constants
HEADER_LEVEL_RANGE: Final = range(1, 7)  # Valid header levels (1-6)

SECTION_HEADER_PREFIX: Final = "#"  # Markdown header prefix

# Markdown header prefix for level 2
HEADER_LEVEL_2_PREFIX: Final = "\n##"

# YAML frontmatter markers
YAML_FRONTMATTER_START: Final = "---\n"
YAML_FRONTMATTER_END: Final = "\n---\n"
FRONTMATTER_MARKER: Final = "---"  # YAML frontmatter delimiter


YAML_DUMP_SETTINGS: Final[Dict[str, bool]] = {
    "default_flow_style": False,
    "sort_keys": False,
}

# File content formatting
DEFAULT_NEWLINE: Final = "\n"
DOUBLE_NEWLINE: Final = "\n\n"

# Section content format
SECTION_CONTENT_FORMAT: Final = (
    "{spacing}{header_prefix} {section_title}\n{section_marker}\n{content}\n"
)

# pytest tests/functions/writer/test_metadata_operations.py -v -s

# Task list patterns
PATTERN_TASK_LIST_MISSING_SPACE_AFTER = r'^- \[[ xX]\](?!\s)'
PATTERN_TASK_LIST_VALID = r'^- \[[ xX]\] .+$'
PATTERN_TASK_LIST_MARKER: Final = r"^- \[([ xX])\] "
PATTERN_MARKDOWNLINT_ERROR: Final = r".*:(\d+):\s*(MD\d+)\s*(.+)"

# Regex flags for search operations
REGEX_FLAGS_CASE_INSENSITIVE = re.IGNORECASE
REGEX_FLAGS_CASE_SENSITIVE = 0

# Error messages (add to errors.py)
ERROR_EMPTY_SEARCH_TEXT = "Search text cannot be empty"
ERROR_INVALID_REGEX = "Invalid regular expression pattern: {error}"
ERROR_SEARCH_REPLACE_FAILED = "Search and replace operation failed: {error}"

# Log messages (add to logs.py)
LOG_SEARCH_REPLACE_START = "Starting search/replace in {file_path}"
LOG_SEARCH_REPLACE_COMPLETE = "Completed search/replace: {count} replacements made"
LOG_NO_MATCHES_FOUND = "No matches found for search text"