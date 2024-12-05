import pytest
import os
import shutil
from pathlib import Path
from src.functions.writer.file_io import (
    ensure_file_newline,
    stream_chunks,
    read_file,
    write_file,
    atomic_write,
    validate_encoding,
    stream_document_content,
    validate_file_access,
    cleanup_partial_file,
)
from src.functions.writer.exceptions import (
    MarkdownIntegrityError,
    FilePermissionError,
)
from src.functions.writer.errors import (
    ERROR_UNSUPPORTED_ENCODING,
    ERROR_PATH_NOT_FOUND,
    ERROR_PATH_NO_READ,
    ERROR_PATH_NOT_EXIST
)

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
        test_file.write_text(test_content, encoding="utf-8")
        result = read_file(test_file, "utf-8")
        assert result == test_content

    def test_read_file_empty(self, test_file):
        """Test reading empty file."""
        test_file.write_text("", encoding="utf-8")
        result = read_file(test_file, "utf-8")
        assert result == ""

    def test_read_file_only_whitespace(self, test_file):
        """Test reading file with only whitespace."""
        content = "  \n\t\n  \n"
        test_file.write_text(content, encoding="utf-8")
        result = read_file(test_file, "utf-8")
        assert result == content

    def test_read_file_nonexistent(self, test_file):
        """Test reading nonexistent file raises error."""
        with pytest.raises(FileNotFoundError):
            read_file(test_file, "utf-8")

    def test_read_file_different_encodings(self, test_file):
        """Test reading file with different encodings."""
        content = "Hello 世界\n"
        encodings = ["utf-8", "utf-16", "ascii"]

        for encoding in encodings:
            if encoding == "ascii":
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
        write_file(test_file, test_content, "utf-8")
        result = test_file.read_text(encoding="utf-8")
        assert result == test_content

    def test_write_file_empty(self, test_file):
        """Test writing empty content."""
        write_file(test_file, "", "utf-8")
        result = test_file.read_text(encoding="utf-8")
        assert result == ""

    def test_write_file_only_whitespace(self, test_file):
        """Test writing only whitespace."""
        content = "  \n\t\n  \n"
        write_file(test_file, content, "utf-8")
        result = test_file.read_text(encoding="utf-8")
        assert result == content

    def test_write_file_permission_error(self, tmp_path):
        """Test writing to readonly directory raises error."""
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        readonly_file = readonly_dir / "test.txt"

        # Make directory readonly
        os.chmod(readonly_dir, 0o444)

        with pytest.raises(PermissionError):
            write_file(readonly_file, "test", "utf-8")

    def test_write_file_creates_parent_directory(self, tmp_path):
        """Test write_file creates parent directories as needed."""
        deep_path = tmp_path / "a" / "b" / "c" / "test.txt"
        content = "test content"

        write_file(deep_path, content, "utf-8")

        assert deep_path.exists()
        assert deep_path.read_text(encoding="utf-8") == content
        assert deep_path.parent.is_dir()

    def test_write_file_parent_directory_not_writable(self, tmp_path):
        """Test write_file with non-writable parent directory."""
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        file_path = readonly_dir / "subdir" / "test.txt"
        
        # Make directory read-only
        os.chmod(readonly_dir, 0o555)  # r-xr-xr-x
        
        try:
            with pytest.raises(PermissionError) as exc_info:
                write_file(file_path, "test content", "utf-8")
            
            assert "Permission denied" in str(exc_info.value)
        finally:
            # Restore permissions for cleanup
            os.chmod(readonly_dir, 0o755)

    def test_validate_encoding_supported(self):
        """Test validation of supported encodings."""
        assert validate_encoding("utf-8")
        assert validate_encoding("ascii")
        assert validate_encoding("utf-16")

    def test_validate_encoding_unsupported(self):
        """Test validation of unsupported encodings."""
        assert not validate_encoding("invalid-encoding")
        assert not validate_encoding("not-real")

    def test_write_file_unsupported_encoding(self, tmp_path):
        """Test write_file with unsupported encoding."""
        file_path = tmp_path / "test.txt"
        invalid_encoding = "invalid-encoding"

        with pytest.raises(LookupError) as exc_info:
            write_file(file_path, "test", invalid_encoding)

        expected_msg = ERROR_UNSUPPORTED_ENCODING.format(encoding=invalid_encoding)
        assert str(exc_info.value) == expected_msg


class TestAtomicWrite:
    def test_atomic_write_success(self, tmp_path):
        """Test successful atomic write operation."""
        file_path = tmp_path / "target.txt"
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()
        content = "Test content\n"

        atomic_write(file_path, content, "utf-8", temp_dir)

        # Verify content
        assert file_path.read_text(encoding="utf-8") == content
        # Verify temp file was cleaned up
        assert not list(temp_dir.glob("temp_*"))

    def test_atomic_write_preserves_content(self, tmp_path, test_content):
        """Test that atomic_write preserves exact content."""
        file_path = tmp_path / "target.txt"
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()

        atomic_write(file_path, test_content, "utf-8", temp_dir)
        result = file_path.read_text(encoding="utf-8")
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
            atomic_write(file_path, "test", "utf-8", temp_dir)

        # Verify temp file was cleaned up
        temp_files = list(temp_dir.iterdir())
        assert len(temp_files) == 0, "Temporary file was not cleaned up"

    def test_atomic_write_temp_dir_not_exists(self, tmp_path):
        """Test atomic write when temp directory doesn't exist."""
        file_path = tmp_path / "target.txt"
        temp_dir = tmp_path / "nonexistent"

        if temp_dir.exists():
            temp_dir.rmdir()

        with pytest.raises(FileNotFoundError) as exc_info:
            atomic_write(file_path, "test", "utf-8", temp_dir)

        expected_msg = ERROR_PATH_NOT_FOUND.format(path=temp_dir)
        assert str(exc_info.value) == expected_msg

    def test_atomic_write_concurrent_access(self, tmp_path):
        """Test atomic write with concurrent access simulation."""
        file_path = tmp_path / "target.txt"
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()

        # Write initial content
        file_path.write_text("initial", encoding="utf-8")

        # Simulate concurrent writes
        contents = ["content1\n", "content2\n", "content3\n"]
        for content in contents:
            atomic_write(file_path, content, "utf-8", temp_dir)
            # Verify content after each write
            assert file_path.read_text(encoding="utf-8") == content

    def test_atomic_write_temp_dir_not_writable(self, tmp_path):
        """Test atomic write with non-writable temp directory."""
        file_path = tmp_path / "target.txt"
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()

        # Make temp directory read-only
        os.chmod(temp_dir, 0o444)

        with pytest.raises(PermissionError) as exc_info:
            atomic_write(file_path, "test", "utf-8", temp_dir)

        # Check for either the validation error or the OS error message
        error_msg = str(exc_info.value)
        assert any(
            [
                "No write permission for path" in error_msg,
                "Permission denied" in error_msg,
            ]
        ), f"Unexpected error message: {error_msg}"

    def test_atomic_write_target_not_writable(self, tmp_path):
        """Test atomic write with non-writable target file."""
        file_path = tmp_path / "target.txt"
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()

        # Create target file as read-only
        file_path.write_text("original")
        os.chmod(file_path, 0o444)

        with pytest.raises(FilePermissionError):
            atomic_write(file_path, "test", "utf-8", temp_dir)

    def test_atomic_write_unsupported_encoding(self, tmp_path):
        """Test atomic write with unsupported encoding."""
        file_path = tmp_path / "test.txt"
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()

        with pytest.raises(LookupError) as exc_info:
            atomic_write(file_path, "test", "invalid-encoding", temp_dir)

        assert "Unsupported encoding" in str(exc_info.value)
        assert not file_path.exists()
        # Verify no temp files were left behind
        assert len(list(temp_dir.iterdir())) == 0

    def test_atomic_write_special_characters(self, tmp_path):
        """Test atomic write with special characters in content and filenames."""
        special_filename = tmp_path / "特殊_file_名.txt"
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()

        # Test content with special characters - use os-specific line endings
        content = (
            "Unicode: 你好世界\n"
            "Emoji: 🌟🚀✨\n"
            "Special: ©®™\n"
            "Control: \t\n\b"  # Removed \r as it's handled differently across platforms
        )

        atomic_write(special_filename, content, "utf-8", temp_dir)
        result = special_filename.read_text(encoding="utf-8")
        assert result == content

    def test_atomic_write_different_encodings(self, tmp_path):
        """Test atomic write with different encodings."""
        file_path = tmp_path / "test.txt"
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()

        test_cases = [
            ("utf-8", "Hello "),
            ("utf-16", "Hello 世界"),
            ("shift-jis", "こんにちは"),
            ("iso-8859-1", "Hello World"),  # Removed € as it's not in iso-8859-1
        ]

        for encoding, content in test_cases:
            atomic_write(file_path, content, encoding, temp_dir)
            result = file_path.read_text(encoding=encoding)
            assert result == content
            assert len(list(temp_dir.iterdir())) == 0

    def test_atomic_write_cross_device(self, tmp_path, monkeypatch):
        """Test atomic write behavior when moving across devices."""
        file_path = tmp_path / "target.txt"
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()
        content = "Test content"

        # Mock shutil.move to simulate cross-device error
        def mock_move(src, dst):
            if not hasattr(mock_move, "called"):
                mock_move.called = True
                raise OSError(18, "Invalid cross-device link")
            shutil.copy2(src, dst)
            Path(src).unlink()

        monkeypatch.setattr(shutil, "move", mock_move)

        atomic_write(file_path, content, "utf-8", temp_dir)
        assert file_path.read_text(encoding="utf-8") == content
        assert len(list(temp_dir.iterdir())) == 0

    def test_atomic_write_partial_failure(self, tmp_path, monkeypatch):
        """Test atomic write with partial write failure."""
        file_path = tmp_path / "target.txt"
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()

        original_content = "original content"
        file_path.write_text(original_content)

        # Mock write_file instead of Path.write_text
        def mock_write_file(path, content, encoding):
            if "temp_" in str(path):
                raise OSError("Disk full")
            return path.write_text(content, encoding=encoding)

        monkeypatch.setattr("src.functions.writer.file_io.write_file", mock_write_file)

        with pytest.raises(OSError, match="Disk full"):
            atomic_write(file_path, "new content", "utf-8", temp_dir)

        # Verify original content is preserved
        assert file_path.read_text() == original_content
        assert len(list(temp_dir.iterdir())) == 0  # No temp files left

    def test_atomic_write_symlink_handling(self, tmp_path):
        """Test atomic write behavior with symlinks."""
        real_file = tmp_path / "real.txt"
        symlink = tmp_path / "link.txt"
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()

        # Create symlink
        real_file.write_text("original")
        symlink.symlink_to(real_file)

        content = "updated content"
        atomic_write(symlink.resolve(), content, "utf-8", temp_dir)  # Use resolved path

        assert real_file.read_text() == content
        assert symlink.read_text() == content
        assert len(list(temp_dir.iterdir())) == 0


class TestFileCleanup:
    @pytest.mark.asyncio
    async def test_cleanup_partial_file_exists(self, tmp_path):
        """Test cleanup of existing partial file."""
        test_file = tmp_path / "partial.txt"
        test_file.write_text("partial content")
        
        await cleanup_partial_file(test_file)
        assert not test_file.exists()

    @pytest.mark.asyncio
    async def test_cleanup_partial_file_nonexistent(self, tmp_path):
        """Test cleanup with nonexistent file."""
        test_file = tmp_path / "nonexistent.txt"
        
        # Should not raise any errors
        await cleanup_partial_file(test_file)

    @pytest.mark.asyncio
    async def test_cleanup_partial_file_permission_error(self, tmp_path):
        """Test cleanup with permission error."""
        test_dir = tmp_path / "readonly"
        test_dir.mkdir()
        test_file = test_dir / "partial.txt"
        test_file.write_text("content")
        
        # Make directory read-only
        os.chmod(test_dir, 0o444)
        try:
            await cleanup_partial_file(test_file)
            # Should log error but not raise
        finally:
            os.chmod(test_dir, 0o755)


class TestFileNewline:
    @pytest.mark.asyncio
    async def test_ensure_file_newline_needed(self, tmp_path):
        """Test newline check when newline is needed."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content without newline", encoding="utf-8")
        
        result = await ensure_file_newline(test_file, "utf-8")
        assert result is True

    @pytest.mark.asyncio
    async def test_ensure_file_newline_not_needed(self, tmp_path):
        """Test newline check when newline is not needed."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content with newline\n", encoding="utf-8")
        
        result = await ensure_file_newline(test_file, "utf-8")
        assert result is False

    @pytest.mark.asyncio
    async def test_ensure_file_newline_empty_file(self, tmp_path):
        """Test newline check with empty file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("", encoding="utf-8")
        
        result = await ensure_file_newline(test_file, "utf-8")
        assert result is False


class TestStreamChunks:
    @pytest.mark.asyncio
    async def test_stream_chunks_success(self, tmp_path):
        """Test successful streaming of content chunks."""
        test_file = tmp_path / "test.txt"
        content = "Test content\n" * 100
        content_bytes = content.encode("utf-8")
        
        await stream_chunks(test_file, content_bytes, chunk_size=1024)
        
        result = test_file.read_text(encoding="utf-8")
        assert result == content

    @pytest.mark.asyncio
    async def test_stream_chunks_unicode_error_strict(self, tmp_path):
        """Test streaming with invalid Unicode in strict mode."""
        test_file = tmp_path / "test.txt"
        # Create invalid UTF-8 bytes
        content_bytes = b"Valid UTF-8\xFF\xFEInvalid UTF-8"
        
        with pytest.raises(MarkdownIntegrityError):
            await stream_chunks(test_file, content_bytes, chunk_size=1024, encoding_errors="strict")

    @pytest.mark.asyncio
    async def test_stream_chunks_unicode_error_replace(self, tmp_path):
        """Test streaming with invalid Unicode in replace mode."""
        test_file = tmp_path / "test.txt"
        # Create invalid UTF-8 bytes
        content_bytes = b"Valid UTF-8\xFF\xFEInvalid UTF-8"
        
        await stream_chunks(test_file, content_bytes, chunk_size=1024, encoding_errors="replace")
        
        result = test_file.read_text(encoding="utf-8")
        assert "Valid UTF-8" in result
        assert "" in result  # Replacement character

    @pytest.mark.asyncio
    async def test_stream_chunks_permission_error(self, tmp_path):
        """Test streaming to readonly file."""
        test_file = tmp_path / "readonly.txt"
        test_file.touch()
        os.chmod(test_file, 0o444)
        
        content_bytes = b"Test content"
        
        with pytest.raises(PermissionError):
            await stream_chunks(test_file, content_bytes, chunk_size=1024)


class TestStreamDocumentContent:
    @pytest.mark.asyncio
    async def test_stream_document_content_success(self, tmp_path):
        """Test successful document content streaming."""
        test_file = tmp_path / "test.txt"
        content = "Test document content\nWith multiple lines\n"
        
        await stream_document_content(
            test_file,
            content,
            chunk_size=1024,
            encoding="utf-8",
            encoding_errors="strict"
        )
        
        result = test_file.read_text(encoding="utf-8")
        assert result == content

    @pytest.mark.asyncio
    async def test_stream_document_content_unicode(self, tmp_path):
        """Test streaming content with Unicode characters."""
        test_file = tmp_path / "test.txt"
        content = "Hello 世界! ñ € 🌟 \u2022 α β γ\n"
        
        await stream_document_content(
            test_file,
            content,
            chunk_size=1024,
            encoding="utf-8"
        )
        
        result = test_file.read_text(encoding="utf-8")
        assert result == content

    @pytest.mark.asyncio
    async def test_stream_document_content_encoding_error(self, tmp_path):
        """Test handling of encoding errors."""
        test_file = tmp_path / "test.txt"
        content = "Hello 世界\n"
        
        with pytest.raises(UnicodeError):
            await stream_document_content(
                test_file,
                content,
                chunk_size=1024,
                encoding="ascii",  # This will fail with non-ASCII content
                encoding_errors="strict"
            )

    @pytest.mark.asyncio
    async def test_stream_document_content_permission_error(self, tmp_path):
        """Test handling of permission errors."""
        test_dir = tmp_path / "readonly"
        test_dir.mkdir()
        test_file = test_dir / "test.txt"
        test_file.touch()
        os.chmod(test_dir, 0o444)  # Make directory read-only
        
        try:
            with pytest.raises(PermissionError):
                await stream_document_content(
                    test_file,
                    "Test content",
                    chunk_size=1024
                )
        finally:
            os.chmod(test_dir, 0o755)  # Restore permissions for cleanup


class TestValidateFileAccess:
    def test_validate_file_access_basic(self, tmp_path):
        """Test basic file access validation."""
        test_file = tmp_path / "test.txt"
        test_file.touch()
        
        # Should not raise any exceptions
        validate_file_access(test_file)

    def test_validate_file_access_missing(self):
        """Test handling of missing files."""
        non_existent = Path("does_not_exist.txt")
        
        with pytest.raises(FileNotFoundError):
            validate_file_access(non_existent)

    def test_validate_file_access_write(self, tmp_path):
        """Test write permission validation."""
        test_file = tmp_path / "test.txt"
        test_file.touch()
        
        # Make file read-only
        test_file.chmod(0o444)
        
        with pytest.raises(FilePermissionError):
            validate_file_access(test_file, require_write=True)

    def test_validate_file_access_parent_creation(self, tmp_path):
        """Test parent directory creation."""
        test_file = tmp_path / "subdir" / "test.txt"
        
        validate_file_access(test_file, create_parents=True, check_exists=False)
        assert test_file.parent.exists()

    def test_validate_file_access_no_exist_check(self, tmp_path):
        """Test skipping existence check."""
        non_existent = tmp_path / "not_here.txt"
        
        # Should not raise an exception when check_exists is False
        validate_file_access(non_existent, check_exists=False)
