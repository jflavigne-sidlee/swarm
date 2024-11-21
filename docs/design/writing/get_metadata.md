# Feature Description: get_metadata

## Problem and Context

- **Problem:**
Metadata is an essential part of structured Markdown documents, typically stored as a YAML block at the top of the file. Retrieving this metadata manually is time-consuming and error-prone, especially when documents are large or metadata fields are numerous.

- **Context:**
The ```get_metadata``` function enables automated extraction of metadata from Markdown documents, providing a structured dictionary for use in subsequent processes like validation, editing, or reporting. It ensures metadata consistency, which is critical for automated workflows and collaborative environments.

## Function-Level Goals

- **Purpose:**
Extract and return the metadata block from the top of a Markdown file as a Python dictionary.

- **Behavior:**
  - **Metadata Parsing:**
    - Locate and parse the YAML metadata block at the beginning of the document, delimited by ```---```.
    - Extract keys and values like ```title, author, date``` and custom fields.
  - **Validation:**
    - Ensure the metadata block follows a valid YAML format.
    - Validate required keys (e.g., ```title, author, date```) for completeness and correctness.
- **Output:**
  - Return the metadata as a dictionary.
- **Input/Output Format:**
  - **Input:**
    - ```file_name``` (```str```): The name of the Markdown file to extract metadata from. Must exist and be a valid ```.md``` file.
  - **Output:**
    - Returns a ```dict``` containing the metadata fields and their values.
- **Example Input:**

```python
file_name = "document.md"
```

- **Example Output:**
For a file containing:

```markdown
---
title: Project Plan
author: Alice Johnson
date: 2024-11-20
tags:
  - planning
  - documentation
---
# Introduction
This is the introduction section.
```

The function would return:

```python
{
    "title": "Project Plan",
    "author": "Alice Johnson",
    "date": "2024-11-20",
    "tags": ["planning", "documentation"]
}
```

- **Constraints and Edge Cases:**
  - **File Not Found:** Raise an error if the specified file does not exist.
  - **Missing Metadata Block:** Return an empty dictionary or raise a warning if no metadata block is found.
  - **Invalid Metadata Format:** Raise an error if the metadata block is improperly formatted or not valid YAML.
  - **Empty File:** Raise an error or return an empty dictionary if the file is empty.
  - **Optional Metadata:** Support additional, non-standard metadata fields while ensuring required fields are present.

## Dependencies

- **Libraries:**
  - ```os``` and ```pathlib```: For file validation and handling.
  - ```yaml``` (via PyYAML): For parsing the metadata block in YAML format.
  - ```logging```: To log warnings and errors during metadata extraction.
- **Best Practices:**
  - Use ```yaml.safe_load()``` for secure parsing of YAML blocks.
  - Validate metadata fields (e.g., required fields, valid date formats) during parsing.
  - Log errors or warnings for missing or malformed metadata.
  - Handle file operations in ```try-except``` blocks to gracefully manage errors (e.g., file not found, permission issues).

## Summary of Feature

The ```get_metadata``` function automates the retrieval of metadata from Markdown documents, ensuring consistency and efficiency in workflows that rely on structured metadata. By validating and returning the metadata as a dictionary, it provides a reliable foundation for document management tasks, including validation, editing, and reporting. This feature is critical for ensuring document integrity and compatibility in collaborative and automated environments.
