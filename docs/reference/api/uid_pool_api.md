# uid_pool API Reference

> **Source**: `src/thegent/isolation/uid_pool.py`

UID pool management for tenant isolation.

---

## UidPool

Manages a pool of UIDs for tenant isolation.

Supports persistence to prevent UID reuse across restarts
and ensures deterministic allocation for the same tenant.

### Methods

#### UidPool.**init**

```python
__init__(self: Any, base_uid: int, size: int, state_file: Any)
```

---

#### UidPool.allocate

```python
allocate(self: Any, tenant_id: str)
```

Allocate a UID for a tenant.

Returns existing UID if already allocated, otherwise picks next available.

---

#### UidPool.get_tenant_id

```python
get_tenant_id(self: Any, uid: int)
```

Get the tenant_id for a UID if it exists.

---

#### UidPool.get_uid

```python
get_uid(self: Any, tenant_id: str)
```

Get the UID for a tenant if it exists.

---

#### UidPool.release

```python
release(self: Any, tenant_id: str)
```

Release a UID back to the pool.

---

---

## allocate

```python
allocate(self: Any, tenant_id: str)
```

Allocate a UID for a tenant.

Returns existing UID if already allocated, otherwise picks next available.

---

## get_tenant_id

```python
get_tenant_id(self: Any, uid: int)
```

Get the tenant_id for a UID if it exists.

---

## get_uid

```python
get_uid(self: Any, tenant_id: str)
```

Get the UID for a tenant if it exists.

---

## release

```python
release(self: Any, tenant_id: str)
```

Release a UID back to the pool.

---
