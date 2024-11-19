class ImageAnalysisError(Exception):
    """Base exception for image analysis errors."""
    pass

class ImageValidationError(ImageAnalysisError):
    """Raised when image validation fails."""
    pass

class APIError(ImageAnalysisError):
    """Raised when API calls fail."""
    pass
