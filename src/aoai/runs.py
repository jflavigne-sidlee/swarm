"""Azure OpenAI Run operations.

This module provides functionality for managing runs within threads, including
creation, retrieval, listing, updating, and streaming of runs. Runs represent
the execution of an assistant's instructions within a thread.

Typical usage example:
    client = AOAIClient.create(...)
    runs = Runs(client)
    run = runs.create(
        thread_id="thread_123",
        assistant_id="asst_abc"
    )
"""

from typing import Optional, List, Dict, Any, Union
from openai import AzureOpenAI, AssistantEventHandler
from .types import TruncationStrategy
from .utils import (
    clean_params,
    validate_thread_id,
    validate_run_id,
    validate_metadata,
    validate_temperature,
    validate_top_p,
)
from .constants import (
    DEFAULT_PARAMS,
    DEFAULT_RUN_LIST_PARAMS,
    DEFAULT_THREAD_MESSAGES,
    ERROR_INVALID_ASSISTANT_ID,
    ERROR_INVALID_LIMIT,
    ERROR_INVALID_RUN_ID,
    ERROR_INVALID_THREAD_ID,
    LIST_LIMIT_RANGE,
    PARAM_AFTER,
    PARAM_BEFORE,
    PARAM_LIMIT,
    PARAM_MESSAGES,
    PARAM_METADATA,
    PARAM_ORDER,
    PARAM_RUN_ID,
    PARAM_TEMPERATURE,
    PARAM_THREAD_ID,
    PARAM_TOP_P,
)
from .steps import RunSteps


class Runs:
    """Manages run operations in Azure OpenAI.
    
    This class provides methods for creating, listing, retrieving, updating,
    and managing runs within threads. Runs represent the execution of an
    assistant's instructions.

    Attributes:
        _client: An instance of AzureOpenAI client.
        steps: An instance of RunSteps for managing run steps.
    """

    def __init__(self, client: AzureOpenAI):
        """Initialize the Runs manager.

        Args:
            client: An instance of AzureOpenAI client.
        """
        self._client = client
        self.steps = RunSteps(client)

    def create(self, thread_id: str, assistant_id: str, **kwargs) -> Any:
        """Creates a new run in a thread.

        Args:
            thread_id: The ID of the thread to create the run in.
            assistant_id: The ID of the assistant to use for the run.
            **kwargs: Additional parameters including temperature and top_p.

        Returns:
            The created run object.

        Raises:
            ValueError: If thread_id or assistant_id is invalid, or if temperature/top_p are out of range.
        """
        validate_thread_id(thread_id, ERROR_INVALID_THREAD_ID)
        if not assistant_id:
            raise ValueError(ERROR_INVALID_ASSISTANT_ID)

        if PARAM_TEMPERATURE in kwargs:
            validate_temperature(kwargs[PARAM_TEMPERATURE])
        if PARAM_TOP_P in kwargs:
            validate_top_p(kwargs[PARAM_TOP_P])

        default_params = DEFAULT_PARAMS["run"].copy()
        default_params.update(kwargs)

        return self._client.beta.threads.runs.create(
            thread_id=thread_id, assistant_id=assistant_id, **clean_params(default_params)
        )

    def list(
        self,
        thread_id: str,
        limit: Optional[int] = DEFAULT_RUN_LIST_PARAMS[PARAM_LIMIT],
        order: Optional[str] = DEFAULT_RUN_LIST_PARAMS[PARAM_ORDER],
        after: Optional[str] = DEFAULT_RUN_LIST_PARAMS[PARAM_AFTER],
        before: Optional[str] = DEFAULT_RUN_LIST_PARAMS[PARAM_BEFORE],
    ) -> Any:
        """Lists runs in a thread with pagination support.

        Args:
            thread_id: The ID of the thread to list runs from.
            limit: Maximum number of runs to return.
            order: Sort order for results.
            after: Return results after this ID.
            before: Return results before this ID.

        Returns:
            A list of run objects.

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
        }

        return self._client.beta.threads.runs.list(**clean_params(params))

    def retrieve(self, thread_id: str, run_id: str) -> Any:
        """Retrieves a specific run from a thread.

        Args:
            thread_id: The ID of the thread containing the run.
            run_id: The ID of the run to retrieve.

        Returns:
            The run object.

        Raises:
            ValueError: If thread_id or run_id is invalid.
        """
        validate_thread_id(thread_id, ERROR_INVALID_THREAD_ID)
        validate_run_id(run_id, ERROR_INVALID_RUN_ID)

        return self._client.beta.threads.runs.retrieve(
            thread_id=thread_id, run_id=run_id
        )

    def update(self, thread_id: str, run_id: str, metadata: Dict[str, str]) -> Any:
        """Updates a run's metadata.

        Args:
            thread_id: The ID of the thread containing the run.
            run_id: The ID of the run to update.
            metadata: New metadata for the run.

        Returns:
            The updated run object.

        Raises:
            ValueError: If thread_id, run_id is invalid or metadata format is incorrect.
        """
        validate_thread_id(thread_id, ERROR_INVALID_THREAD_ID)
        validate_run_id(run_id, ERROR_INVALID_RUN_ID)
        if metadata:
            validate_metadata(metadata)

        params = {
            PARAM_THREAD_ID: thread_id,
            PARAM_RUN_ID: run_id,
            PARAM_METADATA: metadata,
        }

        return self._client.beta.threads.runs.update(**clean_params(params))

    def submit_tool_outputs(
        self,
        thread_id: str,
        run_id: str,
        tool_outputs: List[Dict[str, Any]],
        stream: Optional[bool] = None,
    ) -> Any:
        """Submits outputs for tool calls during a run.

        Args:
            thread_id: The ID of the thread containing the run.
            run_id: The ID of the run.
            tool_outputs: List of tool outputs to submit.
            stream: Whether to stream the response.

        Returns:
            The updated run object.

        Raises:
            ValueError: If thread_id or run_id is invalid.
        """
        validate_thread_id(thread_id, ERROR_INVALID_THREAD_ID)
        validate_run_id(run_id, ERROR_INVALID_RUN_ID)

        return self._client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread_id, run_id=run_id, tool_outputs=tool_outputs, stream=stream
        )

    def cancel(self, thread_id: str, run_id: str) -> Any:
        """Cancels an in-progress run.

        Args:
            thread_id: The ID of the thread containing the run.
            run_id: The ID of the run to cancel.

        Returns:
            The cancelled run object.

        Raises:
            ValueError: If thread_id or run_id is invalid.
        """
        validate_thread_id(thread_id, ERROR_INVALID_THREAD_ID)
        validate_run_id(run_id, ERROR_INVALID_RUN_ID)

        return self._client.beta.threads.runs.cancel(thread_id=thread_id, run_id=run_id)

    def stream(
        self,
        thread_id: str,
        assistant_id: str,
        event_handler: AssistantEventHandler,
        **run_params
    ) -> Any:
        """Streams the execution of a run.

        Args:
            thread_id: The ID of the thread.
            assistant_id: The ID of the assistant.
            event_handler: Handler for streaming events.
            **run_params: Additional parameters for the run.

        Returns:
            The streaming response.

        Raises:
            ValueError: If thread_id or assistant_id is invalid.
        """
        if not thread_id:
            raise ValueError(ERROR_INVALID_THREAD_ID)
        if not assistant_id:
            raise ValueError(ERROR_INVALID_ASSISTANT_ID)

        run_params.pop(PARAM_RUN_ID, None)
        default_params = DEFAULT_PARAMS["run"].copy()
        default_params.update(run_params)

        return self._client.beta.threads.runs.stream(
            thread_id=thread_id,
            assistant_id=assistant_id,
            event_handler=event_handler,
            **default_params
        )

    def create_thread_and_run(
        self, assistant_id: str, thread: Optional[Dict[str, Any]] = None, **run_params
    ) -> Any:
        """Creates a thread and starts a run in one operation.

        Args:
            assistant_id: The ID of the assistant to use.
            thread: Optional thread configuration.
            **run_params: Additional parameters for the run.

        Returns:
            A tuple of (thread, run) objects.

        Raises:
            ValueError: If assistant_id is invalid.
        """
        if not assistant_id:
            raise ValueError(ERROR_INVALID_ASSISTANT_ID)

        thread_params = (
            {PARAM_MESSAGES: thread.get(PARAM_MESSAGES, DEFAULT_THREAD_MESSAGES)}
            if thread
            else None
        )

        default_params = DEFAULT_PARAMS["run"].copy()
        default_params.update(run_params)

        return self._client.beta.threads.create_and_run(
            assistant_id=assistant_id, thread=thread_params, **default_params
        )

    # Compatibility methods
    def create_run(self, *args, **kwargs) -> Any:
        """Compatibility method for create().

        See create() for full documentation.

        Returns:
            The created run object.
        """
        return self.create(*args, **kwargs)

    def list_runs(self, *args, **kwargs) -> Any:
        """Compatibility method for list().

        See list() for full documentation.

        Returns:
            A list of run objects.
        """
        return self.list(*args, **kwargs)

    def retrieve_run(self, *args, **kwargs) -> Any:
        """Compatibility method for retrieve().

        See retrieve() for full documentation.

        Returns:
            The run object.
        """
        return self.retrieve(*args, **kwargs)

    def update_run(self, *args, **kwargs) -> Any:
        """Compatibility method for update().

        See update() for full documentation.

        Returns:
            The updated run object.
        """
        return self.update(*args, **kwargs)

    def submit_tool_outputs_to_run(self, *args, **kwargs) -> Any:
        """Compatibility method for submit_tool_outputs().

        See submit_tool_outputs() for full documentation.

        Returns:
            The updated run object.
        """
        return self.submit_tool_outputs(*args, **kwargs)

    def cancel_run(self, *args, **kwargs) -> Any:
        """Compatibility method for cancel().

        See cancel() for full documentation.

        Returns:
            The cancelled run object.
        """
        return self.cancel(*args, **kwargs)

    def list_run_steps(self, *args, **kwargs) -> Any:
        """Compatibility method for steps.list().

        See RunSteps.list() for full documentation.

        Returns:
            A list of run step objects.
        """
        return self.steps.list(*args, **kwargs)

    def retrieve_run_step(self, *args, **kwargs) -> Any:
        """Compatibility method for steps.retrieve().

        See RunSteps.retrieve() for full documentation.

        Returns:
            The run step object.
        """
        return self.steps.retrieve(*args, **kwargs)
