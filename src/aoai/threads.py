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
    """Thread operations"""

    def __init__(self, client: AzureOpenAI):
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
        """Creates a thread."""
        # Validate metadata if provided
        if metadata:
            validate_metadata(metadata, 
                            max_pairs=MAX_THREAD_METADATA_PAIRS)

        # Validate tool resources if provided
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
        """Retrieves a thread."""
        validate_thread_id(thread_id, ERROR_INVALID_THREAD_ID)
        return self._client.beta.threads.retrieve(thread_id)

    def update(
        self,
        thread_id: str,
        metadata: Optional[Dict[str, str]] = None,
        tool_resources: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """Modifies a thread."""
        validate_thread_id(thread_id, ERROR_INVALID_THREAD_ID)

        # Validate metadata if provided
        if metadata:
            validate_metadata(metadata, 
                            max_pairs=MAX_THREAD_METADATA_PAIRS)

        # Validate tool resources if provided
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
        """Deletes a thread."""
        validate_thread_id(thread_id, ERROR_INVALID_THREAD_ID)
        return self._client.beta.threads.delete(thread_id)

    def list(
        self,
        limit: Optional[int] = DEFAULT_THREAD_LIST_PARAMS[PARAM_LIMIT],
        order: Optional[str] = DEFAULT_THREAD_LIST_PARAMS[PARAM_ORDER],
        after: Optional[str] = DEFAULT_THREAD_LIST_PARAMS[PARAM_AFTER],
        before: Optional[str] = DEFAULT_THREAD_LIST_PARAMS[PARAM_BEFORE],
    ) -> Any:
        """Returns a list of threads."""
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
        """Compatibility method for create()"""
        return self.create(*args, **kwargs)

    def retrieve_thread(self, thread_id: str) -> Any:
        """Compatibility method for retrieve()"""
        return self.retrieve(thread_id)

    def update_thread(self, thread_id: str, **kwargs) -> Any:
        """Compatibility method for update()"""
        return self.update(thread_id, **kwargs)

    def delete_thread(self, thread_id: str) -> Any:
        """Compatibility method for delete()"""
        return self.delete(thread_id)

    def list_threads(self, *args, **kwargs) -> Any:
        """Compatibility method for list()"""
        return self.list(*args, **kwargs)
