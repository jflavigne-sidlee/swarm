import pytest
from src.models.base import ModelProvider, ModelCapabilities, ModelConfig


class TestModelCapabilities:
    """Test suite for model capabilities."""

    def test_chat_model_capabilities(self):
        """Test chat model capabilities configuration."""
        chat_caps = ModelCapabilities(
            chat=True,
            max_context_tokens=4096,
            max_output_tokens=1000,
            supports_functions=True,
            default_temperature=0.7,
        )
        assert chat_caps.chat is True
        assert chat_caps.max_context_tokens == 4096
        assert chat_caps.embedding is False  # Default false

    def test_embedding_model_capabilities(self):
        """Test embedding model capabilities configuration."""
        embed_caps = ModelCapabilities(
            embedding=True,
            max_context_tokens=8191,
            max_output_tokens=None,  # Embeddings don't have output tokens
            supports_streaming=False,
            default_temperature=0.0,
        )
        assert embed_caps.embedding is True
        assert embed_caps.max_context_tokens == 8191
        assert embed_caps.max_output_tokens is None
        assert embed_caps.supports_streaming is False

    def test_image_generation_capabilities(self):
        """Test DALL-E model capabilities configuration."""
        dalle_caps = ModelCapabilities(
            image_generation=True,
            max_context_tokens=None,  # No token limits for image generation
            max_output_tokens=None,
            supports_streaming=False,
            default_temperature=0.0,
        )
        assert dalle_caps.image_generation is True
        assert dalle_caps.max_context_tokens is None
        assert dalle_caps.max_output_tokens is None

    def test_speech_model_capabilities(self):
        """Test speech model capabilities configuration."""
        whisper_caps = ModelCapabilities(
            speech_recognition=True,
            max_context_tokens=None,
            max_output_tokens=None,
            supports_streaming=True,
            supports_audio_input=True,
        )
        assert whisper_caps.speech_recognition is True
        assert whisper_caps.supports_audio_input is True

        tts_caps = ModelCapabilities(
            speech_synthesis=True,
            max_context_tokens=None,
            max_output_tokens=None,
            supports_streaming=True,
            supports_audio_output=True,
        )
        assert tts_caps.speech_synthesis is True
        assert tts_caps.supports_audio_output is True

    def test_token_validation(self):
        """Test token validation logic."""
        # Valid token configuration
        valid_caps = ModelCapabilities(
            chat=True, max_context_tokens=4096, max_output_tokens=2048
        )
        assert valid_caps.max_output_tokens == 2048

        # Invalid: output tokens > context tokens
        with pytest.raises(ValueError) as exc_info:
            ModelCapabilities(
                chat=True, max_context_tokens=1000, max_output_tokens=2000
            )
        assert "cannot exceed max_context_tokens" in str(exc_info.value)

        # Valid: tokens can be None for non-token models
        valid_none = ModelCapabilities(
            image_generation=True, max_context_tokens=None, max_output_tokens=None
        )
        assert valid_none.max_context_tokens is None

    def test_temperature_validation(self):
        """Test temperature validation."""
        # Valid temperature
        valid_temp = ModelCapabilities(
            chat=True, max_context_tokens=1000, default_temperature=0.7
        )
        assert valid_temp.default_temperature == 0.7

        # Invalid: temperature too high
        with pytest.raises(ValueError):
            ModelCapabilities(
                chat=True, max_context_tokens=1000, default_temperature=2.5
            )

        # Invalid: temperature negative
        with pytest.raises(ValueError):
            ModelCapabilities(
                chat=True, max_context_tokens=1000, default_temperature=-0.1
            )


def test_model_config():
    """Test ModelConfig creation and properties."""
    config = ModelConfig(
        provider=ModelProvider.AZURE,
        name="gpt-4",
        deployment_name="my-gpt4",
        capabilities=ModelCapabilities(
            chat=True, max_context_tokens=8192, max_output_tokens=4096
        ),
    )

    assert config.provider == "azure"
    assert config.full_name == "azure/my-gpt4"
    assert str(config) == "azure/gpt-4"
