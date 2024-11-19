from typing import Dict
from ..base import ModelConfig, ModelProvider, ModelCapabilities

# Supported MIME types for vision models
VISION_MIME_TYPES = [
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp"
]

OPENAI_MODELS: Dict[str, ModelConfig] = {
    "gpt-4-turbo-preview": ModelConfig(
        provider=ModelProvider.OPENAI,
        name="gpt-4-turbo-preview",
        description="Most capable GPT-4 model, optimized for speed",
        version="0125",  # Latest version as of now
        capabilities=ModelCapabilities(
            supports_chat=True,
            max_context_tokens=128000,
            max_output_tokens=4096,
            supports_functions=True,
            supports_json_mode=True,
            default_temperature=0.7
        )
    ),
    
    "gpt-4-vision-preview": ModelConfig(
        provider=ModelProvider.OPENAI,
        name="gpt-4-vision-preview",
        description="GPT-4 Turbo with vision capabilities",
        capabilities=ModelCapabilities(
            supports_chat=True,
            max_context_tokens=128000,
            max_output_tokens=4096,
            supports_functions=True,
            supports_json_mode=True,
            supports_vision=True,
            default_temperature=0.7
        ),
        supported_mime_types=VISION_MIME_TYPES
    ),
    
    "gpt-4": ModelConfig(
        provider=ModelProvider.OPENAI,
        name="gpt-4",
        description="GPT-4 base model",
        capabilities=ModelCapabilities(
            supports_chat=True,
            max_context_tokens=8192,
            max_output_tokens=4096,
            supports_functions=True,
            supports_json_mode=True,
            default_temperature=0.7
        )
    ),
    
    "gpt-3.5-turbo": ModelConfig(
        provider=ModelProvider.OPENAI,
        name="gpt-3.5-turbo",
        description="Most capable GPT-3.5 model",
        version="0125",  # Latest version
        capabilities=ModelCapabilities(
            supports_chat=True,
            max_context_tokens=16385,
            max_output_tokens=4096,
            supports_functions=True,
            supports_json_mode=True,
            default_temperature=0.7
        )
    ),
    
    "text-embedding-3-small": ModelConfig(
        provider=ModelProvider.OPENAI,
        name="text-embedding-3-small",
        description="Smaller, cost-effective embedding model",
        capabilities=ModelCapabilities(
            supports_embedding=True,
            max_context_tokens=8191,
            max_output_tokens=None,
            supports_streaming=False,
            default_temperature=0.0
        )
    ),
    
    "text-embedding-3-large": ModelConfig(
        provider=ModelProvider.OPENAI,
        name="text-embedding-3-large",
        description="Most capable embedding model",
        capabilities=ModelCapabilities(
            supports_embedding=True,
            max_context_tokens=8191,
            max_output_tokens=None,
            supports_streaming=False,
            default_temperature=0.0
        )
    ),
    
    "dall-e-3": ModelConfig(
        provider=ModelProvider.OPENAI,
        name="dall-e-3",
        description="Most capable image generation model",
        capabilities=ModelCapabilities(
            supports_chat=False,
            max_context_tokens=4096,  # This is approximate for text prompt
            max_output_tokens=None,
            supports_streaming=False,
            default_temperature=0.7
        ),
        supported_mime_types=["image/png"]  # Output format
    )
}

def get_openai_model(model_name: str) -> ModelConfig:
    """Get OpenAI model configuration by name.
    
    Args:
        model_name: The name of the model
        
    Returns:
        ModelConfig for the specified model
        
    Raises:
        ValueError: If model_name is not found
    """
    if model_name not in OPENAI_MODELS:
        raise ValueError(
            f"Unknown OpenAI model: {model_name}. "
            f"Available models: {', '.join(OPENAI_MODELS.keys())}"
        )
    
    return OPENAI_MODELS[model_name] 