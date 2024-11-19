"""Exceptions for model-related operations."""

class ModelError(Exception):
    """Base class for model-related exceptions."""
    pass

class ModelNotFoundError(ModelError):
    """Raised when a requested model cannot be found."""
    def __init__(self, model_name: str, provider: str = None, suggestion: str = None):
        self.model_name = model_name
        self.provider = provider
        self.suggestion = suggestion
        
        msg = f"Model '{model_name}' not found"
        if provider:
            msg += f" for provider '{provider}'"
        if suggestion:
            msg += f". Did you mean '{suggestion}'?"
        
        super().__init__(msg)

class InvalidModelConfigError(ModelError):
    """Raised when a model configuration is invalid."""
    pass

class ModelCapabilityError(ModelError):
    """Raised when attempting to use an unsupported model capability."""
    def __init__(self, model_name: str, capability: str):
        self.model_name = model_name
        self.capability = capability
        msg = f"Model '{model_name}' does not support capability '{capability}'"
        super().__init__(msg)

class ModelProviderError(ModelError):
    """Raised for provider-specific errors."""
    def __init__(self, provider: str, message: str):
        self.provider = provider
        msg = f"Provider '{provider}' error: {message}"
        super().__init__(msg)

class DeploymentNameError(ModelError):
    """Raised when there are issues with Azure deployment names."""
    def __init__(self, model_name: str, message: str):
        self.model_name = model_name
        msg = f"Deployment name error for model '{model_name}': {message}"
        super().__init__(msg) 