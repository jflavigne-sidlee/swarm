from typing import Dict, Optional, List, Union, Callable
import os
from pathlib import Path
import json
from pydantic import BaseModel, Field
import itertools
from copy import deepcopy

from .base import ModelConfig, ModelProvider, ModelCapabilities
from .providers.azure import AZURE_MODELS, get_azure_model
from .providers.openai import OPENAI_MODELS, get_openai_model


class ModelRegistry:
    """Central registry for all AI model configurations."""

    def __init__(self):
        """Initialize the model registry."""
        self._models: Dict[str, ModelConfig] = {}
        self._built_in_models: set[str] = set()  # Track names of built-in models
        self._load_models()
        self._load_environment_overrides()

    def _load_models(self) -> None:
        """Load all available models."""
        # First, mark all built-in models
        for model in itertools.chain(AZURE_MODELS.values(), OPENAI_MODELS.values()):
            self._built_in_models.add(model.name)
        
        # Then add the models to the registry
        for model in itertools.chain(AZURE_MODELS.values(), OPENAI_MODELS.values()):
            # Add model to registry
            self.add_model(model)
            # Track built-in model names
            self._built_in_models.add(model.name)  # Mark models as built-in

    def _get_azure_deployment_override(self, model_name: str) -> Optional[str]:
        """Helper method to get Azure deployment override from environment variables."""
        env_var = f"AZURE_DEPLOYMENT_{model_name.upper().replace('-', '_')}"
        return os.getenv(env_var)

    def _create_overridden_config(self, base_config: ModelConfig, deployment_name: str) -> ModelConfig:
        """Create a new ModelConfig with an overridden deployment name."""
        return ModelConfig(
            name=base_config.name,
            provider=self._ensure_model_provider(base_config).provider,
            capabilities=base_config.capabilities,
            description=base_config.description,
            supported_mime_types=base_config.supported_mime_types,
            deployment_name=deployment_name,
            version=base_config.version,
        )

    def _load_environment_overrides(self) -> None:
        """Load model configuration overrides from environment variables."""
        # Azure deployment name overrides
        for name in AZURE_MODELS:
            deployment_name = self._get_azure_deployment_override(name)
            if deployment_name:
                base_config = AZURE_MODELS[name]
                overridden_config = self._create_overridden_config(base_config, deployment_name)
                self._models[f"azure/{name}"] = overridden_config

    def _ensure_model_provider(self, model: ModelConfig) -> ModelConfig:
        """
        Ensure the model provider is a ModelProvider enum. If the provider is a string,
        convert it to the corresponding enum value. If it's already a valid ModelProvider, return as is.
        """
        if isinstance(model.provider, str):
            try:
                # Convert string provider to ModelProvider enum
                provider_enum = ModelProvider(model.provider)
                print(
                    f"Converting string provider '{model.provider}' to enum {provider_enum}."
                )
            except ValueError:
                raise ValueError(
                    f"Invalid provider '{model.provider}'. Must be one of {list(ModelProvider)}."
                )

            # Return a new instance of ModelConfig with the updated provider
            return ModelConfig(
                name=model.name,
                provider=provider_enum,
                capabilities=model.capabilities,
                description=model.description,
                supported_mime_types=model.supported_mime_types,
                deployment_name=model.deployment_name,
                version=model.version,
            )

        # If provider is already a ModelProvider, validate and return the same model
        if not isinstance(model.provider, ModelProvider):
            raise ValueError(
                f"Provider must be a ModelProvider enum or valid string. Got: {type(model.provider)}"
            )

        return model

    def add_model(self, model: ModelConfig) -> None:
        """Add a model to the registry."""
        # print(f"Adding model: {model.name}, built-in: {model.name in self._built_in_models}")
        
        # Validate the model configuration first
        self.validate_model_config(model)

        # Check for deployment name conflicts
        if model.deployment_name:
            existing = [
                m
                for m in self._models.values()
                if m.provider == model.provider
                and m.deployment_name == model.deployment_name
                and m.name != model.name  # Allow same model to update its config
            ]
            if existing:
                raise ValueError(
                    f"Deployment name conflict: {model.deployment_name} "
                    f"already used by {existing[0].name}"
                )

        # Mark model as built-in if it is part of the preloaded models
        if model.name in AZURE_MODELS or model.name in OPENAI_MODELS:
            self._built_in_models.add(model.name)

        # Add the model to the registry
        key = f"{model.provider.value}/{model.name}"
        self._models[key] = model

    def get_model(
        self, name: str, provider: Optional[ModelProvider] = None
    ) -> ModelConfig:
        """Get a model by name and optional provider."""
        # Handle full paths (provider/name format)
        if "/" in name:
            provider_name, model_name = name.split("/", 1)
            try:
                provider = ModelProvider(provider_name)
            except ValueError:
                available = sorted(self._models.keys())
                raise ValueError(
                    f"Invalid provider '{provider_name}'. Available models: {', '.join(available)}"
                )
            return self.get_model(model_name, provider)

        # Handle provider-specific lookup
        if provider:
            if not isinstance(provider, ModelProvider):
                raise ValueError(
                    f"Invalid provider type: {type(provider)}. Expected ModelProvider enum."
                )
            key = f"{provider.value}/{name}"
            if key not in self._models:
                available = [
                    m for m in self._models.keys() if m.startswith(f"{provider.value}/")
                ]
                raise ValueError(
                    f"Model '{name}' not found for provider '{provider.value}'. Available models: {', '.join(available)}"
                )
            return self._models[key]

        # Handle ambiguous names
        matches = [m for m in self._models.values() if m.name == name]
        if not matches:
            available = sorted(self._models.keys())
            raise ValueError(
                f"Model not found: '{name}'. Available models: {', '.join(available)}"
            )
        if len(matches) > 1:
            # Create a detailed message showing each conflicting model and its provider
            conflict_details = "\n".join([
                f"  - {m.provider.value}: {m.name} ({m.description or 'No description'})"
                for m in matches
            ])
            raise ValueError(
                f"Ambiguous model name '{name}'. Found multiple matches:\n"
                f"{conflict_details}\n"
                f"Please specify provider using: <provider>/{name}"
            )
        return matches[0]

    def validate_model_config(self, config: ModelConfig):
        """Validate model configuration."""
        # A model is considered built-in if it's in the original AZURE_MODELS or OPENAI_MODELS
        is_built_in = (
            config.name in AZURE_MODELS and config in AZURE_MODELS.values()
        ) or (
            config.name in OPENAI_MODELS and config in OPENAI_MODELS.values()
        )
        
        # print(f"Validating model: {config.name}, built-in: {is_built_in}")

        # Validate MIME types for vision models
        if config.capabilities.vision and not config.supported_mime_types:
            raise ValueError(f"Vision models must support image MIME types: {config.name}")

        # Validate deployment names for Azure models
        if config.provider == ModelProvider.AZURE:
            model_env_key = f"AZURE_DEPLOYMENT_{config.name.upper().replace('-', '_')}"
            override = os.getenv("AZURE_DEPLOYMENT_OVERRIDE")
            model_deployment = os.getenv(model_env_key)

            if model_deployment and override and model_deployment != override:
                if is_built_in:
                    # Allow conflicts for built-in models and log a warning
                    print(
                        f"Warning: Conflict detected for built-in model {config.name}. "
                        f"Using {model_env_key}={model_deployment} over override={override}."
                    )
                else:
                    # Raise an error for manually added models
                    raise ValueError(
                        f"Conflicting deployment names for {config.name}: "
                        f"{model_env_key}={model_deployment}, override={override}. "
                        "Please resolve this conflict before adding the model."
                    )

    def list_models(
        self, provider: Optional[ModelProvider] = None, capability: Optional[str] = None
    ) -> List[ModelConfig]:
        """List models filtered by provider and/or capability."""
        models = list(self._models.values())

        if provider:
            if not isinstance(provider, ModelProvider):
                raise ValueError(f"Invalid provider: {provider}")
            models = [m for m in models if m.provider == provider]

        if capability:
            if callable(capability):
                # Handle function-based filtering
                models = [m for m in models if capability(m.capabilities)]
            else:
                # Get valid capabilities dynamically from ModelCapabilities fields
                valid_capabilities = [
                    field for field in ModelCapabilities.__annotations__.keys()
                    if field not in {"__annotations__", "__dataclass_fields__"}
                ]
                if capability not in valid_capabilities:
                    raise ValueError(f"Unknown capability: {capability}")
                models = [
                    m for m in models if getattr(m.capabilities, capability, False)
                ]

        return models


# Global instance
registry = ModelRegistry()


# Convenience functions
def get_model(
    name_or_path: str, provider: Optional[ModelProvider] = None
) -> ModelConfig:
    """Get model configuration."""
    model = registry.get_model(name_or_path, provider)

    # Check for environment override
    if model.provider == ModelProvider.AZURE:
        deployment_name = registry._get_azure_deployment_override(model.name)
        if deployment_name:
            return registry._create_overridden_config(model, deployment_name)
    return model


def list_models(
    provider: Optional[ModelProvider] = None,
    capability: Optional[Union[str, Callable]] = None,
) -> List[ModelConfig]:
    """List available models."""
    return registry.list_models(provider, capability)
