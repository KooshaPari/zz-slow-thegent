# Wave 78 — Next 50 Tasks (Execution Backlog)

Date: 2026-02-23
Scope: Worktree governance, Ln delegation, enforcement, migration, CI parity.

## Lane A — Worktree Layout Enforcement (8)

1. W78-A01: Add strict `worktree_governance check` CI job. Depends: none.
2. W78-A02: Add `worktree_governance new` docs + examples to CLI docs. Depends: W78-A01.
3. W78-A03: Add branch slug sanitization tests for naming policy. Depends: W78-A01.
4. W78-A04: Add policy fixture tests for `THGENT_WORKTREE_ROOT` override. Depends: W78-A01.
5. W78-A05: Add legacy warning suppression threshold config. Depends: W78-A01.
6. W78-A06: Add migration report generator for nonconforming worktrees. Depends: W78-A03.
7. W78-A07: Add `task governance:worktree:migrate-plan`. Depends: W78-A06.
8. W78-A08: Gate merge on worktree-policy conformance report artifact. Depends: W78-A07.

## Lane B — Delegation Classifier and Contracts (8)

1. W78-B01: Implement classifier loader for `TASK_CLASSIFIER_SCHEMA.yaml`. Depends: none.
2. W78-B02: Add schema validation tests for classifier fields/outputs. Depends: W78-B01.
3. W78-B03: Add delegation contract markdown template generator. Depends: W78-B01.
4. W78-B04: Add domain playbook resolver by task domain. Depends: W78-B01.
5. W78-B05: Add overlap-risk score calculator helper. Depends: W78-B01.
6. W78-B06: Add tier routing (`L2/L3/Ln`) decision helper. Depends: W78-B05.
7. W78-B07: Add task-to-worktree placement recommendation endpoint. Depends: W78-B06.
8. W78-B08: Add end-to-end classifier fixture tests with 20 scenarios. Depends: W78-B07.

## Lane C — Hooks, Taskfile, and Local CI Parity (7)

1. W78-C01: Add `quality:governance:policy` into local gha pre-push workflow parity script. Depends: none.
2. W78-C02: Add deterministic docs-build timeout defaults in CI and local wrappers. Depends: none.
3. W78-C03: Add pre-push output summary for governance policy checks. Depends: W78-C01.
4. W78-C04: Add hook-stage telemetry event for governance check start/end. Depends: W78-C03.
5. W78-C05: Add `quality:pre-push:strict-governance` task alias. Depends: W78-C01.
6. W78-C06: Add regression test ensuring hooks pass filename scoping. Depends: W78-C05.
7. W78-C07: Add failing test when worktree helper is missing/non-executable. Depends: W78-C01.

## Lane D — Observability and SLOs (7)

1. W78-D01: Add worktree policy metric counters (pass/fail/warn). Depends: none.
2. W78-D02: Add delegation efficiency counters (`L1 direct` vs delegated). Depends: none.
3. W78-D03: Add conflict-rate metric keyed by lane and wave. Depends: W78-D01.
4. W78-D04: Add rework-rate metric keyed by commit package. Depends: W78-D02.
5. W78-D05: Add trace context linkage from task id -> commit pkg -> PR branch. Depends: W78-D02.
6. W78-D06: Add SLO check task for governance metrics thresholds. Depends: W78-D03.
7. W78-D07: Add incident report template for governance regressions. Depends: W78-D06.

## Lane E — Migration and Cleanup (7)

1. W78-E01: Inventory all existing worktrees and classify conformance. Depends: none.
2. W78-E02: Generate rename/move plan for nonconforming worktrees. Depends: W78-E01.
3. W78-E03: Add dry-run migrator for worktree path/name normalization. Depends: W78-E02.
4. W78-E04: Add apply mode migrator with safety checkpoints. Depends: W78-E03.
5. W78-E05: Add rollback manifest for migration batches. Depends: W78-E04.
6. W78-E06: Add integration test for migration idempotency. Depends: W78-E04.
7. W78-E07: Mark legacy override (`THGENT_WORKTREE_ALLOW_LEGACY`) removal criteria. Depends: W78-E06.

## Lane F — Protocol and Control Plane Alignment (7)

1. W78-F01: Define MCP boundary for governance-related tool surfaces. Depends: none.
2. W78-F02: Define A2A handoff payload contract for delegation decisions. Depends: none.
3. W78-F03: Add internal control-plane schema for placement decisions. Depends: W78-B06.
4. W78-F04: Add compatibility tests across MCP/A2A/internal schemas. Depends: W78-F03.
5. W78-F05: Add policy versioning doc for control-plane schema changes. Depends: W78-F03.
6. W78-F06: Add protocol audit report template for each rollout phase. Depends: W78-F04.
7. W78-F07: Add conformance gate requiring protocol artifact bundle. Depends: W78-F06.

## Lane G — Release and Rollout Governance (6)

1. W78-G01: Add rollout phases (10/50/100) checklist with entry/exit criteria. Depends: none.
2. W78-G02: Add merge-train policy doc for governance changes. Depends: W78-G01.
3. W78-G03: Add release note template requiring governance deltas. Depends: W78-G02.
4. W78-G04: Add failure policy for blocked governance checks in mainline. Depends: W78-G02.
5. W78-G05: Add fast rollback procedure for governance hook regressions. Depends: W78-G04.
6. W78-G06: Add final signoff bundle task combining lane artifacts. Depends: W78-G05.

## Immediate Start Set (parallel-safe)

1. W78-A01
2. W78-B01
3. W78-C01
4. W78-D01
5. W78-E01
6. W78-F01
7. W78-G01
