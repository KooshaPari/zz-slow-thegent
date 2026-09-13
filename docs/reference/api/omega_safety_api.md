# omega_safety API Reference

> **Source**: `src/thegent/verification/omega_safety.py`

WP-45002: Universal Safety Invariants (Omega).

Enforces system-wide, non-negotiable safety properties across all agent actions.

---

## OmegaInvariantViolation

Details of a universal safety invariant violation.

**Inherits from**: `BaseModel`

---

## OmegaSafetyGuard

The final safety gate for thegent (Phase 45).

Enforces 'Omega' invariants which are universal and cannot be overridden.

### Methods

#### OmegaSafetyGuard.**init**

```python
__init__(self: Any)
```

---

#### OmegaSafetyGuard.is_safe

```python
is_safe(self: Any, action_id: str, action_data: dict[(str, Any)])
```

Convenience method to check if an action is safe according to Omega invariants.

---

#### OmegaSafetyGuard.verify_action

```python
verify_action(self: Any, action_id: str, action_data: dict[(str, Any)])
```

Verify an action against all universal Omega invariants.

---

---

## is_safe

```python
is_safe(self: Any, action_id: str, action_data: dict[(str, Any)])
```

Convenience method to check if an action is safe according to Omega invariants.

---

## verify_action

```python
verify_action(self: Any, action_id: str, action_data: dict[(str, Any)])
```

Verify an action against all universal Omega invariants.

---
