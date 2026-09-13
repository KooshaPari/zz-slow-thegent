# Agent A Batch Status (2026-02-21)

## WL-078

- Status: in-progress
- Done: Added WL-078 regression gate command path and baseline artifact.
- Files changed:
  - `Taskfile.yml`
  - `scripts/check_python_benchmark_regression.py`
  - `benchmarks/baseline.json`
  - `tests/performance/test_python_benchmark_regression.py`
- Validation commands run:
  - `uv run python scripts/check_python_benchmark_regression.py --baseline benchmarks/baseline.json --current benchmarks/baseline.json --max-regression-pct 15`
  - `uv run pytest -q tests/performance/test_python_benchmark_regression.py`

## WL-101

- Status: in-progress
- Done: Implemented SKILL.md-only discovery/load compatibility and fixed markdown resolution bug in discovery.
- Files changed:
  - `src/thegent/skills/discovery.py`
  - `tests/test_unit_skills.py`
- Validation commands run:
  - `uv run python -m py_compile src/thegent/skills/discovery.py`
  - `uv run pytest -q tests/test_unit_skills.py -k "skill_md_only or missing_json or invalid_json"`

## WL-102

- Status: blocked
- Blocker: Full SDK delivery is broad/high-touch for this low-risk batch slice; added implementation-ready plan artifact.
- Files changed:
  - `docs/plans/WL-102-SDK-PUBLIC-API-SLICE-PLAN.md`
- Validation commands run:
  - `uv run python -m py_compile src/thegent/skills/discovery.py src/thegent/mcp/dynamic_tools.py scripts/check_python_benchmark_regression.py`

## WL-103

- Status: blocked
- Blocker: Context compaction requires broader runner integration + token accounting decisions; added implementation-ready plan artifact.
- Files changed:
  - `docs/plans/WL-103-CONTEXT-COMPACTION-SLICE-PLAN.md`
- Validation commands run:
  - `uv run python -m py_compile src/thegent/skills/discovery.py src/thegent/mcp/dynamic_tools.py scripts/check_python_benchmark_regression.py`

## WL-105

- Status: in-progress
- Done: Added isolated `DynamicToolRegistry` primitives for per-session registration, call lifecycle, and tool_call_requested event payload.
- Files changed:
  - `src/thegent/mcp/dynamic_tools.py`
  - `tests/mcp/test_dynamic_tools.py`
- Validation commands run:
  - `uv run python -m py_compile src/thegent/mcp/dynamic_tools.py`
  - `uv run pytest -q tests/mcp/test_dynamic_tools.py`

## Do-Next Loop Notes

- Ran backlog selector equivalent in this checkout: `TERM=dumb thegent plan next --format json`
- Result: `No ready tasks.`
