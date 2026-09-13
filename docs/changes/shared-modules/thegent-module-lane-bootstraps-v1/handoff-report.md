# Handoff Report: thegent Module Split Lane Transition

- **Date:** 2026-03-03
- **Source commit:** 0ed9c3a7f
- **Scope:** `thegent-app`, `thegent-mcp`, `thegent-control-plane`, `thegent-execution`, `thegent-governance`
- **Current state:** Lane prep is complete; handoff and operational sequencing remains.

## 1) What is already done

- `phench projects` now supports include/exclude repo filtering for `run` and `matrix`.
- Split-lane bootstrap tasks added to `Taskfile.yml` for all five lanes.
- Per-lane split smoke tests added for repo-filter path in `tests/commands/test_apps_main.py`.
- Module boundary docs added for each lane.
- WBS updated to mark P6.06..P6.25 as complete.

## 2) Blockers and risks

- P6.26 to P6.29 are complete from this baseline: report published, evidence archived, and runtime smoke matrix captured.
- P6.28 requires explicit PR creation from worktrees and merge-order validation; currently blocked by branch/PR capacity.
- Runtime matrix for matrix-ordering behavior is deferred to first lane implementation.
- Merge/train PR sequencing requires branch capacity for worktree PR concurrency control.
- Evidence artifacts must be attached per lane review before mark-complete.

## 3) Lane owners and responsibilities

| Module                | Owner              | Immediate next responsibility                               |
| --------------------- | ------------------ | ----------------------------------------------------------- |
| thegent-app           | thegent-runtime    | Own app-level execution orchestration and bootstrap handoff |
| thegent-mcp           | thegent-mcp        | Own MCP protocol boundary and transport behavior            |
| thegent-control-plane | thegent-platform   | Own control policy and orchestration sequencing             |
| thegent-execution     | thegent-execution  | Own run-time execution adapters and profile routing         |
| thegent-governance    | thegent-governance | Own policy/quality guardrails and governance integration    |

## 4) Sequencing recommendation

- Wave A: create lane worktrees and run bootstrap commands in each lane.
- Wave B: execute `lane:split:<lane>:smoke` inside each lane branch after schema and manifest adoption.
- Wave C: open PRs in `lane/<module>-split-bootstrap` branches with module-scoped scope.
- Wave D: merge through integration lane in dependency order, then archive openspec and prune worktrees.

## 5) Merge and verification requirements

- Every PR must pass local lane smoke (`task lane:split:<lane>:smoke`) and repo-targeted review.
- Open PR stack must follow worktree + branch policy in:
  - `docs/governance/WORKTREE_AND_DELEGATION_INDEX.md`
  - `docs/governance/WORKTREE_SCALE_COMMIT_VERSION_PR_POLICY.md`
  - `docs/governance/UNIFIED_WORKTREE_WORKFLOW_GOVERNANCE.md`
- Runtime validation for each lane uses `task lane:split:all-smoke` as baseline pass before PR close.

## 6) PR anchor map (provisional)

- thegent-app: `lane/split-thegent-app-bootstrap` _(TBD: PR number)_
- thegent-mcp: `lane/split-thegent-mcp-bootstrap` _(TBD: PR number)_
- thegent-control-plane: `lane/split-thegent-control-plane-bootstrap` _(TBD: PR number)_
- thegent-execution: `lane/split-thegent-execution-bootstrap` _(TBD: PR number)_
- thegent-governance: `lane/split-thegent-governance-bootstrap` _(TBD: PR number)_

## 7) Merge order and blocker notes

- Planned merge order: app -> mcp -> control-plane -> execution -> governance.
- Verification owner: thegent-platform.
- Blocked until lane PR branches exist and are review-ready.
