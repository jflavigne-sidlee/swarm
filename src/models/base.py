from enum import Enum
from typing import Dict, Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


class ModelProvider(str, Enum):
    """Supported model providers."""

    AZURE = "azure"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class ModelCapabilities(BaseModel):
    """
    Defines what a model can do and its limitations.

    Attributes:
        supports_embedding: Whether the model supports embedding generation.
        supports_chat: Whether the model supports conversational capabilities.
        supports_image_generation: Whether the model can generate images.
        supports_speech_recognition: Whether the model can transcribe speech to text.
        supports_speech_synthesis: Whether the model can generate synthetic speech.
        max_context_tokens: The maximum number of tokens (prompt + completion) the model can handle.
        max_output_tokens: The maximum number of tokens the model can generate in its response.
        supports_functions: Whether the model supports additional functions (e.g., plugins or APIs).
        supports_json_mode: Whether the model supports structured JSON input/output.
        supports_vision: Whether the model can process visual data (e.g., images or videos).
        supports_streaming: Whether the model can stream responses incrementally.
        supports_audio_input: Whether the model can process raw audio input.
        supports_audio_output: Whether the model can generate raw audio output.
        default_temperature: The default sampling temperature for the model's responses.
    """

    supports_embedding: bool = Field(
        default=False,
        description="Indicates if the model supports embedding generation.",
    )
    supports_chat: bool = Field(
        default=False,
        description="Indicates if the model supports conversational capabilities.",
    )
    supports_image_generation: bool = Field(
        default=False, description="Indicates if the model can generate images."
    )
    supports_speech_recognition: bool = Field(
        default=False,
        description="Indicates if the model can transcribe speech to text.",
    )
    supports_speech_synthesis: bool = Field(
        default=False,
        description="Indicates if the model can generate synthetic speech.",
    )
    max_context_tokens: Optional[int] = Field(
        None,
        description="Maximum total tokens (prompt + completion) the model can handle.",
        gt=0,
    )
    max_output_tokens: Optional[int] = Field(
        None,
        description="Maximum number of tokens the model can generate in its response.",
    )
    supports_functions: bool = Field(
        default=False,
        description="Indicates if the model supports additional functions, such as plugins or APIs.",
    )
    supports_json_mode: bool = Field(
        default=False,
        description="Indicates if the model supports structured JSON input and output.",
    )
    supports_vision: bool = Field(
        default=False,
        description="Indicates if the model can process visual data such as images or videos.",
    )
    supports_streaming: bool = Field(
        default=True,
        description="Indicates if the model can stream responses incrementally.",
    )
    supports_audio_input: bool = Field(
        default=False, description="Indicates if the model can process raw audio input."
    )
    supports_audio_output: bool = Field(
        default=False,
        description="Indicates if the model can generate raw audio output.",
    )
    default_temperature: float = Field(
        default=0.7,
        description="Default sampling temperature for generating responses.",
        ge=0.0,
        le=2.0,
    )

    model_config = ConfigDict(frozen=True, validate_assignment=True)

    @field_validator("max_output_tokens", mode="after")
    @classmethod
    def validate_output_tokens(cls, value: Optional[int], info) -> Optional[int]:
        """
        Ensure that max_output_tokens does not exceed max_context_tokens.

        Args:
            value: The max_output_tokens value to validate.
            info: Additional context for the field validation.

        Returns:
            The validated max_output_tokens value.

        Raises:
            ValueError: If max_output_tokens exceeds max_context_tokens.
        """
        if value is not None and info.data.get("max_context_tokens") is not None:
            max_context = info.data["max_context_tokens"]
            if value > max_context:
                raise ValueError(
                    f"max_output_tokens ({value}) cannot exceed "
                    f"max_context_tokens ({max_context})."
                )
        return value


class ModelConfig(BaseModel):
    """
    Configuration for a specific model.

    Attributes:
        provider: The provider of the model (e.g., Azure, OpenAI, Anthropic).
        name: The name of the model.
        capabilities: The capabilities and limitations of the model.
        version: Optional version identifier for the model.
        deployment_name: Optional deployment-specific identifier for the model.
        description: Optional description of the model.
        supported_mime_types: Optional list of MIME types supported by the model.
        built_in: Indicates if the model is a built-in (predefined) model.
    """

    provider: ModelProvider
    name: str
    capabilities: ModelCapabilities
    version: Optional[str] = None
    deployment_name: Optional[str] = None
    description: Optional[str] = None
    supported_mime_types: Optional[List[str]] = None
    built_in: bool = False  # Flag to indicate if the model is built-in

    model_config = ConfigDict(
        frozen=True, use_enum_values=False, validate_assignment=True
    )

    def __str__(self) -> str:
        """
        String representation of the model.

        Returns:
            A string in the format <provider>/<name>.
        """
        return f"{self.provider.value}/{self.name}"

    @property
    def full_name(self) -> str:
        """
        Get the full model name, including the provider.

        Returns:
            The full name in the format <provider>/<deployment_name> or <provider>/<name>.
        """
        if self.provider == ModelProvider.AZURE:
            return f"{self.provider.value}/{self.deployment_name or self.name}"
        return f"{self.provider.value}/{self.name}"

    @model_validator(mode='after')
    def validate_mime_types(self) -> 'ModelConfig':
        """
        Validate that models with media capabilities define appropriate MIME types.

        Returns:
            The validated ModelConfig instance.

        Raises:
            ValueError: If MIME types don't match the model's capabilities.
        """
        caps = self.capabilities
        required_mime_prefixes = []

        # Build list of required MIME type prefixes based on capabilities
        if caps.supports_vision:
            required_mime_prefixes.append("image/")
        if caps.supports_audio_input or caps.supports_audio_output:
            required_mime_prefixes.append("audio/")
        
        # Skip validation if no media capabilities
        if not required_mime_prefixes:
            return self

        # Validate MIME types are present and match capabilities
        if not self.supported_mime_types:
            raise ValueError(
                f"Model '{self.name}' has media capabilities but lacks supported MIME types. "
                f"Required MIME type prefixes: {required_mime_prefixes}"
            )

        # Validate each MIME type matches at least one required prefix
        for mime_type in self.supported_mime_types:
            if not any(mime_type.startswith(prefix) for prefix in required_mime_prefixes):
                raise ValueError(
                    f"Invalid MIME type for model '{self.name}': {mime_type}. "
                    f"MIME types must start with one of: {required_mime_prefixes}"
                )

        return self

    def clone_with(self, **overrides) -> 'ModelConfig':
        """
        Clone the current model configuration with specified overrides.
        
        Args:
            **overrides: Keyword arguments to override specific attributes.
                        Only existing model attributes can be overridden.
        
        Returns:
            ModelConfig: A new instance with the specified overrides.
        
        Raises:
            ValueError: If an invalid override key is provided.
        """
        # Validate override keys
        valid_fields = self.model_fields.keys()
        invalid_keys = set(overrides.keys()) - set(valid_fields)
        if invalid_keys:
            raise ValueError(f"Invalid override keys: {invalid_keys}. Valid fields are: {valid_fields}")

        # Create new config with current values and overrides
        config_data = self.model_dump()
        config_data.update(overrides)
        
        return ModelConfig(**config_data)
