# resource_limits API Reference

> **Source**: `src/thegent/infra/resource_limits.py`

Resource limits and enforcement.

---

## ResourceLimits

Manage and enforce resource limits.

### Methods

#### ResourceLimits.**init**

```python
__init__(self: Any)
```

Initialize resource limits manager.

---

#### ResourceLimits.get_fd_limit

```python
get_fd_limit(self: Any)
```

Get current FD limit.

**Returns**: Current file descriptor limit.

---

#### ResourceLimits.get_process_limit

```python
get_process_limit(self: Any)
```

Get current process limit.

**Returns**: Current process limit, or default if not available.

---

#### ResourceLimits.restore_limits

```python
restore_limits(self: Any)
```

Restore original limits.

---

---

## get_fd_limit

```python
get_fd_limit(self: Any)
```

Get current FD limit.

**Returns**: Current file descriptor limit.

---

## get_process_limit

```python
get_process_limit(self: Any)
```

Get current process limit.

**Returns**: Current process limit, or default if not available.

---

## get_resource_limits

Get global resource limits manager.

---

## restore_limits

```python
restore_limits(self: Any)
```

Restore original limits.

---
