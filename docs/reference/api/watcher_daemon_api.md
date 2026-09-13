# watcher_daemon API Reference

> **Source**: `src/thegent/native/watcher_daemon.py`

BKM-09: Multi-tenant file watcher daemon using the watchdog library.

This module provides `WatcherDaemon`, a singleton daemon that manages multiple
independent watch specs concurrently via a single `watchdog.observers.Observer`
thread. Each spec targets a root directory with optional glob patterns, and
fires a typed `WatchEvent` callback in the watcher thread.

A `CircuitBreakerShm` integration is optionally available to track watcher
health: callback errors increment the breaker's failure counter.

Usage::

    from thegent.native.watcher_daemon import WatchEvent, WatchSpec, get_watcher_daemon

    daemon = get_watcher_daemon()
    daemon.start()

    def on_event(ev: WatchEvent) -&gt; None:
        print(ev.event_type, ev.src_path)

    spec = WatchSpec(root=Path("."), patterns=["*.py"], recursive=True, callback=on_event)
    watch_id = daemon.add_watch(spec)

    # ... later ...
    daemon.remove_watch(watch_id)
    daemon.stop()

Thread-safety:
`add_watch`/`remove_watch`/`list_watches` acquire an internal RLock.
Callbacks fire in the watchdog observer thread; they must be fast and
non-blocking. Any exception in a callback is logged and, when the optional
CircuitBreakerShm integration is enabled, recorded as a failure.

Environment variables:
THGENT_WATCHER_USE_SHM=0 Disable the optional CircuitBreakerShm health
integration even if state_shm is available.

FR-trace: BKM-09 (PYTHON_FRONTMATTER_NATIVE_BACKMATTER_AUDIT_PLAN.md)

---

## WatchEvent

Structured file-system event delivered to watch callbacks.

---

## WatchSpec

Configuration for a single watch registered with :class:`WatcherDaemon`.

---

## WatcherDaemon

Multi-tenant file watcher daemon backed by a single watchdog Observer.

One `WatcherDaemon` instance manages N independent :class:`WatchSpec`
objects. Each spec is scheduled on the shared Observer using a dedicated

### Methods

#### WatcherDaemon.**init**

```python
__init__(self: Any)
```

---

#### WatcherDaemon.add_watch

```python
add_watch(self: Any, spec: WatchSpec)
```

Register a new :class:`WatchSpec` and return its watch ID.

If the daemon is not yet started, the watch is registered but events
will not fire until :meth:`start` is called.

**Parameters**:

- `spec`: The watch configuration.

**Returns**: A unique string watch ID used for :meth:`remove_watch`.

---

#### WatcherDaemon.is_running

```python
is_running(self: Any)
```

Return `True` if the Observer thread is active.

---

#### WatcherDaemon.list_watches

```python
list_watches(self: Any)
```

Return a snapshot of currently registered watches.

**Returns**: List of dicts with keys `watch_id`, `root`, `patterns`,
`recursive`.

---

#### WatcherDaemon.remove_watch

```python
remove_watch(self: Any, watch_id: str)
```

Remove a previously registered watch by ID.

**Parameters**:

- `watch_id`: The ID returned by :meth:`add_watch`.

**Returns**: `True` if the watch was found and removed; `False` otherwise.

---

#### WatcherDaemon.start

```python
start(self: Any)
```

Start the underlying watchdog Observer thread.

Idempotent: calling `start()` on an already-running daemon is a
no-op.

---

#### WatcherDaemon.stop

```python
stop(self: Any)
```

Stop the watchdog Observer and wait for it to terminate.

Idempotent: safe to call multiple times. All registered watches are
removed before stopping.

---

---

## \_SpecHandler

watchdog event handler for one WatchSpec.

Converts raw watchdog events to :class:`WatchEvent` and dispatches them to
the registered callback. Callback exceptions are caught, logged, and
forwarded to the optional health breaker.

**Inherits from**: `PatternMatchingEventHandler`

### Methods

#### \_SpecHandler.**init**

```python
__init__(self: Any, watch_id: str, spec: WatchSpec, breaker: Any)
```

---

#### \_SpecHandler.on_created

```python
on_created(self: Any, event: Any)
```

---

#### \_SpecHandler.on_deleted

```python
on_deleted(self: Any, event: Any)
```

---

#### \_SpecHandler.on_modified

```python
on_modified(self: Any, event: Any)
```

---

#### \_SpecHandler.on_moved

```python
on_moved(self: Any, event: Any)
```

---

---

## add_watch

```python
add_watch(self: Any, spec: WatchSpec)
```

Register a new :class:`WatchSpec` and return its watch ID.

If the daemon is not yet started, the watch is registered but events
will not fire until :meth:`start` is called.

**Parameters**:

- `spec`: The watch configuration.

**Returns**: A unique string watch ID used for :meth:`remove_watch`.

---

## get_watcher_daemon

Return the process-level singleton :class:`WatcherDaemon`.

The singleton is created lazily on first call. Callers must still invoke

---

## is_running

```python
is_running(self: Any)
```

Return `True` if the Observer thread is active.

---

## list_watches

```python
list_watches(self: Any)
```

Return a snapshot of currently registered watches.

**Returns**: List of dicts with keys `watch_id`, `root`, `patterns`,
`recursive`.

---

## on_created

```python
on_created(self: Any, event: Any) -> None
```

---

## on_deleted

```python
on_deleted(self: Any, event: Any) -> None
```

---

## on_modified

```python
on_modified(self: Any, event: Any) -> None
```

---

## on_moved

```python
on_moved(self: Any, event: Any) -> None
```

---

## remove_watch

```python
remove_watch(self: Any, watch_id: str)
```

Remove a previously registered watch by ID.

**Parameters**:

- `watch_id`: The ID returned by :meth:`add_watch`.

**Returns**: `True` if the watch was found and removed; `False` otherwise.

---

## start

```python
start(self: Any)
```

Start the underlying watchdog Observer thread.

Idempotent: calling `start()` on an already-running daemon is a
no-op.

**Raises**:

- `RuntimeError`: If the Observer fails to start.

---

## stop

```python
stop(self: Any)
```

Stop the watchdog Observer and wait for it to terminate.

Idempotent: safe to call multiple times. All registered watches are
removed before stopping.

---
