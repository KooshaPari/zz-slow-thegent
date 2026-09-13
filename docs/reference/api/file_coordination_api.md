# file_coordination API Reference

> **Source**: `src/thegent/coordination/file_coordination.py`

Phase 8: File Coordination implementation.

Includes OCC, HLC, and Lease registry.

---

## FileLeaseRegistry

Registry for file leases using flock-like semantics.

### Methods

#### FileLeaseRegistry.**init**

```python
__init__(self: Any, registry_dir: Path)
```

---

#### FileLeaseRegistry.claim_lease

```python
claim_lease(self: Any, path: Path, agent_id: str, mode: str, ttl: int)
```

Claim a lease on a file.

---

#### FileLeaseRegistry.release_lease

```python
release_lease(self: Any, path: Path, agent_id: str, token: str)
```

Release a file lease.

---

#### FileLeaseRegistry.renew_lease

```python
renew_lease(self: Any, path: Path, agent_id: str, token: str, ttl: int)
```

Renew an existing lease.

---

---

## HybridLogicalClock

Implementation of Hybrid Logical Clock (HLC).

### Methods

#### HybridLogicalClock.**init**

```python
__init__(self: Any)
```

---

#### HybridLogicalClock.now

```python
now(self: Any)
```

Generate next HLC timestamp.

---

---

## OCCManager

Optimistic Concurrency Control manager.

### Methods

#### OCCManager.**init**

```python
__init__(self: Any, version_db: Path)
```

---

#### OCCManager.get_version

```python
get_version(self: Any, path: Path)
```

Record current file version (SHA256 hash).

---

#### OCCManager.verify_and_commit

```python
verify_and_commit(self: Any, path: Path, base_version: str, new_content: bytes)
```

Verify version hasn't changed and commit new content.

---

---

## claim_lease

```python
claim_lease(self: Any, path: Path, agent_id: str, mode: str, ttl: int)
```

Claim a lease on a file.

---

## get_version

```python
get_version(self: Any, path: Path)
```

Record current file version (SHA256 hash).

---

## now

```python
now(self: Any)
```

Generate next HLC timestamp.

---

## release_lease

```python
release_lease(self: Any, path: Path, agent_id: str, token: str)
```

Release a file lease.

---

## renew_lease

```python
renew_lease(self: Any, path: Path, agent_id: str, token: str, ttl: int)
```

Renew an existing lease.

---

## verify_and_commit

```python
verify_and_commit(self: Any, path: Path, base_version: str, new_content: bytes)
```

Verify version hasn't changed and commit new content.

---
