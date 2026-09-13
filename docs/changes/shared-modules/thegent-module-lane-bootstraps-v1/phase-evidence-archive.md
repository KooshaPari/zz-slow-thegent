# Phase Evidence Archive

## Purpose

Archive repository evidence for lane split handoff and PR readiness review.

## Included evidence (this phase)

- Code/docs changes: `Taskfile.yml`, `src/thegent/cli/apps/phench_projects.py`, `tests/commands/test_apps_main.py`.
- Boundaries: `docs/guides/thegent-*-boundary.md` (all five modules).
- Handoff docs:
  - `docs/changes/shared-modules/thegent-module-lane-bootstraps-v1/handoff-report.md`
  - `docs/changes/shared-modules/thegent-module-lane-bootstraps-v1/runtime-smoke-matrix.md`
  - `docs/changes/shared-modules/thegent-module-lane-bootstraps-v1/acceptance-matrix.md`
  - `docs/changes/shared-modules/thegent-module-lane-bootstraps-v1/lane-pr-anchor-map.md`
  - `docs/changes/shared-modules/thegent-module-lane-bootstraps-v1/merge-sequencing-checklist.md`
  - `docs/changes/shared-modules/thegent-module-lane-bootstraps-v1/proposal.md`
  - `docs/changes/shared-modules/thegent-module-lane-bootstraps-v1/tasks.md`
  - `docs/sessions/20260302-phench-modularization/03_DAG_WBS.md`
- Runtime matrix artifacts:
  - `docs/changes/shared-modules/thegent-module-lane-bootstraps-v1/artifacts/smoke-app.log`
  - `docs/changes/shared-modules/thegent-module-lane-bootstraps-v1/artifacts/smoke-mcp.log`
  - `docs/changes/shared-modules/thegent-module-lane-bootstraps-v1/artifacts/smoke-control-plane.log`
  - `docs/changes/shared-modules/thegent-module-lane-bootstraps-v1/artifacts/smoke-execution.log`
  - `docs/changes/shared-modules/thegent-module-lane-bootstraps-v1/artifacts/smoke-governance.log`
  - `docs/changes/shared-modules/thegent-module-lane-bootstraps-v1/artifacts/smoke-all.log`

## Archive workflow before done

1. Add artifact links (including `docs/sessions/20260302-phench-modularization/03_DAG_WBS.md` blocker section) and PR-anchor matrix with timestamped smoke matrix evidence.
2. Move this evidence set to `docs/changes/shared-modules/thegent-module-lane-bootstraps-v1/archive/` on finalization.
3. Run `openspec archive <change-anchor> --yes` (if applicable by anchor).
4. Move active worktree entries to done and run prune.
