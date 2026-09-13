# governance_dlq API Reference

> **Source**: `src/thegent/research/governance_dlq.py`

Governance escalation queue with DLQ integration.

---

## EscalationQueueDLQ

Escalation queue with dead letter queue integration.

### Methods

#### EscalationQueueDLQ.**init**

```python
__init__(self: Any)
```

Initialize escalation queue.

---

#### EscalationQueueDLQ.enqueue

```python
enqueue(self: Any, item: dict[(str, Any)])
```

Add item to escalation queue.

**Parameters**:

- `item`: Item to enqueue

---

#### EscalationQueueDLQ.move_to_dlq

```python
move_to_dlq(self: Any, item: dict[(str, Any)], reason: str)
```

Move item to dead letter queue.

**Parameters**:

- `item`: Item to move
- `reason`: Reason for moving to DLQ

---

#### EscalationQueueDLQ.process

```python
process(self: Any)
```

Process next item from queue.

**Returns**: Processed item or None

---

---

## enqueue

```python
enqueue(self: Any, item: dict[(str, Any)])
```

Add item to escalation queue.

**Parameters**:

- `item`: Item to enqueue

---

## move_to_dlq

```python
move_to_dlq(self: Any, item: dict[(str, Any)], reason: str)
```

Move item to dead letter queue.

**Parameters**:

- `item`: Item to move
- `reason`: Reason for moving to DLQ

---

## process

```python
process(self: Any)
```

Process next item from queue.

**Returns**: Processed item or None

---
