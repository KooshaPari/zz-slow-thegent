# homomorphic API Reference

> **Source**: `src/thegent/security/homomorphic.py`

WP-24003: Homomorphic Encryption for Context.

Enables agents to perform computations on encrypted context data without decrypting it.
Protects sensitive context in multi-tenant shared memory environments.

---

## HomomorphicContext

Simulates Fully Homomorphic Encryption (FHE) for agent context.

### Methods

#### HomomorphicContext.**init**

```python
__init__(self: Any)
```

---

#### HomomorphicContext.compute_on_encrypted

```python
compute_on_encrypted(self: Any, ciphertext: str, operation: str)
```

Perform an operation (e.g. search, count) on encrypted data without decrypting.

---

#### HomomorphicContext.decrypt_result

```python
decrypt_result(self: Any, ciphertext: str)
```

Decrypt the result of a homomorphic computation.

---

#### HomomorphicContext.encrypt_context

```python
encrypt_context(self: Any, data: str)
```

Encrypt context data into an FHE ciphertext.

---

---

## compute_on_encrypted

```python
compute_on_encrypted(self: Any, ciphertext: str, operation: str)
```

Perform an operation (e.g. search, count) on encrypted data without decrypting.

---

## decrypt_result

```python
decrypt_result(self: Any, ciphertext: str)
```

Decrypt the result of a homomorphic computation.

---

## encrypt_context

```python
encrypt_context(self: Any, data: str)
```

Encrypt context data into an FHE ciphertext.

---
