# File Operations Interface Refactoring Plan

## Problem Statement
Current file operations show inconsistent patterns in handling paths and configurations:
- Inconsistent use of paths (sometimes full paths, sometimes filenames)
- Risk of filename collisions across different directories
- Unclear responsibility for path resolution and validation

Reference: 
typescript:docs/design/done/refactoring_plan.md
startLine: 1
endLine: 27


## Proposed Solution

### 1. Standardize on Path Objects

```python
def create_document(file_path: Path, metadata: dict, config: Optional[WriterConfig] = None) -> Path:
"""Create a new document using absolute Path."""
config = get_config(config)
if not file_path.is_absolute():
file_path = config.drafts_dir / file_path
return create_document_internal(file_path, metadata, config)
def append_section(file_path: Path, section: str, content: str, config: Optional[WriterConfig] = None) -> None:
"""Append section using absolute Path."""
config = get_config(config)
if not file_path.is_absolute():
file_path = config.drafts_dir / file_path
append_section_internal(file_path, section, content, config)
```


### 2. Update WriterConfig Role

```python
class WriterConfig:
def validate_path(self, file_path: Path) -> Path:
"""Validate and return absolute path."""
if not file_path.is_absolute():
file_path = self.drafts_dir / file_path
validate_file_access(file_path)
return file_path
```



### 3. Deprecation Strategy

Mark filename-only versions as deprecated:

```python
@deprecated("Use Path objects instead of filenames")
def legacy_create_document(filename: str, metadata: dict) -> Path:
"""Legacy interface that accepts filename strings."""
warnings.warn("Use Path objects instead of filenames", DeprecationWarning)
return create_document(Path(filename), metadata)
```



## Implementation Phases

### Phase 1: Path Object Migration
1. Update all functions to accept Path objects
2. Add path resolution and validation
3. Update tests to use Path objects

### Phase 2: Config Updates
1. Refocus config on validation rather than path resolution
2. Add path validation utilities
3. Update tests for new config behavior

### Phase 3: Update Tests
Reference: 
typescript:docs/design/testing/integration_testing_plan.md
startLine: 381
endLine: 391


## Success Criteria

1. All operations use Path objects consistently
2. Clear path resolution and validation
3. No risk of filename collisions
4. All tests pass with new interfaces
5. Documentation updated to reflect Path usage

## Migration Guide
### Old
```python
create_document("doc.md", metadata, config)
```
### New
```python
doc_path = Path("/path/to/doc.md")
create_document(doc_path, metadata, config)
```

Or relative to config

```python
doc_path = Path("doc.md")
create_document(doc_path, metadata, config) # Will be made absolute using config.drafts_di
```
