from enum import Enum
from typing import Dict, Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator

class ModelProvider(str, Enum):
    """Supported model providers."""
    AZURE = "azure"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"

class ModelCapabilities(BaseModel):
    """Defines what a model can do and its limitations."""
    supports_embedding: bool = False
    supports_chat: bool = False
    supports_image_generation: bool = False
    speech_recognition: bool = False
    speech_synthesis: bool = False
    max_context_tokens: Optional[int] = Field(
        None, 
        description="Maximum total tokens (prompt + completion)",
        gt=0
    )
    max_output_tokens: Optional[int] = Field(
        None, 
        description="Maximum tokens for completion response"
    )
    supports_functions: bool = False
    supports_json_mode: bool = False
    supports_vision: bool = False
    supports_streaming: bool = True
    supports_audio_input: bool = False
    supports_audio_output: bool = False
    default_temperature: float = Field(0.7, ge=0.0, le=2.0)
    
    model_config = ConfigDict(
        frozen=True,
        validate_assignment=True
    )
    
    @field_validator('max_output_tokens', mode='after')
    @classmethod
    def validate_output_tokens(cls, value: Optional[int], info) -> Optional[int]:
        """Ensure output tokens don't exceed context tokens if both are set."""
        if value is not None and info.data.get('max_context_tokens') is not None:
            max_context = info.data['max_context_tokens']
            if value > max_context:
                raise ValueError(
                    f"max_output_tokens ({value}) cannot exceed "
                    f"max_context_tokens ({max_context})"
                )
        return value

class ModelConfig(BaseModel):
    """Configuration for a specific model."""
    provider: ModelProvider
    name: str
    capabilities: ModelCapabilities
    version: Optional[str] = None
    deployment_name: Optional[str] = None
    description: Optional[str] = None
    supported_mime_types: Optional[List[str]] = None
    built_in: bool = False  # Flag to indicate if the model is built-in
    
    model_config = ConfigDict(
        frozen=True,
        use_enum_values=False,
        validate_assignment=True
    )
    
    def __str__(self) -> str:
        """String representation of the model."""
        return f"{self.provider.value}/{self.name}"
    
    @property
    def full_name(self) -> str:
        """Get the full model name including provider."""
        if self.provider == ModelProvider.AZURE:
            return f"{self.provider.value}/{self.deployment_name or self.name}"
        return f"{self.provider.value}/{self.name}"
    
    @model_validator(mode='after')
    def validate_mime_types(self) -> 'ModelConfig':
        """Validate MIME types for vision models."""
        if self.capabilities.supports_vision and not self.supported_mime_types:
            raise ValueError(
                f"Vision models must support image MIME types: {self.name}"
            )
        return self
