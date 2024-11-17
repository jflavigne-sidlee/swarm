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

class VectorStores:
    """Vector stores operations"""
    def __init__(self, client: AzureOpenAI):
        self._client = client
        self.file_batches = self.FileBatches(client)

    def create(self, name: str, expires_after: dict) -> Any:
        """Creates a vector store"""
        return self._client.beta.vector_stores.create(
            name=name,
            expires_after=expires_after
        )
    
    def retrieve(self, vector_store_id: str) -> Any:
        """Retrieves a vector store by ID"""
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
                vector_store_id=vector_store_id,
                files=files
            )

class Messages:
    """Message operations"""
    def __init__(self, client: AzureOpenAI):
        self._client = client

    def create(self, thread_id: str, role: MessageRole, content: str, **kwargs) -> Any:
        """Creates a message in a thread"""
        return self._client.beta.threads.messages.create(
            thread_id=thread_id,
            role=role,
            content=content,
            **kwargs
        )

    def list(self, thread_id: str, **kwargs) -> Any:
        """Lists messages in a thread"""
        return self._client.beta.threads.messages.list(thread_id, **kwargs)

    def retrieve(self, thread_id: str, message_id: str) -> Any:
        """Retrieves a message"""
        return self._client.beta.threads.messages.retrieve(
            thread_id=thread_id,
            message_id=message_id
        )

    def update(self, thread_id: str, message_id: str, **kwargs) -> Any:
        """Updates a message"""
        return self._client.beta.threads.messages.update(
            thread_id=thread_id,
            message_id=message_id,
            **kwargs
        )

    def delete(self, thread_id: str, message_id: str) -> Any:
        """Deletes a message"""
        return self._client.beta.threads.messages.delete(
            thread_id=thread_id,
            message_id=message_id
        )

class RunSteps:
    """Run steps operations"""
    def __init__(self, client: AzureOpenAI):
        self._client = client

    def list(self, thread_id: str, run_id: str, **kwargs) -> Any:
        """Lists steps in a run"""
        return self._client.beta.threads.runs.steps.list(
            thread_id=thread_id,
            run_id=run_id,
            **kwargs
        )

    def retrieve(self, thread_id: str, run_id: str, step_id: str) -> Any:
        """Retrieves a run step"""
        return self._client.beta.threads.runs.steps.retrieve(
            thread_id=thread_id,
            run_id=run_id,
            step_id=step_id
        )

class Runs:
    """Run operations"""
    def __init__(self, client: AzureOpenAI):
        self._client = client
        self.steps = RunSteps(client)

    def create(self, thread_id: str, assistant_id: str, **kwargs) -> Any:
        """Creates a run"""
        return self._client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
            **kwargs
        )

    def list(self, thread_id: str, **kwargs) -> Any:
        """Lists runs in a thread"""
        return self._client.beta.threads.runs.list(thread_id, **kwargs)

    def retrieve(self, thread_id: str, run_id: str) -> Any:
        """Retrieves a run"""
        return self._client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run_id
        )

    def update(self, thread_id: str, run_id: str, **kwargs) -> Any:
        """Updates a run"""
        return self._client.beta.threads.runs.update(
            thread_id=thread_id,
            run_id=run_id,
            **kwargs
        )

    def submit_tool_outputs(self, thread_id: str, run_id: str, **kwargs) -> Any:
        """Submits tool outputs"""
        return self._client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread_id,
            run_id=run_id,
            **kwargs
        )

    def cancel(self, thread_id: str, run_id: str) -> Any:
        """Cancels a run"""
        return self._client.beta.threads.runs.cancel(
            thread_id=thread_id,
            run_id=run_id
        )

    def stream(self, thread_id: str, assistant_id: str, event_handler: AssistantEventHandler, **run_params) -> Any:
        """Stream the result of executing a Run."""
        # Remove run_id from run_params if present as it's not needed
        if 'run_id' in run_params:
            del run_params['run_id']
        
        return self._client.beta.threads.runs.stream(
            thread_id=thread_id,
            assistant_id=assistant_id,
            event_handler=event_handler,
            **run_params
        )

    def create_thread_and_run(self, assistant_id: str, thread: Dict[str, Any]) -> Any:
        """Creates a thread and run in one operation."""
        # First create the thread
        created_thread = self._client.beta.threads.create(
            messages=thread.get("messages", [])
        )
        
        # Then create the run
        return self._client.beta.threads.runs.create(
            thread_id=created_thread.id,
            assistant_id=assistant_id
        )

class Threads:
    """Thread operations"""
    def __init__(self, client: AzureOpenAI):
        self._client = client
        self.messages = Messages(client)
        self.runs = Runs(client)

    def create(self, **kwargs) -> Any:
        """Creates a thread"""
        return self._client.beta.threads.create(**kwargs)

    def retrieve(self, thread_id: str) -> Any:
        """Retrieves a thread"""
        return self._client.beta.threads.retrieve(thread_id)

    def update(self, thread_id: str, **kwargs) -> Any:
        """Updates a thread"""
        return self._client.beta.threads.update(thread_id, **kwargs)

    def delete(self, thread_id: str) -> Any:
        """Deletes a thread"""
        return self._client.beta.threads.delete(thread_id)

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

        def create(self, 
                  model: str,
                  messages: List[Dict[str, Any]],
                  tools: Optional[List[Dict[str, Any]]] = None,
                  tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
                  temperature: Optional[float] = None,
                  top_p: Optional[float] = None,
                  n: Optional[int] = None,
                  stream: Optional[bool] = None,
                  stop: Optional[Union[str, List[str]]] = None,
                  max_tokens: Optional[int] = None,
                  presence_penalty: Optional[float] = None,
                  frequency_penalty: Optional[float] = None,
                  logit_bias: Optional[Dict[str, float]] = None,
                  user: Optional[str] = None,
                  response_format: Optional[Dict[str, str]] = None,
                  seed: Optional[int] = None,
                  parallel_tool_calls: Optional[bool] = True) -> Any:
            """Creates a chat completion."""
            params = {
                "model": model,
                "messages": messages,
                "tools": tools,
                "tool_choice": tool_choice,
                "temperature": temperature,
                "top_p": top_p,
                "n": n,
                "stream": stream,
                "stop": stop,
                "max_tokens": max_tokens,
                "presence_penalty": presence_penalty,
                "frequency_penalty": frequency_penalty,
                "logit_bias": logit_bias,
                "user": user,
                "response_format": response_format,
                "seed": seed
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
    def create(cls, 
               api_key: str,
               api_version: str,
               azure_endpoint: str) -> 'AzureClientWrapper':
        """Factory method to create a wrapped client with the given credentials"""
        client = AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=azure_endpoint
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

    def create_vector_store(self, name: str, expires_after: dict) -> Any:
        """Creates a vector store"""
        return self.vector_stores.create(name=name, expires_after=expires_after)

    def retrieve_vector_store(self, vector_store_id: str) -> Any:
        """Retrieves a vector store by ID"""
        return self.vector_stores.retrieve(vector_store_id)

    def upload_files_to_vector_store(self, vector_store_id: str, files: list) -> Any:
        """Uploads files to a vector store"""
        return self.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store_id,
            files=files
        )

    def list_vector_stores(self, **kwargs) -> Any:
        """Lists vector stores"""
        return self.vector_stores.list(**kwargs)

    def delete_vector_store(self, vector_store_id: str) -> Any:
        """Deletes a vector store"""
        return self.vector_stores.delete(vector_store_id)
    