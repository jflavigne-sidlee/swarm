import pytest
from pathlib import Path
import os
from src.functions.writer.file_io import read_file, write_file, atomic_write, validate_encoding
import shutil

@pytest.fixture
def test_file(tmp_path) -> Path:
    """Create a temporary test file."""
    return tmp_path / "test.txt"

@pytest.fixture
def test_content() -> str:
    """Test content with various whitespace and newline patterns."""
    return (
        "First line\n"
        "  Indented line  \n"
        "\n"
        "Line with trailing space  \n"
        "Last line without newline"
    )

class TestReadFile:
    def test_read_file_preserves_content(self, test_file, test_content):
        """Test that read_file preserves exact content."""
        test_file.write_text(test_content, encoding='utf-8')
        result = read_file(test_file, 'utf-8')
        assert result == test_content

    def test_read_file_empty(self, test_file):
        """Test reading empty file."""
        test_file.write_text("", encoding='utf-8')
        result = read_file(test_file, 'utf-8')
        assert result == ""

    def test_read_file_only_whitespace(self, test_file):
        """Test reading file with only whitespace."""
        content = "  \n\t\n  \n"
        test_file.write_text(content, encoding='utf-8')
        result = read_file(test_file, 'utf-8')
        assert result == content

    def test_read_file_nonexistent(self, test_file):
        """Test reading nonexistent file raises error."""
        with pytest.raises(FileNotFoundError):
            read_file(test_file, 'utf-8')

    def test_read_file_different_encodings(self, test_file):
        """Test reading file with different encodings."""
        content = "Hello 世界\n"
        encodings = ['utf-8', 'utf-16', 'ascii']
        
        for encoding in encodings:
            if encoding == 'ascii':
                # Should fail with non-ASCII content
                with pytest.raises(UnicodeEncodeError):
                    test_file.write_text(content, encoding=encoding)
            else:
                test_file.write_text(content, encoding=encoding)
                result = read_file(test_file, encoding)
                assert result == content

class TestWriteFile:
    def test_write_file_preserves_content(self, test_file, test_content):
        """Test that write_file preserves exact content."""
        write_file(test_file, test_content, 'utf-8')
        result = test_file.read_text(encoding='utf-8')
        assert result == test_content

    def test_write_file_empty(self, test_file):
        """Test writing empty content."""
        write_file(test_file, "", 'utf-8')
        result = test_file.read_text(encoding='utf-8')
        assert result == ""

    def test_write_file_only_whitespace(self, test_file):
        """Test writing only whitespace."""
        content = "  \n\t\n  \n"
        write_file(test_file, content, 'utf-8')
        result = test_file.read_text(encoding='utf-8')
        assert result == content

    def test_write_file_permission_error(self, tmp_path):
        """Test writing to readonly directory raises error."""
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        readonly_file = readonly_dir / "test.txt"
        
        # Make directory readonly
        os.chmod(readonly_dir, 0o444)
        
        with pytest.raises(PermissionError):
            write_file(readonly_file, "test", 'utf-8')

    def test_write_file_creates_parent_directory(self, tmp_path):
        """Test write_file creates parent directories as needed."""
        deep_path = tmp_path / "a" / "b" / "c" / "test.txt"
        content = "test content"
        
        write_file(deep_path, content, 'utf-8')
        
        assert deep_path.exists()
        assert deep_path.read_text(encoding='utf-8') == content
        assert deep_path.parent.is_dir()

    def test_write_file_parent_directory_not_writable(self, tmp_path):
        """Test write_file when parent directory can't be created."""
        # Create a read-only directory
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        os.chmod(readonly_dir, 0o444)
        
        file_path = readonly_dir / "subdir" / "test.txt"
        
        with pytest.raises(PermissionError) as exc_info:
            write_file(file_path, "test", 'utf-8')
        
        assert "Permission denied" in str(exc_info.value)

    def test_validate_encoding_supported(self):
        """Test validation of supported encodings."""
        assert validate_encoding('utf-8')
        assert validate_encoding('ascii')
        assert validate_encoding('utf-16')

    def test_validate_encoding_unsupported(self):
        """Test validation of unsupported encodings."""
        assert not validate_encoding('invalid-encoding')
        assert not validate_encoding('not-real')

    def test_write_file_unsupported_encoding(self, tmp_path):
        """Test write_file with unsupported encoding."""
        file_path = tmp_path / "test.txt"
        
        with pytest.raises(LookupError) as exc_info:
            write_file(file_path, "test", 'invalid-encoding')
        
        assert "Unsupported encoding" in str(exc_info.value)
        assert not file_path.exists()

class TestAtomicWrite:
    def test_atomic_write_success(self, tmp_path):
        """Test successful atomic write operation."""
        file_path = tmp_path / "target.txt"
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()
        content = "Test content\n"

        atomic_write(file_path, content, 'utf-8', temp_dir)
        
        # Verify content
        assert file_path.read_text(encoding='utf-8') == content
        # Verify temp file was cleaned up
        assert not list(temp_dir.glob("temp_*"))

    def test_atomic_write_preserves_content(self, tmp_path, test_content):
        """Test that atomic_write preserves exact content."""
        file_path = tmp_path / "target.txt"
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()

        atomic_write(file_path, test_content, 'utf-8', temp_dir)
        result = file_path.read_text(encoding='utf-8')
        assert result == test_content

    def test_atomic_write_cleanup_on_error(self, tmp_path, monkeypatch):
        """Test temp file cleanup when error occurs during atomic write."""
        file_path = tmp_path / "target.txt"
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()

        # Mock shutil.move to raise an error
        def mock_move(src, dst):
            raise OSError("Mock error")
        monkeypatch.setattr(shutil, "move", mock_move)

        with pytest.raises(OSError):
            atomic_write(file_path, "test", 'utf-8', temp_dir)
        
        # Verify temp file was cleaned up
        temp_files = list(temp_dir.iterdir())
        assert len(temp_files) == 0, "Temporary file was not cleaned up"

    def test_atomic_write_temp_dir_not_exists(self, tmp_path):
        """Test atomic write when temp directory doesn't exist."""
        file_path = tmp_path / "target.txt"
        temp_dir = tmp_path / "nonexistent"
        
        # Ensure temp_dir doesn't exist
        if temp_dir.exists():
            temp_dir.rmdir()
        
        with pytest.raises(FileNotFoundError) as exc_info:
            atomic_write(file_path, "test", 'utf-8', temp_dir)
        
        assert "Path not found" in str(exc_info.value)
        assert not file_path.exists()  # Target file should not be created

    def test_atomic_write_concurrent_access(self, tmp_path):
        """Test atomic write with concurrent access simulation."""
        file_path = tmp_path / "target.txt"
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()
        
        # Write initial content
        file_path.write_text("initial", encoding='utf-8')
        
        # Simulate concurrent writes
        contents = ["content1\n", "content2\n", "content3\n"]
        for content in contents:
            atomic_write(file_path, content, 'utf-8', temp_dir)
            # Verify content after each write
            assert file_path.read_text(encoding='utf-8') == content 
            
    def test_atomic_write_temp_dir_not_writable(self, tmp_path):
        """Test atomic write with non-writable temp directory."""
        file_path = tmp_path / "target.txt"
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()
        
        # Make temp directory read-only
        os.chmod(temp_dir, 0o444)
        
        with pytest.raises(PermissionError) as exc_info:
            atomic_write(file_path, "test", 'utf-8', temp_dir)
        
        assert "Path not writable" in str(exc_info.value)
        assert not file_path.exists()

    def test_atomic_write_target_not_writable(self, tmp_path):
        """Test atomic write with non-writable target file."""
        file_path = tmp_path / "target.txt"
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()
        
        # Create target file as read-only
        file_path.write_text("original")
        os.chmod(file_path, 0o444)
        
        with pytest.raises(PermissionError) as exc_info:
            atomic_write(file_path, "test", 'utf-8', temp_dir)
        
        assert "Path not writable" in str(exc_info.value)
        assert file_path.read_text() == "original"  # Content unchanged

    def test_atomic_write_unsupported_encoding(self, tmp_path):
        """Test atomic_write with unsupported encoding."""
        file_path = tmp_path / "test.txt"
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()
        
        with pytest.raises(LookupError) as exc_info:
            atomic_write(file_path, "test", 'invalid-encoding', temp_dir)
        
        assert "Unsupported encoding" in str(exc_info.value)
        assert not file_path.exists()
        # Verify no temp files were left behind
        assert len(list(temp_dir.iterdir())) == 0

# pytest tests/functions/writer/test_file_io.py -v