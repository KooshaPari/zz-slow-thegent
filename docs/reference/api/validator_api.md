# validator API Reference

> **Source**: `src/thegent/task/validator.py`

Task validation implementation.

---

## TaskValidator

Task validator using JSON Schema.

### Methods

#### TaskValidator.**init**

```python
__init__(self: Any, schema_path: Any)
```

Initialize validator with schema.

**Parameters**:

- `schema_path`: Path to JSON Schema file (defaults to schemas/task-input.schema.json)

---

#### TaskValidator.validate

```python
validate(self: Any, task: dict[(str, Any)])
```

Validate a task dictionary.

**Parameters**:

- `task`: Task dictionary to validate

**Returns**: ValidationResult with validation status and errors

---

#### TaskValidator.validate_file

```python
validate_file(self: Any, file_path: Path)
```

Validate a task file.

**Parameters**:

- `file_path`: Path to task file

**Returns**: ValidationResult with validation status and errors

---

---

## ValidationError

Single validation error.

---

## ValidationResult

Task validation result.

### Methods

#### ValidationResult.format_errors

```python
format_errors(self: Any)
```

Format errors for display.

---

---

## format_errors

```python
format_errors(self: Any)
```

Format errors for display.

---

## validate

```python
validate(self: Any, task: dict[(str, Any)])
```

Validate a task dictionary.

**Parameters**:

- `task`: Task dictionary to validate

**Returns**: ValidationResult with validation status and errors

---

## validate_file

```python
validate_file(self: Any, file_path: Path)
```

Validate a task file.

**Parameters**:

- `file_path`: Path to task file

**Returns**: ValidationResult with validation status and errors

---

## validate_task

```python
validate_task(task: dict[(str, Any)], schema_path: Any)
```

Validate a task dictionary.

Convenience function that creates a validator and validates.

**Parameters**:

- `task`: Task dictionary to validate
- `schema_path`: Optional path to schema file

**Returns**: ValidationResult

---

## validate_task_file

```python
validate_task_file(file_path: Path, schema_path: Any)
```

Validate a task file.

Convenience function that creates a validator and validates.

**Parameters**:

- `file_path`: Path to task file
- `schema_path`: Optional path to schema file

**Returns**: ValidationResult

---
