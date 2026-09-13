# quantum_safe API Reference

> **Source**: `src/thegent/security/quantum_safe.py`

WP-24001: Post-Quantum Cryptographic (PQC) Signatures.

Ensures that agent artifacts are signed using algorithms resistant to quantum computer attacks.
Uses NIST-selected candidates like Dilithium or Falcon (Simulated).

---

## PQCSigner

Provides quantum-resistant digital signatures for agent artifacts.

### Methods

#### PQCSigner.**init**

```python
__init__(self: Any, algorithm: str)
```

---

#### PQCSigner.sign_artifact

```python
sign_artifact(self: Any, artifact_data: bytes)
```

Sign artifact data using the PQC private key.

---

#### PQCSigner.verify_signature

```python
verify_signature(self: Any, artifact_data: bytes, signature: str, public_key: str)
```

Verify a PQC signature.

---

---

## sign_artifact

```python
sign_artifact(self: Any, artifact_data: bytes)
```

Sign artifact data using the PQC private key.

---

## verify_signature

```python
verify_signature(self: Any, artifact_data: bytes, signature: str, public_key: str)
```

Verify a PQC signature.

---
