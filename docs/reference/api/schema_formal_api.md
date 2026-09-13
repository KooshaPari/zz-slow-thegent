# schema_formal API Reference

> **Source**: `src/thegent/verification/schema_formal.py`

WP-27003: Formal Verification of Schema Evolution.

Ensures schema changes maintain backward compatibility and follow evolution policies.

---

## SchemaEvolutionVerifier

Verifies evolution between two schema versions to prevent breaking changes.

### Methods

#### SchemaEvolutionVerifier.check_liveness_impact

```python
check_liveness_impact(self: Any, evolution_report: dict[(str, Any)])
```

WP-25001: Check if evolution impacts agent liveness.

Removing critical tags (STATUS, SUMMARY) impacts liveness.

---

#### SchemaEvolutionVerifier.verify_compatibility

```python
verify_compatibility(self: Any, old_schema: dict[(str, Any)], new_schema: dict[(str, Any)])
```

Check for breaking changes between old and new schema.

A breaking change is:

- Removal of a field
- Change of field type (if strictly typed)
- Making an existing optional field mandatory

---

#### SchemaEvolutionVerifier.verify_tag_evolution

```python
verify_tag_evolution(self: Any, old_tags: list[str], new_tags: list[str])
```

Verify evolution of a list of allowed XML tags.

Removing a tag is breaking; adding is an evolution.

---

---

## check_liveness_impact

```python
check_liveness_impact(self: Any, evolution_report: dict[(str, Any)])
```

WP-25001: Check if evolution impacts agent liveness.

Removing critical tags (STATUS, SUMMARY) impacts liveness.

---

## verify_compatibility

```python
verify_compatibility(self: Any, old_schema: dict[(str, Any)], new_schema: dict[(str, Any)])
```

Check for breaking changes between old and new schema.

A breaking change is:

- Removal of a field
- Change of field type (if strictly typed)
- Making an existing optional field mandatory

---

## verify_tag_evolution

```python
verify_tag_evolution(self: Any, old_tags: list[str], new_tags: list[str])
```

Verify evolution of a list of allowed XML tags.

Removing a tag is breaking; adding is an evolution.

---
