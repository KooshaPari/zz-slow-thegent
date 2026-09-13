# api_python API Reference

> **Source**: `src/thegent/docgen/api_python.py`

Enhanced Python API generator (mkdocstrings-like).

---

## PythonAPIGenerator

Generate Python API documentation from docstrings.

### Methods

#### PythonAPIGenerator.**init**

```python
__init__(self: Any)
```

Initialize Python API generator.

---

#### PythonAPIGenerator.generate_docs

```python
generate_docs(self: Any, module_info: dict[(str, Any)])
```

Generate documentation from module info.

**Parameters**:

- `module_info`: Module information dictionary

**Returns**: Generated markdown documentation

---

#### PythonAPIGenerator.parse_module

```python
parse_module(self: Any, module_path: Path)
```

Parse a Python module.

**Parameters**:

- `module_path`: Path to Python module

**Returns**: Parsed module information

---

---

## generate_docs

```python
generate_docs(self: Any, module_info: dict[(str, Any)])
```

Generate documentation from module info.

**Parameters**:

- `module_info`: Module information dictionary

**Returns**: Generated markdown documentation

---

## parse_module

```python
parse_module(self: Any, module_path: Path)
```

Parse a Python module.

**Parameters**:

- `module_path`: Path to Python module

**Returns**: Parsed module information

---
