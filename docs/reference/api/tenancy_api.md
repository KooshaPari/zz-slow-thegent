# tenancy API Reference

> **Source**: `src/thegent/security/tenancy.py`

WP-19001: Multi-Tenant Key Isolation.

Ensures API keys are isolated by owner/tenant in the auth directory.

---

## KeyIsolator

Manages isolated key storage for multi-tenant environments.

### Methods

#### KeyIsolator.**init**

```python
__init__(self: Any, settings: Any)
```

---

#### KeyIsolator.delete_tenant

```python
delete_tenant(self: Any, owner: str)
```

Delete all keys for a specific tenant.

---

#### KeyIsolator.get_key

```python
get_key(self: Any, owner: str, provider: str)
```

Retrieve a key for a specific owner and provider.

---

#### KeyIsolator.get_tenant_dir

```python
get_tenant_dir(self: Any, owner: str)
```

Get the isolated auth directory for a specific owner.

---

#### KeyIsolator.isolate_key

```python
isolate_key(self: Any, owner: str, provider: str, api_key: str)
```

Write an API key to the isolated tenant directory.

---

#### KeyIsolator.list_tenants

```python
list_tenants(self: Any)
```

List all tenants with isolated keys.

---

---

## delete_tenant

```python
delete_tenant(self: Any, owner: str)
```

Delete all keys for a specific tenant.

---

## get_key

```python
get_key(self: Any, owner: str, provider: str)
```

Retrieve a key for a specific owner and provider.

---

## get_tenant_dir

```python
get_tenant_dir(self: Any, owner: str)
```

Get the isolated auth directory for a specific owner.

---

## isolate_key

```python
isolate_key(self: Any, owner: str, provider: str, api_key: str)
```

Write an API key to the isolated tenant directory.

---

## list_tenants

```python
list_tenants(self: Any)
```

List all tenants with isolated keys.

---
