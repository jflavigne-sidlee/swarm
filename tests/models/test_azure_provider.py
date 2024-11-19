import pytest
from src.models.providers.azure import get_azure_model, AZURE_MODELS
from src.models.base import ModelProvider

def test_azure_model_configurations():
    """Test Azure model configurations."""
    # Test basic model retrieval
    gpt4 = get_azure_model("gpt-4")
    assert gpt4.provider == ModelProvider.AZURE
    assert gpt4.capabilities.max_context_tokens == 8192
    assert gpt4.deployment_name is None
    
    # Test vision model capabilities (using gpt-4o which has vision capability)
    vision = get_azure_model("gpt-4o")
    assert vision.capabilities.supports_vision is True
    assert "image/jpeg" in vision.supported_mime_types
    
    # Test deployment name override creates new instance
    custom = get_azure_model("gpt-4", deployment_name="custom-deployment")
    assert custom.deployment_name == "custom-deployment"
    assert custom.name == "gpt-4"  # Original name preserved
    assert custom.provider == ModelProvider.AZURE
    assert custom != gpt4  # Should be different instances
    
    # Test invalid model name
    with pytest.raises(ValueError) as exc_info:
        get_azure_model("invalid-model")
    assert "Unknown Azure model" in str(exc_info.value)

def test_all_azure_models_valid():
    """Test that all defined Azure models have valid configurations."""
    for model_name, config in AZURE_MODELS.items():
        assert config.provider == ModelProvider.AZURE
        if config.capabilities.chat:
            assert config.capabilities.max_context_tokens > 0
