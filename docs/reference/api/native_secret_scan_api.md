# native_secret_scan API Reference

> **Source**: `src/thegent/governance/native_secret_scan.py`

Native secret scanning integration for the hook-dispatcher binary.

Provides `scan_secrets(content)` which delegates to the
`hook-dispatcher scan-secrets --stdin` subcommand (BKM-07). Falls back to a
pure-Python regex implementation when the binary is not found, so the module
is always functional regardless of whether the Rust toolchain has been
compiled.

Traces to: FR-SEC-001 (secret detection), FR-GOV-006 (native binary integration)

---

## SecretMatch

A single secret detected in content.

---

## scan_secrets

```python
scan_secrets(content: str)
```

Scan _content_ for secrets.

Delegates to the Rust `hook-dispatcher scan-secrets --stdin` binary when
available. Falls back to the pure-Python implementation otherwise.

**Parameters**:

- `content`: Raw text (file content or diff) to inspect.

**Returns**: A list of :class:`SecretMatch` objects. Empty list means no secrets
were detected.

---

## scan_secrets_file

```python
scan_secrets_file(path: Any)
```

Convenience wrapper: read _path_ and call :func:`scan_secrets`.

**Parameters**:

- `path`: Path to the file to scan.

**Returns**: List of :class:`SecretMatch` objects.

**Raises**:

- `OSError`: If the file cannot be read.

---
