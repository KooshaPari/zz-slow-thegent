# support API Reference

> **Source**: `src/thegent/governance/support.py`

WP-15005: End-user support mode with automatic PII and secret redaction.

---

## SupportModeSession

Least-privilege session for platform support engineers.

### Methods

#### SupportModeSession.**init**

```python
__init__(self: Any, engineer_id: str)
```

---

#### SupportModeSession.get_view

```python
get_view(self: Any, raw_output: str)
```

Return a redacted view of the system output.

---

---

## SupportRedactor

Automatic redaction of PII and secrets for support mode (WP-15005).

### Methods

#### SupportRedactor.**init**

```python
__init__(self: Any)
```

---

#### SupportRedactor.redact_payload

```python
redact_payload(self: Any, payload: dict[(str, Any)])
```

Recursively redact strings within a nested dictionary payload.

---

#### SupportRedactor.redact_text

```python
redact_text(self: Any, text: str)
```

Apply all redaction patterns to the provided text.

---

---

## get_view

```python
get_view(self: Any, raw_output: str)
```

Return a redacted view of the system output.

---

## redact_payload

```python
redact_payload(self: Any, payload: dict[(str, Any)])
```

Recursively redact strings within a nested dictionary payload.

---

## redact_text

```python
redact_text(self: Any, text: str)
```

Apply all redaction patterns to the provided text.

---
