# os_user_manager API Reference

> **Source**: `src/thegent/infra/os_user_manager.py`

OS User Management for Layer 1 Isolation.

Handles creation, deletion, and management of real system accounts
across macOS, Linux, and Windows.

---

## OSUser

---

## OSUserManager

Manages real OS-level user accounts for L1 identity.

Requires administrative privileges for most operations.

### Methods

#### OSUserManager.**init**

```python
__init__(self: Any, prefix: str)
```

---

#### OSUserManager.create_user

```python
create_user(self: Any, name: str, home_base: Any)
```

Create a new system user if it doesn't exist.

---

#### OSUserManager.delete_user

```python
delete_user(self: Any, username: str, delete_home: bool)
```

Remove a system user.

---

---

## create_user

```python
create_user(self: Any, name: str, home_base: Any)
```

Create a new system user if it doesn't exist.

---

## delete_user

```python
delete_user(self: Any, username: str, delete_home: bool)
```

Remove a system user.

---
