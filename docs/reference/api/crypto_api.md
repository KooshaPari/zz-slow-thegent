# crypto API Reference

> **Source**: `src/thegent/maif/crypto.py`

MAIF Cryptographic Foundation - Signing and Verification.

Provides RSA-2048 signing and verification for MAIF artifacts.

---

## SigningKey

RSA-2048 signing key for artifact creation.

Uses RSA-2048 with SHA-256 for deterministic, reproducible signatures.

### Methods

#### SigningKey.**init**

```python
__init__(self: Any, private_key: rsa.RSAPrivateKey)
```

Initialize with a private key.

**Parameters**:

- `private_key`: cryptography.hazmat RSAPrivateKey instance.

---

#### SigningKey.from_pem

```python
from_pem(cls: Any, pem_bytes: bytes)
```

Load signing key from PEM format.

**Parameters**:

- `pem_bytes`: PEM-encoded private key bytes.

**Returns**: SigningKey instance.

---

#### SigningKey.generate

```python
generate(cls: Any)
```

Generate a new RSA-2048 key pair.

**Returns**: SigningKey instance with freshly generated key pair.

---

#### SigningKey.get_public_key

```python
get_public_key(self: Any)
```

Get the public key for verification.

**Returns**: VerifyingKey instance with the corresponding public key.

---

#### SigningKey.sign

```python
sign(self: Any, data: bytes)
```

Sign data with RSA-2048-SHA256.

**Parameters**:

- `data`: Bytes to sign.

**Returns**: RSA signature bytes (256 bytes for RSA-2048).

---

#### SigningKey.to_pem

```python
to_pem(self: Any)
```

Export signing key to PEM format.

**Returns**: PEM-encoded private key bytes.

---

---

## VerifyingKey

RSA-2048 public key for artifact verification.

Used to verify signatures on MAIF artifacts.

### Methods

#### VerifyingKey.**init**

```python
__init__(self: Any, public_key: rsa.RSAPublicKey)
```

Initialize with a public key.

**Parameters**:

- `public_key`: cryptography.hazmat RSAPublicKey instance.

---

#### VerifyingKey.from_pem

```python
from_pem(cls: Any, pem_bytes: bytes)
```

Load verifying key from PEM format.

**Parameters**:

- `pem_bytes`: PEM-encoded public key bytes.

**Returns**: VerifyingKey instance.

---

#### VerifyingKey.to_pem

```python
to_pem(self: Any)
```

Export verifying key to PEM format.

**Returns**: PEM-encoded public key bytes.

---

#### VerifyingKey.verify

```python
verify(self: Any, data: bytes, signature: bytes)
```

Verify RSA-2048-SHA256 signature.

**Parameters**:

- `data`: Original data bytes that were signed.
- `signature`: RSA signature bytes to verify.

**Returns**: True if signature is valid, False otherwise.

---

---

## from_pem

```python
from_pem(cls: Any, pem_bytes: bytes)
```

Load verifying key from PEM format.

**Parameters**:

- `pem_bytes`: PEM-encoded public key bytes.

**Returns**: VerifyingKey instance.

**Raises**:

- `ValueError`: If PEM format is invalid.

---

## generate

```python
generate(cls: Any)
```

Generate a new RSA-2048 key pair.

**Returns**: SigningKey instance with freshly generated key pair.

---

## get_public_key

```python
get_public_key(self: Any)
```

Get the public key for verification.

**Returns**: VerifyingKey instance with the corresponding public key.

---

## hash_data

```python
hash_data(data: bytes)
```

Compute SHA-256 hash of data.

**Parameters**:

- `data`: Bytes to hash.

**Returns**: Hex-encoded SHA-256 hash.

---

## sign

```python
sign(self: Any, data: bytes)
```

Sign data with RSA-2048-SHA256.

**Parameters**:

- `data`: Bytes to sign.

**Returns**: RSA signature bytes (256 bytes for RSA-2048).

---

## to_pem

```python
to_pem(self: Any)
```

Export verifying key to PEM format.

**Returns**: PEM-encoded public key bytes.

---

## verify

```python
verify(self: Any, data: bytes, signature: bytes)
```

Verify RSA-2048-SHA256 signature.

**Parameters**:

- `data`: Original data bytes that were signed.
- `signature`: RSA signature bytes to verify.

**Returns**: True if signature is valid, False otherwise.

---
