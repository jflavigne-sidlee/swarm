from typing import Optional, List, Dict, Any, Union
from openai import AzureOpenAI
from .utils import (
    validate_temperature,
    validate_top_p,
    validate_presence_penalty,
    validate_frequency_penalty,
    validate_n,
    validate_max_tokens,
    clean_params,
)
from .constants import (
    # DEFAULT_CHAT_MODEL,
    DEFAULT_CHAT_MAX_TOKENS,
    DEFAULT_CHAT_RESPONSE_FORMAT,
    DEFAULT_CHAT_TOOL_CHOICE,
    DEFAULT_CHAT_TOOLS,
    DEFAULT_FREQUENCY_PENALTY,
    DEFAULT_LOGIT_BIAS,
    DEFAULT_N,
    DEFAULT_PRESENCE_PENALTY,
    DEFAULT_SEED,
    DEFAULT_STOP,
    DEFAULT_STREAM,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
    DEFAULT_USER,
    PARAM_FREQUENCY_PENALTY,
    PARAM_LOGIT_BIAS,
    PARAM_MAX_TOKENS,
    PARAM_MESSAGES,
    PARAM_MODEL,
    PARAM_N,
    PARAM_PRESENCE_PENALTY,
    PARAM_RESPONSE_FORMAT,
    PARAM_SEED,
    PARAM_STOP,
    PARAM_STREAM,
    PARAM_TEMPERATURE,
    PARAM_TOOL_CHOICE,
    PARAM_TOOLS,
    PARAM_TOP_P,
    PARAM_USER,
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

            # Validate parameters using utility functions
            validate_temperature(temperature)
            validate_top_p(top_p)
            validate_presence_penalty(presence_penalty)
            validate_frequency_penalty(frequency_penalty)
            validate_n(n)
            validate_max_tokens(max_tokens)

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
                PARAM_TOOLS: tools,
                PARAM_TOOL_CHOICE: tool_choice,
                PARAM_RESPONSE_FORMAT: response_format,
                **kwargs,
            }

            return self._client.chat.completions.create(**clean_params(params))

        # Compatibility method
        def create_chat_completion(self, *args, **kwargs) -> Any:
            """Compatibility method for create()"""
            return self.create(*args, **kwargs)
