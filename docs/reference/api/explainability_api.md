# explainability API Reference

> **Source**: `src/thegent/observability/explainability.py`

WP-9002: Explainability stack (summary/detail/trace).

Provides a structured way to generate and present explanations for agent decisions
at three levels of detail.

---

## DetailLevel

**Inherits from**: `StrEnum`

---

## ExplainabilityEngine

Stack for managing and rendering progressive disclosure explanations.

### Methods

#### ExplainabilityEngine.**init**

```python
__init__(self: Any)
```

---

#### ExplainabilityEngine.get_explanation

```python
get_explanation(self: Any, decision_id: str, level: DetailLevel)
```

Return the explanation string for the requested level.

---

#### ExplainabilityEngine.record_decision

```python
record_decision(self: Any, decision_id: str, explanation: Explanation)
```

Register an explanation for a specific decision.

---

#### ExplainabilityEngine.render_all

```python
render_all(self: Any, decision_id: str)
```

Render a progressive disclosure view of the explanation.

---

---

## Explanation

A single decision explanation at multiple levels.

---

## get_explanation

```python
get_explanation(self: Any, decision_id: str, level: DetailLevel)
```

Return the explanation string for the requested level.

---

## record_decision

```python
record_decision(self: Any, decision_id: str, explanation: Explanation)
```

Register an explanation for a specific decision.

---

## render_all

```python
render_all(self: Any, decision_id: str)
```

Render a progressive disclosure view of the explanation.

---
