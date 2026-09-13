# backlog API Reference

> **Source**: `src/thegent/governance/backlog.py`

Persistent backlog management for AgilePlus cycles.

Maintains a JSONL queue of known issues that could not be resolved in a single
cycle, enabling carry-over across cycles and audit trail of all findings.

---

## BacklogItem

A single backlog entry tracked across AgilePlus cycles.

**Inherits from**: `BaseModel`

---

## BacklogManager

Manages a persistent JSONL backlog of unresolved findings.

Items persist across AgilePlus cycles. Resolved items remain in the file
for audit trail but are excluded from get_pending() results.

### Methods

#### BacklogManager.**init**

```python
__init__(self: Any, session_dir: Path)
```

---

#### BacklogManager.add

```python
add(self: Any, finding_id: str, dimension: str, severity: float, description: str)
```

Add a finding to the backlog as a new pending item.

---

#### BacklogManager.backlog_path

```python
backlog_path(self: Any)
```

---

#### BacklogManager.defer

```python
defer(self: Any, item_id: str, reason: str)
```

Mark a backlog item as deferred with a reason.

---

#### BacklogManager.get_all

```python
get_all(self: Any)
```

Return all backlog items (including resolved/deferred) for audit trail.

---

#### BacklogManager.get_pending

```python
get_pending(self: Any)
```

Return pending items sorted by severity descending, then attempts ascending.

---

#### BacklogManager.increment_attempt

```python
increment_attempt(self: Any, item_id: str)
```

Increment the attempt counter and update the last_attempted_at timestamp.

---

#### BacklogManager.resolve

```python
resolve(self: Any, item_id: str)
```

Mark a backlog item as resolved.

---

#### BacklogManager.update_status

```python
update_status(self: Any, item_id: str, status: BacklogStatus, reason: Any)
```

Update the status of a backlog item.

---

---

## BacklogStatus

Lifecycle status for backlog items.

**Inherits from**: `StrEnum`

---

## add

```python
add(self: Any, finding_id: str, dimension: str, severity: float, description: str)
```

Add a finding to the backlog as a new pending item.

---

## backlog_path

```python
backlog_path(self: Any) -> Path
```

---

## defer

```python
defer(self: Any, item_id: str, reason: str)
```

Mark a backlog item as deferred with a reason.

---

## get_all

```python
get_all(self: Any)
```

Return all backlog items (including resolved/deferred) for audit trail.

---

## get_pending

```python
get_pending(self: Any)
```

Return pending items sorted by severity descending, then attempts ascending.

---

## increment_attempt

```python
increment_attempt(self: Any, item_id: str)
```

Increment the attempt counter and update the last_attempted_at timestamp.

---

## resolve

```python
resolve(self: Any, item_id: str)
```

Mark a backlog item as resolved.

---

## update_status

```python
update_status(self: Any, item_id: str, status: BacklogStatus, reason: Any)
```

Update the status of a backlog item.

---
