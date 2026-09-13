# keepalive API Reference

> **Source**: `src/thegent/ux/keepalive.py`

Terminal keepalive for long-running agent tasks.

Prints periodic dots/messages to stdout so the user can see the process
is still alive. Output is suppressed when stdout is not a TTY (CI/pipe).

Usage::

    from thegent.ux.keepalive import keepalive, KeepaliveConfig, TerminalKeepalive

    with keepalive(interval_s=30.0):
        long_running_operation()

    # Or with custom config:
    cfg = KeepaliveConfig(interval_s=10.0, message=".", newline_every=5)
    with TerminalKeepalive(cfg) as ka:
        long_running_operation()

---

## KeepaliveConfig

Configuration for :class:`TerminalKeepalive`.

---

## TerminalKeepalive

Prints periodic keepalive dots/messages to stdout.

Only prints when `sys.stdout.isatty()` returns _True_ so CI/pipe
environments receive no spurious output.

Thread safety: :meth:`start` and :meth:`stop` are safe to call from
any thread. The background printing thread is a daemon thread so the
process will not be blocked from exiting.

Example::

    with TerminalKeepalive() as ka:
        time.sleep(120)  # dots print every 30 s

### Methods

#### TerminalKeepalive.**init**

```python
__init__(self: Any, config: Any)
```

---

#### TerminalKeepalive.start

```python
start(self: Any)
```

Start the background keepalive thread.

If keepalive is disabled (`config.enabled is False`) or stdout
is not a TTY, this is a no-op. Calling :meth:`start` when the
thread is already running is safe — the existing thread continues.

---

#### TerminalKeepalive.stop

```python
stop(self: Any)
```

Stop the background keepalive thread and print a trailing newline.

Safe to call multiple times. Waits up to 1 second for the thread
to exit cleanly before returning.

---

---

## keepalive

```python
keepalive(interval_s: float, message: str)
```

Context manager convenience wrapper for :class:`TerminalKeepalive`.

Suppresses output when stdout is not a TTY (CI/pipe).

**Parameters**:

- `interval_s`: Seconds between each printed character.
- `message`: Character/string printed on each tick.

**Returns**: The running :class:`TerminalKeepalive` instance.

---

## start

```python
start(self: Any)
```

Start the background keepalive thread.

If keepalive is disabled (`config.enabled is False`) or stdout
is not a TTY, this is a no-op. Calling :meth:`start` when the
thread is already running is safe — the existing thread continues.

---

## stop

```python
stop(self: Any)
```

Stop the background keepalive thread and print a trailing newline.

Safe to call multiple times. Waits up to 1 second for the thread
to exit cleanly before returning.

---
