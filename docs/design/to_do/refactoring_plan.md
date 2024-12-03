# Refactoring Plan for `fileoperations.py` and `filevalidation.py`

## Objective
The goal of this refactor is to improve modularity and maintainability of the `fileoperations.py` and `filevalidation.py` modules while ensuring compatibility with external parts of the codebase that rely on their current structure.

---

## Key Transformations

### 1. Introduce Clear Separation of Concerns
We will reorganize responsibilities into three focused modules:
- **`file_operations.py`:**  
   Responsible for document-level operations such as creating, appending, or editing content in Markdown files.
- **`filevalidation.py`:**  
   Focused on validating file paths, filenames, metadata, and document-specific rules.
- **`file_io.py`:**  
   Handles low-level physical file operations, such as reading, writing, streaming, and cleaning up files.

---

## Steps for the Transformation

### 1. Move Functions to Appropriate Modules
- **From `file_operations.py` to `file_validation.py`:**
  - `validate_file_inputs`
  - `validate_filename`

- **From `file_operations.py` to `file_io.py`:**
  - `cleanup_partial_file`
  - `ensure_file_newline`
  - `stream_chunks`
  - File-writing aspects of `stream_content` (split the function into validation and I/O).

### 2. Update Public Interfaces

To maintain compatibility with external code:
- Keep all existing function signatures and import paths in `file_operations.py` and `file_validation.py`.
- Modify these functions to delegate their logic to the new or updated modules (`file_io.py`, `file_validation.py`).

### 3. Add Deprecation Notices
- For functions being relocated, add clear deprecation warnings to inform developers about their new location.

### 4. Update and Expand Tests
- Ensure existing unit tests for `fileoperations.py` and `filevalidation.py` continue to pass.
- Add new tests targeting the relocated functions in their new modules to confirm behavior.

---

## Transformations by Function

### Functions Moving to `file_validation.py`
1. **`validate_file_inputs`**:
   - Move the logic to `file_validation.py` under the same name.
   - Keep a delegating function in `fileoperations.py` for backward compatibility.

2. **`validate_filename`**:
   - Move the logic to `file_validation.py`.
   - Preserve the public interface in `file_operations.py`.

---

### Functions Moving to `fileio.py`
1. **`cleanup_partial_file`**:
   - Move to `file_io.py`.
   - Update calls within `file_operations.py` to use the relocated function.
   - Add a deprecation warning in `file_operations.py`.

2. **`ensure_file_newline`**:
   - Move to `file_io.py`.
   - Update internal usage within `file_operations.py`.

3. **`stream_chunks`**:
   - Move to `file_io.py`.
   - Ensure `stream_content` in `file_operations.py` relies on this updated implementation.

4. **`stream_content`** (split function):
   - Keep document-level logic (e.g., content validation, chunk-size determination) in `file_operations.py`.
   - Delegate low-level streaming logic to `file_io.py`.

---

### Functions Remaining in `file_operations.py`
1. **`create_document`**: Core document creation logic stays here.
2. **`append_section`**: Stays here as it manipulates the document structure.
3. **`edit_section`**: Remains here for section-specific editing logic.
4. **`validate_section_markers`**: Integral to document structure validation and remains here.

---

## Backward Compatibility Considerations

### Preserving External Functionality
1. **Public API Consistency**:
   - Functions like `validate_file_inputs`, `cleanup_partial_file`, and `stream_chunks` will remain callable from their original locations, even after relocation.
   - Add lightweight delegator functions in `file_operations.py` and `file_validation.py`.

2. **Deprecation Notices**:
   - Use `warnings.warn` to indicate relocated functions and suggest direct usage of their new modules.

### Testing Requirements
1. **Preserve Existing Unit Tests**:
   - Ensure that all existing tests for `file_operations.py` and `file_validation.py` pass without modification.
2. **Add Tests for New Locations**:
   - Add unit tests targeting the functions in their new modules (`file_io.py`, `file_validation.py`).

### Use Existing Constants When Refactoring

- **Use Constants for Logs, Messages, and Errors:**  
  All log messages, error messages, and user-facing strings must be stored as constants, preferably in a centralized module or at the top of the file.
- **Check for Existing Constants:**  
  Before introducing new constants, check if an appropriate constant already exists in the project.
- **Consistency is Critical:**  
  Consistency is critical to maintain a clean and predictable codebase.

***Example:***
```python
# Constants in errors.py
ERROR_FILE_NOT_FOUND = "File not found: {file_path}"
ERROR_PERMISSION_DENIED = "Permission denied: {file_path}"

# Usage
logger.error(ERROR_FILE_NOT_FOUND.format(file_path=str(file_path)))
```

---

## Future-Proofing
1. **Gradual Deprecation**:
   - Keep proxy functions for at least one major version before removing them.
   - Clearly document changes in the release notes.

2. **Improve Documentation**:
   - Document the roles of each module (`file_operations.py`, `file_validation.py`, and `file_io.py`) to ensure clarity for future maintainers.

---

## Example After Refactor

### Before (External Code)
```python
from fileoperations import validate_file_inputs, cleanup_partial_file

validate_file_inputs(file_path, config)
cleanup_partial_file(file_path)
```

### After Refactor (Backward Compatible)
- The above code still works without modification.
- Internally:

```python
# fileoperations.py
from filevalidation import validate_file_inputs as _validate_file_inputs
from fileio import cleanup_partial_file as _cleanup_partial_file

def validate_file_inputs(file_path, config, ...):
    """Wrapper for backward compatibility."""
    return _validate_file_inputs(file_path, config, ...)

def cleanup_partial_file(file_path):
    """Wrapper with deprecation warning."""
    warnings.warn("This function has been moved to fileio.cleanup_partial_file", DeprecationWarning)
    return _cleanup_partial_file(file_path)
```