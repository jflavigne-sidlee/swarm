import pytest
from src.models.providers.openai import get_openai_model, OPENAI_MODELS
from src.models.base import ModelProvider

def test_openai_model_configurations():
    """Test OpenAI model configurations."""
    # Test GPT-4 Turbo
    gpt4_turbo = get_openai_model("gpt-4-turbo-preview")
    assert gpt4_turbo.provider == ModelProvider.OPENAI
    assert gpt4_turbo.capabilities.max_context_tokens == 128000
    assert gpt4_turbo.version == "0125"
    
    # Test vision model capabilities
    vision = get_openai_model("gpt-4-vision-preview")
    assert vision.capabilities.supports_vision == True
    assert "image/jpeg" in vision.supported_mime_types
    
    # Test embedding model
    embedding = get_openai_model("text-embedding-3-small")
    assert embedding.capabilities.embedding == True
    assert embedding.capabilities.supports_streaming == False
    
    # Test DALL-E
    dalle = get_openai_model("dall-e-3")
    assert dalle.capabilities.supports_vision == False
    assert dalle.supported_mime_types == ["image/png"]
    
    # Test invalid model name
    with pytest.raises(ValueError) as exc_info:
        get_openai_model("invalid-model")
    assert "Unknown OpenAI model" in str(exc_info.value)

def test_all_openai_models_valid():
    """Test that all defined OpenAI models have valid configurations."""
    for model_name, config in OPENAI_MODELS.items():
        assert config.provider == ModelProvider.OPENAI
        assert config.capabilities.max_context_tokens > 0
        
        if config.capabilities.supports_vision:
            assert config.supported_mime_types is not None
            assert "image/jpeg" in config.supported_mime_types
            
        if "embedding" in model_name:
            assert config.capabilities.embedding == True
            assert config.capabilities.max_output_tokens is None 