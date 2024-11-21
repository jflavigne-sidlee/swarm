from datetime import datetime
from pathlib import Path
import yaml
from typing import Dict, Optional

from .config import WriterConfig
from .exceptions import WriterError

def create_document(
    file_name: str,
    metadata: Dict[str, str],
    config: Optional[WriterConfig] = None
) -> Path:
    """Create a new Markdown document with YAML frontmatter metadata.
    
    Args:
        file_name: Name of the file to create (will be created in drafts directory)
        metadata: Dictionary of metadata (must include required fields from config)
        config: Optional WriterConfig instance (uses default if not provided)
        
    Returns:
        Path to the created document
        
    Raises:
        WriterError: If file already exists or metadata is invalid
    """
    # Use default config if none provided
    if config is None:
        config = WriterConfig()
        
    # Validate filename
    if not file_name or '/' in file_name or '\0' in file_name:
        raise WriterError("Invalid filename")
        
    # Ensure file has .md extension
    if not file_name.endswith('.md'):
        file_name += '.md'
    
    # Construct full file path in drafts directory
    file_path = config.drafts_dir / file_name
    
    try:
        # Check if file already exists
        if file_path.exists():
            raise WriterError(f"File already exists: {file_path}")
            
        # Validate required metadata fields
        missing_fields = [field for field in config.metadata_keys 
                         if field not in metadata]
        if missing_fields:
            raise WriterError(
                f"Missing required metadata fields: {', '.join(missing_fields)}"
            )
        
        # Create drafts directory if it doesn't exist
        if config.create_directories:
            config.drafts_dir.mkdir(parents=True, exist_ok=True)
            
        # Write file with YAML frontmatter
        with open(file_path, 'w', encoding=config.default_encoding) as f:
            # Write YAML frontmatter
            f.write('---\n')
            yaml.dump(metadata, f, default_flow_style=False)
            f.write('---\n\n')
            
        return file_path
            
    except (OSError, yaml.YAMLError) as e:
        raise WriterError(f"Failed to create document: {str(e)}")
