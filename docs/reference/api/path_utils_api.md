# path_utils API Reference

> **Source**: `src/thegent/utils/path_utils.py`

Cross-platform path handling utilities with security and consistency.

This module provides normalized path operations that work consistently
across Windows, macOS, and Linux. All functions return pathlib.Path objects
to avoid str/Path mixing and ensure type safety.

Key features:

- Automatic ~ expansion and .. resolution
- Cross-platform separator handling
- Directory traversal attack prevention (safe_join / is_within)
- Safe path existence checks (no PermissionError leakage)
- Relative path computation for logging/display

Usage:
from scripts.path_utils import (
normalize_path,
safe_join,
is_within,
safe_exists,
rel_to_cwd,
ensure_dir,
)

    path = normalize_path("~/projects/myfile.txt")
    file = safe_join(base_dir, user_input)
    if not is_within(file, allowed_dir):
        raise ValueError("Path escapes allowed directory")

---

## ensure_dir

```python
ensure_dir(path: Any)
```

Create _path_ as a directory (including parents) if it does not exist.

Equivalent to `mkdir -p`. Does nothing if the directory already exists.

**Parameters**:

- `path`: Directory path to create (`~` expansion applied).

**Returns**: Resolved absolute :class:`~pathlib.Path` of the created/existing directory.

**Raises**:

- `NotADirectoryError`: If _path_ exists but is a file.
- `PermissionError`: If the directory cannot be created.

**Examples**:

```python
>>> ensure_dir("/tmp/myapp/logs")
PosixPath('/tmp/myapp/logs')
```

---

## get_common_ancestor

Find the common ancestor directory of multiple paths.

**Parameters**:

- `*paths`: Paths to find the common ancestor for.

**Returns**: Common ancestor as a :class:`~pathlib.Path`, or the filesystem root
if no common ancestor exists above the root.

**Examples**:

```python
>>> get_common_ancestor("/home/user/a", "/home/user/b")
PosixPath('/home/user')
```

---

## is_absolute_or_relative

```python
is_absolute_or_relative(path: Any)
```

Return `True` if _path_ is absolute, `False` if relative.

Note: `~` paths are treated as relative until expanded.

**Parameters**:

- `path`: Path to inspect.

**Returns**: `True` if the path is absolute.

**Examples**:

```python
>>> is_absolute_or_relative("/home/user")
True

>>> is_absolute_or_relative("~/projects")
False

>>> is_absolute_or_relative("./src")
False
```

---

## is_same_path

```python
is_same_path(path1: Any, path2: Any)
```

Return `True` if two paths refer to the same filesystem object.

Uses :meth:`~pathlib.Path.samefile` when both paths exist (handles
symlinks correctly) and falls back to resolved-path comparison otherwise.

**Parameters**:

- `path1`: First path.
- `path2`: Second path.

**Returns**: `True` if paths refer to the same object.

---

## is_within

```python
is_within(child: Any, parent: Any)
```

Return `True` if _child_ is at or below _parent_ in the filesystem tree.

Both paths are resolved (symlinks expanded, `..` collapsed) before the
containment check so they cannot fool the comparison.

**Parameters**:

- `child`: Path to test.
- `parent`: Directory that _child_ must be contained in.

**Returns**: `True` if _child_ equals _parent_ or is a descendant of _parent_.

**Examples**:

```python
>>> is_within("/tmp/foo/bar.txt", "/tmp/foo")
True

>>> is_within("/tmp/other/file.txt", "/tmp/foo")
False

>>> is_within("/tmp/foo", "/tmp/foo")   # same path → True
True
```

---

## normalize_path

```python
normalize_path(path: Any, base: Any)
```

Normalize a path with ~ expansion and absolute resolution.

If _path_ is relative and _base_ is given, the path is resolved relative
to _base_. If _base_ is omitted, relative paths are resolved against the
current working directory.

**Parameters**:

- `path`: Input path as string or Path object. `None` returns the CWD.
- `base`: Optional base directory for resolving relative paths.

**Returns**: Normalized absolute :class:`~pathlib.Path`.

**Raises**:

- `TypeError`: If _path_ is not `str`, :class:`~pathlib.Path`, or `None`.

**Examples**:

```python
>>> normalize_path("~/projects/thegent")
PosixPath('/Users/username/projects/thegent')

>>> normalize_path("./config", "/home/user/app")
PosixPath('/home/user/app/config')

>>> normalize_path(None)
PosixPath('/current/working/directory')
```

---

## path_to_str

```python
path_to_str(path: Any)
```

Convert a path to a string, handling `None` gracefully.

**Parameters**:

- `path`: Path object, string, or `None`.

**Returns**: String representation of _path_, or `''` for `None`.

---

## rel_to_cwd

```python
rel_to_cwd(path: Any)
```

Return _path_ relative to the current working directory when possible.

If _path_ is not under the CWD the resolved absolute path is returned
unchanged. Intended for human-readable display and logging — not for
filesystem operations.

**Parameters**:

- `path`: Path to make relative (`~` expansion applied).

**Returns**: Relative :class:`~pathlib.Path` when _path_ is inside the CWD,
otherwise the absolute :class:`~pathlib.Path`.

**Examples**:

```python
>>> rel_to_cwd("/home/user/project/src/main.py")   # CWD=/home/user/project
PosixPath('src/main.py')

>>> rel_to_cwd("/etc/hosts")
PosixPath('/etc/hosts')
```

---

## safe_exists

```python
safe_exists(path: Any)
```

Check whether _path_ exists without raising on permission or OS errors.

Unlike :meth:`~pathlib.Path.exists`, this function catches
:class:`PermissionError` and :class:`OSError` and returns `False`
instead of propagating them.

**Parameters**:

- `path`: Path to check (`~` expansion is applied).

**Returns**: `True` if the path exists and is accessible; `False` otherwise.

**Examples**:

```python
>>> safe_exists("/tmp")
True

>>> safe_exists("/nonexistent/path")
False

>>> safe_exists("/root/secret")   # PermissionError → False
False
```

---

## safe_join

```python
safe_join(base: Any)
```

Join _base_ with _parts_, blocking any directory traversal escape.

Resolves the joined path and verifies it remains inside _base_. Raises
:class:`ValueError` if any `..` component or absolute override would
navigate the result outside _base_.

**Parameters**:

- `base`: The trusted base directory.
- `*parts`: Path components to join (may be user-supplied / untrusted).

**Returns**: Absolute :class:`~pathlib.Path` strictly inside (or equal to) _base_.

**Raises**:

- `ValueError`: If the joined path escapes _base_.

**Examples**:

```python
>>> safe_join("/tmp/sandbox", "subdir/file.txt")
PosixPath('/tmp/sandbox/subdir/file.txt')

>>> safe_join("/tmp/sandbox", "../../etc/passwd")
ValueError: Path escapes base '/tmp/sandbox'
```

---

## strip_common_prefix

```python
strip_common_prefix(paths: list[Any])
```

Strip the common directory prefix from a list of paths for display.

**Parameters**:

- `paths`: Paths to strip common prefix from.

**Returns**: List of paths with common prefix removed, as strings.

**Examples**:

```python
>>> strip_common_prefix(["/a/b/file1.txt", "/a/b/file2.txt"])
['file1.txt', 'file2.txt']
```

---
