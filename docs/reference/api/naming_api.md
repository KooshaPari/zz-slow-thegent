# naming API Reference

> **Source**: `src/thegent/design/naming.py`

Consistent naming conventions enforcement.

---

## NamingConvention

Naming convention enforcer.

This class enforces consistent naming conventions across all components:

- Commands: kebab-case
- Config keys: snake_case
- Functions: snake_case
- Classes: PascalCase
- Constants: UPPER_SNAKE_CASE

### Methods

#### NamingConvention.**init**

```python
__init__(self: Any)
```

Initialize naming convention enforcer.

---

#### NamingConvention.suggest_name

```python
suggest_name(self: Any, name: str, convention_type: str)
```

Suggest name following convention.

Converts name to follow the specified convention.

**Parameters**:

- `name`: Name to convert
- `convention_type`: Target convention type

**Returns**: Suggested name following convention

---

#### NamingConvention.validate

```python
validate(self: Any, name: str, convention_type: str)
```

Validate name against convention.

**Parameters**:

- `name`: Name to validate
- `convention_type`: Type of convention (command, config_key, function, class, constant)

**Returns**: True if name follows convention, False otherwise

---

---

## suggest_name

```python
suggest_name(self: Any, name: str, convention_type: str)
```

Suggest name following convention.

Converts name to follow the specified convention.

**Parameters**:

- `name`: Name to convert
- `convention_type`: Target convention type

**Returns**: Suggested name following convention

---

## validate

```python
validate(self: Any, name: str, convention_type: str)
```

Validate name against convention.

**Parameters**:

- `name`: Name to validate
- `convention_type`: Type of convention (command, config_key, function, class, constant)

**Returns**: True if name follows convention, False otherwise

---
