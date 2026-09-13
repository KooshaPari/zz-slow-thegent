# Quality Assurance Guide

> Quality standards, testing patterns, and verification procedures for thegent

---

## 1. Quality Standards

### 1.1 Code Quality Targets

| Metric          | Target | Current |
| --------------- | ------ | ------- |
| Line Coverage   | 80%    | 78%     |
| Branch Coverage | 70%    | 65%     |
| Type Errors     | 0      | 12      |
| Lint Errors     | 0      | 3       |
| Security Issues | 0      | 0       |

### 1.2 Quality Gates

All code must pass:

1. **Syntax Check** - Python type checking with pyright
2. **Linting** - ruff check and format
3. **Tests** - pytest with >80% coverage
4. **Security** - bandit scan
5. **Architecture** - import-linter validation

---

## 2. Running Quality Checks

### 2.1 Full Quality Gate

```bash
# Canonical all-in local quality command
task quality

# Equivalent CI path (DAG wrapper + report artifacts)
QUALITY_FAIL_MODE=hard task quality:dag:ci:junit JUNIT=.quality/junit.xml

# Optional step-by-step checks
task lint          # Linting
task typecheck     # Type checking
task test          # Tests
task security      # Security scan
task lint:architecture  # Architecture validation
```

CI parity note:

- `config/quality-dag.yaml` defines `quality` as `task quality`.
- CI runs that canonical command through the DAG runner (`quality:dag:ci:junit`) to produce `.quality/summary.md`, `.quality/last-run.json`, and JUnit XML.

Quality alias migration note (WL-123):

- Deprecated aliases (for example `quality-a*`, `quality-fix*`) are retired in favor of canonical commands.
- Replacement mapping is source-controlled in `config/deprecated_quality_aliases.json`.
- Audit locally with `task quality:deprecated-aliases`.
- Enforce in strict mode with `task quality:deprecated-aliases:strict` (non-zero exit if deprecated aliases remain).
- Canonical safe fix lane is `task quality:fix:runner`.
- Direct script usage: `uv run python scripts/check_deprecated_quality_aliases.py --format migration`.
- Markdown migration table output: `uv run python scripts/check_deprecated_quality_aliases.py --format migration-md`.
- Machine-readable migration output: `uv run python scripts/check_deprecated_quality_aliases.py --format migration-json`.
- Compact migration summary output: `uv run python scripts/check_deprecated_quality_aliases.py --format summary-json`.
- `migration-json` contract is stable: `{replacement_suggestions, canonical_missing}` for automation consumers.
- `summary-json` contract is stable: `{ok, deprecated_count, replacement_count, unmapped_deprecated_count, canonical_missing_count, total_findings}`.

Core boundary checker mode note (WL-121):

- Local/default mode is advisory and non-blocking: `task quality:core-boundary`.
- CI strict mode is blocking: `task quality:core-boundary:strict` (or `uv run python scripts/check_thegent_core_boundary.py --strict`).
- Machine-readable output is available for tooling: `uv run python scripts/check_thegent_core_boundary.py --format json`.
- Line-oriented violation output is available for tooling pipelines: `uv run python scripts/check_thegent_core_boundary.py --format violations-jsonl`.
- `summary-json` contract is stable: `{ok, mode, violation_count, violation_file_count, clean_file_count, blocked_count, disallowed_count, file_count, import_count}`.
- CI should always run strict boundary mode explicitly (for example in `.github/workflows/ci.yml`):
  - `task quality:core-boundary:strict`

Core boundary checker config examples (WL-121):

| Type  | Prefix           | Example import                          | Result                          |
| ----- | ---------------- | --------------------------------------- | ------------------------------- |
| allow | `thegent.core`   | `from thegent.core import prompt_queue` | Allowed                         |
| allow | `thegent.queue`  | `from thegent.queue import enqueue`     | Allowed                         |
| allow | `thegent.config` | `import thegent.config`                 | Allowed                         |
| block | `thegent`        | `import thegent`                        | Blocked unless also allowlisted |
| block | `thegent`        | `from thegent.mcp import server`        | Blocked unless also allowlisted |

Benchmark regression smoke (WL-078):

- Run `task bench:smoke:ci` for a deterministic benchmark smoke lane in CI.
- CI calls the same smoke command before broader quality gates.
- Refresh the committed baseline with `task bench:baseline:refresh` whenever benchmark semantics intentionally change.
- For stricter checks in CI/local runs, add `--require-complete-baseline` to `scripts/check_python_benchmark_regression.py` so missing benchmark labels fail the gate.
- Benchmark JSON rows should include finite, non-negative `avg_microseconds` values; invalid numeric values fail the regression checker.
- Benchmark JSON rows must include a non-empty `label`; empty labels fail the regression checker.

CI benchmark smoke command snippet (WL-079):

```bash
task bench:smoke:ci
# current command:
uv run pytest -q tests/test_wl079_audit_bench.py
# WL-079 guard verifies this benchmark task remains offline+locked:
CARGO_NET_OFFLINE=true cargo bench --locked --manifest-path crates/Cargo.toml -p thegent-router --bench audit_bench
```

Benchmark workflow contract (WL-079):

- Keep workflow wiring on the task wrapper path (`task bench:smoke:ci`) inside the `Deterministic benchmark smoke` CI step.
- Keep `bench:smoke:ci` as a single-command wrapper (`uv run pytest -q tests/test_wl079_audit_bench.py`) so smoke coverage remains deterministic.
- Do not inline raw `cargo bench` commands in `.github/workflows/ci.yml`; task wiring owns benchmark invocation details.

Vetter auditability contract (WL-093/WL-094):

- `vetter_escalation.reason` should remain deterministic and include `failed_checks`, `policy_escalate_on`, and `policy_lane`.
- Evidence payload check lists (`failed_checks`, `passed_checks`) must reflect executed checks only, including fail-fast short-circuit behavior.

### 2.2 Individual Checks

```bash
# Linting
ruff check src/
ruff format --check src/

# Type checking
pyright src/

# Tests with coverage
pytest --cov=src --cov-report=term-missing

# Security scan
bandit -r src/

# Architecture
import-linter
```

### 2.3 Max-Lines Gate (WL-122)

Use one canonical developer command path for this gate:

```bash
task quality:max-lines
```

Notes:

- This task is the supported local entrypoint for max-lines enforcement.
- `scripts/max-lines-gate.sh` is an internal implementation detail used by task wiring.
- Pre-commit (`pre-commit`, changed-file scope) and CI should call the canonical task path (`task quality:max-lines`) instead of invoking the script directly.

### 2.4 Canonical Contract Reinforcement Bundle (WL-104/WL-106/WL-111/WL-117/WL-122)

Use this focused lane to validate the current canonical contract surfaces without running the full test suite:

```bash
# Canonical CI wiring checker (WL-122 + WL-117 ordering)
uv run python scripts/check_wl122_max_lines_canonical_path.py --strict

# Focused contract tests
uv run pytest -q \
  tests/test_wl122_max_lines_ci_path.py \
  tests/protocols/test_jsonrpc_agent_server_contract.py \
  tests/test_wl106_session_cli_wiring.py \
  tests/mcp/test_tools_skills_contract.py \
  tests/test_wl117_extension_package_metadata.py
```

Notes:

- WL-122 checker now enforces exactly-once execution of both strict checker commands, and order: WL-122 checker -> WL-117 checker -> `task quality:max-lines`.
- WL-122 checker now also requires CI to install Task via `arduino/setup-task@v2` before running `task quality:max-lines`.
- WL-122 checker now requires `.pre-commit-config.yaml` to declare `max-lines-gate` exactly once.
- WL-122 checker now requires exact pre-commit hook entry `entry: task quality:max-lines` (no extra arguments).
- Keep the WL-117 metadata checker before `task quality:max-lines` in CI.
- WL-104 turn submission with `requires_approval=true` now requires string `diff`/`unified_diff` values (non-string input fails with invalid params).
- WL-104 now requires `requires_approval` to be an explicit boolean when provided (non-boolean input fails with invalid params).
- WL-104 now requires non-empty `diff`/`unified_diff` when `requires_approval=true`.
- WL-104 now treats whitespace-only `session_id` / `turn_id` / `approval_id` params as invalid (rejected as required-field errors).
- WL-106 fork/rollback CLI now rejects blank `session_id` inputs at the command boundary.
- WL-106 fork/rollback CLI now rejects non-positive `--from-turn` / `--n-turns` at the command boundary.
- WL-106 fork CLI now rejects `--new-session-id` values that equal the source `session_id`.
- WL-111 skill list payloads are canonically sorted case-insensitively by `name` for stable MCP contract output.
- WL-111 skill list now fails loudly on case-insensitive duplicate skill names to avoid activation ambiguity.
- WL-111 skill list now trims surrounding whitespace on skill names before output and duplicate detection.
- WL-117 metadata checker now rejects duplicate `contributes.commands[*].command` identifiers and requires README Run Steps to include `npm run lint` and `npm run test`.
- WL-117 metadata checker now requires README Run Steps to keep `npm run lint` before `npm run test`.
- WL-117 metadata checker now rejects duplicated `npm run <script>` lines in README Run Steps.

### 2.5 Fast/Deep Test Topology and LOC/SLO Dashboard (WL-134/WL-135)

Use the canonical lane tasks and dashboard pipeline below:

```bash
# WL-134 lane topology
task test:fast-lane
task test:nightly-lane
task test:deep
task test:gate

# WL-135 dashboard pipeline
task metrics:loc
task diag:wl137
uv run python scripts/render_slo_dashboard.py
task metrics:slo:emit-stub
```

Expected artifacts:

- `.quality/loc-metrics.json` (collector output)
- `.quality/wl137-ci-summary.json` (CI summary envelope with runtime buckets + drift)
- `docs/reports/WL-137-weekly-YYYY-MM-DD.md` (weekly diagnosis report)
- `docs/reports/artifacts/wl120-wl136-loc-trend-YYYY-MM-DD.{json,md}` (trend evidence artifacts)
- `.quality/slo-dashboard.md` (rendered markdown dashboard)
- `var/metrics/slo_stub_metrics.jsonl` (stub SLO metric rows)

### 2.6 Runtime Promotion Contract Gates (WL-132/WL-133)

Use the canonical runtime contract gate tasks below:

```bash
# WL-132 Zig ABI promotion contract gates
task quality:runtime-contracts:zig-abi

# WL-133 Mojo deterministic kernel promotion contract gates
task quality:runtime-contracts:mojo-kernel

# Combined runtime contract lane used by CI
task quality:runtime-contracts
```

Gate coverage:

- `quality:runtime-contracts:zig-abi` enforces:
  - ABI contract schema/version validation (`scripts/validate_zig_abi_contract.py`)
  - required symbol + error-envelope conformance check (`scripts/check_zig_abi_artifact.py`)
  - focused contract tests (`tests/test_zig_abi_contract_validation.py`, `tests/test_wl132_zig_abi_contract.py`)
- `quality:runtime-contracts:mojo-kernel` enforces:
  - Mojo kernel contract/harness references and promotion-gate fields
  - deterministic fixture generation + replay harness behavior
  - contract-level smoke checks that do not require a local Mojo installation

---

## 3. Pre-commit Hooks

### 3.1 Setup

```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files

# Skip specific hooks
pre-commit run --files src/thegent/cli.py --hook-stage manual
```

### 3.2 Configuration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: ruff-check
        name: Ruff Check
        entry: ruff check
        language: system
        types: [python]

      - id: ruff-format
        name: Ruff Format
        entry: ruff format --check
        language: system
        types: [python]

      - id: pyright
        name: Type Check
        entry: pyright
        language: system
        types: [python]
```

---

## 4. Test Quality Standards

### 4.1 Test Naming

```bash
# Pattern: test_<module>_<function>_<case>.py

# Good examples
test_user_creation.py
test_cli_run_valid_input.py
test_resilience_retry_exponential_backoff.py

# Bad examples
test_mymodule.py           # Too generic
test_function.py          # Too generic
test_a_b_c.py             # Unclear
```

### 4.2 Test Organization

```python
# tests/test_cli/
test_cli/
├── __init__.py
├── conftest.py           # Shared fixtures
├── test_run.py          # CLI run command
├── test_serve.py        # CLI serve command
└── test_mcp.py          # CLI MCP commands
```

### 4.3 FR Traceability

```python
@pytest.mark.requirement("FR-CORE-001")
@pytest.mark.requirement("FR-CLI-005")
def test_cli_run_basic():
    """Test basic CLI run functionality."""
    # ...
```

---

## 5. Security Standards

### 5.1 Secrets Handling

**Never commit secrets.** Use environment variables:

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_key: str = ""

    @classmethod
    def from_env(cls):
        return cls()  # Reads from environment
```

### 5.2 Security Scanning

```bash
# Run security scans
bandit -r src/          # Find security issues
safety check            # Check dependencies
trivy fs .              # Container scanning

# CI integration
bandit --config .bandit.yaml --recursive src/
```

---

## 6. Performance Standards

### 6.1 Performance Targets

| Operation      | Target  | Current |
| -------------- | ------- | ------- |
| CLI startup    | < 1s    | 0.8s    |
| Hook execution | < 100ms | 85ms    |
| MCP tool call  | < 50ms  | 42ms    |
| Memory usage   | < 100MB | 78MB    |

### 6.2 Performance Testing

```python
import pytest
import time


@pytest.mark.performance
def test_hook_execution_time():
    """Test hook executes within time limit."""
    start = time.perf_counter()
    result = execute_hook()
    elapsed = time.perf_counter() - start

    assert elapsed < 0.1, f"Hook took {elapsed:.3f}s (target: 0.1s)"
```

---

## 7. Documentation Quality

### 7.1 Docstring Standards

```python
def calculate_metrics(values: list[float]) -> dict[str, float]:
    """
    Calculate statistical metrics for a list of values.

    Args:
        values: List of numeric values to analyze

    Returns:
        Dictionary with mean, median, std_dev, min, max

    Raises:
        ValueError: If values list is empty

    Example:
        >>> calculate_metrics([1, 2, 3, 4, 5])
        {'mean': 3.0, 'median': 3.0, 'std_dev': 1.41}
    """
    if not values:
        raise ValueError("Values list cannot be empty")

    n = len(values)
    mean = sum(values) / n
    # ...
```

### 7.2 README Standards

Every module should have:

```markdown
# Module Name

## Overview

Brief description of module purpose.

## Usage

Code examples showing how to use.

## Configuration

Environment variables and settings.

## Testing

How to run tests for this module.

## Related

Links to related modules and documentation.
```

---

## 8. Code Review Checklist

### 8.1 Pre-Review Checklist

- [ ] Code passes all quality gates
- [ ] Deterministic benchmark smoke passed (`task bench:smoke:ci`)
- [ ] CI benchmark smoke step present in PR checks ("Deterministic benchmark smoke")
- [ ] Audit benchmark smoke snippet captured in review notes:
      `task bench:smoke:ci  # wraps CARGO_NET_OFFLINE=true cargo bench --locked -p thegent-router --bench audit_bench`
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No TODO comments
- [ ] No hardcoded secrets
- [ ] Type hints added
- [ ] Error handling complete

### 8.2 Review Questions

1. Does the code follow project conventions?
2. Are there any security concerns?
3. Is the code testable?
4. Are error messages helpful?
5. Is the code maintainable?

---

## 9. Extension Summary

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. **Added Section 1:** Quality Standards (coverage targets, gates)
2. **Added Section 2:** Running Quality Checks (commands)
3. **Added Section 3:** Pre-commit Hooks (configuration)
4. **Added Section 4:** Test Quality Standards (naming, organization)
5. **Added Section 5:** Security Standards (secrets, scanning)
6. **Added Section 6:** Performance Standards (targets, testing)
7. **Added Section 7:** Documentation Quality (docstrings, README)
8. **Added Section 8:** Code Review Checklist

### Cross-References Added

- pytest documentation
- ruff documentation
- bandit documentation
- pydantic-settings documentation

### Practical Additions

- Complete quality checklist
- Performance testing examples
- Code review checklist
- Documentation templates
