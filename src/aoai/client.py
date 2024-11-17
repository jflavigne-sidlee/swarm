from openai import AzureOpenAI
from typing import Optional, List, Dict, Any, Union
from .assistants import Assistants
from .chat import Chat
from .files import VectorStores
from .threads import Threads
from .types import (
    OrderDirection,
    MessageRole,
    TruncationType,
    ToolType,
    RunStatus,
    ToolResources,
    TruncationStrategy
)
from .messages import Messages
from .runs import Runs

class AOAIClient:
    """Azure OpenAI Client wrapper for managing assistants, threads, and vector stores."""
    
    def __init__(self, client: AzureOpenAI):
        """Initialize with component classes."""
        self._client = client
        self.vector_stores = VectorStores(client)
        self.assistants = Assistants(client)
        self.threads = Threads(client)
        self.chat = Chat(client)
        self.messages = Messages(client)
        self.runs = Runs(client)
    
    @classmethod
    def create(cls,
               api_key: str,
               api_version: str,
               azure_endpoint: str) -> 'AOAIClient':
        """Create a new AOAIClient instance with the given credentials."""
        client = AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=azure_endpoint
        )
        return cls(client)
    
    @property
    def client(self) -> AzureOpenAI:
        """Access to underlying client if needed."""
        return self._client
