# Swarm Project

## Overview
A Python-based framework for orchestrating AI agents using Azure OpenAI services. This project implements a swarm of AI agents with file search and vision capabilities, built on Azure OpenAI's API with comprehensive testing infrastructure.

## Features
- 🤖 Multi-agent orchestration
- 📄 File search and analysis with vector store support
- 👁️ Vision and image analysis capabilities
- 🔄 Advanced vector store management
- ⚡ High-performance async operations
- 🧪 Comprehensive testing suite

## Installation

```bash
pip install -r requirements.txt
```

## Project Structure

swarm-project/
├── src/
│   ├── aoai/               # Azure OpenAI client implementation
│   ├── functions/          # Core functionality modules
│   ├── models/            # Model configuration system
│   ├── exceptions/        # Custom exceptions
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


## Key Features

### 1. File Search Capabilities
- Vector store management
- File upload and processing
- Document search and analysis
- MIME type validation

### 2. Vision Analysis
- Image analysis and interpretation
- Multi-image comparison
- Object detection and scene analysis
- Support for various image formats

### 3. Model Management
- Provider-specific configurations
- Capability-based model selection
- Environment-based deployment settings
- MIME type validation for media models

## Configuration System

### Environment Variables
- Azure OpenAI credentials
- Deployment overrides
- Model configurations
- API versions
- File Search Configuration

## Core Components

### 1. Azure OpenAI Client (`src/aoai/`)
- Custom client implementation for Azure OpenAI services
- Handles authentication and API interactions
- Manages vector stores, assistants, and chat completions
- Supports file search capabilities

### 2. File Management System
- Vector store operations and management
- File validation and MIME type checking
- Chunking and embedding management
- Supports multiple file formats including:
  - Documents (PDF, DOCX, TXT)
  - Source code (Python, JavaScript, Java, etc.)
  - Markdown and structured text

### 3. Model Configuration System
The model system provides type-safe configuration for AI models:

```python
@dataclass
class ModelConfig:
    provider: ModelProvider
    name: str
    capabilities: ModelCapabilities
    deployment_name: Optional[str] = None
    supported_mime_types: Optional[List[str]] = None
```

### 4. File Search Configuration
Configurable settings for file search operations:

```python
@dataclass
class FileSearchConfig:
    assistant_name: str = "File Analysis Assistant"
    assistant_instructions: str = "You are an expert at analyzing documents."
    vector_store_expiration_days: int = 7
    chunk_size: int = 800
    chunk_overlap: int = 400
    max_chunks_in_context: int = 20
    model_name: Optional[str] = None
```

## Environment Setup

Required environment variables:

```bash
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_API_VERSION=2024-05-01-preview
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/functions/ -v  # Function tests
pytest tests/models/ -v     # Model tests

# Run with coverage
pytest tests/ -v --cov=src --cov-report=html
```

## Error Handling

The project implements a comprehensive error handling system:

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
```

## Dependencies

Key dependencies:
- openai>=1.54.4
- python-dotenv>=1.0.1
- pytest>=8.3.3
- pydantic>=2.9.2
- instructor>=1.6.4
- httpx>=0.27.2
- aiohttp>=3.11.2

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Documentation

For detailed documentation on specific components:
- [File Search Guide](docs/file_upload.md)
- [Model Configuration](docs/models/README.md)
- [Vision Tests](docs/functions/vision/README.md)

# Instructions
For this project, we use an Azure OpenAI instance. 
Consider this when coding.

# Azure OpenAI Assistants file search tool

08/28/2024
https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/file-search?tabs=python

In this article
- File search support
- Enable file search
- Upload files for file search
- Update the assistant to use the new vector store
- Create a thread
- Create a run and check the output
- How it works
- Vector stores
- Attaching vector stores
- Ensuring vector store readiness before creating runs
- Managing costs with expiration policies

File Search augments the Assistant with knowledge from outside its model, such as proprietary product information or documents provided by your users. OpenAI automatically parses and chunks your documents, creates and stores the embeddings, and use both vector and keyword search to retrieve relevant content to answer user queries.

**Note**
- File search can ingest up to 10,000 files per assistant - 500 times more than before. It is fast, supports parallel queries through multi-threaded searches, and features enhanced reranking and query rewriting.
- Vector store is a new object in the API. Once a file is added to a vector store, it's automatically parsed, chunked, and embedded, made ready to be searched. Vector stores can be used across assistants and threads, simplifying file management and billing.
- We've added support for the tool_choice parameter which can be used to force the use of a specific tool (like file search, code interpreter, or a function) in a particular run.

## File search support

### Supported regions
File search is available in regions that support Assistants.

### API Version
2024-05-01-preview

### Supported file types

**Note**
For text/ MIME types, the encoding must be either utf-8, utf-16, or ASCII.

# Vision Tests

## Running Tests

### Individual test commands:
```bash
# Basic functionality tests
pytest tests/functions/vision/test_image_analysis.py::test_analyze_single_local_image -v
pytest tests/functions/vision/test_image_analysis.py::test_analyze_single_url_image -v
pytest tests/functions/vision/test_image_analysis.py::test_analyze_multiple_images -v
pytest tests/functions/vision/test_image_analysis.py::test_encode_image_to_base64 -v

# Error handling tests
pytest tests/functions/vision/test_image_analysis.py::test_invalid_image_path -v
pytest tests/functions/vision/test_image_analysis.py::test_invalid_image_url -v


# Model configuration tests
pytest tests/functions/vision/test_image_analysis.py::test_analyze_images_model_validation -v
pytest tests/functions/vision/test_image_analysis.py::test_token_limit_validation -v
pytest tests/functions/vision/test_image_analysis.py::test_mime_type_validation -v
pytest tests/functions/vision/test_image_analysis.py::test_environment_model_override -v

# Image set analysis tests
pytest tests/functions/vision/test_image_analysis.py::test_image_set_analysis -v
pytest tests/functions/vision/test_image_analysis.py::test_image_set_with_custom_prompt -v
pytest tests/functions/vision/test_image_analysis.py::test_image_set_token_limit -v

# Response validation tests
pytest tests/functions/vision/test_image_analysis.py::test_response_model_validation -v
pytest tests/functions/vision/test_image_analysis.py::test_max_tokens_limit -v

# Run all tests in file:
pytest tests/functions/vision/test_image_analysis.py -v

# Run all tests with print statements:
pytest tests/functions/vision/test_image_analysis.py -v -s

# Run tests by category:
pytest tests/functions/vision/test_image_analysis.py -v -k "basic" # Run basic functionality tests
pytest tests/functions/vision/test_image_analysis.py -v -k "error" # Run error handling tests
pytest tests/functions/vision/test_image_analysis.py -v -k "model" # Run model configuration tests
pytest tests/functions/vision/test_image_analysis.py -v -k "set" # Run image set tests
pytest tests/functions/vision/test_image_analysis.py -v -k "response" # Run response validation tests

# Run tests with coverage:
pytest tests/functions/vision/test_image_analysis.py -v --cov=src.functions.vision.image_analysis

# Run tests and generate HTML coverage report:
pytest tests/functions/vision/test_image_analysis.py -v --cov=src.functions.vision.image_analysis --cov-report=html