# Model Registry Tests

## Test Categories

### Basic Model Tests
```bash
# Test basic model capabilities
pytest tests/models/test_base.py::TestModelCapabilities::test_chat_model_capabilities -v
pytest tests/models/test_base.py::TestModelCapabilities::test_embedding_model_capabilities -v
pytest tests/models/test_base.py::TestModelCapabilities::test_image_generation_capabilities -v
pytest tests/models/test_base.py::TestModelCapabilities::test_speech_model_capabilities -v

# Test validation
pytest tests/models/test_base.py::TestModelCapabilities::test_token_validation -v
pytest tests/models/test_base.py::TestModelCapabilities::test_temperature_validation -v
```

### Registry Integration Tests
```bash
# Test model type integrations
pytest tests/models/test_registry_integration.py::TestModelRegistryIntegration::test_chat_model_integration -v
pytest tests/models/test_registry_integration.py::TestModelRegistryIntegration::test_vision_model_integration -v
pytest tests/models/test_registry_integration.py::TestModelRegistryIntegration::test_embedding_model_integration -v
pytest tests/models/test_registry_integration.py::TestModelRegistryIntegration::test_speech_model_integration -v
pytest tests/models/test_registry_integration.py::TestModelRegistryIntegration::test_image_generation_integration -v

# Test advanced filtering
pytest tests/models/test_registry_integration.py::TestModelRegistryIntegration::test_cross_capability_filtering -v
pytest tests/models/test_registry_integration.py::TestModelRegistryIntegration::test_provider_specific_models -v
```

### Error Case Tests
```bash
# Test invalid inputs
pytest tests/models/test_registry_errors.py::TestModelRegistryErrors::test_invalid_model_name -v
pytest tests/models/test_registry_errors.py::TestModelRegistryErrors::test_ambiguous_model_resolution -v
pytest tests/models/test_registry_errors.py::TestModelRegistryErrors::test_invalid_capability_queries -v

# Test configuration errors
pytest tests/models/test_registry_errors.py::TestModelRegistryErrors::test_deployment_name_conflicts -v
pytest tests/models/test_registry_errors.py::TestModelRegistryErrors::test_invalid_model_configurations -v
pytest tests/models/test_registry_errors.py::TestModelRegistryErrors::test_mime_type_validation -v
pytest tests/models/test_registry_errors.py::TestModelRegistryErrors::test_provider_validation -v
```

### Run All Tests
```bash
# Run all model tests
pytest tests/models/ -v

# Run with coverage
pytest tests/models/ -v --cov=src.models --cov-report=html

# Run specific test categories
pytest tests/models/ -v -k "basic"  # Run basic capability tests
pytest tests/models/ -v -k "integration"  # Run integration tests
pytest tests/models/ -v -k "error"  # Run error case tests

# Debug Options
# Run with print statements
pytest tests/models/ -v -s

# Run with detailed traceback
pytest tests/models/ -v --tb=long

# Run with PDB on failures
pytest tests/models/