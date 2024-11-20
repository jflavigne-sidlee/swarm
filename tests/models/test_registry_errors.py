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
from src.aoai.client import AOAIClient
from pathlib import Path  # Add this import
from src.exceptions.vision import ImageValidationError  # Add this import
from src.functions.vision import analyze_images  # Add this import
from pydantic import ValidationError  # Import ValidationError from Pydantic


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
        assert "azure: gpt-4" in str(exc_info.value)
        assert "openai: gpt-4" in str(exc_info.value)

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

    from PIL import Image

    @pytest.mark.asyncio
    async def test_mime_type_validation(ai_client: AOAIClient) -> None:
        """Test MIME type validation using a real image."""
        # Resolve the path to the test image
        temp_file = (Path(__file__).parent / "test_assets" / "unsupported_format_image.webp").resolve()
        print(f"Resolved path: {temp_file}")

        # Ensure the file exists
        assert temp_file.exists(), f"Test file not found: {temp_file}"

        # Test the behavior with the unsupported .webp file
        with pytest.raises(ImageValidationError) as exc_info:
            await analyze_images(ai_client, str(temp_file))

        # Assert the exception contains the expected message
        assert "Unsupported image format" in str(exc_info.value), "Expected unsupported image format error"

    def test_provider_validation(self):
        """Test error handling for provider validation."""
        with pytest.raises(ValueError) as exc_info:
            list_models(provider="invalid")
        assert "Invalid provider" in str(exc_info.value)

    def test_mime_type_validation(self):
        """Test MIME type validation for vision models."""
        registry = ModelRegistry()
        
        # Try to add a vision model without MIME types
        with pytest.raises(ValidationError, match=r"has media capabilities but lacks supported MIME types"):
            invalid_model = ModelConfig(
                provider=ModelProvider.AZURE,
                name="invalid-vision-model",
                capabilities=ModelCapabilities(supports_vision=True)
            )
            registry.add_model(invalid_model)  # Attempt to add the invalid model

        # Try to add a vision model with invalid MIME types
        with pytest.raises(ValidationError, match=r"Invalid MIME type.*must start with one of: \['image/'\]"):
            invalid_mime_model = ModelConfig(
                provider=ModelProvider.AZURE,
                name="invalid-mime-model",
                capabilities=ModelCapabilities(supports_vision=True),
                supported_mime_types=["text/plain", "image/png"]
            )
            registry.add_model(invalid_mime_model)  # Attempt to add the invalid model

        # Valid vision model should work
        valid_model = ModelConfig(
            provider=ModelProvider.AZURE,
            name="valid-vision-model",
            capabilities=ModelCapabilities(supports_vision=True),
            supported_mime_types=["image/jpeg", "image/png"]
        )
        registry.add_model(valid_model)
        assert registry.get_model("valid-vision-model") == valid_model
