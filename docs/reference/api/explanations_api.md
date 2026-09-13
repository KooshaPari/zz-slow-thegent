# explanations API Reference

> **Source**: `src/thegent/ux/explanations.py`

WP-4002: Concise and detailed explanation tiers.

---

## ExplanationGenerator

Generates explanations for agent decisions at different levels of detail.

### Methods

#### ExplanationGenerator.**init**

```python
__init__(self: Any, settings: ThegentSettings)
```

---

#### ExplanationGenerator.generate_explanation

```python
generate_explanation(self: Any, data: dict[(str, Any)], tier: ExplanationTier)
```

Generate an explanation based on data and requested tier.

---

---

## ExplanationTier

Tier of explanation detail.

**Inherits from**: `enum.StrEnum`

---

## generate_explanation

```python
generate_explanation(self: Any, data: dict[(str, Any)], tier: ExplanationTier)
```

Generate an explanation based on data and requested tier.

---
