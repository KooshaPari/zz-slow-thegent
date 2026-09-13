# ledger API Reference

> **Source**: `src/thegent/governance/ledger.py`

WP-5006: Ledger integrity verification.

---

## IncidentLedger

Immutable incident ledger with rolling hash chain (WP-15002).

**Inherits from**: `LedgerVerifier`

**Method Resolution Order**: `IncidentLedger -> LedgerVerifier`

### Methods

#### IncidentLedger.**init**

```python
__init__(self: Any, ledger_path: Path)
```

---

#### IncidentLedger.get_run_artifacts

```python
get_run_artifacts(self: Any, run_id: str)
```

Return all artifacts for run_id.

---

#### IncidentLedger.record_artifact

```python
record_artifact(self: Any, run_id: str, action: str, payload: dict[(str, Any)])
```

Append artifact with rolling hash; return computed hash.

---

#### IncidentLedger.verify_integrity

```python
verify_integrity(self: Any)
```

---

---

## LedgerVerifier

Verifies the integrity of the action ledger using rolling hashes.

### Methods

#### LedgerVerifier.**init**

```python
__init__(self: Any, ledger_path: Path)
```

---

#### LedgerVerifier.verify_integrity

```python
verify_integrity(self: Any)
```

Verify the rolling hash chain in the ledger.

---

---

## get_run_artifacts

```python
get_run_artifacts(self: Any, run_id: str)
```

Return all artifacts for run_id.

---

## record_artifact

```python
record_artifact(self: Any, run_id: str, action: str, payload: dict[(str, Any)])
```

Append artifact with rolling hash; return computed hash.

---

## verify_integrity

```python
verify_integrity(self: Any) -> bool
```

---
