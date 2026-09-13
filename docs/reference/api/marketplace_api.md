# marketplace API Reference

> **Source**: `src/thegent/contracts/marketplace.py`

WP-15003: Enterprise plugin marketplace contracts with RSA verification.

---

## PluginContract

---

## PluginVerifier

Verifies third-party plugin contracts for safe execution (WP-15003).

### Methods

#### PluginVerifier.**init**

```python
__init__(self: Any, public_key_dir: Any)
```

---

#### PluginVerifier.check_permissions

```python
check_permissions(self: Any, contract: PluginContract, requested_action: str)
```

Check if the plugin contract allows the requested action.

---

#### PluginVerifier.verify_contract

```python
verify_contract(self: Any, contract: PluginContract)
```

Verify the signature of a plugin contract.

---

---

## check_permissions

```python
check_permissions(self: Any, contract: PluginContract, requested_action: str)
```

Check if the plugin contract allows the requested action.

---

## verify_contract

```python
verify_contract(self: Any, contract: PluginContract)
```

Verify the signature of a plugin contract.

---
