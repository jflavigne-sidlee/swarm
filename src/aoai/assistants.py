"""Azure OpenAI Assistants API wrapper.

This module provides a wrapper for the Azure OpenAI Assistants API, offering methods
to create, list, retrieve, update, and delete assistants.

Typical usage example:
    client = AOAIClient.create(...)
    assistants = Assistants(client)
    assistant = assistants.create(
        model="gpt-4",
        name="My Assistant",
        instructions="You are a helpful assistant."
    )
"""

from typing import Optional, List, Dict, Any
from openai import AzureOpenAI
from .utils import (
    validate_temperature,
    validate_top_p,
    validate_metadata,
    clean_params,
    validate_assistant_name,
    validate_assistant_description,
    validate_assistant_instructions,
    validate_assistant_tools,
    validate_assistant_id,
)
from .constants import (
    DEFAULT_ASSISTANT_DESCRIPTION,
    DEFAULT_ASSISTANT_LIST_PARAMS,
    DEFAULT_ASSISTANT_NAME,
    DEFAULT_ASSISTANT_TEMPERATURE,
    DEFAULT_ASSISTANT_TOOLS,
    DEFAULT_ASSISTANT_TOP_P,
    DEFAULT_INSTRUCTIONS,
    DEFAULT_METADATA,
    DEFAULT_RESPONSE_FORMAT,
    DEFAULT_TOOL_RESOURCES,
    ERROR_INVALID_LIMIT,
    LIST_LIMIT_RANGE,
    PARAM_AFTER,
    PARAM_BEFORE,
    PARAM_DESCRIPTION,
    PARAM_INSTRUCTIONS,
    PARAM_LIMIT,
    PARAM_METADATA,
    PARAM_MODEL,
    PARAM_NAME,
    PARAM_ORDER,
    PARAM_RESPONSE_FORMAT,
    PARAM_TEMPERATURE,
    PARAM_TOOLS,
    PARAM_TOOL_RESOURCES,
    PARAM_TOP_P,
)


class Assistants:
    """Manages Azure OpenAI Assistant operations.
    
    This class provides methods for creating, listing, retrieving, updating,
    and deleting assistants in Azure OpenAI.

    Attributes:
        _client: An instance of AzureOpenAI client.
    """

    def __init__(self, client: AzureOpenAI) -> None:
        """Initializes the Assistants manager.

        Args:
            client: An instance of AzureOpenAI client.
        """
        self._client = client

    def create(
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
        **kwargs
    ) -> Any:
        """Creates an assistant with the specified configuration.

        Args:
            model: The model to use for the assistant.
            name: The name of the assistant.
            description: A description of the assistant's purpose.
            instructions: Instructions for the assistant's behavior.
            tools: List of tools available to the assistant.
            metadata: Additional metadata for the assistant.
            temperature: Sampling temperature between 0 and 2.
            top_p: Nucleus sampling parameter between 0 and 1.
            response_format: Format specification for responses.
            tool_resources: Additional resources for tools.
            **kwargs: Additional parameters to pass to the API.

        Returns:
            The created assistant object.

        Raises:
            ValueError: If any of the parameters fail validation.
        """
        validate_assistant_name(name)
        validate_assistant_description(description)
        validate_assistant_instructions(instructions)
        validate_assistant_tools(tools)
        validate_temperature(temperature)
        validate_top_p(top_p)
        validate_metadata(metadata)

        params = {
            PARAM_MODEL: model,
            PARAM_NAME: name,
            PARAM_DESCRIPTION: description,
            PARAM_INSTRUCTIONS: instructions,
            PARAM_TOOLS: tools,
            PARAM_METADATA: metadata,
            PARAM_TEMPERATURE: temperature,
            PARAM_TOP_P: top_p,
            PARAM_RESPONSE_FORMAT: response_format,
            PARAM_TOOL_RESOURCES: tool_resources,
            **kwargs,
        }

        return self._client.beta.assistants.create(**clean_params(params))

    def list(
        self,
        limit: Optional[int] = DEFAULT_ASSISTANT_LIST_PARAMS[PARAM_LIMIT],
        order: Optional[str] = DEFAULT_ASSISTANT_LIST_PARAMS[PARAM_ORDER],
        after: Optional[str] = DEFAULT_ASSISTANT_LIST_PARAMS[PARAM_AFTER],
        before: Optional[str] = DEFAULT_ASSISTANT_LIST_PARAMS[PARAM_BEFORE],
    ) -> Any:
        """Lists available assistants.

        Args:
            limit: Maximum number of assistants to return.
            order: Sort order for the results ('asc' or 'desc').
            after: Return results after this assistant ID.
            before: Return results before this assistant ID.

        Returns:
            A list of assistant objects.

        Raises:
            ValueError: If limit is outside the valid range.
        """
        if limit and limit not in LIST_LIMIT_RANGE:
            raise ValueError(ERROR_INVALID_LIMIT)

        params = {
            PARAM_LIMIT: limit,
            PARAM_ORDER: order,
            PARAM_AFTER: after,
            PARAM_BEFORE: before,
        }

        return self._client.beta.assistants.list(**clean_params(params))

    def retrieve(self, assistant_id: str) -> Any:
        """Retrieves an assistant by ID.

        Args:
            assistant_id: The ID of the assistant to retrieve.

        Returns:
            The assistant object.

        Raises:
            NotFoundError: If the assistant ID doesn't exist.
        """
        return self._client.beta.assistants.retrieve(assistant_id)

    def update(
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
        **kwargs
    ) -> Any:
        """Updates an existing assistant.

        Args:
            assistant_id: The ID of the assistant to update.
            model: The model to use for the assistant.
            name: The name of the assistant.
            description: A description of the assistant's purpose.
            instructions: Instructions for the assistant's behavior.
            tools: List of tools available to the assistant.
            metadata: Additional metadata for the assistant.
            temperature: Sampling temperature between 0 and 2.
            top_p: Nucleus sampling parameter between 0 and 1.
            response_format: Format specification for responses.
            tool_resources: Additional resources for tools.
            **kwargs: Additional parameters to pass to the API.

        Returns:
            The updated assistant object.

        Raises:
            ValueError: If any of the parameters fail validation.
            NotFoundError: If the assistant ID doesn't exist.
        """
        validate_assistant_id(assistant_id)
        validate_assistant_name(name)
        validate_assistant_description(description)
        validate_assistant_instructions(instructions)
        validate_assistant_tools(tools)
        validate_temperature(temperature)
        validate_top_p(top_p)
        validate_metadata(metadata)

        params = {
            PARAM_MODEL: model,
            PARAM_NAME: name,
            PARAM_DESCRIPTION: description,
            PARAM_INSTRUCTIONS: instructions,
            PARAM_TOOLS: tools,
            PARAM_METADATA: metadata,
            PARAM_TEMPERATURE: temperature,
            PARAM_TOP_P: top_p,
            PARAM_RESPONSE_FORMAT: response_format,
            PARAM_TOOL_RESOURCES: tool_resources,
            **kwargs,
        }

        return self._client.beta.assistants.update(assistant_id, **clean_params(params))

    def delete(self, assistant_id: str) -> Any:
        """Deletes an assistant.

        Args:
            assistant_id: The ID of the assistant to delete.

        Returns:
            A deletion status object.

        Raises:
            NotFoundError: If the assistant ID doesn't exist.
        """
        return self._client.beta.assistants.delete(assistant_id)

    # Compatibility methods
    def create_assistant(self, *args, **kwargs) -> Any:
        """Compatibility alias for create().

        This method exists for backward compatibility.
        See create() for full documentation.

        Returns:
            The created assistant object.
        """
        return self.create(*args, **kwargs)

    def list_assistants(self, *args, **kwargs) -> Any:
        """Compatibility alias for list().

        This method exists for backward compatibility.
        See list() for full documentation.

        Returns:
            A list of assistant objects.
        """
        return self.list(*args, **kwargs)

    def retrieve_assistant(self, assistant_id: str) -> Any:
        """Compatibility alias for retrieve().

        This method exists for backward compatibility.
        See retrieve() for full documentation.

        Args:
            assistant_id: The ID of the assistant to retrieve.

        Returns:
            The assistant object.
        """
        return self.retrieve(assistant_id)

    def update_assistant(self, assistant_id: str, **kwargs) -> Any:
        """Compatibility alias for update().

        This method exists for backward compatibility.
        See update() for full documentation.

        Args:
            assistant_id: The ID of the assistant to update.
            **kwargs: Additional parameters to pass to update().

        Returns:
            The updated assistant object.
        """
        return self.update(assistant_id, **kwargs)

    def delete_assistant(self, assistant_id: str) -> Any:
        """Compatibility alias for delete().

        This method exists for backward compatibility.
        See delete() for full documentation.

        Args:
            assistant_id: The ID of the assistant to delete.

        Returns:
            A deletion status object.
        """
        return self.delete(assistant_id)
