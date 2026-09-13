# capability_registry API Reference

> **Source**: `src/thegent/contracts/capability_registry.py`

WP-10002: Capability registry service.

Authoritative source for available capabilities, versions, and trust levels.

---

## Capability

A registered system capability.

---

## CapabilityRegistry

Central registry for managing and querying system capabilities.

### Methods

#### CapabilityRegistry.**init**

```python
__init__(self: Any)
```

---

#### CapabilityRegistry.get_capability

```python
get_capability(self: Any, cap_id: str)
```

Return capability metadata if found.

---

#### CapabilityRegistry.is_supported

```python
is_supported(self: Any, cap_id: str, version: Any)
```

Check if a capability and version are supported.

---

#### CapabilityRegistry.list_capabilities

```python
list_capabilities(self: Any)
```

List all registered capabilities.

---

#### CapabilityRegistry.register

```python
register(self: Any, cap: Capability)
```

Register a new capability.

---

---

## get_capability

```python
get_capability(self: Any, cap_id: str)
```

Return capability metadata if found.

---

## is_supported

```python
is_supported(self: Any, cap_id: str, version: Any)
```

Check if a capability and version are supported.

---

## list_capabilities

```python
list_capabilities(self: Any)
```

List all registered capabilities.

---

## register

```python
register(self: Any, cap: Capability)
```

Register a new capability.

---
