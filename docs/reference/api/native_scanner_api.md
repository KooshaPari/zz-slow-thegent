# native_scanner API Reference

> **Source**: `src/thegent/governance/native_scanner.py`

Native governance scanner (obfuscated triggers, Rust built).

---

## NativeGovernanceScanner

Native governance scanner with obfuscated triggers.

### Methods

#### NativeGovernanceScanner.**init**

```python
__init__(self: Any)
```

Initialize native governance scanner.

---

#### NativeGovernanceScanner.add_trigger

```python
add_trigger(self: Any, trigger: str, obfuscated: bool)
```

Add a trigger pattern.

**Parameters**:

- `trigger`: Trigger pattern
- `obfuscated`: Whether pattern is obfuscated

---

#### NativeGovernanceScanner.scan

```python
scan(self: Any, content: str)
```

Scan content for governance violations.

**Parameters**:

- `content`: Content to scan

**Returns**: Scan results

---

---

## add_trigger

```python
add_trigger(self: Any, trigger: str, obfuscated: bool)
```

Add a trigger pattern.

**Parameters**:

- `trigger`: Trigger pattern
- `obfuscated`: Whether pattern is obfuscated

---

## scan

```python
scan(self: Any, content: str)
```

Scan content for governance violations.

**Parameters**:

- `content`: Content to scan

**Returns**: Scan results

---
