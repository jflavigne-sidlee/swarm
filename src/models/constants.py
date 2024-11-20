"""Constants used for model configuration and environment variables."""

VISION_MIME_TYPES = ["image/jpeg", "image/png", "image/gif", "image/webp"]
AUDIO_MIME_TYPES = ["audio/wav", "audio/mpeg", "audio/mp3", "audio/ogg"]
MULTIMODAL_MIME_TYPES = VISION_MIME_TYPES + AUDIO_MIME_TYPES

# Environment Variables
ENV_AZURE_DEPLOYMENT_OVERRIDE = "AZURE_DEPLOYMENT_OVERRIDE"
ENV_AZURE_DEPLOYMENT_PREFIX = "AZURE_DEPLOYMENT_"

# Provider Path Separator
PROVIDER_PATH_SEPARATOR = "/"

# Error Messages
ERROR_VISION_MIME_TYPES = "Vision models must support image MIME types: {model_name}"
ERROR_INVALID_PROVIDER = "Invalid provider '{provider}'. Must be one of {valid_providers}"
ERROR_PROVIDER_TYPE = "Provider must be a ModelProvider enum. Got: {provider_type}"
ERROR_MODEL_NOT_FOUND = "Model not found: '{name}'. Available models: {available}"
ERROR_AMBIGUOUS_MODEL = (
    "Ambiguous model name '{name}'. Found multiple matches:\n"
    "{conflict_details}\n"
    "Please specify the provider using <provider>/<name>."
)
ERROR_DEPLOYMENT_CONFLICT = (
    "Conflicting deployment names for {name}: "
    "deployment={specific}, override={override}. "
    "Please resolve this conflict before adding the model."
)
ERROR_DEPLOYMENT_NAME_CONFLICT = (
    "Deployment name conflict: {deployment_name} "
    "already used by {existing_model}"
)
ERROR_UNKNOWN_CAPABILITY = "Unknown capability: {capability}"

# Warning Messages
WARNING_DEPLOYMENT_CONFLICT = (
    "Conflict detected for built-in model {name}. "
    "Using {specific} over override={override}."
)

# Logging Messages
LOG_PROVIDER_CONVERSION = "Converted provider '{provider}' to enum." 