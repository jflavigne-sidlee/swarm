import pytest
from datetime import datetime, timedelta
import json
from pathlib import Path
from unittest.mock import patch
from filelock import Timeout

from src.functions.writer.locking import lock_section, SectionLock, LockCleanupManager
from src.functions.writer.config import WriterConfig
from src.functions.writer.exceptions import (
    WriterError,
    SectionNotFoundError,
    LockAcquisitionError,
    FileValidationError
)
from src.functions.writer.constants import LOCK_METADATA_TIMESTAMP, LOCK_METADATA_AGENT
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
        
    def test_expired_lock(self, temp_md_file):
        """Test handling of expired locks."""
        lock = SectionLock(temp_md_file, "TestSection", timeout=1)
        
        # Create an expired lock
        with lock:
            # Modify the timestamp to make it appear expired
            metadata = json.loads(lock.lock_file.read_text())
            metadata[LOCK_METADATA_TIMESTAMP] = (
                datetime.now() - timedelta(seconds=2)
            ).isoformat()
            lock.lock_file.write_text(json.dumps(metadata))
            
        # Try to acquire the expired lock
        lock2 = SectionLock(temp_md_file, "TestSection", timeout=1)
        assert lock2.acquire() is True  # Should succeed because previous lock expired
        lock2.release()

    def test_lock_with_agent_id(self, temp_md_file):
        """Test locking with agent identification."""
        agent_id = "test_agent_123"
        lock = SectionLock(temp_md_file, "TestSection", timeout=1, agent_id=agent_id)
        
        with lock:
            assert lock.is_locked
            # Verify metadata includes agent_id
            metadata = json.loads(lock.lock_file.read_text())
            assert metadata[LOCK_METADATA_AGENT] == agent_id

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

    def test_lock_section_with_agent(self, temp_md_file, mock_config):
        """Test lock_section function with agent identification."""
        agent_id = "test_agent_456"
        assert lock_section("test.md", "TestSection", mock_config, agent_id=agent_id) is True
        
        # Verify lock file exists and contains agent_id
        lock_file = temp_md_file.parent / ".TestSection.lock"
        assert lock_file.exists()
        metadata = json.loads(lock_file.read_text())
        assert metadata[LOCK_METADATA_AGENT] == agent_id

    def test_automatic_cleanup(self, temp_md_file, mock_config):
        """Test automatic cleanup during lock acquisition."""
        lock_dir = temp_md_file.parent
        
        # Create a stale lock
        stale_lock = lock_dir / ".stale_section.lock"
        stale_metadata = {
            "section": "stale_section",
            "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
            "file": str(temp_md_file)
        }
        stale_lock.write_text(json.dumps(stale_metadata))
        
        # Force cleanup by patching random
        with patch('random.random', return_value=0.0):  # Always trigger cleanup
            lock_section("test.md", "TestSection", mock_config)
            
        # Verify stale lock was cleaned up
        assert not stale_lock.exists()
        
    def test_cleanup_failure_handling(self, temp_md_file, mock_config):
        """Test handling of cleanup failures during lock acquisition."""
        with patch('src.functions.writer.locking.LockCleanupManager.cleanup_stale_locks', 
                  side_effect=Exception("Cleanup failed")):
            with patch('random.random', return_value=0.0):  # Force cleanup attempt
                # Should still succeed despite cleanup failure
                assert lock_section("test.md", "TestSection", mock_config) is True

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

class TestLockCleanup:
    """Test lock cleanup functionality."""
    
    def test_cleanup_stale_locks(self, temp_md_file, mock_config):
        """Test cleanup of stale lock files."""
        # Create some stale locks
        stale_time = datetime.now() - timedelta(hours=2)
        fresh_time = datetime.now()
        
        lock_dir = temp_md_file.parent
        
        # Create stale lock
        stale_lock = lock_dir / ".stale_section.lock"
        stale_metadata = {
            "section": "stale_section",
            "timestamp": stale_time.isoformat(),
            "file": str(temp_md_file)
        }
        stale_lock.write_text(json.dumps(stale_metadata))
        
        # Create fresh lock
        fresh_lock = lock_dir / ".fresh_section.lock"
        fresh_metadata = {
            "section": "fresh_section",
            "timestamp": fresh_time.isoformat(),
            "file": str(temp_md_file)
        }
        fresh_lock.write_text(json.dumps(fresh_metadata))
        
        # Run cleanup
        cleanup_manager = LockCleanupManager(mock_config)
        cleaned_count = cleanup_manager.cleanup_stale_locks()
        
        # Verify results
        assert cleaned_count == 1
        assert not stale_lock.exists()
        assert fresh_lock.exists()
        
    def test_cleanup_invalid_locks(self, temp_md_file, mock_config):
        """Test cleanup of invalid lock files."""
        lock_dir = temp_md_file.parent
        invalid_lock = lock_dir / ".invalid_section.lock"
        invalid_lock.write_text("invalid json")
        
        cleanup_manager = LockCleanupManager(mock_config)
        cleaned_count = cleanup_manager.cleanup_stale_locks()
        
        assert cleaned_count == 1
        assert not invalid_lock.exists()

    # pytest tests/functions/writer/test_locking.py -v -s