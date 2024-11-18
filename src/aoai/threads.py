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
    ERROR_INVALID_THREAD_METADATA_KEY_LENGTH,
    ERROR_INVALID_THREAD_METADATA_PAIRS,
    ERROR_INVALID_THREAD_METADATA_VALUE_LENGTH,
    LIST_LIMIT_RANGE,
    MAX_THREAD_CODE_INTERPRETER_FILES,
    MAX_THREAD_FILE_SEARCH_STORES,
    MAX_THREAD_METADATA_KEY_LENGTH,
    MAX_THREAD_METADATA_PAIRS,
    MAX_THREAD_METADATA_VALUE_LENGTH,
    PARAM_AFTER,
    PARAM_BEFORE,
    PARAM_FILE_IDS,
    PARAM_LIMIT,
    PARAM_MESSAGES,
    PARAM_METADATA,
    PARAM_ORDER,
    PARAM_TOOL_RESOURCES,
    PARAM_VECTOR_STORE_IDS,
    PARAM_VECTOR_STORES,
    TOOL_CODE_INTERPRETER,
    TOOL_FILE_SEARCH,
)
from .messages import Messages
from .runs import Runs


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
            if len(metadata) > MAX_THREAD_METADATA_PAIRS:
                raise ValueError(ERROR_INVALID_THREAD_METADATA_PAIRS)

            for key, value in metadata.items():
                if len(key) > MAX_THREAD_METADATA_KEY_LENGTH:
                    raise ValueError(ERROR_INVALID_THREAD_METADATA_KEY_LENGTH)
                if len(str(value)) > MAX_THREAD_METADATA_VALUE_LENGTH:
                    raise ValueError(ERROR_INVALID_THREAD_METADATA_VALUE_LENGTH)

        # Validate tool resources if provided
        if tool_resources:
            if TOOL_CODE_INTERPRETER in tool_resources:
                file_ids = tool_resources[TOOL_CODE_INTERPRETER].get(PARAM_FILE_IDS, [])
                if len(file_ids) > MAX_THREAD_CODE_INTERPRETER_FILES:
                    raise ValueError(ERROR_INVALID_THREAD_CODE_INTERPRETER_FILES)

            if TOOL_FILE_SEARCH in tool_resources:
                vector_store_ids = tool_resources[TOOL_FILE_SEARCH].get(
                    PARAM_VECTOR_STORE_IDS, []
                )
                vector_stores = tool_resources[TOOL_FILE_SEARCH].get(
                    PARAM_VECTOR_STORES, []
                )
                if (
                    len(vector_store_ids) + len(vector_stores)
                    > MAX_THREAD_FILE_SEARCH_STORES
                ):
                    raise ValueError(ERROR_INVALID_THREAD_FILE_SEARCH_STORES)

        params = {
            PARAM_MESSAGES: messages,
            PARAM_METADATA: metadata,
            PARAM_TOOL_RESOURCES: tool_resources,
            **kwargs,
        }
        params = {k: v for k, v in params.items() if v is not None}

        return self._client.beta.threads.create(**params)

    def retrieve(self, thread_id: str) -> Any:
        """Retrieves a thread."""
        if not thread_id:
            raise ValueError(ERROR_INVALID_THREAD_ID)
        return self._client.beta.threads.retrieve(thread_id)

    def update(
        self,
        thread_id: str,
        metadata: Optional[Dict[str, str]] = None,
        tool_resources: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """Modifies a thread."""
        if not thread_id:
            raise ValueError(ERROR_INVALID_THREAD_ID)

        # Validate metadata if provided
        if metadata:
            if len(metadata) > MAX_THREAD_METADATA_PAIRS:
                raise ValueError(ERROR_INVALID_THREAD_METADATA_PAIRS)

            for key, value in metadata.items():
                if len(key) > MAX_THREAD_METADATA_KEY_LENGTH:
                    raise ValueError(ERROR_INVALID_THREAD_METADATA_KEY_LENGTH)
                if len(str(value)) > MAX_THREAD_METADATA_VALUE_LENGTH:
                    raise ValueError(ERROR_INVALID_THREAD_METADATA_VALUE_LENGTH)

        # Validate tool resources if provided
        if tool_resources:
            if TOOL_CODE_INTERPRETER in tool_resources:
                file_ids = tool_resources[TOOL_CODE_INTERPRETER].get(PARAM_FILE_IDS, [])
                if len(file_ids) > MAX_THREAD_CODE_INTERPRETER_FILES:
                    raise ValueError(ERROR_INVALID_THREAD_CODE_INTERPRETER_FILES)

            if TOOL_FILE_SEARCH in tool_resources:
                vector_store_ids = tool_resources[TOOL_FILE_SEARCH].get(
                    PARAM_VECTOR_STORE_IDS, []
                )
                vector_stores = tool_resources[TOOL_FILE_SEARCH].get(
                    PARAM_VECTOR_STORES, []
                )
                if (
                    len(vector_store_ids) + len(vector_stores)
                    > MAX_THREAD_FILE_SEARCH_STORES
                ):
                    raise ValueError(ERROR_INVALID_THREAD_FILE_SEARCH_STORES)

        params = {
            PARAM_METADATA: metadata,
            PARAM_TOOL_RESOURCES: tool_resources,
            **kwargs,
        }
        params = {k: v for k, v in params.items() if v is not None}

        return self._client.beta.threads.update(thread_id, **params)

    def delete(self, thread_id: str) -> Any:
        """Deletes a thread."""
        if not thread_id:
            raise ValueError(ERROR_INVALID_THREAD_ID)
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
