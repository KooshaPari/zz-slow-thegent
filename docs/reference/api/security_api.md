# security API Reference

> **Source**: `src/thegent/cross_platform/security.py`

Security hardening & compliance.

---

## CrossPlatformSecurity

Cross-platform security hardening and compliance.

### Methods

#### CrossPlatformSecurity.**init**

```python
__init__(self: Any)
```

Initialize security.

---

#### CrossPlatformSecurity.harden

```python
harden(self: Any, target: str)
```

Harden system or application.

**Parameters**:

- `target`: Target for hardening

**Returns**: True if successful

---

#### CrossPlatformSecurity.run_security_check

```python
run_security_check(self: Any, check_name: str)
```

Run system security check.

**Parameters**:

- `check_name`: Name of the check to run

**Returns**: Security check results

---

---

## harden

```python
harden(self: Any, target: str)
```

Harden system or application.

**Parameters**:

- `target`: Target for hardening

**Returns**: True if successful

---

## run_security_check

```python
run_security_check(self: Any, check_name: str)
```

Run system security check.

**Parameters**:

- `check_name`: Name of the check to run

**Returns**: Security check results

---
