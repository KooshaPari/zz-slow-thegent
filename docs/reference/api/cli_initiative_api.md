# cli_initiative API Reference

> **Source**: `src/thegent/cli_initiative.py`

SY-008: Initiative management and roadmap tracking from PLAN.md.

---

## Initiative

Represents a phase or stream from the master plan.

### Methods

#### Initiative.**init**

```python
__init__(self: Any, id: str, title: str, status: str, deliverables: str, effort: str)
```

---

---

## initiative_audit_cmd

Audit initiative progress and dependencies.

---

## initiative_list_cmd

List roadmap initiatives from PLAN.md.

---

## parse_plan_initiatives

```python
parse_plan_initiatives(plan_path: Path)
```

Parse PLAN.md to extract initiatives/phases.

---
