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
    """Sort order for list operations"""

    ASC = ORDER_ASC
    DESC = ORDER_DESC


class MessageRole(str, Enum):
    """Available roles for messages"""

    USER = MESSAGE_ROLE_USER
    ASSISTANT = MESSAGE_ROLE_ASSISTANT


class TruncationType(str, Enum):
    """Available truncation types"""

    AUTO = TRUNCATION_TYPE_AUTO
    LAST_MESSAGES = TRUNCATION_TYPE_LAST_MESSAGES


class ToolType(str, Enum):
    """Available tool types"""

    CODE_INTERPRETER = TOOL_TYPE_CODE_INTERPRETER
    FILE_SEARCH = TOOL_TYPE_FILE_SEARCH
    FUNCTION = TOOL_TYPE_FUNCTION


class RunStatus(str, Enum):
    """Available run statuses"""

    QUEUED = RUN_STATUS_QUEUED
    IN_PROGRESS = RUN_STATUS_IN_PROGRESS
    REQUIRES_ACTION = RUN_STATUS_REQUIRES_ACTION
    CANCELLING = RUN_STATUS_CANCELLING
    CANCELLED = RUN_STATUS_CANCELLED
    FAILED = RUN_STATUS_FAILED
    COMPLETED = RUN_STATUS_COMPLETED
    EXPIRED = RUN_STATUS_EXPIRED


class ToolResources(TypedDict, total=False):
    code_interpreter: Dict[str, List[str]]
    file_search: Dict[str, List[str]]


class TruncationStrategy(TypedDict):
    type: str  # TruncationType
    last_messages: Optional[int]
