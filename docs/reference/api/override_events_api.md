# override_events API Reference

> **Source**: `src/thegent/governance/override_events.py`

Governance override expiry event emission (WP-3003, research-governance-override-events).

Provides structured JSONL event emission when governance overrides expire,
enabling audit trails and downstream reactions.

---

## OverrideActivatedEvent

Structured event emitted when a governance override is activated.

### Methods

#### OverrideActivatedEvent.to_dict

```python
to_dict(self: Any)
```

Serialize to a plain dictionary.

---

---

## OverrideEventEmitter

Writes governance override lifecycle events to a JSONL audit log.

### Methods

#### OverrideEventEmitter.**init**

```python
__init__(self: Any, events_path: Any)
```

---

#### OverrideEventEmitter.emit_activated

```python
emit_activated(self: Any, override_id: str, policy_id: str, owner: str, ttl_s: float)
```

Append an override-activated event to the JSONL log.

**Parameters**:

- `override_id`: Unique identifier for this override.
- `policy_id`: The governance policy being overridden.
- `owner`: The principal who applied the override.
- `ttl_s`: Time-to-live in seconds.

---

#### OverrideEventEmitter.emit_expired

```python
emit_expired(self: Any, event: OverrideExpiredEvent)
```

Append an override-expired event to the JSONL log.

**Parameters**:

- `event`: The structured expiry event to persist.

---

#### OverrideEventEmitter.tail_events

```python
tail_events(self: Any, n: int)
```

Read the last _n_ events from the JSONL log.

**Parameters**:

- `n`: Maximum number of events to return (most-recent last).

**Returns**: List of event dicts, up to _n_ entries.

---

---

## OverrideExpiredEvent

Structured event emitted when a governance override expires.

### Methods

#### OverrideExpiredEvent.to_dict

```python
to_dict(self: Any)
```

Serialize to a plain dictionary.

---

---

## OverrideExpiryMonitor

Background thread that fires callbacks when registered overrides expire.

Usage::

    emitter = OverrideEventEmitter()
    monitor = OverrideExpiryMonitor(emitter=emitter)
    monitor.start()

    monitor.register("ovr-001", time.time() + 10, lambda: print("expired!"))
    ...
    monitor.stop()

### Methods

#### OverrideExpiryMonitor.**init**

```python
__init__(self: Any, emitter: Any, poll_interval_s: float)
```

---

#### OverrideExpiryMonitor.register

```python
register(self: Any, override_id: str, expires_at: float, on_expire: Callable[(Any, None)], policy_id: str, owner: str)
```

Register an override for expiry monitoring.

**Parameters**:

- `override_id`: Unique identifier for the override.
- `expires_at`: Unix timestamp when the override expires.
- `on_expire`: Zero-arg callback invoked on expiry.
- `policy_id`: Policy the override applies to (for event metadata).
- `owner`: Who applied the override (for event metadata).

---

#### OverrideExpiryMonitor.start

```python
start(self: Any)
```

Start the background polling thread.

---

#### OverrideExpiryMonitor.stop

```python
stop(self: Any, timeout_s: float)
```

Signal the background thread to stop and wait for it.

**Parameters**:

- `timeout_s`: Maximum seconds to wait for clean stop.

---

#### OverrideExpiryMonitor.unregister

```python
unregister(self: Any, override_id: str)
```

Remove an override from monitoring (e.g. if manually revoked).

**Parameters**:

- `override_id`: The override to remove.

---

---

## \_Registration

---

## emit_activated

```python
emit_activated(self: Any, override_id: str, policy_id: str, owner: str, ttl_s: float)
```

Append an override-activated event to the JSONL log.

**Parameters**:

- `override_id`: Unique identifier for this override.
- `policy_id`: The governance policy being overridden.
- `owner`: The principal who applied the override.
- `ttl_s`: Time-to-live in seconds.

---

## emit_expired

```python
emit_expired(self: Any, event: OverrideExpiredEvent)
```

Append an override-expired event to the JSONL log.

**Parameters**:

- `event`: The structured expiry event to persist.

---

## register

```python
register(self: Any, override_id: str, expires_at: float, on_expire: Callable[(Any, None)], policy_id: str, owner: str)
```

Register an override for expiry monitoring.

**Parameters**:

- `override_id`: Unique identifier for the override.
- `expires_at`: Unix timestamp when the override expires.
- `on_expire`: Zero-arg callback invoked on expiry.
- `policy_id`: Policy the override applies to (for event metadata).
- `owner`: Who applied the override (for event metadata).

---

## start

```python
start(self: Any)
```

Start the background polling thread.

---

## stop

```python
stop(self: Any, timeout_s: float)
```

Signal the background thread to stop and wait for it.

**Parameters**:

- `timeout_s`: Maximum seconds to wait for clean stop.

---

## tail_events

```python
tail_events(self: Any, n: int)
```

Read the last _n_ events from the JSONL log.

**Parameters**:

- `n`: Maximum number of events to return (most-recent last).

**Returns**: List of event dicts, up to _n_ entries.

---

## to_dict

```python
to_dict(self: Any)
```

Serialize to a plain dictionary.

---

## unregister

```python
unregister(self: Any, override_id: str)
```

Remove an override from monitoring (e.g. if manually revoked).

**Parameters**:

- `override_id`: The override to remove.

---
