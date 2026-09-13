# Unified Worktree & Workflow Governance

**Status:** Active Policy
**Supersedes:** `WORKTREE_SCALE_COMMIT_VERSION_PR_POLICY.md` (still authoritative for commit/PR/merge rules — this doc adds the path schema and system harmonization layer)
**Systems Harmonized:** thegent worktree policy + BMAD lifecycle phases + AgilePlus change anchors
**Last Updated:** 2026-02-24

---

## 1. Purpose

This document establishes a single, unified taxonomy for:

1. **Where** worktrees live on disk (path schema)
2. **What state** a worktree is in (lifecycle state)
3. **How** work in a worktree maps to BMAD phases and AgilePlus change IDs
4. **Which tooling** enforces each layer

It does not replace the commit, versioning, or PR rules in `WORKTREE_SCALE_COMMIT_VERSION_PR_POLICY.md` — those remain authoritative. It extends them with a physical path convention and cross-system vocabulary.

---

## 2. Core Invariants (Non-Negotiable)

1. Primary checkout is always pinned to `main`. Never do feature work there.
2. All non-primary worktrees live under `<repo>/.worktrees/` (or `$THGENT_WORKTREE_ROOT`).
3. Worktree paths are deterministic from their metadata — no ad-hoc naming.
4. Worktrees outside `.worktrees/` (e.g. `/tmp/`, `~/`, stranded from renames) are **non-compliant** and must be migrated or pruned.
5. A worktree's path encodes its full context: repo, domain, scale, change anchor, and state.

---

## 3. Unified Path Schema

```
<repo>/.worktrees/<domain>/<scale>/<change-anchor>/<state>/
```

### 3.1 Schema Segments

| Segment           | Source                                     | Values                                                                                         |
| ----------------- | ------------------------------------------ | ---------------------------------------------------------------------------------------------- |
| `<repo>`          | Git repo name                              | `thegent`, `cliproxy++`, `heliosHarness`, etc.                                                 |
| `<domain>`        | Task classifier `domain` field             | `backend`, `frontend`, `infra`, `data`, `docs`, `research`, `security`, `qa`, `release`, `ops` |
| `<scale>`         | Task classifier `scale` field              | `xs`, `s`, `m`, `l`, `xl`                                                                      |
| `<change-anchor>` | AgilePlus change-id (verb-led, kebab-case) | e.g. `fix-mcp-timeout`, `add-dag-tests`, `refactor-config-layer`                               |
| `<state>`         | Lifecycle state (see §4)                   | `active`, `review`, `blocked`, `integration`, `done`                                           |

### 3.2 Full Example Paths

```
thegent/.worktrees/backend/m/fix-mcp-timeout/active/
thegent/.worktrees/qa/s/add-dag-tests/review/
thegent/.worktrees/infra/xs/bump-lint-config/done/
cliproxy++/.worktrees/security/l/clear-text-logging-v2/blocked/
heliosHarness/.worktrees/infra/m/infra-work/active/
```

### 3.3 Git Branch Name

The git branch name is derived from the path (not the reverse):

```
<domain>/<scale>/<change-anchor>
```

Examples:

- `backend/m/fix-mcp-timeout`
- `qa/s/add-dag-tests`
- `security/l/clear-text-logging-v2`

Legacy branch names (e.g. `thegent-mcp-fix`, `feature/wl-implementation`) are allowed in existing branches but new branches must use this schema.

---

## 4. Lifecycle States

States map to BMAD phases and AgilePlus proposal stages.

| State         | Dir Name       | BMAD Phase Equivalent             | AgilePlus Stage           | Meaning                                                 |
| ------------- | -------------- | --------------------------------- | ------------------------- | ------------------------------------------------------- |
| `active`      | `active/`      | Phase 4 — Implementation          | Apply                     | Work in progress, agent or human actively committing    |
| `review`      | `review/`      | Phase 4 — Review Story            | Apply (pending approval)  | PR open or awaiting code review                         |
| `blocked`     | `blocked/`     | Phase 3 — Readiness / Solutioning | Propose                   | Waiting on dependency, decision, or upstream merge      |
| `integration` | `integration/` | Phase 4 — Sprint Planning / Merge | Apply (integration train) | Merge train or integration worktree in progress         |
| `done`        | `done/`        | Post Phase 4 — Retrospective      | Archive                   | Branch merged, worktree retained briefly before pruning |

### 4.1 State Transitions

```
[proposed] → active → review → integration → done
                ↓
            blocked → active (when unblocked)
```

State is changed by renaming the worktree directory:

```bash
# move from active to review
git worktree move .worktrees/backend/m/fix-mcp-timeout/active \
                  .worktrees/backend/m/fix-mcp-timeout/review
```

Or via the governance script (see §7):

```bash
./scripts/worktree_governance.sh state <change-anchor> review
```

---

## 5. BMAD Phase → Worktree Mapping

BMAD defines 5 phases (0–4) plus a parallel testing track. Each maps to a worktree state or signals that no worktree is needed yet.

| BMAD Phase         | Name                                       | Worktree Needed?          | State                                 |
| ------------------ | ------------------------------------------ | ------------------------- | ------------------------------------- |
| 0                  | Documentation / Brownfield Capture         | No                        | — (docs only)                         |
| 1                  | Analysis (research, brainstorm)            | No                        | — (docs only)                         |
| 2                  | Planning (PRD, UX, tech-spec)              | No                        | — (docs only)                         |
| 3                  | Solutioning (architecture, epics, stories) | No until approved         | `blocked` if pre-approved work queued |
| 4 — Story Creation | Dev story scaffold                         | Yes                       | `active`                              |
| 4 — Implementation | Active coding                              | Yes                       | `active`                              |
| 4 — Review         | PR / code review                           | Yes                       | `review`                              |
| 4 — Integration    | Merge train                                | Yes                       | `integration`                         |
| 4 — Retrospective  | Post-merge                                 | Optional                  | `done`                                |
| Testing (parallel) | ATDD, CI, coverage                         | Yes (parallel to Phase 4) | `active` under `qa/` domain           |

**Rule:** Do not create a worktree during BMAD Phases 0–2. Create the worktree at the start of Phase 4 (when a dev story exists and work is approved).

---

## 6. AgilePlus Change Anchor Integration

Every worktree's `<change-anchor>` segment **is** (or maps 1:1 to) an AgilePlus `change-id`.

This means:

- Every worktree has a corresponding `agileplus/changes/<change-anchor>/` directory in the repo
- `proposal.md` in that change dir is the source-of-truth for what the worktree is doing
- `tasks.md` drives the commit sequence inside the worktree
- When the worktree reaches `done`, run `agileplus archive <change-anchor> --yes`

### 6.1 Exceptions (no AgilePlus proposal required)

Per AgilePlus policy, skip the proposal for:

- Bug fixes (typos, formatting, dependency bumps, config changes)
- Tests for existing behavior

For these, use a descriptive `<change-anchor>` that starts with `fix-` or `test-` and omit the `agileplus/changes/` scaffold. The worktree path schema still applies.

### 6.2 Worktree ↔ AgilePlus Mapping Example

```
thegent/.worktrees/backend/m/fix-mcp-timeout/active/
  ↕
thegent/agileplus/changes/fix-mcp-timeout/
  ├── proposal.md
  ├── tasks.md
  └── specs/mcp-client/spec.md
```

---

## 7. Tooling

### 7.1 Existing Script (extended)

`./scripts/worktree_governance.sh` must expose the canonical governance surface:

```bash
# Create a policy-compliant worktree
./scripts/worktree_governance.sh new <domain> <scale> <change-anchor> [start-point]

# Check all worktrees comply with schema
./scripts/worktree_governance.sh check

# Print expected path for a change anchor
./scripts/worktree_governance.sh path <domain> <scale> <change-anchor> <state>

# Transition a worktree's state
./scripts/worktree_governance.sh state <change-anchor> <new-state>

# List all worktrees with their metadata
./scripts/worktree_governance.sh list

# Refresh a tracked worktree from an upstream ref
./scripts/worktree_governance.sh refresh <change-anchor> [--remote <name>] [--ref <upstream-ref>]

# Prune done/broken worktrees
./scripts/worktree_governance.sh prune [--dry-run]
```

The ergonomic CLI front door mirrors the same contract:

```bash
thegent worktree new <domain> <scale> <change-anchor> [start-point]
thegent worktree state <change-anchor> <new-state>
thegent worktree list
thegent worktree refresh <change-anchor> [--remote origin] [--ref origin/canary]
thegent worktree prune [--dry-run]
thegent worktree check
thegent help worktree
thegent help git
```

### 7.2 `thg_new_worktree` Wrapper

The existing `thg_new_worktree` shell helper should be updated to call the governance script's new signature:

```bash
thg_new_worktree <domain> <scale> <change-anchor> [start-point]
```

### 7.3 BMAD Integration Point

When starting BMAD Phase 4 (dev story), the first action after story approval is:

```bash
./scripts/worktree_governance.sh new <domain> <scale> <change-anchor>
```

If using an AgilePlus proposal, run `agileplus validate <change-anchor> --strict` first.

### 7.4 Canary and Refresh Tracks

The canonical refresh rule and command surface live in `UNIFIED_WORKTREE_WORKFLOW_GOVERNANCE.md`. Use that document as the single source of truth for long-lived PR lanes, canary branches, and high-extreme package branches. The refresh policy is exposed through the script, CLI, consolidated MCP `thegent_worktree` tool, and the named `task quality:governance:canary-refresh` and `task quality:pre-push:strict-governance` entrypoints, and the canonical commands are listed there.

CI enforces the same rule through `task quality:governance:canary-refresh` so the workflow fails if the explicit refresh policy markers drift out of the canonical docs.

---

## 8. Legacy Worktree Migration Plan

The following worktrees are non-compliant (broken gitdir pointers from `/temp-PRODVERCEL/` rename, or misplaced in `~/` or `/tmp/`). They must be migrated or pruned.

### 8.1 Broken (gitdir pointer to missing path) — Prune After Salvage

| Directory                           | Last Known Branch                  | Action                             |
| ----------------------------------- | ---------------------------------- | ---------------------------------- |
| `repos/thegent-dag-tests`           | unknown                            | Salvage any unique commits → prune |
| `repos/thegent-flaky-tests`         | unknown                            | Salvage → prune                    |
| `repos/thegent-lint-fix`            | unknown                            | Salvage → prune                    |
| `repos/thegent-mcp-fix`             | unknown                            | Salvage → prune                    |
| `repos/thegent-mcp-fix2`            | unknown                            | Salvage → prune                    |
| `repos/thegent-mcp-fix3`            | unknown                            | Salvage → prune                    |
| `repos/thegent-mcp-fix4`            | unknown                            | Salvage → prune                    |
| `repos/thegent-merge`               | unknown                            | Salvage → prune                    |
| `repos/thegent-output-tests`        | unknown                            | Salvage → prune                    |
| `repos/thegent-skips-v2`            | unknown                            | Salvage → prune                    |
| `repos/thegent-v2`                  | main (empty)                       | Prune (empty)                      |
| `repos/cliproxy++-config-fix`       | fix/config-build                   | Salvage → prune                    |
| `repos/cliproxy++-security`         | fix/security-clear-text-logging-v2 | Salvage → prune                    |
| `repos/heliosHarness-orchestration` | feature/sub-agent-orchestration    | Salvage → prune                    |

### 8.2 Active but Misplaced — Migrate to Schema

| Directory                                      | Branch                      | Target Path                                                       |
| ---------------------------------------------- | --------------------------- | ----------------------------------------------------------------- |
| `/private/tmp/wl-impl`                         | `feature/wl-implementation` | `thegent/.worktrees/backend/m/wl-impl/active/`                    |
| `~/cliproxy++-security`                        | `main` (standalone clone)   | Evaluate: merge to `repos/cliproxy++` or discard                  |
| `~/cliproxy++-security-work`                   | `security-fix`              | `cliproxy++/.worktrees/security/m/clear-text-logging-v2/blocked/` |
| `temp-PRODVERCEL-485/kush/heliosHarness-infra` | `feature/infra-work`        | `heliosHarness/.worktrees/infra/m/infra-work/active/`             |

### 8.3 Migration Steps (per worktree)

1. Run `git log --oneline -10` in the worktree dir to identify unique commits.
2. If unique commits exist: cherry-pick or create a patch. If no unique commits: skip to step 4.
3. Create a compliant worktree: `./scripts/worktree_governance.sh new <domain> <scale> <change-anchor>`
4. Apply any salvaged commits to the new worktree.
5. Remove the old worktree directory: `git worktree remove --force <path>` then `git worktree prune`.

### 8.4 Remediation Report

Use `task quality:governance:legacy-remediation-report` to generate a remediation artifact for all
legacy worktrees that still sit outside the canonical `.worktrees/` root. The report captures the
current dirty count, branch divergence, prunable state, and a deterministic next action so legacy
lanes can be triaged before migration or pruning.

The canonical migration command for clean legacy lanes is `thegent worktree migrate-legacy <legacy-path> <domain> <scale> <change-anchor> [state]`. It must consume the remediation report first, operate only on the clean migratable entries it names, rename the branch to the structured tuple, and move the worktree into the canonical root before re-running governance checks.

---

## 9. Vocabulary Cross-Reference

| This System        | BMAD Term                                | AgilePlus Term                  | Task Classifier Field           |
| ------------------ | ---------------------------------------- | ------------------------------- | ------------------------------- |
| `<domain>`         | Agent persona domain (backend, QA, etc.) | capability folder               | `domain`                        |
| `<scale>`          | Story size / sprint scope                | — (not used)                    | `scale` (XS/S/M/L/XL)           |
| `<change-anchor>`  | Story ID / epic slug                     | `change-id`                     | `task_id`                       |
| `active`           | Phase 4 — Implementation                 | Apply stage                     | —                               |
| `review`           | Phase 4 — Review Story                   | Apply (pending)                 | —                               |
| `blocked`          | Phase 3 — Readiness                      | Propose (approved, not started) | —                               |
| `integration`      | Phase 4 — Sprint Planning / merge train  | Apply (integration)             | `worktree_mode: integration`    |
| `done`             | Retrospective                            | Archive                         | —                               |
| XS worktree mode   | Single-story, shared lane                | skip proposal                   | `worktree_mode: shared_lane`    |
| M worktree mode    | Lane-dedicated                           | proposal required               | `worktree_mode: lane_dedicated` |
| L/XL worktree mode | Integration worktree                     | proposal required               | `worktree_mode: integration`    |

---

## 10. Governance Checklist (New Work)

### Pre-Creation (Phase 0 — Context Load)

- [ ] `agileplus list` — check active changes for conflicts
- [ ] `agileplus list --specs` — check existing capabilities
- [ ] `git worktree list` — check active worktrees
- [ ] Read `agileplus/project.md` and affected `specs/<capability>/` files
- [ ] Task classified: domain, scale, risk, coupling filled in

### Outcome Definition (Phase 1 — Goal-Backward)

- [ ] `must_haves` defined: observable outcomes stated (what is true when done)
- [ ] `verify_commands` defined: runnable command proving each must_have
- [ ] If change-anchor slug needs "and": split into two changes

### Proposal (Phase 2)

- [ ] If M/L/XL: AgilePlus proposal scaffolded (`proposal.md`, `tasks.md`, `design.md`)
- [ ] Each task in `tasks.md` has a `verify:` line with a runnable command (Nyquist)
- [ ] If L/XL: `design.md` locks all naming, API, error patterns before implementation
- [ ] `agileplus validate <id> --strict` passes
- [ ] Proposal approved (worktree stays in `blocked/` until this gate clears)

### Execution Setup (Phase 3–4)

- [ ] Wave decomposition done for M/L/XL: each task labeled Wave N
- [ ] Worktree created: `./scripts/worktree_governance.sh new <domain> <scale> <change-anchor>`
- [ ] `SESSION_STATE.md` initialized in worktree root (current task, decisions, blockers, next action)
- [ ] Worktree path verified: `<repo>/.worktrees/<domain>/<scale>/<change-anchor>/active/`

### Execution (Phase 5)

- [ ] Wave 1 tasks delegated to fresh subagents in parallel (thin orchestrator)
- [ ] `SESSION_STATE.md` updated after each task
- [ ] Atomic commits per task: `<type>(<domain>/<change-anchor>): <description>`
- [ ] No stopping at "milestones" — halt only at 3 failures, missing config, new dependency, or gate

### Verification (Phase 6)

- [ ] All `verify:` commands from `tasks.md` pass
- [ ] `task quality` passes
- [ ] All `must_haves` observable from outside the system
- [ ] `agileplus validate <id> --strict` passes
- [ ] State transitioned to `review/`: `./scripts/worktree_governance.sh state <change-anchor> review`

### Integration and Archive (Phase 7)

- [ ] On merge: `agileplus archive <change-anchor> --yes`
- [ ] `git worktree prune`
- [ ] Worktree dir moved to `done/` or removed

<!-- PHENOTYPE_GOVERNANCE_OVERLAY_V1 -->

## Phenotype Governance Overlay v1

- Enforce `TDD + BDD + SDD` for all feature and workflow changes.
- Enforce `Hexagonal + Clean + SOLID` boundaries by default.
- Favor explicit failures over silent degradation; required dependencies must fail clearly when unavailable.
- Keep local hot paths deterministic and low-latency; place distributed workflow logic behind durable orchestration boundaries.
- Require policy gating, auditability, and traceable correlation IDs for agent and workflow actions.
- Document architectural and protocol decisions before broad rollout changes.
