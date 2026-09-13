# deferral API Reference

> **Source**: `src/thegent/orchestration/deferral.py`

WP-5004: Non-critical deferral rules.

---

## DeferralManager

Manages deferral of non-critical tasks under high load.

### Methods

#### DeferralManager.**init**

```python
__init__(self: Any, settings: ThegentSettings)
```

---

#### DeferralManager.defer_task

```python
defer_task(self: Any, task_id: str, reason: str)
```

Record a task as deferred.

---

#### DeferralManager.list_deferred

```python
list_deferred(self: Any)
```

List all currently deferred tasks.

---

#### DeferralManager.should_defer

```python
should_defer(self: Any, task_priority: str, load_level: float)
```

Determine if a task should be deferred.

Priority: P0 (critical) to P3 (low).

---

---

## DeferralRule

Rule for deferring non-critical tasks.

### Methods

#### DeferralRule.**init**

```python
__init__(self: Any, id: str, condition: str, action: str)
```

---

---

## defer_task

```python
defer_task(self: Any, task_id: str, reason: str)
```

Record a task as deferred.

---

## list_deferred

```python
list_deferred(self: Any)
```

List all currently deferred tasks.

---

## should_defer

```python
should_defer(self: Any, task_priority: str, load_level: float)
```

Determine if a task should be deferred.

Priority: P0 (critical) to P3 (low).

---
