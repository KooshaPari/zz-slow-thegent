# config_validator API Reference

> **Source**: `src/thegent/infra/config_validator.py`

Configuration validation for thegent.

This module provides utilities for validating configuration files and
settings before they are used.

---

## ConfigValidator

Configuration validator.

### Methods

#### ConfigValidator.**init**

```python
__init__(self: Any, config_path: Any)
```

Initialize the validator.

**Parameters**:

- `config_path`: Path to .env file (default: .env in current directory)

---

#### ConfigValidator.display_results

```python
display_results(self: Any)
```

Display validation results.

---

#### ConfigValidator.validate

```python
validate(self: Any)
```

Validate configuration.

**Returns**: True if configuration is valid, False otherwise

---

---

## display_results

```python
display_results(self: Any)
```

Display validation results.

---

## validate

```python
validate(self: Any)
```

Validate configuration.

**Returns**: True if configuration is valid, False otherwise

---

## validate_config

```python
validate_config(config_path: Any)
```

Validate configuration file.

**Parameters**:

- `config_path`: Path to .env file (default: .env in current directory)

**Returns**: True if configuration is valid, False otherwise

---
