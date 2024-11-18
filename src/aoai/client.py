from openai import AzureOpenAI
from typing import Optional, List, Dict, Any, Union
from .assistants import Assistants
from .chat import Chat
from .files import VectorStores
from .threads import Threads
from .types import (
    OrderDirection,
    MessageRole,
    TruncationType,
    ToolType,
    RunStatus,
    ToolResources,
    TruncationStrategy,
)
from .messages import Messages
from .runs import Runs
from .utils import (
    validate_api_key,
    validate_api_version,
    validate_azure_endpoint,
)


class AOAIClient:
    """Azure OpenAI Client wrapper for managing assistants, threads, and vector stores."""

    def __init__(self, client: AzureOpenAI):
        """Initialize with component classes."""
        self._client = client
        self.vector_stores = VectorStores(client)
        self.assistants = Assistants(client)
        self.threads = Threads(client)
        self.chat = Chat(client)
        self.messages = Messages(client)
        self.runs = Runs(client)

    @classmethod
    def create(
        cls, api_key: str, api_version: str, azure_endpoint: str
    ) -> "AOAIClient":
        """Create a new AOAIClient instance with the given credentials."""
        validate_api_key(api_key)
        validate_api_version(api_version)
        validate_azure_endpoint(azure_endpoint)

        client = AzureOpenAI(
            api_key=api_key, api_version=api_version, azure_endpoint=azure_endpoint
        )
        return cls(client)

    @property
    def client(self) -> AzureOpenAI:
        """Access to underlying client if needed."""
        return self._client

    # Compatibility methods for the original AzureClientWrapper interface
    def create_vector_store(self, *args, **kwargs) -> Any:
        """Compatibility method for vector_stores.create()"""
        return self.vector_stores.create(*args, **kwargs)

    def retrieve_vector_store(self, *args, **kwargs) -> Any:
        """Compatibility method for vector_stores.retrieve()"""
        return self.vector_stores.retrieve(*args, **kwargs)

    def upload_files_to_vector_store(self, *args, **kwargs) -> Any:
        """Compatibility method for vector_stores.file_batches.upload_and_poll()"""
        return self.vector_stores.file_batches.upload_and_poll(*args, **kwargs)

    def list_vector_stores(self, *args, **kwargs) -> Any:
        """Compatibility method for vector_stores.list()"""
        return self.vector_stores.list(*args, **kwargs)

    def delete_vector_store(self, *args, **kwargs) -> Any:
        """Compatibility method for vector_stores.delete()"""
        return self.vector_stores.delete(*args, **kwargs)

    # Assistant compatibility methods
    def create_assistant(self, *args, **kwargs) -> Any:
        """Compatibility method for assistants.create()"""
        return self.assistants.create(*args, **kwargs)

    def list_assistants(self, *args, **kwargs) -> Any:
        """Compatibility method for assistants.list()"""
        return self.assistants.list(*args, **kwargs)

    def retrieve_assistant(self, *args, **kwargs) -> Any:
        """Compatibility method for assistants.retrieve()"""
        return self.assistants.retrieve(*args, **kwargs)

    def update_assistant(self, *args, **kwargs) -> Any:
        """Compatibility method for assistants.update()"""
        return self.assistants.update(*args, **kwargs)

    def delete_assistant(self, *args, **kwargs) -> Any:
        """Compatibility method for assistants.delete()"""
        return self.assistants.delete(*args, **kwargs)

    # Thread compatibility methods
    def create_thread(self, *args, **kwargs) -> Any:
        """Compatibility method for threads.create()"""
        return self.threads.create(*args, **kwargs)

    def retrieve_thread(self, *args, **kwargs) -> Any:
        """Compatibility method for threads.retrieve()"""
        return self.threads.retrieve(*args, **kwargs)

    def update_thread(self, *args, **kwargs) -> Any:
        """Compatibility method for threads.update()"""
        return self.threads.update(*args, **kwargs)

    def delete_thread(self, *args, **kwargs) -> Any:
        """Compatibility method for threads.delete()"""
        return self.threads.delete(*args, **kwargs)

    def list_threads(self, *args, **kwargs) -> Any:
        """Compatibility method for threads.list()"""
        return self.threads.list(*args, **kwargs)

    # Message compatibility methods
    def create_message(self, *args, **kwargs) -> Any:
        """Compatibility method for messages.create()"""
        return self.messages.create(*args, **kwargs)

    def list_messages(self, *args, **kwargs) -> Any:
        """Compatibility method for messages.list()"""
        return self.messages.list(*args, **kwargs)

    def retrieve_message(self, *args, **kwargs) -> Any:
        """Compatibility method for messages.retrieve()"""
        return self.messages.retrieve(*args, **kwargs)

    def update_message(self, *args, **kwargs) -> Any:
        """Compatibility method for messages.update()"""
        return self.messages.update(*args, **kwargs)

    def delete_message(self, *args, **kwargs) -> Any:
        """Compatibility method for messages.delete()"""
        return self.messages.delete(*args, **kwargs)

    # Run compatibility methods
    def create_run(self, *args, **kwargs) -> Any:
        """Compatibility method for runs.create()"""
        return self.runs.create(*args, **kwargs)

    def list_runs(self, *args, **kwargs) -> Any:
        """Compatibility method for runs.list()"""
        return self.runs.list(*args, **kwargs)

    def retrieve_run(self, *args, **kwargs) -> Any:
        """Compatibility method for runs.retrieve()"""
        return self.runs.retrieve(*args, **kwargs)

    def update_run(self, *args, **kwargs) -> Any:
        """Compatibility method for runs.update()"""
        return self.runs.update(*args, **kwargs)

    def cancel_run(self, *args, **kwargs) -> Any:
        """Compatibility method for runs.cancel()"""
        return self.runs.cancel(*args, **kwargs)

    def submit_tool_outputs(self, *args, **kwargs) -> Any:
        """Compatibility method for runs.submit_tool_outputs()"""
        return self.runs.submit_tool_outputs(*args, **kwargs)

    def create_thread_and_run(self, *args, **kwargs) -> Any:
        """Compatibility method for threads.create_and_run()"""
        return self.threads.create_and_run(*args, **kwargs)

    def list_run_steps(self, *args, **kwargs) -> Any:
        """Compatibility method for runs.steps.list()"""
        return self.runs.steps.list(*args, **kwargs)

    def retrieve_run_step(self, *args, **kwargs) -> Any:
        """Compatibility method for runs.steps.retrieve()"""
        return self.runs.steps.retrieve(*args, **kwargs)

AzureClientWrapper = AOAIClient  # Backward compatibility alias
