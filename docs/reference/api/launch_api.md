# launch API Reference

> **Source**: `src/thegent/ux/launch.py`

WP-6007: Post-launch observation and rollback reserve.

---

## LaunchObserver

Observes system health post-launch and manages rollback triggers.

### Methods

#### LaunchObserver.**init**

```python
__init__(self: Any, settings: ThegentSettings)
```

---

#### LaunchObserver.check_health

```python
check_health(self: Any)
```

Check post-launch health metrics.

---

#### LaunchObserver.trigger_rollback

```python
trigger_rollback(self: Any, reason: str)
```

Trigger an emergency rollback to the last stable state.

---

---

## check_health

```python
check_health(self: Any)
```

Check post-launch health metrics.

---

## trigger_rollback

```python
trigger_rollback(self: Any, reason: str)
```

Trigger an emergency rollback to the last stable state.

---
