# tee_check API Reference

> **Source**: `src/thegent/governance/tee_check.py`

WP-23003: Attestable Execution Environments (TEE) check.

Provides verification logic for secure enclave execution.

---

## TEEAttestation

TEE Attestation report (WP-23003).

---

## TEEChecker

Verifies if the agent is running in a trusted execution environment.

### Methods

#### TEEChecker.**init**

```python
__init__(self: Any, mock_mode: bool)
```

---

#### TEEChecker.check

```python
check(self: Any)
```

Perform TEE check and return attestation.

---

#### TEEChecker.enforce_tee

```python
enforce_tee(self: Any)
```

Raise error if not running in TEE and environment requires it.

---

---

## TEEType

**Inherits from**: `Enum`

---

## check

```python
check(self: Any)
```

Perform TEE check and return attestation.

---

## enforce_tee

```python
enforce_tee(self: Any)
```

Raise error if not running in TEE and environment requires it.

---

## get_tee_attestation

Helper for governance audit emission.

---
