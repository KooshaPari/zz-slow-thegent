# jsonl_parser API Reference

> **Source**: `src/thegent/native/jsonl_parser.py`

BKM-10: Thin Python wrapper for thegent-jsonl native binary.

Streams JSON objects from JSONL (newline-delimited JSON) files without loading
entire files into memory. Two execution strategies (tried in order):

1. `thegent-jsonl` binary (Rust, streaming BufReader backend) — zero heap for
   entire-file load.
2. Pure Python fallback — `json.loads` line-by-line — always available.

The fallback is intentionally kept as a standalone, fully functional path so
the module works even when the Rust binary has not been compiled.

FR-JSONL-001 @trace FR-JSONL-001

---

## JsonlParser

Streaming JSONL parser.

Tries the `thegent-jsonl` Rust binary first; falls back to pure Python.

All methods operate lazily (generators) except :meth:`count` and

### Methods

#### JsonlParser.count

```python
count(self: Any, path: Path)
```

Return the number of non-blank lines in _path_.

**Parameters**:

- `path`: Path to a JSONL file.

**Returns**: Integer record count.

---

#### JsonlParser.filter

```python
filter(self: Any, path: Path, key: str, value: str)
```

Yield records from _path_ where `record[key] == value`.

**Parameters**:

- `path`: Path to a JSONL file.
- `key`: Top-level JSON field name.
- `value`: String value to match (coerced via `str()`).

**Returns**: Matching JSON objects.

---

#### JsonlParser.sample

```python
sample(self: Any, path: Path, n: int)
```

Return up to _n_ records from the start of _path_.

**Parameters**:

- `path`: Path to a JSONL file.
- `n`: Maximum number of records to return.

**Returns**: List of up to _n_ parsed JSON dicts.

---

#### JsonlParser.stream

```python
stream(self: Any, path: Path)
```

Yield every JSON object in _path_ without loading the file fully.

**Parameters**:

- `path`: Path to a JSONL file.

**Returns**: Parsed JSON objects as Python dicts. Non-dict values and
malformed lines are silently skipped.

---

---

## count

```python
count(self: Any, path: Path)
```

Return the number of non-blank lines in _path_.

**Parameters**:

- `path`: Path to a JSONL file.

**Returns**: Integer record count.

---

## filter

```python
filter(self: Any, path: Path, key: str, value: str)
```

Yield records from _path_ where `record[key] == value`.

**Parameters**:

- `path`: Path to a JSONL file.
- `key`: Top-level JSON field name.
- `value`: String value to match (coerced via `str()`).

**Returns**: Matching JSON objects.

---

## sample

```python
sample(self: Any, path: Path, n: int)
```

Return up to _n_ records from the start of _path_.

**Parameters**:

- `path`: Path to a JSONL file.
- `n`: Maximum number of records to return.

**Returns**: List of up to _n_ parsed JSON dicts.

---

## stream

```python
stream(self: Any, path: Path)
```

Yield every JSON object in _path_ without loading the file fully.

**Parameters**:

- `path`: Path to a JSONL file.

**Returns**: Parsed JSON objects as Python dicts. Non-dict values and
malformed lines are silently skipped.

---
