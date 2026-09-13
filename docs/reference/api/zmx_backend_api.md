# zmx_backend API Reference

> **Source**: `src/thegent/session/zmx_backend.py`

zmx session persistence backend for thegent agent sessions.

zmx is a Zig-based muxless terminal session persistence tool (libghostty-vt).
It allows agent sessions to survive terminal detachment without tmux/screen.

Integration model: subprocess calls only (no C-ABI linking).
zmx not being installed degrades gracefully to tmux or none.

FR-SES-001: Session backend must be pluggable and auto-detected.
FR-SES-002: Missing backend must not raise at import time.
FR-SES-003: All backend methods must return typed results, never raise on
subprocess failure — caller decides how to handle.

---

## SessionBackend

Minimal protocol that all session backends must implement.

# @trace FR-SES-001

**Inherits from**: `Protocol`

### Methods

#### SessionBackend.attach

```python
attach(self: Any, session_name: str)
```

Attach to an existing session (interactive; blocks until detach).

Returns True on success, False if session does not exist or zmx failed.

---

#### SessionBackend.available

```python
available(self: Any)
```

Return True if the underlying tool is installed and functional.

---

#### SessionBackend.capture

```python
capture(self: Any, session_name: str, last_lines: int)
```

Return the last _last_lines_ lines of session output.

Returns an empty string if the session is unknown or capture fails.

---

#### SessionBackend.create

```python
create(self: Any, session_name: str, cmd: list[str])
```

Create and start a new named session running _cmd_.

Returns True on success, False on failure.

---

#### SessionBackend.kill

```python
kill(self: Any, session_name: str)
```

Terminate a named session.

Returns True on success, False if session was not found or kill failed.

---

#### SessionBackend.list

```python
list(self: Any)
```

Return all sessions known to this backend.

---

#### SessionBackend.name

```python
name(self: Any)
```

Human-readable backend identifier.

---

---

## ZmxBackend

Session backend that delegates to the `zmx` CLI.

All public methods are safe to call even when zmx is not installed —
they log a warning and return a safe fallback value.

# @trace FR-SES-001, FR-SES-002, FR-SES-003

### Methods

#### ZmxBackend.**init**

```python
__init__(self: Any, zmx_bin: str)
```

---

#### ZmxBackend.attach

```python
attach(self: Any, session_name: str)
```

Attach (interactively) to a running zmx session.

Calls: `zmx attach &lt;session_name&gt;`

This call blocks until the user detaches. Returns False when zmx is
unavailable or the session does not exist.

# @trace FR-SES-001

---

#### ZmxBackend.available

```python
available(self: Any)
```

Return True if zmx binary is present and responds.

Result is cached after first check.

# @trace FR-SES-002

---

#### ZmxBackend.capture

```python
capture(self: Any, session_name: str, last_lines: int)
```

Capture the last _last_lines_ lines of a session's scrollback.

Calls: `zmx capture &lt;session_name&gt; --lines &lt;last_lines&gt;`

Returns an empty string when zmx is unavailable or capture fails.

# @trace FR-SES-001

---

#### ZmxBackend.create

```python
create(self: Any, session_name: str, cmd: list[str])
```

Start a new zmx session running _cmd_.

Calls: `zmx new &lt;session_name&gt; -- &lt;cmd...&gt;`

Returns True on success, False on failure (including zmx not installed).

# @trace FR-SES-001

---

#### ZmxBackend.kill

```python
kill(self: Any, session_name: str)
```

Terminate a zmx session.

Calls: `zmx kill &lt;session_name&gt;`

Returns True on success, False on failure.

# @trace FR-SES-001

---

#### ZmxBackend.list

```python
list(self: Any)
```

Return all zmx sessions.

Calls: `zmx list --format json` (falling back to plain text parsing
if --format is unsupported in the installed version).

Returns an empty list when zmx is unavailable.

# @trace FR-SES-001

---

#### ZmxBackend.name

```python
name(self: Any)
```

---

---

## ZmxSession

Metadata for a single zmx-managed session.

---

## attach

```python
attach(self: Any, session_name: str)
```

Attach (interactively) to a running zmx session.

Calls: `zmx attach &lt;session_name&gt;`

This call blocks until the user detaches. Returns False when zmx is
unavailable or the session does not exist.

# @trace FR-SES-001

---

## available

```python
available(self: Any)
```

Return True if zmx binary is present and responds.

Result is cached after first check.

# @trace FR-SES-002

---

## capture

```python
capture(self: Any, session_name: str, last_lines: int)
```

Capture the last _last_lines_ lines of a session's scrollback.

Calls: `zmx capture &lt;session_name&gt; --lines &lt;last_lines&gt;`

Returns an empty string when zmx is unavailable or capture fails.

# @trace FR-SES-001

---

## create

```python
create(self: Any, session_name: str, cmd: list[str])
```

Start a new zmx session running _cmd_.

Calls: `zmx new &lt;session_name&gt; -- &lt;cmd...&gt;`

Returns True on success, False on failure (including zmx not installed).

# @trace FR-SES-001

---

## kill

```python
kill(self: Any, session_name: str)
```

Terminate a zmx session.

Calls: `zmx kill &lt;session_name&gt;`

Returns True on success, False on failure.

# @trace FR-SES-001

---

## list

```python
list(self: Any)
```

Return all zmx sessions.

Calls: `zmx list --format json` (falling back to plain text parsing
if --format is unsupported in the installed version).

Returns an empty list when zmx is unavailable.

# @trace FR-SES-001

---

## name

```python
name(self: Any) -> str
```

---

## resolve_session_backend

```python
resolve_session_backend(backend_override: Any)
```

Return the appropriate session backend based on configuration.

Selection order:

1. _backend_override_ argument (highest priority).
2. `THGENT_SESSION_BACKEND` environment variable.
3. Auto-detect: try zmx, then tmux sentinel, then none.

Currently only `zmx` and `none` are implemented. `tmux` is
acknowledged (returns None) so callers can fall back to the existing
tmux tooling in `thegent.tools.terminal`.

Returns a `ZmxBackend` when backend is `zmx`, or `None` when
the backend is `tmux` or `none` (caller uses legacy path).

# @trace FR-SES-001

---
