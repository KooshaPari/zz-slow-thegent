# shell_strategy API Reference

> **Source**: `src/thegent/cross_platform/shell_strategy.py`

POSIX + PowerShell dual-shell strategy.

---

## DualShellStrategy

Dual-shell strategy for POSIX and PowerShell.

### Methods

#### DualShellStrategy.**init**

```python
__init__(self: Any)
```

Initialize shell strategy.

---

#### DualShellStrategy.execute

```python
execute(self: Any, command: str, capture_output: bool)
```

Execute command in appropriate shell.

**Parameters**:

- `command`: Command to execute
- `capture_output`: Whether to capture stdout/stderr

**Returns**: Execution result dictionary

---

#### DualShellStrategy.normalize_path

```python
normalize_path(self: Any, path: str)
```

Normalize path for current shell.

**Parameters**:

- `path`: Path to normalize

**Returns**: Normalized path

---

---

## execute

```python
execute(self: Any, command: str, capture_output: bool)
```

Execute command in appropriate shell.

**Parameters**:

- `command`: Command to execute
- `capture_output`: Whether to capture stdout/stderr

**Returns**: Execution result dictionary

---

## normalize_path

```python
normalize_path(self: Any, path: str)
```

Normalize path for current shell.

**Parameters**:

- `path`: Path to normalize

**Returns**: Normalized path

---
