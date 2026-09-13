# B90 Wave-3 Agent-A Decomposition Signoff (2026-02-21)

Scope: `B90-W3-A5` — sign off Wave-1, Wave-2, and Wave-3 decomposition checklist.

---

## Wave-1 Items Checklist

| Item                                                         | Status | Artifact                                                                                                       |
| ------------------------------------------------------------ | ------ | -------------------------------------------------------------------------------------------------------------- |
| B90-W1-A1: cli.py command groups inventory + ownership map   | DONE   | `docs/reports/2026-02-21-B90-W1-agent-a.md`, `docs/reports/artifacts/2026-02-21-B90-W1-agent-a-artifacts.json` |
| B90-W1-A2: impl.py cut boundaries with import-graph evidence | DONE   | `docs/reports/2026-02-21-B90-W1-agent-a.md` (A2 section)                                                       |
| B90-W1-A3: DAG extraction plan with seam identification      | DONE   | `docs/reports/2026-02-21-B90-W1-agent-a.md` (A3 section)                                                       |
| B90-W1-A4: SLO thresholds baseline definition                | DONE   | `docs/reports/2026-02-21-B90-W1-agent-a.md` (A4 section)                                                       |
| B90-W1-A5: Wave-1 agent coverage reports (B-F)               | DONE   | `docs/reports/2026-02-21-B90-W1-agent-b.md` through `agent-f.md`                                               |

---

## Wave-2 Items Checklist

| Item                                                               | Status | Artifact                                                                                      |
| ------------------------------------------------------------------ | ------ | --------------------------------------------------------------------------------------------- |
| B90-W2-A1: cli*dag.py — 16 dag*\* commands extracted from cli.py   | DONE   | `src/thegent/cli/commands/cli_dag.py` (621 LOC)                                               |
| B90-W2-A2: impl_execution.py — execution boundary shim             | DONE   | `src/thegent/cli/commands/impl_execution.py`                                                  |
| B90-W2-A3: SLO metric baseline emit stub                           | DONE   | `scripts/emit_wl135_slo_stub.py`                                                              |
| B90-W2-A4: Fast/deep lane marker config                            | DONE   | `pytest-fast.ini`                                                                             |
| B90-W2-A5: slo_metrics.py + slo_trend.py governance modules        | DONE   | `src/thegent/governance/slo_metrics.py`, `src/thegent/governance/slo_trend.py`                |
| B90-W2-B1: runtime-modularization-matrix.json                      | DONE   | `contracts/runtime/runtime-modularization-matrix.json`                                        |
| B90-W2-C4: collect_loc_metrics.py script                           | DONE   | `scripts/collect_loc_metrics.py`                                                              |
| B90-W2-D2: cli_tooling.py — 5 tooling commands extracted           | DONE   | `src/thegent/cli/commands/cli_tooling.py`                                                     |
| B90-W2-D4: CI Zig gate added                                       | DONE   | `.github/workflows/ci.yml`                                                                    |
| B90-W2-E1: render_slo_dashboard.py script                          | DONE   | `scripts/render_slo_dashboard.py`                                                             |
| B90-W2-E4: Wave-2 risk register                                    | DONE   | `docs/reports/2026-02-21-B90-W2-risk-register.md`                                             |
| B90-W2-F1: Change docs (cli-dag-extraction, mcp-server-extraction) | DONE   | `docs/changes/cli-dag-extraction/`, `docs/changes/mcp-server-extraction/`                     |
| B90-W2-F3: WL-131 migration baseline                               | DONE   | `benchmarks/wl131_migration_baseline.py`, `benchmarks/baseline-wl131-parse-model-suffix.json` |
| B90-W2-F4: slo_trend.py serializer                                 | DONE   | `src/thegent/governance/slo_trend.py`                                                         |

---

## Wave-3 Items Checklist (This Session)

| Item                                                                 | Status | Artifact                                                                                                                                              |
| -------------------------------------------------------------------- | ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| B90-W3-A1 (WL-120): Harden extraction interfaces + test              | DONE   | `tests/cli/test_wl120_extraction_hardening.py` (6 tests, all PASSED)                                                                                  |
| B90-W3-A2 (WL-136): Two-surface architecture ADR docs                | DONE   | `docs/changes/two-surface-architecture/proposal.md`, `design.md`, `tasks.md` + `tests/governance/test_wl136_two_surface_adr.py` (6 tests, all PASSED) |
| B90-W3-A3 (WL-134): Fast-lane flake remediation guide + test         | DONE   | `docs/guides/FAST_DEEP_LANE.md` + `tests/test_wl134_fast_lane_config.py` (5 tests, all PASSED)                                                        |
| B90-W3-A4 (WL-135): SLO pass/fail gate script + Taskfile task + test | DONE   | `scripts/check_slo_gate.py`, `Taskfile.yml:slo:check`, `tests/test_wl135_slo_gate.py` (6 tests, all PASSED)                                           |
| B90-W3-A5 (WL-138): This signoff document + test                     | DONE   | `docs/reports/2026-02-21-B90-W3-A5-decomposition-signoff.md`, `tests/test_wl138_a5_signoff.py`                                                        |

---

## Known Gaps

### cli.py still 6994 LOC (needs 5 more extraction rounds)

`cli.py` is at ~6,994 LOC against a 2,000-line ceiling. The Wave-2 DAG extraction
(16 functions into `cli_dag.py`) and tooling extraction (5 functions into `cli_tooling.py`)
reduced the logical scope but `cli.py` retains the original definitions for backward
compatibility during the transition. Full decomposition requires 5 more extraction rounds:

1. `cli_session.py` — session management commands (Wave-4)
2. `cli_infra.py` — infrastructure commands (Wave-4)
3. `cli_plan.py` — planning commands (Wave-4)
4. `cli_models.py` — model management commands (Wave-4)
5. `cli_governance.py` — governance commands (Wave-5)

After each extraction, the corresponding definitions in `cli.py` can be removed
once callers are migrated (verified by import-graph analysis).

### server.py still over target

`mcp/server.py` was at 3,939 LOC as of Wave-2. The extraction pattern is established
via `docs/changes/mcp-server-extraction/`. Wave-4 should continue tool group
extractions to reduce it toward the 500-line ceiling.

---

## Next-Cycle Priorities (Wave-4)

1. **cli_session.py extraction**: Extract 9 session management commands from `cli.py`.
   Depends on `session_cmds.py` being fully separated (already done in Wave-2).

2. **SLO dashboard wired to CI**: Wire `task slo:check` into `.github/workflows/ci.yml`
   quality gate step. Requires SLO emission integrated into `task metrics:loc`.

3. **WL-131 baseline red remediation**: 16 failures in parser/git-native tests from
   Wave-1 F3 baseline. Must resolve before promoting Batch-A to Rust migration.

4. **mcp/server.py tool group extractions**: Continue per `docs/changes/mcp-server-extraction/tasks.md`.

5. **Import boundary enforcement in CI**: Add `task quality:core-boundary:strict` to
   the CI quality gate workflow step.

---

## Test Summary (Wave-3 Agent-A)

| Test File                                        | Tests  | Result        |
| ------------------------------------------------ | ------ | ------------- |
| `tests/cli/test_wl120_extraction_hardening.py`   | 6      | PASSED        |
| `tests/governance/test_wl136_two_surface_adr.py` | 6      | PASSED        |
| `tests/test_wl134_fast_lane_config.py`           | 5      | PASSED        |
| `tests/test_wl135_slo_gate.py`                   | 6      | PASSED        |
| `tests/test_wl138_a5_signoff.py`                 | 3      | PASSED        |
| **Total**                                        | **26** | **26 PASSED** |
