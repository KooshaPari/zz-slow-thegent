# session_watcher API Reference

> **Source**: `src/thegent/orchestration/session_watcher.py`

Session event watcher for auto-launch system.

Watches session directories for completion events using FastFileWatcher.
Harmonized with BackgroundTaskWatcher and NeverIdleLoop.

---

## CompletionHandler

### Methods

#### CompletionHandler.**init**

```python
__init__(self: Any, watcher: SessionEventWatcher)
```

---

#### CompletionHandler.on_completion

```python
on_completion(self: Any, session_id: str, exit_code: int)
```

Handle session completion.

---

---

## SessionEventWatcher

Watches session directories for completion events.

### Methods

#### SessionEventWatcher.**init**

```python
__init__(self: Any, session_dir: Path)
```

Initialize session event watcher.

**Parameters**:

- `session_dir`: Path to session directory (~/.cache/thegent/sessions)

---

#### SessionEventWatcher.on_complete

```python
on_complete(self: Any, callback: Callable[(Any, None)])
```

Register a callback for session completion events.

**Parameters**:

- `callback`: Function(session_id: str, exit_code: int) -> None

---

#### SessionEventWatcher.start

```python
start(self: Any)
```

Start watching for session completion events.

---

#### SessionEventWatcher.stop

```python
stop(self: Any)
```

Stop watching for events.

---

---

## on_complete

```python
on_complete(self: Any, callback: Callable[(Any, None)])
```

Register a callback for session completion events.

**Parameters**:

- `callback`: Function(session_id: str, exit_code: int) -> None

---

## on_completion

```python
on_completion(self: Any, session_id: str, exit_code: int)
```

Handle session completion.

---

## start

```python
start(self: Any)
```

Start watching for session completion events.

---

## stop

```python
stop(self: Any)
```

Stop watching for events.

---

## watch_loop

---
