from typing import Optional, Any
from openai import AzureOpenAI
from .constants import (
    DEFAULT_RUN_STEP_LIST_PARAMS,
    ERROR_INVALID_LIMIT,
    LIST_LIMIT_RANGE,
    PARAM_THREAD_ID,
    PARAM_RUN_ID,
    PARAM_LIMIT,
    PARAM_ORDER,
    PARAM_AFTER,
    PARAM_BEFORE,
    ERROR_INVALID_THREAD_ID,
    ERROR_INVALID_RUN_ID,
    ERROR_INVALID_STEP_ID,
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
        if not thread_id:
            raise ValueError(ERROR_INVALID_THREAD_ID)
        if not run_id:
            raise ValueError(ERROR_INVALID_RUN_ID)
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
        params = {k: v for k, v in params.items() if v is not None}

        return self._client.beta.threads.runs.steps.list(**params)

    def retrieve(self, thread_id: str, run_id: str, step_id: str) -> Any:
        """Retrieves a run step."""
        if not thread_id:
            raise ValueError(ERROR_INVALID_THREAD_ID)
        if not run_id:
            raise ValueError(ERROR_INVALID_RUN_ID)
        if not step_id:
            raise ValueError(ERROR_INVALID_STEP_ID)

        return self._client.beta.threads.runs.steps.retrieve(
            thread_id=thread_id, run_id=run_id, step_id=step_id
        )
