from typing import Optional, List, Dict, Any, Union
from openai import AzureOpenAI, AssistantEventHandler
from .types import TruncationStrategy
from .constants import (
    DEFAULT_INSTRUCTIONS,
    DEFAULT_RUN_LIST_PARAMS,
    DEFAULT_RUN_STEP_LIST_PARAMS,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
    DEFAULT_STREAM,
    DEFAULT_MAX_PROMPT_TOKENS,
    DEFAULT_MAX_COMPLETION_TOKENS,
    DEFAULT_TRUNCATION_STRATEGY,
    DEFAULT_TOOL_CHOICE,
    DEFAULT_RUN_RESPONSE_FORMAT,
    ERROR_INVALID_LIMIT,
    ERROR_INVALID_TEMPERATURE,
    ERROR_INVALID_TOP_P,
    ERROR_INVALID_THREAD_ID,
    ERROR_INVALID_RUN_ID,
    LIST_LIMIT_RANGE,
    PARAM_LIMIT,
    PARAM_ORDER,
    PARAM_AFTER,
    PARAM_BEFORE,
    VALID_TEMPERATURE_RANGE,
    VALID_TOP_P_RANGE,
    PARAM_THREAD_ID,
    PARAM_ASSISTANT_ID,
    PARAM_MODEL,
    PARAM_INSTRUCTIONS,
    PARAM_ADDITIONAL_INSTRUCTIONS,
    PARAM_ADDITIONAL_MESSAGES,
    PARAM_TOOLS,
    PARAM_METADATA,
    PARAM_RUN_ID,
    PARAM_TEMPERATURE,
    PARAM_TOP_P,
    PARAM_STREAM,
    PARAM_MAX_PROMPT_TOKENS,
    PARAM_MAX_COMPLETION_TOKENS,
    PARAM_TRUNCATION_STRATEGY,
    PARAM_TOOL_CHOICE,
    PARAM_RESPONSE_FORMAT,
    DEFAULT_THREAD_MESSAGES,
    DEFAULT_PARAMS,
    ERROR_INVALID_ASSISTANT_ID,
    PARAM_MESSAGES,
)
from .steps import RunSteps


class Runs:
    """Run operations"""

    def __init__(self, client: AzureOpenAI):
        self._client = client
        self.steps = RunSteps(client)

    def create(self, thread_id: str, assistant_id: str, **kwargs) -> Any:
        """Creates a run."""
        if not thread_id:
            raise ValueError(ERROR_INVALID_THREAD_ID)
        if not assistant_id:
            raise ValueError(ERROR_INVALID_ASSISTANT_ID)

        default_params = DEFAULT_PARAMS["run"].copy()
        default_params.update(kwargs)

        return self._client.beta.threads.runs.create(
            thread_id=thread_id, assistant_id=assistant_id, **default_params
        )

    def list(
        self,
        thread_id: str,
        limit: Optional[int] = DEFAULT_RUN_LIST_PARAMS[PARAM_LIMIT],
        order: Optional[str] = DEFAULT_RUN_LIST_PARAMS[PARAM_ORDER],
        after: Optional[str] = DEFAULT_RUN_LIST_PARAMS[PARAM_AFTER],
        before: Optional[str] = DEFAULT_RUN_LIST_PARAMS[PARAM_BEFORE],
    ) -> Any:
        """Returns a list of runs belonging to a thread."""
        if limit and limit not in LIST_LIMIT_RANGE:
            raise ValueError(ERROR_INVALID_LIMIT)

        params = {
            PARAM_THREAD_ID: thread_id,
            PARAM_LIMIT: limit,
            PARAM_ORDER: order,
            PARAM_AFTER: after,
            PARAM_BEFORE: before,
        }
        params = {k: v for k, v in params.items() if v is not None}

        return self._client.beta.threads.runs.list(**params)

    def retrieve(self, thread_id: str, run_id: str) -> Any:
        """Retrieves a run."""
        if not thread_id:
            raise ValueError(ERROR_INVALID_THREAD_ID)
        if not run_id:
            raise ValueError(ERROR_INVALID_RUN_ID)

        return self._client.beta.threads.runs.retrieve(
            thread_id=thread_id, run_id=run_id
        )

    def update(self, thread_id: str, run_id: str, metadata: Dict[str, str]) -> Any:
        """Modifies a run."""
        if not thread_id:
            raise ValueError(ERROR_INVALID_THREAD_ID)
        if not run_id:
            raise ValueError(ERROR_INVALID_RUN_ID)

        params = {
            PARAM_THREAD_ID: thread_id,
            PARAM_RUN_ID: run_id,
            PARAM_METADATA: metadata,
        }
        params = {k: v for k, v in params.items() if v is not None}

        return self._client.beta.threads.runs.update(**params)

    def submit_tool_outputs(
        self,
        thread_id: str,
        run_id: str,
        tool_outputs: List[Dict[str, Any]],
        stream: Optional[bool] = None,
    ) -> Any:
        """Submits outputs for tool calls."""
        if not thread_id:
            raise ValueError(ERROR_INVALID_THREAD_ID)
        if not run_id:
            raise ValueError(ERROR_INVALID_RUN_ID)

        return self._client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread_id, run_id=run_id, tool_outputs=tool_outputs, stream=stream
        )

    def cancel(self, thread_id: str, run_id: str) -> Any:
        """Cancels a run that is in_progress."""
        if not thread_id:
            raise ValueError(ERROR_INVALID_THREAD_ID)
        if not run_id:
            raise ValueError(ERROR_INVALID_RUN_ID)

        return self._client.beta.threads.runs.cancel(thread_id=thread_id, run_id=run_id)

    def stream(
        self,
        thread_id: str,
        assistant_id: str,
        event_handler: AssistantEventHandler,
        **run_params
    ) -> Any:
        """Stream the result of executing a Run."""
        if not thread_id:
            raise ValueError(ERROR_INVALID_THREAD_ID)
        if not assistant_id:
            raise ValueError(ERROR_INVALID_ASSISTANT_ID)

        # Remove run_id from run_params if present as it's not needed
        run_params.pop(PARAM_RUN_ID, None)

        # Apply default run parameters
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
        """Creates a thread and run in one operation."""
        if not assistant_id:
            raise ValueError(ERROR_INVALID_ASSISTANT_ID)

        # Create thread parameters, only including messages
        thread_params = (
            {PARAM_MESSAGES: thread.get(PARAM_MESSAGES, DEFAULT_THREAD_MESSAGES)}
            if thread
            else None
        )

        # Apply default run parameters
        default_params = DEFAULT_PARAMS["run"].copy()
        default_params.update(run_params)

        return self._client.beta.threads.create_and_run(
            assistant_id=assistant_id, thread=thread_params, **default_params
        )

    # Compatibility methods
    def create_run(self, *args, **kwargs) -> Any:
        """Compatibility method for create()"""
        return self.create(*args, **kwargs)

    def list_runs(self, *args, **kwargs) -> Any:
        """Compatibility method for list()"""
        return self.list(*args, **kwargs)

    def retrieve_run(self, *args, **kwargs) -> Any:
        """Compatibility method for retrieve()"""
        return self.retrieve(*args, **kwargs)

    def update_run(self, *args, **kwargs) -> Any:
        """Compatibility method for update()"""
        return self.update(*args, **kwargs)

    def submit_tool_outputs_to_run(self, *args, **kwargs) -> Any:
        """Compatibility method for submit_tool_outputs()"""
        return self.submit_tool_outputs(*args, **kwargs)

    def cancel_run(self, *args, **kwargs) -> Any:
        """Compatibility method for cancel()"""
        return self.cancel(*args, **kwargs)

    def list_run_steps(self, *args, **kwargs) -> Any:
        """Compatibility method for steps.list()"""
        return self.steps.list(*args, **kwargs)

    def retrieve_run_step(self, *args, **kwargs) -> Any:
        """Compatibility method for steps.retrieve()"""
        return self.steps.retrieve(*args, **kwargs)
