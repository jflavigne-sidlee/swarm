import itertools
from src.models.base import ModelProvider
from src.models.providers.azure import AZURE_MODELS
from src.models.providers.openai import OPENAI_MODELS

def test_model_providers():
    for model in itertools.chain(AZURE_MODELS.values(), OPENAI_MODELS.values()):
        assert isinstance(model.provider, ModelProvider), f"Provider is not a ModelProvider: {model.provider}"