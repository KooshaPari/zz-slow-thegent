# override_expired API Reference

> **Source**: `src/thegent/governance/override_expired.py`

Governance override expiration handling.

---

## OverrideExpirationHandler

Handle governance override expiration.

### Methods

#### OverrideExpirationHandler.**init**

```python
__init__(self: Any)
```

Initialize expiration handler.

---

#### OverrideExpirationHandler.check_expired

```python
check_expired(self: Any)
```

Check for expired overrides.

**Returns**: List of expired override dictionaries

---

#### OverrideExpirationHandler.emit_expired_event

```python
emit_expired_event(self: Any, override: dict[(str, Any)])
```

Emit expired override event.

**Parameters**:

- `override`: Expired override dictionary

---

#### OverrideExpirationHandler.register_override

```python
register_override(self: Any, override_id: str, expires_at: datetime, policy: str)
```

Register a governance override.

**Parameters**:

- `override_id`: Override identifier
- `expires_at`: Expiration timestamp
- `policy`: Policy being overridden

---

---

## check_expired

```python
check_expired(self: Any)
```

Check for expired overrides.

**Returns**: List of expired override dictionaries

---

## emit_expired_event

```python
emit_expired_event(self: Any, override: dict[(str, Any)])
```

Emit expired override event.

**Parameters**:

- `override`: Expired override dictionary

---

## register_override

```python
register_override(self: Any, override_id: str, expires_at: datetime, policy: str)
```

Register a governance override.

**Parameters**:

- `override_id`: Override identifier
- `expires_at`: Expiration timestamp
- `policy`: Policy being overridden

---
