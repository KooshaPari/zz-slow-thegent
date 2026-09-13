# signatures API Reference

> **Source**: `src/thegent/governance/signatures.py`

WP-3002: Signed action artifacts and provenance signatures (FR-010).

BKM-03: When THGENT_USE_NATIVE_CRYPTO=1, uses thegent_crypto Rust extension
for hash/sign/verify. Falls back to Python hashlib/hmac otherwise.

---

## ArtifactSigner

Manager for signing and verifying governance artifacts.

### Methods

#### ArtifactSigner.**init**

```python
__init__(self: Any, settings: Any)
```

---

#### ArtifactSigner.create_signed_artifact

```python
create_signed_artifact(self: Any, artifact_type: str, payload: dict[(str, Any)])
```

Create a signed artifact with metadata.

---

#### ArtifactSigner.verify_envelope

```python
verify_envelope(self: Any, envelope: dict[(str, Any)])
```

Verify the signature of an artifact envelope.

---

---

## create_signed_artifact

```python
create_signed_artifact(self: Any, artifact_type: str, payload: dict[(str, Any)])
```

Create a signed artifact with metadata.

---

## generate_artifact_hash

```python
generate_artifact_hash(data: dict[(str, Any)])
```

Generate SHA-256 hash of a dictionary artifact.

---

## sign_artifact

```python
sign_artifact(data: dict[(str, Any)], secret_key: str)
```

Produce a provenance signature for an artifact using HMAC-SHA256.

---

## verify_envelope

```python
verify_envelope(self: Any, envelope: dict[(str, Any)])
```

Verify the signature of an artifact envelope.

---

## verify_signature

```python
verify_signature(data: dict[(str, Any)], signature: str, secret_key: str)
```

Verify the provenance signature of an artifact.

---
