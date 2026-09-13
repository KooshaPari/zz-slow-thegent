# xml_repair API Reference

> **Source**: `src/thegent/tools/xml_repair.py`

## SloppyXMLRepair

WP-ROB-018: Best-effort repair for malformed XML from agents.

ROB-001: Enhanced to handle 90%+ of malformed outputs with tag balancing heuristics.
ROB-015: Handles 95%+ of incomplete XML output.

### Methods

#### SloppyXMLRepair.**init**

```python
__init__(self: Any)
```

---

#### SloppyXMLRepair.extract_and_repair

```python
extract_and_repair(self: Any, text: str)
```

Extract XML block from text and repair it.

---

#### SloppyXMLRepair.repair

```python
repair(self: Any, text: str)
```

Attempt to repair malformed XML structures.

ROB-001: Enhanced with tag balancing heuristics to handle:

- Unclosed trailing tags
- Naked tags
- Tags with unclosed attributes
- Mismatched closing tags (case-insensitive matching)
- Nested unclosed tags (tag stack balancing)

---

---

## extract_and_repair

```python
extract_and_repair(self: Any, text: str)
```

Extract XML block from text and repair it.

---

## repair

```python
repair(self: Any, text: str)
```

Attempt to repair malformed XML structures.

ROB-001: Enhanced with tag balancing heuristics to handle:

- Unclosed trailing tags
- Naked tags
- Tags with unclosed attributes
- Mismatched closing tags (case-insensitive matching)
- Nested unclosed tags (tag stack balancing)

---
