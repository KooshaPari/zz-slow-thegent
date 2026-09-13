# code_annotation API Reference

> **Source**: `src/thegent/docgen/code_annotation.py`

Implement code annotation component for documentation.

---

## CodeAnnotationGenerator

Generate code annotations for documentation.

### Methods

#### CodeAnnotationGenerator.**init**

```python
__init__(self: Any, annotation_format: str)
```

---

#### CodeAnnotationGenerator.generate_annotation_component

```python
generate_annotation_component(self: Any, annotations: list[dict[(str, Any)]])
```

Generate documentation component from annotations.

**Parameters**:

- `annotations`: List of parsed annotations

**Returns**: Formatted documentation component

---

#### CodeAnnotationGenerator.parse_annotations

```python
parse_annotations(self: Any, code: str)
```

Parse annotations from code (comments like # @annotation).

**Parameters**:

- `code`: Source code

**Returns**: List of annotations

---

#### CodeAnnotationGenerator.format_reflection_annotation

```python
format_reflection_annotation(self: Any, payload: dict[(str, Any)])
```

Normalize remote->local reflection annotations to canonical schema order.

**Required Keys (in canonical order)**:

1. `schema`
2. `wl_id`
3. `connector`
4. `direction`
5. `decision`
6. `mutation_id`
7. `timestamp`

**Returns**: Canonically ordered annotation dictionary

---

---

## generate_annotation_component

```python
generate_annotation_component(self: Any, annotations: list[dict[(str, Any)]])
```

Generate documentation component from annotations.

**Parameters**:

- `annotations`: List of parsed annotations

**Returns**: Formatted documentation component

---

## parse_annotations

```python
parse_annotations(self: Any, code: str)
```

Parse annotations from code (comments like # @annotation).

**Parameters**:

- `code`: Source code

**Returns**: List of annotations

---
