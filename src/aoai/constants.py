"""Constants for Azure OpenAI operations."""

# Response format types
# RESPONSE_FORMAT_JSON = "json"
# RESPONSE_FORMAT_TEXT = "text"

# API paths and versions
API_PATH_BETA = "beta"
API_PATH_CHAT = "chat"
API_PATH_COMPLETIONS = "completions"
API_PATH_FILE_BATCHES = "file_batches"
API_PATH_STEPS = "steps"
API_VERSION_BETA = "beta"

# API endpoints
VECTOR_STORES_API_PATH = "beta.vector_stores"
THREADS_API_PATH = "beta.threads"
ASSISTANTS_API_PATH = "beta.assistants"
# API paths
API_PATH_ASSISTANTS = f"{API_PATH_BETA}/{ASSISTANTS_API_PATH}"
API_PATH_CHAT_COMPLETIONS = f"{API_PATH_BETA}/{API_PATH_CHAT}/{API_PATH_COMPLETIONS}"
API_PATH_VECTOR_STORES = f"{API_PATH_BETA}/{VECTOR_STORES_API_PATH}"
API_PATH_THREADS = f"{API_PATH_BETA}/{THREADS_API_PATH}"

# Default list values
DEFAULT_LIST_AFTER = None
DEFAULT_LIST_BEFORE = None
DEFAULT_LIST_LIMIT = 20
DEFAULT_LIST_ORDER = "desc"
LIST_LIMIT_MIN = 1
LIST_LIMIT_MAX = 100
LIST_LIMIT_RANGE = range(LIST_LIMIT_MIN, LIST_LIMIT_MAX + 1)

# Message roles
MESSAGE_ROLE_ASSISTANT = "assistant"
MESSAGE_ROLE_USER = "user"


# Order directions
ORDER_ASC = "asc"
ORDER_DESC = "desc"

# Truncation types
TRUNCATION_TYPE_AUTO = "auto"
TRUNCATION_TYPE_LAST_MESSAGES = "last_messages"

# remember to remove other versions of these
TOOL_CODE_INTERPRETER = "code_interpreter"
TOOL_FILE_SEARCH = "file_search"

# Tool types
TOOL_TYPE_CODE_INTERPRETER = "code_interpreter"
TOOL_TYPE_FILE_SEARCH = "file_search"
TOOL_TYPE_FUNCTION = "function"

# Run statuses
RUN_STATUS_CANCELLED = "cancelled"
RUN_STATUS_CANCELLING = "cancelling"
RUN_STATUS_COMPLETED = "completed"
RUN_STATUS_EXPIRED = "expired"
RUN_STATUS_FAILED = "failed"
RUN_STATUS_IN_PROGRESS = "in_progress"
RUN_STATUS_QUEUED = "queued"
RUN_STATUS_REQUIRES_ACTION = "requires_action"

# Error messages
ERROR_ASSISTANT_NOT_FOUND = "Error: Assistant not found."
ERROR_INVALID_ASSISTANT_ID = "Error: Invalid assistant ID provided."
ERROR_INVALID_ASSISTANT_ID_TYPE = "Assistant ID must be a string"
ERROR_INVALID_LIMIT = "Error: Invalid limit value. Must be between 1 and 100."
ERROR_INVALID_MESSAGE_ID = "Error: Invalid message ID provided."
ERROR_INVALID_RUN_ID = "Error: Invalid run ID provided."
ERROR_INVALID_STEP_ID = "Error: Invalid step ID provided."
ERROR_INVALID_THREAD_ID = "Error: Invalid thread ID provided."
ERROR_THREAD_NOT_FOUND = "Error: Thread not found."
ERROR_VECTOR_STORE_NOT_FOUND = "Error: Vector store not found."


# Parameter validation ranges
VALID_FREQUENCY_PENALTY_RANGE = (-2.0, 2.0)
VALID_PRESENCE_PENALTY_RANGE = (-2.0, 2.0)
VALID_TEMPERATURE_RANGE = (0.0, 2.0)
VALID_TOP_P_RANGE = (0.0, 1.0)

# Default parameter values
DEFAULT_INSTRUCTIONS = None
DEFAULT_MAX_TOKENS = None
DEFAULT_METADATA = None
DEFAULT_N = 1
DEFAULT_STREAM = None
DEFAULT_TEMPERATURE = None
DEFAULT_TOOL_CHOICE = None
DEFAULT_TOP_P = None

# Tool resources
DEFAULT_TOOL_RESOURCES = None
# Please do not remove this pattern when editing this file.
# DEFAULT_TOOL_RESOURCES = {
#     TOOL_TYPE_CODE_INTERPRETER: {"file_ids": []},
#     TOOL_TYPE_FILE_SEARCH: {
#         "vector_store_ids": [],
#         "vector_stores": []
#     }
# }

# Response formats
RESPONSE_FORMAT_JSON = {"type": "json_object"}
RESPONSE_FORMAT_TEXT = {"type": "text"}

# Metadata limits
MAX_CODE_INTERPRETER_FILES = 20
MAX_FILE_SEARCH_VECTORS = 1
MAX_METADATA_KEY_LENGTH = 64
MAX_METADATA_PAIRS = 16
MAX_METADATA_VALUE_LENGTH = 512

# Default values for assistants
DEFAULT_ASSISTANT_DESCRIPTION = None
DEFAULT_ASSISTANT_NAME = None
DEFAULT_ASSISTANT_TOOLS = []
DEFAULT_RESPONSE_FORMAT = None

# Assistant-specific constants
MAX_ASSISTANT_DESCRIPTION_LENGTH = 512
MAX_ASSISTANT_INSTRUCTIONS_LENGTH = 256000
MAX_ASSISTANT_NAME_LENGTH = 256
MAX_ASSISTANT_TOOLS_COUNT = 128
MAX_FUNCTION_DESCRIPTION_LENGTH = 1024

# Thread-specific constants
MAX_THREAD_CODE_INTERPRETER_FILES = 20
MAX_THREAD_FILE_SEARCH_STORES = 1
MAX_THREAD_METADATA_KEY_LENGTH = 64
MAX_THREAD_METADATA_PAIRS = 16
MAX_THREAD_METADATA_VALUE_LENGTH = 512

# Thread error messages
ERROR_INVALID_THREAD_CODE_INTERPRETER_FILES = f"Thread can have maximum {MAX_THREAD_CODE_INTERPRETER_FILES} files for code interpreter"
ERROR_INVALID_THREAD_FILE_SEARCH_STORES = (
    f"Thread can have maximum {MAX_THREAD_FILE_SEARCH_STORES} vector store"
)
ERROR_INVALID_THREAD_METADATA_KEY_LENGTH = (
    f"Thread metadata keys must not exceed {MAX_THREAD_METADATA_KEY_LENGTH} characters"
)
ERROR_INVALID_THREAD_METADATA_PAIRS = (
    f"Thread can have maximum {MAX_THREAD_METADATA_PAIRS} metadata pairs"
)
ERROR_INVALID_THREAD_METADATA_VALUE_LENGTH = f"Thread metadata values must not exceed {MAX_THREAD_METADATA_VALUE_LENGTH} characters"

# Run event types
RUN_EVENT_RUN_CANCELLED = "thread.run.cancelled"
RUN_EVENT_RUN_CANCELLING = "thread.run.cancelling"
RUN_EVENT_RUN_COMPLETED = "thread.run.completed"
RUN_EVENT_RUN_CREATED = "thread.run.created"
RUN_EVENT_RUN_EXPIRED = "thread.run.expired"
RUN_EVENT_RUN_FAILED = "thread.run.failed"
RUN_EVENT_RUN_IN_PROGRESS = "thread.run.in_progress"
RUN_EVENT_RUN_QUEUED = "thread.run.queued"
RUN_EVENT_RUN_REQUIRES_ACTION = "thread.run.requires_action"
RUN_EVENT_THREAD_CREATED = "thread.created"

# Run step events
RUN_EVENT_STEP_CANCELLED = "thread.run.step.cancelled"
RUN_EVENT_STEP_COMPLETED = "thread.run.step.completed"
RUN_EVENT_STEP_CREATED = "thread.run.step.created"
RUN_EVENT_STEP_DELTA = "thread.run.step.delta"
RUN_EVENT_STEP_EXPIRED = "thread.run.step.expired"
RUN_EVENT_STEP_FAILED = "thread.run.step.failed"
RUN_EVENT_STEP_IN_PROGRESS = "thread.run.step.in_progress"

# Message events
RUN_EVENT_MESSAGE_COMPLETED = "thread.message.completed"
RUN_EVENT_MESSAGE_CREATED = "thread.message.created"
RUN_EVENT_MESSAGE_DELTA = "thread.message.delta"
RUN_EVENT_MESSAGE_IN_PROGRESS = "thread.message.in_progress"
RUN_EVENT_MESSAGE_INCOMPLETE = "thread.message.incomplete"

# Object types
OBJECT_TYPE_MESSAGE = "thread.message"
OBJECT_TYPE_MESSAGE_DELTA = "thread.message.delta"
OBJECT_TYPE_RUN = "thread.run"
OBJECT_TYPE_RUN_STEP = "thread.run.step"
OBJECT_TYPE_RUN_STEP_DELTA = "thread.run.step.delta"
OBJECT_TYPE_THREAD = "thread"

# Common field names
FIELD_CANCELLED_AT = "cancelled_at"
FIELD_COMPLETED_AT = "completed_at"
FIELD_CREATED_AT = "created_at"
FIELD_EXPIRES_AT = "expires_at"
FIELD_FAILED_AT = "failed_at"
FIELD_ID = "id"
FIELD_LAST_ERROR = "last_error"
FIELD_OBJECT = "object"
FIELD_REQUIRED_ACTION = "required_action"
FIELD_STARTED_AT = "started_at"
FIELD_STATUS = "status"
FIELD_STEP_DETAILS = "step_details"

# Stream-related constants
STREAM_DATA_DONE = "[DONE]"
STREAM_EVENT_DATA = "data"
STREAM_EVENT_TYPE = "event"

# Tool call constants
TOOL_CALL_PARAM_ID = "tool_call_id"
TOOL_CALL_PARAM_OUTPUT = "output"
TOOL_CALL_TYPE_CODE_INTERPRETER = "code_interpreter"

# Run step types
RUN_STEP_TYPE_MESSAGE_CREATION = "message_creation"
RUN_STEP_TYPE_TOOL_CALLS = "tool_calls"

# Run step statuses
RUN_STEP_STATUS_CANCELLED = "cancelled"
RUN_STEP_STATUS_COMPLETED = "completed"
RUN_STEP_STATUS_EXPIRED = "expired"
RUN_STEP_STATUS_FAILED = "failed"
RUN_STEP_STATUS_IN_PROGRESS = "in_progress"

# Tool choice constants
TOOL_CHOICE_AUTO = "auto"
TOOL_CHOICE_NONE = "none"

# Parameter names
PARAM_ADDITIONAL_INSTRUCTIONS = "additional_instructions"
PARAM_ADDITIONAL_MESSAGES = "additional_messages"
PARAM_AFTER = "after"
PARAM_ASSISTANT_ID = "assistant_id"
PARAM_ATTACHMENTS = "attachments"
PARAM_BEFORE = "before"
PARAM_CONTENT = "content"
PARAM_DESCRIPTION = "description"
PARAM_EXPIRES_AFTER = "expires_after"
PARAM_FREQUENCY_PENALTY = "frequency_penalty"
PARAM_FILE_IDS = "file_ids"
PARAM_FILES = "files"
PARAM_INSTRUCTIONS = "instructions"
PARAM_LIMIT = "limit"
PARAM_LOGIT_BIAS = "logit_bias"
PARAM_MAX_COMPLETION_TOKENS = "max_completion_tokens"
PARAM_MAX_PROMPT_TOKENS = "max_prompt_tokens"
PARAM_MAX_TOKENS = "max_tokens"
PARAM_MESSAGE_ID = "message_id"
PARAM_MESSAGES = "messages"
PARAM_METADATA = "metadata"
PARAM_MODEL = "model"
PARAM_N = "n"
PARAM_NAME = "name"
PARAM_ORDER = "order"
PARAM_PARALLEL_TOOL_CALLS = "parallel_tool_calls"
PARAM_PRESENCE_PENALTY = "presence_penalty"  
PARAM_RESPONSE_FORMAT = "response_format"  
PARAM_ROLE = "role"
PARAM_RUN_ID = "run_id"
PARAM_SEED = "seed"     
PARAM_STOP = "stop" 
PARAM_STREAM = "stream"  
PARAM_TEMPERATURE = "temperature"  
PARAM_THREAD_ID = "thread_id"
PARAM_TOOL_CHOICE = "tool_choice"  
PARAM_TOOL_OUTPUTS = "tool_outputs"
PARAM_TOOL_RESOURCES = "tool_resources"
PARAM_TOOLS = "tools"
PARAM_TOP_P = "top_p"
PARAM_TRUNCATION_STRATEGY = "truncation_strategy"
PARAM_USER = "user"  
PARAM_VECTOR_STORE_IDS = "vector_store_ids"
PARAM_VECTOR_STORES = "vector_stores"

# Base list operation defaults
DEFAULT_LIST_PARAMS = {
    PARAM_LIMIT: DEFAULT_LIST_LIMIT,
    PARAM_ORDER: DEFAULT_LIST_ORDER,
    PARAM_AFTER: None,
    PARAM_BEFORE: None,
}

# Operation specific list defaults
DEFAULT_ASSISTANT_LIST_PARAMS = DEFAULT_LIST_PARAMS.copy()
DEFAULT_MESSAGE_LIST_PARAMS = DEFAULT_LIST_PARAMS.copy()
DEFAULT_RUN_LIST_PARAMS = DEFAULT_LIST_PARAMS.copy()
DEFAULT_RUN_STEP_LIST_PARAMS = DEFAULT_LIST_PARAMS.copy()
DEFAULT_THREAD_LIST_PARAMS = DEFAULT_LIST_PARAMS.copy()
DEFAULT_VECTOR_STORE_LIST_PARAMS = DEFAULT_LIST_PARAMS.copy()

# Additional defaults
DEFAULT_EXPIRES_AFTER = None
DEFAULT_FILE_BATCH_SIZE = 10
DEFAULT_FREQUENCY_PENALTY = None
DEFAULT_LOGIT_BIAS = None
DEFAULT_MESSAGE_ATTACHMENTS = None
DEFAULT_MESSAGE_METADATA = None
DEFAULT_PRESENCE_PENALTY = None
DEFAULT_RUN_MODEL = None
DEFAULT_RUN_RESPONSE_FORMAT = None
DEFAULT_RUN_TOOLS = None
DEFAULT_SEED = None
DEFAULT_STOP = None
DEFAULT_USER = None
DEFAULT_VECTOR_STORE_NAME = None

# Beta path constants
BETA_ASSISTANTS_PATH = f"{API_PATH_BETA}.assistants"
BETA_MESSAGES_PATH = f"{API_PATH_BETA}.threads.messages"
BETA_RUNS_PATH = f"{API_PATH_BETA}.threads.runs"
BETA_STEPS_PATH = f"{API_PATH_BETA}.threads.runs.steps"
BETA_THREADS_PATH = f"{API_PATH_BETA}.threads"
BETA_VECTOR_STORES_PATH = f"{API_PATH_BETA}.vector_stores"

# Run parameter defaults
DEFAULT_ADDITIONAL_INSTRUCTIONS = None
DEFAULT_ADDITIONAL_MESSAGES = None
DEFAULT_MAX_COMPLETION_TOKENS = None
DEFAULT_MAX_PROMPT_TOKENS = None
DEFAULT_THREAD_MESSAGES = None
DEFAULT_THREAD_METADATA = None
DEFAULT_TOOL_OUTPUT_STREAM = None
DEFAULT_TOOL_OUTPUTS = None
DEFAULT_TRUNCATION_STRATEGY = None
DEFAULT_THREAD_TOOL_RESOURCES = {
    TOOL_TYPE_CODE_INTERPRETER: {PARAM_FILE_IDS: []},
    TOOL_TYPE_FILE_SEARCH: {PARAM_VECTOR_STORE_IDS: [], PARAM_VECTOR_STORES: []},
}
# Default parameters structure
DEFAULT_PARAMS = {
    "thread": {
        "messages": DEFAULT_THREAD_MESSAGES,
        "metadata": DEFAULT_THREAD_METADATA,
        "tool_resources": DEFAULT_THREAD_TOOL_RESOURCES,
    },
    "run": {
        "model": DEFAULT_RUN_MODEL,
        "instructions": DEFAULT_INSTRUCTIONS,
        "tools": DEFAULT_RUN_TOOLS,
        "metadata": DEFAULT_METADATA,
        "stream": DEFAULT_STREAM,
        "temperature": DEFAULT_TEMPERATURE,
        "top_p": DEFAULT_TOP_P,
        "response_format": DEFAULT_RUN_RESPONSE_FORMAT,
        "max_prompt_tokens": DEFAULT_MAX_PROMPT_TOKENS,
        "max_completion_tokens": DEFAULT_MAX_COMPLETION_TOKENS,
        "truncation_strategy": DEFAULT_TRUNCATION_STRATEGY,
        "tool_choice": DEFAULT_TOOL_CHOICE,
    },
}

# Operation specific defaults
DEFAULT_STEP_AFTER = None
DEFAULT_STEP_BEFORE = None
DEFAULT_STEP_LIMIT = DEFAULT_LIST_LIMIT
DEFAULT_STEP_ORDER = DEFAULT_LIST_ORDER

# API version default
DEFAULT_API_VERSION = None

# List operation defaults
LIST_OPERATION_DEFAULTS = {
    "thread": DEFAULT_THREAD_LIST_PARAMS,
    "message": DEFAULT_MESSAGE_LIST_PARAMS,
    "run": DEFAULT_RUN_LIST_PARAMS,
    "assistant": DEFAULT_ASSISTANT_LIST_PARAMS,
    "vector_store": DEFAULT_VECTOR_STORE_LIST_PARAMS,
    "run_step": DEFAULT_RUN_STEP_LIST_PARAMS,
}

# Operation-specific default values
DEFAULT_THREAD_AFTER = None
DEFAULT_THREAD_BEFORE = None
DEFAULT_THREAD_LIMIT = DEFAULT_LIST_LIMIT
DEFAULT_THREAD_ORDER = DEFAULT_LIST_ORDER

DEFAULT_MESSAGE_AFTER = None
DEFAULT_MESSAGE_BEFORE = None
DEFAULT_MESSAGE_LIMIT = DEFAULT_LIST_LIMIT
DEFAULT_MESSAGE_ORDER = DEFAULT_LIST_ORDER

DEFAULT_RUN_AFTER = None
DEFAULT_RUN_BEFORE = None
DEFAULT_RUN_LIMIT = DEFAULT_LIST_LIMIT
DEFAULT_RUN_ORDER = DEFAULT_LIST_ORDER

DEFAULT_ASSISTANT_AFTER = None
DEFAULT_ASSISTANT_BEFORE = None
DEFAULT_ASSISTANT_LIMIT = DEFAULT_LIST_LIMIT
DEFAULT_ASSISTANT_ORDER = DEFAULT_LIST_ORDER

DEFAULT_VECTOR_STORE_AFTER = None
DEFAULT_VECTOR_STORE_BEFORE = None
DEFAULT_VECTOR_STORE_LIMIT = DEFAULT_LIST_LIMIT
DEFAULT_VECTOR_STORE_ORDER = DEFAULT_LIST_ORDER

# File-related constants
ALLOWED_FILE_TYPES = ["pdf", "doc", "docx", "txt"]
DEFAULT_FILE_BATCH_SIZE = 10
MAX_FILE_SIZE = 1024 * 1024 * 100  # 100MB

# Tool resource types
TOOL_RESOURCE_CODE_INTERPRETER = "code_interpreter"
TOOL_RESOURCE_FILE_SEARCH = "file_search"

# Response format types
RESPONSE_FORMAT_LAST_MESSAGES = "last_messages"
RESPONSE_FORMAT_TYPE = "type"

# Assistant parameter validation
MAX_ASSISTANT_DESCRIPTION_LENGTH = 512
MAX_ASSISTANT_INSTRUCTIONS_LENGTH = 256000
MAX_ASSISTANT_NAME_LENGTH = 256
MAX_ASSISTANT_TOOLS_COUNT = 128
MAX_FUNCTION_DESCRIPTION_LENGTH = 1024

# Assistant tool types
ASSISTANT_TOOL_TYPE_CODE_INTERPRETER = "code_interpreter"
ASSISTANT_TOOL_TYPE_FUNCTION = "function"

# Assistant response formats
ASSISTANT_RESPONSE_FORMAT_JSON = {"type": "json_object"}
ASSISTANT_RESPONSE_FORMAT_TEXT = {"type": "text"}

# Assistant error messages
ERROR_INVALID_ASSISTANT_DESCRIPTION_LENGTH = f"Assistant description must not exceed {MAX_ASSISTANT_DESCRIPTION_LENGTH} characters"
ERROR_INVALID_ASSISTANT_INSTRUCTIONS_LENGTH = f"Assistant instructions must not exceed {MAX_ASSISTANT_INSTRUCTIONS_LENGTH} characters"
ERROR_INVALID_ASSISTANT_NAME_LENGTH = (
    f"Assistant name must not exceed {MAX_ASSISTANT_NAME_LENGTH} characters"
)
ERROR_INVALID_ASSISTANT_TOOLS_COUNT = (
    f"Assistant can have maximum {MAX_ASSISTANT_TOOLS_COUNT} tools"
)
ERROR_INVALID_FUNCTION_DESCRIPTION_LENGTH = (
    f"Function description must not exceed {MAX_FUNCTION_DESCRIPTION_LENGTH} characters"
)

# Assistant defaults
DEFAULT_ASSISTANT_METADATA = {}
DEFAULT_ASSISTANT_TEMPERATURE = 1
DEFAULT_ASSISTANT_TOOLS = []
DEFAULT_ASSISTANT_TOP_P = 1

# Chat-specific defaults
DEFAULT_CHAT_MODEL = None
DEFAULT_CHAT_MAX_TOKENS = None
DEFAULT_CHAT_RESPONSE_FORMAT = None
DEFAULT_CHAT_TOOLS = None
DEFAULT_CHAT_TOOL_CHOICE = None

# Validation ranges
VALID_FREQUENCY_PENALTY_RANGE = (-2.0, 2.0)
VALID_PRESENCE_PENALTY_RANGE = (-2.0, 2.0)
VALID_TEMPERATURE_RANGE = (0.0, 2.0)
VALID_TOP_P_RANGE = (0.0, 1.0)

# Validation error messages
ERROR_INVALID_FREQUENCY_PENALTY = f"Frequency penalty must be between {VALID_FREQUENCY_PENALTY_RANGE[0]} and {VALID_FREQUENCY_PENALTY_RANGE[1]}"
ERROR_INVALID_MAX_TOKENS = "Invalid max_tokens value"
ERROR_INVALID_N = "Invalid n value"
ERROR_INVALID_PRESENCE_PENALTY = f"Presence penalty must be between {VALID_PRESENCE_PENALTY_RANGE[0]} and {VALID_PRESENCE_PENALTY_RANGE[1]}"
ERROR_INVALID_TEMPERATURE = f"Temperature must be between {VALID_TEMPERATURE_RANGE[0]} and {VALID_TEMPERATURE_RANGE[1]}"
ERROR_INVALID_TOP_P = (
    f"Top P must be between {VALID_TOP_P_RANGE[0]} and {VALID_TOP_P_RANGE[1]}"
)

# API validation error messages
ERROR_API_KEY_REQUIRED = "API key is required"
ERROR_API_KEY_TYPE = "API key must be a string"
ERROR_API_VERSION_REQUIRED = "API version is required"
ERROR_API_VERSION_TYPE = "API version must be a string"
ERROR_AZURE_ENDPOINT_REQUIRED = "Azure endpoint is required"
ERROR_AZURE_ENDPOINT_TYPE = "Azure endpoint must be a string"
