# fork_guard API Reference

> **Source**: `src/thegent/orchestration/fork_guard.py`

WP-21001: Fork Explosion Guard.

Prevents agent recursion depth and fan-out (parallel sub-tasks) from exceeding safe limits.

---

## ForkContext

Tracks fork state for a specific run and its children.

---

## ForkExplosionGuard

Monitors and limits the creation of sub-tasks to prevent cascading execution.

### Methods

#### ForkExplosionGuard.**init**

```python
__init__(self: Any)
```

---

#### ForkExplosionGuard.get_stats

```python
get_stats(self: Any, run_id: str)
```

Return stats for a specific run.

---

#### ForkExplosionGuard.register_run

```python
register_run(self: Any, run_id: str, parent_id: Any)
```

Register a new run, inheriting depth from parent.

---

---

## get_stats

```python
get_stats(self: Any, run_id: str)
```

Return stats for a specific run.

---

## register_run

```python
register_run(self: Any, run_id: str, parent_id: Any)
```

Register a new run, inheriting depth from parent.

---
