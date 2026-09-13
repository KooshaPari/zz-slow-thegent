# prewarm_report API Reference

> **Source**: `src/thegent/hooks/prewarm_report.py`

Implement prewarm and report subcommands (caching + JSON reports).

---

## PrewarmReportSubcommands

Prewarm and report subcommands.

### Methods

#### PrewarmReportSubcommands.**init**

```python
__init__(self: Any, cache_dir: Any)
```

Initialize prewarm/report.

**Parameters**:

- `cache_dir`: Cache directory

---

#### PrewarmReportSubcommands.prewarm

```python
prewarm(self: Any, targets: list[str])
```

Prewarm cache for targets.

**Parameters**:

- `targets`: List of targets to prewarm

**Returns**: Prewarm results

---

#### PrewarmReportSubcommands.report

```python
report(self: Any, output_file: Any)
```

Generate JSON report.

**Parameters**:

- `output_file`: Output file path

**Returns**: Path to report file

---

---

## prewarm

```python
prewarm(self: Any, targets: list[str])
```

Prewarm cache for targets.

**Parameters**:

- `targets`: List of targets to prewarm

**Returns**: Prewarm results

---

## report

```python
report(self: Any, output_file: Any)
```

Generate JSON report.

**Parameters**:

- `output_file`: Output file path

**Returns**: Path to report file

---
