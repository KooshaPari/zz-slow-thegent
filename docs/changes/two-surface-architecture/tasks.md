---
title: Two-Surface Architecture — Remaining Tasks
date: 2026-02-21
status: in-progress
owner: B90-W3-agent-a
tags: [wl-136, tasks, wave-4, decomposition]
---

# Two-Surface Architecture — Remaining Tasks

## Completed (Wave-1 and Wave-2)

| Task                                 | Status | Artifact                                               |
| ------------------------------------ | ------ | ------------------------------------------------------ |
| Extract dag\_\* commands from cli.py | DONE   | `cli_dag.py`                                           |
| Extract tooling commands from cli.py | DONE   | `cli_tooling.py`                                       |
| Create execution boundary shim       | DONE   | `impl_execution.py`                                    |
| Classify modules (core vs tooling)   | DONE   | `design.md`                                            |
| Machine-readable boundary matrix     | DONE   | `contracts/runtime/runtime-modularization-matrix.json` |
| Boundary enforcement script          | DONE   | `scripts/check_thegent_core_boundary.py`               |

## Wave-4 Extractions (Remaining cli.py decomposition)

The following extractions are planned for Wave-4 to reduce `cli.py` from ~6,994 LOC
to under 2,000 LOC. Each module extracts a logical command group.

### cli_session.py

**Target**: Extract session management commands from `cli.py`.
**Commands**: `session_list_cmd`, `session_status_cmd`, `session_attach_cmd`,
`session_fork_cmd`, `session_rollback_cmd`, `session_export_cmd`.
**Surface**: tooling (session inspection is developer-facing).
**Dependencies**: `session_cmds.py`, `session_cmds_helpers.py` (already extracted).
**Predecessor**: Verify `session_cmds.py` is fully separated first.

### cli_infra.py

**Target**: Extract infrastructure commands from `cli.py`.
**Commands**: `infra_start_cmd`, `infra_stop_cmd`, `infra_status_cmd`,
`infra_logs_cmd`, `infra_reset_cmd`.
**Surface**: tooling (infra management is operator-facing).
**Dependencies**: `infra_cmds.py` and helpers (already extracted).
**Predecessor**: Verify `infra_cmds.py` is complete.

### cli_plan.py

**Target**: Extract planning commands from `cli.py`.
**Commands**: `plan_next_cmd`, `plan_loop_cmd`, `plan_incorporate_cmd`,
`plan_list_cmd`, `plan_archive_cmd`.
**Surface**: tooling (planning is orchestration tooling).
**Dependencies**: `plan_cmds.py` (already extracted).
**Predecessor**: Boundary test for plan_cmds.py.

### cli_models.py

**Target**: Extract model management commands from `cli.py`.
**Commands**: `models_list_cmd`, `models_inspect_cmd`, `models_set_cmd`,
`models_cost_cmd`.
**Surface**: tooling (model management is developer configuration).
**Dependencies**: `model_cmds.py` (already extracted).
**Predecessor**: Verify model_cmds.py import is clean.

### cli_governance.py

**Target**: Extract governance commands from `cli.py`.
**Commands**: `govern_conformance_cmd`, `govern_audit_cmd`, `govern_policy_cmd`,
`govern_slo_cmd`.
**Surface**: tooling (governance inspection is operator tooling).
**Dependencies**: `governance_cmds.py` (already extracted).
**Predecessor**: Boundary enforcement test for governance_cmds.py.

## Wave-4+ SLO Dashboard Wiring

Wire the SLO pass/fail gate to CI:

1. `scripts/check_slo_gate.py` — reads `.quality/slo-metrics.jsonl`, exits 1 on red
   (WL-135 B90-W3-A4).
2. Add `slo:check` task to `Taskfile.yml` (WL-135 B90-W3-A4).
3. Integrate `task slo:check` into `.github/workflows/ci.yml` quality gate step.
4. Wire SLO emission into `task metrics:loc` so each CI run emits a metric.

## Boundary Enforcement Test Reference

The canonical boundary enforcement test is:

```
uv run pytest tests/cli/test_wl120_extraction_hardening.py -v
uv run pytest tests/governance/test_wl136_two_surface_adr.py -v
```

These tests must pass before any Wave-4 extraction PR is merged.
