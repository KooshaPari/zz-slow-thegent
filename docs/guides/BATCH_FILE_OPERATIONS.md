# Batch File Operations Guide

Batch file operations reduce tool call verbosity by 3-5x when performing multi-file operations. This guide covers usage patterns, performance benefits, and integration with hooks and scripts.

## Overview

The `batch_file_ops` module provides atomic, transactional file operations with automatic rollback on failure. It's designed for:

- Multi-file refactoring and migrations
- Spec generation and documentation updates
- Agent-driven automation workflows
- Reducing API call overhead

## Key Benefits

1. **Reduced Verbosity**: 3-5x fewer tool calls for multi-file operations
2. **Atomic Transactions**: All-or-nothing operations with automatic rollback
3. **Error Recovery**: Automatic backup and restoration on failure
4. **Performance**: Batch processing is significantly faster than sequential operations
5. **Tracking**: Detailed operation metadata and timestamps

## Python API

### Basic Usage

```python
from batch_file_ops import (
    batch_read_files,
    batch_write_files,
    batch_edit_files,
    batch_delete_files,
)

# Read multiple files
files = batch_read_files(["/path/to/file1.py", "/path/to/file2.py"])

# Write multiple files (atomic)
from batch_file_ops import batch_write_files

result = batch_write_files(
    [
        ("/path/to/file1.py", "content 1"),
        ("/path/to/file2.py", "content 2"),
    ]
)

# Edit multiple files (search/replace)
result = batch_edit_files(
    [
        ("/path/to/file1.py", "old_text", "new_text"),
        ("/path/to/file2.py", "search", "replace"),
    ]
)

# Delete multiple files (atomic)
result = batch_delete_files(["/path/to/file1.py", "/path/to/file2.py"])
```

### Batch Read Files

Read multiple files in a single operation with optional offset/limit:

```python
from batch_file_ops import batch_read_files

# Read entire files
files = batch_read_files(
    [
        "docs/file1.md",
        "docs/file2.md",
        "docs/file3.md",
    ]
)

# Read with offset and limit (efficient for large files)
files = batch_read_files(
    ["docs/large_file.md"],
    offsets={"docs/large_file.md": 100},  # Start at line 100
    limits={"docs/large_file.md": 50},  # Read 50 lines
)

# Results are in a dict
for path, content in files.items():
    print(f"{path}: {len(content)} bytes")
```

### Batch Write Files

Write multiple files atomically with automatic rollback:

```python
from batch_file_ops import batch_write_files

# Write files atomically
result = batch_write_files(
    [
        ("src/module1.py", "def func1(): pass"),
        ("src/module2.py", "def func2(): pass"),
        ("src/module3.py", "def func3(): pass"),
    ],
    atomic=True,
)

# Check results
print(f"Wrote {result.successful}/{result.total} files")
print(f"Backup directory: {result.backup_dir}")

# Access operation details
for op in result.operations:
    print(f"{op.file_path}: {op.operation_type} - {op.success}")
```

### Batch Edit Files

Edit multiple files with search/replace, atomic by default:

```python
from batch_file_ops import batch_edit_files

# Edit files
result = batch_edit_files(
    [
        ("src/file1.py", "old_import", "new_import"),
        ("src/file2.py", "deprecated_func", "new_func"),
        ("src/file3.py", "OLD_CONSTANT", "NEW_CONSTANT"),
    ]
)

# Replace only first N occurrences
result = batch_edit_files(
    [
        ("src/file.py", "pattern", "replacement"),
    ],
    count=1,
)  # Replace only first occurrence

# Replace all occurrences
result = batch_edit_files(
    [
        ("src/file.py", "pattern", "replacement"),
    ],
    count=-1,
)  # Replace all
```

### Batch Delete Files

Delete multiple files atomically with automatic rollback:

```python
from batch_file_ops import batch_delete_files

# Delete files atomically
result = batch_delete_files(
    [
        "old_file1.py",
        "old_file2.py",
        "deprecated/module.py",
    ],
    atomic=True,
)

# On failure, files are restored from backup
if result.failed > 0:
    print(f"Failed to delete {result.failed} files")
    for op in result.operations:
        if not op.success:
            print(f"  - {op.file_path}: {op.error_message}")
```

### Error Handling

```python
from batch_file_ops import batch_edit_files, BatchFileOpsError

try:
    result = batch_edit_files(
        [
            ("file1.py", "search", "replace"),
            ("file2.py", "nonexistent", "replace"),  # Will fail
        ]
    )
except BatchFileOpsError as e:
    print(f"Operation failed: {e}")
    print(f"Errors: {e.errors}")
    print(f"Result: {e.result}")

    # Access individual operation results
    for op in e.result.operations:
        if not op.success:
            print(f"  - {op.file_path}: {op.error_message}")
```

### Advanced Usage

```python
from batch_file_ops import BatchFileOps

# Use BatchFileOps class directly for more control
ops = BatchFileOps(create_backups=True, verbose=True)

# Read with custom encoding
files = ops.batch_read_files(["file1.txt", "file2.txt"], encoding="latin-1")

# Write with rollback on any failure
result = ops.batch_write_files([("file1.txt", "content1"), ("file2.txt", "content2")], atomic=True)

# Edit specific count
result = ops.batch_edit_files(
    [("file.py", "foo", "bar")],
    atomic=True,
    count=2,  # Replace first 2 occurrences
)
```

### Result Metadata

```python
result = batch_write_files([...])

# Total operations
print(result.total)  # Total files
print(result.successful)  # Successfully modified
print(result.failed)  # Failed operations

# Backup information
print(result.backup_dir)  # Location of backups
print(result.duration_ms)  # Operation duration

# Per-operation details
for op in result.operations:
    print(op.file_path)  # File path
    print(op.operation_type)  # 'read', 'write', 'edit', 'delete'
    print(op.success)  # Boolean success
    print(op.error_message)  # Error details if failed
    print(op.result)  # Operation-specific metadata
    print(op.timestamp)  # ISO timestamp

# Convert to JSON
import json

json_str = json.dumps(result.to_dict(), indent=2)
```

## Shell API

The shell wrapper provides bash-friendly interfaces:

```bash
#!/usr/bin/env bash

# Read files
batch_read_files file1 file2 file3

# Write files (path:content format)
batch_write_files "/path/file1:content1" "/path/file2:content2"

# Edit files (path:search:replace format)
batch_edit_files "/path/file:old:new" "/path/file2:search:replace"

# Delete files
batch_delete_files file1 file2 file3

# Enable verbose output
BATCH_FILE_OPS_VERBOSE=1 batch_write_files "/path/file:content"
```

## Integration Examples

### Hook Integration

In hooks, use batch operations to reduce tool calls:

```bash
#!/usr/bin/env bash
# hooks/my-hook.sh

source "$(dirname "$0")/lib/batch_file_ops.sh"

# Instead of multiple individual writes:
# batch_write_files "/path/file1:content1" "/path/file2:content2"

# Or use Python directly for complex operations:
python3 - <<'EOF'
from scripts.batch_file_ops import batch_write_files

result = batch_write_files([
    ("file1.py", "# Generated content"),
    ("file2.py", "# Generated content"),
])
print(f"Wrote {result.successful} files")
EOF
```

### Script Integration

```python
#!/usr/bin/env python3
# scripts/refactor_imports.py

from pathlib import Path
from batch_file_ops import batch_edit_files

# Find all Python files
py_files = list(Path(".").rglob("*.py"))

# Build edit operations
operations = []
for py_file in py_files:
    operations.append((str(py_file), "from old_module import func", "from new_module import func"))

# Apply atomically
result = batch_edit_files(operations, atomic=True)
print(f"Updated {result.successful}/{result.total} files")

if result.failed > 0:
    print(f"Failed files:")
    for op in result.operations:
        if not op.success:
            print(f"  - {op.file_path}: {op.error_message}")
```

### Multi-File Refactoring

```python
from batch_file_ops import batch_read_files, batch_write_files, batch_edit_files
import re
from pathlib import Path

# 1. Read all files
py_files = [str(f) for f in Path("src").rglob("*.py")]
files_content = batch_read_files(py_files)

# 2. Process all content
processed = {}
for path, content in files_content.items():
    # Apply transformations
    new_content = content.replace("old_pattern", "new_pattern")
    processed[path] = new_content

# 3. Write all files atomically
result = batch_write_files([(path, content) for path, content in processed.items()], atomic=True)

print(f"Refactored {result.successful}/{result.total} files")
```

## Performance Comparison

### Before (Sequential Operations)

```python
# Multiple individual tool calls
files = ["file1.py", "file2.py", "file3.py", "file4.py", "file5.py"]

# Read sequentially: 5 tool calls
contents = {}
for file in files:
    contents[file] = Path(file).read_text()

# Write sequentially: 5 tool calls
for file, content in contents.items():
    Path(file).write_text(content)

# Total: 10 tool calls, ~500ms
```

### After (Batch Operations)

```python
from batch_file_ops import batch_read_files, batch_write_files

files = ["file1.py", "file2.py", "file3.py", "file4.py", "file5.py"]

# Read batch: 1 tool call
contents = batch_read_files(files)

# Write batch: 1 tool call
result = batch_write_files([(f, c) for f, c in contents.items()])

# Total: 2 tool calls, ~50ms
```

**10x reduction in tool calls and 10x faster execution.**

## Backup and Recovery

All write, edit, and delete operations automatically create backups:

```python
from batch_file_ops import batch_write_files
import shutil
from pathlib import Path

result = batch_write_files(
    [
        ("file1.py", "new content"),
    ]
)

# Backup location
backup_dir = Path(result.backup_dir)
print(f"Backups stored in: {backup_dir}")

# Backups preserve directory structure
backup_file = backup_dir / "file1.py"
assert backup_file.exists()

# Manually restore if needed
original = Path("file1.py")
shutil.copy(backup_file, original)
```

Backups are stored in `~/.thegent/backups/{TIMESTAMP}/` with directory structure preserved.

## Error Handling and Atomicity

The module provides strong atomicity guarantees:

```python
from batch_file_ops import batch_write_files, BatchFileOpsError

try:
    result = batch_write_files(
        [
            ("file1.py", "content1"),
            ("file2.py", "content2"),
            # Imagine file3 write fails (permission denied)
            ("file3.py", "content3"),
        ],
        atomic=True,
    )
except BatchFileOpsError as e:
    # ALL files are rolled back to original state
    # Backups are created before any modification
    print(f"Operation failed. Rolled back {len(e.result.operations)} files")
    print(f"Backup directory: {e.result.backup_dir}")
```

## CLI Usage

Use batch operations from the command line:

```bash
# Read files
python3 scripts/batch_file_ops.py --read file1 file2 file3

# Write files
python3 scripts/batch_file_ops.py --write file1 "content1" file2 "content2"

# Edit files
python3 scripts/batch_file_ops.py --edit file "old" "new" file2 "search" "replace"

# Delete files
python3 scripts/batch_file_ops.py --delete file1 file2 file3

# JSON output
python3 scripts/batch_file_ops.py --read file1 --json

# Verbose output
python3 scripts/batch_file_ops.py --write file "content" --verbose
```

## Best Practices

1. **Use batch operations for 3+ files** - For 1-2 files, individual operations are simpler
2. **Enable atomic mode** - Default is `atomic=True`, keep it unless you have a specific reason
3. **Check result metadata** - Always examine `result.operations` for detailed status
4. **Enable verbose mode during development** - `verbose=True` provides helpful debug information
5. **Handle BatchFileOpsError** - Don't let errors propagate silently
6. **Clean up backups** - Backups are kept in `~/.thegent/backups/` and should be cleaned periodically

## Troubleshooting

### Operation failed with permission error

```python
# Ensure parent directories are writable
from pathlib import Path

parent = Path(file_path).parent
parent.mkdir(parents=True, exist_ok=True)
```

### Backup directory not created

```python
# Backups only created for write/edit/delete operations, not read
# For read operations, no backup is needed
result = batch_write_files([...])  # Creates backup
assert result.backup_dir is not None
```

### Large batch operations

```python
# For very large batches (1000+ files), consider chunking:
files = list(range(10000))
chunk_size = 500

for i in range(0, len(files), chunk_size):
    chunk = files[i : i + chunk_size]
    result = batch_write_files([...])
    print(f"Processed chunk {i // chunk_size + 1}")
```

## See Also

- `scripts/batch_file_ops.py` - Main implementation
- `tests/test_batch_file_ops.py` - Comprehensive test suite
- `hooks/lib/batch_file_ops.sh` - Shell wrapper
