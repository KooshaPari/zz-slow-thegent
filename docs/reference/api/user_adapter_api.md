# user_adapter API Reference

> **Source**: `src/thegent/os/user_adapter.py`

OS-level user creation adapter (Linux/macOS/Win).

---

## OSUserAdapter

Cross-platform OS user creation adapter.

### Methods

#### OSUserAdapter.**init**

```python
__init__(self: Any)
```

Initialize OS user adapter.

---

#### OSUserAdapter.create_user

```python
create_user(self: Any, username: str, home_dir: Any)
```

Create OS user.

**Parameters**:

- `username`: Username
- `home_dir`: Optional home directory

**Returns**: Creation result

---

---

## create_user

```python
create_user(self: Any, username: str, home_dir: Any)
```

Create OS user.

**Parameters**:

- `username`: Username
- `home_dir`: Optional home directory

**Returns**: Creation result

---
