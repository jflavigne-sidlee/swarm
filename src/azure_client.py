from enum import Enum
from openai import AzureOpenAI, AssistantEventHandler
from typing import Optional, List, Dict, Any, TypedDict, Union
from .azure_client_constants import (
    VECTOR_STORES_API_PATH,
    THREADS_API_PATH,
    ASSISTANTS_API_PATH,
    DEFAULT_LIST_LIMIT,
    DEFAULT_LIST_ORDER,
    ERROR_VECTOR_STORE_NOT_FOUND,
    ERROR_THREAD_NOT_FOUND,
    ERROR_ASSISTANT_NOT_FOUND,
    MESSAGE_ROLE_USER,
    MESSAGE_ROLE_ASSISTANT,
    TRUNCATION_TYPE_AUTO,
    TRUNCATION_TYPE_LAST_MESSAGES,
    RUN_STATUS_QUEUED,
    RUN_STATUS_IN_PROGRESS,
    RUN_STATUS_REQUIRES_ACTION,
    RUN_STATUS_CANCELLING,
    RUN_STATUS_CANCELLED,
    RUN_STATUS_FAILED,
    RUN_STATUS_COMPLETED,
    RUN_STATUS_EXPIRED,
    API_VERSION_BETA,
    TOOL_TYPE_CODE_INTERPRETER,
    TOOL_TYPE_FILE_SEARCH,
    TOOL_TYPE_FUNCTION,
    ORDER_ASC,
    ORDER_DESC,
    PARAM_FILE_IDS,
    PARAM_VECTOR_STORE_IDS,
    PARAM_MESSAGES,
    PARAM_PARALLEL_TOOL_CALLS,
    PARAM_RUN_ID,
    DEFAULT_PARALLEL_TOOL_CALLS,
    RESPONSE_FORMAT_TYPE,
    RESPONSE_FORMAT_LAST_MESSAGES,
    API_PATH_BETA,
    PARAM_NAME,
    PARAM_THREAD_ID,
    PARAM_ROLE,
    PARAM_CONTENT,
    PARAM_MODEL,
    PARAM_ATTACHMENTS,
    PARAM_STREAM,
    PARAM_ASSISTANT_ID,
    ERROR_INVALID_THREAD_ID,
    ERROR_INVALID_MESSAGE_ID,
    ERROR_INVALID_ASSISTANT_ID,
    ERROR_INVALID_RUN_ID,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
    DEFAULT_N,
    DEFAULT_TOOL_RESOURCES,
    CHAT_PARAM_N,
    CHAT_PARAM_STOP,
    CHAT_PARAM_MAX_TOKENS,
    CHAT_PARAM_PRESENCE_PENALTY,
    CHAT_PARAM_FREQUENCY_PENALTY,
    CHAT_PARAM_LOGIT_BIAS,
    CHAT_PARAM_USER,
    CHAT_PARAM_SEED,
    CHAT_PARAM_TOOL_CHOICE,
    CHAT_PARAM_STREAM,
    CHAT_PARAM_RESPONSE_FORMAT,
    RUN_PARAM_ADDITIONAL_INSTRUCTIONS,
    RUN_PARAM_ADDITIONAL_MESSAGES,
    RUN_PARAM_MAX_PROMPT_TOKENS,
    RUN_PARAM_MAX_COMPLETION_TOKENS,
    RUN_PARAM_TRUNCATION_STRATEGY,
    TOOL_CHOICE_AUTO,
    TOOL_CHOICE_NONE,
    PARAM_LIMIT,
    PARAM_ORDER,
    PARAM_AFTER,
    PARAM_BEFORE,
    PARAM_EXPIRES_AFTER,
    PARAM_FILES,
    TOOL_RESOURCE_CODE_INTERPRETER,
    TOOL_RESOURCE_FILE_SEARCH,
    FIELD_ID,
    DEFAULT_MAX_METADATA_PAIRS,
    MAX_METADATA_KEY_LENGTH,
    MAX_METADATA_VALUE_LENGTH,
    MAX_CODE_INTERPRETER_FILES,
    MAX_FILE_SEARCH_VECTORS,
    LIST_LIMIT_RANGE,
    PARAM_TOOLS,
    CHAT_PARAM_TEMPERATURE,
    DEFAULT_INSTRUCTIONS,
    DEFAULT_ADDITIONAL_INSTRUCTIONS,
    DEFAULT_ADDITIONAL_MESSAGES,
    DEFAULT_TRUNCATION_STRATEGY,
    DEFAULT_TOOL_CHOICE,
    DEFAULT_METADATA,
    DEFAULT_STREAM,
    DEFAULT_MAX_PROMPT_TOKENS,
    DEFAULT_MAX_COMPLETION_TOKENS,
    DEFAULT_PRESENCE_PENALTY,
    DEFAULT_FREQUENCY_PENALTY,
    DEFAULT_LOGIT_BIAS,
    DEFAULT_SEED,
    DEFAULT_USER,
    DEFAULT_STOP,
    DEFAULT_VECTOR_STORE_NAME,
    DEFAULT_EXPIRES_AFTER,
    DEFAULT_ASSISTANT_NAME,
    DEFAULT_ASSISTANT_DESCRIPTION,
    DEFAULT_ASSISTANT_TOOLS,
    DEFAULT_RESPONSE_FORMAT,
    DEFAULT_THREAD_MESSAGES,
    DEFAULT_THREAD_METADATA,
    DEFAULT_THREAD_TOOL_RESOURCES,
    DEFAULT_MESSAGE_ATTACHMENTS,
    DEFAULT_MESSAGE_METADATA,
    DEFAULT_RUN_MODEL,
    DEFAULT_RUN_TOOLS,
    DEFAULT_RUN_RESPONSE_FORMAT,
    DEFAULT_STEP_LIMIT,
    DEFAULT_STEP_ORDER,
    DEFAULT_STEP_AFTER,
    DEFAULT_STEP_BEFORE,
    DEFAULT_TOOL_OUTPUTS,
    DEFAULT_TOOL_OUTPUT_STREAM,
    DEFAULT_API_VERSION,
    BETA_VECTOR_STORES_PATH,
    BETA_THREADS_PATH,
    BETA_ASSISTANTS_PATH,
    BETA_MESSAGES_PATH,
    BETA_RUNS_PATH,
    BETA_STEPS_PATH,
    DEFAULT_FILE_BATCH_SIZE,
    MAX_FILE_SIZE,
    ALLOWED_FILE_TYPES,
    DEFAULT_MESSAGE_LIMIT,
    DEFAULT_MESSAGE_ORDER,
    DEFAULT_MESSAGE_AFTER,
    DEFAULT_MESSAGE_BEFORE,
    DEFAULT_ASSISTANT_LIMIT,
    DEFAULT_ASSISTANT_ORDER,
    DEFAULT_ASSISTANT_AFTER,
    DEFAULT_ASSISTANT_BEFORE,
    DEFAULT_VECTOR_STORE_LIMIT,
    DEFAULT_VECTOR_STORE_ORDER,
    DEFAULT_VECTOR_STORE_AFTER,
    DEFAULT_VECTOR_STORE_BEFORE,
    VALID_TEMPERATURE_RANGE,
    VALID_TOP_P_RANGE,
    VALID_PRESENCE_PENALTY_RANGE,
    VALID_FREQUENCY_PENALTY_RANGE,
    ERROR_INVALID_TEMPERATURE,
    ERROR_INVALID_TOP_P,
    ERROR_INVALID_PRESENCE_PENALTY,
    ERROR_INVALID_FREQUENCY_PENALTY,
    ERROR_INVALID_MAX_TOKENS,
    ERROR_INVALID_N,
    ERROR_INVALID_LIMIT,
    API_PATH_CHAT_COMPLETIONS,
    API_PATH_VECTOR_STORES,
    API_PATH_THREADS,
    API_PATH_ASSISTANTS,
    DEFAULT_ASSISTANT_LIST_PARAMS,
    DEFAULT_MESSAGE_LIST_PARAMS,
    LIST_PARAM_LIMIT,
    LIST_PARAM_ORDER,
    LIST_PARAM_AFTER,
    LIST_PARAM_BEFORE,
    DEFAULT_RUN_STEP_LIST_PARAMS,
    DEFAULT_RUN_LIST_PARAMS,
    DEFAULT_VECTOR_STORE_LIST_PARAMS,
    PARAM_METADATA,
    PARAM_TOOL_RESOURCES,
    PARAM_RUN_ID,
    DEFAULT_RUN_LIMIT,
    DEFAULT_RUN_ORDER,
    DEFAULT_RUN_AFTER,
    DEFAULT_RUN_BEFORE,
    DEFAULT_PARAMS,
    DEFAULT_THREAD_LIMIT,
    DEFAULT_THREAD_ORDER,
    DEFAULT_THREAD_AFTER,
    DEFAULT_THREAD_BEFORE,
    MAX_ASSISTANT_NAME_LENGTH,
    MAX_ASSISTANT_DESCRIPTION_LENGTH,
    MAX_ASSISTANT_INSTRUCTIONS_LENGTH,
    MAX_ASSISTANT_TOOLS_COUNT,
    VALID_TEMPERATURE_RANGE,
    VALID_TOP_P_RANGE,
    ERROR_INVALID_ASSISTANT_NAME_LENGTH,
    ERROR_INVALID_ASSISTANT_DESCRIPTION_LENGTH,
    ERROR_INVALID_ASSISTANT_INSTRUCTIONS_LENGTH,
    ERROR_INVALID_ASSISTANT_TOOLS_COUNT,
    ERROR_INVALID_TEMPERATURE,
    ERROR_INVALID_TOP_P,
    DEFAULT_ASSISTANT_TEMPERATURE,
    DEFAULT_ASSISTANT_TOP_P,
    MAX_THREAD_METADATA_PAIRS,
    MAX_THREAD_METADATA_KEY_LENGTH,
    MAX_THREAD_METADATA_VALUE_LENGTH,
    MAX_THREAD_CODE_INTERPRETER_FILES,
    MAX_THREAD_FILE_SEARCH_STORES,
    ERROR_INVALID_THREAD_METADATA_PAIRS,
    ERROR_INVALID_THREAD_METADATA_KEY_LENGTH,
    ERROR_INVALID_THREAD_METADATA_VALUE_LENGTH,
    ERROR_INVALID_THREAD_CODE_INTERPRETER_FILES,
    ERROR_INVALID_THREAD_FILE_SEARCH_STORES,
    THREAD_TOOL_TYPE_CODE_INTERPRETER,
    THREAD_TOOL_TYPE_FILE_SEARCH,
    THREAD_FIELD_ID,
    THREAD_FIELD_OBJECT,
    THREAD_FIELD_CREATED_AT,
    THREAD_FIELD_METADATA,
    DEFAULT_THREAD_MESSAGES,
    DEFAULT_THREAD_METADATA,
    DEFAULT_THREAD_TOOL_RESOURCES,
)


class OrderDirection(str, Enum):
    """Sort order for list operations"""

    ASC = ORDER_ASC
    DESC = ORDER_DESC


class MessageRole(str, Enum):
    """Available roles for messages"""

    USER = MESSAGE_ROLE_USER
    ASSISTANT = MESSAGE_ROLE_ASSISTANT


class TruncationType(str, Enum):
    """Available truncation types"""

    AUTO = TRUNCATION_TYPE_AUTO
    LAST_MESSAGES = TRUNCATION_TYPE_LAST_MESSAGES


class ToolType(str, Enum):
    """Available tool types"""

    CODE_INTERPRETER = TOOL_TYPE_CODE_INTERPRETER
    FILE_SEARCH = TOOL_TYPE_FILE_SEARCH
    FUNCTION = TOOL_TYPE_FUNCTION


class RunStatus(str, Enum):
    """Available run statuses"""

    QUEUED = RUN_STATUS_QUEUED
    IN_PROGRESS = RUN_STATUS_IN_PROGRESS
    REQUIRES_ACTION = RUN_STATUS_REQUIRES_ACTION
    CANCELLING = RUN_STATUS_CANCELLING
    CANCELLED = RUN_STATUS_CANCELLED
    FAILED = RUN_STATUS_FAILED
    COMPLETED = RUN_STATUS_COMPLETED
    EXPIRED = RUN_STATUS_EXPIRED


class Defaults:
    """Default values for API parameters"""

    LIST_LIMIT = DEFAULT_LIST_LIMIT
    LIST_ORDER = DEFAULT_LIST_ORDER
    MAX_METADATA_PAIRS = DEFAULT_MAX_METADATA_PAIRS
    MAX_METADATA_KEY_LENGTH = MAX_METADATA_KEY_LENGTH
    MAX_METADATA_VALUE_LENGTH = MAX_METADATA_VALUE_LENGTH
    MAX_CODE_INTERPRETER_FILES = MAX_CODE_INTERPRETER_FILES
    MAX_FILE_SEARCH_VECTORS = MAX_FILE_SEARCH_VECTORS
    LIST_LIMIT_RANGE = LIST_LIMIT_RANGE  # 1-100


class ToolResources(TypedDict, total=False):
    code_interpreter: Dict[str, List[str]]
    file_search: Dict[str, List[str]]


class TruncationStrategy(TypedDict):
    type: str  # TruncationType
    last_messages: Optional[int]


class VectorStores:
    """Vector stores operations"""

    def __init__(self, client: AzureOpenAI):
        self._client = client
        self.file_batches = self.FileBatches(client)

    def create(self, name: str, expires_after: dict) -> Any:
        """Creates a vector store"""
        return self._client.beta.vector_stores.create(
            name=name, expires_after=expires_after
        )

    def retrieve(self, vector_store_id: str) -> Any:
        """Retrieves a vector store by ID"""
        if not vector_store_id:
            raise ValueError(ERROR_VECTOR_STORE_NOT_FOUND)
        return self._client.beta.vector_stores.retrieve(vector_store_id)

    def list(self, **kwargs) -> Any:
        """Lists vector stores"""
        return self._client.beta.vector_stores.list(**kwargs)

    def delete(self, vector_store_id: str) -> Any:
        """Deletes a vector store"""
        return self._client.beta.vector_stores.delete(vector_store_id)

    class FileBatches:
        """File batch operations for vector stores"""

        def __init__(self, client: AzureOpenAI):
            self._client = client

        def upload_and_poll(self, vector_store_id: str, files: list) -> Any:
            """Uploads a batch of files to vector store"""
            return self._client.beta.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vector_store_id, files=files
            )


class Messages:
    """Message operations"""

    def __init__(self, client: AzureOpenAI):
        self._client = client

    def create(self, thread_id: str, role: MessageRole, content: str, **kwargs) -> Any:
        """Creates a message in a thread"""
        return self._client.beta.threads.messages.create(
            thread_id=thread_id, role=role, content=content, **kwargs
        )

    def list(
        self,
        thread_id: str,
        limit: Optional[int] = DEFAULT_MESSAGE_LIMIT,
        order: Optional[str] = DEFAULT_MESSAGE_ORDER,
        after: Optional[str] = DEFAULT_MESSAGE_AFTER,
        before: Optional[str] = DEFAULT_MESSAGE_BEFORE,
    ) -> Any:
        """Lists messages in a thread"""
        if limit and limit not in LIST_LIMIT_RANGE:
            raise ValueError(ERROR_INVALID_LIMIT)

        return self._client.beta.threads.messages.list(
            thread_id=thread_id, limit=limit, order=order, after=after, before=before
        )

    def retrieve(self, thread_id: str, message_id: str) -> Any:
        """Retrieves a message"""
        return self._client.beta.threads.messages.retrieve(
            thread_id=thread_id, message_id=message_id
        )

    def update(self, thread_id: str, message_id: str, **kwargs) -> Any:
        """Updates a message"""
        return self._client.beta.threads.messages.update(
            thread_id=thread_id, message_id=message_id, **kwargs
        )

    def delete(self, thread_id: str, message_id: str) -> Any:
        """Deletes a message"""
        return self._client.beta.threads.messages.delete(
            thread_id=thread_id, message_id=message_id
        )


class RunSteps:
    """Run steps operations"""

    def __init__(self, client: AzureOpenAI):
        self._client = client

    def list(self, thread_id: str, run_id: str, **kwargs) -> Any:
        """Lists steps in a run"""
        return self._client.beta.threads.runs.steps.list(
            thread_id=thread_id, run_id=run_id, **kwargs
        )

    def retrieve(self, thread_id: str, run_id: str, step_id: str) -> Any:
        """Retrieves a run step"""
        return self._client.beta.threads.runs.steps.retrieve(
            thread_id=thread_id, run_id=run_id, step_id=step_id
        )


class Runs:
    """Run operations"""

    def __init__(self, client: AzureOpenAI):
        self._client = client
        self.steps = RunSteps(client)

    def create(self, thread_id: str, assistant_id: str, **kwargs) -> Any:
        """Creates a run"""
        default_params = DEFAULT_PARAMS["run"].copy()
        default_params.update(kwargs)

        return self._client.beta.threads.runs.create(
            thread_id=thread_id, assistant_id=assistant_id, **default_params
        )

    def list(
        self,
        thread_id: str,
        limit: Optional[int] = DEFAULT_RUN_LIMIT,
        order: Optional[str] = DEFAULT_RUN_ORDER,
        after: Optional[str] = DEFAULT_RUN_AFTER,
        before: Optional[str] = DEFAULT_RUN_BEFORE,
    ) -> Any:
        """Lists runs in a thread"""
        if limit and limit not in LIST_LIMIT_RANGE:
            raise ValueError(ERROR_INVALID_LIMIT)

        return self._client.beta.threads.runs.list(
            thread_id=thread_id, limit=limit, order=order, after=after, before=before
        )

    def retrieve(self, thread_id: str, run_id: str) -> Any:
        """Retrieves a run"""
        if not thread_id:
            raise ValueError(ERROR_INVALID_THREAD_ID)
        if not run_id:
            raise ValueError(ERROR_INVALID_RUN_ID)

        return self._client.beta.threads.runs.retrieve(
            thread_id=thread_id, run_id=run_id
        )

    def update(
        self, thread_id: str, run_id: str, metadata: Optional[Dict[str, str]] = None
    ) -> Any:
        """Updates a run"""
        if not thread_id:
            raise ValueError(ERROR_INVALID_THREAD_ID)
        if not run_id:
            raise ValueError(ERROR_INVALID_RUN_ID)

        return self._client.beta.threads.runs.update(
            thread_id=thread_id, run_id=run_id, metadata=metadata
        )

    def submit_tool_outputs(
        self,
        thread_id: str,
        run_id: str,
        tool_outputs: List[Dict[str, Any]],
        stream: Optional[bool] = DEFAULT_STREAM,
    ) -> Any:
        """Submits tool outputs"""
        if not thread_id:
            raise ValueError(ERROR_INVALID_THREAD_ID)
        if not run_id:
            raise ValueError(ERROR_INVALID_RUN_ID)

        return self._client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread_id, run_id=run_id, tool_outputs=tool_outputs, stream=stream
        )

    def cancel(self, thread_id: str, run_id: str) -> Any:
        """Cancels a run"""
        if not thread_id:
            raise ValueError(ERROR_INVALID_THREAD_ID)
        if not run_id:
            raise ValueError(ERROR_INVALID_RUN_ID)

        return self._client.beta.threads.runs.cancel(thread_id=thread_id, run_id=run_id)

    def stream(
        self,
        thread_id: str,
        assistant_id: str,
        event_handler: AssistantEventHandler,
        **run_params
    ) -> Any:
        """Stream the result of executing a Run."""
        if not thread_id:
            raise ValueError(ERROR_INVALID_THREAD_ID)
        if not assistant_id:
            raise ValueError(ERROR_INVALID_ASSISTANT_ID)

        # Remove run_id from run_params if present as it's not needed
        run_params.pop(PARAM_RUN_ID, None)

        # Apply default run parameters
        default_params = DEFAULT_PARAMS["run"].copy()
        default_params.update(run_params)

        return self._client.beta.threads.runs.stream(
            thread_id=thread_id,
            assistant_id=assistant_id,
            event_handler=event_handler,
            **default_params
        )

    def create_thread_and_run(
        self, assistant_id: str, thread: Dict[str, Any], **run_params
    ) -> Any:
        """Creates a thread and run in one operation."""
        if not assistant_id:
            raise ValueError(ERROR_INVALID_ASSISTANT_ID)

        # Create thread parameters, only including messages
        thread_params = {
            PARAM_MESSAGES: thread.get(PARAM_MESSAGES, DEFAULT_THREAD_MESSAGES)
        }

        # Apply default run parameters
        default_run_params = DEFAULT_PARAMS["run"].copy()
        default_run_params.update(run_params)

        return self._client.beta.threads.create_and_run(
            assistant_id=assistant_id,
            thread=thread_params,  # Pass as a nested thread parameter
            **default_run_params
        )


class Threads:
    """Thread operations"""

    def __init__(self, client: AzureOpenAI):
        self._client = client
        self.messages = Messages(client)
        self.runs = Runs(client)

    def create(self, **kwargs) -> Any:
        """Creates a thread"""
        default_params = DEFAULT_PARAMS["thread"].copy()
        default_params.update(kwargs)
        return self._client.beta.threads.create(**default_params)

    def retrieve(self, thread_id: str) -> Any:
        """Retrieves a thread"""
        return self._client.beta.threads.retrieve(thread_id)

    def update(self, thread_id: str, **kwargs) -> Any:
        """Updates a thread"""
        return self._client.beta.threads.update(thread_id, **kwargs)

    def delete(self, thread_id: str) -> Any:
        """Deletes a thread"""
        return self._client.beta.threads.delete(thread_id)

    def list(
        self,
        limit: Optional[int] = DEFAULT_THREAD_LIMIT,
        order: Optional[str] = DEFAULT_THREAD_ORDER,
        after: Optional[str] = DEFAULT_THREAD_AFTER,
        before: Optional[str] = DEFAULT_THREAD_BEFORE,
    ) -> Any:
        """Lists threads"""
        if limit and limit not in LIST_LIMIT_RANGE:
            raise ValueError(ERROR_INVALID_LIMIT)

        return self._client.beta.threads.list(
            limit=limit, order=order, after=after, before=before
        )


class Assistants:
    """Assistant operations"""

    def __init__(self, client: AzureOpenAI):
        self._client = client

    def create(self, model: str, **kwargs) -> Any:
        """Creates an assistant"""
        return self._client.beta.assistants.create(model=model, **kwargs)

    def list(self, **kwargs) -> Any:
        """Lists assistants"""
        return self._client.beta.assistants.list(**kwargs)

    def retrieve(self, assistant_id: str) -> Any:
        """Retrieves an assistant"""
        return self._client.beta.assistants.retrieve(assistant_id)

    def update(self, assistant_id: str, **kwargs) -> Any:
        """Updates an assistant"""
        return self._client.beta.assistants.update(assistant_id, **kwargs)

    def delete(self, assistant_id: str) -> Any:
        """Deletes an assistant"""
        return self._client.beta.assistants.delete(assistant_id)


class Chat:
    """Chat operations"""

    def __init__(self, client: AzureOpenAI):
        self._client = client
        self.completions = self.Completions(client)

    class Completions:
        """Chat completion operations"""

        def __init__(self, client: AzureOpenAI):
            self._client = client

        def create(
            self,
            model: str,
            messages: List[Dict[str, Any]],
            tools: Optional[List[Dict[str, Any]]] = None,
            tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
            temperature: Optional[float] = DEFAULT_TEMPERATURE,
            top_p: Optional[float] = DEFAULT_TOP_P,
            n: Optional[int] = DEFAULT_N,
            stream: Optional[bool] = None,
            stop: Optional[Union[str, List[str]]] = None,
            max_tokens: Optional[int] = None,
            presence_penalty: Optional[float] = None,
            frequency_penalty: Optional[float] = None,
            logit_bias: Optional[Dict[str, float]] = None,
            user: Optional[str] = None,
            response_format: Optional[Dict[str, str]] = None,
            seed: Optional[int] = None,
            parallel_tool_calls: Optional[bool] = DEFAULT_PARALLEL_TOOL_CALLS,
        ) -> Any:
            """Creates a chat completion."""
            params = {
                PARAM_MODEL: model,
                PARAM_MESSAGES: messages,
                PARAM_TOOLS: tools,
                CHAT_PARAM_TOOL_CHOICE: tool_choice,
                CHAT_PARAM_TEMPERATURE: temperature,
                CHAT_PARAM_N: n,
                CHAT_PARAM_STREAM: stream,
                CHAT_PARAM_STOP: stop,
                CHAT_PARAM_MAX_TOKENS: max_tokens,
                CHAT_PARAM_PRESENCE_PENALTY: presence_penalty,
                CHAT_PARAM_FREQUENCY_PENALTY: frequency_penalty,
                CHAT_PARAM_LOGIT_BIAS: logit_bias,
                CHAT_PARAM_USER: user,
                CHAT_PARAM_RESPONSE_FORMAT: response_format,
                CHAT_PARAM_SEED: seed,
            }

            # Only include parallel_tool_calls if tools are present
            if tools:
                params["parallel_tool_calls"] = parallel_tool_calls

            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}

            return self._client.chat.completions.create(**params)


class AzureClientWrapper:
    """Wrapper for Azure OpenAI client to abstract API version specifics"""

    @classmethod
    def create(
        cls, api_key: str, api_version: str, azure_endpoint: str
    ) -> "AzureClientWrapper":
        """Factory method to create a wrapped client with the given credentials"""
        client = AzureOpenAI(
            api_key=api_key, api_version=api_version, azure_endpoint=azure_endpoint
        )
        return cls(client)

    def __init__(self, client: AzureOpenAI):
        """Initialize the wrapper with component classes"""
        self._client = client
        self.vector_stores = VectorStores(client)
        self.assistants = Assistants(client)
        self.threads = Threads(client)
        self.chat = Chat(client)

    @property
    def client(self) -> AzureOpenAI:
        """Access to underlying client if needed"""
        return self._client

    def create_assistant(
        self,
        model: str,
        name: Optional[str] = DEFAULT_ASSISTANT_NAME,
        description: Optional[str] = DEFAULT_ASSISTANT_DESCRIPTION,
        instructions: Optional[str] = DEFAULT_INSTRUCTIONS,
        tools: Optional[List[Dict[str, Any]]] = DEFAULT_ASSISTANT_TOOLS,
        metadata: Optional[Dict[str, str]] = DEFAULT_METADATA,
        temperature: Optional[float] = DEFAULT_ASSISTANT_TEMPERATURE,
        top_p: Optional[float] = DEFAULT_ASSISTANT_TOP_P,
        response_format: Optional[Dict[str, str]] = DEFAULT_RESPONSE_FORMAT,
        tool_resources: Optional[Dict[str, Any]] = DEFAULT_TOOL_RESOURCES,
    ) -> Any:
        """Creates an assistant with specified configuration"""
        # Validate name length
        if name and len(name) > MAX_ASSISTANT_NAME_LENGTH:
            raise ValueError(ERROR_INVALID_ASSISTANT_NAME_LENGTH)

        # Validate description length
        if description and len(description) > MAX_ASSISTANT_DESCRIPTION_LENGTH:
            raise ValueError(ERROR_INVALID_ASSISTANT_DESCRIPTION_LENGTH)

        # Validate instructions length
        if instructions and len(instructions) > MAX_ASSISTANT_INSTRUCTIONS_LENGTH:
            raise ValueError(ERROR_INVALID_ASSISTANT_INSTRUCTIONS_LENGTH)

        # Validate tools count
        if tools and len(tools) > MAX_ASSISTANT_TOOLS_COUNT:
            raise ValueError(ERROR_INVALID_ASSISTANT_TOOLS_COUNT)

        # Validate temperature range
        if (
            temperature is not None
            and not VALID_TEMPERATURE_RANGE[0]
            <= temperature
            <= VALID_TEMPERATURE_RANGE[1]
        ):
            raise ValueError(ERROR_INVALID_TEMPERATURE)

        # Validate top_p range
        if (
            top_p is not None
            and not VALID_TOP_P_RANGE[0] <= top_p <= VALID_TOP_P_RANGE[1]
        ):
            raise ValueError(ERROR_INVALID_TOP_P)

        return self._client.beta.assistants.create(
            model=model,
            name=name,
            description=description,
            instructions=instructions,
            tools=tools,
            metadata=metadata,
            temperature=temperature,
            top_p=top_p,
            response_format=response_format,
            tool_resources=tool_resources,
        )

    def list_assistants(
        self,
        limit: Optional[int] = DEFAULT_ASSISTANT_LIST_PARAMS[LIST_PARAM_LIMIT],
        order: Optional[str] = DEFAULT_ASSISTANT_LIST_PARAMS[LIST_PARAM_ORDER],
        after: Optional[str] = DEFAULT_ASSISTANT_LIST_PARAMS[LIST_PARAM_AFTER],
        before: Optional[str] = DEFAULT_ASSISTANT_LIST_PARAMS[LIST_PARAM_BEFORE],
    ) -> Any:
        """Returns a list of assistants"""
        if limit and limit not in LIST_LIMIT_RANGE:
            raise ValueError(ERROR_INVALID_LIMIT)

        return self._client.beta.assistants.list(
            limit=limit, order=order, after=after, before=before
        )

    def retrieve_assistant(self, assistant_id: str) -> Any:
        """Retrieves an assistant by ID"""
        return self._client.beta.assistants.retrieve(assistant_id)

    def update_assistant(
        self,
        assistant_id: str,
        model: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        instructions: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, str]] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        response_format: Optional[Dict[str, str]] = None,
        tool_resources: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Updates an existing assistant with validation"""
        if not assistant_id:
            raise ValueError(ERROR_INVALID_ASSISTANT_ID)

        # Validate name length
        if name and len(name) > MAX_ASSISTANT_NAME_LENGTH:
            raise ValueError(ERROR_INVALID_ASSISTANT_NAME_LENGTH)

        # Validate description length
        if description and len(description) > MAX_ASSISTANT_DESCRIPTION_LENGTH:
            raise ValueError(ERROR_INVALID_ASSISTANT_DESCRIPTION_LENGTH)

        # Validate instructions length
        if instructions and len(instructions) > MAX_ASSISTANT_INSTRUCTIONS_LENGTH:
            raise ValueError(ERROR_INVALID_ASSISTANT_INSTRUCTIONS_LENGTH)

        # Validate tools count
        if tools and len(tools) > MAX_ASSISTANT_TOOLS_COUNT:
            raise ValueError(ERROR_INVALID_ASSISTANT_TOOLS_COUNT)

        # Validate temperature range
        if (
            temperature is not None
            and not VALID_TEMPERATURE_RANGE[0]
            <= temperature
            <= VALID_TEMPERATURE_RANGE[1]
        ):
            raise ValueError(ERROR_INVALID_TEMPERATURE)

        # Validate top_p range
        if (
            top_p is not None
            and not VALID_TOP_P_RANGE[0] <= top_p <= VALID_TOP_P_RANGE[1]
        ):
            raise ValueError(ERROR_INVALID_TOP_P)

        return self._client.beta.assistants.update(
            assistant_id,
            model=model,
            name=name,
            description=description,
            instructions=instructions,
            tools=tools,
            metadata=metadata,
            temperature=temperature,
            top_p=top_p,
            response_format=response_format,
            tool_resources=tool_resources,
        )

    def delete_assistant(self, assistant_id: str) -> Any:
        """Deletes an assistant"""
        return self._client.beta.assistants.delete(assistant_id)

    # Thread Operations
    def create_thread(
        self,
        messages: Optional[List[Dict[str, Any]]] = DEFAULT_THREAD_MESSAGES,
        metadata: Optional[Dict[str, str]] = DEFAULT_THREAD_METADATA,
        tool_resources: Optional[Dict[str, Any]] = DEFAULT_THREAD_TOOL_RESOURCES,
    ) -> Any:
        """Creates a thread."""
        if metadata and len(metadata) > MAX_THREAD_METADATA_PAIRS:
            raise ValueError(ERROR_INVALID_THREAD_METADATA_PAIRS)

        if metadata:
            for key, value in metadata.items():
                if len(key) > MAX_THREAD_METADATA_KEY_LENGTH:
                    raise ValueError(ERROR_INVALID_THREAD_METADATA_KEY_LENGTH)
                if len(value) > MAX_THREAD_METADATA_VALUE_LENGTH:
                    raise ValueError(ERROR_INVALID_THREAD_METADATA_VALUE_LENGTH)

        if tool_resources:
            if THREAD_TOOL_TYPE_CODE_INTERPRETER in tool_resources:
                file_ids = tool_resources[THREAD_TOOL_TYPE_CODE_INTERPRETER].get(
                    "file_ids", []
                )
                if len(file_ids) > MAX_THREAD_CODE_INTERPRETER_FILES:
                    raise ValueError(ERROR_INVALID_THREAD_CODE_INTERPRETER_FILES)

            if THREAD_TOOL_TYPE_FILE_SEARCH in tool_resources:
                vector_store_ids = tool_resources[THREAD_TOOL_TYPE_FILE_SEARCH].get(
                    "vector_store_ids", []
                )
                vector_stores = tool_resources[THREAD_TOOL_TYPE_FILE_SEARCH].get(
                    "vector_stores", []
                )
                if (
                    len(vector_store_ids) + len(vector_stores)
                    > MAX_THREAD_FILE_SEARCH_STORES
                ):
                    raise ValueError(ERROR_INVALID_THREAD_FILE_SEARCH_STORES)

        return self._client.beta.threads.create(
            messages=messages, metadata=metadata, tool_resources=tool_resources
        )

    def retrieve_thread(self, thread_id: str) -> Any:
        """Retrieves a thread by ID."""
        return self._client.beta.threads.retrieve(thread_id)

    def update_thread(
        self,
        thread_id: str,
        metadata: Optional[Dict[str, str]] = None,
        tool_resources: Optional[ToolResources] = None,
    ) -> Any:
        """Modifies an existing thread."""
        return self._client.beta.threads.update(
            thread_id, metadata=metadata, tool_resources=tool_resources
        )

    def delete_thread(self, thread_id: str) -> Any:
        """Deletes a thread."""
        return self._client.beta.threads.delete(thread_id)

    # Message Operations
    def create_message(
        self,
        thread_id: str,
        role: MessageRole,
        content: str,
        attachments: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Creates a message in a thread."""
        return self._client.beta.threads.messages.create(
            thread_id,
            role=role,
            content=content,
            attachments=attachments,
            metadata=metadata,
        )

    def list_messages(
        self,
        thread_id: str,
        limit: Optional[int] = DEFAULT_MESSAGE_LIST_PARAMS[LIST_PARAM_LIMIT],
        order: Optional[str] = DEFAULT_MESSAGE_LIST_PARAMS[LIST_PARAM_ORDER],
        after: Optional[str] = DEFAULT_MESSAGE_LIST_PARAMS[LIST_PARAM_AFTER],
        before: Optional[str] = DEFAULT_MESSAGE_LIST_PARAMS[LIST_PARAM_BEFORE],
        run_id: Optional[str] = None,
    ) -> Any:
        """Returns a list of messages for a given thread."""
        if limit and limit not in LIST_LIMIT_RANGE:
            raise ValueError(ERROR_INVALID_LIMIT)

        return self._client.beta.threads.messages.list(
            thread_id,
            limit=limit,
            order=order,
            after=after,
            before=before,
            run_id=run_id,
        )

    def retrieve_message(self, thread_id: str, message_id: str) -> Any:
        """Retrieves a specific message from a thread."""
        return self._client.beta.threads.messages.retrieve(
            message_id=message_id, thread_id=thread_id
        )

    def update_message(
        self, thread_id: str, message_id: str, metadata: Optional[Dict[str, str]] = None
    ) -> Any:
        """Modifies a message."""
        return self._client.beta.threads.messages.update(
            message_id=message_id, thread_id=thread_id, metadata=metadata
        )

    def delete_message(self, thread_id: str, message_id: str) -> Any:
        """Deletes a message."""
        return self._client.beta.threads.messages.delete(
            message_id=message_id, thread_id=thread_id
        )

    # Run Operations
    def create_run(
        self,
        thread_id: str,
        assistant_id: str,
        model: Optional[str] = DEFAULT_RUN_MODEL,
        instructions: Optional[str] = DEFAULT_INSTRUCTIONS,
        additional_instructions: Optional[str] = DEFAULT_ADDITIONAL_INSTRUCTIONS,
        additional_messages: Optional[
            List[Dict[str, Any]]
        ] = DEFAULT_ADDITIONAL_MESSAGES,
        tools: Optional[List[Dict[str, Any]]] = DEFAULT_RUN_TOOLS,
        metadata: Optional[Dict[str, str]] = DEFAULT_METADATA,
        temperature: Optional[float] = DEFAULT_TEMPERATURE,
        top_p: Optional[float] = DEFAULT_TOP_P,
        stream: Optional[bool] = DEFAULT_STREAM,
        max_prompt_tokens: Optional[int] = DEFAULT_MAX_PROMPT_TOKENS,
        max_completion_tokens: Optional[int] = DEFAULT_MAX_COMPLETION_TOKENS,
        truncation_strategy: Optional[TruncationStrategy] = DEFAULT_TRUNCATION_STRATEGY,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = DEFAULT_TOOL_CHOICE,
        response_format: Optional[Dict[str, str]] = DEFAULT_RUN_RESPONSE_FORMAT,
    ) -> Any:
        """Creates a run for a thread."""
        if (
            temperature is not None
            and not VALID_TEMPERATURE_RANGE[0]
            <= temperature
            <= VALID_TEMPERATURE_RANGE[1]
        ):
            raise ValueError(ERROR_INVALID_TEMPERATURE)
        if (
            top_p is not None
            and not VALID_TOP_P_RANGE[0] <= top_p <= VALID_TOP_P_RANGE[1]
        ):
            raise ValueError(ERROR_INVALID_TOP_P)

        return self._client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
            model=model,
            instructions=instructions,
            additional_instructions=additional_instructions,
            additional_messages=additional_messages,
            tools=tools,
            metadata=metadata,
            temperature=temperature,
            top_p=top_p,
            stream=stream,
            max_prompt_tokens=max_prompt_tokens,
            max_completion_tokens=max_completion_tokens,
            truncation_strategy=truncation_strategy,
            tool_choice=tool_choice,
            response_format=response_format,
        )

    def create_thread_and_run(
        self,
        assistant_id: str,
        thread: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        instructions: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, str]] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        stream: Optional[bool] = None,
        max_prompt_tokens: Optional[int] = None,
        max_completion_tokens: Optional[int] = None,
        truncation_strategy: Optional[TruncationStrategy] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Creates a thread and run in a single request."""
        return self._client.beta.threads.create_and_run(
            assistant_id=assistant_id,
            thread=thread,
            model=model,
            instructions=instructions,
            tools=tools,
            metadata=metadata,
            temperature=temperature,
            top_p=top_p,
            stream=stream,
            max_prompt_tokens=max_prompt_tokens,
            max_completion_tokens=max_completion_tokens,
            truncation_strategy=truncation_strategy,
            tool_choice=tool_choice,
            response_format=response_format,
        )

    def list_runs(
        self,
        thread_id: str,
        limit: Optional[int] = DEFAULT_RUN_LIST_PARAMS[LIST_PARAM_LIMIT],
        order: Optional[str] = DEFAULT_RUN_LIST_PARAMS[LIST_PARAM_ORDER],
        after: Optional[str] = DEFAULT_RUN_LIST_PARAMS[LIST_PARAM_AFTER],
        before: Optional[str] = DEFAULT_RUN_LIST_PARAMS[LIST_PARAM_BEFORE],
    ) -> Any:
        """Returns a list of runs belonging to a thread."""
        if limit and limit not in LIST_LIMIT_RANGE:
            raise ValueError(ERROR_INVALID_LIMIT)

        return self._client.beta.threads.runs.list(
            thread_id=thread_id, limit=limit, order=order, after=after, before=before
        )

    def list_run_steps(
        self,
        thread_id: str,
        run_id: str,
        limit: Optional[int] = DEFAULT_RUN_STEP_LIST_PARAMS[LIST_PARAM_LIMIT],
        order: Optional[str] = DEFAULT_RUN_STEP_LIST_PARAMS[LIST_PARAM_ORDER],
        after: Optional[str] = DEFAULT_RUN_STEP_LIST_PARAMS[LIST_PARAM_AFTER],
        before: Optional[str] = DEFAULT_RUN_STEP_LIST_PARAMS[LIST_PARAM_BEFORE],
    ) -> Any:
        """Returns a list of run steps belonging to a run."""
        if limit and limit not in LIST_LIMIT_RANGE:
            raise ValueError(ERROR_INVALID_LIMIT)

        return self._client.beta.threads.runs.steps.list(
            thread_id=thread_id,
            run_id=run_id,
            limit=limit,
            order=order,
            after=after,
            before=before,
        )

    def retrieve_run(self, thread_id: str, run_id: str) -> Any:
        """Retrieves a run."""
        return self._client.beta.threads.runs.retrieve(
            thread_id=thread_id, run_id=run_id
        )

    def retrieve_run_step(self, thread_id: str, run_id: str, step_id: str) -> Any:
        """Retrieves a run step."""
        return self._client.beta.threads.runs.steps.retrieve(
            thread_id=thread_id, run_id=run_id, step_id=step_id
        )

    def update_run(self, thread_id: str, run_id: str, metadata: Dict[str, str]) -> Any:
        """Modifies a run."""
        return self._client.beta.threads.runs.update(
            thread_id=thread_id, run_id=run_id, metadata=metadata
        )

    def submit_tool_outputs(
        self,
        thread_id: str,
        run_id: str,
        tool_outputs: List[Dict[str, Any]],
        stream: Optional[bool] = None,
    ) -> Any:
        """Submits outputs for tool calls."""
        return self._client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread_id, run_id=run_id, tool_outputs=tool_outputs, stream=stream
        )

    def cancel_run(self, thread_id: str, run_id: str) -> Any:
        """Cancels a run that is in_progress."""
        return self._client.beta.threads.runs.cancel(thread_id=thread_id, run_id=run_id)

    def create_vector_store(self, name: str, expires_after: dict) -> Any:
        """Creates a vector store"""
        return self.vector_stores.create(name=name, expires_after=expires_after)

    def retrieve_vector_store(self, vector_store_id: str) -> Any:
        """Retrieves a vector store by ID"""
        return self.vector_stores.retrieve(vector_store_id)

    def upload_files_to_vector_store(self, vector_store_id: str, files: list) -> Any:
        """Uploads files to a vector store"""
        return self.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store_id, files=files
        )

    def list_vector_stores(
        self,
        limit: Optional[int] = DEFAULT_VECTOR_STORE_LIST_PARAMS[LIST_PARAM_LIMIT],
        order: Optional[str] = DEFAULT_VECTOR_STORE_LIST_PARAMS[LIST_PARAM_ORDER],
        after: Optional[str] = DEFAULT_VECTOR_STORE_LIST_PARAMS[LIST_PARAM_AFTER],
        before: Optional[str] = DEFAULT_VECTOR_STORE_LIST_PARAMS[LIST_PARAM_BEFORE],
    ) -> Any:
        """Lists vector stores"""
        if limit and limit not in LIST_LIMIT_RANGE:
            raise ValueError(ERROR_INVALID_LIMIT)

        return self._client.beta.vector_stores.list(
            limit=limit, order=order, after=after, before=before
        )

    def delete_vector_store(self, vector_store_id: str) -> Any:
        """Deletes a vector store"""
        return self.vector_stores.delete(vector_store_id)
