import pytest
from datetime import datetime, timedelta
import json
from pathlib import Path
from unittest.mock import patch
from filelock import Timeout

from src.functions.writer.locking import lock_section, SectionLock
from src.functions.writer.config import WriterConfig
from src.functions.writer.exceptions import (
    WriterError,
    SectionNotFoundError,
    LockAcquisitionError,
    FileValidationError
)

@pytest.fixture
def mock_config(tmp_path):
    """Create a config that points to temporary test directory."""
    config = WriterConfig()
    config.lock_timeout = 5
    config.drafts_dir = tmp_path
    return config

@pytest.fixture
def temp_md_file(tmp_path):
    """Create a temporary markdown file with test sections."""
    file_path = tmp_path / "test.md"
    content = """# Test Document
<!-- Section: TestSection -->
Test content
<!-- Section: AnotherSection -->
More content
"""
    file_path.write_text(content)
    return file_path

class TestSectionLock:
    """Test SectionLock class behavior."""
    
    def test_basic_lock_operations(self, temp_md_file):
        """Test basic lock acquire and release."""
        lock = SectionLock(temp_md_file, "TestSection", timeout=1)
        
        assert lock.acquire() is True
        assert lock.is_locked is True
        
        lock.release()
        assert lock.is_locked is False
        assert not lock.lock_file.exists()
        
    def test_context_manager(self, temp_md_file):
        """Test context manager behavior."""
        lock = SectionLock(temp_md_file, "TestSection", timeout=1)
        
        with lock:
            assert lock.is_locked
            assert lock.lock_file.exists()
            
            # Verify metadata
            metadata = json.loads(lock.lock_file.read_text())
            assert metadata["section"] == "TestSection"
            assert metadata["file"] == str(temp_md_file)
        
        assert not lock.is_locked
        assert not lock.lock_file.exists()
        
    def test_concurrent_lock(self, temp_md_file):
        """Test concurrent lock attempts."""
        lock1 = SectionLock(temp_md_file, "TestSection")
        lock2 = SectionLock(temp_md_file, "TestSection")
        
        assert lock1.acquire() is True
        assert lock2.acquire() is False
        
        lock1.release()
        assert lock2.acquire() is True
        lock2.release()

class TestLockSection:
    """Test lock_section function behavior."""
    
    def test_successful_lock(self, temp_md_file, mock_config):
        """Test successful section locking."""
        result = lock_section("test.md", "TestSection", mock_config)
        assert result is True
        
        # Verify lock file exists
        lock_file = temp_md_file.parent / ".TestSection.lock"
        assert lock_file.exists()
        
        # Verify metadata
        metadata = json.loads(lock_file.read_text())
        assert metadata["section"] == "TestSection"
        assert metadata["file"] == str(temp_md_file)
        
    def test_concurrent_section_locks(self, temp_md_file, mock_config):
        """Test concurrent lock attempts on the same section."""
        assert lock_section("test.md", "TestSection", mock_config) is True
        assert lock_section("test.md", "TestSection", mock_config) is False
        
    def test_multiple_sections(self, temp_md_file, mock_config):
        """Test locking different sections."""
        assert lock_section("test.md", "TestSection", mock_config) is True
        assert lock_section("test.md", "AnotherSection", mock_config) is True
        
    def test_nonexistent_section(self, temp_md_file, mock_config):
        """Test locking nonexistent section."""
        with pytest.raises(SectionNotFoundError):
            lock_section("test.md", "NonexistentSection", mock_config)
            
    def test_invalid_file(self, mock_config):
        """Test locking section in nonexistent file."""
        with pytest.raises(FileValidationError):
            lock_section("nonexistent.md", "TestSection", mock_config)
            
    def test_lock_timeout(self, temp_md_file, mock_config):
        """Test lock acquisition timeout."""
        with patch('filelock.FileLock.acquire', side_effect=Timeout):
            assert lock_section("test.md", "TestSection", mock_config) is False

class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_cleanup_error(self, temp_md_file):
        """Test handling of cleanup errors."""
        lock = SectionLock(temp_md_file, "TestSection")
        with patch('pathlib.Path.unlink', side_effect=PermissionError):
            with lock:
                pass  # Should not raise exception despite cleanup error
                
    def test_metadata_write_error(self, temp_md_file):
        """Test handling of metadata write errors."""
        lock = SectionLock(temp_md_file, "TestSection")
        with patch('pathlib.Path.write_text', side_effect=PermissionError):
            with pytest.raises(LockAcquisitionError):
                with lock:
                    pass  # Should not reach here


    # pytest tests/functions/writer/test_locking.py -v -s