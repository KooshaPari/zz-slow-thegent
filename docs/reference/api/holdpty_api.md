# holdpty API Reference

> **Source**: `src/thegent/tools/holdpty.py`

PTY holder for headless interactive sessions (WP-9007).

---

## PTYHolder

Wraps a process in a PTY and exposes it via a Unix socket.

### Methods

#### PTYHolder.**init**

```python
__init__(self: Any, socket_path: Path, cmd: list[str], cwd: Any, env: Any)
```

---

#### PTYHolder.start

```python
start(self: Any)
```

Start the process and the proxy server.

---

#### PTYHolder.stop

```python
stop(self: Any)
```

---

---

## start

```python
start(self: Any)
```

Start the process and the proxy server.

---

## stop

```python
stop(self: Any)
```

---

## wrap_with_holdpty

```python
wrap_with_holdpty(cmd: list[str], session_id: str, socket_path: Path)
```

Return a command that runs the original command via holdpty holder.

---
