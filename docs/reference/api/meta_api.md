# meta API Reference

> **Source**: `src/thegent/governance/meta.py`

WP-20004: Meta-Governance & Constitutional AI.

Provides high-level, human-aligned rules (constitution) for all agent operations.
Inspired by Constitutional AI principles (Anthropic).

---

## ConstitutionalPrinciple

**Inherits from**: `StrEnum`

---

## MetaGovernance

Manages the agent constitution and high-level governance rules.

### Methods

#### MetaGovernance.**init**

```python
__init__(self: Any, constitution_path: Any)
```

---

#### MetaGovernance.get_constitution_summary

```python
get_constitution_summary(self: Any)
```

Return a formatted summary of the agent constitution.

---

#### MetaGovernance.save_constitution

```python
save_constitution(self: Any)
```

Save the constitution to disk.

---

#### MetaGovernance.validate_action

```python
validate_action(self: Any, action_description: str, tags: set[str])
```

Validate an agent's intended action against the constitution.

---

---

## Rule

A high-level governance rule aligned with a constitutional principle.

---

## get_constitution_summary

```python
get_constitution_summary(self: Any)
```

Return a formatted summary of the agent constitution.

---

## save_constitution

```python
save_constitution(self: Any)
```

Save the constitution to disk.

---

## validate_action

```python
validate_action(self: Any, action_description: str, tags: set[str])
```

Validate an agent's intended action against the constitution.

---
