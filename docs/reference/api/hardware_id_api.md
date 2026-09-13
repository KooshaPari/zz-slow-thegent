# hardware_id API Reference

> **Source**: `src/thegent/security/hardware_id.py`

WP-23002: Hardware-Bound Identity (TPM/SecureEnclave).

Ensures agent identities are bound to physical hardware or secure enclaves.
Provides hardware-attested provenance for agent actions.

---

## HardwareAttestation

Metadata for a hardware-bound identity attestation.

**Inherits from**: `BaseModel`

---

## HardwareIdentityManager

Manages hardware-bound cryptographic identities for agents.

### Methods

#### HardwareIdentityManager.**init**

```python
__init__(self: Any, agent_id: str)
```

---

#### HardwareIdentityManager.get_hardware_attestation

```python
get_hardware_attestation(self: Any)
```

Retrieve an attestation token from the local hardware provider.

---

#### HardwareIdentityManager.verify_attestation

```python
verify_attestation(self: Any, attestation: HardwareAttestation)
```

Verify a hardware attestation token.

---

---

## get_hardware_attestation

```python
get_hardware_attestation(self: Any)
```

Retrieve an attestation token from the local hardware provider.

---

## verify_attestation

```python
verify_attestation(self: Any, attestation: HardwareAttestation)
```

Verify a hardware attestation token.

---
