# distributed API Reference

> **Source**: `src/thegent/resources/distributed.py`

Distributed resource coordination backed by a file-locked JSON lease store.

Coordinates resource usage across multiple thegent nodes/processes using a
shared lease file at `~/.thegent/resource_leases.json`. A `filelock`
advisory lock prevents concurrent writers from corrupting state; if
`filelock` is not installed the module falls back to a simple read/write
approach that is safe for single-process use.

---

## DistributedResourceCoordinator

Coordinate resource usage across thegent nodes via a shared lease file.

Uses `filelock.FileLock` for mutual exclusion when available, otherwise
falls back to a simple read/write approach (safe for single-process use).

### Methods

#### DistributedResourceCoordinator.**init**

```python
__init__(self: Any, lease_file: Any, resource_limits: Any, lock_timeout: float)
```

---

#### DistributedResourceCoordinator.acquire

```python
acquire(self: Any, resource: str, amount: float, owner: str, ttl_s: float, total: Any)
```

Acquire a lease on _amount_ units of _resource_.

**Parameters**:

- `resource`: Name of the resource to lease.
- `amount`: Quantity to reserve.
- `owner`: Identifier for the entity claiming the lease.
- `ttl_s`: Time-to-live in seconds before the lease automatically expires.
- `total`: Override total capacity for this call. Falls back to
  `resource_limits` dict, then no limit (always succeeds).

**Returns**: A :class:`ResourceLease` on success, or `None` if insufficient
capacity is available.

---

#### DistributedResourceCoordinator.cleanup_expired

```python
cleanup_expired(self: Any)
```

Remove all expired leases from the store.

**Returns**: Number of leases removed.

---

#### DistributedResourceCoordinator.get_active_leases

```python
get_active_leases(self: Any, resource: Any)
```

Return non-expired leases, optionally filtered by resource name.

**Parameters**:

- `resource`: When given, only leases for this resource are returned.

**Returns**: List of active :class:`ResourceLease` instances sorted by
`expires_at` ascending.

---

#### DistributedResourceCoordinator.get_available

```python
get_available(self: Any, resource: str, total: float)
```

Return available capacity for _resource_ given a known _total_.

**Parameters**:

- `resource`: Name of the resource.
- `total`: Known total capacity for the resource.

**Returns**: `total` minus the sum of active (non-expired) lease amounts for
_resource_. Never returns a negative value.

---

#### DistributedResourceCoordinator.release

```python
release(self: Any, lease_id: str)
```

Release a lease by its identifier.

**Parameters**:

- `lease_id`: The `lease_id` of the :class:`ResourceLease` to remove.

**Returns**: `True` if the lease was found and removed, `False` otherwise.

---

---

## ResourceCoordinationError

Raised when the coordinator cannot perform a lease operation.

**Inherits from**: `Exception`

---

## ResourceLease

A time-bounded claim on a portion of a named resource.

### Methods

#### ResourceLease.from_dict

```python
from_dict(cls: Any, data: dict)
```

Deserialise from a plain dictionary.

---

#### ResourceLease.is_expired

```python
is_expired(self: Any)
```

Return True when the lease has passed its expiry time.

---

#### ResourceLease.to_dict

```python
to_dict(self: Any)
```

Serialise to a plain dictionary.

---

---

## acquire

```python
acquire(self: Any, resource: str, amount: float, owner: str, ttl_s: float, total: Any)
```

Acquire a lease on _amount_ units of _resource_.

**Parameters**:

- `resource`: Name of the resource to lease.
- `amount`: Quantity to reserve.
- `owner`: Identifier for the entity claiming the lease.
- `ttl_s`: Time-to-live in seconds before the lease automatically expires.
- `total`: Override total capacity for this call. Falls back to
  `resource_limits` dict, then no limit (always succeeds).

**Returns**: A :class:`ResourceLease` on success, or `None` if insufficient
capacity is available.

**Raises**:

- `ResourceCoordinationError`: If the lock cannot be acquired or
  storage I/O fails.

---

## cleanup_expired

```python
cleanup_expired(self: Any)
```

Remove all expired leases from the store.

**Returns**: Number of leases removed.

---

## from_dict

```python
from_dict(cls: Any, data: dict)
```

Deserialise from a plain dictionary.

---

## get_active_leases

```python
get_active_leases(self: Any, resource: Any)
```

Return non-expired leases, optionally filtered by resource name.

**Parameters**:

- `resource`: When given, only leases for this resource are returned.

**Returns**: List of active :class:`ResourceLease` instances sorted by
`expires_at` ascending.

---

## get_available

```python
get_available(self: Any, resource: str, total: float)
```

Return available capacity for _resource_ given a known _total_.

**Parameters**:

- `resource`: Name of the resource.
- `total`: Known total capacity for the resource.

**Returns**: `total` minus the sum of active (non-expired) lease amounts for
_resource_. Never returns a negative value.

---

## is_expired

```python
is_expired(self: Any)
```

Return True when the lease has passed its expiry time.

---

## release

```python
release(self: Any, lease_id: str)
```

Release a lease by its identifier.

**Parameters**:

- `lease_id`: The `lease_id` of the :class:`ResourceLease` to remove.

**Returns**: `True` if the lease was found and removed, `False` otherwise.

---

## to_dict

```python
to_dict(self: Any)
```

Serialise to a plain dictionary.

---
