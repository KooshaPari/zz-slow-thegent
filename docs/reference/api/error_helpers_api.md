# error_helpers API Reference

> **Source**: `src/thegent/utils/error_helpers.py`

Actionable error messages with suggested fixes.

---

## ActionableError

Error with actionable suggestions for fixing it.

**Inherits from**: `Exception`

### Methods

#### ActionableError.**init**

```python
__init__(self: Any, message: str, suggestion: Any, docs_url: Any, context: Any)
```

---

---

## handle_error_actionable

```python
handle_error_actionable(error: Exception, custom_message: Any, suggestion: Any, docs_url: Any)
```

Wrap an error in an ActionableError.

**Parameters**:

- `error`: Original exception
- `custom_message`: Optional custom message
- `suggestion`: Optional suggestion
- `docs_url`: Optional docs URL

**Returns**: ActionableError instance

---
