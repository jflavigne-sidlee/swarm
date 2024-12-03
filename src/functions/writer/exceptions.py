from typing import Optional

class WriterError(Exception):
    """Base exception class for writer module errors."""
    pass

class SectionError(WriterError):
    """Base class for section-related errors."""
    def __init__(self, section_title: str, message: Optional[str] = None):
        self.section_title = section_title
        super().__init__(message or f"Error with section: {section_title}")

class SectionNotFoundError(SectionError):
    """Raised when a section cannot be found in the document."""
    def __init__(self, section_title: str):
        super().__init__(section_title, f"Section not found: {section_title}")

class DuplicateSectionError(SectionError):
    """Raised when a duplicate section is found."""
    def __init__(self, section_title: str):
        super().__init__(section_title, f"Duplicate section found: {section_title}")

class FileValidationError(WriterError):
    """Base class for file validation errors."""
    def __init__(self, file_path: str, message: Optional[str] = None):
        self.file_path = file_path
        super().__init__(message or f"File validation error: {file_path}")

class FilePermissionError(FileValidationError):
    """Raised when file permissions are insufficient."""
    def __init__(self, file_path: str):
        super().__init__(file_path, f"Permission denied: {file_path}")

class InvalidMarkdownError(FileValidationError):
    """Raised when file is not a valid Markdown document."""
    def __init__(self, file_path: str):
        super().__init__(file_path, f"Invalid Markdown file: {file_path}")

class ConfigurationError(WriterError):
    """Raised when there's an error in configuration."""
    pass

class PathValidationError(ConfigurationError):
    """Raised when a path is invalid or not accessible."""
    pass

class LockAcquisitionError(WriterError):
    """Raised when a section lock cannot be acquired."""
    pass 

class InvalidChunkSizeError(ValueError):
    """Raised when the chunk size is not a positive integer."""
    pass

class WritePermissionError(IOError):
    """Raised when the file cannot be written to."""
    pass

class MarkdownIntegrityError(ValueError):
    """Raised when content would break Markdown formatting."""
    pass