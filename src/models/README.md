# AI Model Configuration System

A flexible and type-safe configuration system for managing AI model definitions, capabilities, and provider-specific settings.

## Overview

This module provides a centralized registry for managing AI model configurations across different providers (Azure, OpenAI, etc.). It handles:

- Model capabilities and limitations
- Provider-specific configurations
- Deployment overrides
- MIME type validation for multimodal models
- Environment-based configuration

## Core Components

### ModelConfig

Represents a complete model configuration including:

- Provider information
- Model capabilities
- Version information
- Deployment settings
- MIME type support
- Description and metadata

```python
model = ModelConfig(
    provider=ModelProvider.AZURE,
    name="gpt-4",
    capabilities=ModelCapabilities(
    supports_chat=True,
    max_context_tokens=8192,
        supports_functions=True
    ),
    deployment_name="my-deployment"
)
```

### ModelCapabilities

Defines what a model can do and its limitations:

- Text capabilities (chat, embeddings)
- Vision capabilities
- Audio capabilities (speech recognition, synthesis)
- Token limits
- Temperature settings
- Streaming support

```python
capabilities = ModelCapabilities(
    supports_chat=True,
    supports_vision=True,
    max_context_tokens=4096,
    supports_functions=True
)
```

### ModelRegistry

Central registry for managing model configurations:

- Loading and validating models
- Handling deployment overrides
- Filtering models by capability
- Provider-specific model management

## Usage Examples

### Basic Model Access

```python
from src.models.config import get_model, list_models
from src.models.base import ModelProvider

# Get a specific model
model = get_model("gpt-4")

# List all models
all_models = list_models()

# List models from a specific provider
azure_models = list_models(provider=ModelProvider.AZURE)
```

### Filtering Models by Capability

```python
# Get vision-capable models
vision_models = list_models(capability="supports_vision")

# Get models that support both chat and functions
def custom_filter(model):
    return (model.capabilities.supports_chat and
            model.capabilities.supports_functions)

advanced_models = list_models(capability=custom_filter)
```

### Environment Configuration

The system supports environment variables for deployment configuration:

```bash
# Global deployment override for Azure
export AZURE_DEPLOYMENT_OVERRIDE="my-deployment"

# Model-specific deployment
export AZURE_DEPLOYMENT_GPT_4="gpt4-deployment"
```

### Adding Custom Models

```python
from src.models.base import ModelConfig, ModelCapabilities

custom_model = ModelConfig(
    provider=ModelProvider.AZURE,
    name="custom-model",
    capabilities=ModelCapabilities(
        supports_chat=True,
        max_context_tokens=4096
    ),
    deployment_name="custom-deployment"
)

registry.add_model(custom_model)
```

## MIME Type Support

Models with media capabilities (vision, audio) must specify supported MIME types:

```python
vision_model = ModelConfig(
    provider=ModelProvider.AZURE,
    name="vision-model",
    capabilities=ModelCapabilities(supports_vision=True),
    supported_mime_types=["image/jpeg", "image/png"]
)
```

## Provider Support

### Azure

- Deployment name overrides
- Environment-based configuration
- Custom deployment mapping

### OpenAI

- Standard model configurations
- Vision and image generation support
- Embedding models

## Best Practices

1. **Use Type Hints**: All components are type-safe and support IDE autocompletion
2. **Environment Configuration**: Use environment variables for deployment settings
3. **Capability Checking**: Always verify model capabilities before use
4. **Error Handling**: Handle configuration errors appropriately
5. **MIME Type Validation**: Specify supported formats for media-capable models

## Error Handling

The system provides detailed error messages for common issues:

- Invalid model configurations
- Missing MIME types
- Deployment conflicts
- Unknown capabilities
- Provider validation errors

## Contributing

When adding new models or capabilities:

1. Update the appropriate provider file
2. Add necessary MIME types
3. Update capability definitions if needed
4. Add tests for new functionality
5. Document any new features or changes

