"""Azure OpenAI Run Steps operations.

This module provides functionality for managing run steps within threads and runs,
including listing and retrieving individual steps. Run steps represent the detailed
execution stages of an assistant's run.

Typical usage example:
    client = AOAIClient.create(...)
    run_steps = RunSteps(client)
    steps = run_steps.list(
        thread_id="thread_123",
        run_id="run_abc"
    )
"""

from typing import Optional, Any
from openai import AzureOpenAI
from .utils import (
    clean_params,
    validate_thread_id,
    validate_run_id,
    validate_step_id,
)
from .constants import (
    DEFAULT_RUN_STEP_LIST_PARAMS,
    ERROR_INVALID_LIMIT,
    ERROR_INVALID_STEP_ID,
    ERROR_INVALID_THREAD_ID,
    ERROR_INVALID_RUN_ID,
    LIST_LIMIT_RANGE,
    PARAM_AFTER,
    PARAM_BEFORE,
    PARAM_LIMIT,
    PARAM_ORDER,
    PARAM_RUN_ID,
    PARAM_THREAD_ID,
)


class RunSteps:
    """Manages run step operations in Azure OpenAI.
    
    This class provides methods for listing and retrieving run steps, which represent
    the individual stages of execution within a run.

    Attributes:
        _client: An instance of AzureOpenAI client.
    """

    def __init__(self, client: AzureOpenAI):
        """Initialize the RunSteps manager.

        Args:
            client: An instance of AzureOpenAI client.
        """
        self._client = client

    def list(
        self,
        thread_id: str,
        run_id: str,
        limit: Optional[int] = DEFAULT_RUN_STEP_LIST_PARAMS[PARAM_LIMIT],
        order: Optional[str] = DEFAULT_RUN_STEP_LIST_PARAMS[PARAM_ORDER],
        after: Optional[str] = DEFAULT_RUN_STEP_LIST_PARAMS[PARAM_AFTER],
        before: Optional[str] = DEFAULT_RUN_STEP_LIST_PARAMS[PARAM_BEFORE],
    ) -> Any:
        """Lists run steps in a run with pagination support.

        Args:
            thread_id: The ID of the thread containing the run.
            run_id: The ID of the run to list steps from.
            limit: Maximum number of steps to return (default: from DEFAULT_RUN_STEP_LIST_PARAMS).
            order: Sort order for results (default: from DEFAULT_RUN_STEP_LIST_PARAMS).
            after: Return results after this ID (default: from DEFAULT_RUN_STEP_LIST_PARAMS).
            before: Return results before this ID (default: from DEFAULT_RUN_STEP_LIST_PARAMS).

        Returns:
            A list of run step objects.

        Raises:
            ValueError: If thread_id or run_id is invalid, or if limit is outside valid range.
        """
        validate_thread_id(thread_id, ERROR_INVALID_THREAD_ID)
        validate_run_id(run_id, ERROR_INVALID_RUN_ID)
        if limit and limit not in LIST_LIMIT_RANGE:
            raise ValueError(ERROR_INVALID_LIMIT)

        params = {
            PARAM_THREAD_ID: thread_id,
            PARAM_RUN_ID: run_id,
            PARAM_LIMIT: limit,
            PARAM_ORDER: order,
            PARAM_AFTER: after,
            PARAM_BEFORE: before,
        }

        return self._client.beta.threads.runs.steps.list(**clean_params(params))

    def retrieve(self, thread_id: str, run_id: str, step_id: str) -> Any:
        """Retrieves a specific run step.

        Args:
            thread_id: The ID of the thread containing the run.
            run_id: The ID of the run containing the step.
            step_id: The ID of the step to retrieve.

        Returns:
            The run step object.

        Raises:
            ValueError: If thread_id, run_id, or step_id is invalid.
        """
        validate_thread_id(thread_id, ERROR_INVALID_THREAD_ID)
        validate_run_id(run_id, ERROR_INVALID_RUN_ID)
        validate_step_id(step_id, ERROR_INVALID_STEP_ID)

        return self._client.beta.threads.runs.steps.retrieve(
            thread_id=thread_id, run_id=run_id, step_id=step_id
        )
