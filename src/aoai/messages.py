from typing import Optional, Dict, Any, List, Union
from openai import AzureOpenAI
from .types import MessageRole
from .utils import (
    clean_params, 
    validate_metadata, 
    validate_thread_id, 
    validate_message_id
)
from .constants import (
    DEFAULT_MESSAGE_LIST_PARAMS,
    ERROR_INVALID_LIMIT,
    ERROR_INVALID_MESSAGE_ID,
    ERROR_INVALID_THREAD_ID,
    LIST_LIMIT_RANGE,
    PARAM_AFTER,
    PARAM_BEFORE,
    PARAM_CONTENT,
    PARAM_LIMIT,
    PARAM_MESSAGE_ID,
    PARAM_METADATA,
    PARAM_ORDER,
    PARAM_ROLE,
    PARAM_RUN_ID,
    PARAM_THREAD_ID,
)


class Messages:
    """Message operations"""

    def __init__(self, client: AzureOpenAI):
        self._client = client

    def create(
        self, 
        thread_id: str, 
        role: MessageRole, 
        content: str, 
        metadata: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Any:
        """Creates a message in a thread."""
        validate_thread_id(thread_id, ERROR_INVALID_THREAD_ID)

        # Validate metadata if provided
        if metadata:
            validate_metadata(metadata)

        params = {
            PARAM_THREAD_ID: thread_id,
            PARAM_ROLE: role,
            PARAM_CONTENT: content,
            PARAM_METADATA: metadata,
            **kwargs
        }

        return self._client.beta.threads.messages.create(**clean_params(params))

    def list(
        self,
        thread_id: str,
        limit: Optional[int] = DEFAULT_MESSAGE_LIST_PARAMS[PARAM_LIMIT],
        order: Optional[str] = DEFAULT_MESSAGE_LIST_PARAMS[PARAM_ORDER],
        after: Optional[str] = DEFAULT_MESSAGE_LIST_PARAMS[PARAM_AFTER],
        before: Optional[str] = DEFAULT_MESSAGE_LIST_PARAMS[PARAM_BEFORE],
        run_id: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Returns a list of messages for a given thread."""
        validate_thread_id(thread_id, ERROR_INVALID_THREAD_ID)

        if limit and limit not in LIST_LIMIT_RANGE:
            raise ValueError(ERROR_INVALID_LIMIT)

        params = {
            PARAM_THREAD_ID: thread_id,
            PARAM_LIMIT: limit,
            PARAM_ORDER: order,
            PARAM_AFTER: after,
            PARAM_BEFORE: before,
            PARAM_RUN_ID: run_id,
            **kwargs,
        }

        return self._client.beta.threads.messages.list(**clean_params(params))

    def retrieve(self, thread_id: str, message_id: str, **kwargs) -> Any:
        """Retrieves a specific message from a thread."""
        validate_thread_id(thread_id, ERROR_INVALID_THREAD_ID)
        validate_message_id(message_id, ERROR_INVALID_MESSAGE_ID)

        params = {
            PARAM_MESSAGE_ID: message_id,
            PARAM_THREAD_ID: thread_id,
            **kwargs
        }

        return self._client.beta.threads.messages.retrieve(**clean_params(params))

    def update(
        self,
        thread_id: str,
        message_id: str,
        metadata: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Any:
        """Modifies a message."""
        validate_thread_id(thread_id, ERROR_INVALID_THREAD_ID)
        validate_message_id(message_id, ERROR_INVALID_MESSAGE_ID)

        # Validate metadata if provided
        if metadata:
            validate_metadata(metadata)

        params = {
            PARAM_MESSAGE_ID: message_id,
            PARAM_THREAD_ID: thread_id,
            PARAM_METADATA: metadata,
            **kwargs,
        }

        return self._client.beta.threads.messages.update(**clean_params(params))

    def delete(self, thread_id: str, message_id: str, **kwargs) -> Any:
        """Deletes a message."""
        validate_thread_id(thread_id, ERROR_INVALID_THREAD_ID)
        validate_message_id(message_id, ERROR_INVALID_MESSAGE_ID)

        params = {
            PARAM_MESSAGE_ID: message_id,
            PARAM_THREAD_ID: thread_id,
            **kwargs
        }

        return self._client.beta.threads.messages.delete(**clean_params(params))

    # Compatibility methods
    def create_message(self, *args, **kwargs) -> Any:
        """Compatibility method for create()"""
        return self.create(*args, **kwargs)

    def list_messages(self, *args, **kwargs) -> Any:
        """Compatibility method for list()"""
        return self.list(*args, **kwargs)

    def retrieve_message(self, *args, **kwargs) -> Any:
        """Compatibility method for retrieve()"""
        return self.retrieve(*args, **kwargs)

    def update_message(self, *args, **kwargs) -> Any:
        """Compatibility method for update()"""
        return self.update(*args, **kwargs)

    def delete_message(self, *args, **kwargs) -> Any:
        """Compatibility method for delete()"""
        return self.delete(*args, **kwargs)
