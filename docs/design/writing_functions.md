

# Module Overview: Markdown Document Management System

## Purpose

The Markdown Document Management System is designed to facilitate collaborative creation, editing, validation, and finalization of Markdown documents. 
It aims to enable seamless interactions between agents (both AI-driven and human) by providing a robust framework for structured content generation and management.

## Core Objectives

    1. **Streamlined Document Creation:**
        - Enable the automated generation and organization of Markdown documents, adhering to a consistent structure and format.
    2. **Efficient Editing and Updating:**
        - Provide tools for locating, modifying, and appending specific sections of documents, ensuring changes are easy to track and apply.
    3. **Validation and Integrity:**
        - Include mechanisms to validate Markdown content, ensuring syntax correctness and compatibility with various Markdown parsers.
    4. **Version Control:**
        - Support versioning of documents, allowing for snapshots of progress and the ability to track changes over time.
    5. **Scalability:**
        - Handle long or complex documents incrementally (e.g., streaming content), making it suitable for use in resource-constrained environments or multi-agent systems.
    6. **Extensibility:**
        - Provide a modular design that allows the addition of new features, such as exporting to other formats (PDF, HTML) or integrating with collaborative editing tools.

## Module Scope

The module is built to handle the entire lifecycle of Markdown document management, from initial creation to finalization. Key features include:
    - **Document Initialization:** Setting up a new Markdown file with metadata and a clean structure.
    - **Content Management:** Appending, editing, retrieving, or streaming sections of content.
    - **Metadata Handling:** Managing document metadata such as title, author, date, and custom tags.
    - **Validation:** Ensuring the document complies with Markdown standards and supports downstream conversion to other formats.
    - **File Storage and Organization:** Managing temporary files, drafts, and finalized outputs.
    - **Collaborative Editing Support:** Locking mechanisms to prevent conflicts during multi-agent or multi-user edits.

## Target Audience

    1. **Developers:**
        - Those building AI systems that generate structured content.
        - Developers integrating Markdown management into larger systems.
    2. **Content Creators and Editors:**
        - Teams using AI-driven tools to create, edit, or publish documents in Markdown format.
    3. **Multi-Agent Systems:**
        - Environments where multiple agents collaborate on document production in an incremental or conversational manner.

## Guiding Principles

    1. **Modularity:** Each function should perform a single, clearly defined task.
    2. **Reusability:** Code should be reusable across different projects or systems.
    3. **Error Resilience:** The system should handle edge cases gracefully and provide meaningful feedback.
    4. **Human Readability:** Outputs should be structured to be clear and intuitive for human readers.

## High-Level Architecture

The module is composed of several interconnected components:
    1. **Core Functionality:**
        - File operations (creation, reading, writing).
        - Section management (append, edit, retrieve).
        - Metadata handling.
    2. **Validation Layer:**
        - Syntax checks and formatting validation.
    3. **Storage System:**
        - Temporary files for streaming content.
        - Drafts for work-in-progress documents.
        - Finalized files for completed documents.
    4. **Extension Layer:**
        - Exporting content to other formats.
        - Collaborative tools and locking mechanisms.

## Example Use Case

An AI agent collaborates with a team to create a project plan:
    1. The agent initializes a new Markdown document with metadata.
    2. Team members and the AI append user stories, edit specific sections, and validate the document's structure.
    3. The AI streams updates to sections, locks portions of the document during edits, and tracks changes.
    4. The finalized document is exported as Markdown and converted to a PDF for distribution.

## Outcome

The module empowers teams and systems to manage Markdown documents efficiently, leveraging AI-driven functionality to enhance productivity, organization, and content quality.

## Core Functions

1. create_document(file_name: str, metadata: dict) -> None
    - **Purpose:** Initialize a new Markdown document with metadata at the top.
    - **Behavior:**
        - Create a file with the given name.
        - Add metadata (e.g., title, author, date) in a comment block at the start of the file.
        - Ensure the file is ready for incremental updates.
    - **Notes:**
        - Metadata keys should support standard values like title, author, and date.
        - This feature is implemented in src/functions/writer/file_operations.py

2. append_section(file_name: str, section_title: str, content: str) -> None
    - **Purpose:** Add a new section to the Markdown document under a given title.
    - **Behavior:**
        - If the section already exists, raise an error or append to the existing section based on user preference.
        - Use Markdown headers (#, ##, etc.) to delineate sections.
        - Add a unique marker (e.g., <!-- Section: section_title -->) below the header for easy identification.
    - **Notes:**
        - Ensure no duplicate section titles unless explicitly allowed.
        - this feature is implemented in src/functions/writer/file_operations.py

3. edit_section(file_name: str, section_title: str, new_content: str) -> None
    - **Purpose:** Locate a specific section by title and replace its content with new content.
    - **Behavior:**
        - Use the unique marker (<!-- Section: section_title -->) to locate the section.
        - Replace all content between the section’s start marker and the next header or end of file.
    - **Notes:**
        - Ensure proper Markdown formatting during edits.
        - this feature is implemented in src/functions/writer/file_operations.py
    
4. get_section(file_name: str, section_title: str) -> str
    - **Purpose:** Retrieve the content of a specific section for preview or analysis.
    - **Behavior:**
        - Search for the section marker and return all content until the next section marker or end of file.
    - **Notes:**
        - Return an error if the section is not found.
        - this feature is implemented in src/functions/writer/file_operations.py

5. finalize_document(file_name: str, output_format: str = "md") -> str
    - **Purpose:** Finalize the document and optionally convert it to another format (e.g., PDF, HTML).
    - **Behavior:**
        - Ensure all Markdown syntax is valid.
        - If output format is specified, use a library or tool to convert the document.
        - Save the final document and return its path.
    - **Notes:**
        - Support additional formats with appropriate tools (e.g., Pandoc for PDF).
        - this feature is implemented in src/functions/writer/finalize.py

## Advanced Functions

6. lock_section(file_name: str, section_title: str) -> bool
    - **Purpose:** Temporarily prevent other agents from editing a specific section.
    - **Behavior:**
        - Create a lock marker in the document's metadata or a temporary file.
        - Return True if the lock is successful, False if the section is already locked.
    - **Notes:**
        - Ensure locks are removed when edits are complete or after a timeout.
        - this feature is implemented in src/functions/writer/locking.py

7. save_version(file_name: str) -> str
    - **Purpose:** Save the current state of the document as a versioned snapshot.
    - **Behavior:**
    - Copy the current document to a versioned file (e.g., file_name_v1.md).
    - Store version metadata in the original file if required.
    - **Notes:**
        - Ensure versioning does not overwrite prior snapshots.
        - this feature is implemented in src/functions/writer/version_control.py

8. search_and_replace(file_name: str, search_text: str, replace_text: str) -> int
    - **Purpose:** Find and replace text across the entire document or within a specific section.
    - **Behavior:**
        - Search for all instances of search_text in the document.
        - Replace them with replace_text.
        - Return the count of replacements made.
    - **Notes:**
        - Support case sensitivity and regex-based searches if needed.
        - this feature is implemented in src/functions/writer/file_operations.py

9. section_exists(file_name: str, section_title: str) -> bool
    - **Purpose:** Check if a section exists in the document.
    - **Behavior:**
        - Search for the section marker (<!-- Section: section_title -->).
        - Return True if found, False otherwise.
    - **Notes:**
        - this feature is implemented in src/functions/writer/file_operations.py

10. stream_content(file_name: str, content: str, chunk_size: int = 1024) -> None
    - **Purpose:** Append content to the document incrementally for long sections or large documents.
    - **Behavior:**
        - Split content into chunks of chunk_size bytes.
        - Write each chunk to the file sequentially.
    - **Notes:**
        - Maintain formatting integrity across chunks.
        - this feature is implemented in src/functions/writer/streaming.py

11. validate_markdown(file_name: str) -> bool
    - **Purpose:** Check if the document follows Markdown standards.
    - **Behavior:**
        - Parse the document to detect broken links, invalid tables, or unsupported syntax.
        - Return True if valid, False otherwise, with an error log.
    - **Notes:**
        - Use external Markdown validators if necessary.
        - this feature is implemented in src/functions/writer/validation.py

12. get_metadata(file_name: str) -> dict
    - **Purpose:** Retrieve metadata from the document.
    - **Behavior:**
        - Parse the top metadata block for keys like title, author, date.
        - Return metadata as a dictionary.
    - **Notes:**
        - Validate that metadata follows a consistent format.
        - this feature is implemented in src/functions/writer/metadata_operations.py

13.	update_metadata(file_name: str, new_metadata: dict) -> None
    - **Purpose:** Update or add metadata fields in the document.
    - **Behavior:**
        - Overwrite or add new fields to the metadata block.
        - Preserve formatting.
    - **Notes:**
        - Avoid overwriting essential fields unless specified.
        - this feature is implemented in src/functions/writer/metadata_operations.py
        
## Core Modules (Built-in)

    1. **os and pathlib**
        - For file management, such as creating, reading, and writing files, and handling file paths.
        - Relevant for functions like create_document, finalize_document, and save_version.
    2. **re**
        - For searching and editing specific sections using regular expressions (e.g., parsing <!-- Section: ... --> markers).
        - Critical for functions like edit_section, search_and_replace, and section_exists.
    3. **shutil**
        - For creating versioned snapshots of files.
        - Relevant for save_version.
    4. **filelock**
        - For locking sections to prevent concurrent edits.
        - Useful for lock_section.
    5. **tempfile**
        - For handling temporary files during streaming or content validation.
        - Relevant for stream_content or validate_markdown.
    6. **json and yaml**
        - For handling metadata or configuration files if you choose to store these in external files.
        - Useful for get_metadata and update_metadata.

Third-Party Modules

    1. **markdown**
        - A Python library to parse and validate Markdown.
        - Relevant for validate_markdown and finalize_document.
    2. **mistune**
        - A lightweight Markdown parser that is easy to extend.
        - Alternative to the markdown module for advanced parsing.
    3. **PyYAML**
        - For handling metadata in YAML format, which is commonly embedded in Markdown documents (e.g., for front matter).
        - Relevant for get_metadata and update_metadata.
    4. **Markdown2**
        - Another Markdown parser that also supports conversion to HTML.
        - Useful for finalize_document when exporting to formats like HTML.
    5. **pandoc via pypandoc**
        - A Python wrapper for Pandoc, a universal document converter.
        - Essential for finalize_document if exporting to formats like PDF, DOCX, or LaTeX.
    6. **difflib**
        - For comparing document versions or showing changes when editing sections.
        - Useful for collaborative workflows or save_version.
    7. **watchdog**
        - For monitoring file changes during streaming or collaborative editing.
        - Useful for real-time updates in multi-agent environments.
    8. **logging**
        - For tracking operations, errors, and edits, especially in collaborative or production environments.
        - Relevant across all functions for debugging and monitoring.
    9. **aiofiles**
        - For asynchronous file operations, especially useful in streaming large documents or collaborative environments.
        - Relevant for stream_content.
    10. **pytest**
        - For unit testing the functions to ensure robustness.
        - Critical for validating the correctness of functions like edit_section, validate_markdown, etc.

Optional Modules (Advanced Use Cases)

    1. **beautifulsoup4**
        - If parsing or extracting content from HTML-converted Markdown becomes necessary.
        - Useful for enhancing finalize_document.
    2. **rich**
        - For formatting logs or previews of sections in the console (e.g., colorized Markdown previews).
        - Useful for debugging and get_section.
    3. **gitpython**
        - For managing version control directly within the system, especially for save_version.
        - Allows integration with Git for collaborative editing and history tracking.
    4. **multiprocessing**
        - For handling concurrent agent actions, such as editing different sections simultaneously.
        - Useful for lock_section and stream_content.
    5. **openai or transformers**
        - If generative AI is embedded directly for producing or editing content.
        - Useful for generating content for append_section or validating edit_section.

## Module Mapping to Functions

| Function | Modules |
|----------|---------|
| create_document | os, pathlib, json, yaml |
| append_section | os, re, markdown, aiofiles |
| edit_section | re, os, markdown |
| get_section | re, os |
| finalize_document | markdown, pypandoc, os |
| lock_section | filelock, multiprocessing |
| save_version | shutil, gitpython |
| search_and_replace | re, aiofiles |
| stream_content | aiofiles, tempfile |
| validate_markdown | markdown, mistune, logging |
| get_metadata | yaml, json |
| update_metadata | yaml, json |

## Project Structure
project_name/
├── src/
│   ├── functions/
│   │   ├── writer/
│   │   │   ├── __init__.py
│   │   │   ├── config.py               # Configuration management
│   │   │   ├── constants.py            # Shared constants
│   │   │   ├── errors.py               # Error messages
│   │   │   ├── exceptions.py           # Custom exceptions
│   │   │   ├── file_io.py             # Low-level file operations
│   │   │   ├── file_operations.py      # Core file operations and section handling
│   │   │   ├── file_validation.py      # File-specific validation
│   │   │   ├── finalize.py            # Document finalization
│   │   │   ├── locking.py             # Section locking
│   │   │   ├── logs.py                # Logging messages
│   │   │   ├── metadata_operations.py  # Metadata management
│   │   │   ├── metadata_utils.py       # Metadata utility functions
│   │   │   ├── patterns.py            # Pattern matching constants
│   │   │   ├── suggestions.py         # Error suggestions
│   │   │   ├── utils.py               # System-related utility functions
│   │   │   ├── validation.py          # Markdown validation
│   │   │   ├── validation_constants.py # Validation constants
│   │   │   └── version_control.py      # Version management
│   ├── utils/
│   │   ├── __init__.py
├── tests/
│   ├── functions/
│   │   └── writer/
│   │       ├── test_config.py
│   │       ├── test_file_io.py
│   │       ├── test_file_operations.py
│   │       ├── test_file_validation.py
│   │       ├── test_finalize.py
│   │       ├── test_locking.py
│   │       ├── test_metadata_operations.py
│   │       ├── test_validation.py
│   │       └── test_version_control.py
│   ├── utils/
│   └── conftest.py                # Test configurations
├── data/
│   ├── temp/                      # Temporary files
│   │   └── .gitkeep
│   ├── finalized/                 # Finalized documents
│   │   └── .gitkeep
│   ├── drafts/                    # Work in progress
│   │   └── .gitkeep
│   └── .gitignore                 # Ignore temp files but keep structure
├── docs/
│   ├── design/
│   │   ├── done/                 # Completed design docs
│   │   └── to_do/               # Pending design docs
│   ├── api_reference.md
│   └── user_guide.md
├── .env.example                  # Example environment variables
├── requirements.txt              # Production dependencies
├── requirements-dev.txt          # Development dependencies
├── setup.py                     # Package setup
├── MANIFEST.in                  # Package manifest
└── README.md


### Explanation of Key Folders

1. src/functions/
    - This is where all core functions are implemented. It’s divided into modules (e.g., file_operations.py, metadata_operations.py) to keep related logic grouped.
    - By separating logic into files, you can avoid bloated code and make individual functions easier to test and maintain.
2. src/utils/
    - This contains utility scripts like logging (logger.py) or configuration management (config_loader.py) that are shared across multiple functions.
3. data/
    - temp/: Temporary files created during streaming or intermediate processing. These can be purged periodically or upon process termination.
    - finalized/: Finalized documents, stored here for long-term usage or conversion to other formats.
    - drafts/: Drafts actively being worked on, possibly by multiple agents.
    - Keeping data outside the src/ folder ensures a clear separation of logic (code) and state (files).
4. tests/
    - Unit tests for each functional module. Use a testing framework like pytest to ensure each function behaves as expected.
5. docs/
    - Store documentation for your project here. This includes API references for the functions and user guides for developers or end-users.

### Additional Notes

- config_loader.py:
    - Use this to load paths, file types, and other configurations from a centralized file like config.yaml or config.json.
    - Example configuration:

```python
paths:
  temp: "data/temp"
  finalized: "data/finalized"
  drafts: "data/drafts"
```

- Environment Variables:
    - Use .env files with a library like python-dotenv for sensitive settings (e.g., output format defaults or API keys).
- Temporary File Management:
    - Use a library like tempfile for managing temporary files dynamically, ensuring cleanup even after crashes.  

## String Handling Rules
**NEVER modify content**
- No .strip()
- No .rstrip()
- No .lstrip()
- No newline normalization
- No whitespace "fixing"
**Preserve EXACT content**
- Keep all newlines exactly as found
- Keep all whitespace exactly as found
- Keep all trailing spaces exactly as found
- Keep all blank lines exactly as found
**Pattern Matching**
- Match patterns exactly as they appear
- Don't try to "clean up" or "normalize" matches
- Use raw strings (r"pattern") for regex to avoid escaping issues
**Content Boundaries**
- When finding sections, preserve ALL content between markers
- Don't add or remove newlines at section boundaries
- Don't modify spacing between sections
**Document Structure**
- The document's exact structure is the caller's responsibility
- Our job is to find and replace content, not format it
- Let the tests define the expected format
**Remember**
- We are a FINDER and REPLACER
- We are NOT a formatter
- We are NOT a normalizer
- We are NOT a cleaner
This will help avoid future issues where we try to be "helpful" by cleaning up content when we should just be preserving it exactly as is.  