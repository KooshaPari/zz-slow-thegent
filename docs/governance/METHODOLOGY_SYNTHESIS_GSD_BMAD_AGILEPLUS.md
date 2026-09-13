# Methodology Synthesis: GSD + BMAD + AgilePlus + thegent

**Status:** Active Reference
**Date:** 2026-02-24
**Purpose:** Extract the best process ideas from GSD, BMAD, and AgilePlus and integrate them
into the thegent governance model. No new tooling installed — methodology only.

---

## 1. The Three Systems at a Glance

| Dimension               | GSD                                                     | BMAD                                                 | AgilePlus                                                     |
| ----------------------- | ------------------------------------------------------- | ---------------------------------------------------- | ------------------------------------------------------------- |
| **Core problem solved** | Context rot; fresh agents per task                      | AI agent inconsistency; pre-negotiate all decisions  | Brownfield spec drift; audit-safe incremental change          |
| **Planning model**      | Goal-backward (outcomes → artifacts → tasks)            | Requirements-down (stakeholder → PRD → arch → story) | Change-driven (propose delta → approve → implement → archive) |
| **Unit of work**        | Phase (2–3 task atomic plan, ~50% of 200k context)      | Story (acceptance criteria + tasks + DoD checklist)  | Change proposal (verb-led ID, per-capability spec delta)      |
| **State storage**       | `.planning/` filesystem                                 | `sprint-status.yaml` + document artifacts            | `changes/` directory structure + `specs/` canonical truth     |
| **Context strategy**    | Fresh 200k subagent per plan; thin orchestrator         | Artifact-as-memory; context.xml for cold-start       | specs/ = current truth; changes/ = proposed truth             |
| **Parallelism**         | Wave-based (independent plans simultaneously)           | Sequential roles (Analyst → PM → Arch → Dev)         | Sequential within a change; conflict detection across changes |
| **Human gates**         | Phase discussion confirmation; `yolo` skips all         | Extensive checkpoints at every phase                 | Hard approval gate before implementation starts               |
| **Verification model**  | Nyquist (test-map before code) + goal-backward verifier | Dev story DoD checklist + QA agent                   | agileplus validate --strict before approval                   |
| **Commit discipline**   | Atomic per task, auto-committed                         | Bulk at story completion                             | Incremental per capability delta                              |

---

## 2. What Each System Does Best (Keep These)

### From GSD

**Keep:** Fresh-agent-per-task architecture

- Context quality degrades monotonically in a long session. The quality curve is real.
- Solution: never accumulate work in one agent. Delegate to fresh subagents; orchestrator stays lean.
- **Integration:** thegent's Task tool delegation pattern already follows this. Reinforce it explicitly.

**Keep:** Goal-backward planning

- Start from observable outcomes (truths), work backward to artifacts, then to tasks.
- This catches underspecified requirements — if you cannot state what a completed feature looks like from the outside, the plan is not ready.
- **Integration:** Add to the worktree governance checklist: define `must_haves` (observable outcomes) before scaffolding a worktree.

**Keep:** Atomic plan sizing

- Each plan: 2–3 tasks, sized to consume ~50% of a fresh context window.
- This makes context rot structurally impossible within a single execution unit.
- **Integration:** Map to thegent's scale taxonomy: XS/S plans = 1 atomic plan, M = 2–3 plans, L/XL = phased plan set.

**Keep:** Nyquist Validation Layer

- Map automated test coverage to each requirement BEFORE writing code.
- Plans lacking a verification command for each task are rejected.
- **Integration:** Add as a required field in the AgilePlus `tasks.md` format: each task must include a `verify:` line with a runnable command.

**Keep:** Wave-based parallelism

- Independent tasks execute simultaneously across fresh agents. Dependent tasks queue.
- **Integration:** When decomposing an L/XL worktree into sub-plans, explicitly label each plan as Wave 1 (independent) or Wave N (depends on Wave N-1).

**Keep:** `.planning/`-style file-based state

- The filesystem is the message bus and memory between agents across sessions.
- **Integration:** thegent already uses `docs/`, `agileplus/changes/`, `contracts/` for this. Formalize the convention: all cross-agent state lives in files, never in agent memory.

**Keep:** Pause/resume context serialization

- Before ending a session, serialize current state and decisions to a file. On resume, load it first.
- **Integration:** Add `SESSION_STATE.md` convention to worktree — a file inside each active worktree recording: current task, decisions made, blockers, next action.

### From BMAD

**Keep:** Documents as the handoff interface

- No informal verbal handoffs. The receiver validates completeness, not the sender.
- **Integration:** Formalize the readiness signals (see §4).

**Keep:** Architecture as the consistency contract

- Before implementation begins, all naming, API shapes, error patterns, and data models must be pre-decided and written down.
- Agents implementing parallel stories reference this document — it prevents contradictory implementations.
- **Integration:** For M/L/XL changes, require `design.md` in the AgilePlus change dir (already part of AgilePlus for multi-system changes). Treat it as the consistency contract for all parallel sub-agents.

**Keep:** No-stop implementation mandate

- Do not stop at "milestones," "significant progress," or "session boundaries."
- Halt only at: 3 consecutive failures, missing required config, new dependency approval needed, or gate not met.
- **Integration:** Add to thegent's agent instruction policy: completion means DoD satisfied, not "most of it done."

**Keep:** Sprint-status as work state source of truth

- A single authoritative file tracks what work is in what state (ready-for-dev / in-progress / review).
- **Integration:** Map to the worktree state dir names (`active/`, `review/`, `blocked/`, `done/`). The worktree path IS the sprint-status file — no separate YAML needed.

**Keep:** Receiver-validates-completeness protocol

- Upstream phase produces document. Downstream phase validates it before starting.
- This prevents silent incomplete handoffs.
- **Integration:** Add pre-start checklist to worktree governance (see §4).

### From AgilePlus

**Keep:** Current-truth vs. proposed-truth separation

- `specs/` = what IS. `changes/` = what SHOULD BE. Never mix.
- **Integration:** Already in place. Reinforce: no implementation begins without a `changes/<id>/` dir and approved proposal.

**Keep:** Hard approval gate before implementation

- "Do not start implementation until proposal is reviewed and approved." (Appears twice — intentional.)
- **Integration:** The `blocked/` worktree state IS this gate. A worktree cannot move to `active/` until the proposal passes `agileplus validate --strict`.

**Keep:** Proactive conflict detection

- Before scaffolding a change, check active changes for overlapping specs.
- **Integration:** Add `agileplus list` + `agileplus list --specs` to the pre-worktree-creation checklist.

**Keep:** Simplicity forcing function

- Default to <100 lines. Single-file until proven insufficient. No frameworks without justification.
- Complexity escalation requires evidence: performance data, concrete scale numbers, or multiple proven use cases.
- **Integration:** Add to thegent's library-first policy: "start with the smallest correct implementation; escalate with evidence."

**Keep:** Capability single-responsibility check

- If describing a spec capability requires the word "AND," split it.
- **Integration:** Same rule applies to worktree change anchors. If the change-anchor slug needs "and," the worktree should be split.

---

## 3. What to Discard (Conflicts with thegent Policy)

| System    | Pattern                                            | Why Discard                                                          |
| --------- | -------------------------------------------------- | -------------------------------------------------------------------- |
| BMAD      | Sprint ceremonies, story points, stakeholder syncs | Agent-driven environment; no humans in the loop for ceremonies       |
| BMAD      | "Schedule audit," "Get approval from X"            | Forbidden in thegent plans per CLAUDE.md                             |
| BMAD      | `yolo` mode with no verification                   | All work must have validation evidence; no silent completion         |
| GSD       | `yolo` mode (skips all human gates)                | thegent requires explicit completion gates                           |
| GSD       | Greenfield-first planning                          | thegent workspace is brownfield; treat everything as existing system |
| AgilePlus | Sequential-only within a change                    | thegent prefers wave parallelism where safe; override for M/L scale  |

---

## 4. Integrated Process: The thegent Workflow

Combining the best of all three into a single coherent flow:

### Phase 0 — Context Load (from AgilePlus + BMAD)

Before any worktree is created:

```
1. agileplus list                          # What changes are active?
2. agileplus list --specs                  # What capabilities exist?
3. git worktree list                      # What worktrees are active?
4. Read agileplus/project.md               # Project conventions
5. Read relevant specs/[capability]/      # Current truth for affected areas
6. Check for conflicts with active changes
```

If this is a brownfield codebase entry point, first run the codebase mapping equivalent:

- Read `docs/reference/CODE_ENTITY_MAP.md` if it exists
- Read `docs/reference/SOFTWARE_ARCHITECTURE_REFERENCE.md`
- Identify affected modules before touching anything

### Phase 1 — Define Outcomes (from GSD)

Before writing a proposal:

```
must_haves:
  - [Observable outcome 1]: what a user/system can do or observe when done
  - [Observable outcome 2]: ...

verify_commands:
  - [command that proves must_have 1 is satisfied]
  - [command that proves must_have 2 is satisfied]
```

If you cannot fill this in, the work is not ready to start.

### Phase 2 — Propose (from AgilePlus + BMAD architecture)

For M/L/XL scale changes:

```
agileplus/changes/<change-anchor>/
  proposal.md     # business justification + scope + must_haves
  tasks.md        # ordered tasks, each with verify: command
  design.md       # architectural decisions (= BMAD consistency contract)
  specs/          # capability deltas
```

Run `agileplus validate <id> --strict`. Resolve every issue. Get approval.

For XS/S scale (bug fix, test, config): skip proposal. Use `fix-` or `test-` prefix. Still define `verify:` for each task.

### Phase 3 — Plan Decomposition (from GSD wave model)

Decompose `tasks.md` into execution waves:

```yaml
wave: 1  # Independent — can run in parallel
  - task: fix-mcp-timeout/core-retry-logic
    verify: pytest tests/test_mcp_retry.py -v
  - task: fix-mcp-timeout/error-classification
    verify: pytest tests/test_mcp_errors.py -v

wave: 2  # Depends on wave 1
  - task: fix-mcp-timeout/integration-test
    verify: pytest tests/integration/test_mcp_e2e.py -v
    depends: [core-retry-logic, error-classification]
```

Each task in a wave: 2–3 subtasks maximum, sized to fit ~50% of one agent's context window.

### Phase 4 — Create Worktree (from unified path schema)

```bash
./scripts/worktree_governance.sh new <domain> <scale> <change-anchor>
# Creates: <repo>/.worktrees/<domain>/<scale>/<change-anchor>/active/
```

Initialize the worktree's `SESSION_STATE.md`:

```markdown
# SESSION_STATE — <change-anchor>

## Current Task

[task from tasks.md being worked on]

## Decisions Made

- [key decision + rationale]

## Blockers

- none

## Next Action

[exact next step]
```

### Phase 5 — Execute (from GSD + BMAD no-stop mandate)

Execution rules:

1. **Thin orchestrator**: coordinate, never execute directly. Delegate each wave to fresh subagents.
2. **Wave parallelism**: launch all Wave 1 tasks simultaneously via Task tool.
3. **No stopping**: halt only at 3 consecutive failures, missing config, new dependency, or gate not met.
4. **Atomic commits**: one commit per task, message format: `<type>(<domain>/<change-anchor>): <description>`
5. **Update SESSION_STATE.md** after each task.

### Phase 6 — Verify (from GSD Nyquist + BMAD DoD)

After all tasks complete:

1. Run every `verify:` command from `tasks.md`. All must pass.
2. Run `task quality` (thegent quality gate).
3. Check every `must_have` from the proposal. Observable from the outside? Check.
4. Run `agileplus validate <id> --strict` one final time.
5. Move worktree to `review/` state: `./scripts/worktree_governance.sh state <change-anchor> review`

### Phase 7 — Integrate and Archive

After approval:

1. Merge to main via integration worktree (L/XL) or direct squash (XS/S).
2. `agileplus archive <change-anchor> --yes`
3. `git worktree prune`
4. Move worktree dir to `done/` or remove.

---

## 5. Readiness Signals (Solving the BMAD Handoff Gap)

The BMAD handbook identified "No formal role handoff protocol" as its acknowledged weak point. We define explicit signals:

| Signal                    | Mechanism                                                                             | Meaning                                           |
| ------------------------- | ------------------------------------------------------------------------------------- | ------------------------------------------------- |
| Proposal ready for review | `agileplus validate --strict` passes + PR/comment on proposal.md                      | Implementation approved to begin                  |
| Design ready              | `design.md` committed + comment "APPROVED"                                            | Consistency contract locked; agents may implement |
| Worktree ready for review | State dir renamed `active/` → `review/` + all verify commands pass                    | PR open, awaiting merge                           |
| Story/change complete     | All verify commands pass + `agileplus validate --strict` passes + quality gate passes | Safe to archive and merge                         |

All signals are **file-based and machine-readable** — no informal verbal handoffs.

---

## 6. Scale → Process Mapping

| Scale | AgilePlus Proposal?    | Wave Decomposition? | design.md? | Worktree Mode             |
| ----- | ---------------------- | ------------------- | ---------- | ------------------------- |
| XS    | No                     | No (single task)    | No         | shared_lane               |
| S     | No (fix-/test- anchor) | No                  | No         | shared_lane               |
| M     | Yes                    | 2–3 waves           | Optional   | lane_dedicated            |
| L     | Yes                    | 3+ waves            | Required   | integration               |
| XL    | Yes                    | Full phase set      | Required   | integration (merge train) |

---

## 7. Key Principles (Unified)

1. **Fresh agents, thin orchestrators** (GSD) — delegate to fresh subagents; never accumulate work in one degrading context.
2. **Goal-backward validation** (GSD) — define observable outcomes before writing plans; verify outcomes achieved, not tasks completed.
3. **Atomic plan sizing** (GSD) — 2–3 tasks per execution unit, sized to ~50% of one context window.
4. **Nyquist first** (GSD) — every task has a `verify:` command before implementation starts.
5. **Documents are the memory** (BMAD) — all cross-agent state lives in files; no agent-memory handoffs.
6. **Architecture is the consistency contract** (BMAD) — pre-negotiate all decisions in `design.md` before parallel agents implement.
7. **No-stop implementation** (BMAD) — halt only at explicit failure conditions; "significant progress" is not done.
8. **Receiver validates completeness** (BMAD) — downstream phase checks the handoff; sender does not self-certify.
9. **Specs = current truth; changes = proposed truth** (AgilePlus) — never mix what IS with what SHOULD BE.
10. **Hard approval gate** (AgilePlus) — worktrees do not leave `blocked/` without validated proposal approval.
11. **Simplicity by default** (AgilePlus) — smallest correct implementation first; escalate with evidence.
12. **File-based state** (all three) — the filesystem is the message bus, memory, and audit trail.

---

## 8. What This Changes in Existing Governance Docs

| Doc                                          | Update Needed                                                                                                              |
| -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `UNIFIED_WORKTREE_WORKFLOW_GOVERNANCE.md`    | Add `must_haves` to pre-creation checklist (§10); add `SESSION_STATE.md` convention; add wave labels to task decomposition |
| `WORKTREE_SCALE_COMMIT_VERSION_PR_POLICY.md` | Add commit message format with change-anchor; add no-stop mandate                                                          |
| `TASK_CLASSIFIER_SCHEMA.yaml`                | Add `must_haves` and `verify_commands` as required output fields for M/L/XL                                                |
| `DOMAIN_PLAYBOOKS.md`                        | Add wave decomposition guidance per domain                                                                                 |
| `CLAUDE.md` (global)                         | Already has Library-First, Fail-Fast, No-Fallbacks — add Goal-Backward and Nyquist as explicit named principles            |

---

## 9. Sources

| System    | Source                                                                                                                                                                                                                                     |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| GSD       | [github.com/gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done); [ccforeveryone.com/gsd](https://ccforeveryone.com/gsd); [thenewstack.io/beating-the-rot](https://thenewstack.io/beating-the-rot-and-getting-stuff-done/) |
| BMAD      | `/Users/kooshapari/CodeProjects/.bmad/` (local install); workflow YAMLs in `bmm/workflows/`                                                                                                                                                |
| AgilePlus | `/Users/kooshapari/CodeProjects/Phenotype/repos/archive/crun/agileplus/` (local usage)                                                                                                                                                     |
| thegent   | `docs/governance/WORKTREE_SCALE_COMMIT_VERSION_PR_POLICY.md`; `docs/governance/TASK_CLASSIFIER_SCHEMA.yaml`; `CLAUDE.md`                                                                                                                   |
