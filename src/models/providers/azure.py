from typing import Dict
from ..base import ModelConfig, ModelProvider, ModelCapabilities
from ..constants import VISION_MIME_TYPES, AUDIO_MIME_TYPES, MULTIMODAL_MIME_TYPES

AZURE_MODELS: Dict[str, ModelConfig] = {
    "o1-preview": ModelConfig(
        provider=ModelProvider.AZURE,
        name="o1-preview",
        description="Advanced model designed for reasoning and problem-solving tasks.",
        capabilities=ModelCapabilities(
            supports_chat=True,
            max_context_tokens=128000,
            max_output_tokens=32768,
            supports_functions=False,
            supports_json_mode=False,
            default_temperature=0.7,
        ),
    ),
    "o1-mini": ModelConfig(
        provider=ModelProvider.AZURE,
        name="o1-mini",
        description="Efficient model for reasoning tasks with faster response times.",
        capabilities=ModelCapabilities(
            supports_chat=True,
            max_context_tokens=128000,
            max_output_tokens=65536,
            supports_functions=False,
            supports_json_mode=False,
            default_temperature=0.7,
        ),
    ),
    "gpt-4o": ModelConfig(
        provider=ModelProvider.AZURE,
        name="gpt-4o",
        description="Latest multimodal model accepting both text and images.",
        capabilities=ModelCapabilities(
            supports_chat=True,
            max_context_tokens=128000,
            max_output_tokens=4096,
            supports_functions=True,
            supports_json_mode=True,
            supports_vision=True,
            default_temperature=0.7,
        ),
        supported_mime_types=VISION_MIME_TYPES,
    ),
    "gpt-4o-mini": ModelConfig(
        provider=ModelProvider.AZURE,
        name="gpt-4o-mini",
        description="Compact version of GPT-4o with multimodal capabilities.",
        capabilities=ModelCapabilities(
            supports_chat=True,
            max_context_tokens=128000,
            max_output_tokens=4096,
            supports_functions=True,
            supports_json_mode=True,
            supports_vision=True,
            default_temperature=0.7,
        ),
        supported_mime_types=VISION_MIME_TYPES,
    ),
    "gpt-4o-realtime-preview": ModelConfig(
        provider=ModelProvider.AZURE,
        name="gpt-4o-realtime-preview",
        description="Low-latency model supporting 'speech in, speech out' interactions.",
        capabilities=ModelCapabilities(
            supports_chat=True,
            max_context_tokens=128000,
            max_output_tokens=4096,
            supports_functions=True,
            supports_json_mode=True,
            supports_vision=True,
            supports_audio_input=True,
            supports_audio_output=True,
            default_temperature=0.7,
        ),
        supported_mime_types=MULTIMODAL_MIME_TYPES,
    ),
    "gpt-4": ModelConfig(
        provider=ModelProvider.AZURE,
        name="gpt-4",
        description="Advanced model improving upon GPT-3.5 for natural language and code generation.",
        capabilities=ModelCapabilities(
            supports_chat=True,
            max_context_tokens=8192,
            max_output_tokens=4096,
            supports_functions=True,
            supports_json_mode=True,
            default_temperature=0.7,
        ),
    ),
    "gpt-3.5": ModelConfig(
        provider=ModelProvider.AZURE,
        name="gpt-3.5",
        description="Enhanced model over GPT-3 for natural language and code generation.",
        capabilities=ModelCapabilities(
            supports_chat=True,
            max_context_tokens=4096,
            max_output_tokens=2048,
            supports_functions=True,
            supports_json_mode=True,
            default_temperature=0.7,
        ),
    ),
    "text-embedding-ada-002": ModelConfig(
        provider=ModelProvider.AZURE,
        name="text-embedding-ada-002",
        description="Model converting text into numerical vectors for text similarity.",
        capabilities=ModelCapabilities(
            supports_embedding=True,
            max_context_tokens=8191,
            max_output_tokens=None,
            supports_streaming=False,
            default_temperature=0.0,
        ),
    ),
    "dall-e": ModelConfig(
        provider=ModelProvider.AZURE,
        name="dall-e",
        description="Model generating original images from natural language descriptions.",
        capabilities=ModelCapabilities(
            supports_image_generation=True,
            max_context_tokens=None,
            max_output_tokens=None,
            supports_streaming=False,
            default_temperature=0.0,
        ),
    ),
    "whisper": ModelConfig(
        provider=ModelProvider.AZURE,
        name="whisper",
        description="Model transcribing and translating speech to text.",
        capabilities=ModelCapabilities(
            supports_speech_recognition=True,
            supports_streaming=True,
            supports_audio_input=True,
            default_temperature=0.0,
        ),
        supported_mime_types=AUDIO_MIME_TYPES,
    ),
    "text-to-speech": ModelConfig(
        provider=ModelProvider.AZURE,
        name="text-to-speech",
        description="Model synthesizing text into speech.",
        capabilities=ModelCapabilities(
            supports_speech_synthesis=True,
            supports_streaming=True,
            supports_audio_output=True,
            default_temperature=0.0,
        ),
        supported_mime_types=AUDIO_MIME_TYPES,
    ),
}


def get_azure_model(model_name: str, deployment_name: str = None) -> ModelConfig:
    """
    Get Azure model configuration by name.

    Args:
        model_name: The name of the model
        deployment_name: Optional Azure deployment name

    Returns:
        ModelConfig for the specified model

    Raises:
        ValueError: If model_name is not found
    """
    if model_name not in AZURE_MODELS:
        raise ValueError(
            f"Unknown Azure model: {model_name}. "
            f"Available models: {', '.join(AZURE_MODELS.keys())}"
        )

    base_config = AZURE_MODELS[model_name]
    
    # If deployment_name is provided, create a new config with the override
    if deployment_name:
        return base_config.clone_with(deployment_name=deployment_name)

    return base_config
