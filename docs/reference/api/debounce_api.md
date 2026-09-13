# debounce API Reference

> **Source**: `src/thegent/hooks/debounce.py`

Implement debounce subcommand (file-based coordination).

---

## DebounceSubcommand

Debounce subcommand for file-based coordination.

### Methods

#### DebounceSubcommand.**init**

```python
__init__(self: Any, debounce_dir: Any)
```

Initialize debounce.

**Parameters**:

- `debounce_dir`: Directory for debounce files

---

#### DebounceSubcommand.clear

```python
clear(self: Any, key: str)
```

Clear debounce for a key.

**Parameters**:

- `key`: Debounce key

---

#### DebounceSubcommand.debounce

```python
debounce(self: Any, key: str, delay_seconds: float)
```

Check if operation should be debounced.

**Parameters**:

- `key`: Debounce key
- `delay_seconds`: Delay in seconds

**Returns**: True if should proceed, False if debounced

---

---

## clear

```python
clear(self: Any, key: str)
```

Clear debounce for a key.

**Parameters**:

- `key`: Debounce key

---

## debounce

```python
debounce(self: Any, key: str, delay_seconds: float)
```

Check if operation should be debounced.

**Parameters**:

- `key`: Debounce key
- `delay_seconds`: Delay in seconds

**Returns**: True if should proceed, False if debounced

---
