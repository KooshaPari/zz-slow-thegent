# overrides API Reference

> **Source**: `src/thegent/governance/overrides.py`

WP-3003: Override path with TTL and revalidation (FR-011).

---

## OverrideManager

Manages temporary policy overrides.

### Methods

#### OverrideManager.**init**

```python
__init__(self: Any, settings: Any)
```

---

#### OverrideManager.apply_override

```python
apply_override(self: Any, policy_id: str, reason: str, by: str, duration_minutes: int, metadata: Any)
```

Create a new temporary override.

---

#### OverrideManager.cleanup_expired

```python
cleanup_expired(self: Any)
```

Remove all expired overrides from disk.

---

#### OverrideManager.get_override

```python
get_override(self: Any, policy_id: str)
```

Get an active override for a policy.

---

---

## PolicyOverride

An active override for a governance policy.

### Methods

#### PolicyOverride.from_dict

```python
from_dict(cls: Any, data: dict[(str, Any)])
```

Create from dictionary.

---

#### PolicyOverride.is_active

```python
is_active(self: Any)
```

Check if the override is still valid.

---

#### PolicyOverride.to_dict

```python
to_dict(self: Any)
```

Convert to dictionary.

---

---

## apply_override

```python
apply_override(self: Any, policy_id: str, reason: str, by: str, duration_minutes: int, metadata: Any)
```

Create a new temporary override.

---

## cleanup_expired

```python
cleanup_expired(self: Any)
```

Remove all expired overrides from disk.

---

## from_dict

```python
from_dict(cls: Any, data: dict[(str, Any)])
```

Create from dictionary.

---

## get_override

```python
get_override(self: Any, policy_id: str)
```

Get an active override for a policy.

---

## is_active

```python
is_active(self: Any)
```

Check if the override is still valid.

---

## to_dict

```python
to_dict(self: Any)
```

Convert to dictionary.

---
