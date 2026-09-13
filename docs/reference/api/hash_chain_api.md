# hash_chain API Reference

> **Source**: `src/thegent/maif/hash_chain.py`

MAIF Hash Chain Validator - Verifying artifact integrity.

Implements the HashChainValidator class for verifying artifact chains and
detecting tampering.

---

## HashChainValidator

Validator for MAIF artifact chains.

Verifies the integrity of artifact chains by checking:

- Hash chain continuity (each artifact's previous_hash matches prior artifact's hash)
- Signature validity (each artifact is properly signed)
- Chain heads (latest artifact hash per session)

### Methods

#### HashChainValidator.**init**

```python
__init__(self: Any, verifying_key: VerifyingKey)
```

Initialize the hash chain validator.

**Parameters**:

- `verifying_key`: VerifyingKey instance for signature verification.

---

#### HashChainValidator.get_chain_head

```python
get_chain_head(self: Any, session_id: str)
```

Get the latest artifact hash for a session.

**Parameters**:

- `session_id`: Session identifier.

**Returns**: Hash of the latest artifact in the session, or None if not known.

---

#### HashChainValidator.has_chain_head

```python
has_chain_head(self: Any, session_id: str)
```

Check if chain head is known for a session.

**Parameters**:

- `session_id`: Session identifier.

**Returns**: True if chain head is known, False otherwise.

---

#### HashChainValidator.reset_session

```python
reset_session(self: Any, session_id: str)
```

Reset chain head for a session.

**Parameters**:

- `session_id`: Session identifier.

---

#### HashChainValidator.verify_artifact

```python
verify_artifact(self: Any, artifact: MAIFArtifact)
```

Verify a single artifact's signature.

**Parameters**:

- `artifact`: MAIFArtifact to verify.

**Returns**: True if signature is valid, False otherwise.

---

#### HashChainValidator.verify_chain

```python
verify_chain(self: Any, artifacts: list[MAIFArtifact])
```

Verify integrity of an artifact chain.

Checks that:

1. Hash chain is continuous (each artifact's previous_hash matches prior)
2. All signatures are valid
3. Chain is internally consistent

**Parameters**:

- `artifacts`: List of MAIFArtifacts to verify (should be sorted by timestamp).

**Returns**: Tuple of (is_valid, message) where is_valid is True if chain is valid.

---

#### HashChainValidator.verify_chain_from_head

```python
verify_chain_from_head(self: Any, session_id: str, artifacts: list[MAIFArtifact])
```

Verify chain starting from known chain head.

Verifies that the provided artifacts extend or match the known chain head
for the session.

**Parameters**:

- `session_id`: Session identifier.
- `artifacts`: List of artifacts to verify.

**Returns**: Tuple of (is_valid, message).

---

---

## get_chain_head

```python
get_chain_head(self: Any, session_id: str)
```

Get the latest artifact hash for a session.

**Parameters**:

- `session_id`: Session identifier.

**Returns**: Hash of the latest artifact in the session, or None if not known.

---

## has_chain_head

```python
has_chain_head(self: Any, session_id: str)
```

Check if chain head is known for a session.

**Parameters**:

- `session_id`: Session identifier.

**Returns**: True if chain head is known, False otherwise.

---

## reset_session

```python
reset_session(self: Any, session_id: str)
```

Reset chain head for a session.

**Parameters**:

- `session_id`: Session identifier.

---

## verify_artifact

```python
verify_artifact(self: Any, artifact: MAIFArtifact)
```

Verify a single artifact's signature.

**Parameters**:

- `artifact`: MAIFArtifact to verify.

**Returns**: True if signature is valid, False otherwise.

---

## verify_chain

```python
verify_chain(self: Any, artifacts: list[MAIFArtifact])
```

Verify integrity of an artifact chain.

Checks that:

1. Hash chain is continuous (each artifact's previous_hash matches prior)
2. All signatures are valid
3. Chain is internally consistent

**Parameters**:

- `artifacts`: List of MAIFArtifacts to verify (should be sorted by timestamp).

**Returns**: Tuple of (is_valid, message) where is_valid is True if chain is valid.

---

## verify_chain_from_head

```python
verify_chain_from_head(self: Any, session_id: str, artifacts: list[MAIFArtifact])
```

Verify chain starting from known chain head.

Verifies that the provided artifacts extend or match the known chain head
for the session.

**Parameters**:

- `session_id`: Session identifier.
- `artifacts`: List of artifacts to verify.

**Returns**: Tuple of (is_valid, message).

---
