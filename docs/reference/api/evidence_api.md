# evidence API Reference

> **Source**: `src/thegent/orchestration/evidence.py`

Evidence capture at every promotion gate (WP-1005, FR-004).

Captures CSM state as evidence before promotion, with hash verification
and completeness audit trail.

---

## PromotionGate

WP-1005: Evidence capture and validation before state promotion.

### Methods

#### PromotionGate.**init**

```python
__init__(self: Any, session_dir: Path)
```

---

#### PromotionGate.capture_evidence

```python
capture_evidence(self: Any, run_id: str, csm: Any)
```

Capture CSM state as evidence; return SHA-256 hash. Appends to audit trail.

---

#### PromotionGate.validate_promotion

```python
validate_promotion(self: Any, csm: Any, policy: FallbackPolicy)
```

Validate if CSM is ready for promotion based on policy.

---

#### PromotionGate.verify_evidence_hash

```python
verify_evidence_hash(self: Any, run_id: str, phase: str, expected_hash: str)
```

Verify stored evidence hash matches expected. Returns True if valid.

---

---

## capture_evidence

```python
capture_evidence(self: Any, run_id: str, csm: Any)
```

Capture CSM state as evidence; return SHA-256 hash. Appends to audit trail.

---

## validate_promotion

```python
validate_promotion(self: Any, csm: Any, policy: FallbackPolicy)
```

Validate if CSM is ready for promotion based on policy.

---

## verify_evidence_hash

```python
verify_evidence_hash(self: Any, run_id: str, phase: str, expected_hash: str)
```

Verify stored evidence hash matches expected. Returns True if valid.

---
