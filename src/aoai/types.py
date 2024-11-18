"""Azure OpenAI type definitions.

This module provides type definitions and enumerations used throughout the Azure OpenAI
client library. It includes enums for order direction, message roles, truncation types,
tool types, and run statuses, as well as TypedDict definitions for tool resources
and truncation strategies.

Typical usage example:
    from aoai.types import MessageRole, RunStatus, ToolResources
    
    message_role = MessageRole.USER
    run_status = RunStatus.COMPLETED
    tool_resources: ToolResources = {
        "code_interpreter": {"files": ["file1.py"]},
        "file_search": {"stores": ["store1"]}
    }
"""

from enum import Enum
from typing import TypedDict, Optional, Dict, List, Union

from .constants import (
    ORDER_ASC,
    ORDER_DESC,
    MESSAGE_ROLE_USER,
    MESSAGE_ROLE_ASSISTANT,
    TRUNCATION_TYPE_AUTO,
    TRUNCATION_TYPE_LAST_MESSAGES,
    TOOL_TYPE_CODE_INTERPRETER,
    TOOL_TYPE_FILE_SEARCH,
    TOOL_TYPE_FUNCTION,
    RUN_STATUS_QUEUED,
    RUN_STATUS_IN_PROGRESS,
    RUN_STATUS_REQUIRES_ACTION,
    RUN_STATUS_CANCELLING,
    RUN_STATUS_CANCELLED,
    RUN_STATUS_FAILED,
    RUN_STATUS_COMPLETED,
    RUN_STATUS_EXPIRED,
)


class OrderDirection(str, Enum):
    """Sort order for list operations.
    
    Attributes:
        ASC: Ascending order (oldest first).
        DESC: Descending order (newest first).
    """

    ASC = ORDER_ASC
    DESC = ORDER_DESC


class MessageRole(str, Enum):
    """Available roles for messages.
    
    Attributes:
        USER: Message from the user.
        ASSISTANT: Message from the assistant.
    """

    USER = MESSAGE_ROLE_USER
    ASSISTANT = MESSAGE_ROLE_ASSISTANT


class TruncationType(str, Enum):
    """Available truncation types.
    
    Attributes:
        AUTO: Automatic truncation based on context length.
        LAST_MESSAGES: Keep only the specified number of most recent messages.
    """

    AUTO = TRUNCATION_TYPE_AUTO
    LAST_MESSAGES = TRUNCATION_TYPE_LAST_MESSAGES


class ToolType(str, Enum):
    """Available tool types.
    
    Attributes:
        CODE_INTERPRETER: Tool for executing code.
        FILE_SEARCH: Tool for searching through files.
        FUNCTION: Tool for calling functions.
    """

    CODE_INTERPRETER = TOOL_TYPE_CODE_INTERPRETER
    FILE_SEARCH = TOOL_TYPE_FILE_SEARCH
    FUNCTION = TOOL_TYPE_FUNCTION


class RunStatus(str, Enum):
    """Available run statuses.
    
    Attributes:
        QUEUED: Run is queued for execution.
        IN_PROGRESS: Run is currently executing.
        REQUIRES_ACTION: Run needs user action to proceed.
        CANCELLING: Run is in the process of being cancelled.
        CANCELLED: Run has been cancelled.
        FAILED: Run has failed.
        COMPLETED: Run has completed successfully.
        EXPIRED: Run has expired.
    """

    QUEUED = RUN_STATUS_QUEUED
    IN_PROGRESS = RUN_STATUS_IN_PROGRESS
    REQUIRES_ACTION = RUN_STATUS_REQUIRES_ACTION
    CANCELLING = RUN_STATUS_CANCELLING
    CANCELLED = RUN_STATUS_CANCELLED
    FAILED = RUN_STATUS_FAILED
    COMPLETED = RUN_STATUS_COMPLETED
    EXPIRED = RUN_STATUS_EXPIRED


class ToolResources(TypedDict, total=False):
    """Resources configuration for tools.
    
    A TypedDict defining the structure of tool resources configuration.
    All fields are optional.

    Attributes:
        code_interpreter: Configuration for code interpreter tool.
            Dictionary with string keys and lists of strings as values.
        file_search: Configuration for file search tool.
            Dictionary with string keys and lists of strings as values.
    """

    code_interpreter: Dict[str, List[str]]
    file_search: Dict[str, List[str]]


class TruncationStrategy(TypedDict):
    """Strategy for message truncation.
    
    A TypedDict defining how messages should be truncated when context length
    is exceeded.

    Attributes:
        type: The type of truncation to apply (from TruncationType).
        last_messages: Optional number of messages to keep when using LAST_MESSAGES type.
    """

    type: str  # TruncationType
    last_messages: Optional[int]
