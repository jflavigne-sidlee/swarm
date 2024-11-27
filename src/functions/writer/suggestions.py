
# Error suggestions for common markdown issues
from typing import Final

ERROR_SUGGESTIONS = {
    # Markdownlint rules
    "MD007": "Fix list indentation to use 2 spaces",
    "MD022": "Add blank lines before and after headers",
    "MD031": "Add blank lines around code blocks",
    "MD032": "Add blank lines before lists",
    "MD034": "Use bare URLs in angle brackets <url>",
    "MD037": "Remove spaces inside emphasis markers",
    # Remark-lint rules
    "no-undefined-references": "Ensure all referenced links and images are defined",
    "no-empty-sections": "Add content to empty sections or remove them",
    "heading-increment": "Headers should increment by one level at a time",
    "no-duplicate-headings": "Use unique heading text within sections",
    # Content validation
    "broken_image": "Ensure image file exists in the specified path",
    "broken_link": "Verify the linked file exists in the correct location",
    "empty_file": "Add content to the markdown file",
    # GFM-specific suggestions
    "table-pipe-alignment": "Align table pipes vertically for better readability",
    "table-cell-padding": "Add single space padding around table cell content",
    "no-undefined-references": "Define all referenced links at the bottom of the document",
    "heading-increment": "Headers should only increment by one level at a time",
    "no-duplicate-headings": "Use unique heading text within each section",
    "task-list-marker": 'Use "[ ]" or "[x]" for task list items',
    "task-list-indent": "Task lists should be indented with 2 spaces",
    "task-list-empty": "Task list items should not be empty",
    "task-list-spacing": 'Add a space after the dash: "- [ ]"',
}


SUGGESTION_HEADER_LEVEL: Final = "Suggestion: Use {suggested} instead of {current}"
SUGGESTION_BROKEN_IMAGE: Final = (
    "Ensure the image file exists in the correct location and the path is correct"
)
SUGGESTION_BROKEN_LINK: Final = (
    "Check if the linked file exists and the path is correct"
)
SUGGESTION_TASK_LIST_FORMAT: Final = (
    "Use exactly one space after dash: '- [ ]' or '- [x]'"
)