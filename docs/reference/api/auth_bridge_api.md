# auth_bridge API Reference

> **Source**: `src/thegent/security/auth_bridge.py`

WP-19003: Enterprise SSO Bridge (OIDC/SAML).

Enables enterprise identity federation for thegent instances.

---

## AuthBridge

Enterprise SSO integration for thegent instances.

### Methods

#### AuthBridge.**init**

```python
__init__(self: Any, config: Any)
```

---

#### AuthBridge.bridge_saml_response

```python
bridge_saml_response(self: Any, saml_response: str)
```

WP-19003: Simple bridge for SAML assertions (mock).

---

---

## SSOConfig

Configuration for SSO (OIDC/SAML).

**Inherits from**: `BaseModel`

---

## bridge_saml_response

```python
bridge_saml_response(self: Any, saml_response: str)
```

WP-19003: Simple bridge for SAML assertions (mock).

---
