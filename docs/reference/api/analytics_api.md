# analytics API Reference

> **Source**: `src/thegent/docgen/analytics.py`

Implement Google Analytics / Plausible integration for documentation.

---

## AnalyticsGenerator

Generate analytics integration for documentation.

### Methods

#### AnalyticsGenerator.**init**

```python
__init__(self: Any, google_analytics_id: Any, plausible_domain: Any)
```

---

#### AnalyticsGenerator.generate_google_analytics_script

```python
generate_google_analytics_script(self: Any)
```

Generate Google Analytics script tag.

**Returns**: Google Analytics script tag HTML content

---

#### AnalyticsGenerator.generate_plausible_script

```python
generate_plausible_script(self: Any)
```

Generate Plausible script tag.

**Returns**: Plausible script tag HTML content

---

---

## generate_google_analytics_script

```python
generate_google_analytics_script(self: Any)
```

Generate Google Analytics script tag.

**Returns**: Google Analytics script tag HTML content

---

## generate_plausible_script

```python
generate_plausible_script(self: Any)
```

Generate Plausible script tag.

**Returns**: Plausible script tag HTML content

---
