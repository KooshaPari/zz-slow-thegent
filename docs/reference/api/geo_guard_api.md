# geo_guard API Reference

> **Source**: `src/thegent/security/geo_guard.py`

WP-35003: Geo-Distributed Data Sovereignty Guard.

Ensures that data is stored and processed according to regional sovereignty rules.

---

## DataLocationCheck

Result of a sovereignty check.

**Inherits from**: `BaseModel`

---

## GeoGuard

Enforces data sovereignty policies across distributed regions.

### Methods

#### GeoGuard.**init**

```python
__init__(self: Any)
```

---

#### GeoGuard.add_rule

```python
add_rule(self: Any, rule: SovereigntyRule)
```

Add or update a sovereignty rule.

---

#### GeoGuard.validate_location

```python
validate_location(self: Any, data_id: str, category: str, region: str)
```

Verify if data of a given category can reside in the specified region.

---

---

## SovereigntyRule

Defines where specific data types can be stored/processed.

**Inherits from**: `BaseModel`

---

## add_rule

```python
add_rule(self: Any, rule: SovereigntyRule)
```

Add or update a sovereignty rule.

---

## validate_location

```python
validate_location(self: Any, data_id: str, category: str, region: str)
```

Verify if data of a given category can reside in the specified region.

---
