---
title: Two-Surface Architecture Design
date: 2026-02-21
status: accepted
owner: B90-W3-agent-a
tags: [wl-136, design, import-boundary, decomposition]
---

# Two-Surface Architecture Design

## Module Classification Table

| Module | Surface | Rationale |
|--------|---------|-----------|
| `src/thegent/agents/` | core | Production agent runners |
| `src/thegent/mcp/` | core | MCP server — always-on |
| `src/thegent/routing/` | core | Request routing — hot path |
| `src/thegent/governance/` | core | SLO emitter, policy engine |
| `src/thegent/infra/` | core | Infrastructure primitives |
| `src/thegent/config.py` | core | Config resolution at startup |
| `src/thegent/session/` | core | Session state management |
| `src/thegent/orchestration/` | core | DAG execution engine |
| `src/thegent/cli/commands/impl.py` | core | Execution dispatch |
| `src/thegent/cli/commands/run_cmds.py` | core | `thegent run` entrypoint |
| `src/thegent/cli/commands/cli_dag.py` | tooling | DAG management CLI (WL-120) |
| `src/thegent/cli/commands/cli_tooling.py` | tooling | Dev utilities (WL-136) |
| `src/thegent/cli/commands/impl_execution.py` | tooling | Execution boundary shim |
| `benchmarks/` | tooling | Performance benchmarks |
| `scripts/` | tooling | Dev/QA scripts |

## Import Boundary Rule

**Rule**: Tooling modules MAY import core modules. Core modules MUST NOT import tooling modules.

```
core  ← tooling   (allowed: tooling depends on core)
core  → tooling   (FORBIDDEN: core must not depend on tooling)
```

This is an acyclic dependency graph with core at the root.

### Enforcement

The import boundary is enforced by `scripts/check_thegent_core_boundary.py`:

```bash
# Advisory check (warns, non-blocking)
uv run python scripts/check_thegent_core_boundary.py

# Strict check (exits 1 on violation — used in CI)
uv run python scripts/check_thegent_core_boundary.py --strict
```

Via Taskfile:
```bash
task quality:core-boundary         # advisory
task quality:core-boundary:strict  # CI-blocking
```

Violations are any import edge where a core module imports from a tooling module.
The enforcement script reads `config/thegent_core_boundary.toml` for the boundary
definition.

## Tooling Module Details

### `cli_dag.py` (tooling surface)

Contains the 16 `dag_*_cmd` functions extracted from `cli.py` in WL-120 B90-W2-A1:

- `dag_validate_cmd`, `dag_list_cmd`, `dag_add_cmd`, `dag_remove_cmd`
- `dag_cancel_cmd`, `dag_status_cmd`, `dag_update_cmd`, `dag_ready_cmd`
- `dag_reconcile_cmd`, `dag_run_cmd`, `dag_sync_cmd`, `dag_checkpoint_cmd`
- `dag_rollback_cmd`, `dag_checkpoints_cmd`, `dag_recover_cmd`, `dag_probe_cmd`

These commands import from `cli.py` helpers (lazy imports via the `_lazy_import` pattern)
and from `thegent.execution` (core). They orchestrate DAG sessions and are user-facing
developer tools, not production runtime.

### `cli_tooling.py` (tooling surface)

Contains 5 commands extracted from `cli.py` in WL-136 B90-W2-D2:

- `audit_verify_cmd` — cross-check audit log against governance contracts
- `benchmark_cmd` — report orchestration performance metrics (WP-6001)
- `deep_research_cmd` — trigger deep research sub-agent workflow
- `drift_monitor_cmd` — continuous drift detection against governance baseline
- `roadmap_cmd` — generate roadmap view from workstream and plan data

### `impl_execution.py` (execution boundary shim)

A thin module (33 lines) that re-exports the four canonical execution boundary
functions from `impl.py`:

```python
from thegent.cli.commands.impl_execution import run_impl, bg_impl, resume_impl, loop_impl
```

This shim is a transition artifact. Once all callers are migrated to import from
`impl_execution`, the function bodies will be moved here in a follow-on sprint (WL-120 Phase 3).

## Contract Metadata

The boundary is also machine-readable in `contracts/runtime/runtime-modularization-matrix.json`.
This file records the module classification, surface assignment, and migration status
for each module in the decomposition.

## Decision: Backmatter

**Decision delta**: cli_dag.py and cli_tooling.py are classified as tooling; impl.py
and run_cmds.py remain core.

**Validation commands**:
```bash
task quality:core-boundary:strict
uv run pytest tests/cli/test_wl120_extraction_hardening.py -v
uv run pytest tests/governance/test_wl136_two_surface_adr.py -v
```

**Residual risks**:
- `cli.py` still imports from `cli_tooling.py` via re-exports; these must be removed
  when cli.py is fully decomposed (Wave-5+).
- `cli_dag.py` imports from `cli.py` (lazy import pattern); this creates a transient
  coupling until Phase 3 migration.

**Follow-up review date**: 2026-03-21
