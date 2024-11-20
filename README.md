# swarm-project

# Swarm Project Codebase Structure

Overview
This is an Azure OpenAI-based project that implements a swarm of AI agents with file search and vision capabilities. The project uses Azure OpenAI's API and includes comprehensive testing infrastructure.
Core Components
1. Azure OpenAI Client (src/aoai/)
Custom client implementation for Azure OpenAI services
Handles authentication and API interactions
Manages vector stores, assistants, and chat completions
Key files:
client.py: Main client implementation
constants.py: API constants and configuration
types.py: Type definitions
files.py: Vector store operations
runs.py: Run management
chat.py: Chat completion functionality
2. File Management (src/file_manager.py)
Handles file operations and vector store management
Validates file types and MIME types
Manages file uploads to vector stores
Integrates with Azure OpenAI's file search capabilities
3. Models System (src/models/)
Type-safe configuration system for AI models
Supports multiple providers (Azure, OpenAI)
Handles model capabilities and limitations
Key components:


### ModelConfig

Represents a complete model configuration including:

- Provider information
- Model capabilities
- Version information
- Deployment settings
- MIME type support
- Description and metadata

4. Functions (src/functions/)
Vision analysis capabilities
File search operations
Type definitions and schemas
Notable features:

```python
@dataclass
class ImageAnalysisResponse:
    """Response structure for image analysis results."""
    description: str
    tags: List[str]
    objects: List[str]
    text: Optional[str] = None
    faces: Optional[List[dict]] = None
    colors: Optional[List[str]] = None
    landmarks: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    brands: Optional[List[str]] = None


5. Configuration (src/config.py)
Central configuration management
Handles file search settings
Deployment configurations
Example configuration:

```python
@dataclass
class FileSearchConfig:
    """Configuration for FileSearchManager.
    
    Attributes:
        assistant_name: Name for created assistants
        assistant_instructions: Instructions for created assistants
        vector_store_expiration_days: Days until vector store expires
        max_retries: Number of retries for API calls
        retry_delay: Delay between retries in seconds
        chunk_size: Size of chunks for text splitting (in tokens)
        chunk_overlap: Overlap between chunks (in tokens)
        max_chunks_in_context: Maximum number of chunks to include in context
        model_name: Name of the Azure OpenAI deployment to use
    """
    assistant_name: str = "File Analysis Assistant"
    assistant_instructions: str = "You are an expert at analyzing documents and answering questions about them."
    vector_store_expiration_days: int = 7
    max_retries: int = 3
    retry_delay: float = 1.0
    chunk_size: int = 800
    chunk_overlap: int = 400
    max_chunks_in_context: int = 20
    model_name: Optional[str] = None
```

6. Testing Infrastructure
Comprehensive test suite
Pytest-based testing framework
Test utilities and fixtures
Key test directories:
/tests/: Main test suite
/tests/functions/: Function-specific tests
/tests/models/: Model system tests
Project Structure

swarm-project/
├── src/
│   ├── aoai/               # Azure OpenAI client implementation
│   ├── functions/          # Core functionality modules
│   ├── models/            # Model configuration system
│   ├── exceptions/        # Custom exceptions
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── file_manager.py    # File operations
│   └── types.py           # Type definitions
├── tests/
│   ├── functions/         # Function tests
│   ├── models/           # Model tests
│   ├── conftest.py       # Test configuration
│   └── test_*.py         # Test files
├── docs/                 # Documentation
└── requirements.txt      # Dependencies

Key Features
1. File Search Capabilities
Vector store management
File upload and processing
Document search and analysis
MIME type validation
2. Vision Analysis
Image analysis and interpretation
Multi-image comparison
Object detection and scene analysis
Support for various image formats
3. Model Management
Provider-specific configurations
Capability-based model selection
Environment-based deployment settings
MIME type validation for media models

Configuration System
Environment Variables
Azure OpenAI credentials
Deployment overrides
Model configurations
API versions

File Search Configuration

```python
@dataclass
class FileSearchConfig:
    """Configuration for FileSearchManager.
    
    Attributes:
        assistant_name: Name for created assistants
        assistant_instructions: Instructions for created assistants
        vector_store_expiration_days: Days until vector store expires
        max_retries: Number of retries for API calls
        retry_delay: Delay between retries in seconds
        chunk_size: Size of chunks for text splitting (in tokens)
        chunk_overlap: Overlap between chunks (in tokens)
        max_chunks_in_context: Maximum number of chunks to include in context
        model_name: Name of the Azure OpenAI deployment to use
    """
    assistant_name: str = "File Analysis Assistant"
    assistant_instructions: str = "You are an expert at analyzing documents and answering questions about them."
    vector_store_expiration_days: int = 7
    max_retries: int = 3
    retry_delay: float = 1.0
    chunk_size: int = 800
    chunk_overlap: int = 400
    max_chunks_in_context: int = 20
    model_name: Optional[str] = None
```

Testing Structure
Test Categories
Basic Functionality Tests
Integration Tests
Error Handling Tests
Model Configuration Tests
Vision Analysis Tests
Test Utilities
Test fixtures
Environment setup
Mock data generation
Response validation
Dependencies
Key dependencies from requirements.txt:
openai
python-dotenv
pytest
pydantic
instructor
httpx
aiohttp

Error Handling
The project implements a comprehensive error handling system with custom exceptions:

```python
class FileSearchError(Exception):
    """Base exception for file search operations."""
    pass

class FileValidationError(FileSearchError):
    """Raised when file validation fails."""
    pass

class VectorStoreError(FileSearchError):
    """Raised when vector store operations fail."""
    pass

class AssistantError(FileSearchError):
    """Raised when assistant operations fail."""
    pass
```
