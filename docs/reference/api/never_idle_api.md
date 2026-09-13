# never_idle API Reference

> **Source**: `src/thegent/sitback/never_idle.py`

Never-idle loop engine for Sitback Agent.

Provides continuous resident loop with:

- Non-blocking background task completion detection
- Rotating gardening checks
- Wake-on-completion callbacks

---

## NeverIdleLoop

Resident never-idle loop for Sitback Agent.

Runs continuously with configurable sleep interval between iterations.
Checks for background task completions (non-blocking) and runs gardening steps.

### Methods

#### NeverIdleLoop.**init**

```python
__init__(self: Any, session_dir: Any, sleep_interval: int, project_root: Any)
```

Initialize the never-idle loop.

**Parameters**:

- `session_dir`: Path to session directory. Defaults to ~/.thegent/sessions/
- `sleep_interval`: Seconds to sleep between iterations. Default 45.
- `project_root`: Root directory for gardening. Defaults to cwd.

---

#### NeverIdleLoop.current_step

```python
current_step(self: Any)
```

Return the current gardening step name.

---

#### NeverIdleLoop.get_findings

```python
get_findings(self: Any)
```

Return gardening findings that need attention.

---

#### NeverIdleLoop.get_last_completion

```python
get_last_completion(self: Any)
```

Return last background task completion info.

---

#### NeverIdleLoop.get_status

```python
get_status(self: Any)
```

Get current status of the never-idle loop.

---

#### NeverIdleLoop.is_running

```python
is_running(self: Any)
```

Return whether the loop is currently running.

---

#### NeverIdleLoop.register_wake_callback

```python
register_wake_callback(self: Any, callback: WakeCallback)
```

Register a callback to be called when background task completes.

**Parameters**:

- `callback`: Function(list of (session_id, exit_code)) to call.

---

#### NeverIdleLoop.start

```python
start(self: Any)
```

Start the never-idle loop in a background thread.

---

#### NeverIdleLoop.stop

```python
stop(self: Any)
```

Stop the never-idle loop.

---

---

## current_step

```python
current_step(self: Any)
```

Return the current gardening step name.

---

## get_findings

```python
get_findings(self: Any)
```

Return gardening findings that need attention.

---

## get_last_completion

```python
get_last_completion(self: Any)
```

Return last background task completion info.

---

## get_never_idle

Get the global never-idle loop instance.

---

## get_never_idle_status

Get status of the global never-idle loop.

---

## get_status

```python
get_status(self: Any)
```

Get current status of the never-idle loop.

---

## is_running

```python
is_running(self: Any)
```

Return whether the loop is currently running.

---

## register_wake_callback

```python
register_wake_callback(self: Any, callback: WakeCallback)
```

Register a callback to be called when background task completes.

**Parameters**:

- `callback`: Function(list of (session_id, exit_code)) to call.

---

## start

```python
start(self: Any)
```

Start the never-idle loop in a background thread.

---

## start_never_idle

```python
start_never_idle(sleep_interval: int, session_dir: Any, project_root: Any)
```

Start the global never-idle loop.

**Parameters**:

- `sleep_interval`: Seconds between iterations.
- `session_dir`: Path to session directory.
- `project_root`: Root directory for gardening.

**Returns**: The started NeverIdleLoop instance.

---

## stop

```python
stop(self: Any)
```

Stop the never-idle loop.

---

## stop_never_idle

Stop the global never-idle loop.

---
