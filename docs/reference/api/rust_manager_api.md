# rust_manager API Reference

> **Source**: `src/thegent/maif/rust_manager.py`

MAIF Artifact Manager using Rust binary.

---

## RustMAIFManager

Manager that delegates MAIF operations to the Rust binary.

### Methods

#### RustMAIFManager.**init**

```python
__init__(self: Any, binary_path: Path, private_key_path: Path, public_key_path: Path)
```

---

#### RustMAIFManager.create_artifact

```python
create_artifact(self: Any, action: str, payload: dict[(str, Any)], agent: str, session: str, output_path: Path)
```

Create and sign a MAIF artifact using the Rust binary.

---

#### RustMAIFManager.ensure_keys

```python
ensure_keys(self: Any, bits: int)
```

Ensure RSA keys exist, generate if not.

---

#### RustMAIFManager.verify_artifact

```python
verify_artifact(self: Any, artifact_path: Path)
```

Verify a MAIF artifact using the Rust binary.

---

---

## create_artifact

```python
create_artifact(self: Any, action: str, payload: dict[(str, Any)], agent: str, session: str, output_path: Path)
```

Create and sign a MAIF artifact using the Rust binary.

---

## ensure_keys

```python
ensure_keys(self: Any, bits: int)
```

Ensure RSA keys exist, generate if not.

---

## verify_artifact

```python
verify_artifact(self: Any, artifact_path: Path)
```

Verify a MAIF artifact using the Rust binary.

---
