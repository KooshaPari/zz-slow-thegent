# fast_file_ops API Reference

> **Source**: `src/thegent/infra/fast_file_ops.py`

Fast file operations with platform-specific optimizations.

This module provides optimized file operations that use platform-specific
optimizations for better performance:

- Linux: os.sendfile() for large file copies (zero-copy)
- All platforms: Optimized shutil operations
- Batch operations where possible

Performance improvements:

- sendfile() on Linux: Zero-copy for large files (10-100MB+)
- Optimized directory operations
- Batch file operations

---

## FastFileOps

High-performance file operations with platform-specific optimizations.

### Methods

#### FastFileOps.copy

```python
copy(src: Any, dst: Any, preserve_metadata: bool)
```

Copy file with optimized method selection.

**Parameters**:

- `src`: Source file path
- `dst`: Destination file path
- `preserve_metadata`: Whether to preserve file metadata

---

#### FastFileOps.copy_tree

```python
copy_tree(src: Any, dst: Any, ignore: Any)
```

Copy directory tree with optimizations.

**Parameters**:

- `src`: Source directory path
- `dst`: Destination directory path
- `ignore`: Optional list of patterns to ignore

---

#### FastFileOps.ensure_dir

```python
ensure_dir(path: Any, mode: int)
```

Ensure directory exists (create if needed).

**Parameters**:

- `path`: Directory path
- `mode`: Directory permissions

**Returns**: Path object

---

#### FastFileOps.get_size

```python
get_size(path: Any)
```

Get file or directory size (optimized).

**Parameters**:

- `path`: Path to file or directory

**Returns**: Size in bytes

---

#### FastFileOps.move

```python
move(src: Any, dst: Any)
```

Move file or directory (optimized).

**Parameters**:

- `src`: Source path
- `dst`: Destination path

---

#### FastFileOps.remove

```python
remove(path: Any, recursive: bool)
```

Remove file or directory (optimized).

**Parameters**:

- `path`: Path to remove
- `recursive`: If True, remove directory recursively

---

---

## copy

```python
copy(src: Any, dst: Any, preserve_metadata: bool)
```

Copy file with optimized method selection.

**Parameters**:

- `src`: Source file path
- `dst`: Destination file path
- `preserve_metadata`: Whether to preserve file metadata

---

## copy_file

```python
copy_file(src: Any, dst: Any, preserve_metadata: bool)
```

Copy file with optimized method.

---

## copy_tree

```python
copy_tree(src: Any, dst: Any, ignore: Any)
```

Copy directory tree with optimizations.

**Parameters**:

- `src`: Source directory path
- `dst`: Destination directory path
- `ignore`: Optional list of patterns to ignore

---

## ensure_dir

```python
ensure_dir(path: Any, mode: int)
```

Ensure directory exists (create if needed).

**Parameters**:

- `path`: Directory path
- `mode`: Directory permissions

**Returns**: Path object

---

## ensure_directory

```python
ensure_directory(path: Any, mode: int)
```

Ensure directory exists.

---

## get_path_size

```python
get_path_size(path: Any)
```

Get file or directory size.

---

## get_size

```python
get_size(path: Any)
```

Get file or directory size (optimized).

**Parameters**:

- `path`: Path to file or directory

**Returns**: Size in bytes

---

## ignore_func

```python
ignore_func(directory: str, files: list[str]) -> list[str]
```

---

## move

```python
move(src: Any, dst: Any)
```

Move file or directory (optimized).

**Parameters**:

- `src`: Source path
- `dst`: Destination path

---

## move_file

```python
move_file(src: Any, dst: Any)
```

Move file or directory.

---

## remove

```python
remove(path: Any, recursive: bool)
```

Remove file or directory (optimized).

**Parameters**:

- `path`: Path to remove
- `recursive`: If True, remove directory recursively

---

## remove_path

```python
remove_path(path: Any, recursive: bool)
```

Remove file or directory.

---
