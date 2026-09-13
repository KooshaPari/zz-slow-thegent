# file_index API Reference

> **Source**: `src/thegent/indexing/file_index.py`

File indexing (fd-style) for fast find patterns.

Provides a TTL-based in-memory file index built with os.scandir for
performance. Avoids repeated filesystem traversals for common find patterns.

Design reference: docs/research/CACHING_INDEXING_PREWARMING_DEEP_RESEARCH.md §3.1

---

## FileIndex

In-memory file index with TTL-based invalidation.

Builds the index once using `os.scandir` (faster than `os.walk`),
then serves queries from memory until the TTL expires.

Usage::

    idx = FileIndex()
    idx.build(Path("/my/project"))
    py_files = idx.find_by_ext(".py")
    configs  = idx.find_by_name("pyproject.toml")
    srcs     = idx.find("src/**/*.py")

### Methods

#### FileIndex.**init**

```python
__init__(self: Any, ttl: Any)
```

---

#### FileIndex.build

```python
build(self: Any, root: Path, exclude_dirs: Any)
```

Scan _root_ recursively and cache the result.

**Parameters**:

- `root`: Directory to index.
- `exclude_dirs`: Directory names to skip during traversal.
- `force`: Rebuild even if a valid cached index exists.

**Returns**: List of all non-excluded file paths found under _root_.

---

#### FileIndex.find

```python
find(self: Any, pattern: str, root: Any)
```

Return paths matching a glob _pattern_ (e.g. `src/**/*.py`).

The index for _root_ must already be built (or will be built on demand).

---

#### FileIndex.find_by_ext

```python
find_by_ext(self: Any, ext: str, root: Any)
```

Return paths with the given extension (e.g. `".py"`).

The leading dot is optional: `"py"` and `".py"` both work.

---

#### FileIndex.find_by_name

```python
find_by_name(self: Any, name: str, root: Any)
```

Return paths whose filename (last component) equals _name_.

---

#### FileIndex.invalidate

```python
invalidate(self: Any, root: Any)
```

Manually expire the cache for _root_ (or all roots if None).

---

#### FileIndex.is_cached

```python
is_cached(self: Any, root: Path)
```

Return True if a valid (non-expired) index exists for _root_.

---

---

## build

```python
build(self: Any, root: Path, exclude_dirs: Any)
```

Scan _root_ recursively and cache the result.

**Parameters**:

- `root`: Directory to index.
- `exclude_dirs`: Directory names to skip during traversal.
- `force`: Rebuild even if a valid cached index exists.

**Returns**: List of all non-excluded file paths found under _root_.

---

## find

```python
find(self: Any, pattern: str, root: Any)
```

Return paths matching a glob _pattern_ (e.g. `src/**/*.py`).

The index for _root_ must already be built (or will be built on demand).

---

## find_by_ext

```python
find_by_ext(self: Any, ext: str, root: Any)
```

Return paths with the given extension (e.g. `".py"`).

The leading dot is optional: `"py"` and `".py"` both work.

---

## find_by_name

```python
find_by_name(self: Any, name: str, root: Any)
```

Return paths whose filename (last component) equals _name_.

---

## invalidate

```python
invalidate(self: Any, root: Any)
```

Manually expire the cache for _root_ (or all roots if None).

---

## is_cached

```python
is_cached(self: Any, root: Path)
```

Return True if a valid (non-expired) index exists for _root_.

---
