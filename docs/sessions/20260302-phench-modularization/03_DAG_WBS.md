# Phench Modularization and Project-Orchestration WBS

Current milestone state:

- [done] feat(thegent): add projects modules command and manifest listing (`018c148c3`)
- [done] feat(phench): expose runtime module discovery helper (`8a0cf4bbe`)
- [done] chore(phench): sync audit metadata and module source roots (`e692ba7e5`)
- [done] chore(phench): make missing module manifest schema defaults migration-compatible
- [done] feat(phench): add cross-repo shared module scan + sync helper functions in service
- [done] feat(phench): add `phench_modules` command module and base command wiring
- [done] feat(thegent): export service helpers used by CLI (`audit_shared_modules_across_repos`, `sync_project_modules_from_repos`)
- [done] feat(thegent): add `--include-repo` / `--exclude-repo` to `phench projects run|matrix`.
- [done] test(thegent): add targeted smoke tests for include/exclude combinations on run/matrix command paths.
- [done] docs(thegent): document `--include-repo` / `--exclude-repo` options for `phench projects run`.

## Phase 1: Foundation and Discovery [discovery]

1. [done] Phase1.01 - Confirm module boundary model and repo scan assumptions.
2. [done] Phase1.02 - Add cross-repo audit helper to enumerate shared module ownership signals.
3. [done] Phase1.03 - Add cross-repo sync helper to harvest repo-local module manifests.
4. [done] Phase1.04 - Add default repo exclusion set for shared scan and sync (`4sgm`, `trace`, `parpour`, `civ`).
5. [done] Phase1.05 - Wire helper imports/exports for top-level `thegent.phench` API.

## Phase 2: CLI Surface [commandization]

6. [done] Phase2.01 - Register `phench modules` typer namespace.
7. [done] Phase2.02 - Register `phench modules audit` command and options.
8. [done] Phase2.03 - Register `phench modules sync` command and options.
9. [done] Phase2.04 - Route `phench modules` dispatches through dedicated service adapters.
10. [done] Phase2.05 - Print JSON payloads for both new commands.
11. [done] Phase2.06 - Add command-level integration tests for dispatch paths under `tests/commands/test_apps_main.py`.
12. [done] Phase2.07 - Add CLI reference docs for `phench modules audit|sync`.

## Phase 3: Service Validation [validation]

13. [done] Phase3.01 - Add unit tests for `audit_shared_modules_across_repos` including filters/excludes.
14. [done] Phase3.02 - Add unit tests for `sync_project_modules_from_repos` dry-run mode.
15. [done] Phase3.03 - Add unit tests for `sync_project_modules_from_repos` conflict detection and overwrite behavior.
16. [done] Phase3.04 - Verify default repo exclusions are honored across both helpers.
17. [done] Phase3.05 - Confirm error paths for invalid manifests and missing JSON content.

## Phase 4: Runtime and Governance Integration [orchestration]

18. [done] Phase4.01 - Add `Phenotype/projects` destination manifest generation integration checks.
19. [done] Phase4.02 - Confirm merged module manifests are sorted and deterministic.
20. [done] Phase4.03 - Validate sync behavior under mixed include/exclude module filters.
21. [done] Phase4.04 - Validate audit output `moduleization_candidates` against existing `projects/modules`.
22. [done] Phase4.05 - Add targeted smoke command tests in local workflow to ensure `--include-repo/--exclude-repo` combos.

## Phase 5: Documentation and Delivery [handoff]

23. [done] Phase5.01 - Update WBS to reflect all remaining moduleization and worktree follow-up tasks.
24. [done] Phase5.02 - Track residual work for worktree split lanes (`thegent-app`, `thegent-mcp`, `thegent-control-plane`, `thegent-execution`, `thegent-governance`).
25. [done] Phase5.03 - Capture remaining blockers, risks, and next-step execution plan for handoff.
26. [done] Phase5.04 - Run quality verification and report residual findings.

## Phase 6: Worktree Split and Lane Handoff [decomposition]

27. [done] P6.01 - Record residual split manifest for `thegent-app`.
28. [done] P6.02 - Record residual split manifest for `thegent-mcp`.
29. [done] P6.03 - Record residual split manifest for `thegent-control-plane`.
30. [done] P6.04 - Record residual split manifest for `thegent-execution`.
31. [done] P6.05 - Record residual split manifest for `thegent-governance`.
32. [done] P6.06 - Stage `thegent-app` worktree bootstrap and lane ownership.
33. [done] P6.07 - Stage `thegent-mcp` worktree bootstrap and lane ownership.
34. [done] P6.08 - Stage `thegent-control-plane` worktree bootstrap and lane ownership.
35. [done] P6.09 - Stage `thegent-execution` worktree bootstrap and lane ownership.
36. [done] P6.10 - Stage `thegent-governance` worktree bootstrap and lane ownership.
37. [done] P6.11 - Define minimal API boundaries for `thegent-app`.
38. [done] P6.12 - Define minimal API boundaries for `thegent-mcp`.
39. [done] P6.13 - Define minimal API boundaries for `thegent-control-plane`.
40. [done] P6.14 - Define minimal API boundaries for `thegent-execution`.
41. [done] P6.15 - Define minimal API boundaries for `thegent-governance`.
42. [done] P6.16 - Add lane-specific `Taskfile` targets for `thegent-app`.
43. [done] P6.17 - Add lane-specific `Taskfile` targets for `thegent-mcp`.
44. [done] P6.18 - Add lane-specific `Taskfile` targets for `thegent-control-plane`.
45. [done] P6.19 - Add lane-specific `Taskfile` targets for `thegent-execution`.
46. [done] P6.20 - Add lane-specific `Taskfile` targets for `thegent-governance`.
47. [done] P6.21 - Add smoke tests for repo filtering under `thegent-app` split workflow.
48. [done] P6.22 - Add smoke tests for repo filtering under `thegent-mcp` split workflow.
49. [done] P6.23 - Add smoke tests for repo filtering under `thegent-control-plane` split workflow.
50. [done] P6.24 - Add smoke tests for repo filtering under `thegent-execution` split workflow.
51. [done] P6.25 - Add smoke tests for repo filtering under `thegent-governance` split workflow.
52. [done] P6.26 - Publish lane handoff report with blockers, owners, and sequencing.
53. [done] P6.27 - Archive phase evidence for handoff review.
54. [todo] P6.28 - Open phased PRs from lane worktrees and verify merge queue order.
55. [done] P6.29 - Capture runtime smoke matrix for each split lane.
56. [in_progress] P6.30 - Finalize moduleization acceptance matrix and close lane residuals.

## Dependencies (DAG)

- P1.01 -> P1.02 -> P1.03
- P1.02 -> P2.01
- P1.03 -> P2.02, P2.03
- P1.04 -> P2.02, P2.03, P3.04
- P1.05 -> P2.04
- P2.01 -> P2.05 -> P2.06 -> P2.07 -> P3.01
- P3.01 -> P3.02 -> P3.03
- P3.03 -> P4.01
- P1.03 -> P3.01
- P1.04 -> P3.04
- P4.05 -> P5.01
- P5.04 -> P5.03
- P6.01 -> P6.02 -> P6.03 -> P6.04 -> P6.05
- P6.01 -> P6.06 -> P6.11 -> P6.16 -> P6.21 -> P6.26
- P6.02 -> P6.07 -> P6.12 -> P6.17 -> P6.22 -> P6.26
- P6.03 -> P6.08 -> P6.13 -> P6.18 -> P6.23 -> P6.26
- P6.04 -> P6.09 -> P6.14 -> P6.19 -> P6.24 -> P6.26
- P6.05 -> P6.10 -> P6.15 -> P6.20 -> P6.25 -> P6.26

## Status Legend

- [done] - Completed and verified in code.
- [todo] - Planned or in progress.
- [in_progress] - Actively being implemented.
- [blocked] - Waiting on external gate or dependency.

## Blocker / Risk Register

- P6.28, P6.30, P6.31, and P6.39 remain active and require dedicated branch capacity for PR mechanics and merge-order validation.
- P6.32, P6.33, P6.39–P6.46 are blocked on lane branch creation/PR workflow execution.
- P6.27 is now complete at the handoff-doc level; evidence set is documented in `phase-evidence-archive.md`.
- P6.32 now includes PR anchor map and merge sequencing checklists; these now live in `docs/changes/shared-modules/thegent-module-lane-bootstraps-v1/{lane-pr-anchor-map.md, merge-sequencing-checklist.md}`.
- No matrix-level regression test was added for `projects matrix` include/exclude output ordering; this remains deferred to first implementation PR.

## Critical Path (Current)

1. P1.01 -> P1.02 -> P1.03 -> P2.01 -> P2.02 -> P2.03 -> P3.01 -> P3.03 -> P4.01 -> P4.05 -> P5.01 -> P6.01 -> P6.11 -> P6.16 -> P6.26
