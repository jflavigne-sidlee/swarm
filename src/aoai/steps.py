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
    """Run step operations"""

    def __init__(self, client: AzureOpenAI):
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
        """Returns a list of run steps belonging to a run."""
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
        """Retrieves a run step."""
        validate_thread_id(thread_id, ERROR_INVALID_THREAD_ID)
        validate_run_id(run_id, ERROR_INVALID_RUN_ID)
        validate_step_id(step_id, ERROR_INVALID_STEP_ID)

        return self._client.beta.threads.runs.steps.retrieve(
            thread_id=thread_id, run_id=run_id, step_id=step_id
        )
