from typing import Optional, Dict, Any
from openai import AzureOpenAI
from .constants import (
    DEFAULT_MESSAGE_LIST_PARAMS,
    LIST_PARAM_LIMIT,
    LIST_PARAM_ORDER,
    LIST_PARAM_AFTER,
    LIST_PARAM_BEFORE,
    LIST_LIMIT_RANGE,
    ERROR_INVALID_LIMIT,
    ERROR_INVALID_MESSAGE_ID,
    DEFAULT_MESSAGE_METADATA
)

class Messages:
    """Message operations"""
    
    def __init__(self, client: AzureOpenAI):
        self._client = client

    def list(self,
             thread_id: str,
             limit: Optional[int] = DEFAULT_MESSAGE_LIST_PARAMS[LIST_PARAM_LIMIT],
             order: Optional[str] = DEFAULT_MESSAGE_LIST_PARAMS[LIST_PARAM_ORDER],
             after: Optional[str] = DEFAULT_MESSAGE_LIST_PARAMS[LIST_PARAM_AFTER],
             before: Optional[str] = DEFAULT_MESSAGE_LIST_PARAMS[LIST_PARAM_BEFORE],
             run_id: Optional[str] = None,
             **kwargs) -> Any:
        """Returns a list of messages for a given thread."""
        if limit and limit not in LIST_LIMIT_RANGE:
            raise ValueError(ERROR_INVALID_LIMIT)
        
        params = {
            'thread_id': thread_id,
            LIST_PARAM_LIMIT: limit,
            LIST_PARAM_ORDER: order,
            LIST_PARAM_AFTER: after,
            LIST_PARAM_BEFORE: before,
            'run_id': run_id,
            **kwargs
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        return self._client.beta.threads.messages.list(**params)

    def retrieve(self,
                thread_id: str,
                message_id: str,
                **kwargs) -> Any:
        """Retrieves a specific message from a thread."""
        if not message_id:
            raise ValueError(ERROR_INVALID_MESSAGE_ID)
            
        return self._client.beta.threads.messages.retrieve(
            message_id=message_id,
            thread_id=thread_id,
            **kwargs
        )

    def update(self,
               thread_id: str,
               message_id: str,
               metadata: Optional[Dict[str, str]] = DEFAULT_MESSAGE_METADATA,
               **kwargs) -> Any:
        """Modifies a message."""
        if not message_id:
            raise ValueError(ERROR_INVALID_MESSAGE_ID)
            
        params = {
            'message_id': message_id,
            'thread_id': thread_id,
            'metadata': metadata,
            **kwargs
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        return self._client.beta.threads.messages.update(**params)

    # Compatibility methods
    def list_messages(self, *args, **kwargs) -> Any:
        """Compatibility method for list()"""
        return self.list(*args, **kwargs)

    def retrieve_message(self, *args, **kwargs) -> Any:
        """Compatibility method for retrieve()"""
        return self.retrieve(*args, **kwargs)

    def update_message(self, *args, **kwargs) -> Any:
        """Compatibility method for update()"""
        return self.update(*args, **kwargs) 