# terminal_keepalive API Reference

> **Source**: `src/thegent/infra/terminal_keepalive.py`

Terminal keepalive mechanism to prevent timeout in long-running commands.

Detects the calling terminal and sends keepalive input (Enter key) periodically
to prevent timeout (e.g., Cursor's 4-minute guard).

This module provides a robust keepalive mechanism that:

- Detects parent terminal processes using multiple methods
- Sends keepalive signals via stdin or tmux
- Handles errors gracefully without affecting the main process
- Provides detailed logging for debugging

---

## TerminalKeepalive

Manages keepalive mechanism for long-running commands.

Thread-safe, robust keepalive that handles errors gracefully and provides
detailed logging for debugging. Automatically detects the best keepalive
method based on the environment.

### Methods

#### TerminalKeepalive.**init**

```python
__init__(self: Any, interval: float, enabled: bool, max_failures: int)
```

Initialize keepalive.

**Parameters**:

- `interval`: Seconds between keepalive signals (default: 180s)
- `enabled`: Whether keepalive is enabled
- `max_failures`: Maximum consecutive failures before disabling (default: 3)

---

#### TerminalKeepalive.get_stats

```python
get_stats(self: Any)
```

Get keepalive statistics.

**Returns**: Dict with success_count, failure_count, last_success_time, is_running

---

#### TerminalKeepalive.should_enable

```python
should_enable(self: Any)
```

Check if keepalive should be enabled based on environment.

Uses multiple detection methods for robustness:

1. Environment variable detection (fastest)
2. Process inspection (most accurate)
3. TTY detection (fallback)

**Returns**: True if keepalive should be enabled, False otherwise

---

#### TerminalKeepalive.start

```python
start(self: Any)
```

Start keepalive thread.

Thread-safe: can be called multiple times safely.

**Returns**: True if started, False otherwise

---

#### TerminalKeepalive.stop

```python
stop(self: Any)
```

Stop keepalive thread.

Thread-safe: can be called multiple times safely.
Waits up to 2 seconds for thread to finish.

---

---

## create_keepalive

```python
create_keepalive(interval: float, enabled: bool, max_failures: int)
```

Create a keepalive instance.

Factory function for creating TerminalKeepalive instances with
sensible defaults.

**Parameters**:

- `interval`: Seconds between keepalive signals (default: 180s, min: 30s)
- `enabled`: Whether keepalive is enabled (default: True)
- `max_failures`: Max consecutive failures before disabling (default: 3)

**Returns**: TerminalKeepalive instance

**Examples**:

```python
>>> keepalive = create_keepalive(interval=120.0)
>>> if keepalive.start():
...     try:
...         # Long-running operation
...         pass
...     finally:
...         keepalive.stop()
```

---

## get_stats

```python
get_stats(self: Any)
```

Get keepalive statistics.

**Returns**: Dict with success_count, failure_count, last_success_time, is_running

---

## should_enable

```python
should_enable(self: Any)
```

Check if keepalive should be enabled based on environment.

Uses multiple detection methods for robustness:

1. Environment variable detection (fastest)
2. Process inspection (most accurate)
3. TTY detection (fallback)

**Returns**: True if keepalive should be enabled, False otherwise

---

## start

```python
start(self: Any)
```

Start keepalive thread.

Thread-safe: can be called multiple times safely.

**Returns**: True if started, False otherwise

---

## stop

```python
stop(self: Any)
```

Stop keepalive thread.

Thread-safe: can be called multiple times safely.
Waits up to 2 seconds for thread to finish.

---
