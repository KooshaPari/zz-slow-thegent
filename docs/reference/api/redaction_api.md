# redaction API Reference

> **Source**: `src/thegent/governance/redaction.py`

Automatic PII and secret redaction for support mode and compliance (WP-15003).

---

## PIIRedactor

Redacts PII and secrets from text outputs.

### Methods

#### PIIRedactor.**init**

```python
__init__(self: Any, custom_patterns: Any)
```

---

#### PIIRedactor.contains_pii

```python
contains_pii(self: Any, text: str)
```

Check if text contains any PII or secrets.

---

#### PIIRedactor.redact

```python
redact(self: Any, text: str, mode: str)
```

Redact PII and secrets from text.

**Parameters**:

- `text`: Input text to redact
- `mode`: Redaction mode ("support", "audit", "standard")

**Returns**: Redacted text

---

---

## contains_pii

```python
contains_pii(self: Any, text: str)
```

Check if text contains any PII or secrets.

---

## redact

```python
redact(self: Any, text: str, mode: str)
```

Redact PII and secrets from text.

**Parameters**:

- `text`: Input text to redact
- `mode`: Redaction mode ("support", "audit", "standard")

**Returns**: Redacted text

---
