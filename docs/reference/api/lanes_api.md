# lanes API Reference

> **Source**: `src/thegent/orchestration/lanes.py`

Priority and urgency lane model (WP-1002, FR-019).

Defines execution lanes with priority ordering and critical lane protection.
Critical lane bypasses overload rejection and gets reserved capacity under burst.

---

## Lane

Canonical execution lanes (WP-1002).

**Inherits from**: `StrEnum`

---

## LaneModel

Priority and urgency lane model for task management (WP-1002, FR-019).

Usage:
model = LaneModel()
model.get_priority("critical") # 0 (highest)
model.is_protected("critical") # True - bypasses overload rejection
model.reserved_slots_for_critical # 2

### Methods

#### LaneModel.check_capacity

```python
check_capacity(cls: Any, lane: str, active_count: int, total_capacity: int)
```

Check if lane has capacity (starvation prevention, FR-019).

Critical lane always has capacity. Non-critical lanes leave reserved
slots for critical to prevent starvation under burst.

---

#### LaneModel.get_priority

```python
get_priority(cls: Any, lane: str)
```

Return numeric priority for a lane (lower = higher priority).

---

#### LaneModel.get_urgency

```python
get_urgency(cls: Any, lane: str)
```

Return urgency tier for a lane.

---

#### LaneModel.is_protected

```python
is_protected(cls: Any, lane: str)
```

True if lane bypasses overload rejection (FR-019 critical lane protection).

---

#### LaneModel.sort_tasks

```python
sort_tasks(cls: Any, tasks: list[dict[(str, Any)]])
```

Sort tasks by lane priority (asc) then by creation time (asc).

---

---

## check_capacity

```python
check_capacity(cls: Any, lane: str, active_count: int, total_capacity: int)
```

Check if lane has capacity (starvation prevention, FR-019).

Critical lane always has capacity. Non-critical lanes leave reserved
slots for critical to prevent starvation under burst.

---

## get_priority

```python
get_priority(cls: Any, lane: str)
```

Return numeric priority for a lane (lower = higher priority).

---

## get_urgency

```python
get_urgency(cls: Any, lane: str)
```

Return urgency tier for a lane.

---

## is_protected

```python
is_protected(cls: Any, lane: str)
```

True if lane bypasses overload rejection (FR-019 critical lane protection).

---

## sort_tasks

```python
sort_tasks(cls: Any, tasks: list[dict[(str, Any)]])
```

Sort tasks by lane priority (asc) then by creation time (asc).

---
