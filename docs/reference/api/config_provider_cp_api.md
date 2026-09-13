# config_provider_cp API Reference

> **Source**: `src/thegent/governance/config_provider_cp.py`

WP-10002: ControlPlaneConfigProvider implementation for Control Plane Phase 2.

---

## ControlPlaneConfigProvider

Connects to the long-running control-plane service for configuration.

Applies full resolution order (request -> session -> tenant -> stamp -> global)
server-side to ensure multi-tenant isolation.

### Methods

#### ControlPlaneConfigProvider.**init**

```python
__init__(self: Any, url: str, timeout: float)
```

---

#### ControlPlaneConfigProvider.get_tenant_config

```python
get_tenant_config(self: Any, tenant_id: str)
```

Fetch raw tenant config via CP API.

---

#### ControlPlaneConfigProvider.resolve

```python
resolve(self: Any, tenant_id: Any, session_id: Any, request_overrides: Any, keys: Any)
```

Resolve config via Control Plane API.

---

---

## get_tenant_config

```python
get_tenant_config(self: Any, tenant_id: str)
```

Fetch raw tenant config via CP API.

---

## resolve

```python
resolve(self: Any, tenant_id: Any, session_id: Any, request_overrides: Any, keys: Any)
```

Resolve config via Control Plane API.

---
