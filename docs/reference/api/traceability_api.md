# traceability API Reference

> **Source**: `src/thegent/verification/traceability.py`

WP-25003: Automated Spec-to-Code Traceability.

Scans source code and tests for FR-ID and WP-ID tags to ensure spec adherence.
Provides a coverage report mapping requirements to implementation artifacts.

---

## TraceabilityAuditor

Audits code and specs for traceability links.

### Methods

#### TraceabilityAuditor.**init**

```python
__init__(self: Any, root_dir: Path)
```

---

#### TraceabilityAuditor.audit

```python
audit(self: Any, expected_ids: list[str])
```

Scan the project for implementation of expected IDs.

---

#### TraceabilityAuditor.generate_markdown_report

```python
generate_markdown_report(self: Any, report: TraceabilityReport)
```

Format the traceability report as Markdown.

---

---

## TraceabilityReport

Result of a traceability audit.

**Inherits from**: `BaseModel`

---

## audit

```python
audit(self: Any, expected_ids: list[str])
```

Scan the project for implementation of expected IDs.

---

## generate_markdown_report

```python
generate_markdown_report(self: Any, report: TraceabilityReport)
```

Format the traceability report as Markdown.

---
