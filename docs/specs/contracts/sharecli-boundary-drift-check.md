# ShareCLI Boundary Drift Check

## Status

Draft - pre-code enforcement specification for the `thegent` -> `sharecli`
boundary cleanup.

## Purpose

The boundary audit and contract spec define where execution substrate code should
live. This document defines the recurring check that prevents the boundary from
drifting while code moves in stages.

The check is intentionally staged. It starts as a reporting gate while adapters
are being introduced, then becomes a failing gate after each surface has a
sharecli-owned implementation and a thegent adapter.

## Boundary Invariant

After a surface is migrated, `thegent` may depend on a stable sharecli adapter
or command/API contract, but it must not import or grow local implementations of
sharecli-owned substrate behavior.

Sharecli-owned substrate behavior includes:

- process lifecycle and process inventory
- queue implementation and queue storage mechanics
- structural merge implementation and merge-driver setup
- worktree allocation, cleanup, and conflict queues
- resource limits, sandbox mechanics, and execution purification
- native harness runtime strategies, dispatcher, cache, retry, throttle, and
  jobserver behavior

Thegent-owned behavior remains allowed:

- governance approval and policy decisions
- agent orchestration and teammate workflow decisions
- MCP/tool registry routing
- evidence interpretation and human-in-the-loop decisions
- temporary compatibility shims that delegate to sharecli contracts

## Check Scope

| Path                                 | Initial mode | Final mode | Reason                                                               |
| ------------------------------------ | ------------ | ---------- | -------------------------------------------------------------------- |
| `src/thegent/governance/**`          | warn         | fail       | Governance must not grow harness mechanics after adapters exist.     |
| `src/thegent/mesh/cli.py`            | warn         | fail       | User-visible CLI may stay, but substrate work must delegate.         |
| `src/thegent/mesh/main.py`           | warn         | fail       | Mesh entrypoint should present status and commands through adapters. |
| `src/thegent/mesh/mesh.py`           | warn         | fail       | Mixed queue/process composition is a migration hotspot.              |
| `src/thegent/mesh/agent_patterns.py` | warn         | fail       | Process inventory should come from sharecli once available.          |
| `src/thegent/mesh/audit.py`          | warn         | fail       | Audit may interpret records, not collect substrate internals.        |
| `src/thegent/mesh/observability.py`  | warn         | fail       | Status may render sharecli health, not own process telemetry.        |
| `tests/**`                           | report       | report     | Tests may reference legacy modules until each lane is migrated.      |
| `docs/**`                            | ignore       | ignore     | Historical and planning references are allowed.                      |

The check should not scan archived BytePort paths listed in `AGENTS.md`.

## Violation Patterns

The first implementation should detect direct imports and obvious local growth.
It does not need full semantic analysis on day one.

| Pattern                                                                      | Meaning                              | Initial action | Final action                     |
| ---------------------------------------------------------------------------- | ------------------------------------ | -------------- | -------------------------------- |
| `from thegent.mesh.task_queue import` outside allowed shims/tests            | Queue implementation dependency      | warn           | fail after queue lane            |
| `from thegent.mesh.smart_merge import` outside allowed shims/tests           | Merge implementation dependency      | warn           | fail after merge lane            |
| `from thegent.mesh.git_parallelism import` outside allowed shims/tests       | Worktree pool dependency             | warn           | fail after worktree lane         |
| `from thegent.mesh.worktree import` outside allowed shims/tests              | Worktree lifecycle dependency        | warn           | fail after worktree lane         |
| `from thegent_gitops` or `import thegent_gitops` outside allowed shims/tests | Gitops substrate dependency          | warn           | fail after worktree lane         |
| `from thegent.mesh.process_detection import` outside adapters/tests          | Process inventory dependency         | warn           | fail after process lane          |
| `from thegent.mesh.resources import` outside adapters/tests                  | Resource substrate dependency        | warn           | fail after execution-safety lane |
| `from thegent.mesh.sandbox import` outside adapters/tests                    | Sandbox substrate dependency         | warn           | fail after execution-safety lane |
| `from thegent.mesh.injection import` outside policy-gated UX/tests           | Shell/session execution dependency   | warn           | fail after execution-safety lane |
| New code under `crates/harness-native/**`                                    | Native runtime growth in source repo | warn           | fail after native lane           |

## Allowed Temporary Imports

Temporary imports are allowed only when they are listed in a lane manifest. The
manifest should live with the future check implementation, for example
`tools/boundary/sharecli_boundary_allowlist.toml`.

Each allowlist row should include:

| Field         | Meaning                                                                               |
| ------------- | ------------------------------------------------------------------------------------- |
| `path`        | File path containing the temporary import.                                            |
| `symbol`      | Import or module name allowed.                                                        |
| `lane`        | `native-harness`, `queue`, `merge-worktree`, `process-health`, or `execution-safety`. |
| `sunset_gate` | Test or PR condition that removes the allowance.                                      |
| `reason`      | One sentence explaining why the temporary dependency remains.                         |

An allowlist entry without a sunset gate should fail review even before the
check is enforcement-grade.

## Rollout Stages

| Stage                     | Behavior                                                                                                   | Exit gate                                                               |
| ------------------------- | ---------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| Drift 0: Spec only        | This document exists and is linked from the audit.                                                         | Committed docs.                                                         |
| Drift 1: Reporter         | `scripts/sharecli_boundary_drift_check.py` prints current violations with lane labels and allowlist hints. | Reporter output is stable in CI artifacts or local `task quality`.      |
| Drift 2: Lane warnings    | Reporter exits non-zero only for new, unallowlisted violations in migrated lanes.                          | First migrated lane has adapter tests and sharecli owner tests.         |
| Drift 3: Full enforcement | All migrated surfaces fail on direct substrate imports or local implementation growth.                     | Native, queue, merge/worktree, and execution-safety lanes are complete. |
| Drift 4: Recurring audit  | CI/task quality runs the check and points to remediation docs.                                             | Check is part of the default quality path.                              |

## Output Contract

The reporter should emit machine-readable JSON plus a concise text summary.

Minimum JSON fields:

| Field         | Meaning                                              |
| ------------- | ---------------------------------------------------- |
| `path`        | File containing the finding.                         |
| `line`        | One-based line number.                               |
| `pattern`     | Matched import or growth pattern.                    |
| `lane`        | Migration lane responsible for the finding.          |
| `severity`    | `info`, `warn`, or `fail`.                           |
| `allowlisted` | Whether an allowlist row matched.                    |
| `sunset_gate` | Required condition to remove an allowlisted finding. |

Minimum text summary:

- count by lane
- count by severity
- first five failing findings
- pointer to this spec and the boundary contract spec

## Integration Points

The check should become part of the quality path in this order:

1. Local script: `scripts/sharecli_boundary_drift_check.py`.
2. Allowlist: `config/sharecli_boundary_drift_allowlist.toml`.
3. Targeted test: `tests/test_sharecli_boundary_drift_check.py`.
4. Advisory quality task: `task quality:sharecli-boundary`.
5. `task quality` runs the advisory reporter before existing Tach/Vale/Ruff
   checks.
6. CI after the first migrated lane is complete.

The check must not attempt cleanup, process termination, git mutation, or
automatic rewrites. It reports boundary drift only.

## Reporter Commands

| Command                                                                                  | Meaning                                                             |
| ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `python scripts/sharecli_boundary_drift_check.py --format summary-json`                  | Current advisory summary; used by `task quality:sharecli-boundary`. |
| `python scripts/sharecli_boundary_drift_check.py --format json`                          | Full machine-readable payload with findings.                        |
| `python scripts/sharecli_boundary_drift_check.py --enforce-lane native-harness --strict` | Example migrated-lane enforcement mode.                             |

## Implemented Reporter Slice

1. Add a minimal reporter that scans Python imports and `crates/harness-native`
   file changes.
2. Seed the allowlist from the caller/test-owner map in
   `docs/reports/THEGENT_SHARECLI_BOUNDARY_AUDIT_2026-06-21.md`.
3. Add fixture tests that prove allowed, warned, and failed imports are
   classified correctly.
4. Keep enforcement in reporter mode until the first sharecli-owned lane lands.

## Next Implementation Slice

1. Pick the first migrated lane to enforce, likely `native-harness` because it
   has no allowlisted source imports and its findings are ownership-growth
   records.
2. Move or mirror the native harness runtime into sharecli ownership with
   owner-side tests.
3. Set `native-harness` in `sharecli_boundary.enforced_lanes` only after the
   sharecli owner tests and thegent adapter/shim tests pass.
