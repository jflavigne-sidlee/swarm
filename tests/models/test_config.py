import pytest
import os
from src.models.config import get_model, list_models, ModelRegistry
from src.models.base import ModelProvider


def test_model_registry_basic():
    """Test basic model registry functionality."""
    registry = ModelRegistry()

    # Test getting model with explicit provider
    model = registry.get_model("gpt-4", provider=ModelProvider.AZURE)
    assert isinstance(model.provider, ModelProvider)
    assert model.provider == ModelProvider.AZURE
    assert model.name == "gpt-4"

    # Test getting model with provider prefix
    model = get_model("azure/gpt-4")
    assert model.provider == ModelProvider.AZURE
    assert model.name == "gpt-4"


def test_model_registry_filtering():
    """Test model listing and filtering."""
    registry = ModelRegistry()

    # List all vision models
    vision_models = registry.list_models(capability="vision")
    assert len(vision_models) > 0
    assert all(m.capabilities.vision for m in vision_models)
    assert all(isinstance(m.provider, ModelProvider) for m in vision_models)

    # List Azure models
    azure_models = registry.list_models(provider=ModelProvider.AZURE)
    assert len(azure_models) > 0
    assert all(m.provider == ModelProvider.AZURE for m in azure_models)


def test_model_registry_errors():
    """Test error handling."""
    # Test invalid model name
    with pytest.raises(ValueError) as exc_info:
        get_model("invalid-model")
    assert "not found" in str(exc_info.value)

    # Test ambiguous model name
    with pytest.raises(ValueError) as exc_info:
        get_model("gpt-4")  # Exists in both Azure and OpenAI
    assert "Ambiguous model name" in str(exc_info.value)
    assert "azure: gpt-4" in str(exc_info.value)
    assert "openai: gpt-4" in str(exc_info.value)


def test_environment_overrides():
    """Test environment variable overrides."""
    try:
        # Set up environment override
        os.environ["AZURE_DEPLOYMENT_GPT_4"] = "custom-gpt4"

        model = get_model("gpt-4", provider=ModelProvider.AZURE)
        assert model.provider == ModelProvider.AZURE
        assert model.deployment_name == "custom-gpt4"
        assert model.name == "gpt-4"
    finally:
        # Clean up
        os.environ.pop("AZURE_DEPLOYMENT_GPT_4", None)


def test_ambiguous_model_name():
    registry = ModelRegistry()
    with pytest.raises(ValueError) as exc_info:
        registry.get_model("gpt-4")

    expected_error = """Ambiguous model name 'gpt-4'. Found multiple matches:
  - azure: gpt-4 (Advanced model improving upon GPT-3.5 for natural language and code generation.)
  - openai: gpt-4 (GPT-4 base model)
Please specify provider using: <provider>/gpt-4"""

    assert str(exc_info.value) == expected_error
