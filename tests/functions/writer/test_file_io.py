import pytest
from pathlib import Path
import os
from src.functions.writer.file_io import read_file, write_file, atomic_write

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

        # Mock replace to raise an error
        def mock_replace(self, target):
            raise OSError("Mock error")
        monkeypatch.setattr(Path, "replace", mock_replace)

        with pytest.raises(OSError):
            atomic_write(file_path, "test", 'utf-8', temp_dir)
        
        # Verify temp file was cleaned up
        assert not list(temp_dir.glob("temp_*"))

    def test_atomic_write_temp_dir_not_exists(self, tmp_path):
        """Test atomic write when temp directory doesn't exist."""
        file_path = tmp_path / "target.txt"
        temp_dir = tmp_path / "nonexistent"

        with pytest.raises(FileNotFoundError):
            atomic_write(file_path, "test", 'utf-8', temp_dir)

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