# fast_file_watcher API Reference

> **Source**: `src/thegent/infra/fast_file_watcher.py`

Fast file watcher with optimized backends.

This module provides a high-performance abstraction layer for file watching
that automatically selects the fastest available backend:

- watchfiles (Rust-based): 5-10x faster than watchdog
- watchdog: Cross-platform fallback

Performance improvements:

- watchfiles uses Rust implementation (5-10x faster)
- Better performance for high-frequency file changes
- Automatic backend selection based on availability

---

## FastFileWatcher

High-performance file watcher with automatic backend selection.

Backend priority (fastest first):

1. watchfiles (if installed) - 5-10x faster, Rust-based
2. watchdog (cross-platform fallback) - baseline performance

### Methods

#### FastFileWatcher.**init**

```python
__init__(self: Any, path: Any, recursive: bool)
```

Initialize file watcher.

**Parameters**:

- `path`: Directory or file to watch
- `recursive`: Whether to watch recursively

---

#### FastFileWatcher.backend

```python
backend(self: Any)
```

Get current backend name.

---

#### FastFileWatcher.start

```python
start(self: Any, event_handler: Any)
```

Start watching (watchdog backend).

**Parameters**:

- `event_handler`: Optional custom event handler

---

#### FastFileWatcher.stop

```python
stop(self: Any)
```

Stop watching.

---

#### FastFileWatcher.watch

```python
watch(self: Any, callback: Callable[(Any, None)])
```

Watch for file changes using watchfiles backend.

**Parameters**:

- `callback`: Function to call on changes
- `**kwargs`: Additional options for watchfiles

---

---

## SimpleHandler

**Inherits from**: `FileSystemEventHandler`

### Methods

#### SimpleHandler.on_any_event

```python
on_any_event(self: Any, event: FileSystemEvent)
```

---

---

## backend

```python
backend(self: Any)
```

Get current backend name.

---

## on_any_event

```python
on_any_event(self: Any, event: FileSystemEvent) -> None
```

---

## start

```python
start(self: Any, event_handler: Any)
```

Start watching (watchdog backend).

**Parameters**:

- `event_handler`: Optional custom event handler

---

## stop

```python
stop(self: Any)
```

Stop watching.

---

## watch

```python
watch(self: Any, callback: Callable[(Any, None)])
```

Watch for file changes using watchfiles backend.

**Parameters**:

- `callback`: Function to call on changes
- `**kwargs`: Additional options for watchfiles

---

## watch_files

```python
watch_files(path: Any, callback: Callable[(Any, None)], recursive: bool)
```

Watch files using fastest available backend (watchfiles preferred).

**Parameters**:

- `path`: Directory or file to watch
- `callback`: Function to call on changes
- `recursive`: Whether to watch recursively
- `**kwargs`: Additional options

---
