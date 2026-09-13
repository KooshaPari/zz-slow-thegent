# leasing API Reference

> **Source**: `src/thegent/orchestration/leasing.py`

## EditLease

### Methods

#### EditLease.is_expired

```python
is_expired(self: Any)
```

---

---

## EditLeaseManager

MTSP-11: Centralized edit lease management for multi-tenant agent environments.

Prevents agent-on-agent edit collisions by providing advisory locks with TTL.

### Methods

#### EditLeaseManager.**init**

```python
__init__(self: Any, state_dir: Path)
```

---

#### EditLeaseManager.acquire

```python
acquire(self: Any, path: str, agent_id: str, duration: float, force: bool)
```

Acquire an advisory lease on a file path.

---

#### EditLeaseManager.check

```python
check(self: Any, path: str, agent_id: Any)
```

Check if a path is currently leased by another agent.

---

#### EditLeaseManager.prune

```python
prune(self: Any)
```

Remove all expired leases.

---

#### EditLeaseManager.release

```python
release(self: Any, path: str, agent_id: str)
```

Release a lease if held by the agent.

---

---

## acquire

```python
acquire(self: Any, path: str, agent_id: str, duration: float, force: bool)
```

Acquire an advisory lease on a file path.

---

## check

```python
check(self: Any, path: str, agent_id: Any)
```

Check if a path is currently leased by another agent.

---

## get_lease_manager

```python
get_lease_manager(state_dir: Path)
```

Return shared in-memory EditLeaseManager. MTSP-14: zero-latency lock coordination.

---

## is_expired

```python
is_expired(self: Any) -> bool
```

---

## prune

```python
prune(self: Any)
```

Remove all expired leases.

---

## release

```python
release(self: Any, path: str, agent_id: str)
```

Release a lease if held by the agent.

---
