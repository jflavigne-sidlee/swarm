"""Constants for Azure Client operations."""

# API paths
VECTOR_STORES_API_PATH = "beta.vector_stores"
THREADS_API_PATH = "beta.threads"
ASSISTANTS_API_PATH = "beta.assistants"

# API paths and endpoints
API_PATH_BETA = "beta"
API_PATH_CHAT = "chat"
API_PATH_COMPLETIONS = "completions"
API_PATH_FILE_BATCHES = "file_batches"
API_PATH_STEPS = "steps"

# Default values
DEFAULT_LIST_LIMIT = 20
DEFAULT_LIST_ORDER = "desc"  # Assuming this is the default order
DEFAULT_MAX_METADATA_PAIRS = 16

# Metadata limits
MAX_METADATA_KEY_LENGTH = 64
MAX_METADATA_VALUE_LENGTH = 512
MAX_CODE_INTERPRETER_FILES = 20
MAX_FILE_SEARCH_VECTORS = 1

# List limit range
LIST_LIMIT_MIN = 1
LIST_LIMIT_MAX = 100
LIST_LIMIT_RANGE = range(LIST_LIMIT_MIN, LIST_LIMIT_MAX + 1)  # 1-100

# Error messages
ERROR_VECTOR_STORE_NOT_FOUND = "Error: Vector store not found."
ERROR_THREAD_NOT_FOUND = "Error: Thread not found."
ERROR_ASSISTANT_NOT_FOUND = "Error: Assistant not found."
ERROR_INVALID_THREAD_ID = "Error: Invalid thread ID provided."
ERROR_INVALID_MESSAGE_ID = "Error: Invalid message ID provided."
ERROR_INVALID_ASSISTANT_ID = "Error: Invalid assistant ID provided."
ERROR_INVALID_RUN_ID = "Error: Invalid run ID provided."

# Message roles
MESSAGE_ROLE_USER = "user"
MESSAGE_ROLE_ASSISTANT = "assistant"

# Truncation types
TRUNCATION_TYPE_AUTO = "auto"
TRUNCATION_TYPE_LAST_MESSAGES = "last_messages"

# Run statuses
RUN_STATUS_QUEUED = "queued"
RUN_STATUS_IN_PROGRESS = "in_progress"
RUN_STATUS_REQUIRES_ACTION = "requires_action"
RUN_STATUS_CANCELLING = "cancelling"
RUN_STATUS_CANCELLED = "cancelled"
RUN_STATUS_FAILED = "failed"
RUN_STATUS_COMPLETED = "completed"
RUN_STATUS_EXPIRED = "expired"

# API Version paths
API_VERSION_BETA = "beta"

# Tool types
TOOL_TYPE_CODE_INTERPRETER = "code_interpreter"
TOOL_TYPE_FILE_SEARCH = "file_search"
TOOL_TYPE_FUNCTION = "function"

# Order directions
ORDER_ASC = "asc"
ORDER_DESC = "desc"

# Parameter keys
PARAM_FILE_IDS = "file_ids"
PARAM_VECTOR_STORE_IDS = "vector_store_ids"
PARAM_MESSAGES = "messages"
PARAM_PARALLEL_TOOL_CALLS = "parallel_tool_calls"
PARAM_RUN_ID = "run_id"
PARAM_VECTOR_STORES = "vector_stores"

# Default parameter values
DEFAULT_PARALLEL_TOOL_CALLS = True

# Response format keys
RESPONSE_FORMAT_TYPE = "type"
RESPONSE_FORMAT_LAST_MESSAGES = "last_messages"

# Parameter names
PARAM_MODEL = "model"
PARAM_NAME = "name"
PARAM_DESCRIPTION = "description"
PARAM_INSTRUCTIONS = "instructions"
PARAM_TOOLS = "tools"
PARAM_METADATA = "metadata"
PARAM_TEMPERATURE = "temperature"
PARAM_TOP_P = "top_p"
PARAM_RESPONSE_FORMAT = "response_format"
PARAM_TOOL_RESOURCES = "tool_resources"
PARAM_THREAD_ID = "thread_id"
PARAM_MESSAGE_ID = "message_id"
PARAM_ROLE = "role"
PARAM_CONTENT = "content"
PARAM_ATTACHMENTS = "attachments"
PARAM_STREAM = "stream"
PARAM_ASSISTANT_ID = "assistant_id"

# Default values for chat parameters
DEFAULT_TEMPERATURE = None  
DEFAULT_TOP_P = None       
DEFAULT_N = 1             # Default number of completions
DEFAULT_MAX_TOKENS = None # Default max tokens (None means model maximum)

# Chat completion specific constants
CHAT_PARAM_N = "n"
CHAT_PARAM_STOP = "stop"
CHAT_PARAM_MAX_TOKENS = "max_tokens"
CHAT_PARAM_PRESENCE_PENALTY = "presence_penalty"
CHAT_PARAM_FREQUENCY_PENALTY = "frequency_penalty"
CHAT_PARAM_LOGIT_BIAS = "logit_bias"
CHAT_PARAM_USER = "user"
CHAT_PARAM_SEED = "seed"
CHAT_PARAM_TOOL_CHOICE = "tool_choice"
CHAT_PARAM_TEMPERATURE = "temperature"
CHAT_PARAM_STREAM = "stream"
CHAT_PARAM_RESPONSE_FORMAT = "response_format"

# Run specific parameters
RUN_PARAM_ADDITIONAL_INSTRUCTIONS = "additional_instructions"
RUN_PARAM_ADDITIONAL_MESSAGES = "additional_messages"
RUN_PARAM_MAX_PROMPT_TOKENS = "max_prompt_tokens"
RUN_PARAM_MAX_COMPLETION_TOKENS = "max_completion_tokens"
RUN_PARAM_TRUNCATION_STRATEGY = "truncation_strategy"

# Tool choice constants
TOOL_CHOICE_AUTO = "auto"
TOOL_CHOICE_NONE = "none"

# Default values for list operations
DEFAULT_LIST_AFTER = None
DEFAULT_LIST_BEFORE = None

# Tool resource keys
TOOL_RESOURCE_CODE_INTERPRETER = "code_interpreter"
TOOL_RESOURCE_FILE_SEARCH = "file_search"

# Common parameter keys
PARAM_LIMIT = "limit"
PARAM_ORDER = "order"
PARAM_AFTER = "after"
PARAM_BEFORE = "before"
PARAM_EXPIRES_AFTER = "expires_after"
PARAM_FILES = "files"
PARAM_MODEL = "model"
PARAM_STREAM = "stream"
PARAM_TOOL_OUTPUTS = "tool_outputs"

# Response format types
RESPONSE_FORMAT_JSON = "json"
RESPONSE_FORMAT_TEXT = "text"

# Common field names
FIELD_ID = "id"

# Default values for tool resources
DEFAULT_TOOL_RESOURCES = None
DEFAULT_INSTRUCTIONS = None
DEFAULT_ADDITIONAL_INSTRUCTIONS = None
DEFAULT_ADDITIONAL_MESSAGES = None
DEFAULT_TRUNCATION_STRATEGY = None
DEFAULT_TOOL_CHOICE = None
DEFAULT_METADATA = None
DEFAULT_ATTACHMENTS = None
DEFAULT_FILES = None

# Stream defaults
DEFAULT_STREAM = None

# Token limits
DEFAULT_MAX_PROMPT_TOKENS = None
DEFAULT_MAX_COMPLETION_TOKENS = None

# Penalty defaults
DEFAULT_PRESENCE_PENALTY = None
DEFAULT_FREQUENCY_PENALTY = None

# Other defaults
DEFAULT_LOGIT_BIAS = None
DEFAULT_SEED = None
DEFAULT_USER = None
DEFAULT_STOP = None

# Common parameter names for runs
PARAM_INSTRUCTIONS = "instructions"
PARAM_ADDITIONAL_INSTRUCTIONS = "additional_instructions"
PARAM_ADDITIONAL_MESSAGES = "additional_messages"
PARAM_TRUNCATION_STRATEGY = "truncation_strategy"
PARAM_TOOL_CHOICE = "tool_choice"
PARAM_TOOL_OUTPUTS = "tool_outputs"
PARAM_METADATA = "metadata"

# Default values for vector stores
DEFAULT_VECTOR_STORE_NAME = None
DEFAULT_EXPIRES_AFTER = None

# Default values for assistants
DEFAULT_ASSISTANT_NAME = None
DEFAULT_ASSISTANT_DESCRIPTION = None
DEFAULT_ASSISTANT_TOOLS = []
DEFAULT_RESPONSE_FORMAT = None

# Default values for threads
DEFAULT_THREAD_MESSAGES = None
DEFAULT_THREAD_METADATA = None
DEFAULT_THREAD_TOOL_RESOURCES = {
    TOOL_TYPE_CODE_INTERPRETER: {PARAM_FILE_IDS: []},
    TOOL_TYPE_FILE_SEARCH: {
        PARAM_VECTOR_STORE_IDS: [],
        PARAM_VECTOR_STORES: []
    }
}

# Default values for messages
DEFAULT_MESSAGE_ATTACHMENTS = None
DEFAULT_MESSAGE_METADATA = None

# Default values for runs
DEFAULT_RUN_MODEL = None
DEFAULT_RUN_TOOLS = None
DEFAULT_RUN_RESPONSE_FORMAT = None

# Default values for run steps
DEFAULT_STEP_LIMIT = None
DEFAULT_STEP_ORDER = None
DEFAULT_STEP_AFTER = None
DEFAULT_STEP_BEFORE = None

# Default values for tool outputs
DEFAULT_TOOL_OUTPUTS = None
DEFAULT_TOOL_OUTPUT_STREAM = None

# API version defaults
DEFAULT_API_VERSION = API_VERSION_BETA

# Beta path constants
BETA_VECTOR_STORES_PATH = f"{API_PATH_BETA}.vector_stores"
BETA_THREADS_PATH = f"{API_PATH_BETA}.threads"
BETA_ASSISTANTS_PATH = f"{API_PATH_BETA}.assistants"
BETA_MESSAGES_PATH = f"{API_PATH_BETA}.threads.messages"
BETA_RUNS_PATH = f"{API_PATH_BETA}.threads.runs"
BETA_STEPS_PATH = f"{API_PATH_BETA}.threads.runs.steps"

# File related constants
DEFAULT_FILE_BATCH_SIZE = 10  # If there's a recommended batch size for file uploads
MAX_FILE_SIZE = 1024 * 1024 * 100  # 100MB example, adjust to actual limit
ALLOWED_FILE_TYPES = ["pdf", "doc", "docx", "txt"]  # Example, adjust to actual allowed types

# Chat completion parameter defaults
DEFAULT_CHAT_MODEL = None
DEFAULT_CHAT_TOOLS = None
DEFAULT_CHAT_TOOL_CHOICE = None
DEFAULT_CHAT_MAX_TOKENS = None
DEFAULT_CHAT_RESPONSE_FORMAT = None

# Thread operation defaults
DEFAULT_THREAD_LIMIT = DEFAULT_LIST_LIMIT
DEFAULT_THREAD_ORDER = DEFAULT_LIST_ORDER
DEFAULT_THREAD_AFTER = None
DEFAULT_THREAD_BEFORE = None

# Run operation defaults
DEFAULT_RUN_LIMIT = DEFAULT_LIST_LIMIT
DEFAULT_RUN_ORDER = DEFAULT_LIST_ORDER
DEFAULT_RUN_AFTER = None
DEFAULT_RUN_BEFORE = None

# Message operation defaults
DEFAULT_MESSAGE_LIMIT = DEFAULT_LIST_LIMIT
DEFAULT_MESSAGE_ORDER = DEFAULT_LIST_ORDER
DEFAULT_MESSAGE_AFTER = None
DEFAULT_MESSAGE_BEFORE = None

# Assistant operation defaults
DEFAULT_ASSISTANT_LIMIT = DEFAULT_LIST_LIMIT
DEFAULT_ASSISTANT_ORDER = DEFAULT_LIST_ORDER
DEFAULT_ASSISTANT_AFTER = None
DEFAULT_ASSISTANT_BEFORE = None

# Vector store operation defaults
DEFAULT_VECTOR_STORE_LIMIT = DEFAULT_LIST_LIMIT
DEFAULT_VECTOR_STORE_ORDER = DEFAULT_LIST_ORDER
DEFAULT_VECTOR_STORE_AFTER = None
DEFAULT_VECTOR_STORE_BEFORE = None

# Parameter validation constants
VALID_TEMPERATURE_RANGE = (0.0, 2.0)
VALID_TOP_P_RANGE = (0.0, 1.0)
VALID_PRESENCE_PENALTY_RANGE = (-2.0, 2.0)
VALID_FREQUENCY_PENALTY_RANGE = (-2.0, 2.0)

# API endpoint paths
API_PATH_CHAT_COMPLETIONS = f"{API_PATH_CHAT}/{API_PATH_COMPLETIONS}"
API_PATH_VECTOR_STORES = f"{API_PATH_BETA}/{VECTOR_STORES_API_PATH}"
API_PATH_THREADS = f"{API_PATH_BETA}/{THREADS_API_PATH}"
API_PATH_ASSISTANTS = f"{API_PATH_BETA}/{ASSISTANTS_API_PATH}"

# Error messages for validation
ERROR_INVALID_TEMPERATURE = "Temperature must be between 0 and 2"
ERROR_INVALID_TOP_P = "Top P must be between 0 and 1"
ERROR_INVALID_PRESENCE_PENALTY = "Presence penalty must be between -2 and 2"
ERROR_INVALID_FREQUENCY_PENALTY = "Frequency penalty must be between -2 and 2"
ERROR_INVALID_MAX_TOKENS = "Max tokens must be a positive integer"
ERROR_INVALID_N = "N must be a positive integer"
ERROR_INVALID_LIMIT = f"Limit must be between {LIST_LIMIT_MIN} and {LIST_LIMIT_MAX}"

# List parameter keys (add these if missing)
LIST_PARAM_LIMIT = "limit"
LIST_PARAM_ORDER = "order"
LIST_PARAM_AFTER = "after"
LIST_PARAM_BEFORE = "before"

# Base list operation defaults
DEFAULT_LIST_PARAMS = {
    LIST_PARAM_LIMIT: DEFAULT_LIST_LIMIT,
    LIST_PARAM_ORDER: DEFAULT_LIST_ORDER,
    LIST_PARAM_AFTER: None,
    LIST_PARAM_BEFORE: None
}

# Operation specific list defaults (all inheriting from base defaults)
DEFAULT_THREAD_LIST_PARAMS = DEFAULT_LIST_PARAMS.copy()
DEFAULT_MESSAGE_LIST_PARAMS = DEFAULT_LIST_PARAMS.copy()
DEFAULT_RUN_LIST_PARAMS = DEFAULT_LIST_PARAMS.copy()
DEFAULT_ASSISTANT_LIST_PARAMS = DEFAULT_LIST_PARAMS.copy()
DEFAULT_VECTOR_STORE_LIST_PARAMS = DEFAULT_LIST_PARAMS.copy()
DEFAULT_RUN_STEP_LIST_PARAMS = DEFAULT_LIST_PARAMS.copy()

# Run event types
RUN_EVENT_THREAD_CREATED = "thread.created"
RUN_EVENT_RUN_CREATED = "thread.run.created"
RUN_EVENT_RUN_QUEUED = "thread.run.queued"
RUN_EVENT_RUN_IN_PROGRESS = "thread.run.in_progress"
RUN_EVENT_RUN_REQUIRES_ACTION = "thread.run.requires_action"
RUN_EVENT_RUN_COMPLETED = "thread.run.completed"
RUN_EVENT_RUN_FAILED = "thread.run.failed"
RUN_EVENT_RUN_CANCELLING = "thread.run.cancelling"
RUN_EVENT_RUN_CANCELLED = "thread.run.cancelled"
RUN_EVENT_RUN_EXPIRED = "thread.run.expired"

# Run step event types
RUN_EVENT_STEP_CREATED = "thread.run.step.created"
RUN_EVENT_STEP_IN_PROGRESS = "thread.run.step.in_progress"
RUN_EVENT_STEP_DELTA = "thread.run.step.delta"
RUN_EVENT_STEP_COMPLETED = "thread.run.step.completed"
RUN_EVENT_STEP_FAILED = "thread.run.step.failed"
RUN_EVENT_STEP_CANCELLED = "thread.run.step.cancelled"
RUN_EVENT_STEP_EXPIRED = "thread.run.step.expired"

# Message event types
RUN_EVENT_MESSAGE_CREATED = "thread.message.created"
RUN_EVENT_MESSAGE_IN_PROGRESS = "thread.message.in_progress"
RUN_EVENT_MESSAGE_DELTA = "thread.message.delta"
RUN_EVENT_MESSAGE_COMPLETED = "thread.message.completed"
RUN_EVENT_MESSAGE_INCOMPLETE = "thread.message.incomplete"

# Other event types
RUN_EVENT_ERROR = "error"
RUN_EVENT_DONE = "done"

# Run step types
RUN_STEP_TYPE_MESSAGE_CREATION = "message_creation"
RUN_STEP_TYPE_TOOL_CALLS = "tool_calls"

# Run step statuses
RUN_STEP_STATUS_IN_PROGRESS = "in_progress"
RUN_STEP_STATUS_CANCELLED = "cancelled"
RUN_STEP_STATUS_FAILED = "failed"
RUN_STEP_STATUS_COMPLETED = "completed"
RUN_STEP_STATUS_EXPIRED = "expired"

# Tool call related constants
TOOL_CALL_TYPE_CODE_INTERPRETER = "code_interpreter"
TOOL_CALL_PARAM_ID = "tool_call_id"
TOOL_CALL_PARAM_OUTPUT = "output"

# Stream related constants
STREAM_EVENT_DATA = "data"
STREAM_EVENT_TYPE = "event"
STREAM_DATA_DONE = "[DONE]"

# Object types
OBJECT_TYPE_THREAD = "thread"
OBJECT_TYPE_RUN = "thread.run"
OBJECT_TYPE_RUN_STEP = "thread.run.step"
OBJECT_TYPE_MESSAGE = "thread.message"
OBJECT_TYPE_MESSAGE_DELTA = "thread.message.delta"
OBJECT_TYPE_RUN_STEP_DELTA = "thread.run.step.delta"

# Common field names for responses
FIELD_CREATED_AT = "created_at"
FIELD_EXPIRES_AT = "expires_at"
FIELD_STARTED_AT = "started_at"
FIELD_CANCELLED_AT = "cancelled_at"
FIELD_FAILED_AT = "failed_at"
FIELD_COMPLETED_AT = "completed_at"
FIELD_OBJECT = "object"
FIELD_STATUS = "status"
FIELD_LAST_ERROR = "last_error"
FIELD_REQUIRED_ACTION = "required_action"
FIELD_STEP_DETAILS = "step_details"

# Update existing default parameters section
DEFAULT_PARAMS = {
    # Thread defaults
    "thread": {
        "messages": DEFAULT_THREAD_MESSAGES,
        "metadata": DEFAULT_THREAD_METADATA,
        "tool_resources": DEFAULT_THREAD_TOOL_RESOURCES
    },
    # Run defaults
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
        "tool_choice": DEFAULT_TOOL_CHOICE
    }
}

# Update list operation defaults to be more specific
LIST_OPERATION_DEFAULTS = {
    "thread": DEFAULT_THREAD_LIST_PARAMS,
    "message": DEFAULT_MESSAGE_LIST_PARAMS,
    "run": DEFAULT_RUN_LIST_PARAMS,
    "assistant": DEFAULT_ASSISTANT_LIST_PARAMS,
    "vector_store": DEFAULT_VECTOR_STORE_LIST_PARAMS,
    "run_step": DEFAULT_RUN_STEP_LIST_PARAMS
}

# Assistant parameter validation constants
MAX_ASSISTANT_NAME_LENGTH = 256
MAX_ASSISTANT_DESCRIPTION_LENGTH = 512
MAX_ASSISTANT_INSTRUCTIONS_LENGTH = 256000
MAX_ASSISTANT_TOOLS_COUNT = 128
MAX_FUNCTION_DESCRIPTION_LENGTH = 1024

# Assistant tool types
ASSISTANT_TOOL_TYPE_CODE_INTERPRETER = "code_interpreter"
ASSISTANT_TOOL_TYPE_FUNCTION = "function"

# Assistant response format types
ASSISTANT_RESPONSE_FORMAT_JSON = {"type": "json_object"}
ASSISTANT_RESPONSE_FORMAT_TEXT = {"type": "text"}

# Assistant error messages
ERROR_INVALID_ASSISTANT_NAME_LENGTH = f"Assistant name must not exceed {MAX_ASSISTANT_NAME_LENGTH} characters"
ERROR_INVALID_ASSISTANT_DESCRIPTION_LENGTH = f"Assistant description must not exceed {MAX_ASSISTANT_DESCRIPTION_LENGTH} characters"
ERROR_INVALID_ASSISTANT_INSTRUCTIONS_LENGTH = f"Assistant instructions must not exceed {MAX_ASSISTANT_INSTRUCTIONS_LENGTH} characters"
ERROR_INVALID_ASSISTANT_TOOLS_COUNT = f"Assistant can have maximum {MAX_ASSISTANT_TOOLS_COUNT} tools"
ERROR_INVALID_FUNCTION_DESCRIPTION_LENGTH = f"Function description must not exceed {MAX_FUNCTION_DESCRIPTION_LENGTH} characters"

# Assistant defaults (update existing)
DEFAULT_ASSISTANT_TOOLS = []  # Empty list as per documentation
DEFAULT_ASSISTANT_METADATA = {}  # Empty dict as default
DEFAULT_ASSISTANT_TEMPERATURE = 1  # Default as per documentation
DEFAULT_ASSISTANT_TOP_P = 1  # Default as per documentation

# Thread specific constants
MAX_THREAD_METADATA_PAIRS = 16
MAX_THREAD_METADATA_KEY_LENGTH = 64
MAX_THREAD_METADATA_VALUE_LENGTH = 512
MAX_THREAD_CODE_INTERPRETER_FILES = 20
MAX_THREAD_FILE_SEARCH_STORES = 1

# Thread error messages
ERROR_INVALID_THREAD_METADATA_PAIRS = f"Thread can have maximum {MAX_THREAD_METADATA_PAIRS} metadata pairs"
ERROR_INVALID_THREAD_METADATA_KEY_LENGTH = f"Thread metadata keys must not exceed {MAX_THREAD_METADATA_KEY_LENGTH} characters"
ERROR_INVALID_THREAD_METADATA_VALUE_LENGTH = f"Thread metadata values must not exceed {MAX_THREAD_METADATA_VALUE_LENGTH} characters"
ERROR_INVALID_THREAD_CODE_INTERPRETER_FILES = f"Thread can have maximum {MAX_THREAD_CODE_INTERPRETER_FILES} files for code interpreter"
ERROR_INVALID_THREAD_FILE_SEARCH_STORES = f"Thread can have maximum {MAX_THREAD_FILE_SEARCH_STORES} vector store"

# Thread tool resource types
THREAD_TOOL_TYPE_CODE_INTERPRETER = "code_interpreter"
THREAD_TOOL_TYPE_FILE_SEARCH = "file_search"

# Thread object fields
THREAD_FIELD_ID = "id"
THREAD_FIELD_OBJECT = "thread"
THREAD_FIELD_CREATED_AT = "created_at"
THREAD_FIELD_METADATA = "metadata"

# Thread default values
DEFAULT_THREAD_MESSAGES = []  # Empty list as default
DEFAULT_THREAD_METADATA = {}  # Empty dict as default
DEFAULT_THREAD_TOOL_RESOURCES = {
    TOOL_TYPE_CODE_INTERPRETER: {PARAM_FILE_IDS: []},
    TOOL_TYPE_FILE_SEARCH: {
        PARAM_VECTOR_STORE_IDS: [],
        PARAM_VECTOR_STORES: []
    }
}
