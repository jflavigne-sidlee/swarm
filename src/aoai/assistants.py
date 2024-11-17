from typing import Optional, List, Dict, Any
from openai import AzureOpenAI
from .constants import (
    DEFAULT_ASSISTANT_NAME,
    DEFAULT_ASSISTANT_DESCRIPTION,
    DEFAULT_INSTRUCTIONS,
    DEFAULT_ASSISTANT_TOOLS,
    DEFAULT_METADATA,
    DEFAULT_ASSISTANT_TEMPERATURE,
    DEFAULT_ASSISTANT_TOP_P,
    DEFAULT_RESPONSE_FORMAT,
    DEFAULT_TOOL_RESOURCES,
    MAX_ASSISTANT_NAME_LENGTH,
    MAX_ASSISTANT_DESCRIPTION_LENGTH,
    MAX_ASSISTANT_INSTRUCTIONS_LENGTH,
    MAX_ASSISTANT_TOOLS_COUNT,
    ERROR_INVALID_ASSISTANT_ID,
    ERROR_INVALID_ASSISTANT_NAME_LENGTH,
    ERROR_INVALID_ASSISTANT_DESCRIPTION_LENGTH,
    ERROR_INVALID_ASSISTANT_INSTRUCTIONS_LENGTH,
    ERROR_INVALID_ASSISTANT_TOOLS_COUNT,
    ERROR_INVALID_TEMPERATURE,
    ERROR_INVALID_TOP_P,
    VALID_TEMPERATURE_RANGE,
    VALID_TOP_P_RANGE,
    LIST_LIMIT_RANGE,
    ERROR_INVALID_LIMIT,
    DEFAULT_ASSISTANT_LIST_PARAMS,
    LIST_PARAM_LIMIT,
    LIST_PARAM_ORDER,
    LIST_PARAM_AFTER,
    LIST_PARAM_BEFORE
)

class Assistants:
    """Assistant operations"""
    
    def __init__(self, client: AzureOpenAI):
        self._client = client

    def create(self,
               model: str,
               name: Optional[str] = DEFAULT_ASSISTANT_NAME,
               description: Optional[str] = DEFAULT_ASSISTANT_DESCRIPTION,
               instructions: Optional[str] = DEFAULT_INSTRUCTIONS,
               tools: Optional[List[Dict[str, Any]]] = DEFAULT_ASSISTANT_TOOLS,
               metadata: Optional[Dict[str, str]] = DEFAULT_METADATA,
               temperature: Optional[float] = DEFAULT_ASSISTANT_TEMPERATURE,
               top_p: Optional[float] = DEFAULT_ASSISTANT_TOP_P,
               response_format: Optional[Dict[str, str]] = DEFAULT_RESPONSE_FORMAT,
               tool_resources: Optional[Dict[str, Any]] = DEFAULT_TOOL_RESOURCES,
               **kwargs) -> Any:
        """Creates an assistant with validation."""
        # Validate parameters
        if name and len(name) > MAX_ASSISTANT_NAME_LENGTH:
            raise ValueError(ERROR_INVALID_ASSISTANT_NAME_LENGTH)
        
        if description and len(description) > MAX_ASSISTANT_DESCRIPTION_LENGTH:
            raise ValueError(ERROR_INVALID_ASSISTANT_DESCRIPTION_LENGTH)
        
        if instructions and len(instructions) > MAX_ASSISTANT_INSTRUCTIONS_LENGTH:
            raise ValueError(ERROR_INVALID_ASSISTANT_INSTRUCTIONS_LENGTH)
        
        if tools and len(tools) > MAX_ASSISTANT_TOOLS_COUNT:
            raise ValueError(ERROR_INVALID_ASSISTANT_TOOLS_COUNT)
        
        if temperature is not None and not VALID_TEMPERATURE_RANGE[0] <= temperature <= VALID_TEMPERATURE_RANGE[1]:
            raise ValueError(ERROR_INVALID_TEMPERATURE)
        
        if top_p is not None and not VALID_TOP_P_RANGE[0] <= top_p <= VALID_TOP_P_RANGE[1]:
            raise ValueError(ERROR_INVALID_TOP_P)

        # Combine all parameters
        params = {
            'model': model,
            'name': name,
            'description': description,
            'instructions': instructions,
            'tools': tools,
            'metadata': metadata,
            'temperature': temperature,
            'top_p': top_p,
            'response_format': response_format,
            'tool_resources': tool_resources,
            **kwargs
        }

        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}

        return self._client.beta.assistants.create(**params)

    def list(self,
             limit: Optional[int] = DEFAULT_ASSISTANT_LIST_PARAMS[LIST_PARAM_LIMIT],
             order: Optional[str] = DEFAULT_ASSISTANT_LIST_PARAMS[LIST_PARAM_ORDER],
             after: Optional[str] = DEFAULT_ASSISTANT_LIST_PARAMS[LIST_PARAM_AFTER],
             before: Optional[str] = DEFAULT_ASSISTANT_LIST_PARAMS[LIST_PARAM_BEFORE]) -> Any:
        """Lists assistants.
        
        Args:
            limit: Maximum number of assistants to return
            order: Sort order ('asc' or 'desc')
            after: Return results after this ID
            before: Return results before this ID
        """
        if limit and limit not in LIST_LIMIT_RANGE:
            raise ValueError(ERROR_INVALID_LIMIT)
        
        params = {
            LIST_PARAM_LIMIT: limit,
            LIST_PARAM_ORDER: order,
            LIST_PARAM_AFTER: after,
            LIST_PARAM_BEFORE: before
        }
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        return self._client.beta.assistants.list(**params)

    def retrieve(self, assistant_id: str) -> Any:
        """Retrieves an assistant by ID"""
        return self._client.beta.assistants.retrieve(assistant_id)

    def update(self,
               assistant_id: str,
               model: Optional[str] = None,
               name: Optional[str] = None,
               description: Optional[str] = None,
               instructions: Optional[str] = None,
               tools: Optional[List[Dict[str, Any]]] = None,
               metadata: Optional[Dict[str, str]] = None,
               temperature: Optional[float] = None,
               top_p: Optional[float] = None,
               response_format: Optional[Dict[str, str]] = None,
               tool_resources: Optional[Dict[str, Any]] = None,
               **kwargs) -> Any:
        """Updates an existing assistant with validation"""
        if not assistant_id:
            raise ValueError(ERROR_INVALID_ASSISTANT_ID)

        # Validate parameters if present
        if name and len(name) > MAX_ASSISTANT_NAME_LENGTH:
            raise ValueError(ERROR_INVALID_ASSISTANT_NAME_LENGTH)
        
        if description and len(description) > MAX_ASSISTANT_DESCRIPTION_LENGTH:
            raise ValueError(ERROR_INVALID_ASSISTANT_DESCRIPTION_LENGTH)
        
        if instructions and len(instructions) > MAX_ASSISTANT_INSTRUCTIONS_LENGTH:
            raise ValueError(ERROR_INVALID_ASSISTANT_INSTRUCTIONS_LENGTH)
        
        if tools and len(tools) > MAX_ASSISTANT_TOOLS_COUNT:
            raise ValueError(ERROR_INVALID_ASSISTANT_TOOLS_COUNT)
        
        if temperature is not None and not VALID_TEMPERATURE_RANGE[0] <= temperature <= VALID_TEMPERATURE_RANGE[1]:
            raise ValueError(ERROR_INVALID_TEMPERATURE)
        
        if top_p is not None and not VALID_TOP_P_RANGE[0] <= top_p <= VALID_TOP_P_RANGE[1]:
            raise ValueError(ERROR_INVALID_TOP_P)

        # Combine all parameters
        params = {
            'model': model,
            'name': name,
            'description': description,
            'instructions': instructions,
            'tools': tools,
            'metadata': metadata,
            'temperature': temperature,
            'top_p': top_p,
            'response_format': response_format,
            'tool_resources': tool_resources,
            **kwargs
        }

        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}

        return self._client.beta.assistants.update(assistant_id, **params)

    def delete(self, assistant_id: str) -> Any:
        """Deletes an assistant"""
        return self._client.beta.assistants.delete(assistant_id)
    # Compatibility methods
    def create_assistant(self, *args, **kwargs) -> Any:
        """Compatibility method for create()"""
        return self.create(*args, **kwargs)

    def list_assistants(self, *args, **kwargs) -> Any:
        """Compatibility method for list()"""
        return self.list(*args, **kwargs)

    def retrieve_assistant(self, assistant_id: str) -> Any:
        """Compatibility method for retrieve()"""
        return self.retrieve(assistant_id)

    def update_assistant(self, assistant_id: str, **kwargs) -> Any:
        """Compatibility method for update()"""
        return self.update(assistant_id, **kwargs)

    def delete_assistant(self, assistant_id: str) -> Any:
        """Compatibility method for delete()"""
        return self.delete(assistant_id)

