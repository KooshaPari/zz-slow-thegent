# compliance_reports API Reference

> **Source**: `src/thegent/governance/compliance_reports.py`

Automated compliance reporting.

---

## ComplianceReporter

Generate automated compliance reports.

### Methods

#### ComplianceReporter.**init**

```python
__init__(self: Any)
```

Initialize compliance reporter.

---

#### ComplianceReporter.export_report

```python
export_report(self: Any, compliance_data: dict[(str, Any)], output_path: Path, format: str)
```

Export compliance report to file.

**Parameters**:

- `compliance_data`: Compliance data
- `output_path`: Output file path
- `format`: Report format

**Returns**: Path to exported file

---

#### ComplianceReporter.generate_report

```python
generate_report(self: Any, compliance_data: dict[(str, Any)], format: str)
```

Generate compliance report.

**Parameters**:

- `compliance_data`: Compliance data dictionary
- `format`: Report format (json, markdown, html)

**Returns**: Report content as string

---

---

## export_report

```python
export_report(self: Any, compliance_data: dict[(str, Any)], output_path: Path, format: str)
```

Export compliance report to file.

**Parameters**:

- `compliance_data`: Compliance data
- `output_path`: Output file path
- `format`: Report format

**Returns**: Path to exported file

---

## generate_report

```python
generate_report(self: Any, compliance_data: dict[(str, Any)], format: str)
```

Generate compliance report.

**Parameters**:

- `compliance_data`: Compliance data dictionary
- `format`: Report format (json, markdown, html)

**Returns**: Report content as string

---
