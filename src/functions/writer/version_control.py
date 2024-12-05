import logging
import shutil
from pathlib import Path
from typing import Union, Optional

from .exceptions import WriterError
from .file_validation import validate_file_inputs
from .metadata_operations import MetadataOperations
from .constants import (
    ERROR_VERSION_CREATE,
    ERROR_VERSION_EXISTS,
    LOG_VERSION_CREATED,
    LOG_VERSION_UPDATING
)
from .config import WriterConfig

logger = logging.getLogger(__name__)

def save_version(file_name: Union[str, Path], config: Optional[WriterConfig] = None) -> str:
    """Creates a versioned snapshot of a Markdown document.
    
    Creates a new file with an incremented version number appended to the original 
    file name (e.g., file_name_v1.md, file_name_v2.md). If the document contains
    version metadata, it will be updated in the original file.
    
    Args:
        file_name: Path to the Markdown file to version. Must exist and be a valid .md file.
        config: Optional WriterConfig instance. If not provided, default config will be used.
        
    Returns:
        str: Path to the created version file
        
    Raises:
        WriterError: If version creation fails or if a version conflict occurs
        FileValidationError: If input file validation fails
        
    Example:
        >>> save_version("document.md")
        'document_v2.md'
    """
    # Convert to Path object and validate inputs
    file_path = Path(file_name)
    if config is None:
        config = WriterConfig()
    validate_file_inputs(file_path, config, require_write=True, check_extension=True)
    
    # Initialize metadata operations
    metadata_ops = MetadataOperations()
    metadata = {}
    
    try:
        # Get current version from metadata if it exists
        current_version = 0  # Start at 0 so first version will be v1
        try:
            metadata = metadata_ops.get_metadata(file_path)
            if 'version' in metadata:
                current_version = int(metadata['version'])
        except (KeyError, ValueError, AttributeError):
            # If no metadata, invalid version, or metadata access fails, 
            # continue with default version
            pass
            
        # Generate new version file name
        new_version = current_version + 1
        version_file = file_path.parent / f"{file_path.stem}_v{new_version}{file_path.suffix}"
        
        # Ensure we don't overwrite existing version files
        while version_file.exists():
            logger.warning(ERROR_VERSION_EXISTS.format(file=version_file))
            new_version += 1
            version_file = file_path.parent / f"{file_path.stem}_v{new_version}{file_path.suffix}"
            
        # Create the versioned copy
        logger.info(LOG_VERSION_CREATED.format(
            source=file_path,
            target=version_file
        ))
        shutil.copy2(file_path, version_file)
        
        # Update metadata in original file if version tracking is enabled
        if metadata and 'version' in metadata:
            logger.info(LOG_VERSION_UPDATING.format(
                file=file_path,
                version=new_version
            ))
            metadata['version'] = str(new_version)  # Store as string for consistency
            metadata_ops.update_metadata(file_path, metadata)
            
        return str(version_file)
        
    except Exception as e:
        logger.error(ERROR_VERSION_CREATE.format(
            file=file_path,
            error=str(e)
        ))
        raise WriterError(ERROR_VERSION_CREATE.format(
            file=file_path,
            error=str(e)
        )) from e
