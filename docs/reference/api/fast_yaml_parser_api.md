# fast_yaml_parser API Reference

> **Source**: `src/thegent/infra/fast_yaml_parser.py`

Fast YAML parser with optimized backends.

This module provides a high-performance abstraction layer for YAML parsing
that automatically selects the fastest available backend:

- oyaml (orjson-based): 3-5x faster than PyYAML
- ruamel.yaml: 2-3x faster, preserves formatting
- PyYAML: Standard fallback

Performance improvements:

- oyaml uses orjson for JSON-like speed (3-5x faster)
- ruamel.yaml optimized C implementation (2-3x faster)
- Automatic backend selection based on availability

---

## FastYAMLParser

High-performance YAML parser with automatic backend selection.

Backend priority (fastest first):

1. oyaml (if installed) - 3-5x faster, orjson-based
2. ruamel.yaml (if installed) - 2-3x faster, preserves formatting
3. PyYAML (standard fallback) - baseline performance

### Methods

#### FastYAMLParser.**init**

```python
__init__(self: Any, preserve_formatting: bool)
```

Initialize YAML parser.

**Parameters**:

- `preserve_formatting`: If True, prefer ruamel.yaml for round-trip preservation

---

#### FastYAMLParser.backend

```python
backend(self: Any)
```

Get current backend name.

---

#### FastYAMLParser.dump

```python
dump(self: Any, data: dict[(str, Any)], stream: Any)
```

Dump YAML to string or file.

**Parameters**:

- `data`: Data to serialize
- `stream`: Optional file-like object or Path to write to
- `**kwargs`: Additional options

**Returns**: YAML string if stream is None, else None

---

#### FastYAMLParser.dumps

```python
dumps(self: Any, data: dict[(str, Any)])
```

Dump YAML to string.

**Parameters**:

- `data`: Data to serialize
- `**kwargs`: Additional options

**Returns**: YAML string

---

#### FastYAMLParser.load

```python
load(self: Any, stream: Any)
```

Load YAML from string or file path.

**Parameters**:

- `stream`: YAML string, Path object, or file-like object

**Returns**: Parsed YAML as dictionary

---

#### FastYAMLParser.loads

```python
loads(self: Any, s: str)
```

Load YAML from string.

**Parameters**:

- `s`: YAML string

**Returns**: Parsed YAML as dictionary

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

Dump YAML to string or file.

**Parameters**:

- `data`: Data to serialize
- `stream`: Optional file-like object or Path to write to
- `**kwargs`: Additional options

**Returns**: YAML string if stream is None, else None

---

## dumps

```python
dumps(self: Any, data: dict[(str, Any)])
```

Dump YAML to string.

**Parameters**:

- `data`: Data to serialize
- `**kwargs`: Additional options

**Returns**: YAML string

---

## get_yaml_parser

```python
get_yaml_parser(preserve_formatting: bool)
```

Get global fast YAML parser instance.

**Parameters**:

- `preserve_formatting`: If True, prefer ruamel.yaml for round-trip preservation

**Returns**: FastYAMLParser instance

---

## load

```python
load(self: Any, stream: Any)
```

Load YAML from string or file path.

**Parameters**:

- `stream`: YAML string, Path object, or file-like object

**Returns**: Parsed YAML as dictionary

---

## loads

```python
loads(self: Any, s: str)
```

Load YAML from string.

**Parameters**:

- `s`: YAML string

**Returns**: Parsed YAML as dictionary

---

## yaml_dump

```python
yaml_dump(data: dict[(str, Any)], stream: Any)
```

Dump YAML using fastest available backend.

---

## yaml_dumps

```python
yaml_dumps(data: dict[(str, Any)])
```

Dump YAML to string using fastest available backend.

---

## yaml_load

```python
yaml_load(stream: Any)
```

Load YAML using fastest available backend.

---

## yaml_loads

```python
yaml_loads(s: str)
```

Load YAML string using fastest available backend.

---
