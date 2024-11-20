import pytest
from src.models.base import ModelProvider, ModelCapabilities, ModelConfig
from pydantic import ValidationError


class TestModelCapabilities:
    """Test suite for model capabilities."""

    def test_chat_model_capabilities(self):
        """Test chat model capabilities configuration."""
        chat_caps = ModelCapabilities(
            supports_chat=True,
            max_context_tokens=4096,
            max_output_tokens=1000,
            supports_functions=True,
            default_temperature=0.7,
        )
        assert chat_caps.supports_chat is True
        assert chat_caps.max_context_tokens == 4096
        assert chat_caps.supports_embedding is False  # Default false

    def test_embedding_model_capabilities(self):
        """Test embedding model capabilities configuration."""
        embed_caps = ModelCapabilities(
            supports_embedding=True,
            max_context_tokens=8191,
            max_output_tokens=None,  # Embeddings don't have output tokens
            supports_streaming=False,
            default_temperature=0.0,
        )
        assert embed_caps.supports_embedding is True
        assert embed_caps.max_context_tokens == 8191
        assert embed_caps.max_output_tokens is None
        assert embed_caps.supports_streaming is False

    def test_image_generation_capabilities(self):
        """Test DALL-E model capabilities configuration."""
        dalle_caps = ModelCapabilities(
            supports_image_generation=True,
            max_context_tokens=None,  # No token limits for image generation
            max_output_tokens=None,
            supports_streaming=False,
            default_temperature=0.0,
        )
        assert dalle_caps.supports_image_generation is True
        assert dalle_caps.max_context_tokens is None
        assert dalle_caps.max_output_tokens is None

    def test_speech_model_capabilities(self):
        """Test speech model capabilities configuration."""
        whisper_caps = ModelCapabilities(
            supports_speech_recognition=True,
            max_context_tokens=None,
            max_output_tokens=None,
            supports_streaming=True,
            supports_audio_input=True,
        )
        assert whisper_caps.supports_speech_recognition is True
        assert whisper_caps.supports_audio_input is True

        tts_caps = ModelCapabilities(
            supports_speech_synthesis=True,
            max_context_tokens=None,
            max_output_tokens=None,
            supports_streaming=True,
            supports_audio_output=True,
        )
        assert tts_caps.supports_speech_synthesis is True
        assert tts_caps.supports_audio_output is True

    def test_token_validation(self):
        """Test token validation logic."""
        # Valid token configuration
        valid_caps = ModelCapabilities(
            supports_chat=True, max_context_tokens=4096, max_output_tokens=2048
        )
        assert valid_caps.max_output_tokens == 2048

        # Invalid: output tokens > context tokens
        with pytest.raises(ValueError) as exc_info:
            ModelCapabilities(
                supports_chat=True, max_context_tokens=1000, max_output_tokens=2000
            )
        assert "cannot exceed max_context_tokens" in str(exc_info.value)

        # Valid: tokens can be None for non-token models
        valid_none = ModelCapabilities(
            supports_image_generation=True, max_context_tokens=None, max_output_tokens=None
        )
        assert valid_none.max_context_tokens is None

    def test_temperature_validation(self):
        """Test temperature validation."""
        # Valid temperature
        valid_temp = ModelCapabilities(
            supports_chat=True, max_context_tokens=1000, default_temperature=0.7
        )
        assert valid_temp.default_temperature == 0.7

        # Invalid: temperature too high
        with pytest.raises(ValueError):
            ModelCapabilities(
                supports_chat=True, max_context_tokens=1000, default_temperature=2.5
            )

        # Invalid: temperature negative
        with pytest.raises(ValueError):
            ModelCapabilities(
                supports_chat=True, max_context_tokens=1000, default_temperature=-0.1
            )


def test_model_config():
    """Test ModelConfig creation and properties."""
    config = ModelConfig(
        provider=ModelProvider.AZURE,
        name="gpt-4",
        deployment_name="my-gpt4",
        capabilities=ModelCapabilities(
            supports_chat=True, max_context_tokens=8192, max_output_tokens=4096
        ),
    )

    assert config.provider == "azure"
    assert config.full_name == "azure/my-gpt4"
    assert str(config) == "azure/gpt-4"


def test_vision_model_mime_types():
    """Test MIME type validation for vision models."""
    # Valid configuration with supported MIME types
    valid_config = ModelConfig(
        provider=ModelProvider.OPENAI,
        name="test-vision-model",
        capabilities=ModelCapabilities(supports_vision=True),
        supported_mime_types=["image/jpeg", "image/png"]
    )
    assert valid_config.supported_mime_types == ["image/jpeg", "image/png"]

    # Missing MIME types
    with pytest.raises(
        ValidationError,
        match=r"Model 'test-vision-model' has media capabilities but lacks supported MIME types"
    ):
        ModelConfig(
            provider=ModelProvider.OPENAI,
            name="test-vision-model",
            capabilities=ModelCapabilities(supports_vision=True)
        )

    # Invalid MIME type format
    with pytest.raises(
        ValidationError,
        match=r"Invalid MIME type.*must start with one of: \['image/'\]"
    ):
        ModelConfig(
            provider=ModelProvider.OPENAI,
            name="test-vision-model",
            capabilities=ModelCapabilities(supports_vision=True),
            supported_mime_types=["application/json", "image/png"]
        )

    # Non-vision model doesn't require MIME types 
    non_vision_config = ModelConfig(
        provider=ModelProvider.OPENAI,
        name="test-chat-model",
        capabilities=ModelCapabilities(supports_chat=True)
    )
    assert non_vision_config.supported_mime_types is None


def test_model_provider_configurations():
    """Test model configurations from different providers."""
    from src.models.providers.azure import AZURE_MODELS
    from src.models.providers.openai import OPENAI_MODELS

    # Test Azure vision models
    vision_models = [m for m in AZURE_MODELS.values() if m.capabilities.supports_vision]
    for model in vision_models:
        assert model.supported_mime_types is not None, f"Azure model {model.name} missing MIME types"
        assert any(mt.startswith("image/") for mt in model.supported_mime_types), \
            f"Invalid MIME types in Azure model {model.name}: {model.supported_mime_types}"


def test_model_config_clone():
    """Test ModelConfig clone_with method."""
    original = ModelConfig(
        provider=ModelProvider.AZURE,
        name="test-model",
        capabilities=ModelCapabilities(supports_chat=True),
        version="1.0",
        description="Original model"
    )

    # Test cloning with deployment override
    cloned = original.clone_with(deployment_name="custom-deployment")
    assert cloned.deployment_name == "custom-deployment"
    assert cloned.name == original.name
    assert cloned.capabilities == original.capabilities
    assert cloned.version == original.version
    assert cloned.description == original.description

    # Test cloning with multiple overrides
    cloned = original.clone_with(
        deployment_name="custom-deployment",
        version="2.0",
        description="Modified model"
    )
    assert cloned.deployment_name == "custom-deployment"
    assert cloned.version == "2.0"
    assert cloned.description == "Modified model"
    assert cloned.name == original.name
    assert cloned.capabilities == original.capabilities

    # Test invalid override
    with pytest.raises(ValueError, match="Invalid override keys"):
        original.clone_with(invalid_field="value")
