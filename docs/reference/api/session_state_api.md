# session_state API Reference

> **Source**: `src/thegent/ui/compositor/session_state.py`

SessionState - Session persistence and management.

---

## SessionState

Manages session state persistence.

### Methods

#### SessionState.**init**

```python
__init__(self: Any, session_id: str, session_dir: Any)
```

Initialize SessionState.

**Parameters**:

- `session_id`: Unique session identifier
- `session_dir`: Directory for storing sessions (default: ~/.config/thegent/sessions)

---

#### SessionState.delete

```python
delete(self: Any)
```

Delete session state file.

**Returns**: True if successful, False otherwise

---

#### SessionState.list_sessions

```python
list_sessions(self: Any)
```

List all available sessions.

**Returns**: List of session IDs

---

#### SessionState.load

```python
load(self: Any)
```

Load session state from disk.

**Returns**: Dictionary of state, or None if not found

---

#### SessionState.save

```python
save(self: Any, state_data: dict)
```

Save session state to disk.

**Parameters**:

- `state_data`: Dictionary of state to save

**Returns**: True if successful, False otherwise

---

---

## delete

```python
delete(self: Any)
```

Delete session state file.

**Returns**: True if successful, False otherwise

---

## list_sessions

```python
list_sessions(self: Any)
```

List all available sessions.

**Returns**: List of session IDs

---

## load

```python
load(self: Any)
```

Load session state from disk.

**Returns**: Dictionary of state, or None if not found

---

## save

```python
save(self: Any, state_data: dict)
```

Save session state to disk.

**Parameters**:

- `state_data`: Dictionary of state to save

**Returns**: True if successful, False otherwise

---
