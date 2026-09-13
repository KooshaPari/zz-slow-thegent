# watchdog API Reference

> **Source**: `src/thegent/sitback/watchdog.py`

Background task watcher for non-blocking completion detection.

Provides polling-based detection of background task completion without blocking.
Used by the never-idle loop to wake on task completion.

---

## BackgroundTaskWatcher

Non-blocking watcher for background task completion.

Polls run_registry.jsonl for 'finish' events and checks session RC files.
Supports callback registration for completion notifications.

### Methods

#### BackgroundTaskWatcher.**init**

```python
__init__(self: Any, session_dir: Any, poll_interval: float)
```

Initialize the watcher.

**Parameters**:

- `session_dir`: Path to session directory. Defaults to ~/.thegent/sessions/
- `poll_interval`: Polling interval in seconds. Default 2.0

---

#### BackgroundTaskWatcher.check_completions

```python
check_completions(self: Any)
```

Check for newly completed tasks.

Polls run_registry.jsonl for 'finish' events and checks session RC files.

**Returns**: List of (session_id, exit_code) tuples for newly completed tasks.

---

#### BackgroundTaskWatcher.get_known_sessions

```python
get_known_sessions(self: Any)
```

Return set of known session IDs.

---

#### BackgroundTaskWatcher.register_callback

```python
register_callback(self: Any, callback: CompletionCallback)
```

Register a callback to be called on task completion.

**Parameters**:

- `callback`: Function(session_id, exit_code) to call when task completes.

---

#### BackgroundTaskWatcher.reset

```python
reset(self: Any)
```

Reset state (for testing).

---

#### BackgroundTaskWatcher.run_once

```python
run_once(self: Any)
```

Run one check cycle, trigger callbacks, return completions.

**Returns**: List of (session_id, exit_code) tuples for completed tasks.

---

#### BackgroundTaskWatcher.wait_for_completion

```python
wait_for_completion(self: Any, timeout: Any)
```

Wait for any task to complete.

This is a blocking wait with timeout. For non-blocking use run_once().

**Parameters**:

- `timeout`: Maximum seconds to wait. None = wait forever.

**Returns**: List of (session_id, exit_code) tuples for completed tasks.

---

---

## check_completions

```python
check_completions(self: Any)
```

Check for newly completed tasks.

Polls run_registry.jsonl for 'finish' events and checks session RC files.

**Returns**: List of (session_id, exit_code) tuples for newly completed tasks.

---

## get_known_sessions

```python
get_known_sessions(self: Any)
```

Return set of known session IDs.

---

## register_callback

```python
register_callback(self: Any, callback: CompletionCallback)
```

Register a callback to be called on task completion.

**Parameters**:

- `callback`: Function(session_id, exit_code) to call when task completes.

---

## reset

```python
reset(self: Any)
```

Reset state (for testing).

---

## run_once

```python
run_once(self: Any)
```

Run one check cycle, trigger callbacks, return completions.

**Returns**: List of (session_id, exit_code) tuples for completed tasks.

---

## wait_for_completion

```python
wait_for_completion(self: Any, timeout: Any)
```

Wait for any task to complete.

This is a blocking wait with timeout. For non-blocking use run_once().

**Parameters**:

- `timeout`: Maximum seconds to wait. None = wait forever.

**Returns**: List of (session_id, exit_code) tuples for completed tasks.

---
