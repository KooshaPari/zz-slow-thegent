---
title: CLI DAG Extraction — Design
date: 2026-02-21
status: implemented
owner: agent-f (B90-W2-F1)
tags: [wl-120, b90, monolith-split, cli]
---

# Design: CLI DAG Extraction

## New Module Layout

```
src/thegent/cli/commands/
├── cli.py              # Legacy monolith (6,870 lines post-wave-2)
│                       # Exports: all public CLI helpers, app object,
│                       #          re-exports from run_cmds, session_cmds,
│                       #          governance_cmds, plan_cmds, model_cmds,
│                       #          infra_cmds, team_cmds
├── cli_dag.py          # EXTRACTED — 622 lines (WL-120 B90-W2-A1)
│                       # Contains: dag_*_cmd handlers (16 functions)
│                       # Imports helpers from cli.py; no business logic
├── run_cmds.py         # Re-exported from cli.py (WL-124)
├── session_cmds.py     # Re-exported from cli.py (WL-124)
├── governance_cmds.py  # Re-exported from cli.py (WL-124)
├── plan_cmds.py        # Re-exported from cli.py (WL-124)
├── model_cmds.py       # Re-exported from cli.py (WL-124)
├── infra_cmds.py       # Re-exported from cli.py (WL-124)
├── team_cmds.py        # Re-exported from cli.py (WL-124)
├── queue_commands.py   # Re-exported via delegation from cli.py (WL-124)
└── observability_impl.py # Extracted from impl.py (WL-120 B90-W2-A2)
```

## What Was Moved

### cli_dag.py (622 lines)

All DAG command handler functions extracted from `cli.py`:

| Function              | Responsibility                              |
| --------------------- | ------------------------------------------- |
| `dag_validate_cmd`    | Validate DAG session file; exit 2 on errors |
| `dag_list_cmd`        | List DAG tasks (table or JSON format)       |
| `dag_add_cmd`         | Add a new task to the active DAG            |
| `dag_remove_cmd`      | Remove a task from the DAG                  |
| `dag_cancel_cmd`      | Cancel a running task                       |
| `dag_status_cmd`      | Show DAG status summary                     |
| `dag_update_cmd`      | Update task metadata (status, owner, deps)  |
| `dag_ready_cmd`       | Show tasks ready to execute                 |
| `dag_reconcile_cmd`   | Reconcile DAG with git session state        |
| `dag_run_cmd`         | Run a specific task by ID                   |
| `dag_sync_cmd`        | Sync DAG to upstream and auto-run next      |
| `dag_checkpoint_cmd`  | Create a DAG checkpoint snapshot            |
| `dag_rollback_cmd`    | Roll back to a named checkpoint             |
| `dag_checkpoints_cmd` | List all saved checkpoints                  |
| `dag_recover_cmd`     | Recover from failure (retry-failed action)  |
| `dag_probe_cmd`       | Probe DAG against a baseline                |

### observability_impl.py (WL-120 A2, extracted from impl.py)

37 functions for health reporting, observe-summary, compliance, and review.
Imported by `impl.py` via a re-export block at line 1091.

## Re-Export Strategy

`cli.py` currently does **not** re-export `cli_dag.py` via a wildcard import.
The DAG Typer sub-application wires `cli_dag.py` directly. This avoids
namespace pollution and allows `cli_dag.py` to be tested without importing
the full `cli.py` monolith.

`impl.py` re-exports `observability_impl.py` via named import at line 1091.

## Import Graph (simplified)

```
cli_dag.py
  └─ imports helpers from cli.py
       (LazyConsole, ThegentSettings, _atomic_write, _check_dag_cycles,
        _dag_path, _dag_update_task, _default_owner_tag,
        _ensure_contract_version_header, _ensure_dag_file,
        _parse_dag_full, _parse_dag_session, _parse_depends_on,
        _resolve_checkpoint_id, _resolve_cwd, _serialize_dag,
        _session_status_for, _validate_agent, _validate_dag,
        _validate_task_id, console, dag_ready_impl, dag_recover_impl,
        dag_run_impl, dag_sync_impl)
```

## Parity Notes

- All 16 `dag_*_cmd` handlers are present in `cli_dag.py`; none were lost.
- `cli.py` still contains the original function stubs (kept for any direct callers
  until removal gate is green).
- Import chain: `cli_dag.py` → `cli.py` (helpers only, not circular).
