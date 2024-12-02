"""Constants for the writer module configuration."""

from enum import Enum, auto
from typing import Set, List, Dict, Type, Final
import os

# Environment variable names
ENV_PREFIX: Final = "WRITER_"
ENV_TEMP_DIR: Final = f"{ENV_PREFIX}TEMP_DIR"
ENV_DRAFTS_DIR: Final = f"{ENV_PREFIX}DRAFTS_DIR"
ENV_FINALIZED_DIR: Final = f"{ENV_PREFIX}FINALIZED_DIR"
ENV_BACKUP_DIR: Final = f"{ENV_PREFIX}BACKUP_DIR"

# Default paths with environment variable support
DEFAULT_BASE_PATH: Final = os.getenv(f"{ENV_PREFIX}BASE_PATH", "data")
DEFAULT_PATHS: Final[Dict[str, str]] = {
    "temp": os.getenv(ENV_TEMP_DIR, f"{DEFAULT_BASE_PATH}/temp"),
    "drafts": os.getenv(ENV_DRAFTS_DIR, f"{DEFAULT_BASE_PATH}/drafts"),
    "finalized": os.getenv(ENV_FINALIZED_DIR, f"{DEFAULT_BASE_PATH}/finalized"),
}

DEFAULT_METADATA_FIELDS: Final[Set[str]] = {'title', 'author', 'date'}
DEFAULT_ENCODING: Final = "utf-8"

# File operations
DEFAULT_MAX_FILE_SIZE_MB: Final = 10.0
DEFAULT_MAX_FILE_SIZE: Final = int(
    DEFAULT_MAX_FILE_SIZE_MB * 1024 * 1024
)  # Convert MB to bytes
ALLOWED_EXTENSIONS: Final[List[str]] = [".md", ".markdown"]

# Version control
DEFAULT_VERSION_FORMAT: Final = "{base_name}_v{version}{ext}"
MIN_VERSIONS: Final = 1
DEFAULT_VERSIONS: Final = 5

# Locking
DEFAULT_LOCK_TIMEOUT: Final = 300  # 5 minutes in seconds
LOCK_FILE_SUFFIX = ".lock"
LOCK_METADATA_FORMAT = "lock_{section_title}"
MIN_LOCK_RETRIES: Final = 1
DEFAULT_LOCK_RETRIES: Final = 3
MIN_RETRY_DELAY: Final = 0
DEFAULT_RETRY_DELAY: Final = 5

# File operation constants
MD_EXTENSION: Final = ".md"

# File mode constants
FILE_MODE_READ: Final = "r"
FILE_MODE_WRITE: Final = "w"
FILE_MODE_APPEND: Final = "a"
FILE_MODE_READ_BINARY: Final = "rb"
FILE_MODE_WRITE_BINARY: Final = "wb"
FILE_MODE_APPEND_BINARY: Final = "ab"

# External tool configurations
REMARK_CONFIG_FILE: Final = ".remarkrc.js"
MARKDOWNLINT_CONFIG_FILE: Final = ".markdownlint.json"
PANDOC_FROM_FORMAT: Final = "markdown"
PANDOC_TO_FORMAT: Final = "html"
# External tool configurations
PANDOC_COMMAND: Final = "pandoc"
PANDOC_FROM_ARG: Final = "--from"
PANDOC_TO_ARG: Final = "--to"

# Markdown formatting options
MDFORMAT_OPTIONS: Final[Dict[str, bool]] = {"check": True, "number": True, "wrap": "no"}
MDFORMAT_EXTENSIONS: Final[List[str]] = ["gfm", "tables"]

# URL prefixes
HTTP_PREFIX: Final = "http://"
HTTPS_PREFIX: Final = "https://"
URL_PREFIXES: Final = (HTTP_PREFIX, HTTPS_PREFIX)

# Pandoc-related constants and error messages
PANDOC_COMMAND: Final = "pandoc"

MARKDOWN_EXTENSION_GFM = "gfm"  # Define the GFM extension constant

# Lock metadata keys
LOCK_METADATA_SECTION = "section"
LOCK_METADATA_TIMESTAMP = "timestamp"
LOCK_METADATA_FILE = "file"
LOCK_METADATA_AGENT = "agent_id"
