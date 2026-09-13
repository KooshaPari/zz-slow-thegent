# watch_mode API Reference

> **Source**: `src/thegent/docgen/watch_mode.py`

Implement watch mode for auto-regeneration of documentation.

---

## DocumentationWatcher

Watch documentation source files and auto-regenerate.

### Methods

#### DocumentationWatcher.**init**

```python
__init__(self: Any, source_dir: Path, output_dir: Path, build_func: Callable)
```

---

#### DocumentationWatcher.start

```python
start(self: Any, poll_interval: float)
```

Start documentation watcher in a background thread.

---

#### DocumentationWatcher.stop

```python
stop(self: Any)
```

Stop documentation watcher.

---

---

## start

```python
start(self: Any, poll_interval: float)
```

Start documentation watcher in a background thread.

---

## stop

```python
stop(self: Any)
```

Stop documentation watcher.

---
