# code_validator API Reference

> **Source**: `src/thegent/docgen/code_validator.py`

Implement code example validation for documentation.

---

## CodeExampleValidator

Validate code examples in documentation.

### Methods

#### CodeExampleValidator.**init**

```python
__init__(self: Any, check_syntax: bool, run_tests: bool)
```

---

#### CodeExampleValidator.validate_code_snippet

```python
validate_code_snippet(self: Any, code: str, language: str)
```

Validate a code snippet for syntax errors.

**Parameters**:

- `code`: Source code string
- `language`: Programming language

**Returns**: Tuple of (is_valid, error_message)

---

#### CodeExampleValidator.validate_doc_file

```python
validate_doc_file(self: Any, file_path: Path)
```

Validate all code snippets in a documentation file.

**Parameters**:

- `file_path`: Documentation file path

**Returns**: List of errors found

---

---

## validate_code_snippet

```python
validate_code_snippet(self: Any, code: str, language: str)
```

Validate a code snippet for syntax errors.

**Parameters**:

- `code`: Source code string
- `language`: Programming language

**Returns**: Tuple of (is_valid, error_message)

---

## validate_doc_file

```python
validate_doc_file(self: Any, file_path: Path)
```

Validate all code snippets in a documentation file.

**Parameters**:

- `file_path`: Documentation file path

**Returns**: List of errors found

---
