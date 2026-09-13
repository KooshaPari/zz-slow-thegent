# event_system API Reference

> **Source**: `src/thegent/events/event_system.py`

Event system for thegent.

---

## EventSystem

Event system for pub/sub.

### Methods

#### EventSystem.**init**

```python
__init__(self: Any)
```

Initialize event system.

---

#### EventSystem.emit

```python
emit(self: Any, event_type: str, data: Any)
```

Emit an event.

**Parameters**:

- `event_type`: Event type
- `data`: Event data

---

#### EventSystem.subscribe

```python
subscribe(self: Any, event_type: str, handler: Callable)
```

Subscribe to event type.

**Parameters**:

- `event_type`: Event type
- `handler`: Handler function

---

---

## emit

```python
emit(self: Any, event_type: str, data: Any)
```

Emit an event.

**Parameters**:

- `event_type`: Event type
- `data`: Event data

---

## subscribe

```python
subscribe(self: Any, event_type: str, handler: Callable)
```

Subscribe to event type.

**Parameters**:

- `event_type`: Event type
- `handler`: Handler function

---
