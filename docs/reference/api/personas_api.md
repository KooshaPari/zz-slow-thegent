# personas API Reference

> **Source**: `src/thegent/governance/personas.py`

WP-12007: Persona profiles and access constraints.

Defines role-based access limits and defaults for different operator personas.

---

## PersonaManager

Manages role-based constraints for operator personas.

### Methods

#### PersonaManager.**init**

```python
__init__(self: Any)
```

---

#### PersonaManager.check_access

```python
check_access(self: Any, persona: str, operation: str, lane: str)
```

Verify if a persona can perform a specific operation in a specific lane.

---

---

## check_access

```python
check_access(self: Any, persona: str, operation: str, lane: str)
```

Verify if a persona can perform a specific operation in a specific lane.

---
