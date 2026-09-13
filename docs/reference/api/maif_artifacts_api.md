# maif_artifacts API Reference

> **Source**: `src/thegent/research/maif_artifacts.py`

MAIF Action Artifacts (Signed Artifacts).

---

## MAIFArtifact

MAIF (Model-Action Interface Format) signed artifact.

### Methods

#### MAIFArtifact.**init**

```python
__init__(self: Any, action: dict[(str, Any)], signature: Any)
```

Initialize MAIF artifact.

**Parameters**:

- `action`: Action dictionary
- `signature`: Digital signature

---

#### MAIFArtifact.sign

```python
sign(self: Any, private_key: str)
```

Sign the artifact.

**Parameters**:

- `private_key`: Private key for signing

**Returns**: Signature string

---

#### MAIFArtifact.to_dict

```python
to_dict(self: Any)
```

Convert to dictionary.

**Returns**: Dictionary representation

---

#### MAIFArtifact.verify

```python
verify(self: Any, public_key: str)
```

Verify artifact signature.

**Parameters**:

- `public_key`: Public key for verification

**Returns**: True if signature is valid

---

---

## sign

```python
sign(self: Any, private_key: str)
```

Sign the artifact.

**Parameters**:

- `private_key`: Private key for signing

**Returns**: Signature string

---

## to_dict

```python
to_dict(self: Any)
```

Convert to dictionary.

**Returns**: Dictionary representation

---

## verify

```python
verify(self: Any, public_key: str)
```

Verify artifact signature.

**Parameters**:

- `public_key`: Public key for verification

**Returns**: True if signature is valid

---
