# validation API Reference

> **Source**: `src/thegent/contracts/validation.py`

Semantic Validation Layer for agent structured messages.

Enforces invariants and cross-tag logic for CanonicalStructuredMessage (CSM).

---

## InvariantViolation

Raised when a specific invariant is violated.

**Inherits from**: `SemanticValidationError`

**Method Resolution Order**: `InvariantViolation -> SemanticValidationError`

---

## SemanticPolicyEngine

WP-7005: Policy layer for semantic validation of agent outputs.

### Methods

#### SemanticPolicyEngine.**init**

```python
__init__(self: Any, strict: bool)
```

---

#### SemanticPolicyEngine.add_rule

```python
add_rule(self: Any, rule: Callable[(Any, list[str])])
```

Register a custom validation rule.

---

#### SemanticPolicyEngine.evaluate

```python
evaluate(self: Any, csm: CanonicalStructuredMessage)
```

Evaluate CSM against all semantic rules.

**Returns**: Dict with 'allowed', 'issues', 'drift_detected'.

---

---

## SemanticValidationError

Raised when a CSM fails semantic validation.

**Inherits from**: `Exception`

---

## add_rule

```python
add_rule(self: Any, rule: Callable[(Any, list[str])])
```

Register a custom validation rule.

---

## ensure_valid_csm

```python
ensure_valid_csm(csm: CanonicalStructuredMessage)
```

Raise InvariantViolation if CSM is semantically invalid.

---

## evaluate

```python
evaluate(self: Any, csm: CanonicalStructuredMessage)
```

Evaluate CSM against all semantic rules.

**Returns**: Dict with 'allowed', 'issues', 'drift_detected'.

---

## validate_csm

```python
validate_csm(csm: CanonicalStructuredMessage)
```

Perform semantic validation on a CSM.

**Returns**: List of validation issue strings. Empty if valid.

---
