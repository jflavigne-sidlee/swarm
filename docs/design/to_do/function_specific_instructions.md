
# Function-Specific Instructions for Standardizing Path Handling

This document provides function-specific instructions for updating their signatures and behavior to handle `Path` objects and strings consistently.

---

## **1. `write_document`**

### Current Signature:
```python
def write_document(file_path: Path, metadata: Dict[str, str], encoding: str) -> None:
```

### Updated Signature:
```python
def write_document(
    file_path: Union[Path, str], metadata: Dict[str, str], encoding: str, config: Optional[WriterConfig] = None
) -> None:
```

### Changes:
1. Accept `Union[Path, str]` for `file_path`.
2. Use `resolve_path_with_config` to handle relative paths using `config.drafts_dir`.
3. Log a debug statement when resolving a string or relative path.

### Implementation:
```python
def write_document(
    file_path: Union[Path, str], metadata: Dict[str, str], encoding: str, config: Optional[WriterConfig] = None
) -> None:
    config = get_config(config)
    file_path = resolve_path_with_config(file_path, config.drafts_dir)
    with open(file_path, "w", encoding=encoding) as f:
        f.write(YAML_FRONTMATTER_START)
        f.write(yaml.dump(metadata, default_flow_style=False, sort_keys=False))
        f.write(YAML_FRONTMATTER_END)
```

---

## **2. `append_section`**

### Current Signature:
```python
def append_section(
    file_name: str, section_title: str, content: str, config: Optional[WriterConfig] = None, ...
) -> None:
```

### Updated Signature:
```python
def append_section(
    file_path: Union[Path, str], section_title: str, content: str, config: Optional[WriterConfig] = None, ...
) -> None:
```

### Changes:
1. Replace `file_name` with `Union[Path, str]` as `file_path`.
2. Use `resolve_path_with_config` to handle relative paths using `config.drafts_dir`.
3. Validate file existence after resolving the path.

### Implementation:
```python
def append_section(
    file_path: Union[Path, str], section_title: str, content: str, config: Optional[WriterConfig] = None, ...
) -> None:
    config = get_config(config)
    file_path = resolve_path_with_config(file_path, config.drafts_dir)
    validate_file(file_path, require_write=True)

    with open(file_path, "a", encoding=config.default_encoding) as f:
        f.write(f"

## {section_title}

{content}")
```

---

## **3. `create_document`**

### Current Signature:
```python
def create_document(file_name: str, metadata: Dict[str, str], config: Optional[WriterConfig] = None) -> Path:
```

### Updated Signature:
```python
def create_document(
    file_path: Union[Path, str], metadata: Dict[str, str], config: Optional[WriterConfig] = None
) -> Path:
```

### Changes:
1. Replace `file_name` with `Union[Path, str]` as `file_path`.
2. Use `resolve_path_with_config` to handle relative paths.
3. Log a debug message for any string resolution.

### Implementation:
```python
def create_document(
    file_path: Union[Path, str], metadata: Dict[str, str], config: Optional[WriterConfig] = None
) -> Path:
    config = get_config(config)
    file_path = resolve_path_with_config(file_path, config.drafts_dir)
    
    if file_path.exists():
        raise WriterError(f"Document already exists: {file_path}")

    write_document(file_path, metadata, config.default_encoding)
    return file_path
```

---

## **4. `edit_section`**

### Current Signature:
```python
def edit_section(
    file_name: str, section_title: str, new_content: str, config: Optional[WriterConfig] = None
) -> None:
```

### Updated Signature:
```python
def edit_section(
    file_path: Union[Path, str], section_title: str, new_content: str, config: Optional[WriterConfig] = None
) -> None:
```

### Changes:
1. Replace `file_name` with `Union[Path, str]` as `file_path`.
2. Use `resolve_path_with_config` to handle relative paths.
3. Add debug logging for path resolution.

### Implementation:
```python
def edit_section(
    file_path: Union[Path, str], section_title: str, new_content: str, config: Optional[WriterConfig] = None
) -> None:
    config = get_config(config)
    file_path = resolve_path_with_config(file_path, config.drafts_dir)
    
    content = read_file(file_path, config.default_encoding)
    updated_content = replace_section(content, section_title, new_content)

    atomic_write(file_path, updated_content, config.default_encoding, config.temp_dir)
```

---

## **5. `stream_content`**

### Current Signature:
```python
async def stream_content(
    file_name: str, content: str, chunk_size: Optional[int] = None, ...
) -> None:
```

### Updated Signature:
```python
async def stream_content(
    file_path: Union[Path, str], content: str, chunk_size: Optional[int] = None, ...
) -> None:
```

### Changes:
1. Replace `file_name` with `Union[Path, str]` as `file_path`.
2. Resolve `file_path` with `resolve_path_with_config`.
3. Log a debug statement for any string resolution.

### Implementation:
```python
async def stream_content(
    file_path: Union[Path, str], content: str, chunk_size: Optional[int] = None, ...
) -> None:
    config = get_config(config)
    file_path = resolve_path_with_config(file_path, config.drafts_dir)
    
    if chunk_size is None:
        chunk_size = config.min_chunk_size
    
    await stream_document_content(file_path, content, chunk_size, config.default_encoding)
```

---

## **6. `search_and_replace`**

### Current Signature:
```python
def search_and_replace(file_name: str, search_text: str, replace_text: str, ...) -> int:
```

### Updated Signature:
```python
def search_and_replace(
    file_path: Union[Path, str], search_text: str, replace_text: str, ...
) -> int:
```

### Changes:
1. Replace `file_name` with `Union[Path, str]` as `file_path`.
2. Use `resolve_path_with_config` to handle relative paths.
3. Log string resolution.

### Implementation:
```python
def search_and_replace(
    file_path: Union[Path, str], search_text: str, replace_text: str, ...
) -> int:
    config = get_config(config)
    file_path = resolve_path_with_config(file_path, config.drafts_dir)

    content = read_file(file_path, config.default_encoding)
    updated_content, replacements = pattern.subn(replace_text, content)

    atomic_write(file_path, updated_content, config.default_encoding, config.temp_dir)
    return replacements
```

---

## Next Steps
1. Implement the changes in the code.
2. Add tests for each function to ensure:
   - Both `Path` and string inputs are handled.
   - Relative paths are resolved correctly.
   - Debug logs are generated for path resolutions.
