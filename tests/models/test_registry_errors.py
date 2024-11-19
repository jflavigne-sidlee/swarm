import pytest
import os
from src.models.config import get_model, list_models, ModelRegistry
from src.models.base import ModelProvider, ModelCapabilities, ModelConfig
from src.models.providers.azure import AZURE_MODELS  # Import AZURE_MODELS
from src.exceptions.models import (
    ModelError,
    ModelNotFoundError,
    InvalidModelConfigError,
    ModelCapabilityError,
    ModelProviderError,
    DeploymentNameError,
)


class TestModelRegistryErrors:
    """Test suite for model registry error handling."""

    def test_invalid_model_name(self):
        """Test error handling for invalid model names."""
        with pytest.raises(ValueError) as exc_info:
            get_model("non-existent-model")
        assert "Model not found" in str(exc_info.value)

    def test_ambiguous_model_resolution(self):
        """Test error handling for ambiguous model names."""
        with pytest.raises(ValueError) as exc_info:
            get_model("gpt-4")  # Exists in both Azure and OpenAI
        assert "Ambiguous model name" in str(exc_info.value)
        assert "azure/gpt-4" in str(exc_info.value)
        assert "openai/gpt-4" in str(exc_info.value)

    def test_invalid_capability_queries(self):
        """Test error handling for invalid capability queries."""
        with pytest.raises(ValueError) as exc_info:
            list_models(capability="nonexistent_capability")
        assert "Unknown capability" in str(exc_info.value)

    def test_deployment_name_conflicts(self):
        """Test error handling for deployment name conflicts."""
        # Set up conflicting deployment names
        os.environ["AZURE_DEPLOYMENT_GPT_4"] = "custom-gpt4"
        os.environ["AZURE_DEPLOYMENT_OVERRIDE"] = "different-gpt4"

        registry = ModelRegistry()

        # Built-in model should load without error and log a warning
        built_in_config = AZURE_MODELS["gpt-4"]
        try:
            registry.add_model(built_in_config)  # Should not raise an error
        except ValueError:
            pytest.fail(
                "Built-in models should not raise errors for deployment conflicts."
            )

        # Validate built-in model loaded successfully
        assert "azure/gpt-4" in registry._models

        # Manually added model should raise an error
        manual_config = ModelConfig(
            name="gpt-4",
            provider=ModelProvider.AZURE,
            capabilities=ModelCapabilities(chat=True),
            description="Manually added test model",
        )
        with pytest.raises(ValueError, match="Conflicting deployment names for gpt-4"):
            registry.add_model(manual_config)

    def test_invalid_model_configurations(self):
        """Test error handling for invalid model configurations."""
        with pytest.raises(ValueError) as exc_info:
            ModelCapabilities(chat=True, max_context_tokens=-1, max_output_tokens=100)
        assert "greater than 0" in str(exc_info.value)

    def test_mime_type_validation(self):
        """Test error handling for MIME type validation."""
        with pytest.raises(ValueError) as exc_info:
            ModelConfig(
                name="test-vision",
                provider=ModelProvider.AZURE,
                capabilities=ModelCapabilities(vision=True),
                supported_mime_types=None,  # Should raise error for vision model
                description="Test model",
            )
        assert "Vision models must support image MIME types" in str(exc_info.value)

    def test_provider_validation(self):
        """Test error handling for provider validation."""
        with pytest.raises(ValueError) as exc_info:
            list_models(provider="invalid")
        assert "Invalid provider" in str(exc_info.value)