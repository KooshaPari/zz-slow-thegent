# fast_json_schema API Reference

> **Source**: `src/thegent/infra/fast_json_schema.py`

Fast JSON schema validator with optimized backends.

This module provides a high-performance abstraction layer for JSON schema validation
that automatically selects the fastest available backend:

- fastjsonschema: 2-3x faster than jsonschema
- jsonschema: Standard fallback

Performance improvements:

- fastjsonschema compiles schemas to Python code (2-3x faster)
- Automatic backend selection based on availability
- Cached compiled schemas for repeated validation

---

## FastJSONSchemaValidator

High-performance JSON schema validator with automatic backend selection.

Backend priority (fastest first):

1. fastjsonschema (if installed) - 2-3x faster, compiles schemas to Python
2. jsonschema (standard fallback) - baseline performance

### Methods

#### FastJSONSchemaValidator.**init**

```python
__init__(self: Any, schema: dict[(str, Any)])
```

Initialize validator with a schema.

**Parameters**:

- `schema`: JSON schema dictionary

---

#### FastJSONSchemaValidator.backend

```python
backend(self: Any)
```

Get current backend name.

---

#### FastJSONSchemaValidator.is_valid

```python
is_valid(self: Any, instance: Any)
```

Check if instance is valid without raising exception.

**Parameters**:

- `instance`: Data to validate

**Returns**: True if valid, False otherwise

---

#### FastJSONSchemaValidator.validate

```python
validate(self: Any, instance: Any)
```

Validate instance against schema.

**Parameters**:

- `instance`: Data to validate

---

---

## backend

```python
backend(self: Any)
```

Get current backend name.

---

## get_schema_validator

```python
get_schema_validator(schema: dict[(str, Any)], cache_key: Any)
```

Get or create a schema validator (with caching).

**Parameters**:

- `schema`: JSON schema dictionary
- `cache_key`: Optional cache key (uses schema hash if not provided)

**Returns**: FastJSONSchemaValidator instance

---

## is_valid

```python
is_valid(self: Any, instance: Any)
```

Check if instance is valid without raising exception.

**Parameters**:

- `instance`: Data to validate

**Returns**: True if valid, False otherwise

---

## is_valid_json_schema

```python
is_valid_json_schema(instance: Any, schema: dict[(str, Any)], cache_key: Any)
```

Check if instance is valid against schema.

**Parameters**:

- `instance`: Data to validate
- `schema`: JSON schema dictionary
- `cache_key`: Optional cache key for schema caching

**Returns**: True if valid, False otherwise

---

## validate

```python
validate(self: Any, instance: Any)
```

Validate instance against schema.

**Parameters**:

- `instance`: Data to validate

**Raises**:

- `ValidationError`: If validation fails

---

## validate_json_schema

```python
validate_json_schema(instance: Any, schema: dict[(str, Any)], cache_key: Any)
```

Validate instance against schema using fastest available backend.

**Parameters**:

- `instance`: Data to validate
- `schema`: JSON schema dictionary
- `cache_key`: Optional cache key for schema caching

**Raises**:

- `ValidationError`: If validation fails

---
