# verification API Reference

> **Source**: `src/thegent/agents/verification.py`

WP-16001: Multi-Step CoT Verification.

Chain-of-Thought (CoT) verification before agent execution.

---

## CoTVerifier

Verifies multi-step agent reasoning chains before final execution.

### Methods

#### CoTVerifier.**init**

```python
__init__(self: Any, run_id: str)
```

---

#### CoTVerifier.get_summary

```python
get_summary(self: Any)
```

Summarize all verification results.

---

#### CoTVerifier.verify_step

```python
verify_step(self: Any, step_id: str, prompt: str, reasoning: str)
```

Verify a single reasoning step against its intended prompt.

---

---

## VerificationResult

Result of a CoT step verification.

**Inherits from**: `BaseModel`

---

## get_summary

```python
get_summary(self: Any)
```

Summarize all verification results.

---

## verify_step

```python
verify_step(self: Any, step_id: str, prompt: str, reasoning: str)
```

Verify a single reasoning step against its intended prompt.

---
