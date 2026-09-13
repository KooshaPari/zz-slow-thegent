# rbac API Reference

> **Source**: `src/thegent/security/rbac.py`

WP-19002: Role-Based Access Control (RBAC).

Formally defines roles, permissions, and access checks.

---

## Permission

Fine-grained permissions.

**Inherits from**: `StrEnum`

---

## RBACManager

Orchestrates RBAC checks across the system.

### Methods

#### RBACManager.**init**

```python
__init__(self: Any)
```

---

#### RBACManager.check_access

```python
check_access(self: Any, role: Role, operation: str, lane: str)
```

Hybrid check using both fine-grained permissions and persona-based constraints.

---

#### RBACManager.has_permission

```python
has_permission(self: Any, role: Role, permission: Permission)
```

Check if a role has a specific permission.

---

---

## Role

Standard operator roles.

**Inherits from**: `StrEnum`

---

## check_access

```python
check_access(self: Any, role: Role, operation: str, lane: str)
```

Hybrid check using both fine-grained permissions and persona-based constraints.

---

## has_permission

```python
has_permission(self: Any, role: Role, permission: Permission)
```

Check if a role has a specific permission.

---
