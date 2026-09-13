# moral_ui API Reference

> **Source**: `src/thegent/ux/moral_ui.py`

WP-29003: Human-in-the-Loop Moral Arbitration.

Provides a UI interface for humans to resolve moral dilemmas encountered by agents.

---

## ArbitrationResult

The result of human moral arbitration.

**Inherits from**: `BaseModel`

---

## MoralDilemma

Represents a moral conflict that needs arbitration.

**Inherits from**: `BaseModel`

---

## MoralUI

Manages the UI flow for moral arbitration.

### Methods

#### MoralUI.**init**

```python
__init__(self: Any)
```

---

#### MoralUI.present_dilemma

```python
present_dilemma(self: Any, dilemma: MoralDilemma)
```

Register a dilemma for human review.

---

#### MoralUI.resolve_dilemma

```python
resolve_dilemma(self: Any, result: ArbitrationResult)
```

Apply the human decision to a pending dilemma.

---

---

## present_dilemma

```python
present_dilemma(self: Any, dilemma: MoralDilemma)
```

Register a dilemma for human review.

---

## resolve_dilemma

```python
resolve_dilemma(self: Any, result: ArbitrationResult)
```

Apply the human decision to a pending dilemma.

---
