# incremental API Reference

> **Source**: `src/thegent/hooks/incremental.py`

Implement incremental-check/record subcommands (manifest-based).

---

## IncrementalSubcommands

Incremental check/record subcommands.

### Methods

#### IncrementalSubcommands.**init**

```python
__init__(self: Any, manifest_path: Any)
```

Initialize incremental subcommands.

**Parameters**:

- `manifest_path`: Manifest file path

---

#### IncrementalSubcommands.check

```python
check(self: Any, file_path: Path)
```

Check if file needs processing.

**Parameters**:

- `file_path`: File to check

**Returns**: True if needs processing

---

#### IncrementalSubcommands.record

```python
record(self: Any, file_path: Path)
```

Record file as processed.

**Parameters**:

- `file_path`: File to record

---

---

## check

```python
check(self: Any, file_path: Path)
```

Check if file needs processing.

**Parameters**:

- `file_path`: File to check

**Returns**: True if needs processing

---

## record

```python
record(self: Any, file_path: Path)
```

Record file as processed.

**Parameters**:

- `file_path`: File to record

---
