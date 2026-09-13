# WL-120 Final Report

Date: 2026-02-21
Workstream: WL-120 — Python LOC Reduction Program (Core Boundary + Runtime Split)

## Outcome

- Executed a new monolith-cut extraction wave across CLI impl + MCP server surfaces and reduced all three tracked monolith files.
- WL-120 remains `in_progress` (not `COMPLETED`) because acceptance criteria are still unmet.

## Extraction Wave Delivered

1. `impl.py` DAG delegation cut (W3-B1 slice)

- Replaced duplicated DAG internals and DAG public impl functions in `src/thegent/cli/commands/impl.py` with re-exports from `src/thegent/cli/commands/dag_impl.py`.
- Preserved legacy import surface (`DagDocument`, `_validate_dag`, `dag_*_impl`, etc.) for compatibility.

2. `cli.py` wrapper cleanup cut

- Removed duplicate compatibility wrappers in `src/thegent/cli/commands/cli.py` that are already covered by extracted wildcard re-exports (`governance_cmds`, `plan_cmds`, `team_cmds`, `infra_cmds`).

3. `mcp/server.py` loader boilerplate cut (W3-C3 slice)

- Collapsed remaining manual `importlib` loader boilerplate in `src/thegent/mcp/server.py` to shared `server_load_module` helper calls while preserving `_load_server_*` wrapper names.

## LOC Evidence Refreshed

- Updated `.quality/loc-metrics.json` via `python scripts/collect_loc_metrics.py`.
- Added monolith baseline artifacts:
  - `docs/reports/artifacts/wl120-monolith-baseline-2026-02-21.json`
  - `docs/reports/artifacts/wl120-monolith-baseline-2026-02-21.txt`

Monolith line-count deltas (baseline before this wave -> after this wave):

- `src/thegent/cli/commands/cli.py`: `6881 -> 6797` (-84)
- `src/thegent/cli/commands/impl.py`: `6541 -> 5932` (-609)
- `src/thegent/mcp/server.py`: `3867 -> 3845` (-22)

## Focused Validation

1. Syntax/compile

- `python -m py_compile src/thegent/cli/commands/cli.py src/thegent/cli/commands/impl.py src/thegent/mcp/server.py` (pass)

2. Focused tests

- `uv run pytest -q tests/cli/test_wl120_extraction_hardening.py tests/test_wl126_server_module_loader.py tests/mcp/test_wl120_mcp_server_extraction.py`
- Result: `19 passed, 6 warnings`

## Workstream Status Decision

- WL-120 **NOT** moved to `COMPLETED`.
- Kept `docs/reference/WORK_STREAM.md` status `in_progress` and updated blockers with concrete current evidence.

Current concrete blockers:

1. Monolith ceilings are still not met.

- Current baselines: `cli.py 6797`, `impl.py 5932`, `mcp/server.py 3845`.

2. 3-day LOC decline acceptance is still not met.

- Existing day-end trend artifact remains `122545 -> 117587 -> 117587` (flat day 3) in `docs/reports/artifacts/wl120-wl136-loc-trend-2026-02-21.md`.
- Next required step: record a lower 2026-02-22 day-end snapshot after additional extraction cuts.

## Files Updated

- `src/thegent/cli/commands/impl.py`
- `src/thegent/cli/commands/cli.py`
- `src/thegent/mcp/server.py`
- `docs/changes/cli-dag-extraction/tasks.md`
- `docs/changes/mcp-server-extraction/tasks.md`
- `docs/reference/WORK_STREAM.md`
- `.quality/loc-metrics.json`
- `docs/reports/artifacts/wl120-monolith-baseline-2026-02-21.json`
- `docs/reports/artifacts/wl120-monolith-baseline-2026-02-21.txt`
- `.thegent/agent-batch/final-wl120.md`
