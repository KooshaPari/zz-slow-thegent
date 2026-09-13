# queue_tui API Reference

> **Source**: `src/thegent/ux/queue_tui.py`

WP-7002: Queue TUI for managing deferred prompts.

---

## QueueTUI

Rich-based TUI for the prompt queue.

### Methods

#### QueueTUI.**init**

```python
__init__(self: Any, session_dir: Path)
```

---

#### QueueTUI.render_table

```python
render_table(self: Any)
```

Render the queue as a Rich Table.

---

#### QueueTUI.show

```python
show(self: Any)
```

Show the queue once.

---

#### QueueTUI.watch

```python
watch(self: Any, interval: float)
```

Watch the queue live.

---

---

## render_table

```python
render_table(self: Any)
```

Render the queue as a Rich Table.

---

## show

```python
show(self: Any)
```

Show the queue once.

---

## watch

```python
watch(self: Any, interval: float)
```

Watch the queue live.

---
