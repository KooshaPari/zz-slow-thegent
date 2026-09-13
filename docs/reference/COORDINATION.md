# Multi-Level Coordination (L1/L2/L3)

**Status:** Active | **Last Updated:** 2026-02-18 | **Framework:** Three-Level Hierarchy

---

## Overview

The multi-level coordination system defines three hierarchical layers for managing concurrent work across a distributed team of AI agents and human operators. This framework ensures safe, predictable, and observable multi-actor execution without resource conflicts or work duplication.

### Three-Level Hierarchy

```
┌─────────────────────────────────────────────────────┐
│          L1: Coordinator (Claude Code)              │
│  - User intent & strategic decisions                │
│  - Work item creation & triage                       │
│  - Dependency resolution & conflict arbitration      │
│  - Progress monitoring & reporting                   │
└─────────────────────────────────────────────────────┘
                           │
                           │ Delegates to
                           ▼
┌─────────────────────────────────────────────────────┐
│        L2: Teammates (Named Agents)                 │
│  - Component ownership (auth, api, frontend, etc.)  │
│  - Task claiming & execution                        │
│  - Blockedby/Blocks relationship management         │
│  - Sub-task delegation to L3                        │
└─────────────────────────────────────────────────────┘
                           │
                           │ Dispatches to
                           ▼
┌─────────────────────────────────────────────────────┐
│       L3: Thegent Agents (Free/Premium)             │
│  - Sub-task execution (exploration, implementation) │
│  - Pattern searches, file operations                │
│  - Parallel work on independent subtasks            │
│  - Background execution (--bg)                      │
└─────────────────────────────────────────────────────┘
```

---

## Level 1: Coordinator (Claude Code)

**Role:** Strategic orchestrator and decision maker.

### Responsibilities

1. **User Intent Capture**
   - Clarify ambiguous requests
   - Translate user language into structured work items
   - Set strategic direction and priorities

2. **Work Stream Management**
   - Create new work items in `docs/reference/WORK_STREAM.md`
   - Triage and prioritize based on dependencies
   - Monitor overall progress (PENDING → CLAIMED → COMPLETED)

3. **Team Coordination**
   - Create teams with `TeamCreate` when multi-actor work needed
   - Assign L2 teammates with clear, isolated components
   - Maintain team roster in `~/.claude/teams/{team-name}/config.json`

4. **Dependency Resolution**
   - Identify blockedBy/Blocks relationships
   - Detect and resolve circular dependencies
   - Create work items to unblock stalled tasks

5. **Decision Gates**
   - Architecture decisions (technology choices, patterns)
   - Resource allocation (how many agents, which models)
   - Conflict resolution (when agents disagree or have conflicting goals)
   - Trade-off decisions (speed vs. quality, breadth vs. depth)

6. **Progress Reporting**
   - Summarize completed phases
   - Report blockers and risks
   - Update trackers and status documents

### Tools Used

- `TeamCreate` - Create new teams with designated agents
- `TaskCreate`, `TaskUpdate`, `TaskList` - Work stream management
- `SendMessage` - Direct communication with L2 teammates
- `Read`, `Write` - Work stream and documentation updates
- `Bash` - Work stream queries and reports

### Decision Authority

L1 has **final authority** on:

- Strategic direction and priorities
- Team composition and role assignments
- Architecture and major design choices
- Conflict resolution between teams or agents
- Resource constraints and SLOs

L1 **delegates execution** to L2 but retains veto power over direction changes.

---

## Level 2: Teammates (Named Agents)

**Role:** Component owners responsible for specific functional areas or features.

### Responsibilities

1. **Component Ownership**
   - Own specific modules, services, or features (e.g., "auth", "api", "frontend")
   - Understand all code and dependencies within component
   - Responsible for component health and test coverage

2. **Task Claiming & Execution**
   - Monitor `WORK_STREAM.md` for available work
   - Claim items by adding to CLAIMED section with agent_id and timestamp
   - Move claimed items to IN_PROGRESS during active work
   - Complete items by moving to COMPLETED with duration

3. **Sub-Task Decomposition**
   - Break large tasks into smaller L3 subtasks if needed
   - Assign to thegent agents (free tier by default)
   - Monitor and support L3 agents

4. **Quality Gates**
   - All code passes linting, typing, and tests
   - PR review and approval before committing
   - Update documentation and trackers for completed work

5. **Status Communication**
   - Send status updates to L1 using `SendMessage`
   - Report blockers immediately
   - Highlight dependencies or risks early

6. **Escalation**
   - Escalate blocking issues to L1 quickly
   - Request help for out-of-scope work
   - Propose scope changes or trade-offs

### Team Structure

**Agent Identity**: Each teammate has a unique **name** (e.g., "research-agent", "implementation-specialist", "test-runner").

**Component Mapping**:

```
Team Lead (Claude Code)
├── Researcher ("research-agent")
│   └── Component: Discovery, pattern analysis
├── Implementer ("dev-agent")
│   └── Component: Core implementation
├── Tester ("test-agent")
│   └── Component: Test coverage, validation
└── Integration ("integration-agent")
    └── Component: System integration, E2E
```

### Tools Used

- `TaskList` - Find available work items
- `TaskUpdate` - Claim, progress, complete work
- `SendMessage` - Report status and blockers to L1
- `Bash`, `Glob`, `Read`, `Edit`, `Write` - Direct file operations
- `Skill` - Domain-specific operations (code review, testing, etc.)

### Decision Authority

L2 has **authority** within assigned components:

- Implementation approach and design details
- Code review and merge decisions
- Sub-task delegation to L3
- Technical trade-offs within component scope

L2 **must escalate** to L1 for:

- Cross-component impacts
- Architecture changes
- Resource constraints or SLOs
- Scope changes or reprioritization

---

## Level 3: Thegent Agents (Free/Premium)

**Role:** Execution specialists for independent subtasks.

### Responsibilities

1. **Subtask Execution**
   - Implement specific, well-defined tasks
   - No independent decision-making; follow L2 instructions
   - Report results back to L2

2. **Parallel Work**
   - Execute independent subtasks in parallel
   - Respect file locking and coordination mechanisms
   - No direct L2-to-L2 communication

3. **Pattern Searches & Exploration**
   - Find code patterns, usage examples
   - Analyze logs, errors, test results
   - Surface insights to L2

4. **Background Execution**
   - Long-running tasks (tests, builds, searches)
   - Use `--bg` flag for non-blocking execution
   - Return results via stdout/file writes

### Tools Used

- Basic: `Bash`, `Glob`, `Read`, `Edit`, `Write`, `Grep`
- Advanced: Code analysis, testing, MCP tools (model-specific)

### Decision Authority

L3 agents have **no independent authority**:

- Must follow L2 instructions without deviation
- Cannot make design decisions or architectural changes
- Cannot claim new work; must be explicitly assigned by L2
- Cannot communicate directly with L1

L3 agents **report results** via file writes or stdout; L2 interprets and acts on results.

---

## CLAIMED Workflow

**Purpose:** Register that work is about to begin, preventing duplicate effort.

### Step-by-Step

#### 1. Agent Reads Current Status

```bash
# L2 reads the WORK_STREAM.md
cat docs/reference/WORK_STREAM.md
# or
thegent plan do-next  # Get list of pending work
```

#### 2. Find Unclaimed Item

Look for items in **PENDING** section with:

- **Status** = `PENDING`
- **Depends On** = All satisfied (empty or already COMPLETED)
- No agent_id in CLAIMED section

Example:

```markdown
| TGNT-P6.1 | Per-agent GIT_INDEX_FILE management | feature | TGNT-P4.1 | ~8min | PENDING |
```

#### 3. Agent Claims Item

L2 adds row to **CLAIMED** section with:

- **Item ID**: `TGNT-P6.1`
- **Agent ID**: Your unique agent identifier (e.g., `research-agent`, `dev-agent-1`)
- **Started**: ISO timestamp (e.g., `2026-02-18T14:30:00Z`)
- **Status**: `IN_PROGRESS`

```markdown
## CLAIMED

| ID        | Agent       | Started              | Status      |
| --------- | ----------- | -------------------- | ----------- |
| TGNT-P6.1 | dev-agent-1 | 2026-02-18T14:30:00Z | IN_PROGRESS |
```

#### 4. Update Original Row Status

Change original PENDING item status to `CLAIMED`:

```markdown
| TGNT-P6.1 | Per-agent GIT_INDEX_FILE management | feature | TGNT-P4.1 | ~8min | CLAIMED |
```

#### 5. Commit & Push

Immediately commit and push to ensure visibility:

```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush
git add docs/reference/WORK_STREAM.md
git commit -m "Claim TGNT-P6.1: Per-agent GIT_INDEX_FILE management"
git push origin main
```

**Why:** Other agents see claimed items and skip them. No duplicate work.

---

## COMPLETED Workflow

**Purpose:** Register that work is done and dependencies are satisfied for downstream tasks.

### Step-by-Step

#### 1. Finish Implementation

Code, tests, and documentation complete. Ready to move to COMPLETED.

#### 2. Move to COMPLETED Section

Remove from **CLAIMED** section. Add to **COMPLETED** section with:

- **Item ID**: `TGNT-P6.1`
- **Agent ID**: Your agent identifier
- **Started**: Original start time (ISO)
- **Completed**: ISO timestamp when finished
- **Duration**: Human-readable (e.g., `15 min`)
- **Notes**: Optional summary or key files changed

```markdown
## COMPLETED

| ID        | Agent       | Started              | Completed            | Duration | Notes                                                   |
| --------- | ----------- | -------------------- | -------------------- | -------- | ------------------------------------------------------- |
| TGNT-P6.1 | dev-agent-1 | 2026-02-18T14:30:00Z | 2026-02-18T14:45:00Z | 15 min   | Implemented per-agent INDEX handling with atomic writes |
```

#### 3. Update Original Row Status

Change original row status from `CLAIMED` to `COMPLETED`:

```markdown
| TGNT-P6.1 | Per-agent GIT_INDEX_FILE management | feature | TGNT-P4.1 | ~8min | COMPLETED |
```

#### 4. Unblock Downstream Tasks

Move any dependent items from PENDING to active (L1 may reprioritize):

```markdown
# Items now unblocked:

| TGNT-P6.2 | Git plumbing commit pipeline | feature | TGNT-P6.1 | ~10min | PENDING |
| TGNT-P6.3 | CAS ref update with backoff | feature | TGNT-P6.2 | ~5min | PENDING |
```

#### 5. Update Trackers

Update related documents:

- `docs/reference/PLAN_STATUS.md` - Phase completion status
- `docs/reference/CODE_ENTITY_MAP.md` - Map new functions/modules to FRs and work items
- `docs/research/CONVERSATION_DUMP_YYYY-MM-DD.md` - Key decisions and findings (if significant)

#### 6. Commit & Push

```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush
git add docs/reference/WORK_STREAM.md docs/reference/PLAN_STATUS.md
git commit -m "Complete TGNT-P6.1: Per-agent GIT_INDEX_FILE management

- Implemented atomic GIT_INDEX_FILE init/copy/cleanup
- All tests passing (15/15)
- Documentation updated at docs/implementation/GIT_PARALLELISM.md"
git push origin main
```

**Why:** L1 sees completion, identifies newly-unblocked work, and dispatches next batch.

---

## Recovery Procedures

**Purpose:** Handle failure scenarios without deadlock or silent failures.

### Scenario 1: Agent Crash During Execution

**Symptom:** Item in CLAIMED, no progress for 10+ minutes, agent not responding.

**Recovery:**

1. L1 notices staleness via `thegent ps` or timeout
2. L1 moves item back to PENDING (remove from CLAIMED)
3. L1 sends message to agent: "Task timed out, released. If you continue, results will be orphaned."
4. Another agent can now claim the item
5. Update WORK_STREAM.md:

```markdown
## CLAIMED

| ID        | Agent       | Started              | Status                    |
| --------- | ----------- | -------------------- | ------------------------- |
| TGNT-P6.1 | dev-agent-1 | 2026-02-18T14:30:00Z | TIMEOUT (released 15:00Z) |
```

### Scenario 2: Circular Dependency Detected

**Symptom:** Task A depends on B, B depends on A. Both PENDING.

**Recovery:**

1. L1 runs DAG validator: `thegent plan do-next` or manual inspection
2. L1 identifies cycle and splits one task:
   - Reduce scope of one task (e.g., "Phase 2a: Part A", "Phase 2b: Part B")
   - Make Part A independent; complete Part A first
   - Make Part B depend on Part A
3. Update WORK_STREAM.md with new structure
4. Notify affected agents of scope change

### Scenario 3: Conflicting File Edits (Multiple Agents)

**Symptom:** Two agents claim non-overlapping tasks, but both edit the same file.

**Recovery:**

1. L1 detects conflict via git merge attempt or explicit reporting
2. L1 escalates to affected L2 agents for manual resolution:
   - Determine correct final state
   - One agent rebases/redoes work on top of other
   - Failing agent re-claims task with updated instructions
3. Update CLAIMED to reflect new start time:

```markdown
| TGNT-P6.2 | dev-agent-2 | 2026-02-18T14:00:00Z | CONFLICT (recovered 15:30Z) |
| TGNT-P6.2 | dev-agent-2 | 2026-02-18T15:30:00Z | IN_PROGRESS (restart) |
```

### Scenario 4: Dependency Not Yet Satisfied

**Symptom:** Agent claims task, but a dependency is still PENDING.

**Recovery:**

1. Agent reports blocker to L2 immediately
2. L2 escalates to L1
3. L1 options:
   - **Prioritize dependency:** Move dependency to front of queue, assign agents
   - **Parallel-ize:** If independent, assign separate agents to both
   - **Reduce scope:** Remove blocker from task scope, do partial work
4. Update task status to BLOCKED:

```markdown
| TGNT-P6.2 | Git plumbing commit pipeline | feature | TGNT-P6.1 | ~10min | BLOCKED (waiting: TGNT-P6.1) |
```

### Scenario 5: Agent Completes, Then Discovers Bug

**Symptom:** Item moved to COMPLETED, but downstream task finds regression.

**Recovery:**

1. Downstream agent reports issue to L1
2. L1 moves original item back to IN_PROGRESS:

```markdown
## CLAIMED

| ID        | Agent       | Started              | Status                                   |
| --------- | ----------- | -------------------- | ---------------------------------------- |
| TGNT-P6.1 | dev-agent-1 | 2026-02-18T14:30:00Z | REOPENED (regression found by TGNT-P6.2) |
```

3. Original agent fixes issue
4. Re-move to COMPLETED with updated notes:

```markdown
| TGNT-P6.1 | dev-agent-1 | 2026-02-18T14:30:00Z | 2026-02-18T15:45:00Z | 75 min | Fixed atomic write race condition detected by TGNT-P6.2 |
```

### Scenario 6: SLO Breach (Task Takes 10x Estimated Time)

**Symptom:** Task estimated `~8min`, now at `60+ min`.

**Recovery:**

1. L1 detects via elapsed time vs. estimate
2. L1 sends message to agent: "Task running long. Are you blocked? Do you need help?"
3. Agent responds:
   - **If stuck:** L1 splits remaining work, brings in additional agents
   - **If on track:** Update estimate and continue
4. Update CLAIMED with note:

```markdown
| TGNT-P6.1 | dev-agent-1 | 2026-02-18T14:30:00Z | IN_PROGRESS (running long: ~50min, estimate was ~8min) |
```

5. Post-completion, analyze and document:
   - Update estimate for future similar tasks
   - Document what took longer (e.g., "edge case complexity higher than expected")
   - Update planning assumptions

---

## TUI Dashboard Design

**Purpose:** Real-time visibility into work stream, claimed work, and progress.

### Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│ WORK STREAM MONITOR - 2026-02-18 15:30:00 UTC              │
├─────────────────────────────────────────────────────────────┤
│ Phase: 6 (Git Parallelism) | PENDING: 12 | CLAIMED: 3 | COMPLETED: 5 │
├─────────────────────────────────────────────────────────────┤
│ ACTIVE AGENTS (CLAIMED)                                     │
├─────────────────────────────────────────────────────────────┤
│ Agent         │ Task ID    │ Task Title              │ Elapsed│
├───────────────┼────────────┼─────────────────────────┼────────┤
│ dev-agent-1   │ TGNT-P6.1  │ Per-agent GIT_INDEX...  │ 15:23  │
│ test-agent    │ TGNT-P6.3  │ CAS ref update with...  │ 03:45  │
│ integration   │ TGNT-P6.5  │ harness git status      │ 02:12  │
├─────────────────────────────────────────────────────────────┤
│ RECENTLY COMPLETED                                          │
├─────────────────────────────────────────────────────────────┤
│ Task ID    │ Agent         │ Completed At        │ Duration│
├────────────┼───────────────┼─────────────────────┼──────────┤
│ TGNT-P6.4  │ dev-agent-2   │ 15:18 UTC           │ 22 min  │
│ TGNT-P6.2  │ implementation│ 15:05 UTC           │ 18 min  │
│ TGNT-P6.0  │ research-agent│ 14:55 UTC           │ 10 min  │
├─────────────────────────────────────────────────────────────┤
│ BLOCKERS (4 WAITING)                                        │
├─────────────────────────────────────────────────────────────┤
│ Task ID    │ Blocked By              │ Time Waiting│ Severity
├────────────┼────────────────────────┼─────────────┼──────────┤
│ TGNT-P6.7  │ TGNT-P6.5 (2 min left) │ 5 min       │ LOW      │
│ TGNT-P7.1  │ TGNT-P6 Phase (50%)    │ 25 min      │ MEDIUM   │
│ TGNT-P7.2  │ TGNT-P6 Phase (50%)    │ 25 min      │ MEDIUM   │
├─────────────────────────────────────────────────────────────┤
│ NEXT AVAILABLE (5 PENDING, sorted by priority)             │
├─────────────────────────────────────────────────────────────┤
│ ID         │ Title                       │ Est.  │ Ready?│ PR  │
├────────────┼─────────────────────────────┼───────┼───────┼─────┤
│ TGNT-P6.6  │ Performance benchmarks      │ ~10m  │ YES   │ ✓   │
│ TGNT-P6.8  │ Documentation updates       │ ~5m   │ YES   │ ✓   │
│ TGNT-P6.9  │ Integration test suite      │ ~15m  │ NO    │ ✗ (blocking: TGNT-P6.7) │
│ TGNT-P7.1  │ Phase 7 kickoff planning    │ ~8m   │ NO    │ ✗ (blocking: Phase 6 at 50%) │
│ TGNT-P7.2  │ Phase 7 task design         │ ~12m  │ NO    │ ✗ (blocking: Phase 6 at 50%) │
├─────────────────────────────────────────────────────────────┤
│ HEALTH METRICS                                              │
├─────────────────────────────────────────────────────────────┤
│ Avg Task Duration (vs. Estimate): 105% (on track)           │
│ Cycle Time (CLAIMED → COMPLETED): 18 min (target: 15 min)  │
│ Agent Utilization: 3/5 active (60%) | 2 idle               │
│ Blocker Count: 4 (1 critical, 2 medium, 1 low)             │
│ Estimated Phase Completion: 16:45 UTC (45 min)             │
│                                                              │
│ Commands: [A]gents [W]orkstream [B]lockers [R]efresh [Q]uit│
└─────────────────────────────────────────────────────────────┘
```

### Key Metrics

| Metric                   | Display                       | Action Threshold                    |
| ------------------------ | ----------------------------- | ----------------------------------- |
| **Elapsed vs. Estimate** | % over (e.g., 115%)           | >150% → Flag as SLO breach          |
| **Cycle Time**           | Minutes (CLAIMED → COMPLETED) | >30 min → Investigate               |
| **Agent Utilization**    | Active/Total (e.g., 3/5)      | <50% → Release agents, reduce scope |
| **Blocker Count**        | Total & severity breakdown    | >5 blockers → Escalate to L1        |
| **Phase Completion %**   | Current phase progress        | >80% done → Prepare next phase      |

### Updating Dashboard

Dashboard is read-only view of `WORK_STREAM.md`:

```bash
# Watch work stream changes in real-time
watch -n 5 'tail -50 docs/reference/WORK_STREAM.md'

# Or use dedicated dashboard tool (future)
thegent dashboard --watch
```

---

## Tools & Commands Quick Reference

### Work Stream Management

| Command                           | Purpose                               | Used By                   |
| --------------------------------- | ------------------------------------- | ------------------------- |
| `thegent plan do-next`            | List next 5 actionable items          | L1, L2                    |
| `thegent plan do-next --limit 10` | List next 10 items                    | L1 for batch assignment   |
| `TaskCreate` (tool)               | Create new work item programmatically | L1 when spawning teams    |
| `TaskList` (tool)                 | List all work items and status        | L2 to find available work |
| `TaskUpdate` (tool)               | Claim, progress, or complete item     | L2 during execution       |
| `TaskGet` (tool)                  | Read full details of single task      | L2 before starting work   |

### Team & Agent Management

| Command                       | Purpose                     | Used By                                 |
| ----------------------------- | --------------------------- | --------------------------------------- |
| `TeamCreate`                  | Create new team with roster | L1 for multi-agent projects             |
| `SendMessage`                 | Send message to teammate    | L1 for instructions/status requests     |
| `SendMessage` (broadcast)     | Send to all teammates       | L1 for critical updates (use sparingly) |
| `thegent ps`                  | List running agent sessions | L1 to monitor activity                  |
| `thegent wait <session_id>`   | Block until agent finishes  | L1 to wait for completion               |
| `thegent status <session_id>` | Check agent progress        | L1 to get status update                 |

### File Operations

| Command      | Purpose                      | Used By              |
| ------------ | ---------------------------- | -------------------- |
| `Read`       | Read work stream or document | L1, L2               |
| `Edit`       | Update work stream inline    | L1, L2               |
| `Write`      | Replace work stream entirely | L1 only (careful!)   |
| `Bash` (git) | Commit and push changes      | L1, L2 for atomicity |

### Analysis & Reporting

| Command         | Purpose                          | Used By              |
| --------------- | -------------------------------- | -------------------- |
| `Grep`          | Search for blocked/overdue items | L1 for health checks |
| `Bash` (script) | Generate reports, metrics        | L1 for dashboards    |

---

## Summary: Key Principles

1. **Single Source of Truth:** `docs/reference/WORK_STREAM.md` is canonical. All status updates happen here.

2. **No Duplicate Work:** CLAIMED section ensures only one agent works on a task.

3. **Clear Dependencies:** Depends On column prevents circular dependencies and surprises.

4. **Visibility:** Dashboard and status commands let L1 monitor progress without micromanaging.

5. **Fast Recovery:** Recovery procedures handle common failure modes without manual intervention.

6. **Escalation Hierarchy:** L3 reports to L2, L2 reports to L1. Blockers surface quickly.

7. **Atomic Updates:** All work stream changes committed immediately to prevent conflicts.

8. **Respect Autonomy:** L1 sets direction; L2 executes independently within that direction.

---

**Version:** 1.0
**Maintained By:** Coordination Leadership (L1)
**Next Review:** 2026-02-25
