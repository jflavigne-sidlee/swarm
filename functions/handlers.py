from openai import AssistantEventHandler
from typing import Optional, Any

class FileSearchEventHandler(AssistantEventHandler):
    """Event handler for file search operations with Azure OpenAI Assistant."""
    
    def __init__(self):
        self.response: Optional[str] = None
        self.error: Optional[str] = None
        self.is_complete: bool = False
        self.tool_calls: list = []
        self.file_searches: list = []
    
    def on_text_created(self, text: Any) -> None:
        """Called when assistant starts generating text."""
        print("\nassistant > ", end="", flush=True)
    
    def on_text_delta(self, delta: Any, snapshot: Any) -> None:
        """Called when assistant generates text incrementally."""
        print(delta.value, end="", flush=True)
        if snapshot:
            self.response = snapshot.value
    
    def on_tool_call_created(self, tool_call: Any) -> None:
        """Called when assistant initiates a tool call."""
        self.tool_calls.append(tool_call)
        print(f"\nTool call created: {tool_call.type}")
    
    def on_tool_call_delta(self, delta: Any, snapshot: Any) -> None:
        """Called during tool call execution."""
        if delta.type == "file_search":
            query = delta.file_search.query if hasattr(delta, 'file_search') else ''
            self.file_searches.append(query)
            print(f"\nSearching files: {query}")
    
    def on_error(self, error: Any) -> None:
        """Called when an error occurs."""
        print(f"\nError: {error}")
        self.error = str(error)
        self.is_complete = True
    
    def on_end(self) -> None:
        """Called when streaming ends."""
        print("\nStream ended")
        self.is_complete = True
    
    @property
    def has_response(self) -> bool:
        """Check if handler has received a response."""
        return self.response is not None
    
    @property
    def has_error(self) -> bool:
        """Check if handler encountered an error."""
        return self.error is not None 