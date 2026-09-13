---
title: "B90-W3-D1: Dead Code Inventory — Pre-Split CLI Modules"
date: 2026-02-21
status: active
owner: b90-wave3-agent-d
tags: [wl-120, cli, dead-code, monolith-split]
---

# B90-W3-D1: Dead Code Inventory — Pre-Split CLI Modules

## Summary

This report inventories code that exists in `src/thegent/cli/commands/cli.py` but
has been migrated to one of the split modules:

- `src/thegent/cli/commands/cli_dag.py` (WL-120 B90-W2-A1)
- `src/thegent/cli/commands/cli_tooling.py` (WL-136 B90-W2-D2)
- `src/thegent/cli/commands/impl_execution.py` (WL-120 B90-W2-A2)

## Module Statistics

| Module              | LOC    | Target  | Status      |
| ------------------- | ------ | ------- | ----------- |
| `cli.py`            | 6,881  | ≤ 2,000 | OVER (3.4×) |
| `cli_dag.py`        | ~600   | ≤ 600   | OK          |
| `cli_tooling.py`    | ~270   | ≤ 300   | OK          |
| `impl_execution.py` | exists | —       | OK          |

## Tooling Surface: Re-exported Functions (Backwards Compat)

The following five functions were extracted to `cli_tooling.py` and are
**re-imported into `cli.py`** at lines 27–33 for backwards compatibility.
Because they are re-exported under renamed aliases (prefixed `_tooling_`),
they are NOT directly accessible from the `cli` module namespace, meaning
the backwards-compat value is limited to internal call sites.

| Function            | Canonical Location   | Re-exported in cli.py? | Alias in cli.py              |
| ------------------- | -------------------- | ---------------------- | ---------------------------- |
| `audit_verify_cmd`  | `cli_tooling.py:223` | YES                    | `_tooling_audit_verify_cmd`  |
| `benchmark_cmd`     | `cli_tooling.py:44`  | YES                    | `_tooling_benchmark_cmd`     |
| `deep_research_cmd` | `cli_tooling.py:101` | YES                    | `_tooling_deep_research_cmd` |
| `drift_monitor_cmd` | `cli_tooling.py:155` | YES                    | `_tooling_drift_monitor_cmd` |
| `roadmap_cmd`       | `cli_tooling.py:189` | YES                    | `_tooling_roadmap_cmd`       |

Additionally, cli.py still contains **duplicate definitions** of all five
functions at their original lines (these were NOT removed when the split was
done; only re-exports were added):

| Function            | cli.py line | cli_tooling.py line | Status    |
| ------------------- | ----------- | ------------------- | --------- |
| `audit_verify_cmd`  | present     | 223                 | DUPLICATE |
| `benchmark_cmd`     | present     | 44                  | DUPLICATE |
| `deep_research_cmd` | present     | 101                 | DUPLICATE |
| `drift_monitor_cmd` | present     | 155                 | DUPLICATE |
| `roadmap_cmd`       | present     | 189                 | DUPLICATE |

## DAG Surface: Duplicate Functions

The following 16 `dag_*` functions were extracted to `cli_dag.py` but remain
as full definitions in `cli.py` (no re-export was added; cli.py retains the
original bodies). `cli_dag.py` imports helpers from `cli.py` and re-implements
the command handlers calling those helpers.

| Function              | cli.py line | cli_dag.py line | Status    |
| --------------------- | ----------- | --------------- | --------- |
| `dag_validate_cmd`    | 3717        | 46              | DUPLICATE |
| `dag_list_cmd`        | 3756        | 83              | DUPLICATE |
| `dag_add_cmd`         | 3804        | 131             | DUPLICATE |
| `dag_remove_cmd`      | 3860        | 187             | DUPLICATE |
| `dag_cancel_cmd`      | 3881        | 208             | DUPLICATE |
| `dag_status_cmd`      | 3887        | 214             | DUPLICATE |
| `dag_update_cmd`      | 3920        | 247             | DUPLICATE |
| `dag_ready_cmd`       | 3984        | 311             | DUPLICATE |
| `dag_reconcile_cmd`   | 4025        | 352             | DUPLICATE |
| `dag_run_cmd`         | 4664        | 401             | DUPLICATE |
| `dag_sync_cmd`        | 4704        | 441             | DUPLICATE |
| `dag_checkpoint_cmd`  | 4722        | 461             | DUPLICATE |
| `dag_rollback_cmd`    | 4745        | 484             | DUPLICATE |
| `dag_checkpoints_cmd` | 4774        | 513             | DUPLICATE |
| `dag_recover_cmd`     | 4802        | 541             | DUPLICATE |
| `dag_probe_cmd`       | 4820        | 559             | DUPLICATE |

## Wave-4 Removal Recommendations

The following can be safely removed in Wave-4 once callers are audited:

### High Confidence — Remove in Wave-4

These functions in `cli.py` are duplicated in a split module and the Typer
`app` registration should point to the split module version. Safe to remove
from `cli.py` after verifying no external import of `cli.py.<fn>`.

1. All 16 `dag_*_cmd` functions (lines 3717–4900 range) — canonical in `cli_dag.py`
2. All 5 tooling commands (`audit_verify_cmd`, `benchmark_cmd`, `deep_research_cmd`,
   `drift_monitor_cmd`, `roadmap_cmd`) — canonical in `cli_tooling.py`
3. The re-import block (lines 27–33) — remove once callers updated

### Prerequisite for Removal

- Verify that the Typer app registration (or `register_commands()` call) uses
  the split module functions, not the `cli.py` copies.
- Run full test suite before and after each deletion batch.
- Estimated LOC saved: ~800 lines (dag) + ~250 lines (tooling) = ~1,050 lines,
  bringing `cli.py` from 6,881 to ~5,831 (still over ceiling; further splits required).

## Decision Record

- **Do NOT remove in Wave-3**: Removals require caller audit + full regression.
- **Wave-4 target**: Remove duplicates, update Typer registrations, verify parity.
- **Wave-5 target**: cli.py ≤ 2,000 lines.

## Backmatter

- **Decision delta**: Document existence of duplicates; defer removal to Wave-4.
- **Validation commands**: `wc -l src/thegent/cli/commands/cli.py`
- **Residual risks**: Typer registration may still point to cli.py copies; updating
  registration without removing definition is safe.
- **Follow-up review date**: 2026-02-28 (Wave-4 kick-off).
