"""Azure OpenAI Thread operations.

This module provides functionality for managing threads, including creation,
retrieval, updating, deletion, and listing of threads. Threads serve as
containers for messages and runs in conversations with assistants.

Typical usage example:
    client = AOAIClient.create(...)
    threads = Threads(client)
    thread = threads.create(
        messages=[{"role": "user", "content": "Hello!"}],
        metadata={"user_id": "123"}
    )
"""

from typing import Optional, Dict, Any, List, Union
from openai import AzureOpenAI
from .constants import (
    DEFAULT_THREAD_LIST_PARAMS,
    DEFAULT_THREAD_MESSAGES,
    DEFAULT_THREAD_METADATA,
    DEFAULT_THREAD_TOOL_RESOURCES,
    ERROR_INVALID_LIMIT,
    ERROR_INVALID_THREAD_CODE_INTERPRETER_FILES,
    ERROR_INVALID_THREAD_FILE_SEARCH_STORES,
    ERROR_INVALID_THREAD_ID,
    LIST_LIMIT_RANGE,
    MAX_THREAD_CODE_INTERPRETER_FILES,
    MAX_THREAD_FILE_SEARCH_STORES,
    MAX_THREAD_METADATA_PAIRS,
    PARAM_AFTER,
    PARAM_BEFORE,
    PARAM_LIMIT,
    PARAM_MESSAGES,
    PARAM_METADATA,
    PARAM_ORDER,
    PARAM_TOOL_RESOURCES,
)
from .messages import Messages
from .runs import Runs
from .utils import (
    clean_params,
    validate_metadata,
    validate_thread_id,
    validate_thread_tool_resources,
)


class Threads:
    """Manages thread operations in Azure OpenAI.
    
    This class provides methods for creating, retrieving, updating, and deleting
    threads, as well as managing messages and runs within threads.

    Attributes:
        _client: An instance of AzureOpenAI client.
        messages: Interface for message operations within threads.
        runs: Interface for run operations within threads.
    """

    def __init__(self, client: AzureOpenAI):
        """Initialize the Threads manager.

        Args:
            client: An instance of AzureOpenAI client.
        """
        self._client = client
        self.messages = Messages(client)
        self.runs = Runs(client)

    def create(
        self,
        messages: Optional[List[Dict[str, Any]]] = DEFAULT_THREAD_MESSAGES,
        metadata: Optional[Dict[str, str]] = DEFAULT_THREAD_METADATA,
        tool_resources: Optional[Dict[str, Any]] = DEFAULT_THREAD_TOOL_RESOURCES,
        **kwargs
    ) -> Any:
        """Creates a new thread.

        Args:
            messages: Initial messages for the thread (default: DEFAULT_THREAD_MESSAGES).
            metadata: Optional metadata for the thread (default: DEFAULT_THREAD_METADATA).
            tool_resources: Optional tool configurations (default: DEFAULT_THREAD_TOOL_RESOURCES).
            **kwargs: Additional parameters to pass to the API.

        Returns:
            The created thread object.

        Raises:
            ValueError: If metadata or tool_resources validation fails.
        """
        if metadata:
            validate_metadata(metadata, max_pairs=MAX_THREAD_METADATA_PAIRS)

        validate_thread_tool_resources(
            tool_resources,
            max_code_interpreter_files=MAX_THREAD_CODE_INTERPRETER_FILES,
            max_file_search_stores=MAX_THREAD_FILE_SEARCH_STORES,
            error_code_interpreter=ERROR_INVALID_THREAD_CODE_INTERPRETER_FILES,
            error_file_search=ERROR_INVALID_THREAD_FILE_SEARCH_STORES
        )

        params = {
            PARAM_MESSAGES: messages,
            PARAM_METADATA: metadata,
            PARAM_TOOL_RESOURCES: tool_resources,
            **kwargs,
        }
        return self._client.beta.threads.create(**clean_params(params))

    def retrieve(self, thread_id: str) -> Any:
        """Retrieves a specific thread.

        Args:
            thread_id: The ID of the thread to retrieve.

        Returns:
            The thread object.

        Raises:
            ValueError: If thread_id is invalid.
        """
        validate_thread_id(thread_id, ERROR_INVALID_THREAD_ID)
        return self._client.beta.threads.retrieve(thread_id)

    def update(
        self,
        thread_id: str,
        metadata: Optional[Dict[str, str]] = None,
        tool_resources: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """Updates a thread's metadata and tool resources.

        Args:
            thread_id: The ID of the thread to update.
            metadata: Optional new metadata for the thread.
            tool_resources: Optional new tool configurations.
            **kwargs: Additional parameters to pass to the API.

        Returns:
            The updated thread object.

        Raises:
            ValueError: If thread_id is invalid or metadata/tool_resources validation fails.
        """
        validate_thread_id(thread_id, ERROR_INVALID_THREAD_ID)

        if metadata:
            validate_metadata(metadata, max_pairs=MAX_THREAD_METADATA_PAIRS)

        validate_thread_tool_resources(
            tool_resources,
            max_code_interpreter_files=MAX_THREAD_CODE_INTERPRETER_FILES,
            max_file_search_stores=MAX_THREAD_FILE_SEARCH_STORES,
            error_code_interpreter=ERROR_INVALID_THREAD_CODE_INTERPRETER_FILES,
            error_file_search=ERROR_INVALID_THREAD_FILE_SEARCH_STORES
        )

        params = {
            PARAM_METADATA: metadata,
            PARAM_TOOL_RESOURCES: tool_resources,
            **kwargs,
        }
        return self._client.beta.threads.update(thread_id, **clean_params(params))

    def delete(self, thread_id: str) -> Any:
        """Deletes a thread.

        Args:
            thread_id: The ID of the thread to delete.

        Returns:
            A deletion status object.

        Raises:
            ValueError: If thread_id is invalid.
        """
        validate_thread_id(thread_id, ERROR_INVALID_THREAD_ID)
        return self._client.beta.threads.delete(thread_id)

    def list(
        self,
        limit: Optional[int] = DEFAULT_THREAD_LIST_PARAMS[PARAM_LIMIT],
        order: Optional[str] = DEFAULT_THREAD_LIST_PARAMS[PARAM_ORDER],
        after: Optional[str] = DEFAULT_THREAD_LIST_PARAMS[PARAM_AFTER],
        before: Optional[str] = DEFAULT_THREAD_LIST_PARAMS[PARAM_BEFORE],
    ) -> Any:
        """Lists threads with pagination support.

        Args:
            limit: Maximum number of threads to return (default: from DEFAULT_THREAD_LIST_PARAMS).
            order: Sort order for results (default: from DEFAULT_THREAD_LIST_PARAMS).
            after: Return results after this ID (default: from DEFAULT_THREAD_LIST_PARAMS).
            before: Return results before this ID (default: from DEFAULT_THREAD_LIST_PARAMS).

        Returns:
            A list of thread objects.

        Raises:
            ValueError: If limit is outside valid range.
        """
        if limit and limit not in LIST_LIMIT_RANGE:
            raise ValueError(ERROR_INVALID_LIMIT)

        params = {
            PARAM_LIMIT: limit,
            PARAM_ORDER: order,
            PARAM_AFTER: after,
            PARAM_BEFORE: before,
        }
        params = {k: v for k, v in params.items() if v is not None}

        return self._client.beta.threads.list(**params)

    # Compatibility methods
    def create_thread(self, *args, **kwargs) -> Any:
        """Compatibility method for create().

        See create() for full documentation.

        Returns:
            The created thread object.
        """
        return self.create(*args, **kwargs)

    def retrieve_thread(self, thread_id: str) -> Any:
        """Compatibility method for retrieve().

        See retrieve() for full documentation.

        Returns:
            The thread object.
        """
        return self.retrieve(thread_id)

    def update_thread(self, thread_id: str, **kwargs) -> Any:
        """Compatibility method for update().

        See update() for full documentation.

        Returns:
            The updated thread object.
        """
        return self.update(thread_id, **kwargs)

    def delete_thread(self, thread_id: str) -> Any:
        """Compatibility method for delete().

        See delete() for full documentation.

        Returns:
            A deletion status object.
        """
        return self.delete(thread_id)

    def list_threads(self, *args, **kwargs) -> Any:
        """Compatibility method for list().

        See list() for full documentation.

        Returns:
            A list of thread objects.
        """
        return self.list(*args, **kwargs)
