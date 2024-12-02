import pytest
from datetime import datetime, timedelta
import json
from pathlib import Path
from unittest.mock import Mock, patch
from filelock import Timeout

from src.functions.writer.locking import lock_section, SectionLock
from src.functions.writer.config import WriterConfig
from src.functions.writer.exceptions import (
    WriterError,
    SectionNotFoundError,
    LockAcquisitionError,
    FileValidationError
)

# Test fixtures
@pytest.fixture
def mock_config():
    config = WriterConfig()
    config.lock_timeout = 5  # Short timeout for testing
    return config

@pytest.fixture
def temp_md_file(tmp_path):
    """Create a temporary markdown file with a test section."""
    file_path = tmp_path / "test.md"
    content = """# Test Document
<!-- Section: TestSection -->
Test content
<!-- Section: AnotherSection -->
More content
"""
    file_path.write_text(content)
    return file_path

@pytest.fixture
def section_lock(temp_md_file):
    return SectionLock(temp_md_file, "TestSection", timeout=1)

# Basic Functionality Tests
class TestLockSectionBasic:
    def test_successful_lock_acquisition(self, temp_md_file, mock_config):
        """Test successful lock acquisition for an existing section."""
        result = lock_section("test.md", "TestSection", mock_config)
        assert result is True
        
        # Verify lock file exists with correct metadata
        lock_file = Path(str(temp_md_file) + ".TestSection.lock")
        assert lock_file.exists()
        
        # Verify metadata content
        metadata = json.loads(lock_file.read_text())
        assert metadata["section"] == "TestSection"
        assert "timestamp" in metadata
        assert "expires" in metadata

    def test_lock_already_held(self, temp_md_file, mock_config):
        """Test attempting to lock an already locked section."""
        # First lock should succeed
        assert lock_section("test.md", "TestSection", mock_config) is True
        
        # Second lock should fail
        assert lock_section("test.md", "TestSection", mock_config) is False

    def test_lock_release(self, section_lock):
        """Test that locks are properly released."""
        with section_lock:
            assert section_lock.lock_file.exists()
        
        # Lock file should be cleaned up after context exit
        assert not section_lock.lock_file.exists()

# Error Handling Tests
class TestLockSectionErrors:
    def test_nonexistent_section(self, temp_md_file, mock_config):
        """Test attempting to lock a non-existent section."""
        with pytest.raises(SectionNotFoundError):
            lock_section("test.md", "NonexistentSection", mock_config)

    def test_invalid_file(self, mock_config):
        """Test attempting to lock a section in a non-existent file."""
        with pytest.raises(FileValidationError):
            lock_section("nonexistent.md", "TestSection", mock_config)

    def test_lock_timeout(self, temp_md_file, mock_config):
        """Test lock acquisition timeout."""
        # Create a mock that simulates a timeout
        with patch('filelock.FileLock.acquire', side_effect=Timeout):
            assert lock_section("test.md", "TestSection", mock_config) is False

    def test_cleanup_error_handling(self, section_lock):
        """Test handling of cleanup errors."""
        with patch('pathlib.Path.unlink', side_effect=PermissionError):
            with section_lock:
                pass  # Should not raise exception despite cleanup error

# Configuration Tests
class TestLockSectionConfig:
    def test_default_config(self, temp_md_file):
        """Test lock_section with default configuration."""
        result = lock_section("test.md", "TestSection")
        assert result is True

    def test_custom_timeout(self, temp_md_file):
        """Test lock_section with custom timeout configuration."""
        config = WriterConfig()
        config.lock_timeout = 1
        
        with patch('filelock.FileLock') as mock_lock:
            lock_section("test.md", "TestSection", config)
            mock_lock.assert_called_with(
                str(Path(str(temp_md_file) + ".TestSection.lock")),
                timeout=1
            )

# Integration Tests
class TestLockSectionIntegration:
    def test_concurrent_access(self, temp_md_file, mock_config):
        """Test concurrent access to the same section."""
        # First lock
        lock1 = lock_section("test.md", "TestSection", mock_config)
        assert lock1 is True
        
        # Concurrent lock attempt
        lock2 = lock_section("test.md", "TestSection", mock_config)
        assert lock2 is False

    def test_multiple_section_locks(self, temp_md_file, mock_config):
        """Test locking multiple different sections."""
        # Lock first section
        lock1 = lock_section("test.md", "TestSection", mock_config)
        assert lock1 is True
        
        # Lock second section
        lock2 = lock_section("test.md", "AnotherSection", mock_config)
        assert lock2 is True

# Lock Metadata Tests
class TestLockMetadata:
    def test_metadata_format(self, section_lock):
        """Test the format and content of lock metadata."""
        with section_lock:
            metadata = json.loads(section_lock.lock_file.read_text())
            
            # Check required fields
            assert "section" in metadata
            assert "timestamp" in metadata
            assert "expires" in metadata
            
            # Validate timestamp format
            timestamp = datetime.fromisoformat(metadata["timestamp"])
            expires = datetime.fromisoformat(metadata["expires"])
            
            # Check expiration time
            assert expires > timestamp
            assert expires - timestamp == timedelta(seconds=section_lock.timeout)

    def test_metadata_cleanup(self, section_lock):
        """Test that metadata is properly cleaned up after lock release."""
        with section_lock:
            assert section_lock.lock_file.exists()
        
        # Verify cleanup
        assert not section_lock.lock_file.exists() 


    # pytest tests/functions/writer/test_locking.py -v -s