# fast_path_ops API Reference

> **Source**: `src/thegent/infra/fast_path_ops.py`

Fast path operations with optimizations.

This module provides optimized path operations:

- Direct os.path operations for hot paths
- Optimized path joining and normalization
- Fast path existence checks

Performance improvements:

- Direct os.path: Faster than pathlib for simple operations
- Optimized for common path operations

---

## FastPathOps

High-performance path operations with optimizations.

### Methods

#### FastPathOps.abspath

```python
abspath(path: str)
```

Get absolute path efficiently.

**Parameters**:

- `path`: Path to resolve

**Returns**: Absolute path

---

#### FastPathOps.basename

```python
basename(path: Any)
```

Get basename efficiently.

**Parameters**:

- `path`: Path

**Returns**: Basename (filename)

---

#### FastPathOps.dirname

```python
dirname(path: Any)
```

Get directory name efficiently.

**Parameters**:

- `path`: Path

**Returns**: Directory name

---

#### FastPathOps.exists

```python
exists(path: Any)
```

Check if path exists efficiently.

**Parameters**:

- `path`: Path to check

**Returns**: True if path exists

---

#### FastPathOps.is_dir

```python
is_dir(path: Any)
```

Check if path is a directory efficiently.

**Parameters**:

- `path`: Path to check

**Returns**: True if path is a directory

---

#### FastPathOps.is_file

```python
is_file(path: Any)
```

Check if path is a file efficiently.

**Parameters**:

- `path`: Path to check

**Returns**: True if path is a file

---

#### FastPathOps.join

Join path parts efficiently.

**Parameters**:

- `*parts`: Path components

**Returns**: Joined path string

---

#### FastPathOps.normalize

```python
normalize(path: str)
```

Normalize path efficiently.

**Parameters**:

- `path`: Path to normalize

**Returns**: Normalized path

---

#### FastPathOps.split

```python
split(path: Any)
```

Split path into directory and filename efficiently.

**Parameters**:

- `path`: Path to split

**Returns**: Tuple of (directory, filename)

---

#### FastPathOps.splitext

```python
splitext(path: Any)
```

Split path into base and extension efficiently.

**Parameters**:

- `path`: Path to split

**Returns**: Tuple of (base, extension)

---

---

## abspath

```python
abspath(path: str)
```

Get absolute path efficiently.

**Parameters**:

- `path`: Path to resolve

**Returns**: Absolute path

---

## basename

```python
basename(path: Any)
```

Get basename efficiently.

**Parameters**:

- `path`: Path

**Returns**: Basename (filename)

---

## dirname

```python
dirname(path: Any)
```

Get directory name efficiently.

**Parameters**:

- `path`: Path

**Returns**: Directory name

---

## exists

```python
exists(path: Any)
```

Check if path exists efficiently.

**Parameters**:

- `path`: Path to check

**Returns**: True if path exists

---

## is_dir

```python
is_dir(path: Any)
```

Check if path is a directory efficiently.

**Parameters**:

- `path`: Path to check

**Returns**: True if path is a directory

---

## is_file

```python
is_file(path: Any)
```

Check if path is a file efficiently.

**Parameters**:

- `path`: Path to check

**Returns**: True if path is a file

---

## join

Join path parts efficiently.

**Parameters**:

- `*parts`: Path components

**Returns**: Joined path string

---

## normalize

```python
normalize(path: str)
```

Normalize path efficiently.

**Parameters**:

- `path`: Path to normalize

**Returns**: Normalized path

---

## path_exists

```python
path_exists(path: Any)
```

Check if path exists efficiently.

---

## path_is_dir

```python
path_is_dir(path: Any)
```

Check if path is a directory efficiently.

---

## path_is_file

```python
path_is_file(path: Any)
```

Check if path is a file efficiently.

---

## path_join

Join path parts efficiently.

---

## path_normalize

```python
path_normalize(path: str)
```

Normalize path efficiently.

---

## split

```python
split(path: Any)
```

Split path into directory and filename efficiently.

**Parameters**:

- `path`: Path to split

**Returns**: Tuple of (directory, filename)

---

## splitext

```python
splitext(path: Any)
```

Split path into base and extension efficiently.

**Parameters**:

- `path`: Path to split

**Returns**: Tuple of (base, extension)

---
