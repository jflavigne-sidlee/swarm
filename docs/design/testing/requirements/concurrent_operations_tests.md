# Concurrent Operations Tests Requirements

## Overview
This document outlines the requirements and specifications for implementing concurrent operations testing in the Markdown Document Management System.

## Locking Mechanism

### Scope and Granularity
Reference implementation:
```typescript:docs/design/testing/integration_testing_plan.md
startLine: 77
endLine: 135
```

- Primary lock granularity: Section-level
- Secondary lock granularity: Document-level (for metadata operations)
- Multiple sections can be locked concurrently by different processes
- Document-level locks prevent all section operations

### Lock Ownership
```python
LockMetadata = {
    "owner_id": str,        # Process or thread ID
    "timestamp": datetime,  # Lock acquisition time
    "operation": str,      # Type of operation being performed
    "ttl": int            # Time-to-live in seconds
}
```

- Lock ownership tracked by process/thread ID
- Automatic lock release on process termination
- Lock metadata stored in filesystem alongside document
- Heartbeat mechanism to detect stale locks

## Concurrency Model

### Operation Types
1. **Exclusive Operations (Write)**
   - Section content modifications
   - Section deletion
   - Section reordering
   
2. **Shared Operations (Read)**
   - Content retrieval
   - Validation
   - Export operations

### Conflict Resolution
```python
async def handle_concurrent_edit(doc_path: Path, section: str, content: str) -> Result:
    max_retries = 3
    retry_delay = 100  # milliseconds
    
    for attempt in range(max_retries):
        try:
            async with document_lock(doc_path, section):
                return await edit_section(doc_path, section, content)
        except LockError as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(retry_delay / 1000)
```

- First-come-first-served lock acquisition
- No automatic conflict merging
- Configurable retry mechanism
- Deadlock prevention through timeout

## Error Handling

### Error Types
```python
class LockError(Exception):
    """Base class for lock-related errors."""
    pass

class LockAcquisitionError(LockError):
    """Failed to acquire lock."""
    pass

class LockTimeoutError(LockError):
    """Lock held for too long."""
    pass

class StaleProcessLockError(LockError):
    """Lock held by terminated process."""
    pass
```

### Recovery Mechanisms
Reference implementation:
```typescript:docs/design/testing/integration_testing_plan.md
startLine: 206
endLine: 260
```

- Automatic lock cleanup after timeout (default: 5 minutes)
- Process death detection via heartbeat
- Rollback of partial changes on failure
- Audit trail of lock operations

## State Management

### Consistency Requirements
- All section operations must be atomic
- Changes visible only after successful commit
- Lock state must be consistent across processes
- No partial updates visible to readers

### Version Control
```python
@dataclass
class SectionVersion:
    content: str
    timestamp: datetime
    author: str
    version: int
    checksum: str
```

- Linear version history per section
- Atomic version increments
- Checksum validation for content integrity
- Version metadata preserved during concurrent edits

## Performance Requirements

### Benchmarks
- Lock acquisition: < 100ms under normal load
- Maximum concurrent editors: 50 per document
- Lock cleanup interval: 60 seconds
- Maximum lock hold time: 5 minutes

### Resource Limits
- Maximum active locks per document: 100
- Maximum lock metadata size: 1KB per lock
- Lock file storage: Temporary filesystem

## Test Scenarios

### Basic Concurrency Tests
Reference implementation:
```typescript:docs/design/testing/integration_testing_plan.md
startLine: 311
endLine: 326
```

### Advanced Scenarios
1. **High Contention**
   - Multiple processes editing same section
   - Rapid lock/unlock cycles
   - Mixed read/write operations

2. **Error Conditions**
   - Process termination during lock
   - Network partition simulation
   - Filesystem errors

3. **Performance Tests**
   - Sustained concurrent operations
   - Resource usage monitoring
   - Lock contention measurement

## Monitoring Requirements

### Metrics
```json
{
  "locks": {
    "active": number,
    "waiting": number,
    "timeouts": number,
    "contentions": number
  },
  "operations": {
    "throughput": number,
    "latency": number,
    "failures": number
  }
}
```

### Logging
- All lock operations logged with metadata
- Lock contention events
- Cleanup operations
- Error conditions and recovery actions

## Implementation Guidelines

### Test Structure
```python
@pytest.mark.asyncio
async def test_concurrent_scenario():
    """
    Given: Multiple processes/threads
    When: Concurrent operations are performed
    Then: System maintains consistency and performance
    """
    # Setup
    # Execute concurrent operations
    # Verify results and state
```

### Assertions
- Lock state consistency
- Content integrity
- Performance within bounds
- Resource cleanup
- Error handling correctness 

## Advanced Implementation Details

### Heartbeat Implementation
Based on patterns from:
```typescript:docs/design/writing/lock_section.md
startLine: 52
endLine: 59
```

- Heartbeat Frequency:
  - Default check interval: 30 seconds
  - Configurable via `LOCK_HEARTBEAT_INTERVAL` environment variable
  - Minimum interval: 5 seconds
  - Maximum interval: 120 seconds
- Heartbeat File Structure:
  ```python
  @dataclass
  class HeartbeatMetadata:
      last_heartbeat: datetime
      process_id: int
      host_id: str
      operation_start: datetime
      expected_duration: int  # seconds
  ```

### Lock File Management
Reference implementation patterns:
```typescript:docs/design/writing/lock_section.md
startLine: 63
endLine: 74
```

- Storage Location:
  - Lock files stored in `.locks` directory alongside document
  - Filename pattern: `{section_id}.lock`
  - Metadata in JSON format for easy inspection
- Persistence:
  - Lock files are temporary by default
  - Cleared on system restart
  - Optional persistent mode for cross-restart operations
  - Automatic cleanup of stale locks during startup

### Edge Case Test Scenarios
```python
@pytest.mark.asyncio
async def test_rapid_succession_edits():
    """Test rapid succession of edits on the same section."""
    edit_interval = 0.1  # seconds
    num_edits = 10
    
    async def rapid_edit(section: str, content: str) -> List[Result]:
        results = []
        for i in range(num_edits):
            try:
                async with document_lock(doc_path, section):
                    result = await edit_section(doc_path, section, f"{content}_{i}")
                    results.append(result)
            except LockError:
                results.append(None)
            await asyncio.sleep(edit_interval)
        return results
    
    results = await rapid_edit("test_section", "content")
    assert len([r for r in results if r is not None]) > 0
```

### Manual Recovery Tools
```python
class LockManager:
    @staticmethod
    def force_release(doc_path: Path, section: str) -> bool:
        """Administrative tool to force release a lock."""
        lock_path = get_lock_path(doc_path, section)
        if not lock_path.exists():
            return False
            
        try:
            # Verify lock is actually stale
            metadata = read_lock_metadata(lock_path)
            if not is_lock_stale(metadata):
                raise LockError("Cannot force release active lock")
                
            # Release lock and log action
            lock_path.unlink()
            log_forced_release(doc_path, section, metadata)
            return True
        except Exception as e:
            log_release_failure(doc_path, section, str(e))
            return False
```

### Recovery Process Flow
1. **Automatic Recovery**
   - System startup check
   - Periodic heartbeat verification
   - Timeout-based cleanup

2. **Manual Intervention**
   - Administrative lock release
   - Lock metadata inspection
   - Process termination option
   - Audit trail requirements

3. **Recovery Validation**
   - Lock state verification
   - Document consistency check
   - Operation replay if needed
   - Recovery action logging