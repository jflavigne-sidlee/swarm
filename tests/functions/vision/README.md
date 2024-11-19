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

``` 












