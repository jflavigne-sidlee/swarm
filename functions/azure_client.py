from enum import Enum
from openai import AzureOpenAI, AssistantEventHandler
from typing import Optional, List, Dict, Any, TypedDict, Union

class OrderDirection(str, Enum):
    """Sort order for list operations"""
    ASC = "asc"
    DESC = "desc"

class MessageRole(str, Enum):
    """Available roles for messages"""
    USER = "user"
    ASSISTANT = "assistant"

class TruncationType(str, Enum):
    """Available truncation types"""
    AUTO = "auto"
    LAST_MESSAGES = "last_messages"

class ToolType(str, Enum):
    """Available tool types"""
    CODE_INTERPRETER = "code_interpreter"
    FILE_SEARCH = "file_search"
    FUNCTION = "function"

class RunStatus(str, Enum):
    """Available run statuses"""
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    REQUIRES_ACTION = "requires_action"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"
    FAILED = "failed"
    COMPLETED = "completed"
    EXPIRED = "expired"

class Defaults:
    """Default values for API parameters"""
    LIST_LIMIT = 20
    LIST_ORDER = OrderDirection.DESC
    MAX_METADATA_PAIRS = 16
    MAX_METADATA_KEY_LENGTH = 64
    MAX_METADATA_VALUE_LENGTH = 512
    MAX_CODE_INTERPRETER_FILES = 20
    MAX_FILE_SEARCH_VECTORS = 1
    LIST_LIMIT_RANGE = range(1, 101)  # 1-100

class ToolResources(TypedDict, total=False):
    code_interpreter: Dict[str, List[str]]  # {"file_ids": [...]}
    file_search: Dict[str, List[str]]      # {"vector_store_ids": [...]}

class TruncationStrategy(TypedDict):
    type: str  # TruncationType
    last_messages: Optional[int]

class AzureClientWrapper:
    """Wrapper for Azure OpenAI client to abstract API version specifics"""
    
    def __init__(self, client: AzureOpenAI):
        self._client = client

    def create_vector_store(self, name: str, expires_after: dict) -> Any:
        """Creates a vector store"""
        return self._client.beta.vector_stores.create(
            name=name,
            expires_after=expires_after
        )
    
    def retrieve_vector_store(self, vector_store_id: str) -> Any:
        """Retrieves a vector store by ID"""
        return self._client.beta.vector_stores.retrieve(vector_store_id)
    
    def upload_file_batch(self, vector_store_id: str, files: list) -> Any:
        """Uploads a batch of files to vector store"""
        return self._client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store_id,
            files=files
        )
    
    def create_assistant(self, 
                        model: str,
                        name: Optional[str] = None,
                        description: Optional[str] = None,
                        instructions: Optional[str] = None,
                        tools: Optional[List[Dict[str, Any]]] = None,
                        metadata: Optional[Dict[str, str]] = None,
                        temperature: Optional[float] = None,
                        top_p: Optional[float] = None,
                        response_format: Optional[Dict[str, str]] = None,
                        tool_resources: Optional[Dict[str, Any]] = None) -> Any:
        """Creates an assistant with specified configuration"""
        return self._client.beta.assistants.create(
            model=model,
            name=name,
            description=description,
            instructions=instructions,
            tools=tools or [],
            metadata=metadata,
            temperature=temperature,
            top_p=top_p,
            response_format=response_format,
            tool_resources=tool_resources
        )
    
    def list_assistants(self, 
                       limit: Optional[int] = None,
                       order: Optional[str] = None,
                       after: Optional[str] = None,
                       before: Optional[str] = None) -> Any:
        """Returns a list of assistants"""
        return self._client.beta.assistants.list(
            limit=limit,
            order=order,
            after=after,
            before=before
        )
    
    def retrieve_assistant(self, assistant_id: str) -> Any:
        """Retrieves an assistant by ID"""
        return self._client.beta.assistants.retrieve(assistant_id)
    
    def update_assistant(self,
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
                        tool_resources: Optional[Dict[str, Any]] = None) -> Any:
        """Updates an existing assistant"""
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
            tool_resources=tool_resources
        )
    
    def delete_assistant(self, assistant_id: str) -> Any:
        """Deletes an assistant"""
        return self._client.beta.assistants.delete(assistant_id)
    
    # Thread Operations
    def create_thread(self, 
                     messages: Optional[List[Dict[str, Any]]] = None,
                     metadata: Optional[Dict[str, str]] = None,
                     tool_resources: Optional[ToolResources] = None) -> Any:
        """Creates a new thread."""
        return self._client.beta.threads.create(
            messages=messages,
            metadata=metadata,
            tool_resources=tool_resources
        )

    def retrieve_thread(self, thread_id: str) -> Any:
        """Retrieves a thread by ID."""
        return self._client.beta.threads.retrieve(thread_id)

    def update_thread(self,
                     thread_id: str,
                     metadata: Optional[Dict[str, str]] = None,
                     tool_resources: Optional[ToolResources] = None) -> Any:
        """Modifies an existing thread."""
        return self._client.beta.threads.update(
            thread_id,
            metadata=metadata,
            tool_resources=tool_resources
        )

    def delete_thread(self, thread_id: str) -> Any:
        """Deletes a thread."""
        return self._client.beta.threads.delete(thread_id)
    
    # Message Operations
    def create_message(self,
                      thread_id: str,
                      role: MessageRole,
                      content: str,
                      attachments: Optional[List[Dict[str, Any]]] = None,
                      metadata: Optional[Dict[str, str]] = None) -> Any:
        """Creates a message in a thread."""
        return self._client.beta.threads.messages.create(
            thread_id,
            role=role,
            content=content,
            attachments=attachments,
            metadata=metadata
        )

    def list_messages(self,
                     thread_id: str,
                     limit: Optional[int] = Defaults.LIST_LIMIT,
                     order: Optional[OrderDirection] = Defaults.LIST_ORDER,
                     after: Optional[str] = None,
                     before: Optional[str] = None,
                     run_id: Optional[str] = None) -> Any:
        """Returns a list of messages for a given thread."""
        return self._client.beta.threads.messages.list(
            thread_id,
            limit=limit,
            order=order,
            after=after,
            before=before,
            run_id=run_id
        )

    def retrieve_message(self,
                        thread_id: str,
                        message_id: str) -> Any:
        """Retrieves a specific message from a thread."""
        return self._client.beta.threads.messages.retrieve(
            message_id=message_id,
            thread_id=thread_id
        )

    def update_message(self,
                      thread_id: str,
                      message_id: str,
                      metadata: Optional[Dict[str, str]] = None) -> Any:
        """Modifies a message."""
        return self._client.beta.threads.messages.update(
            message_id=message_id,
            thread_id=thread_id,
            metadata=metadata
        )

    def delete_message(self,
                      thread_id: str,
                      message_id: str) -> Any:
        """Deletes a message."""
        return self._client.beta.threads.messages.delete(
            message_id=message_id,
            thread_id=thread_id
        )
    
    # Run Operations
    def create_run(self,
                  thread_id: str,
                  assistant_id: str,
                  model: Optional[str] = None,
                  instructions: Optional[str] = None,
                  additional_instructions: Optional[str] = None,
                  additional_messages: Optional[List[Dict[str, Any]]] = None,
                  tools: Optional[List[Dict[str, Any]]] = None,
                  metadata: Optional[Dict[str, str]] = None,
                  temperature: Optional[float] = None,
                  top_p: Optional[float] = None,
                  stream: Optional[bool] = None,
                  max_prompt_tokens: Optional[int] = None,
                  max_completion_tokens: Optional[int] = None,
                  truncation_strategy: Optional[TruncationStrategy] = None,
                  tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
                  response_format: Optional[Dict[str, str]] = None) -> Any:
        """Creates a run for a thread."""
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
            response_format=response_format
        )

    def create_thread_and_run(self,
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
                            response_format: Optional[Dict[str, str]] = None) -> Any:
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
            response_format=response_format
        )

    def list_runs(self,
                 thread_id: str,
                 limit: Optional[int] = None,
                 order: Optional[str] = None,
                 after: Optional[str] = None,
                 before: Optional[str] = None) -> Any:
        """Returns a list of runs belonging to a thread."""
        return self._client.beta.threads.runs.list(
            thread_id=thread_id,
            limit=limit,
            order=order,
            after=after,
            before=before
        )

    def list_run_steps(self,
                      thread_id: str,
                      run_id: str,
                      limit: Optional[int] = None,
                      order: Optional[str] = None,
                      after: Optional[str] = None,
                      before: Optional[str] = None) -> Any:
        """Returns a list of run steps belonging to a run."""
        return self._client.beta.threads.runs.steps.list(
            thread_id=thread_id,
            run_id=run_id,
            limit=limit,
            order=order,
            after=after,
            before=before
        )

    def retrieve_run(self, thread_id: str, run_id: str) -> Any:
        """Retrieves a run."""
        return self._client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run_id
        )

    def retrieve_run_step(self, thread_id: str, run_id: str, step_id: str) -> Any:
        """Retrieves a run step."""
        return self._client.beta.threads.runs.steps.retrieve(
            thread_id=thread_id,
            run_id=run_id,
            step_id=step_id
        )

    def update_run(self, thread_id: str, run_id: str, metadata: Dict[str, str]) -> Any:
        """Modifies a run."""
        return self._client.beta.threads.runs.update(
            thread_id=thread_id,
            run_id=run_id,
            metadata=metadata
        )

    def submit_tool_outputs(self,
                          thread_id: str,
                          run_id: str,
                          tool_outputs: List[Dict[str, Any]],
                          stream: Optional[bool] = None) -> Any:
        """Submits outputs for tool calls."""
        return self._client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread_id,
            run_id=run_id,
            tool_outputs=tool_outputs,
            stream=stream
        )

    def cancel_run(self, thread_id: str, run_id: str) -> Any:
        """Cancels a run that is in_progress."""
        return self._client.beta.threads.runs.cancel(
            thread_id=thread_id,
            run_id=run_id
        )

    def stream_run(self,
                  thread_id: str,
                  assistant_id: str,
                  event_handler: AssistantEventHandler,
                  **run_params) -> Any:
        """Stream the result of executing a Run."""
        return self._client.beta.threads.runs.stream(
            thread_id=thread_id,
            assistant_id=assistant_id,
            event_handler=event_handler,
            **run_params
        ) 