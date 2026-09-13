# constitution API Reference

> **Source**: `src/thegent/governance/constitution.py`

Constitutional AI and alignment enforcement for thegent (WP-3001).

---

## ConstitutionManager

WP-3001: Manages project principles and critique logic.

### Methods

#### ConstitutionManager.**init**

```python
__init__(self: Any, constitution_path: Path)
```

---

#### ConstitutionManager.critique_action

```python
critique_action(self: Any, action: dict[(str, Any)])
```

WP-3001: Pre-execution critique of a proposed agent action.

---

#### ConstitutionManager.generate_poa

```python
generate_poa(self: Any, action_id: str, aligned: bool)
```

Generate a Proof of Alignment for a MAIF artifact.

---

---

## ConstitutionalViolation

**Inherits from**: `BaseModel`

---

## ProofOfAlignment

Verifiable proof that an action aligns with the constitution.

**Inherits from**: `BaseModel`

---

## critique_action

```python
critique_action(self: Any, action: dict[(str, Any)])
```

WP-3001: Pre-execution critique of a proposed agent action.

---

## generate_poa

```python
generate_poa(self: Any, action_id: str, aligned: bool)
```

Generate a Proof of Alignment for a MAIF artifact.

---
