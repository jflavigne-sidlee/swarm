from typing import Dict, Optional, List, Union, Callable
import os
from pathlib import Path
import json
from pydantic import BaseModel, Field
import itertools
from copy import deepcopy
import logging

from .base import ModelConfig, ModelProvider, ModelCapabilities
from .providers.azure import AZURE_MODELS, get_azure_model
from .providers.openai import OPENAI_MODELS, get_openai_model
from .constants import (
    ENV_AZURE_DEPLOYMENT_OVERRIDE,
    ENV_AZURE_DEPLOYMENT_PREFIX,
    PROVIDER_PATH_SEPARATOR,
    ERROR_VISION_MIME_TYPES,
    ERROR_INVALID_PROVIDER,
    ERROR_PROVIDER_TYPE,
    ERROR_MODEL_NOT_FOUND,
    ERROR_AMBIGUOUS_MODEL,
    ERROR_DEPLOYMENT_CONFLICT,
    ERROR_DEPLOYMENT_NAME_CONFLICT,
    ERROR_UNKNOWN_CAPABILITY,
    WARNING_DEPLOYMENT_CONFLICT,
    LOG_PROVIDER_CONVERSION,
)


class ModelRegistry:
    """
    Central registry for managing AI model configurations.
    
    This class handles:
    - Loading and storing model configurations
    - Environment-based deployment overrides
    - Model validation and capability checking
    - Provider-specific model management
    """
    VALID_CAPABILITIES = list(ModelCapabilities.__annotations__.keys())
    
    def __init__(self):
        """Initialize the model registry."""
        self._models: Dict[str, ModelConfig] = {}
        self._built_in_models: set[str] = set()  # Track names of built-in models
        self._load_models()
        self._load_environment_overrides()

    def _load_models(self) -> None:
        """Load all available models."""
        for model in itertools.chain(AZURE_MODELS.values(), OPENAI_MODELS.values()):
            self.add_model(model)

    def _get_model_deployment_config(self, model_name: str) -> tuple[Optional[str], Optional[str]]:
        """
        Get deployment configuration from environment variables.
        
        Args:
            model_name: Name of the model to get deployment config for
            
        Returns:
            tuple: (model_specific_deployment, global_override)
                - model_specific_deployment: Value from AZURE_DEPLOYMENT_{MODEL_NAME}
                - global_override: Value from AZURE_DEPLOYMENT_OVERRIDE
        """
        specific_deployment = os.getenv(f"{ENV_AZURE_DEPLOYMENT_PREFIX}{model_name.upper().replace('-', '_')}")
        global_override = os.getenv(ENV_AZURE_DEPLOYMENT_OVERRIDE)
        return specific_deployment, global_override

    def _get_deployment_override(self, model_name: str) -> Optional[str]:
        """Fetch deployment override from environment variables."""
        specific_deployment, _ = self._get_model_deployment_config(model_name)
        return specific_deployment

    def _create_overridden_config(self, base_config: ModelConfig, deployment_name: str) -> ModelConfig:
        """
        Create a new ModelConfig with an overridden deployment name.
        
        Args:
            base_config: Original model configuration
            deployment_name: New deployment name to use
            
        Returns:
            ModelConfig: New configuration with updated deployment name
        """
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
            deployment_name = self._get_deployment_override(name)
            if deployment_name:
                base_config = AZURE_MODELS[name]
                overridden_config = self._create_overridden_config(base_config, deployment_name)
                self._models[f"azure/{name}"] = overridden_config

    def _ensure_model_provider(self, model: ModelConfig) -> ModelConfig:
        """
        Ensure the model provider is a valid ModelProvider enum.
        
        Args:
            model: The model configuration to validate
            
        Returns:
            ModelConfig: Either the original model or a new instance with converted provider
            
        Raises:
            ValueError: If the provider is invalid or of wrong type
        """
        if isinstance(model.provider, str):
            try:
                provider = ModelProvider(model.provider)
                logging.info(LOG_PROVIDER_CONVERSION.format(provider=provider))
                return ModelConfig(
                    name=model.name,
                    provider=provider,
                    capabilities=model.capabilities,
                    description=model.description,
                    supported_mime_types=model.supported_mime_types,
                    deployment_name=model.deployment_name,
                    version=model.version,
                )
            except ValueError:
                raise ValueError(ERROR_INVALID_PROVIDER.format(
                    provider=model.provider,
                    valid_providers=list(ModelProvider)
                ))
        elif not isinstance(model.provider, ModelProvider):
            raise ValueError(ERROR_PROVIDER_TYPE.format(provider_type=type(model.provider)))
        return model

    def add_model(self, model: ModelConfig) -> None:
        """
        Add a model to the registry.
        
        Args:
            model: Model configuration to add
            
        Raises:
            ValueError: If model configuration is invalid or conflicts exist
        """
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
                    ERROR_DEPLOYMENT_NAME_CONFLICT.format(
                        deployment_name=model.deployment_name,
                        existing_model=existing[0].name
                    )
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
        """
        Get a model by name and optional provider.
        
        Args:
            name: Model name or full path (provider/name)
            provider: Optional provider to disambiguate model selection
            
        Returns:
            ModelConfig: The requested model configuration
            
        Raises:
            ValueError: If model not found or name is ambiguous
        """
        # Handle full paths (provider/name format)
        if "/" in name:
            provider_name, model_name = name.split("/", 1)
            try:
                provider = ModelProvider(provider_name)
            except ValueError:
                available = sorted(self._models.keys())
                raise ValueError(
                    ERROR_MODEL_NOT_FOUND.format(
                        name=name,
                        available=available
                    )
                )
            return self.get_model(model_name, provider)

        # Handle provider-specific lookup
        if provider:
            if not isinstance(provider, ModelProvider):
                raise ValueError(
                    ERROR_PROVIDER_TYPE.format(provider_type=type(provider))
                )
            key = f"{provider.value}/{name}"
            if key not in self._models:
                available = [
                    m for m in self._models.keys() if m.startswith(f"{provider.value}/")
                ]
                raise ValueError(
                    ERROR_MODEL_NOT_FOUND.format(
                        name=name,
                        available=available
                    )
                )
            return self._models[key]

        # Handle ambiguous names
        matches = [m for m in self._models.values() if m.name == name]
        if not matches:
            available = sorted(self._models.keys())
            raise ValueError(
                ERROR_MODEL_NOT_FOUND.format(
                    name=name,
                    available=available
                )
            )
        if len(matches) > 1:
            conflict_details = "\n".join([
                f"  - {m.provider.value}: {m.name} ({m.description or 'No description'})"
                for m in matches
            ])
            raise ValueError(
                ERROR_AMBIGUOUS_MODEL.format(
                    name=name,
                    conflict_details=conflict_details
                )
            )
        return matches[0]

    def validate_model_config(self, config: ModelConfig):
        """
        Validate model configuration for correctness and consistency.
        
        Checks:
        - MIME type support for vision models
        - Azure deployment name conflicts
        - Built-in model overrides
        
        Args:
            config: Model configuration to validate
            
        Raises:
            ValueError: If validation fails
        """
        # Built-in model check
        is_built_in = config in AZURE_MODELS.values() or config in OPENAI_MODELS.values()

        # Validate MIME types for vision models
        if config.capabilities.vision and not config.supported_mime_types:
            raise ValueError(ERROR_VISION_MIME_TYPES.format(model_name=config.name))

        # Azure deployment name validation
        if config.provider == ModelProvider.AZURE:
            specific_deployment, global_override = self._get_model_deployment_config(config.name)

            if specific_deployment and global_override and specific_deployment != global_override:
                if is_built_in:
                    logging.warning(
                        WARNING_DEPLOYMENT_CONFLICT.format(
                            name=config.name,
                            specific=specific_deployment,
                            override=global_override
                        )
                    )
                else:
                    raise ValueError(
                        ERROR_DEPLOYMENT_CONFLICT.format(
                            name=config.name,
                            specific=specific_deployment,
                            override=global_override
                        )
                    )

    def list_models(
        self, provider: Optional[ModelProvider] = None, capability: Optional[Union[str, Callable]] = None
    ) -> List[ModelConfig]:
        """
        List models filtered by provider and/or capability.
        
        Args:
            provider: Optional provider to filter by
            capability: Either a capability name or a callable that takes
                       ModelCapabilities and returns bool
            
        Returns:
            List[ModelConfig]: Filtered list of model configurations
            
        Raises:
            ValueError: If provider or capability is invalid
        """
        models = list(self._models.values())

        # Filter by provider if specified
        if provider:
            if not isinstance(provider, ModelProvider):
                raise ValueError(f"Invalid provider: {provider}")
            models = [m for m in models if m.provider == provider]

        # Filter by capability if specified
        if capability:
            if callable(capability):
                # Apply callable directly to capabilities
                models = [m for m in models if capability(m.capabilities)]
            else:
                # Validate capability name
                if capability not in self.VALID_CAPABILITIES:
                    raise ValueError(ERROR_UNKNOWN_CAPABILITY.format(capability=capability))
                # Filter models by the specified capability
                models = [m for m in models if getattr(m.capabilities, capability, False)]

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
        deployment_name = registry._get_deployment_override(model.name)
        if deployment_name:
            return registry._create_overridden_config(model, deployment_name)
    return model


def list_models(
    provider: Optional[ModelProvider] = None,
    capability: Optional[Union[str, Callable]] = None,
) -> List[ModelConfig]:
    """List available models."""
    return registry.list_models(provider, capability)
