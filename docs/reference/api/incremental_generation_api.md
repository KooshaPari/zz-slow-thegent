# incremental_generation API Reference

> **Source**: `src/thegent/docgen/incremental_generation.py`

Incremental documentation generation (only changed files).

---

## IncrementalGenerator

Generate documentation only for changed files.

### Methods

#### IncrementalGenerator.**init**

```python
__init__(self: Any, manifest_path: Any)
```

Initialize incremental generator.

**Parameters**:

- `manifest_path`: Path to manifest file

---

#### IncrementalGenerator.generate_incremental

```python
generate_incremental(self: Any, files: list[Path], generator_func: callable)
```

Generate documentation incrementally.

**Parameters**:

- `files`: List of files to check
- `generator_func`: Function to generate docs

**Returns**: Generation results

---

#### IncrementalGenerator.get_changed_files

```python
get_changed_files(self: Any, files: list[Path])
```

Get list of changed files.

**Parameters**:

- `files`: List of files to check

**Returns**: List of changed files

---

---

## generate_incremental

```python
generate_incremental(self: Any, files: list[Path], generator_func: callable)
```

Generate documentation incrementally.

**Parameters**:

- `files`: List of files to check
- `generator_func`: Function to generate docs

**Returns**: Generation results

---

## get_changed_files

```python
get_changed_files(self: Any, files: list[Path])
```

Get list of changed files.

**Parameters**:

- `files`: List of files to check

**Returns**: List of changed files

---
