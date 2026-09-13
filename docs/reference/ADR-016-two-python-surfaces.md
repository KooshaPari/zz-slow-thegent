# ADR-016: Two Python Surfaces (Core Runtime vs Tooling/Test)

## Status

ACCEPTED (2026-02-21)

## Context

WL-120 and WL-136 identified sustained Python growth in mixed-purpose modules. Runtime command paths and tooling/test/research helpers were co-located, which increased coupling, slowed default quality lanes, and made decomposition progress hard to measure.

The repository already introduced extraction modules (`dag_impl.py`, `work_stream_impl.py`, `observability_impl.py`, `cli_dag.py`) and a boundary checker (`scripts/check_thegent_core_boundary.py`), but the architecture decision itself was not ratified in ADR form.

## Decision

Adopt and enforce two explicit Python surfaces:

1. Core runtime surface:

- Includes runtime command handlers and runtime execution/control modules.
- Must trend downward in LOC and import complexity.
- Must stay on fast-lane validation paths.

2. Tooling/test/research surface:

- Includes tests, scripts, docs generators, migration/diagnostic tooling.
- May grow independently, but must not become a runtime dependency without explicit approval.
- Runs in separate/deeper lanes where possible.

Routing rule:

- When a domain has an extracted implementation module, command surfaces import that module directly instead of pulling handlers from `impl.py`.

## Consequences

Positive:

- Clear ownership and enforcement target for WL-136.
- Lower coupling between command surfaces and the legacy `impl.py` monolith.
- Better decomposition signal for WL-120 progress.

Tradeoffs:

- Transition period keeps some compatibility exports in `impl.py`.
- Additional import-routing checks are required to prevent regressions.

## Implementation Notes (Track A closeout slice)

- `src/thegent/cli/commands/plan_cmds.py` routes `dag_status_impl` via `dag_impl`, and routes work-stream actions via `work_stream_impl`.
- `src/thegent/cli/commands/cli_dag.py` routes `dag_status_impl` via `dag_impl`.
- Focused regression test added:
  - `tests/commands/test_wl120_extraction_import_routing.py`

## Related Artifacts

- `docs/plans/WL-136-TWO-PYTHON-SURFACES.md`
- `docs/plans/2026-02-21-MODERNIZATION-MASTER-PLAN.md`
- `scripts/check_thegent_core_boundary.py`
- `config/thegent_core_boundary.toml`
