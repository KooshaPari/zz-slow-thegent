# terminal_capture API Reference

> **Source**: `src/thegent/utils/terminal_capture.py`

Multi-backend terminal output capture.

Provides a unified interface for capturing the last N lines of terminal output
across multiple backends: tmux, zmx, /proc fd, termitty, and a null fallback.

Selection order (first available wins):

1. tmux -- `capture-pane` via subprocess
2. zmx -- ZmxBackend.capture() if zmx binary present
3. proc -- read /proc/{pid}/fd/1 on Linux
4. termitty -- VirtualTerminal.process_output() on already-captured bytes
5. none -- empty result

FR-SES-001: Session backend must be pluggable and auto-detected.
FR-SES-002: Missing backend must not raise at import time.
FR-SES-003: All backend methods must return typed results, never raise on
subprocess failure -- caller decides how to handle.

---

## CaptureResult

Result of a terminal capture operation.

# @trace FR-SES-001

---

## TerminalCapture

Unified multi-backend terminal output capture.

Instantiate once and call :meth:`capture_last_n_lines` or

### Methods

#### TerminalCapture.capture_by_pid

```python
capture_by_pid(self: Any, pid: int, n: int)
```

Capture the last _n_ lines of output from process _pid_.

Backend selection order:

1. /proc/{pid}/fd/1 -- Linux only
2. termitty -- feed any bytes obtained from other sources
3. none -- empty fallback

**Parameters**:

- `pid`: Target process ID.
- `n`: Number of lines to capture (default 50).

**Returns**: A :class:`CaptureResult` with `backend` indicating which path
was used and `pane_id` set to `str(pid)`.

---

#### TerminalCapture.capture_last_n_lines

```python
capture_last_n_lines(self: Any, n: int, pane_id: Any)
```

Capture the last _n_ lines of terminal output.

Backend selection order:

1. tmux -- if a _pane_id_ is given and tmux is available
2. zmx -- if a _pane_id_ is given (treated as session name) and zmx is available
3. termitty -- reads the controlling tty of the current process
4. none -- empty fallback

**Parameters**:

- `n`: Number of lines to capture (default 50).
- `pane_id`: tmux pane id (e.g. `%0`) **or** zmx session name.
  When None the tmux/zmx backends are skipped.

**Returns**: A :class:`CaptureResult` with `backend` indicating which path
was used.

---

---

## capture_by_pid

```python
capture_by_pid(self: Any, pid: int, n: int)
```

Capture the last _n_ lines of output from process _pid_.

Backend selection order:

1. /proc/{pid}/fd/1 -- Linux only
2. termitty -- feed any bytes obtained from other sources
3. none -- empty fallback

**Parameters**:

- `pid`: Target process ID.
- `n`: Number of lines to capture (default 50).

**Returns**: A :class:`CaptureResult` with `backend` indicating which path
was used and `pane_id` set to `str(pid)`.

---

## capture_last_n_lines

```python
capture_last_n_lines(self: Any, n: int, pane_id: Any)
```

Capture the last _n_ lines of terminal output.

Backend selection order:

1. tmux -- if a _pane_id_ is given and tmux is available
2. zmx -- if a _pane_id_ is given (treated as session name) and zmx is available
3. termitty -- reads the controlling tty of the current process
4. none -- empty fallback

**Parameters**:

- `n`: Number of lines to capture (default 50).
- `pane_id`: tmux pane id (e.g. `%0`) **or** zmx session name.
  When None the tmux/zmx backends are skipped.

**Returns**: A :class:`CaptureResult` with `backend` indicating which path
was used.

---
