# isolation API Reference

> **Source**: `src/thegent/governance/isolation.py`

Tenant isolation and data leakage protection.

---

## AccessDenied

Exception raised when cross-tenant access is attempted.

**Inherits from**: `Exception`

---

## TenantIsolationProvider

Provides isolation between federated namespaces.

### Methods

#### TenantIsolationProvider.**init**

```python
__init__(self: Any)
```

---

#### TenantIsolationProvider.create_session

```python
create_session(self: Any, tenant_id: str, session_id: str)
```

Create a new isolated session.

---

#### TenantIsolationProvider.get_session_telemetry

```python
get_session_telemetry(self: Any, tenant_id: str, session_id: str)
```

Get telemetry for a session, enforcing isolation.

---

#### TenantIsolationProvider.record_telemetry

```python
record_telemetry(self: Any, tenant_id: str, session_id: str, data: dict[(str, Any)])
```

Record telemetry for a tenant's session.

---

---

## TenantSession

Represents an isolated agent session for a tenant.

### Methods

#### TenantSession.**init**

```python
__init__(self: Any, tenant_id: str, session_id: str, provider: TenantIsolationProvider)
```

---

#### TenantSession.emit_telemetry

```python
emit_telemetry(self: Any, data: dict[(str, Any)])
```

Emit telemetry for this session.

---

---

## create_session

```python
create_session(self: Any, tenant_id: str, session_id: str)
```

Create a new isolated session.

---

## emit_telemetry

```python
emit_telemetry(self: Any, data: dict[(str, Any)])
```

Emit telemetry for this session.

---

## get_session_telemetry

```python
get_session_telemetry(self: Any, tenant_id: str, session_id: str)
```

Get telemetry for a session, enforcing isolation.

---

## record_telemetry

```python
record_telemetry(self: Any, tenant_id: str, session_id: str, data: dict[(str, Any)])
```

Record telemetry for a tenant's session.

---
