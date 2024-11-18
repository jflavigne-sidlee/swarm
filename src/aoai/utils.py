"""Utility functions for Azure OpenAI operations."""

from typing import Dict, Any, Optional, List
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
    """Validates metadata dictionary against constraints."""
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
    """Validates temperature parameter."""
    if (
        temperature is not None
        and not VALID_TEMPERATURE_RANGE[0] <= temperature <= VALID_TEMPERATURE_RANGE[1]
    ):
        raise ValueError(ERROR_INVALID_TEMPERATURE)


def validate_top_p(top_p: Optional[float]) -> None:
    """Validates top_p parameter."""
    if top_p is not None and not VALID_TOP_P_RANGE[0] <= top_p <= VALID_TOP_P_RANGE[1]:
        raise ValueError(ERROR_INVALID_TOP_P)


def validate_presence_penalty(presence_penalty: Optional[float]) -> None:
    """Validates presence_penalty parameter."""
    if (
        presence_penalty is not None
        and not VALID_PRESENCE_PENALTY_RANGE[0]
        <= presence_penalty
        <= VALID_PRESENCE_PENALTY_RANGE[1]
    ):
        raise ValueError(ERROR_INVALID_PRESENCE_PENALTY)


def validate_frequency_penalty(frequency_penalty: Optional[float]) -> None:
    """Validates frequency_penalty parameter."""
    if (
        frequency_penalty is not None
        and not VALID_FREQUENCY_PENALTY_RANGE[0]
        <= frequency_penalty
        <= VALID_FREQUENCY_PENALTY_RANGE[1]
    ):
        raise ValueError(ERROR_INVALID_FREQUENCY_PENALTY)


def clean_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Removes None values from parameters dictionary."""
    return {k: v for k, v in params.items() if v is not None}


def validate_vector_store_id(vector_store_id: Optional[str]) -> None:
    """Validates vector store ID."""
    if not vector_store_id:
        raise ValueError("Vector store ID is required")
    if not isinstance(vector_store_id, str):
        raise ValueError("Vector store ID must be a string")


def validate_files(files: Optional[list]) -> None:
    """Validates files list for vector store operations."""
    if not files:
        raise ValueError("Files list cannot be empty")
    if not isinstance(files, list):
        raise ValueError("Files must be provided as a list")
    if not all(isinstance(f, (str, bytes, dict)) for f in files):
        raise ValueError("Each file must be a string path, bytes, or file object")


def validate_thread_id(
    thread_id: Optional[str], error_msg: str = "Thread ID is required"
) -> None:
    """Validates thread ID."""
    if not thread_id:
        raise ValueError(error_msg)
    if not isinstance(thread_id, str):
        raise ValueError("Thread ID must be a string")


def validate_message_id(
    message_id: Optional[str], error_msg: str = "Message ID is required"
) -> None:
    """Validates message ID."""
    if not message_id:
        raise ValueError(error_msg)
    if not isinstance(message_id, str):
        raise ValueError("Message ID must be a string")


def validate_run_id(
    run_id: Optional[str], error_msg: str = "Run ID is required"
) -> None:
    """Validates run ID."""
    if not run_id:
        raise ValueError(error_msg)
    if not isinstance(run_id, str):
        raise ValueError("Run ID must be a string")


def validate_step_id(
    step_id: Optional[str], error_msg: str = "Step ID is required"
) -> None:
    """Validates step ID."""
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
    """Validates thread tool resources."""
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
    """Validates assistant name length."""
    if name and len(name) > MAX_ASSISTANT_NAME_LENGTH:
        raise ValueError(ERROR_INVALID_ASSISTANT_NAME_LENGTH)


def validate_assistant_description(description: Optional[str]) -> None:
    """Validates assistant description length."""
    if description and len(description) > MAX_ASSISTANT_DESCRIPTION_LENGTH:
        raise ValueError(ERROR_INVALID_ASSISTANT_DESCRIPTION_LENGTH)


def validate_assistant_instructions(instructions: Optional[str]) -> None:
    """Validates assistant instructions length."""
    if instructions and len(instructions) > MAX_ASSISTANT_INSTRUCTIONS_LENGTH:
        raise ValueError(ERROR_INVALID_ASSISTANT_INSTRUCTIONS_LENGTH)


def validate_assistant_tools(tools: Optional[List[Dict[str, Any]]]) -> None:
    """Validates assistant tools count."""
    if tools and len(tools) > MAX_ASSISTANT_TOOLS_COUNT:
        raise ValueError(ERROR_INVALID_ASSISTANT_TOOLS_COUNT)


def validate_assistant_id(assistant_id: Optional[str]) -> None:
    """Validates assistant ID."""
    if not assistant_id:
        raise ValueError(ERROR_INVALID_ASSISTANT_ID)
    if not isinstance(assistant_id, str):
        raise ValueError(ERROR_INVALID_ASSISTANT_ID_TYPE)


def validate_n(n: Optional[int]) -> None:
    """Validates n parameter."""
    if n is not None and n < 1:
        raise ValueError(ERROR_INVALID_N)


def validate_max_tokens(max_tokens: Optional[int]) -> None:
    """Validates max_tokens parameter."""
    if max_tokens is not None and max_tokens < 1:
        raise ValueError(ERROR_INVALID_MAX_TOKENS)


def validate_api_key(api_key: Optional[str]) -> None:
    """Validates API key."""
    if not api_key:
        raise ValueError(ERROR_API_KEY_REQUIRED)
    if not isinstance(api_key, str):
        raise ValueError(ERROR_API_KEY_TYPE)


def validate_api_version(api_version: Optional[str]) -> None:
    """Validates API version."""
    if not api_version:
        raise ValueError(ERROR_API_VERSION_REQUIRED)
    if not isinstance(api_version, str):
        raise ValueError(ERROR_API_VERSION_TYPE)


def validate_azure_endpoint(azure_endpoint: Optional[str]) -> None:
    """Validates Azure endpoint."""
    if not azure_endpoint:
        raise ValueError(ERROR_AZURE_ENDPOINT_REQUIRED)
    if not isinstance(azure_endpoint, str):
        raise ValueError(ERROR_AZURE_ENDPOINT_TYPE)
