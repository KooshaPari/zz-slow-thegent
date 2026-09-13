# fast_subprocess API Reference

> **Source**: `src/thegent/infra/fast_subprocess.py`

Fast subprocess execution with async support and optimizations.

This module provides optimized subprocess execution with:

- Async subprocess support for concurrent execution
- Optimized process creation and management
- Better resource usage for concurrent operations
- Platform-specific optimizations

Performance improvements:

- Async execution for concurrent subprocesses (non-blocking)
- Optimized process creation flags
- Better resource management

---

## FastSubprocess

High-performance subprocess execution with async support.

### Methods

#### FastSubprocess.run_optimized

```python
run_optimized(cmd: list[str])
```

Run subprocess with optimizations (synchronous).

**Parameters**:

- `cmd`: Command and arguments
- `cwd`: Working directory
- `env`: Environment variables
- `timeout`: Timeout in seconds
- `check`: Raise exception on non-zero exit
- `capture_output`: Capture stdout/stderr
- `start_new_session`: Start new session (Unix)
- `close_fds`: Close file descriptors (Unix)
- `**kwargs`: Additional subprocess options

**Returns**: CompletedProcess with stdout, stderr, returncode

---

---

## run_optimized

```python
run_optimized(cmd: list[str])
```

Run subprocess with optimizations (synchronous).

**Parameters**:

- `cmd`: Command and arguments
- `cwd`: Working directory
- `env`: Environment variables
- `timeout`: Timeout in seconds
- `check`: Raise exception on non-zero exit
- `capture_output`: Capture stdout/stderr
- `start_new_session`: Start new session (Unix)
- `close_fds`: Close file descriptors (Unix)
- `**kwargs`: Additional subprocess options

**Returns**: CompletedProcess with stdout, stderr, returncode

---

## run_subprocess_optimized

```python
run_subprocess_optimized(cmd: list[str])
```

Run subprocess with optimizations.

**Parameters**:

- `input`: Input to send to stdin (str or bytes)
- `text`: If True, input/output are text (str), else bytes
- `**kwargs`: Additional subprocess options

---
