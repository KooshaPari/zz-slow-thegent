# liveness API Reference

> **Source**: `src/thegent/verification/liveness.py`

WP-25001: Liveness Proofs for Autonomous Agent Loops.

Ensures that an agent loop will eventually terminate or make progress.
Uses formal-inspired invariant checking on loop state history.

---

## LivenessChecker

Verifies liveness properties of autonomous execution loops.

### Methods

#### LivenessChecker.**init**

```python
__init__(self: Any, run_id: str, max_retries: int, progress_timeout_s: int)
```

---

#### LivenessChecker.check_invariants

```python
check_invariants(self: Any)
```

Check for liveness violations in the execution history.

---

#### LivenessChecker.record_step

```python
record_step(self: Any, step_type: str, state: dict[(str, Any)])
```

Record a step in the agent loop for liveness analysis.

---

---

## LivenessViolation

Details of a detected liveness violation.

**Inherits from**: `BaseModel`

---

## check_invariants

```python
check_invariants(self: Any)
```

Check for liveness violations in the execution history.

---

## record_step

```python
record_step(self: Any, step_type: str, state: dict[(str, Any)])
```

Record a step in the agent loop for liveness analysis.

---
