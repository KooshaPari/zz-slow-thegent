# session API Reference

> **Source**: `src/thegent/tui/session.py`

Session persistence for TUI compositor.

Saves and restores session state including layouts, history, and settings.

---

## SessionInfo

Session metadata.

---

## SessionPersistence

Manages session persistence to disk.

### Methods

#### SessionPersistence.**init**

```python
__init__(self: Any, storage_dir: Any)
```

---

#### SessionPersistence.cleanup_old_sessions

```python
cleanup_old_sessions(self: Any, max_age_days: int)
```

Delete sessions older than max_age_days.

---

#### SessionPersistence.create_session

```python
create_session(self: Any, session_id: str, agent_name: Any, cwd: Any)
```

Create a new session.

---

#### SessionPersistence.delete_session

```python
delete_session(self: Any, session_id: str)
```

Delete a session.

---

#### SessionPersistence.get_current_session

```python
get_current_session(self: Any)
```

Get the current session.

---

#### SessionPersistence.get_layout_for_session

```python
get_layout_for_session(self: Any, session_id: str)
```

Get the saved layout for a session.

---

#### SessionPersistence.get_session

```python
get_session(self: Any, session_id: str)
```

Get a session by ID.

---

#### SessionPersistence.get_statistics

```python
get_statistics(self: Any)
```

Get session statistics.

---

#### SessionPersistence.list_sessions

```python
list_sessions(self: Any)
```

List all session IDs.

---

#### SessionPersistence.load_state

```python
load_state(self: Any, session_id: str, key: str, default: Any)
```

Load state for a session.

---

#### SessionPersistence.save_layout_for_session

```python
save_layout_for_session(self: Any, session_id: str, layout_state: LayoutState)
```

Save a layout for a specific session.

---

#### SessionPersistence.save_state

```python
save_state(self: Any, session_id: str, key: str, value: Any)
```

Save arbitrary state for a session.

---

#### SessionPersistence.set_current_session

```python
set_current_session(self: Any, session_id: str)
```

Set the current active session.

---

#### SessionPersistence.update_session

```python
update_session(self: Any, session_id: str)
```

Update session fields.

---

---

## cleanup_old_sessions

```python
cleanup_old_sessions(self: Any, max_age_days: int)
```

Delete sessions older than max_age_days.

---

## create_session

```python
create_session(self: Any, session_id: str, agent_name: Any, cwd: Any)
```

Create a new session.

---

## delete_session

```python
delete_session(self: Any, session_id: str)
```

Delete a session.

---

## get_current_session

```python
get_current_session(self: Any)
```

Get the current session.

---

## get_layout_for_session

```python
get_layout_for_session(self: Any, session_id: str)
```

Get the saved layout for a session.

---

## get_session

```python
get_session(self: Any, session_id: str)
```

Get a session by ID.

---

## get_statistics

```python
get_statistics(self: Any)
```

Get session statistics.

---

## list_sessions

```python
list_sessions(self: Any)
```

List all session IDs.

---

## load_state

```python
load_state(self: Any, session_id: str, key: str, default: Any)
```

Load state for a session.

---

## save_layout_for_session

```python
save_layout_for_session(self: Any, session_id: str, layout_state: LayoutState)
```

Save a layout for a specific session.

---

## save_state

```python
save_state(self: Any, session_id: str, key: str, value: Any)
```

Save arbitrary state for a session.

---

## set_current_session

```python
set_current_session(self: Any, session_id: str)
```

Set the current active session.

---

## update_session

```python
update_session(self: Any, session_id: str)
```

Update session fields.

---
