# zmx_session API Reference

> **Source**: `src/thegent/muxless/zmx_session.py`

Muxless zmx session persistence manager for thegent agent sessions.

Provides a high-level manager for creating and managing zmx virtual terminal
sessions, enabling agent sessions to persist without tmux/screen.

Integration model: subprocess calls only via subprocess.run (never os.system).
zmx not being installed degrades gracefully -- all methods return safe defaults.

FR-SES-001: Session backend must be pluggable and auto-detected.
FR-SES-002: Missing backend must not raise at import time.
FR-SES-003: All backend methods must return typed results, never raise on
subprocess failure -- caller decides how to handle.

---

## ZmxSessionConfig

Configuration for ZmxSessionManager.

### Methods

#### ZmxSessionConfig.from_env

```python
from_env(cls: Any)
```

Deprecated: Use from_settings() instead.

---

#### ZmxSessionConfig.from_settings

```python
from_settings(cls: Any)
```

Build a ZmxSessionConfig reading values from settings.

---

---

## ZmxSessionManager

High-level manager for zmx muxless virtual terminal sessions.

All public methods are safe to call even when zmx is not installed --
they log a warning and return a safe fallback value.

Subprocess integration: all zmx calls go through subprocess.run().

# @trace FR-SES-001, FR-SES-002, FR-SES-003

### Methods

#### ZmxSessionManager.**init**

```python
__init__(self: Any, config: Any)
```

Create a ZmxSessionManager.

**Parameters**:

- `config`: Optional configuration. When None, defaults are used.

---

#### ZmxSessionManager.attach_session

```python
attach_session(self: Any, session_name: str)
```

Attach (interactively) to an existing zmx session.

Calls: `zmx attach &lt;session_name&gt;`

This call blocks until the user detaches from the session.

**Parameters**:

- `session_name`: Name of the session to attach to.

**Returns**: True on success, False when zmx is unavailable or the session
does not exist.

---

#### ZmxSessionManager.capture_output

```python
capture_output(self: Any, session_name: str, lines: int)
```

Capture the last _lines_ lines of output from a zmx session.

Calls: `zmx capture &lt;session_name&gt; --lines &lt;lines&gt;`

**Parameters**:

- `session_name`: Name of the session to capture from.
- `lines`: Number of trailing lines to return (default 100).

**Returns**: Captured output as a string, or empty string on failure.

---

#### ZmxSessionManager.create_session

```python
create_session(self: Any, session_id: str, command: list[str])
```

Create a new zmx session running _command_.

Calls: `zmx new &lt;session_id&gt; -- &lt;command...&gt;`

**Parameters**:

- `session_id`: Unique session identifier; becomes the zmx session name.
- `command`: Command and arguments to run inside the session.

**Returns**: The session name (same as _session_id_) on success, or an empty
string on failure (including when zmx is unavailable).

---

#### ZmxSessionManager.destroy_session

```python
destroy_session(self: Any, session_name: str)
```

Terminate and clean up a zmx session.

Calls: `zmx kill &lt;session_name&gt;`

**Parameters**:

- `session_name`: Name of the session to destroy.

**Returns**: True on success, False on failure.

---

#### ZmxSessionManager.is_available

```python
is_available(self: Any)
```

Return True if the zmx binary is present and functional.

The result is cached after the first check.

# @trace FR-SES-002

---

#### ZmxSessionManager.list_sessions

```python
list_sessions(self: Any)
```

Return the names of all active zmx sessions.

Calls: `zmx list` (or `zmx list --format json` if supported).

**Returns**: Sorted list of session name strings, or empty list on failure.

---

#### ZmxSessionManager.send_input

```python
send_input(self: Any, session_name: str, text: str)
```

Send keystrokes (text) to a zmx session.

Calls: `zmx send-keys &lt;session_name&gt; &lt;text&gt;`

**Parameters**:

- `session_name`: Target session name.
- `text`: Text to deliver as keystrokes.

**Returns**: True on success, False on failure (including zmx unavailable).

---

---

## attach_session

```python
attach_session(self: Any, session_name: str)
```

Attach (interactively) to an existing zmx session.

Calls: `zmx attach &lt;session_name&gt;`

This call blocks until the user detaches from the session.

**Parameters**:

- `session_name`: Name of the session to attach to.

**Returns**: True on success, False when zmx is unavailable or the session
does not exist.

---

## capture_output

```python
capture_output(self: Any, session_name: str, lines: int)
```

Capture the last _lines_ lines of output from a zmx session.

Calls: `zmx capture &lt;session_name&gt; --lines &lt;lines&gt;`

**Parameters**:

- `session_name`: Name of the session to capture from.
- `lines`: Number of trailing lines to return (default 100).

**Returns**: Captured output as a string, or empty string on failure.

---

## create_session

```python
create_session(self: Any, session_id: str, command: list[str])
```

Create a new zmx session running _command_.

Calls: `zmx new &lt;session_id&gt; -- &lt;command...&gt;`

**Parameters**:

- `session_id`: Unique session identifier; becomes the zmx session name.
- `command`: Command and arguments to run inside the session.

**Returns**: The session name (same as _session_id_) on success, or an empty
string on failure (including when zmx is unavailable).

---

## destroy_session

```python
destroy_session(self: Any, session_name: str)
```

Terminate and clean up a zmx session.

Calls: `zmx kill &lt;session_name&gt;`

**Parameters**:

- `session_name`: Name of the session to destroy.

**Returns**: True on success, False on failure.

---

## from_env

```python
from_env(cls: Any)
```

Deprecated: Use from_settings() instead.

---

## from_settings

```python
from_settings(cls: Any)
```

Build a ZmxSessionConfig reading values from settings.

---

## is_available

```python
is_available(self: Any)
```

Return True if the zmx binary is present and functional.

The result is cached after the first check.

# @trace FR-SES-002

---

## list_sessions

```python
list_sessions(self: Any)
```

Return the names of all active zmx sessions.

Calls: `zmx list` (or `zmx list --format json` if supported).

**Returns**: Sorted list of session name strings, or empty list on failure.

---

## make_zmx_session_manager

```python
make_zmx_session_manager(config: Any)
```

Create a ZmxSessionManager, reading config from environment if not provided.

Reads `THGENT_ZMX_BINARY` to determine the zmx binary path.

**Parameters**:

- `config`: Optional pre-built config. When None, config is built from
  environment variables via :meth:`ZmxSessionConfig.from_env`.

**Returns**: A configured :class:`ZmxSessionManager` instance.

---

## send_input

```python
send_input(self: Any, session_name: str, text: str)
```

Send keystrokes (text) to a zmx session.

Calls: `zmx send-keys &lt;session_name&gt; &lt;text&gt;`

**Parameters**:

- `session_name`: Target session name.
- `text`: Text to deliver as keystrokes.

**Returns**: True on success, False on failure (including zmx unavailable).

---
