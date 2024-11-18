"""Utility functions for Azure OpenAI operations.

This module provides validation and utility functions used throughout the Azure OpenAI
client library. It includes functions for validating various parameters, cleaning
parameter dictionaries, and ensuring constraints are met.

Typical usage example:
    from aoai.utils import validate_metadata, clean_params, validate_temperature

    validate_metadata({"key": "value"}, max_pairs=10)
    validate_temperature(0.7)
    cleaned_params = clean_params({"param1": "value", "param2": None})
"""

from typing import Dict, Any, Optional, List, IO
from io import BufferedReader, TextIOWrapper
from .constants import (
    ERROR_API_KEY_REQUIRED,
    ERROR_API_KEY_TYPE,
    ERROR_API_VERSION_REQUIRED,
    ERROR_API_VERSION_TYPE,
    ERROR_AZURE_ENDPOINT_REQUIRED,
    ERROR_AZURE_ENDPOINT_TYPE,
    ERROR_INVALID_ASSISTANT_DESCRIPTION_LENGTH,
    ERROR_INVALID_ASSISTANT_ID,
    ERROR_INVALID_ASSISTANT_ID_TYPE,
    ERROR_INVALID_ASSISTANT_INSTRUCTIONS_LENGTH,
    ERROR_INVALID_ASSISTANT_NAME_LENGTH,
    ERROR_INVALID_ASSISTANT_TOOLS_COUNT,
    ERROR_INVALID_FREQUENCY_PENALTY,
    ERROR_INVALID_MAX_TOKENS,
    ERROR_INVALID_N,
    ERROR_INVALID_PRESENCE_PENALTY,
    ERROR_INVALID_TEMPERATURE,
    ERROR_INVALID_TOP_P,
    MAX_ASSISTANT_DESCRIPTION_LENGTH,
    MAX_ASSISTANT_INSTRUCTIONS_LENGTH,
    MAX_ASSISTANT_NAME_LENGTH,
    MAX_ASSISTANT_TOOLS_COUNT,
    MAX_METADATA_KEY_LENGTH,
    MAX_METADATA_PAIRS,
    MAX_METADATA_VALUE_LENGTH,
    PARAM_FILE_IDS,
    PARAM_VECTOR_STORE_IDS,
    PARAM_VECTOR_STORES,
    TOOL_CODE_INTERPRETER,
    TOOL_FILE_SEARCH,
    VALID_FREQUENCY_PENALTY_RANGE,
    VALID_PRESENCE_PENALTY_RANGE,
    VALID_TEMPERATURE_RANGE,
    VALID_TOP_P_RANGE,
)


def validate_metadata(
    metadata: Dict[str, str], max_pairs: int = MAX_METADATA_PAIRS
) -> None:
    """Validates metadata dictionary against constraints.

    Args:
        metadata: Dictionary of metadata key-value pairs.
        max_pairs: Maximum number of allowed metadata pairs.

    Raises:
        ValueError: If metadata exceeds size limits or contains invalid values.
    """
    if not metadata:
        return

    if len(metadata) > max_pairs:
        raise ValueError(f"Maximum {max_pairs} metadata pairs allowed")

    for key, value in metadata.items():
        if len(key) > MAX_METADATA_KEY_LENGTH:
            raise ValueError(
                f"Metadata key length must not exceed {MAX_METADATA_KEY_LENGTH} characters"
            )
        if len(str(value)) > MAX_METADATA_VALUE_LENGTH:
            raise ValueError(
                f"Metadata value length must not exceed {MAX_METADATA_VALUE_LENGTH} characters"
            )


def validate_temperature(temperature: Optional[float]) -> None:
    """Validates temperature parameter.

    Args:
        temperature: The temperature value to validate.

    Raises:
        ValueError: If temperature is outside the valid range.
    """
    if (
        temperature is not None
        and not VALID_TEMPERATURE_RANGE[0] <= temperature <= VALID_TEMPERATURE_RANGE[1]
    ):
        raise ValueError(ERROR_INVALID_TEMPERATURE)


def validate_top_p(top_p: Optional[float]) -> None:
    """Validates the top_p sampling parameter.

    Args:
        top_p: The top_p value to validate. If provided, must be between 0 and 1.

    Raises:
        ValueError: If top_p is outside the valid range defined in VALID_TOP_P_RANGE.
    """
    if top_p is not None and not VALID_TOP_P_RANGE[0] <= top_p <= VALID_TOP_P_RANGE[1]:
        raise ValueError(ERROR_INVALID_TOP_P)


def validate_presence_penalty(presence_penalty: Optional[float]) -> None:
    """Validates the presence penalty parameter.

    Args:
        presence_penalty: The presence penalty value to validate. If provided, must be
            within the range defined by VALID_PRESENCE_PENALTY_RANGE.

    Raises:
        ValueError: If presence_penalty is outside the valid range.
    """
    if (
        presence_penalty is not None
        and not VALID_PRESENCE_PENALTY_RANGE[0]
        <= presence_penalty
        <= VALID_PRESENCE_PENALTY_RANGE[1]
    ):
        raise ValueError(ERROR_INVALID_PRESENCE_PENALTY)


def validate_frequency_penalty(frequency_penalty: Optional[float]) -> None:
    """Validates the frequency penalty parameter.

    Args:
        frequency_penalty: The frequency penalty value to validate. If provided, must be
            within the range defined by VALID_FREQUENCY_PENALTY_RANGE.

    Raises:
        ValueError: If frequency_penalty is outside the valid range.
    """
    if (
        frequency_penalty is not None
        and not VALID_FREQUENCY_PENALTY_RANGE[0]
        <= frequency_penalty
        <= VALID_FREQUENCY_PENALTY_RANGE[1]
    ):
        raise ValueError(ERROR_INVALID_FREQUENCY_PENALTY)


def clean_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Removes None values from parameters dictionary.

    Args:
        params: Dictionary of parameters.

    Returns:
        A new dictionary with None values removed.
    """
    return {k: v for k, v in params.items() if v is not None}


def validate_vector_store_id(vector_store_id: Optional[str]) -> None:
    """Validates vector store ID.

    Args:
        vector_store_id: The vector store ID to validate.

    Raises:
        ValueError: If vector_store_id is None or not a string.
    """
    if not vector_store_id:
        raise ValueError("Vector store ID is required")
    if not isinstance(vector_store_id, str):
        raise ValueError("Vector store ID must be a string")


def validate_files(files: Optional[list]) -> None:
    """Validates files list for vector store operations.

    Args:
        files: List of files to validate.

    Raises:
        ValueError: If files list is empty or contains invalid file types.
    """
    if not files:
        raise ValueError("Files list cannot be empty")
    if not isinstance(files, list):
        raise ValueError("Files must be provided as a list")
    if not all(isinstance(f, (str, bytes, dict, BufferedReader, TextIOWrapper)) for f in files):
        raise ValueError("Each file must be a string path, bytes, file object, or dict")


def validate_thread_id(
    thread_id: Optional[str], error_msg: str = "Thread ID is required"
) -> None:
    """Validates thread ID format and presence.

    Args:
        thread_id: The thread ID to validate.
        error_msg: Custom error message for missing thread ID (default: "Thread ID is required").

    Raises:
        ValueError: If thread_id is None, empty, or not a string.
    """
    if not thread_id:
        raise ValueError(error_msg)
    if not isinstance(thread_id, str):
        raise ValueError("Thread ID must be a string")


def validate_message_id(
    message_id: Optional[str], error_msg: str = "Message ID is required"
) -> None:
    """Validates message ID format and presence.

    Args:
        message_id: The message ID to validate.
        error_msg: Custom error message for missing message ID (default: "Message ID is required").

    Raises:
        ValueError: If message_id is None, empty, or not a string.
    """
    if not message_id:
        raise ValueError(error_msg)
    if not isinstance(message_id, str):
        raise ValueError("Message ID must be a string")


def validate_run_id(
    run_id: Optional[str], error_msg: str = "Run ID is required"
) -> None:
    """Validates run ID format and presence.

    Args:
        run_id: The run ID to validate.
        error_msg: Custom error message for missing run ID (default: "Run ID is required").

    Raises:
        ValueError: If run_id is None, empty, or not a string.
    """
    if not run_id:
        raise ValueError(error_msg)
    if not isinstance(run_id, str):
        raise ValueError("Run ID must be a string")


def validate_step_id(
    step_id: Optional[str], error_msg: str = "Step ID is required"
) -> None:
    """Validates step ID format and presence.

    Args:
        step_id: The step ID to validate.
        error_msg: Custom error message for missing step ID (default: "Step ID is required").

    Raises:
        ValueError: If step_id is None, empty, or not a string.
    """
    if not step_id:
        raise ValueError(error_msg)
    if not isinstance(step_id, str):
        raise ValueError("Step ID must be a string")


def validate_thread_tool_resources(
    tool_resources: Optional[Dict[str, Any]],
    max_code_interpreter_files: int,
    max_file_search_stores: int,
    error_code_interpreter: str,
    error_file_search: str,
) -> None:
    """Validates tool resources configuration for threads.

    Checks that the number of files and vector stores in tool resources does not
    exceed the specified limits.

    Args:
        tool_resources: Dictionary containing tool configurations.
        max_code_interpreter_files: Maximum number of allowed files for code interpreter.
        max_file_search_stores: Maximum number of allowed vector stores for file search.
        error_code_interpreter: Error message for code interpreter limit violation.
        error_file_search: Error message for file search limit violation.

    Raises:
        ValueError: If the number of files or vector stores exceeds the specified limits.
    """
    if not tool_resources:
        return

    if TOOL_CODE_INTERPRETER in tool_resources:
        file_ids = tool_resources[TOOL_CODE_INTERPRETER].get(PARAM_FILE_IDS, [])
        if len(file_ids) > max_code_interpreter_files:
            raise ValueError(error_code_interpreter)

    if TOOL_FILE_SEARCH in tool_resources:
        vector_store_ids = tool_resources[TOOL_FILE_SEARCH].get(
            PARAM_VECTOR_STORE_IDS, []
        )
        vector_stores = tool_resources[TOOL_FILE_SEARCH].get(PARAM_VECTOR_STORES, [])
        if len(vector_store_ids) + len(vector_stores) > max_file_search_stores:
            raise ValueError(error_file_search)


def validate_assistant_name(name: Optional[str]) -> None:
    """Validates the length of an assistant's name.

    Args:
        name: The name to validate. Can be None.

    Raises:
        ValueError: If name length exceeds MAX_ASSISTANT_NAME_LENGTH characters.
    """
    if name and len(name) > MAX_ASSISTANT_NAME_LENGTH:
        raise ValueError(ERROR_INVALID_ASSISTANT_NAME_LENGTH)


def validate_assistant_description(description: Optional[str]) -> None:
    """Validates the length of an assistant's description.

    Args:
        description: The description to validate. Can be None.

    Raises:
        ValueError: If description length exceeds MAX_ASSISTANT_DESCRIPTION_LENGTH characters.
    """
    if description and len(description) > MAX_ASSISTANT_DESCRIPTION_LENGTH:
        raise ValueError(ERROR_INVALID_ASSISTANT_DESCRIPTION_LENGTH)


def validate_assistant_instructions(instructions: Optional[str]) -> None:
    """Validates the length of an assistant's instructions.

    Args:
        instructions: The instructions to validate. Can be None.

    Raises:
        ValueError: If instructions length exceeds MAX_ASSISTANT_INSTRUCTIONS_LENGTH characters.
    """
    if instructions and len(instructions) > MAX_ASSISTANT_INSTRUCTIONS_LENGTH:
        raise ValueError(ERROR_INVALID_ASSISTANT_INSTRUCTIONS_LENGTH)


def validate_assistant_tools(tools: Optional[List[Dict[str, Any]]]) -> None:
    """Validates the number of tools assigned to an assistant.

    Args:
        tools: List of tool configurations to validate. Can be None.
            Each tool is represented as a dictionary with tool-specific settings.

    Raises:
        ValueError: If the number of tools exceeds MAX_ASSISTANT_TOOLS_COUNT.
    """
    if tools and len(tools) > MAX_ASSISTANT_TOOLS_COUNT:
        raise ValueError(ERROR_INVALID_ASSISTANT_TOOLS_COUNT)


def validate_assistant_id(assistant_id: Optional[str]) -> None:
    """Validates the format and presence of an assistant ID.

    Args:
        assistant_id: The assistant ID to validate. Cannot be None or empty.

    Raises:
        ValueError: If assistant_id is None, empty, or not a string.
    """
    if not assistant_id:
        raise ValueError(ERROR_INVALID_ASSISTANT_ID)
    if not isinstance(assistant_id, str):
        raise ValueError(ERROR_INVALID_ASSISTANT_ID_TYPE)


def validate_n(n: Optional[int]) -> None:
    """Validates the 'n' parameter for number of completions.

    Args:
        n: The number of completions to generate. If provided, must be >= 1.

    Raises:
        ValueError: If n is less than 1.
    """
    if n is not None and n < 1:
        raise ValueError(ERROR_INVALID_N)


def validate_max_tokens(max_tokens: Optional[int]) -> None:
    """Validates the maximum number of tokens for completion.

    Args:
        max_tokens: The maximum number of tokens to generate. If provided, must be >= 1.

    Raises:
        ValueError: If max_tokens is less than 1.
    """
    if max_tokens is not None and max_tokens < 1:
        raise ValueError(ERROR_INVALID_MAX_TOKENS)


def validate_api_key(api_key: Optional[str]) -> None:
    """Validates the Azure OpenAI API key.

    Args:
        api_key: The API key to validate. Cannot be None, empty, or non-string.

    Raises:
        ValueError: If api_key is None, empty, or not a string type.
            Specific error messages are defined in ERROR_API_KEY_REQUIRED and
            ERROR_API_KEY_TYPE constants.
    """
    if not api_key:
        raise ValueError(ERROR_API_KEY_REQUIRED)
    if not isinstance(api_key, str):
        raise ValueError(ERROR_API_KEY_TYPE)


def validate_api_version(api_version: Optional[str]) -> None:
    """Validates the Azure OpenAI API version.

    Args:
        api_version: The API version to validate. Cannot be None, empty, or non-string.

    Raises:
        ValueError: If api_version is None, empty, or not a string type.
            Specific error messages are defined in ERROR_API_VERSION_REQUIRED and
            ERROR_API_VERSION_TYPE constants.
    """
    if not api_version:
        raise ValueError(ERROR_API_VERSION_REQUIRED)
    if not isinstance(api_version, str):
        raise ValueError(ERROR_API_VERSION_TYPE)


def validate_azure_endpoint(azure_endpoint: Optional[str]) -> None:
    """Validates the Azure OpenAI endpoint URL.

    Args:
        azure_endpoint: The endpoint URL to validate. Cannot be None, empty, or non-string.
            Should be in the format: https://<resource-name>.openai.azure.com/

    Raises:
        ValueError: If azure_endpoint is None, empty, or not a string type.
            Specific error messages are defined in ERROR_AZURE_ENDPOINT_REQUIRED and
            ERROR_AZURE_ENDPOINT_TYPE constants.
    """
    if not azure_endpoint:
        raise ValueError(ERROR_AZURE_ENDPOINT_REQUIRED)
    if not isinstance(azure_endpoint, str):
        raise ValueError(ERROR_AZURE_ENDPOINT_TYPE)
