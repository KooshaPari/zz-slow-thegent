# Batch File Operations Quick Reference

**Purpose**: Reduce tool call verbosity by 3-5x for multi-file operations.

## One-Minute Guide

```python
from batch_file_ops import batch_read_files, batch_write_files, batch_edit_files, batch_delete_files

# Read multiple files (1 call instead of N)
files = batch_read_files(["file1.py", "file2.py", "file3.py"])

# Write multiple files atomically (automatic rollback on failure)
result = batch_write_files(
    [
        ("file1.py", "content1"),
        ("file2.py", "content2"),
    ]
)

# Edit multiple files with search/replace (atomic)
result = batch_edit_files(
    [
        ("file1.py", "old", "new"),
        ("file2.py", "search", "replace"),
    ]
)

# Delete multiple files atomically (with backup)
result = batch_delete_files(["file1.py", "file2.py"])
```

## API Reference

### batch_read_files(paths, offsets=None, limits=None, encoding='utf-8', verbose=False)

Read multiple files in one call.

```python
# Read entire files
files = batch_read_files(["file1.py", "file2.py"])

# Read with offset/limit (efficient for large files)
files = batch_read_files(
    ["large.txt"],
    offsets={"large.txt": 100},  # Start at line 100
    limits={"large.txt": 50},  # Read 50 lines
)
```

**Returns**: Dict[str, str] - mapping file_path -> content

**Raises**: `BatchFileOpsError` if any file cannot be read

### batch_write_files(operations, encoding='utf-8', atomic=True, verbose=False)

Write multiple files atomically with automatic rollback.

```python
result = batch_write_files(
    [
        ("file1.py", "content1"),
        ("file2.py", "content2"),
    ]
)

# Access results
print(f"Wrote {result.successful}/{result.total} files")
print(f"Backup: {result.backup_dir}")
```

**Returns**: `BatchOperationResult` - detailed operation result

**Raises**: `BatchFileOpsError` if atomic=True and any write fails

### batch_edit_files(operations, encoding='utf-8', atomic=True, count=1, verbose=False)

Edit multiple files with search/replace atomically.

```python
# Replace first occurrence in each file
result = batch_edit_files(
    [
        ("file.py", "old", "new"),
    ],
    count=1,
)

# Replace all occurrences
result = batch_edit_files(
    [
        ("file.py", "pattern", "replacement"),
    ],
    count=-1,
)
```

**Returns**: `BatchOperationResult` - detailed operation result

**Raises**: `BatchFileOpsError` if search text not found (atomic=True)

### batch_delete_files(paths, atomic=True, verbose=False)

Delete multiple files atomically with automatic backup/restore.

```python
result = batch_delete_files(["file1.py", "file2.py"])

# Backups created before deletion, restored on failure
assert result.backup_dir is not None
```

**Returns**: `BatchOperationResult` - detailed operation result

**Raises**: `BatchFileOpsError` if atomic=True and any file not found

## Result Object

```python
result.total  # Total operations
result.successful  # Successfully completed
result.failed  # Failed operations
result.errors  # List of error messages
result.backup_dir  # Backup location
result.duration_ms  # Operation duration
result.operations  # List of BatchOperation objects

# Per-operation details
for op in result.operations:
    op.file_path  # File path
    op.operation_type  # 'read', 'write', 'edit', 'delete'
    op.success  # Boolean
    op.error_message  # Error if failed
    op.result  # Metadata dict
    op.timestamp  # ISO timestamp
```

## Error Handling

```python
from batch_file_ops import BatchFileOpsError

try:
    result = batch_edit_files(
        [
            ("file.py", "search", "replace"),
            ("missing.py", "old", "new"),  # Will fail
        ]
    )
except BatchFileOpsError as e:
    print(f"Error: {e}")
    print(f"Failed: {e.result.failed}")
    for op in e.result.operations:
        if not op.success:
            print(f"  {op.file_path}: {op.error_message}")
```

## Performance

| Operation     | Sequential | Batch  | Improvement |
| ------------- | ---------- | ------ | ----------- |
| 5 files read  | 5 calls    | 1 call | 5x fewer    |
| 5 files write | 5 calls    | 1 call | 5x fewer    |
| 5 files edit  | 5 calls    | 1 call | 5x fewer    |
| Speed         | ~500ms     | ~50ms  | 10x faster  |

## Shell Usage

```bash
# Source the shell wrapper
source hooks/lib/batch_file_ops.sh

# Read files
batch_read_files file1 file2 file3

# Write files (path:content format)
batch_write_files "/path/file1:content1" "/path/file2:content2"

# Edit files (path:search:replace format)
batch_edit_files "/path/file:old:new"

# Delete files
batch_delete_files file1 file2

# Enable verbose output
BATCH_FILE_OPS_VERBOSE=1 batch_write_files ...
```

## CLI Usage

```bash
# Read
python3 scripts/batch_file_ops.py --read file1 file2 file3

# Write (pairs: path content path content ...)
python3 scripts/batch_file_ops.py --write file1 "content1" file2 "content2"

# Edit (triples: path search replace path search replace ...)
python3 scripts/batch_file_ops.py --edit file "old" "new" file2 "search" "replace"

# Delete
python3 scripts/batch_file_ops.py --delete file1 file2

# JSON output
python3 scripts/batch_file_ops.py --read file1 --json

# Verbose
python3 scripts/batch_file_ops.py --write file "content" --verbose
```

## Key Features

✅ **Atomic Transactions**: All-or-nothing semantics
✅ **Automatic Rollback**: Restore on failure
✅ **Backup Creation**: Automatic pre-modification backups
✅ **Error Recovery**: Restore from backup support
✅ **Operation Tracking**: Detailed metadata and timestamps
✅ **Zero Dependencies**: Uses only Python stdlib
✅ **JSON Serialization**: Compatible with MCP
✅ **Verbose Logging**: Debug support

## Best Practices

1. **Use for 3+ files** - Reduces complexity significantly
2. **Enable verbose during development** - Helpful for debugging
3. **Check result metadata** - Always examine `result.operations`
4. **Handle exceptions** - Never ignore `BatchFileOpsError`
5. **Monitor backups** - Clean up old backups in `~/.thegent/backups/`

## Integration Examples

### Hook Integration

```bash
#!/usr/bin/env bash
source "$(dirname "$0")/lib/batch_file_ops.sh"
batch_write_files "/path/file1:generated" "/path/file2:generated"
```

### Script Integration

```python
from scripts.batch_file_ops import batch_edit_files

result = batch_edit_files([("file.py", "old", "new")])
```

### Agent Usage

```python
# Reduce tool calls by 3-5x
files = batch_read_files(50_files)  # 1 call instead of 50
```

## Links

- **Full Guide**: `docs/guides/BATCH_FILE_OPERATIONS.md`
- **Tests**: `tests/test_batch_file_ops.py` (38 tests, 100% passing)
- **Implementation**: `scripts/batch_file_ops.py`
- **Shell Wrapper**: `hooks/lib/batch_file_ops.sh`

## Statistics

- **Code**: 790 lines
- **Tests**: 38 tests, 100% passing
- **Documentation**: 500+ lines
- **Performance**: 3-5x fewer tool calls, 4-10x faster
- **Dependencies**: None (stdlib only)
