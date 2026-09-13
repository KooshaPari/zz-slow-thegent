# scratchpad API Reference

> **Source**: `src/thegent/skills/scratchpad.py`

WP-22002: AI Scratchpad for Multi-Turn Command Drafting.

Provides a persistent buffer for drafting complex multi-line CLI commands.
Integration layer between agents and the shell buffer.

---

## AIScratchpad

Manages a persistent drafting buffer for CLI commands.

### Methods

#### AIScratchpad.**init**

```python
__init__(self: Any, state_path: Any)
```

---

#### AIScratchpad.add_line

```python
add_line(self: Any, line: str)
```

Add a command line to the buffer.

---

#### AIScratchpad.clear

```python
clear(self: Any)
```

Clear the buffer.

---

#### AIScratchpad.delete_last

```python
delete_last(self: Any)
```

Remove the last line from the buffer.

---

#### AIScratchpad.get_content

```python
get_content(self: Any)
```

Get the full content of the buffer.

---

#### AIScratchpad.set_metadata

```python
set_metadata(self: Any, key: str, value: str)
```

Set metadata for the current draft (e.g., task_id).

---

---

## ScratchpadState

Current state of the AI scratchpad.

**Inherits from**: `BaseModel`

---

## add_line

```python
add_line(self: Any, line: str)
```

Add a command line to the buffer.

---

## clear

```python
clear(self: Any)
```

Clear the buffer.

---

## delete_last

```python
delete_last(self: Any)
```

Remove the last line from the buffer.

---

## get_content

```python
get_content(self: Any)
```

Get the full content of the buffer.

---

## set_metadata

```python
set_metadata(self: Any, key: str, value: str)
```

Set metadata for the current draft (e.g., task_id).

---
