---
title: CLI DAG Extraction — Remaining Tasks
date: 2026-02-21
status: in-progress
owner: agent-f (B90-W2-F1)
tags: [wl-120, b90, monolith-split, cli]
---

# Remaining Tasks: CLI Monolith Split

## Completed

- [x] **B90-W2-A1** Extract `dag_*_cmd` handlers to `cli_dag.py` (622 lines)
- [x] **B90-W2-A2** Extract observability/health handlers to `observability_impl.py`
- [x] **WL-124** Re-export `run_cmds`, `session_cmds`, `governance_cmds`, `plan_cmds`,
      `model_cmds`, `infra_cmds`, `team_cmds` from `cli.py` via wildcard re-exports
- [x] **W3-B1 (slice, 2026-02-21)** Delegate DAG internals/public impls in `impl.py` to
      `dag_impl.py` and remove duplicated in-file DAG implementation
      (`impl.py` line-count baseline: `6541 -> 5932` in
      `docs/reports/artifacts/wl120-monolith-baseline-2026-02-21.json`)
- [x] **W3-B2 (2026-02-21)** Extract session backend logic from `impl.py` to `session_impl.py`
      (1716 LOC; 36 functions extracted; `impl.py` body reduced by ~1000 lines of session logic)
- [x] **W3-B3 (2026-02-21)** Extract infra/compute backend logic from `impl.py` to `infra_impl.py`
      (560 LOC; 10 functions extracted; `impl.py` 5932 → 3719 total after W3-B2+B3, -2213 lines)
      LOC recorded in `.quality/loc-metrics.jsonl`

## Remaining Extractions (Future Waves)

### Wave-3: cli.py monolith further reduction

| ID    | Target module                                                    | Estimated LOC | Depends on        | Status              |
| ----- | ---------------------------------------------------------------- | ------------- | ----------------- | ------------------- |
| W3-A1 | `cli_session.py` — extract all `session_*_cmd` handlers          | ~400          | A1 pattern stable | DONE (99 LOC final) |
| W3-A2 | `cli_infra.py` — extract all infra/compute/sandbox cmd handlers  | ~350          | A1 pattern stable | DONE                |
| W3-A3 | `cli_plan.py` — extract all plan/workstream cmd handlers         | ~300          | A1 pattern stable | DONE                |
| W3-A4 | `cli_models.py` — extract all model catalog cmd handlers         | ~250          | A1 pattern stable | DONE                |
| W3-A5 | `cli_governance.py` — extract governance/team/audit cmd handlers | ~200          | A1 pattern stable | DONE                |

### Wave-3: impl.py monolith further reduction

| ID    | Target module                                   | Estimated LOC | Depends on        | Status |
| ----- | ----------------------------------------------- | ------------- | ----------------- | ------ |
| W3-B1 | `dag_impl.py` — extract DAG backend logic       | ~500          | A2 pattern stable | DONE   |
| W3-B2 | `session_impl.py` — extract session backend     | 1716 actual   | A2 pattern stable | DONE   |
| W3-B3 | `infra_impl.py` — extract infra/compute backend | 560 actual    | A2 pattern stable | DONE   |

## Cut-over Gate (per module)

Before removing the stub shim from `cli.py` / `impl.py` for any extracted module:

1. `python -c "from thegent.cli.commands.<module> import <cmd>"` exits 0
2. Focused unit tests for the extracted module pass (`pytest tests/commands/test_<module>.py`)
3. No p95 CLI latency regression vs baseline
4. Core-boundary strict check still green (`task quality:core-boundary:strict`)
5. LOC metric recorded for the extracted module in `.quality/loc-metrics.jsonl`

## Target Ceiling

- `cli.py`: reduce from 6,870 to < 2,000 lines by end of Wave-5
- `impl.py`: reduce from 6,541 to < 2,000 lines by end of Wave-5
- Each extracted module: < 500 lines (enforced by `contracts/max_lines.json`)
