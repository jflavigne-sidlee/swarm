"""Azure OpenAI Message operations.

This module provides functionality for managing messages within threads, including
creation, retrieval, listing, updating, and deletion of messages.

Typical usage example:
    client = AOAIClient.create(...)
    messages = Messages(client)
    message = messages.create(
        thread_id="thread_123",
        role="user",
        content="Hello!"
    )
"""

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
    """Manages message operations in Azure OpenAI.
    
    This class provides methods for creating, listing, retrieving, updating,
    and deleting messages within threads.

    Attributes:
        _client: An instance of AzureOpenAI client.
    """

    def __init__(self, client: AzureOpenAI):
        """Initialize the Messages manager.

        Args:
            client: An instance of AzureOpenAI client.
        """
        self._client = client

    def create(
        self, 
        thread_id: str, 
        role: MessageRole, 
        content: str, 
        metadata: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Any:
        """Creates a message in a thread.

        Args:
            thread_id: The ID of the thread to create the message in.
            role: The role of the message sender (e.g., 'user', 'assistant').
            content: The content of the message.
            metadata: Optional metadata for the message.
            **kwargs: Additional parameters to pass to the API.

        Returns:
            The created message object.

        Raises:
            ValueError: If thread_id is invalid or metadata format is incorrect.
        """
        validate_thread_id(thread_id, ERROR_INVALID_THREAD_ID)

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
        """Lists messages in a thread with pagination support.

        Args:
            thread_id: The ID of the thread to list messages from.
            limit: Maximum number of messages to return (default: from DEFAULT_MESSAGE_LIST_PARAMS).
            order: Sort order for results (default: from DEFAULT_MESSAGE_LIST_PARAMS).
            after: Return results after this ID (default: from DEFAULT_MESSAGE_LIST_PARAMS).
            before: Return results before this ID (default: from DEFAULT_MESSAGE_LIST_PARAMS).
            run_id: Optional run ID to filter messages by.
            **kwargs: Additional parameters to pass to the API.

        Returns:
            A list of message objects.

        Raises:
            ValueError: If thread_id is invalid or limit is outside valid range.
        """
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
        """Retrieves a specific message from a thread.

        Args:
            thread_id: The ID of the thread containing the message.
            message_id: The ID of the message to retrieve.
            **kwargs: Additional parameters to pass to the API.

        Returns:
            The message object.

        Raises:
            ValueError: If thread_id or message_id is invalid.
        """
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
        """Updates a message's metadata.

        Args:
            thread_id: The ID of the thread containing the message.
            message_id: The ID of the message to update.
            metadata: Optional new metadata for the message.
            **kwargs: Additional parameters to pass to the API.

        Returns:
            The updated message object.

        Raises:
            ValueError: If thread_id, message_id is invalid or metadata format is incorrect.
        """
        validate_thread_id(thread_id, ERROR_INVALID_THREAD_ID)
        validate_message_id(message_id, ERROR_INVALID_MESSAGE_ID)

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
        """Deletes a message from a thread.

        Args:
            thread_id: The ID of the thread containing the message.
            message_id: The ID of the message to delete.
            **kwargs: Additional parameters to pass to the API.

        Returns:
            A deletion status object.

        Raises:
            ValueError: If thread_id or message_id is invalid.
        """
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
        """Compatibility method for create().

        See create() for full documentation.

        Returns:
            The created message object.
        """
        return self.create(*args, **kwargs)

    def list_messages(self, *args, **kwargs) -> Any:
        """Compatibility method for list().

        See list() for full documentation.

        Returns:
            A list of message objects.
        """
        return self.list(*args, **kwargs)

    def retrieve_message(self, *args, **kwargs) -> Any:
        """Compatibility method for retrieve().

        See retrieve() for full documentation.

        Returns:
            The message object.
        """
        return self.retrieve(*args, **kwargs)

    def update_message(self, *args, **kwargs) -> Any:
        """Compatibility method for update().

        See update() for full documentation.

        Returns:
            The updated message object.
        """
        return self.update(*args, **kwargs)

    def delete_message(self, *args, **kwargs) -> Any:
        """Compatibility method for delete().

        See delete() for full documentation.

        Returns:
            A deletion status object.
        """
        return self.delete(*args, **kwargs)
