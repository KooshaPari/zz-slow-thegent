# sub_user_provider API Reference

> **Source**: `src/thegent/isolation/sub_user_provider.py`

Sub-user isolation provider implementation.

---

## SubUserIsolationProvider

Isolation provider using sub-user UIDs and temporary home directories.

**Inherits from**: `IsolationProvider`

### Methods

#### SubUserIsolationProvider.**init**

```python
__init__(self: Any, base_home_dir: str, base_uid: int, uid_pool_size: int)
```

Initialize SubUserIsolationProvider.

**Parameters**:

- `base_home_dir`: Base directory for tenant home directories
- `base_uid`: Starting UID for tenant allocation
- `uid_pool_size`: Maximum number of tenants (pool size)

---

#### SubUserIsolationProvider.allocate_tenant

```python
allocate_tenant(self: Any, tenant_id: str, agent_id: Any)
```

Allocate resources for a tenant.

Uses hash-based UID allocation to ensure idempotency.

---

#### SubUserIsolationProvider.cleanup_tenant

```python
cleanup_tenant(self: Any, context: TenantContext)
```

Clean up resources allocated for a tenant.

Removes the tenant's home directory and evicts from cache.

---

#### SubUserIsolationProvider.execute_in_context

```python
execute_in_context(self: Any, context: TenantContext, command: list, timeout_sec: int)
```

Execute a command in the tenant's isolated context.

Environment variables and working directory are set from context.

---

---

## allocate_tenant

```python
allocate_tenant(self: Any, tenant_id: str, agent_id: Any)
```

Allocate resources for a tenant.

Uses hash-based UID allocation to ensure idempotency.

---

## cleanup_tenant

```python
cleanup_tenant(self: Any, context: TenantContext)
```

Clean up resources allocated for a tenant.

Removes the tenant's home directory and evicts from cache.

---

## execute_in_context

```python
execute_in_context(self: Any, context: TenantContext, command: list, timeout_sec: int)
```

Execute a command in the tenant's isolated context.

Environment variables and working directory are set from context.

---
