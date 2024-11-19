class AssistantError(Exception):
    """Base exception for assistant operations."""
    pass

class AssistantCreationError(AssistantError):
    """Raised when assistant creation fails."""
    pass

class AssistantNotFoundError(AssistantError):
    """Raised when an assistant cannot be found."""
    pass

class AssistantUpdateError(AssistantError):
    """Raised when assistant update fails."""
    pass 