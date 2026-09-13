# native_governance_scan API Reference

> **Source**: `src/thegent/governance/native_governance_scan.py`

Native governance scanning integration for the hook-dispatcher binary.

Provides `NativeGovernanceScanner` which delegates to the
`hook-dispatcher governance` subcommand (BKM-11). Falls back to a
pure-Python regex implementation when the binary is not found, so the module
is always functional regardless of whether the Rust toolchain has been
compiled.

Traces to: FR-GOV-007 (governance violation detection), FR-GOV-006 (native binary integration)

---

## GovernanceViolation

A single governance violation detected in source content.

---

## NativeGovernanceScanner

Governance scanner that uses the Rust hook-dispatcher binary when available.

Falls back to a pure-Python implementation when the binary is absent or
returns an error, ensuring the scanner is always operational.

Example::

    scanner = NativeGovernanceScanner()
    violations = scanner.scan_file(Path("src/foo.py"))
    for v in violations:
        print(f"  [{v.severity}] {v.rule} at line {v.line}: {v.message}")

### Methods

#### NativeGovernanceScanner.check_contract

```python
check_contract(self: Any, contract_id: str, path: Path)
```

Check a file against a specific governance contract.

**Parameters**:

- `contract_id`: Contract identifier (e.g. `"P2-PRIVACY"`).
- `path`: Path to the file to check.

**Returns**: List of :class:`GovernanceViolation` objects relevant to the
specified contract. Empty list means no violations.

---

#### NativeGovernanceScanner.check_contract_content

```python
check_contract_content(self: Any, contract_id: str, content: str)
```

Check raw _content_ against a specific governance contract.

**Parameters**:

- `contract_id`: Contract identifier (e.g. `"P2-PRIVACY"`).
- `content`: Raw text to inspect.

**Returns**: List of :class:`GovernanceViolation` objects.

---

#### NativeGovernanceScanner.scan_content

```python
scan_content(self: Any, content: str)
```

Scan raw _content_ for governance violations.

Delegates to the Rust binary when available; falls back to Python
otherwise.

**Parameters**:

- `content`: Raw text to inspect.

**Returns**: List of :class:`GovernanceViolation` objects.

---

#### NativeGovernanceScanner.scan_file

```python
scan_file(self: Any, path: Path)
```

Scan a single file for governance violations.

**Parameters**:

- `path`: Path to the file to scan.

**Returns**: List of :class:`GovernanceViolation` objects. Empty list means
no violations were detected.

---

---

## check_contract

```python
check_contract(self: Any, contract_id: str, path: Path)
```

Check a file against a specific governance contract.

**Parameters**:

- `contract_id`: Contract identifier (e.g. `"P2-PRIVACY"`).
- `path`: Path to the file to check.

**Returns**: List of :class:`GovernanceViolation` objects relevant to the
specified contract. Empty list means no violations.

**Raises**:

- `OSError`: If the file cannot be read.

---

## check_contract_content

```python
check_contract_content(self: Any, contract_id: str, content: str)
```

Check raw _content_ against a specific governance contract.

**Parameters**:

- `contract_id`: Contract identifier (e.g. `"P2-PRIVACY"`).
- `content`: Raw text to inspect.

**Returns**: List of :class:`GovernanceViolation` objects.

---

## scan_content

```python
scan_content(self: Any, content: str)
```

Scan raw _content_ for governance violations.

Delegates to the Rust binary when available; falls back to Python
otherwise.

**Parameters**:

- `content`: Raw text to inspect.

**Returns**: List of :class:`GovernanceViolation` objects.

---

## scan_file

```python
scan_file(self: Any, path: Path)
```

Scan a single file for governance violations.

**Parameters**:

- `path`: Path to the file to scan.

**Returns**: List of :class:`GovernanceViolation` objects. Empty list means
no violations were detected.

**Raises**:

- `OSError`: If the file cannot be read.

---
