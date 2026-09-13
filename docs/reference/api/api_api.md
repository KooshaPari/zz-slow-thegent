# api API Reference

> **Source**: `src/thegent/artifacts/api.py`

Artifact Verification and Retrieval API - High-level interface for artifact operations.

Provides:

- Artifact creation and storage
- Verification and validation
- Retrieval and querying
- Dependency tracking

---

## ArtifactAPI

High-level API for artifact operations.

Provides:

- Artifact creation with generators
- Storage and retrieval
- Verification and validation
- Dependency and relationship tracking

### Methods

#### ArtifactAPI.**init**

```python
__init__(self: Any, signing_key: SigningKey, verifying_key: VerifyingKey, storage: Any, registry: Any)
```

Initialize artifact API.

**Parameters**:

- `signing_key`: RSA signing key for artifacts
- `verifying_key`: RSA verifying key for validation
- `storage`: Artifact storage (defaults to in-memory)
- `registry`: Artifact registry (defaults to global registry)

---

#### ArtifactAPI.get_artifact_type_info

```python
get_artifact_type_info(self: Any, artifact_type: str)
```

Get information about an artifact type.

**Parameters**:

- `artifact_type`: Type identifier

**Returns**: Type information or None if not found

---

---

## get_artifact_type_info

```python
get_artifact_type_info(self: Any, artifact_type: str)
```

Get information about an artifact type.

**Parameters**:

- `artifact_type`: Type identifier

**Returns**: Type information or None if not found

---
