# System Audit Framework

`thegent audit` detects drift between declared configuration and the actual on-disk state of the project.

## Overview

The audit framework inspects four categories:

| Category | What it checks |
|---|---|
| **hooks** | Hooks registered in `hooks/hook-config.yaml` versus `.sh` files on disk |
| **agents** | Agent `.md` persona files in `agents/` versus optional `bounded-contexts.yaml` registry |
| **config** | `ThegentSettings` field defaults versus actual `THGENT_*` environment variables |
| **dependencies** | `pyproject.toml` declared dependencies versus installed packages |

## Quick Start

```bash
# Full audit (all categories)
thegent audit

# Machine-readable JSON output
thegent audit --json

# Show fix suggestions for every issue
thegent audit --fix

# Restrict to one category
thegent audit --category hooks
thegent audit --category agents
thegent audit --category config
thegent audit --category dependencies

# Write JSON report to a file
thegent audit --json --out /tmp/audit-report.json
```

Exit code is `0` when no drift is detected, `1` when any issues are found.

## Status Values

| Status | Meaning |
|---|---|
| `ok` | Check passed; declared state matches actual state |
| `missing` | Declared entry has no corresponding file or resource |
| `unexpected` | Resource exists on disk but is not declared |
| `drift` | Declared specifier does not match actual value (e.g., wrong version) |
| `warn` | Non-critical issue; attention recommended |
| `error` | Audit could not complete the check (e.g., parse failure) |

## Category Details

### hooks

Compares the `hooks:` section of `hooks/hook-config.yaml` against `.sh` scripts found directly in the `hooks/` directory.

- **MISSING**: a hook is declared in YAML but the `.sh` file is absent from disk.
- **UNEXPECTED**: a `.sh` file exists in `hooks/` but is not declared in the YAML.
- **OK**: hook is declared and the script is present.

Fix suggestions are automatically generated for `MISSING` and `UNEXPECTED` results.

### agents

Scans `agents/` for `.md` persona files and cross-checks against `agents/bounded-contexts.yaml` when present.

- **MISSING**: `agents/` directory does not exist, or a name in `bounded-contexts.yaml` has no corresponding `.md` file.
- **WARN**: `agents/` is empty, or a `.md` file has no content.
- **OK**: agent file is non-empty and present.

### config

Inspects every field declared in `ThegentSettings` (from `src/thegent/config.py`) and the corresponding `THGENT_*` environment variable.

- **OK**: field has either an explicit env-var override or uses its default.
- **UNEXPECTED**: a `THGENT_*` env var is set in the environment but is not mapped to any `ThegentSettings` field.

This is useful for detecting leftover environment variables from old configuration.

### dependencies

Reads `[project].dependencies` from `pyproject.toml` and verifies each package against `importlib.metadata` (the installed package set).

- **MISSING**: package is declared but not installed.
- **DRIFT**: package is installed but the version does not satisfy the declared specifier.
- **OK**: package is installed and version satisfies specifier.
- **ERROR**: `pyproject.toml` is missing or has invalid TOML.

Version specifier checking uses the `packaging` library when available, with graceful fallback.

## Programmatic API

```python
from pathlib import Path
from thegent.audit.system_audit import SystemAuditor

auditor = SystemAuditor()  # auto-detects project root
# or: SystemAuditor(project_root=Path("/path/to/project"))

# Run individual categories
hooks_results = auditor.audit_hooks()
agents_results = auditor.audit_agents()
config_results = auditor.audit_config()
deps_results = auditor.audit_dependencies()

# Full audit
report = auditor.run_full_audit()

# Human-readable output
print(auditor.format_report(report))

# JSON export
auditor.export_json(report, Path("audit-report.json"))

# Check for drift
if report.has_drift:
    print("Drift detected!")
    print(report.summary)
```

### AuditResult dataclass

```python
@dataclass
class AuditResult:
    category: str  # "hooks" | "agents" | "config" | "dependencies"
    item: str  # name of the hook, agent, field, or package
    status: AuditStatus  # AuditStatus enum value
    expected: str  # what was expected
    actual: str  # what was found
    fix_suggestion: str  # actionable fix (empty for OK results)
```

### AuditReport dataclass

```python
@dataclass
class AuditReport:
    timestamp: str  # ISO 8601 timestamp
    results: list[AuditResult]  # all results
    summary: dict[str, int]  # per-status counts plus "total"
```

`AuditReport.has_drift` returns `True` when any non-OK result is present.

`AuditReport.to_dict()` and `AuditResult.to_dict()` produce plain dicts suitable for JSON serialization.

## JSON Report Format

```json
{
  "timestamp": "2026-01-01T00:00:00+00:00",
  "summary": {
    "total": 42,
    "ok": 38,
    "missing": 2,
    "unexpected": 1,
    "drift": 1,
    "warn": 0,
    "error": 0
  },
  "results": [
    {
      "category": "hooks",
      "item": "quality-gate",
      "status": "ok",
      "expected": "hooks/quality-gate.sh",
      "actual": "hooks/quality-gate.sh",
      "fix_suggestion": ""
    },
    {
      "category": "dependencies",
      "item": "httpx",
      "status": "drift",
      "expected": "httpx>=0.28.1",
      "actual": "httpx==0.27.0 (requires >=0.28.1)",
      "fix_suggestion": "Run: pip install 'httpx>=0.28.1'"
    }
  ]
}
```

## CI Integration

Run the audit as part of CI to catch drift early:

```yaml
# .github/workflows/audit.yml
- name: System audit
  run: thegent audit --json --out audit-report.json
  continue-on-error: false
```

The command exits with code `1` when any drift is detected, causing the CI step to fail.

## Source Locations

| File | Purpose |
|---|---|
| `src/thegent/audit/__init__.py` | Module public API |
| `src/thegent/audit/system_audit.py` | `AuditResult`, `AuditReport`, `SystemAuditor` |
| `src/thegent/commands/audit.py` | `thegent audit` CLI command (typer app) |
| `tests/test_system_audit.py` | 34 unit tests (FR-AUDIT-001 through FR-AUDIT-020) |
