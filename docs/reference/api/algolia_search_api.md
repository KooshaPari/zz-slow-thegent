# algolia_search API Reference

> **Source**: `src/thegent/docgen/algolia_search.py`

Algolia search integration for documentation.

---

## AlgoliaSearchIntegration

Algolia search integration with suggestions.

### Methods

#### AlgoliaSearchIntegration.**init**

```python
__init__(self: Any, app_id: str, api_key: str, index_name: str)
```

Initialize Algolia integration.

**Parameters**:

- `app_id`: Algolia application ID
- `api_key`: Algolia API key
- `index_name`: Index name

---

#### AlgoliaSearchIntegration.generate_config

```python
generate_config(self: Any)
```

Generate Algolia configuration.

**Returns**: Configuration dictionary

---

#### AlgoliaSearchIntegration.render_search_component

```python
render_search_component(self: Any)
```

Render search component HTML.

**Returns**: HTML string

---

---

## generate_config

```python
generate_config(self: Any)
```

Generate Algolia configuration.

**Returns**: Configuration dictionary

---

## render_search_component

```python
render_search_component(self: Any)
```

Render search component HTML.

**Returns**: HTML string

---
