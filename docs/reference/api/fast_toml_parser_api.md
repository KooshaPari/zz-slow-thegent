# fast_toml_parser API Reference

> **Source**: `src/thegent/infra/fast_toml_parser.py`

Fast TOML parser with optimized backends.

This module provides a high-performance abstraction layer for TOML parsing
that automatically selects the fastest available backend:

- rtoml (Rust-based): 10-20x faster than tomlkit
- tomli/tomli-w (Python 3.11+): 3-5x faster for reading
- tomlkit: Standard fallback (good for editing)

Performance improvements:

- rtoml uses Rust implementation (10-20x faster)
- tomli optimized pure-Python (3-5x faster)
- Automatic backend selection based on availability and use case

---

## FastTOMLParser

High-performance TOML parser with automatic backend selection.

Backend priority (fastest first):

1. rtoml (if installed) - 10-20x faster, Rust-based
2. tomli/tomli-w (if installed) - 3-5x faster, pure-Python
3. tomlkit (standard fallback) - good for editing, slower for reading

### Methods

#### FastTOMLParser.**init**

```python
__init__(self: Any, edit_mode: bool)
```

Initialize TOML parser.

**Parameters**:

- `edit_mode`: If True, prefer tomlkit for editing capabilities

---

#### FastTOMLParser.backend

```python
backend(self: Any)
```

Get current backend name.

---

#### FastTOMLParser.dump

```python
dump(self: Any, data: dict[(str, Any)], stream: Any)
```

Dump TOML to string or file.

**Parameters**:

- `data`: Data to serialize
- `stream`: Optional file-like object or Path to write to
- `**kwargs`: Additional options

**Returns**: TOML string if stream is None, else None

---

#### FastTOMLParser.dumps

```python
dumps(self: Any, data: dict[(str, Any)])
```

Dump TOML to string.

**Parameters**:

- `data`: Data to serialize
- `**kwargs`: Additional options

**Returns**: TOML string

---

#### FastTOMLParser.load

```python
load(self: Any, stream: Any)
```

Load TOML from string or file path.

**Parameters**:

- `stream`: TOML string, Path object, or file-like object

**Returns**: Parsed TOML as dictionary

---

#### FastTOMLParser.loads

```python
loads(self: Any, s: str)
```

Load TOML from string.

**Parameters**:

- `s`: TOML string

**Returns**: Parsed TOML as dictionary

---

---

## backend

```python
backend(self: Any)
```

Get current backend name.

---

## dump

```python
dump(self: Any, data: dict[(str, Any)], stream: Any)
```

Dump TOML to string or file.

**Parameters**:

- `data`: Data to serialize
- `stream`: Optional file-like object or Path to write to
- `**kwargs`: Additional options

**Returns**: TOML string if stream is None, else None

---

## dumps

```python
dumps(self: Any, data: dict[(str, Any)])
```

Dump TOML to string.

**Parameters**:

- `data`: Data to serialize
- `**kwargs`: Additional options

**Returns**: TOML string

---

## get_toml_parser

```python
get_toml_parser(edit_mode: bool)
```

Get global fast TOML parser instance.

**Parameters**:

- `edit_mode`: If True, prefer tomlkit for editing capabilities

**Returns**: FastTOMLParser instance

---

## load

```python
load(self: Any, stream: Any)
```

Load TOML from string or file path.

**Parameters**:

- `stream`: TOML string, Path object, or file-like object

**Returns**: Parsed TOML as dictionary

---

## loads

```python
loads(self: Any, s: str)
```

Load TOML from string.

**Parameters**:

- `s`: TOML string

**Returns**: Parsed TOML as dictionary

---

## toml_dump

```python
toml_dump(data: dict[(str, Any)], stream: Any)
```

Dump TOML using fastest available backend.

---

## toml_dumps

```python
toml_dumps(data: dict[(str, Any)])
```

Dump TOML to string using fastest available backend.

---

## toml_load

```python
toml_load(stream: Any)
```

Load TOML using fastest available backend.

---

## toml_loads

```python
toml_loads(s: str)
```

Load TOML string using fastest available backend.

---
