class WriterError(Exception):
    """Base exception class for writer module."""
    pass

class ConfigurationError(WriterError):
    """Raised when there's an error in configuration."""
    pass

class PathValidationError(ConfigurationError):
    """Raised when a path is invalid or not accessible."""
    pass 