# api_typescript API Reference

> **Source**: `src/thegent/docgen/api_typescript.py`

TypeScript/JavaScript API generator.

---

## TypeScriptAPIGenerator

Generate TypeScript/JavaScript API documentation.

### Methods

#### TypeScriptAPIGenerator.**init**

```python
__init__(self: Any)
```

Initialize TypeScript API generator.

---

#### TypeScriptAPIGenerator.generate_docs

```python
generate_docs(self: Any, file_info: dict[(str, Any)])
```

Generate documentation from file info.

**Parameters**:

- `file_info`: File information dictionary

**Returns**: Generated markdown documentation

---

#### TypeScriptAPIGenerator.parse_file

```python
parse_file(self: Any, file_path: Path)
```

Parse a TypeScript/JavaScript file.

**Parameters**:

- `file_path`: Path to TS/JS file

**Returns**: Parsed file information

---

---

## generate_docs

```python
generate_docs(self: Any, file_info: dict[(str, Any)])
```

Generate documentation from file info.

**Parameters**:

- `file_info`: File information dictionary

**Returns**: Generated markdown documentation

---

## parse_file

```python
parse_file(self: Any, file_path: Path)
```

Parse a TypeScript/JavaScript file.

**Parameters**:

- `file_path`: Path to TS/JS file

**Returns**: Parsed file information

---
