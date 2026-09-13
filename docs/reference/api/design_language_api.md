# design_language API Reference

> **Source**: `src/thegent/design/design_language.py`

Design language system with platform-specific tokens.

---

## DesignLanguage

Design language system.

This class manages design tokens (colors, typography, spacing) and
applies them consistently across all components, with platform-specific
overrides where appropriate.

### Methods

#### DesignLanguage.**init**

```python
__init__(self: Any)
```

Initialize design language system.

---

#### DesignLanguage.apply_to_cli

```python
apply_to_cli(self: Any)
```

Apply design language to CLI.

Configures Rich console styling from the active design tokens.

---

#### DesignLanguage.get_token

```python
get_token(self: Any, name: str, platform: Any)
```

Get design token value.

**Parameters**:

- `name`: Token name (e.g., "color.primary")
- `platform`: Platform override, or None to use detected platform

**Returns**: Token value, or None if not found

---

---

## DesignToken

Design token definition.

---

## apply_to_cli

```python
apply_to_cli(self: Any)
```

Apply design language to CLI.

Configures Rich console styling from the active design tokens.

---

## get_token

```python
get_token(self: Any, name: str, platform: Any)
```

Get design token value.

**Parameters**:

- `name`: Token name (e.g., "color.primary")
- `platform`: Platform override, or None to use detected platform

**Returns**: Token value, or None if not found

---
