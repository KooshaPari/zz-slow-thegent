# session_tui API Reference

> **Source**: `src/thegent/ux/session_tui.py`

Rich TUI for session management with subagent monitoring and control.

---

## SessionTUI

Rich-based TUI for session management with subagent monitoring.

### Methods

#### SessionTUI.**init**

```python
__init__(self: Any, session_id: Any)
```

---

#### SessionTUI.manage_session

```python
manage_session(self: Any, session_id: str, action: str)
```

Manage a session (stop, pause, resume, logs).

---

#### SessionTUI.render_session_view

```python
render_session_view(self: Any, session_id: str)
```

Render detailed view for a specific session.

---

#### SessionTUI.render_sessions_list

```python
render_sessions_list(self: Any)
```

Render list of all sessions.

---

#### SessionTUI.show

```python
show(self: Any, session_id: Any)
```

Show session view (single session or list).

---

#### SessionTUI.watch

```python
watch(self: Any, session_id: Any, interval: float)
```

Watch sessions live with auto-refresh.

---

---

## manage_session

```python
manage_session(self: Any, session_id: str, action: str)
```

Manage a session (stop, pause, resume, logs).

---

## render_session_view

```python
render_session_view(self: Any, session_id: str)
```

Render detailed view for a specific session.

---

## render_sessions_list

```python
render_sessions_list(self: Any)
```

Render list of all sessions.

---

## show

```python
show(self: Any, session_id: Any)
```

Show session view (single session or list).

---

## watch

```python
watch(self: Any, session_id: Any, interval: float)
```

Watch sessions live with auto-refresh.

---
