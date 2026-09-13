# fallback_ui API Reference

> **Source**: `src/thegent/ux/fallback_ui.py`

WP-4003: One-click safe fallback options.

---

## FallbackOption

A safe fallback action for the operator.

### Methods

#### FallbackOption.**init**

```python
__init__(self: Any, id: str, label: str, description: str, command: str)
```

---

---

## FallbackRegistry

Registry of safe fallback options based on failure context.

### Methods

#### FallbackRegistry.**init**

```python
__init__(self: Any, settings: ThegentSettings)
```

---

#### FallbackRegistry.get_recommendations

```python
get_recommendations(self: Any, failure_kind: str)
```

Return recommended fallback options based on failure type.

---

---

## get_recommendations

```python
get_recommendations(self: Any, failure_kind: str)
```

Return recommended fallback options based on failure type.

---
