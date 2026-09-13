# openapi API Reference

> **Source**: `src/thegent/docgen/openapi.py`

Implement OpenAPI/Swagger integration for documentation.

---

## OpenAPIGenerator

Generate OpenAPI/Swagger integration for documentation.

### Methods

#### OpenAPIGenerator.**init**

```python
__init__(self: Any, output_format: str)
```

---

#### OpenAPIGenerator.generate_swagger_ui_html

```python
generate_swagger_ui_html(self: Any, spec_url: str)
```

Generate HTML for Swagger UI.

**Parameters**:

- `spec_url`: URL to spec file

**Returns**: Swagger UI HTML content

---

#### OpenAPIGenerator.parse_openapi_spec

```python
parse_openapi_spec(self: Any, file_path: Path)
```

Parse an OpenAPI spec file.

**Parameters**:

- `file_path`: Spec file path

**Returns**: Parsed spec dictionary

---

---

## generate_swagger_ui_html

```python
generate_swagger_ui_html(self: Any, spec_url: str)
```

Generate HTML for Swagger UI.

**Parameters**:

- `spec_url`: URL to spec file

**Returns**: Swagger UI HTML content

---

## parse_openapi_spec

```python
parse_openapi_spec(self: Any, file_path: Path)
```

Parse an OpenAPI spec file.

**Parameters**:

- `file_path`: Spec file path

**Returns**: Parsed spec dictionary

---
