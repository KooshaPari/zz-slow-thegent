# value_lock API Reference

> **Source**: `src/thegent/governance/value_lock.py`

WP-29001: Value-Lock (Immutable Ethical Constraints).

Provides a mechanism to lock core agent values and ethical constraints.
Ensures that even if self-evolution occurs, fundamental alignment principles cannot be removed.

---

## LockedPrinciple

An ethically-locked principle that cannot be modified by autonomous loops.

**Inherits from**: `BaseModel`

---

## ValueLock

Manages immutable ethical constraints for thegent.

### Methods

#### ValueLock.**init**

```python
__init__(self: Any, lock_path: Path)
```

---

#### ValueLock.lock_principle

```python
lock_principle(self: Any, principle_id: str, description: str)
```

Ethically lock a principle, preventing future modification.

---

#### ValueLock.validate_change

```python
validate_change(self: Any, principle_id: str, new_description: str)
```

Validate if a proposed change violates a Value-Lock.

---

---

## lock_principle

```python
lock_principle(self: Any, principle_id: str, description: str)
```

Ethically lock a principle, preventing future modification.

---

## validate_change

```python
validate_change(self: Any, principle_id: str, new_description: str)
```

Validate if a proposed change violates a Value-Lock.

---
