"""Document finalization and format conversion utilities."""

import logging
from pathlib import Path
from typing import Optional, Set, Dict, Any

# Try importing optional dependencies
try:
    import pypandoc
except ImportError:
    pypandoc = None  # Allow the module to load even if pypandoc isn't installed

try:
    import weasyprint  # Add conditional import
except ImportError:
    weasyprint = None  # Allow the module to load even if weasyprint isn't installed

from .config import WriterConfig
from .validation import validate_markdown
from .file_io import validate_file_access, read_file, atomic_write
from .file_validation import validate_file_inputs
from .exceptions import WriterError, FileValidationError
from .metadata_operations import MetadataOperations

logger = logging.getLogger(__name__)

SUPPORTED_FORMATS: Set[str] = {'md', 'pdf', 'html', 'docx', 'latex'}

DEFAULT_PANDOC_OPTIONS: Dict[str, Any] = {
    'pdf': {'pdf-engine': 'xelatex'},
    'html': {'standalone': True},
    'docx': {'reference-doc': None},  # Optional template
    'latex': {'top-level-division': 'chapter'}
}

def check_pandoc_availability() -> bool:
    """Check if pandoc is available for format conversion."""
    try:
        pypandoc.get_pandoc_version()
        return True
    except OSError:
        return False

def convert_document(
    input_path: Path,
    output_format: str,
    config: WriterConfig,
    pandoc_options: Dict[str, Any]
) -> Path:
    """Convert document to specified format using pandoc."""
    try:
        # Allow custom output directory from config
        output_dir = config.output_dir or input_path.parent
        output_path = output_dir / input_path.with_suffix(f'.{output_format}').name
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Convert using pypandoc with options
        pypandoc.convert_file(
            str(input_path),
            output_format,
            outputfile=str(output_path),
            format='markdown',
            **pandoc_options
        )
        
        return output_path
        
    except Exception as e:
        logger.error(f"Format conversion failed: {str(e)}")
        raise WriterError(f"Failed to convert document: {str(e)}")

def finalize_document(
    file_name: str,
    output_format: str = "md",
    config: Optional[WriterConfig] = None,
    pandoc_options: Optional[Dict[str, Any]] = None
) -> str:
    """Finalize document and convert to specified format if needed.
    
    Args:
        file_name: Name of the Markdown file to finalize
        output_format: Desired output format (md, pdf, html, docx, latex)
        config: Optional configuration object
        pandoc_options: Optional dictionary of pandoc-specific options
        
    Returns:
        Path to the finalized document as string
        
    Raises:
        WriterError: If validation fails or conversion fails
    """
    config = config or WriterConfig()
    file_path = Path(file_name)
    
    try:
        logger.info(f"Starting document finalization for {file_name}")
        
        # Validate metadata
        metadata_ops = MetadataOperations(config)
        try:
            metadata_ops.validate_metadata_block(file_path)
            logger.info("Metadata validation successful")
        except WriterError as e:
            logger.error(f"Metadata validation failed: {str(e)}")
            raise

        # Validate output format
        output_format = output_format.lower()
        if output_format not in SUPPORTED_FORMATS:
            raise WriterError(
                f"Unsupported output format: {output_format}. "
                f"Supported formats are: {', '.join(sorted(SUPPORTED_FORMATS))}"
            )
        
        # Validate inputs
        validate_file_inputs(
            file_path,
            config,
            require_write=True,
            check_extension=True
        )
        logger.info("Input validation successful")
        
        # Validate markdown content
        logger.info("Validating markdown content...")
        is_valid, errors = validate_markdown(file_name)
        if not is_valid:
            raise WriterError(
                f"Document validation failed:\n" + "\n".join(errors)
            )
        logger.info("Markdown validation successful")
            
        # If no format conversion needed, return original path
        if output_format == "md":
            logger.info("No format conversion needed, returning original path")
            return str(file_path)
            
        # Check pandoc availability for conversion
        logger.info("Checking Pandoc availability...")
        if not check_pandoc_availability():
            raise WriterError(
                "Pandoc is required for format conversion but not found"
            )
        
        # Check if output file exists
        output_path = file_path.with_suffix(f'.{output_format}')
        if output_path.exists():
            logger.warning(f"Output file already exists: {output_path}")
            raise WriterError(
                f"Output file already exists: {output_path}. "
                "Please remove it or use a different name."
            )
            
        # Get format-specific options
        format_options = DEFAULT_PANDOC_OPTIONS.get(output_format, {}).copy()
        if pandoc_options:
            format_options.update(pandoc_options)

        # Check for custom template in config
        if hasattr(config, f'{output_format}_template'):
            template_path = getattr(config, f'{output_format}_template')
            if template_path and Path(template_path).exists():
                format_options['reference-doc'] = template_path

        # Validate format-specific requirements
        validate_format_requirements(output_format, config)

        # Convert document
        logger.info(f"Converting document to {output_format}...")
        output_path = convert_document(
            file_path,
            output_format,
            config,
            format_options
        )
        logger.info(f"Document successfully converted to {output_path}")
        
        # Cleanup temporary files
        try:
            temp_patterns = [
                f"{file_path.stem}*.{output_format}.*",  # Format-specific temps
                f"{file_path.stem}*.aux",  # LaTeX auxiliary files
                f"{file_path.stem}*.log",  # Log files
                f"{file_path.stem}*.out"   # Output files
            ]
            
            temp_dir = Path(config.temp_dir)
            if temp_dir.exists():
                for pattern in temp_patterns:
                    for temp_file in temp_dir.glob(pattern):
                        try:
                            temp_file.unlink()
                            logger.debug(f"Cleaned up temporary file: {temp_file}")
                        except Exception as e:
                            logger.warning(f"Failed to cleanup temporary file {temp_file}: {e}")
        except Exception as e:
            logger.warning(f"Error during temporary file cleanup: {e}")
        
        return str(output_path)
        
    except Exception as e:
        logger.error(f"Document finalization failed: {str(e)}")
        raise WriterError(f"Failed to finalize document: {str(e)}") 

def validate_format_requirements(output_format: str, config: WriterConfig) -> None:
    """Validate format-specific requirements are met."""
    if output_format == 'pdf':
        # Check for LaTeX engine
        try:
            import subprocess
            subprocess.run(['xelatex', '--version'], 
                         capture_output=True, check=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            raise WriterError(
                "PDF conversion requires XeLaTeX. Please install TeX Live or similar."
            )
    
    elif output_format == 'html':
        # Check for HTML-specific requirements
        if 'standalone' in DEFAULT_PANDOC_OPTIONS['html']:
            if weasyprint is None:  # Use the global import check
                raise WriterError(
                    "HTML standalone conversion requires WeasyPrint for CSS processing."
                )
    
    elif output_format == 'docx':
        # Verify MS Word template if specified
        template_path = getattr(config, 'docx_template', None)
        if template_path and not Path(template_path).exists():
            raise WriterError(
                f"Specified Word template not found: {template_path}"
            )

def cleanup_temp_files(file_path: Path, output_format: str, config: WriterConfig) -> None:
    """Clean up temporary files created during conversion."""
    temp_dir = Path(config.temp_dir)
    if temp_dir.exists():
        patterns = [
            f"{file_path.stem}*.{output_format}.*",
            f"{file_path.stem}*.tex",  # LaTeX intermediates
            f"{file_path.stem}*.log",  # Conversion logs
            f"{file_path.stem}*.aux"   # Auxiliary files
        ]
        for pattern in patterns:
            for temp_file in temp_dir.glob(pattern):
                try:
                    temp_file.unlink()
                    logger.debug(f"Cleaned up temporary file: {temp_file}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup temporary file {temp_file}: {e}")