# Wave-2 Agent E Report (2026-02-21)

Scope executed: `WL-121`, `WL-123`, `WL-124`, `WL-125`, `WL-126`

## Completed Slices

### WL-121 — thegent-core Boundary Spec and Ownership Map

- Completed code slice: refactored `scripts/check_thegent_core_boundary.py` from regex scanning to AST-based import parsing.
- Added policy support for both allow-list and block-list imports from `config/thegent_core_boundary.toml`.
- Added deterministic CLI args (`--core-dir`, `--config`) for targeted runs.
- Added tests: `tests/test_wl121_core_boundary_checker.py` (allowed imports, blocked/disallowed imports, relative-import behavior).
- Updated plan doc with wave-2 completion details.

### WL-123 — Retire Deprecated Quality Aliases

- Completed unblock slice: added `scripts/check_deprecated_quality_aliases.py` as a deterministic pre-removal audit tool for Taskfile alias inventory.
- Tool supports staged enforcement (`--strict`) for post-WL-122 removal gating.
- Added tests: `tests/test_wl123_deprecated_quality_aliases.py`.
- Updated plan doc with wave-2 unblock details.

### WL-124 — Monolith Split: `src/thegent/cli/commands/cli.py`

- Completed unblock slice: added monolith baseline inventory via `scripts/collect_wl_monolith_baselines.py`.
- Captured current baseline artifact at `.thegent/agent-batch/wave2-monolith-baseline.json`.
- Updated plan doc with wave-2 dependency-unblock command and baseline usage.

### WL-125 — Monolith Split: `src/thegent/cli/commands/impl.py`

- Completed unblock slice: included `impl.py` metrics in shared monolith baseline collector/artifact.
- Baseline now captures line/function/class/async counts for extraction checkpointing.
- Updated plan doc with wave-2 dependency-unblock details.

### WL-126 — Monolith Split: `src/thegent/mcp/server.py`

- Completed unblock slice: included `server.py` metrics in shared monolith baseline collector/artifact.
- Baseline now captures server extraction complexity signals for modular split planning.
- Updated plan doc with wave-2 dependency-unblock details.

## Validation

Commands run:

- `python -m py_compile scripts/check_thegent_core_boundary.py scripts/check_deprecated_quality_aliases.py scripts/collect_wl_monolith_baselines.py` (pass)
- `python scripts/check_thegent_core_boundary.py` (pass)
- `python scripts/check_deprecated_quality_aliases.py --format text` (pass; reports baseline deprecated alias inventory)
- `python scripts/collect_wl_monolith_baselines.py --format json --out .thegent/agent-batch/wave2-monolith-baseline.json` (pass)
- `uv run pytest -q tests/test_wl121_core_boundary_checker.py` (pass)
- `uv run pytest -q tests/test_wl123_deprecated_quality_aliases.py` (pass)
- `uv run pytest -q tests/test_wl124_125_126_monolith_baselines.py` (pass)

## Blockers

- `WL-123`: full alias retirement remains blocked by `WL-122` canonical quality gate parity (this wave delivered pre-removal audit + strict-mode gate tooling).
- `WL-124`: full monolith extraction remains blocked by `WL-121` completion at architecture level; this wave delivered measured baseline and plan-level unblock sequencing.
- `WL-125`: full monolith extraction remains blocked by `WL-121`; this wave delivered measured baseline and dependency-unblock artifact.
- `WL-126`: full monolith extraction remains blocked by `WL-121`; this wave delivered measured baseline and dependency-unblock artifact.

## Exact Files Touched

- `.thegent/agent-batch/wave2-agent-e.md`
- `.thegent/agent-batch/wave2-monolith-baseline.json`
- `docs/plans/WL-121-THEGENT-CORE-BOUNDARY-SPEC-AND-OWNERSHIP-MAP.md`
- `docs/plans/WL-123-RETIRE-DEPRECATED-QUALITY-ALIASES-PLAN.md`
- `docs/plans/WL-124-CLI-COMMANDS-CLI-PY-MONOLITH-SPLIT-PLAN.md`
- `docs/plans/WL-125-CLI-COMMANDS-IMPL-PY-MONOLITH-SPLIT-PLAN.md`
- `docs/plans/WL-126-MCP-SERVER-PY-MONOLITH-SPLIT-PLAN.md`
- `scripts/check_thegent_core_boundary.py`
- `scripts/check_deprecated_quality_aliases.py`
- `scripts/collect_wl_monolith_baselines.py`
- `tests/test_wl121_core_boundary_checker.py`
- `tests/test_wl123_deprecated_quality_aliases.py`
- `tests/test_wl124_125_126_monolith_baselines.py`
