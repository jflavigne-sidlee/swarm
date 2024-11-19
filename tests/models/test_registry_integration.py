import pytest
from src.models.config import get_model, list_models, ModelRegistry
from src.models.base import ModelProvider, ModelCapabilities, ModelConfig


class TestModelRegistryIntegration:
    """Test suite for model registry integration with different model types."""

    def setup_method(self):
        """Set up test registry with some test models."""
        self.registry = ModelRegistry()
        
        # Add test models with proper enum providers
        chat_model = ModelConfig(
            name="test-chat",
            provider=ModelProvider.AZURE,
            capabilities=ModelCapabilities(chat=True, supports_streaming=True),
            description="Test chat model"
        )
        vision_model = ModelConfig(
            name="test-vision",
            provider=ModelProvider.AZURE,
            capabilities=ModelCapabilities(supports_vision=True),
            supported_mime_types=["image/jpeg"],
            description="Test vision model"
        )
        self.registry.add_model(chat_model)
        self.registry.add_model(vision_model)

    def test_chat_model_integration(self):
        """Test chat model filtering and capabilities."""
        chat_models = list_models(capability="chat")
        assert len(chat_models) > 0
        assert all(m.capabilities.chat for m in chat_models)
        assert all(isinstance(m.provider, ModelProvider) for m in chat_models)

    def test_vision_model_integration(self):
        """Test vision model filtering and capabilities."""
        vision_models = list_models(capability="supports_vision")
        assert len(vision_models) > 0
        assert all(m.capabilities.supports_vision for m in vision_models)
        assert all(m.supported_mime_types for m in vision_models)
        assert all(isinstance(m.provider, ModelProvider) for m in vision_models)

    def test_embedding_model_integration(self):
        """Test embedding model filtering and capabilities."""
        embedding_models = list_models(capability="supports_embedding")
        assert len(embedding_models) > 0
        assert all(m.capabilities.supports_embedding for m in embedding_models)
        assert all(isinstance(m.provider, ModelProvider) for m in embedding_models)

    def test_image_generation_integration(self):
        """Test image generation model filtering and capabilities."""
        image_models = list_models(capability="image_generation")
        assert len(image_models) > 0
        assert all(m.capabilities.image_generation for m in image_models)
        assert all(isinstance(m.provider, ModelProvider) for m in image_models)

    def test_cross_capability_filtering(self):
        """Test filtering models by multiple capabilities."""
        chat_stream_models = self.registry.list_models(
            capability=lambda c: c.chat and c.supports_streaming
        )
        assert len(chat_stream_models) > 0
        assert all(
            m.capabilities.chat and m.capabilities.supports_streaming
            for m in chat_stream_models
        )
        assert all(isinstance(m.provider, ModelProvider) for m in chat_stream_models)

    def test_provider_specific_models(self):
        """Test filtering models by provider."""
        azure_models = self.registry.list_models(provider=ModelProvider.AZURE)
        assert len(azure_models) > 0
        assert all(m.provider == ModelProvider.AZURE for m in azure_models)
