# errors API Reference

> **Source**: `src/thegent/errors.py`

Production error handling framework for thegent.

---

## ConfigError

Raised when there is a configuration-related failure.

**Inherits from**: `ThegentError`

**Method Resolution Order**: `ConfigError -> ThegentError`

### Methods

#### ConfigError.**init**

```python
__init__(self: Any, message: str, remediation_hint: Any)
```

---

---

## MCPError

Raised when an MCP-related failure occurs.

**Inherits from**: `ThegentError`

**Method Resolution Order**: `MCPError -> ThegentError`

### Methods

#### MCPError.**init**

```python
__init__(self: Any, message: str, remediation_hint: Any)
```

---

---

## ProviderError

Raised when an AI provider (Anthropic, Google, etc.) returns an error.

**Inherits from**: `ThegentError`

**Method Resolution Order**: `ProviderError -> ThegentError`

### Methods

#### ProviderError.**init**

```python
__init__(self: Any, message: str, remediation_hint: Any)
```

---

---

## ThegentError

Base class for all errors in thegent.

**Inherits from**: `Exception`

### Methods

#### ThegentError.**init**

```python
__init__(self: Any, message: str, remediation_hint: Any)
```

---

---

## get_hint_for_message

```python
get_hint_for_message(message: str)
```

Try to find a predefined hint for a given error message.

---

## get_install_hint

```python
get_install_hint(tool: str)
```

Get platform-specific installation hint for a missing tool.

---

## print_error

```python
print_error(message: str, hint: Any, console: Any)
```

Print a formatted error message with an optional remediation hint.

**Parameters**:

- `message`: The error message to display.
- `hint`: An optional hint on how to fix the error.
- `console`: A Rich console object (optional).

---
