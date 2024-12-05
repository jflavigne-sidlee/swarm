import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.functions.writer.finalize import finalize_document, WriterError
from src.functions.writer.config import WriterConfig
from src.functions.writer.metadata_operations import MetadataOperations

class TestFinalizeDocument(unittest.TestCase):

    def setUp(self):
        # Create mock for MetadataOperations
        self.metadata_ops_patcher = patch('src.functions.writer.finalize.MetadataOperations')
        self.mock_metadata_ops = self.metadata_ops_patcher.start()
        # Configure the mock
        self.mock_metadata_ops.return_value.validate_metadata_block.return_value = None
        
    def tearDown(self):
        self.metadata_ops_patcher.stop()

    @patch('src.functions.writer.finalize.validate_file_inputs')
    @patch('src.functions.writer.finalize.validate_markdown')
    @patch('src.functions.writer.finalize.check_pandoc_availability')
    @patch('src.functions.writer.finalize.convert_document')
    @patch('src.functions.writer.finalize.validate_format_requirements')
    def test_finalize_document_success(self, mock_validate_format, mock_convert, mock_check_pandoc, mock_validate_md, mock_validate_inputs):
        # Setup mocks
        mock_validate_inputs.return_value = None
        mock_validate_md.return_value = (True, [])
        mock_check_pandoc.return_value = True
        mock_convert.return_value = Path("output.pdf")
        mock_validate_format.return_value = None

        # Test successful finalization
        result = finalize_document("test.md", "pdf", WriterConfig())
        self.assertEqual(result, "output.pdf")
        mock_validate_inputs.assert_called_once()
        mock_validate_md.assert_called_once()
        mock_check_pandoc.assert_called_once()
        mock_convert.assert_called_once()
        mock_validate_format.assert_called_once()

    @patch('src.functions.writer.finalize.validate_file_inputs')
    @patch('src.functions.writer.finalize.validate_markdown')
    def test_finalize_document_invalid_markdown(self, mock_validate_md, mock_validate_inputs):
        # Setup mocks
        mock_validate_inputs.return_value = None
        mock_validate_md.return_value = (False, ["Error: Invalid syntax"])

        # Test markdown validation failure
        with self.assertRaises(WriterError) as context:
            finalize_document("test.md", "pdf", WriterConfig())
        self.assertIn("Document validation failed", str(context.exception))
        mock_validate_md.assert_called_once()

    @patch('src.functions.writer.finalize.validate_file_inputs')
    @patch('src.functions.writer.finalize.validate_markdown')
    @patch('src.functions.writer.finalize.check_pandoc_availability')
    def test_finalize_document_pandoc_unavailable(self, mock_check_pandoc, mock_validate_md, mock_validate_inputs):
        # Setup mocks
        mock_validate_inputs.return_value = None
        mock_validate_md.return_value = (True, [])
        mock_check_pandoc.return_value = False

        # Test Pandoc availability failure
        with self.assertRaises(WriterError) as context:
            finalize_document("test.md", "pdf", WriterConfig())
        self.assertIn("Pandoc is required for format conversion but not found", str(context.exception))
        mock_check_pandoc.assert_called_once()

    @patch('src.functions.writer.finalize.validate_file_inputs')
    @patch('src.functions.writer.finalize.validate_markdown')
    @patch('src.functions.writer.finalize.check_pandoc_availability')
    @patch('src.functions.writer.finalize.convert_document')
    def test_finalize_document_unsupported_format(self, mock_convert, mock_check_pandoc, mock_validate_md, mock_validate_inputs):
        # Setup mocks
        mock_validate_inputs.return_value = None
        mock_validate_md.return_value = (True, [])
        mock_check_pandoc.return_value = True

        # Test unsupported format
        with self.assertRaises(WriterError) as context:
            finalize_document("test.md", "unsupported_format", WriterConfig())
        self.assertIn("Unsupported output format", str(context.exception))

    @patch('src.functions.writer.finalize.validate_file_inputs')
    def test_finalize_document_file_not_found(self, mock_validate_inputs):
        # Setup mocks
        mock_validate_inputs.side_effect = FileNotFoundError("File not found")

        # Test file not found error
        with self.assertRaises(WriterError) as context:
            finalize_document("nonexistent.md", "pdf", WriterConfig())
        self.assertIn("File not found", str(context.exception))
        mock_validate_inputs.assert_called_once()

    @patch('src.functions.writer.finalize.validate_file_inputs')
    @patch('src.functions.writer.finalize.validate_markdown')
    @patch('src.functions.writer.finalize.check_pandoc_availability')
    @patch('src.functions.writer.finalize.convert_document')
    def test_finalize_document_file_overwrite_protection(self, mock_convert, mock_check_pandoc, mock_validate_md, mock_validate_inputs):
        # Setup mocks
        mock_validate_inputs.return_value = None
        mock_validate_md.return_value = (True, [])
        mock_check_pandoc.return_value = True

        # Simulate existing output file
        with patch('pathlib.Path.exists', return_value=True):
            with self.assertRaises(WriterError) as context:
                finalize_document("test.md", "pdf", WriterConfig())
            self.assertIn("Output file already exists", str(context.exception))

    @patch('src.functions.writer.finalize.validate_file_inputs')
    @patch('src.functions.writer.finalize.validate_markdown')
    @patch('src.functions.writer.finalize.check_pandoc_availability')
    @patch('src.functions.writer.finalize.convert_document')
    def test_finalize_document_pdf_conversion_requires_xelatex(self, mock_convert, mock_check_pandoc, mock_validate_md, mock_validate_inputs):
        # Setup mocks
        mock_validate_inputs.return_value = None
        mock_validate_md.return_value = (True, [])
        mock_check_pandoc.return_value = True

        # Simulate XeLaTeX not installed
        with patch('subprocess.run', side_effect=FileNotFoundError("XeLaTeX not found")):
            with self.assertRaises(WriterError) as context:
                finalize_document("test.md", "pdf", WriterConfig())
            self.assertIn("PDF conversion requires XeLaTeX", str(context.exception))

if __name__ == '__main__':
    unittest.main() 


# pytest tests/functions/writer/test_finalize.py -v