# B90 Wave-2 Risk Register (2026-02-21)

## Overview

This register captures risks identified during B90 Wave-2 execution across all five agent threads (a through e).
Risks are derived from Wave-1 artifact analysis, codebase observation, and coordination state at the time of Wave-2 execution.

## Active Risks

| ID      | Risk                                                                                                                                                | Probability | Impact | Mitigation                                                                                                                          | Owner            |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- | ------ | ----------------------------------------------------------------------------------------------------------------------------------- | ---------------- |
| R-W2-01 | Parallel agents edit same file (pyproject.toml, Taskfile.yml) causing merge conflicts                                                               | Medium      | High   | Each agent has bounded edit scope; conflicts resolved at wave end                                                                   | B90 Orchestrator |
| R-W2-02 | Rust parity tests fail due to incomplete PyO3 bindings                                                                                              | Medium      | Medium | Python-side parity tests stand alone; Rust tests in crate                                                                           | agent-b          |
| R-W2-03 | CLI monolith extraction breaks callers                                                                                                              | Low         | High   | Re-export pattern preserves backward compatibility                                                                                  | agent-a/d        |
| R-W2-04 | Zig ABI contract version mismatch                                                                                                                   | Low         | Low    | Contract tests catch mismatches; continue-on-error in CI                                                                            | agent-d          |
| R-W2-05 | `fast` marker not annotated on existing tests — fast lane runs full suite                                                                           | High        | Medium | pytest-fast.ini uses exclude-by-negation (not slow/integration/e2e/load); no per-test annotation required for current lane strategy | agent-e          |
| R-W2-06 | `.quality/` directory absent in CI environment, SLO dashboard render fails                                                                          | Low         | Medium | Script calls `QUALITY_DIR.mkdir(parents=False, exist_ok=True)` and exits loudly if directory cannot be created                      | agent-e          |
| R-W2-07 | `contracts/runtime/runtime-modularization-matrix.json` not yet linked from CI governance check — matrix data may drift from plan                    | Medium      | Low    | Governance summary and modernization plan now reference the file path; CI linkage is a follow-up WL                                 | B90 Orchestrator |
| R-W2-08 | WL-117 VS Code extension already completed (COMPLETED status in WORK_STREAM) but Wave-2 task asks to scaffold it — risk of double-work or overwrite | High        | Low    | Wave-2 task produces documentation/plan artifacts only; existing `extensions/vscode/` not modified                                  | agent-e          |
| R-W2-09 | pyproject.toml `[tool.thegent.pytest_lanes]` section not read by any tool — lane definitions are documentation-only, not enforced                   | Medium      | Medium | `test:fast-lane` Taskfile task now uses `pytest-fast.ini` which is executable; lane definitions are a secondary record              | agent-a/e        |
| R-W2-10 | Governance summary mutation (appending Runtime Modularization Matrix section) conflicts with agent-c/d edits to same file                           | Medium      | High   | Section appended at document tail with clear WL-130 heading; conflict zone is distinct from other sections                          | agent-e          |

## Closed Risks (Wave-1 → Wave-2 Transition)

| ID      | Risk                                        | Resolution                                                                        |
| ------- | ------------------------------------------- | --------------------------------------------------------------------------------- |
| R-W1-01 | WL-104 not completed before WL-117 scaffold | Closed: WL-104 COMPLETED 2026-02-20; WL-117 also COMPLETED                        |
| R-W1-02 | No fast lane defined in CI                  | Closed: Taskfile `test:fast-lane` exists; `pytest-fast.ini` created in Wave-2     |
| R-W1-03 | No machine-readable runtime matrix          | Closed: `contracts/runtime/runtime-modularization-matrix.json` exists (Wave-2 B1) |

## Risk Monitoring

- Risk register must be updated at the start of each wave by the orchestrator agent.
- Risks transitioning to CLOSED must include the resolution mechanism and date.
- New codebase-observed risks should be escalated to `R-W{N}-{NN}` format with owner assignment.

_Generated by agent-e — WL-138 B90-W2-E4_
