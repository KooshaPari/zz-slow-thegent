# escalation API Reference

> **Source**: `src/thegent/governance/escalation.py`

WP-3008: Escalation SLA and governance queue (FR-028).

---

## EscalationItem

An item in the escalation queue.

### Methods

#### EscalationItem.from_dict

```python
from_dict(cls: Any, data: dict[(str, Any)])
```

Create from dictionary.

---

#### EscalationItem.to_dict

```python
to_dict(self: Any)
```

Convert to dictionary for serialization.

---

---

## EscalationPriority

Priority of an escalation item.

**Inherits from**: `StrEnum`

---

## EscalationQueue

Manages the governance escalation queue.

### Methods

#### EscalationQueue.**init**

```python
__init__(self: Any, settings: Any)
```

---

#### EscalationQueue.add

```python
add(self: Any, run_id: str, reason: str, priority: int)
```

Simplified add for legacy/internal callers.

---

#### EscalationQueue.escalate

```python
escalate(self: Any, run_id: str, prompt: str, reason: str, agent: str, priority: EscalationPriority, sla_minutes: int, metadata: Any)
```

Add a new item to the escalation queue.

---

#### EscalationQueue.get_item

```python
get_item(self: Any, esc_id: str)
```

Retrieve a specific escalation item.

---

#### EscalationQueue.list_items

```python
list_items(self: Any, status: Any)
```

List items in the queue, optionally filtered by status.

---

#### EscalationQueue.resolve

```python
resolve(self: Any, esc_id: str, resolution: str, solver: str)
```

Mark an escalation item as resolved.

---

---

## EscalationStatus

Status of an escalation item.

**Inherits from**: `StrEnum`

---

## add

```python
add(self: Any, run_id: str, reason: str, priority: int)
```

Simplified add for legacy/internal callers.

---

## escalate

```python
escalate(self: Any, run_id: str, prompt: str, reason: str, agent: str, priority: EscalationPriority, sla_minutes: int, metadata: Any)
```

Add a new item to the escalation queue.

---

## from_dict

```python
from_dict(cls: Any, data: dict[(str, Any)])
```

Create from dictionary.

---

## get_item

```python
get_item(self: Any, esc_id: str)
```

Retrieve a specific escalation item.

---

## list_items

```python
list_items(self: Any, status: Any)
```

List items in the queue, optionally filtered by status.

---

## resolve

```python
resolve(self: Any, esc_id: str, resolution: str, solver: str)
```

Mark an escalation item as resolved.

---

## to_dict

```python
to_dict(self: Any)
```

Convert to dictionary for serialization.

---
