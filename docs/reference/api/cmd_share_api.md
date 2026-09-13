# cmd_share API Reference

> **Source**: `src/thegent/orchestration/execution/cmd_share.py`

CLI-Share Command Debouncing and Stream Attachment.

Ensures heavy commands are shared across multiple agent tenants (L2)
under the same L1 project context.

---

## CommandSharer

Manages command debouncing using SHM locks.

If a command is already running, subsequent agents attach to its output.

### Methods

#### CommandSharer.**init**

```python
__init__(self: Any, session_dir: Path)
```

---

#### CommandSharer.execute_shared

```python
execute_shared(self: Any, command: list[str], cwd: Path, env: Any)
```

Execute a command or attach to an existing one if already running.

---

---

## execute_shared

```python
execute_shared(self: Any, command: list[str], cwd: Path, env: Any)
```

Execute a command or attach to an existing one if already running.

---
