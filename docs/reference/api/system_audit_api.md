# system_audit API Reference

> **Source**: `src/thegent/audit/system_audit.py`

System audit framework: detect drift between declared config and actual state.

This module checks:

- Hooks: registered in hook-config.yaml vs hook scripts on disk
- Agents: agent .md files on disk vs any agent registry
- Config: ThegentSettings fields vs actual environment variables set
- Dependencies: pyproject.toml declared deps vs pip-installed packages

---

## AuditReport

Full audit report produced by SystemAuditor.run_full_audit().

### Methods

#### AuditReport.add_results

```python
add_results(self: Any, results: list[AuditResult])
```

Append results and refresh summary counts.

---

#### AuditReport.has_drift

```python
has_drift(self: Any)
```

True when any non-OK result exists.

---

#### AuditReport.to_dict

```python
to_dict(self: Any)
```

Serialize to plain dict for JSON export.

---

---

## AuditResult

Result of one audit check.

### Methods

#### AuditResult.is_ok

```python
is_ok(self: Any)
```

Return True when no problem detected.

---

#### AuditResult.to_dict

```python
to_dict(self: Any)
```

Serialize to plain dict for JSON export.

---

---

## AuditStatus

Status of a single audit check.

**Inherits from**: `str, Enum`

---

## SystemAuditor

Detects drift between declared configuration and actual on-disk state.

### Methods

#### SystemAuditor.**init**

```python
__init__(self: Any, project_root: Any)
```

---

#### SystemAuditor.audit_agents

```python
audit_agents(self: Any)
```

Verify agent .md files in agents/ are valid and parseable.

Checks:

- agents/ directory exists
- Each .md file is non-empty
- Any agent referenced in bounded-contexts.yaml (if present) is on disk

---

#### SystemAuditor.audit_config

```python
audit_config(self: Any)
```

Compare ThegentSettings field defaults against actual environment.

For each field that has a corresponding THGENT\_\* environment variable
we report whether the env var is set (non-default) or absent (default).
We also flag env vars whose values diverge from the declared default.

---

#### SystemAuditor.audit_dependencies

```python
audit_dependencies(self: Any)
```

Compare pyproject.toml declared dependencies against installed packages.

Uses importlib.metadata to check installed distributions. Reports:

- MISSING: declared but not installed
- OK: present and version satisfies declared specifier
- DRIFT: present but version does not satisfy declared specifier
- WARN: present but specifier cannot be verified

---

#### SystemAuditor.audit_hooks

```python
audit_hooks(self: Any)
```

Compare hooks declared in hook-config.yaml against scripts on disk.

For each hook entry in the config's `hooks:` section we check that a
corresponding `.sh` file exists under `hooks/`. We also flag any
`.sh` files in the hooks directory that are _not_ registered in config.

---

#### SystemAuditor.export_json

```python
export_json(self: Any, report: AuditReport, path: Path)
```

Write machine-readable JSON audit report to _path_.

---

#### SystemAuditor.format_report

```python
format_report(self: Any, report: AuditReport)
```

Return a human-readable text summary of the audit report.

---

#### SystemAuditor.run_full_audit

```python
run_full_audit(self: Any)
```

Run all audit categories and return a combined AuditReport.

---

---

## add_results

```python
add_results(self: Any, results: list[AuditResult])
```

Append results and refresh summary counts.

---

## audit_agents

```python
audit_agents(self: Any)
```

Verify agent .md files in agents/ are valid and parseable.

Checks:

- agents/ directory exists
- Each .md file is non-empty
- Any agent referenced in bounded-contexts.yaml (if present) is on disk

---

## audit_config

```python
audit_config(self: Any)
```

Compare ThegentSettings field defaults against actual environment.

For each field that has a corresponding THGENT\_\* environment variable
we report whether the env var is set (non-default) or absent (default).
We also flag env vars whose values diverge from the declared default.

---

## audit_dependencies

```python
audit_dependencies(self: Any)
```

Compare pyproject.toml declared dependencies against installed packages.

Uses importlib.metadata to check installed distributions. Reports:

- MISSING: declared but not installed
- OK: present and version satisfies declared specifier
- DRIFT: present but version does not satisfy declared specifier
- WARN: present but specifier cannot be verified

---

## audit_hooks

```python
audit_hooks(self: Any)
```

Compare hooks declared in hook-config.yaml against scripts on disk.

For each hook entry in the config's `hooks:` section we check that a
corresponding `.sh` file exists under `hooks/`. We also flag any
`.sh` files in the hooks directory that are _not_ registered in config.

---

## export_json

```python
export_json(self: Any, report: AuditReport, path: Path)
```

Write machine-readable JSON audit report to _path_.

---

## format_report

```python
format_report(self: Any, report: AuditReport)
```

Return a human-readable text summary of the audit report.

---

## has_drift

```python
has_drift(self: Any)
```

True when any non-OK result exists.

---

## is_ok

```python
is_ok(self: Any)
```

Return True when no problem detected.

---

## run_full_audit

```python
run_full_audit(self: Any)
```

Run all audit categories and return a combined AuditReport.

---

## to_dict

```python
to_dict(self: Any)
```

Serialize to plain dict for JSON export.

---
