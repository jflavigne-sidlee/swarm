
# Standardizing Function Signatures for Path Objects and Strings

## Objective
Standardize all functions to:
1. Accept `Path` objects or strings for path-related parameters.
2. Resolve strings into `Path` objects if necessary.
3. Log a debug statement when this resolution occurs.

---

## Implementation Steps

### 1. Update Function Signatures
- Use `Union[Path, str]` for all path-related parameters.

**Example:**
```python
from typing import Union

def write_document(
    file_path: Union[Path, str], metadata: Dict[str, str], encoding: str
) -> None:
```

---

### 2. Create a Utility for Path Resolution
Add a helper function to handle path resolution:
1. Check if the input is a string.
2. Convert it to a `Path` object.
3. Log a debug statement when conversion happens.

**Implementation:**
```python
from pathlib import Path
from typing import Union
import logging

logger = logging.getLogger(__name__)

def resolve_path(file_path: Union[Path, str]) -> Path:
    """Resolve a string or Path into an absolute Path object."""
    if isinstance(file_path, str):
        logger.debug(f"Resolving string to Path: {file_path}")
        file_path = Path(file_path)
    return file_path
```

---

### 3. Resolve Relative Paths Using Configuration
Extend the utility to handle relative paths, resolving them with a base directory.

**Implementation:**
```python
def resolve_path_with_config(
    file_path: Union[Path, str], base_dir: Path
) -> Path:
    """Resolve a string or Path into an absolute Path with a base directory."""
    file_path = resolve_path(file_path)
    if not file_path.is_absolute():
        logger.debug(f"Resolving relative path: {file_path} with base: {base_dir}")
        file_path = base_dir / file_path
    return file_path.resolve()
```

**Usage:**
```python
file_path = resolve_path_with_config(file_path, config.drafts_dir)
```

---

### 4. Refactor Functions to Use the Utilities
Update functions to use `resolve_path` and `resolve_path_with_config`.

**Example:**
Before:
```python
def write_document(file_path: Path, metadata: Dict[str, str], encoding: str) -> None:
    with open(file_path, "w", encoding=encoding) as f:
        f.write(content)
```

After:
```python
def write_document(
    file_path: Union[Path, str], metadata: Dict[str, str], encoding: str, config: Optional[WriterConfig] = None
) -> None:
    config = get_config(config)
    file_path = resolve_path_with_config(file_path, config.drafts_dir)
    with open(file_path, "w", encoding=encoding) as f:
        f.write(content)
```

---

### 5. Add Debug Logging
Log all:
1. String-to-`Path` conversions.
2. Relative-to-absolute path resolutions.

---

### 6. Update Unit Tests
Write tests to validate:
1. Acceptance of both `Path` objects and strings.
2. Correct resolution of strings to `Path` objects.
3. Correct handling of relative paths.

**Example Tests:**
```python
def test_resolve_path():
    assert resolve_path("file.txt") == Path("file.txt")
    assert resolve_path(Path("file.txt")) == Path("file.txt")

def test_resolve_path_with_config():
    base_dir = Path("/home/user")
    assert resolve_path_with_config("file.txt", base_dir) == Path("/home/user/file.txt")
    assert resolve_path_with_config("/absolute/path.txt", base_dir) == Path("/absolute/path.txt")
```

---

### 7. Document Changes
Update function and module documentation to reflect:
1. Acceptance of `Path` objects and strings.
2. Handling of relative paths with a configuration context.

---

## Checklist
1. **Update All Function Signatures:**
   - Use `Union[Path, str]` for path-related parameters.
2. **Ensure Path Resolution:**
   - Convert strings to `Path` objects using the utility.
   - Resolve relative paths based on configuration.
3. **Log All Resolutions:**
   - Add debug logs for string-to-`Path` conversions and relative-to-absolute resolutions.
4. **Test Thoroughly:**
   - Verify consistent handling of `Path` and string inputs.
5. **Document Changes:**
   - Update the code documentation.

---

## Example Refactor: `write_document`

### Before
```python
def write_document(file_path: Path, metadata: Dict[str, str], encoding: str) -> None:
    with open(file_path, "w", encoding=encoding) as f:
        f.write(content)
```

### After
```python
def write_document(
    file_path: Union[Path, str], metadata: Dict[str, str], encoding: str, config: Optional[WriterConfig] = None
) -> None:
    config = get_config(config)
    file_path = resolve_path_with_config(file_path, config.drafts_dir)
    with open(file_path, "w", encoding=encoding) as f:
        f.write(content)
```

---

## Success Criteria
1. All functions accept `Path` or string parameters.
2. Strings are consistently resolved into `Path` objects.
3. Debug statements are logged during path resolution.
4. Relative paths are handled correctly using a configuration context.
5. All tests pass, and new tests validate path handling.
