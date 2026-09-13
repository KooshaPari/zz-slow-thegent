# enhanced_errors API Reference

> **Source**: `src/thegent/infra/enhanced_errors.py`

Enhanced error handling with actionable context and recovery suggestions.

This module provides utilities for creating rich, actionable error messages
that help users understand what went wrong, why it happened, and how to fix it.

---

## ConfigurationError

Error related to configuration issues.

**Inherits from**: `EnhancedError`

**Method Resolution Order**: `ConfigurationError -> EnhancedError`

---

## DependencyError

Error related to missing or incompatible dependencies.

**Inherits from**: `EnhancedError`

**Method Resolution Order**: `DependencyError -> EnhancedError`

---

## EnhancedError

Base exception class with enhanced error reporting.

**Inherits from**: `Exception`

### Methods

#### EnhancedError.**init**

```python
__init__(self: Any, message: str, context: Any, cause: Any)
```

---

#### EnhancedError.display

```python
display(self: Any)
```

Display the error with rich formatting.

---

---

## ErrorContext

Rich context for error reporting.

### Methods

---

## NetworkError

Error related to network connectivity.

**Inherits from**: `EnhancedError`

**Method Resolution Order**: `NetworkError -> EnhancedError`

---

## RuntimeError

Error related to runtime selection or execution.

**Inherits from**: `EnhancedError`

**Method Resolution Order**: `RuntimeError -> EnhancedError`

---

## create_config_error

```python
create_config_error(message: str, config_file: Path, suggestion: Any)
```

Create a configuration error with context.

---

## create_dependency_error

```python
create_dependency_error(message: str, dependency: str, install_command: Any)
```

Create a dependency error with context.

---

## create_network_error

```python
create_network_error(message: str, endpoint: Any, suggestion: Any)
```

Create a network error with context.

---

## create_runtime_error

```python
create_runtime_error(message: str, runtime: str, available_runtimes: list[str], suggestion: Any)
```

Create a runtime error with context.

---

## display

```python
display(self: Any)
```

Display the error with rich formatting.

---

## error_report

```python
error_report(error: Exception, include_traceback: bool)
```

Generate a detailed error report for bug reporting.

---

## format_error_with_context

```python
format_error_with_context(error: Exception, context: Any)
```

Format and display an error with rich context.

---
