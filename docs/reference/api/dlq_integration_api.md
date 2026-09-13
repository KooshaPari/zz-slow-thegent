# dlq_integration API Reference

> **Source**: `src/thegent/governance/dlq_integration.py`

Escalation queue DLQ integration.

---

## GovernanceDLQIntegration

Integration between governance escalation queue and DLQ.

### Methods

#### GovernanceDLQIntegration.**init**

```python
__init__(self: Any)
```

Initialize DLQ integration.

---

#### GovernanceDLQIntegration.process_with_dlq

```python
process_with_dlq(self: Any, max_retries: int)
```

Process escalation queue with DLQ fallback.

**Parameters**:

- `max_retries`: Maximum retry attempts

---

---

## process_with_dlq

```python
process_with_dlq(self: Any, max_retries: int)
```

Process escalation queue with DLQ fallback.

**Parameters**:

- `max_retries`: Maximum retry attempts

---
