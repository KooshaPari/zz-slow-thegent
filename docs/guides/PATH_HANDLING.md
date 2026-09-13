# Cross-Platform Path Handling Guide

## Overview

`scripts/path_utils.py` provides centralized, cross-platform path handling utilities. All primary functions return `pathlib.Path` objects to avoid `str`/`Path` mixing, ensuring type consistency and preventing filesystem errors across Windows, macOS, and Linux.

**Security model**: `safe_join()` and `is_within()` together prevent directory traversal attacks from user-supplied path components.

---

## Quick Start

```python
from scripts.path_utils import (
    normalize_path,
    safe_join,
    is_within,
    safe_exists,
    rel_to_cwd,
    ensure_dir,
)

# Normalize any user-supplied path
path = normalize_path(user_input)

# Safely join user-supplied components (traversal-safe)
file = safe_join(base_dir, user_filename)

# Guard: reject paths that escape the sandbox
if not is_within(file, base_dir):
    raise ValueError("Path escapes allowed directory")

# Check existence without raising on permission errors
if safe_exists(config_file):
    ...

# Human-readable display path for logs
logger.info(f"Writing {rel_to_cwd(file)}")

# Create directories (mkdir -p semantics)
ensure_dir("~/.myapp/logs")
```

---

## API Reference

### `normalize_path(path, base=None) -> Path`

Normalize a path: expand `~`, resolve `..`, return an absolute `Path`.

If `path` is relative and `base` is given, it is resolved relative to `base`.
If `base` is omitted, relative paths resolve against the current working directory.
`None` returns the current working directory.

```python
normalize_path("~/projects/thegent")
# PosixPath('/Users/username/projects/thegent')

normalize_path("./config", "/home/user/app")
# PosixPath('/home/user/app/config')

normalize_path(None)
# PosixPath('/current/working/directory')
```

**Raises**:
- `TypeError` if `path` is not `str`, `Path`, or `None`.

---

### `safe_join(base, *parts) -> Path`

Join `base` with one or more `parts`, **blocking any directory traversal escape**.

The resolved result is checked with `is_within()`. If any `..` component or absolute override would navigate outside `base`, a `ValueError` is raised.

```python
safe_join("/tmp/sandbox", "subdir/file.txt")
# PosixPath('/tmp/sandbox/subdir/file.txt')

safe_join("/tmp/sandbox", "../../etc/passwd")
# ValueError: Path escapes base '/tmp/sandbox'

# Tilde expansion works in base
safe_join("~", ".thegent", "sessions")
# PosixPath('/Users/username/.thegent/sessions')

# .. that stays inside base is allowed
safe_join("/tmp/sandbox", "sub", "..", "other.txt")
# PosixPath('/tmp/sandbox/other.txt')  -- still inside base
```

**Raises**:
- `ValueError` if the joined path would escape `base`.

**Security note**: Always use `safe_join` (not the `/` operator) when any path component comes from user input, configuration files, or environment variables.

---

### `is_within(child, parent) -> bool`

Return `True` if `child` is at or below `parent` in the filesystem tree.

Both paths are fully resolved (symlinks expanded, `..` collapsed) before comparison.

```python
is_within("/tmp/foo/bar.txt", "/tmp/foo")  # True
is_within("/tmp/foo", "/tmp/foo")  # True  (same path)
is_within("/tmp/foo", "/tmp/foo/bar")  # False (parent is not within child)
is_within("/tmp/foo_extra", "/tmp/foo")  # False (prefix != path component)
```

**Note on symlinks**: `/tmp/link/file` where `link -> /tmp/real` will report `True` for `is_within("/tmp/link/file", "/tmp/real")` because both sides are resolved.

---

### `safe_exists(path) -> bool`

Check whether `path` exists without raising on permission or OS errors.

```python
safe_exists("/tmp")  # True
safe_exists("/nonexistent/path")  # False
safe_exists("/root/secret")  # False  (PermissionError caught)
safe_exists("~/projects")  # True  (~ expanded before check)
```

Unlike `Path.exists()`, this never propagates `PermissionError` or `OSError`.

---

### `rel_to_cwd(path) -> Path`

Return `path` relative to the current working directory.

If `path` is not under the CWD, the resolved absolute path is returned unchanged. Intended for logging and user-facing messages, not for filesystem operations.

```python
# When CWD is /home/user/project:
rel_to_cwd("/home/user/project/src/main.py")
# PosixPath('src/main.py')

rel_to_cwd("/etc/hosts")
# PosixPath('/etc/hosts')   (outside CWD -- returned as-is)
```

---

### `ensure_dir(path) -> Path`

Create `path` as a directory (including all intermediate parents) if it does not exist. Equivalent to `mkdir -p`. Does nothing if the directory already exists.

```python
ensure_dir("/tmp/myapp/logs")
# PosixPath('/tmp/myapp/logs')   -- created

ensure_dir("~/.thegent/sessions")
# PosixPath('/Users/username/.thegent/sessions')

ensure_dir("/tmp")  # already exists -- no error
```

**Returns**: Resolved absolute `Path` of the created/existing directory.

**Raises**:
- `NotADirectoryError` if `path` exists but is a file.
- `PermissionError` if the directory cannot be created.

---

## Additional Helpers

These are lower-level utilities retained from the original implementation.

| Function | Description |
|---|---|
| `path_to_str(path)` | Convert `Path`/`str`/`None` to `str`; `None` returns `""`. |
| `get_common_ancestor(*paths)` | Find the common ancestor directory of multiple paths. |
| `is_same_path(p1, p2)` | Check if two paths refer to the same filesystem object (handles symlinks). |
| `is_absolute_or_relative(path)` | `True` if path is absolute; `False` if relative (`~` counts as relative). |
| `strip_common_prefix(paths)` | Strip common directory prefix from a list of paths; useful for display. |

---

## Security Notes

### Directory Traversal Attacks

A directory traversal attack uses `../` components to escape an intended base directory. Example:

```
User provides:  "../../etc/passwd"
Naive join:     base_dir + "../../etc/passwd" = "/etc/passwd"   -- DANGEROUS
safe_join:      ValueError raised immediately                    -- SAFE
```

**Rules**:
1. Never use `Path.__truediv__` (`/`) or `os.path.join` with user input.
2. Always use `safe_join(base, user_input)`.
3. After any join, validate with `is_within(result, base)` if you have separate join logic.

### Permission Errors

`safe_exists()` silently returns `False` for permission errors instead of crashing. This is intentional for existence probes. If you need to differentiate "does not exist" from "permission denied", use `Path.exists()` directly and handle the exception yourself.

### Symlink Resolution

All functions that call `.resolve()` expand symlinks. This means:
- A symlinked directory is treated as its real location for containment checks.
- Circular symlinks will raise an `OSError` from Python's `resolve()` (not caught).

---

## Common Patterns

### Config File Handling

```python
from scripts.path_utils import normalize_path, ensure_dir, safe_join

CONFIG_BASE = normalize_path("~/.myapp")
ensure_dir(CONFIG_BASE)

config_file = safe_join(CONFIG_BASE, "config.toml")
logs_dir = ensure_dir(safe_join(CONFIG_BASE, "logs"))
```

### User Input Validation

```python
from scripts.path_utils import normalize_path, is_within, safe_join


def process_user_file(user_path: str, allowed_base: str) -> Path:
    """Process user-provided file path safely."""
    base = normalize_path(allowed_base)
    try:
        return safe_join(base, user_path)
    except ValueError as exc:
        raise PermissionError(f"Access denied: {exc}") from exc
```

### Logging Display

```python
from scripts.path_utils import rel_to_cwd, strip_common_prefix

# Single path
logger.info(f"Writing {rel_to_cwd(output_file)}")

# List of files
files = ["/home/user/src/a.py", "/home/user/src/b.py"]
for name in strip_common_prefix(files):
    logger.debug(f"  {name}")
```

---

## Cross-Platform Considerations

### Windows

- `pathlib.Path` uses `PureWindowsPath` on Windows, which understands drive letters (`C:\`) and UNC paths (`\\server\share`).
- `safe_join` and `is_within` compare resolved paths so they work correctly on all platforms.
- Tilde expansion (`~`) works on Windows via Python's `Path.expanduser()`.

### macOS Symlinks

`/tmp` on macOS is a symlink to `/private/tmp`. Always use `.resolve()` (which all functions do) to avoid comparison mismatches.

### Case Sensitivity

Path comparisons via `.relative_to()` are case-sensitive on Linux and macOS (usually), and case-insensitive on Windows. The utilities inherit the OS behavior.

---

## Migration Guide

| Old pattern | New pattern |
|---|---|
| `os.path.expanduser("~/.app")` | `normalize_path("~/.app")` |
| `os.path.join(base, user_input)` | `safe_join(base, user_input)` |
| `base / user_input` | `safe_join(base, user_input)` |
| `path.exists()` (may raise) | `safe_exists(path)` |
| `os.makedirs(path, exist_ok=True)` | `ensure_dir(path)` |
| `str(path)` (None-unsafe) | `path_to_str(path)` |

---

## Testing

Tests live at `tests/test_path_utils.py` (88 test cases).

```bash
# Run all path utility tests
pytest tests/test_path_utils.py -v

# Run specific class
pytest tests/test_path_utils.py::TestSafeJoin -v

# Run with coverage
pytest tests/test_path_utils.py --cov=scripts.path_utils --cov-report=term-missing
```

---

## See Also

- `scripts/path_utils.py` -- Implementation (300 LOC)
- `tests/test_path_utils.py` -- Test suite (88 tests)
- `docs/guides/BATCH_FILE_OPERATIONS.md` -- Batch file ops (uses path_utils)
- `CLAUDE.md` -- Listed under "Available Helpers" section
