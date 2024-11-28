import yaml
from typing import Dict, Any

def format_metadata_block(metadata: Dict[str, Any], content: str = "") -> str:
    """
    Format metadata and content into a YAML front matter block.
    
    Args:
        metadata: Dictionary of metadata to format
        content: Optional content to append after metadata block
        
    Returns:
        Formatted string with YAML front matter
    """
    return f"---\n{yaml.dump(metadata, default_flow_style=False, allow_unicode=True)}---\n{content}" 