# Feature Description: update_metadata

## Problem and Context

### Problem:
Metadata in Markdown documents often requires updates, such as modifying the title, author, or adding new tags. Manually editing the metadata block is error-prone and risks disrupting the file’s structure or integrity, particularly in collaborative or automated workflows.

### Context:
The ```update_metadata``` function simplifies and automates the process of updating or adding metadata fields in a Markdown document while preserving the structure and formatting of the metadata block. It ensures that updates are precise, safe, and compliant with YAML standards, facilitating downstream tasks like validation, exporting, or reporting.

## Function-Level Goals

- **Purpose:**  
Update or add metadata fields in the YAML metadata block of a Markdown document while preserving the document’s structure and formatting.

- **Behavior:**
  - **Metadata Update:**
    - Locate the metadata block delimited by ```---``` at the beginning of the document.
    - Parse the metadata into a dictionary.
    - Overwrite existing fields or add new ones based on the provided ```new_metadata```.
  - **Formatting Preservation:**
    - Preserve the YAML block's structure and formatting, including indentation and ordering.
  - **Field Protection:**
    - Prevent accidental overwriting of essential fields (e.g., ```title, author```) unless explicitly specified in ```new_metadata```.
- **Input/Output Format:**
  - **Input:**
    - ```file_name``` (```str```): The name of the Markdown file to update. Must exist and be a valid ```.md``` file.
    - ```new_metadata``` (```dict```): A dictionary containing the fields to update or add.
  - **Output:**
    - Returns ```None```. Updates the specified file in place.
- **Example Input:**

```python
file_name = "document.md"
new_metadata = {
    "title": "Updated Project Plan",
    "tags": ["planning", "updated"],
    "status": "Draft"
}
```

- **Example Behavior:**
For a file containing:

```markdown
---
title: Project Plan
author: Alice Johnson
date: 2024-11-20
tags:
  - planning
---
# Introduction
This is the introduction section.
```

After calling update_metadata, the file will be updated to:

```markdown
---
title: Updated Project Plan
author: Alice Johnson
date: 2024-11-20
tags:
  - planning
  - updated
status: Draft
---
# Introduction
This is the introduction section.
```

- **Constraints and Edge Cases:**
  - **File Not Found:** Raise an error if the specified file does not exist.
  - **Missing Metadata Block:** Raise an error if the file does not contain a valid YAML metadata block.
  - **Invalid Metadata Format:** Raise an error if the provided ```new_metadata``` is not a dictionary or contains invalid YAML syntax.
  - **Field Overwriting:** Avoid overwriting critical fields (e.g., ```title, author```) unless explicitly provided in ```new_metadata```.
  - **Empty Metadata Updates:** If ```new_metadata``` is empty, make no changes to the file.

## Dependencies

- **Libraries:**
  - ```os``` and ```pathlib```: For file validation and handling.
  - ```yaml``` **(via PyYAML)**: To parse, manipulate, and serialize the metadata block in YAML format.
  - ```logging```: To log updates, warnings, and errors.
- **Best Practices:**
  - Use ```yaml.safe_load()``` for secure parsing of YAML blocks.
  - Preserve the original file's structure and ensure no unintended changes to its formatting.
  - Log all updates for traceability, especially in collaborative environments.
  - Handle file operations and YAML parsing in ```try-except``` blocks to manage errors gracefully (e.g., file not found, malformed metadata).

## Summary of Feature

The ```update_metadata``` function ensures safe and structured updates to the metadata block of Markdown documents. By automating field updates and preserving formatting, it supports collaborative and automated workflows that rely on consistent and accurate metadata. The function’s robust error handling and adherence to YAML standards make it a reliable tool for managing document metadata in the Markdown Document Management System.