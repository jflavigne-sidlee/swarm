from typing import Optional, List, Dict, Any, Union
from openai import AzureOpenAI
from .constants import (
    # DEFAULT_CHAT_MODEL,
    DEFAULT_CHAT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
    DEFAULT_N,
    DEFAULT_STREAM,
    DEFAULT_STOP,
    DEFAULT_PRESENCE_PENALTY,
    DEFAULT_FREQUENCY_PENALTY,
    DEFAULT_LOGIT_BIAS,
    DEFAULT_USER,
    DEFAULT_SEED,
    DEFAULT_CHAT_TOOLS,
    DEFAULT_CHAT_TOOL_CHOICE,
    DEFAULT_CHAT_RESPONSE_FORMAT,
    VALID_TEMPERATURE_RANGE,
    VALID_TOP_P_RANGE,
    VALID_PRESENCE_PENALTY_RANGE,
    VALID_FREQUENCY_PENALTY_RANGE,
    ERROR_INVALID_TEMPERATURE,
    ERROR_INVALID_TOP_P,
    ERROR_INVALID_PRESENCE_PENALTY,
    ERROR_INVALID_FREQUENCY_PENALTY,
    ERROR_INVALID_N,
    ERROR_INVALID_MAX_TOKENS,
    PARAM_TEMPERATURE,
    PARAM_TOP_P,
    PARAM_N,
    PARAM_STREAM,
    PARAM_STOP,
    PARAM_MAX_TOKENS,
    PARAM_PRESENCE_PENALTY,
    PARAM_FREQUENCY_PENALTY,
    PARAM_LOGIT_BIAS,
    PARAM_USER,
    PARAM_SEED,
    PARAM_TOOL_CHOICE,
    PARAM_RESPONSE_FORMAT,
    PARAM_MODEL,
    PARAM_MESSAGES,
)


class Chat:
    """Chat operations"""

    def __init__(self, client: AzureOpenAI):
        self._client = client
        self.completions = self.Completions(client)

    class Completions:
        """Chat completion operations"""

        def __init__(self, client: AzureOpenAI):
            self._client = client

        def create(
            self,
            model: str,
            messages: List[Dict[str, str]],
            temperature: Optional[float] = DEFAULT_TEMPERATURE,
            top_p: Optional[float] = DEFAULT_TOP_P,
            n: Optional[int] = DEFAULT_N,
            stream: Optional[bool] = DEFAULT_STREAM,
            stop: Optional[Union[str, List[str]]] = DEFAULT_STOP,
            max_tokens: Optional[int] = DEFAULT_CHAT_MAX_TOKENS,
            presence_penalty: Optional[float] = DEFAULT_PRESENCE_PENALTY,
            frequency_penalty: Optional[float] = DEFAULT_FREQUENCY_PENALTY,
            logit_bias: Optional[Dict[str, float]] = DEFAULT_LOGIT_BIAS,
            user: Optional[str] = DEFAULT_USER,
            seed: Optional[int] = DEFAULT_SEED,
            tools: Optional[List[Dict[str, Any]]] = DEFAULT_CHAT_TOOLS,
            tool_choice: Optional[
                Union[str, Dict[str, Any]]
            ] = DEFAULT_CHAT_TOOL_CHOICE,
            response_format: Optional[Dict[str, str]] = DEFAULT_CHAT_RESPONSE_FORMAT,
            **kwargs
        ) -> Any:
            """Creates a chat completion with validation."""

            # Validate temperature
            if (
                temperature is not None
                and not VALID_TEMPERATURE_RANGE[0]
                <= temperature
                <= VALID_TEMPERATURE_RANGE[1]
            ):
                raise ValueError(ERROR_INVALID_TEMPERATURE)

            # Validate top_p
            if (
                top_p is not None
                and not VALID_TOP_P_RANGE[0] <= top_p <= VALID_TOP_P_RANGE[1]
            ):
                raise ValueError(ERROR_INVALID_TOP_P)

            # Validate n
            if n is not None and n < 1:
                raise ValueError(ERROR_INVALID_N)

            # Validate max_tokens
            if max_tokens is not None and max_tokens < 1:
                raise ValueError(ERROR_INVALID_MAX_TOKENS)

            # Validate presence_penalty
            if (
                presence_penalty is not None
                and not VALID_PRESENCE_PENALTY_RANGE[0]
                <= presence_penalty
                <= VALID_PRESENCE_PENALTY_RANGE[1]
            ):
                raise ValueError(ERROR_INVALID_PRESENCE_PENALTY)

            # Validate frequency_penalty
            if (
                frequency_penalty is not None
                and not VALID_FREQUENCY_PENALTY_RANGE[0]
                <= frequency_penalty
                <= VALID_FREQUENCY_PENALTY_RANGE[1]
            ):
                raise ValueError(ERROR_INVALID_FREQUENCY_PENALTY)

            # Combine all parameters using the correct parameter names
            params = {
                PARAM_MODEL: model,
                PARAM_MESSAGES: messages,
                PARAM_TEMPERATURE: temperature,
                PARAM_TOP_P: top_p,
                PARAM_N: n,
                PARAM_STREAM: stream,
                PARAM_STOP: stop,
                PARAM_MAX_TOKENS: max_tokens,
                PARAM_PRESENCE_PENALTY: presence_penalty,
                PARAM_FREQUENCY_PENALTY: frequency_penalty,
                PARAM_LOGIT_BIAS: logit_bias,
                PARAM_USER: user,
                PARAM_SEED: seed,
                PARAM_TOOL_CHOICE: tool_choice,
                PARAM_RESPONSE_FORMAT: response_format,
                **kwargs,
            }

            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}

            return self._client.chat.completions.create(**params)

        # Compatibility method
        def create_chat_completion(self, *args, **kwargs) -> Any:
            """Compatibility method for create()"""
            return self.create(*args, **kwargs)
