# Master Systems Plan: Threading, Roles, Runbooks, Git Automation

**Date**: 2026-02-24
**Status**: Research & Planning Phase
**Sources**: helios-qs.md, Teammate PRD, helios-consolidated.md, user clarification

---

## Executive Summary

This document synthesizes research into a unified plan for building:

1. **Automatic Threading System** - Context isolation via subagent clones
2. **Roles System** - Hierarchical agent roles with pooled pre-warming
3. **Runbook Engine** - Semantic workflows with learned patterns
4. **Git Automation** - Shadow git + public git with multi-tenant support
5. **Micro-Backup System** - Granular, lossless, reconcilable backups
6. **Multi-Agent Reconciliation** - Global state with socket attachment
7. **Versioning Model** - Fast, cheap helper model for commit/annotation
8. **Context Management** - Episodic memory layers (20-50 levels)

---

## 1. Automatic Threading System

### 1.1 Problem Statement

User asks off-topic question during active development session:

> "During dev work, user notices Python version is wrong and asks about it"

Current behavior: Agent adapts goals, pollutes context, loses focus

Target behavior: **Spawn a thread (subagent clone) to handle it**

### 1.2 Thread Definition

A **thread** is:

- A **unit of work** with **partial context share**
- A **parallel execution path** (does not block parent unless necessary)
- Gets: **chat summary + last full turn (unsummarized) + thread instructions + user prompt**
- Returns: **1-2 line update** (e.g., "updated py version")

### 1.3 Thread Trigger Conditions

| Trigger                                        | Action       |
| ---------------------------------------------- | ------------ |
| Prompt unrelated to current goals              | Spawn thread |
| Prompt would require significant context shift | Spawn thread |
| User explicitly requests `@thread` prefix      | Spawn thread |
| Prompt matches "quick question" pattern        | Spawn thread |

### 1.4 Thread Lifecycle

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Parent    │────▶│    Thread    │────▶│   Return    │
│   Chat      │     │   (Spawn)    │     │   Summary   │
└─────────────┘     └──────────────┘     └─────────────┘
      │                    │                    │
      │   chat_summary     │   1-2 line result  │
      │   + last_turn      │                    │
      │   + instructions   │                    │
      ▼                    ▼                    ▼
   Continues          Parallel exec         Parent notified
   unblocked          (auto bg'd)           on completion
```

### 1.5 Thread Context Isolation

**NOT included in thread context:**

- Full conversation history
- All previous tool calls
- Intermediate reasoning

**INCLUDED in thread context:**

- Chat summary (compressed)
- Last full turn (unsummarized)
- Thread state instructions
- User prompt

### 1.6 Thread-State Smart Contract

At the start of each turn, agent writes a **smart contract**:

```yaml
turn_contract:
  goal: "Implement user authentication"
  constraints:
    - "Must not modify database schema"
    - "Must maintain backward compatibility"
  success_criteria:
    - "Tests pass"
    - "No security vulnerabilities"
  must_satisfy: "end_of_turn | as_it_goes"
```

Contract must be satisfied before thread can complete.

### 1.7 Thread End States

| End State    | Behavior                                        |
| ------------ | ----------------------------------------------- |
| Success      | Return 1-2 line summary, merge results          |
| Partial      | Return summary + pending items                  |
| Failed       | Return error summary, flag for parent attention |
| Needs Parent | Escalate back to parent chat                    |

### 1.8 Thread Resumption

- Threads get unique IDs
- Parent can introspect thread context
- Parent can resume thread if relevant to main task
- **Agent system prompt nudges NOT to resume unless relevant**

### 1.9 CC Feature Replication: Background Commands

```
run cmd -> can bg or block at run, during run, wait for complete in chat
        -> or idle (send stop signal)
        -> auto be sent new prompt notification on complete
```

Implementation:

```python
class CommandExecution:
    mode: Literal["blocking", "background", "idle"]
    on_complete: Callable[[Result], None]  # Notification callback
```

---

## 2. Roles System

### 2.1 Core Roles

| Role             | Purpose                 | Trigger Pattern       |
| ---------------- | ----------------------- | --------------------- |
| Planner          | Decompose complex tasks | Multi-step request    |
| Researcher       | Fetch docs, search      | Needs external info   |
| Coder            | Write/modify code       | Implementation needed |
| Reviewer         | Review changes          | After code changes    |
| Tester           | Run tests, validate     | After implementation  |
| Commiter         | Generate commits        | Changes ready         |
| Perf Profiler    | Profile performance     | Optimization needed   |
| Security Scanner | Find vulnerabilities    | Security review       |
| Doc Writer       | Maintain documentation  | Code changes          |
| Orchestrator     | Coordinate agents       | Multi-agent workflow  |

### 2.2 Role Assignment Modes

| Mode             | Description                           |
| ---------------- | ------------------------------------- |
| **Explicit**     | User says `use XYZ role`              |
| **Implicit**     | System detects task type              |
| **Tool-Based**   | Agent calls `assumeRole()` tool       |
| **Hybrid**       | Mix of explicit + implicit            |
| **Hierarchical** | Orchestrator delegates to specialists |

### 2.3 Role Hierarchy

```
                    Orchestrator
                         │
         ┌───────────────┼───────────────┐
         │               │               │
     Planner         Researcher       Coder
         │               │               │
    ┌────┴────┐     ┌────┴────┐     ┌────┴────┐
    │         │     │         │     │         │
Reviewer  Tester  Local    Web    Reviewer Tester
    │                 │         │
    └─────────────────┴─────────┘
                │
            Commiter
```

### 2.4 Role Spawning Rules

- **Depth Limit**: 2 (L^1 children, L^2 grandchildren)
- Subagents are **role-only** (must have generalist for basic tasks)
- Researcher spawns: 2 local + 2 web (concurrent if has local context, otherwise waits)

### 2.5 Role Lifecycle

| Phase           | Strategy                       |
| --------------- | ------------------------------ |
| **Pooled**      | Pre-warmed instances ready     |
| **Ephemeral**   | Spawn on demand, die when done |
| **Speculative** | Pre-warm based on prediction   |
| **Hybrid**      | All of the above + more        |

### 2.6 Role Configuration

Roles should be **subconfigurable**:

```yaml
roles:
  coder:
    model: "claude-3-5-sonnet"
    tools: ["edit", "write", "bash"]
    max_depth: 2
    pool_size: 3
    prewarm: true
  researcher:
    model: "claude-3-5-haiku" # Cheaper for search
    tools: ["web_search", "read"]
    pool_size: 5
    timeout: 60s
```

---

## 3. Runbook Engine

### 3.1 Runbook Definition

A **runbook** is:

- A **predefined semantic workflow** for an agent/human to execute
- Based on **scientific management principles**
- Evolved from **learned patterns**
- Has **declarative goal state** + structural governance

### 3.2 Runbook Types

| Type              | Description                      | Example             |
| ----------------- | -------------------------------- | ------------------- |
| **Deterministic** | Fixed steps, no branching        | `run(project=)`     |
| **Semantic**      | Goal-driven, agent decides steps | "Implement auth"    |
| **Learned**       | Pattern extracted from history   | "Fix failing tests" |
| **Hybrid**        | Mix of above                     | PR review workflow  |

### 3.3 Trigger Mechanisms

| Trigger       | Example                      |
| ------------- | ---------------------------- |
| Manual        | `/runbook deploy`            |
| Event-based   | File changed → lint runbook  |
| Schedule      | Nightly cleanup              |
| Agent-decided | Detects need, invokes        |
| Threshold     | Coverage drops → fix runbook |
| ML-predicted  | Predict next task            |

### 3.4 Example Runbooks

```yaml
runbooks:
  feature-planning:
    triggers: [manual, agent-decided]
    steps:
      - gather_requirements
      - research_similar_features
      - create_spec
      - break_down_tasks
    goal_state: "Tasks registered and prioritized"

  fix-failing-tests:
    triggers: [threshold: test_pass_rate < 0.9]
    steps:
      - identify_failures
      - analyze_root_cause
      - implement_fix
      - verify_fix
    goal_state: "All tests passing"

  pr-review:
    triggers: [event: pr_opened]
    steps:
      - code_review
      - security_scan
      - perf_check
      - doc_update_check
    goal_state: "PR approved or feedback given"
```

### 3.5 Project Registration

Agents need a way to register and manage projects centrally:

```yaml
projects:
  thegent:
    path: "/Users/kooshapari/CodeProjects/Phenotype/repos/thegent"
    commands:
      run: "just run"
      test: "just test"
      lint: "just lint"
    runbooks: [default, python-project]
```

Generic commands auto-match/find or are empty until populated.

### 3.6 Reference Implementations

Look at for complex flows:

- **AgilePlus** - Specification-driven development
- **GSD** - Getting Stuff Done framework
- **BMAD** - Behavior-Driven AI Development
- **SDD** - Specification-Driven Development

---

## 4. Git Automation

### 4.1 Dual Git System

| System         | Scope         | Visibility | Granularity     |
| -------------- | ------------- | ---------- | --------------- |
| **Shadow Git** | Every change  | Internal   | Per-edit        |
| **Public Git** | Logical units | External   | Per-turn/commit |

### 4.2 Shadow Git

**Purpose**: Full audit trail, granular restore

```
.shadow-git/
├── objects/
│   ├── edit-001-abcd1234
│   ├── edit-002-efgh5678
│   └── ...
├── journal.jsonl
└── index.db
```

**Storage Options**:

- Temporal-backed (?) + ???
- MinIO / SQLite
- Git notes
- Custom object store

**Recommendation**: Research best approach in existing docs

### 4.3 Public Git

**Rules**:

- Each **turn** ends in a commit
- Next turn(s) may loop on fixing hook/commit check errors
- Agent can elect to **wait** if work is explicitly incomplete
- **Batch where possible** but handle dependencies

### 4.4 Commit Timing

| Scenario              | Action                    |
| --------------------- | ------------------------- |
| 1 file edited         | Commit at turn end        |
| 10 files edited       | Batch commit at turn end  |
| Agent waiting on work | Skip commit, mark pending |
| Hook errors           | Next turn = fix loop      |

### 4.5 Multi-Tenant Git

When multiple agents work in one worktree:

| Strategy             | Description                           |
| -------------------- | ------------------------------------- |
| **Lock-based**       | Agent locks file before edit          |
| **Optimistic**       | Edit freely, merge/conflict on commit |
| **Branch-per-agent** | Each agent gets branch, merge later   |
| **Queue-based**      | Edits serialized through queue        |

**Research needed**: Check thegent's existing multi-tenant git handling

### 4.6 Branch Strategy

```
main
├── feat/auth-system
│   ├── thread-001-password-validation
│   └── thread-002-session-mgmt
├── feat/api-refactor
│   └── thread-003-endpoint-cleanup
└── ...
```

- Main + feature branches
- Per-thread branches (optional)
- Layered PR strategy (heavily important)

---

## 5. Micro-Backup System

### 5.1 Granularity Levels

| Level              | What's Backed Up       | Example                 |
| ------------------ | ---------------------- | ----------------------- |
| **File**           | Complete file          | `src/foo.py`            |
| **Hunk**           | Lines in file          | Lines 10-20 of `foo.py` |
| **Edit Operation** | Semantic change        | "Renamed x to y"        |
| **Agent Action**   | All changes in session | Coder agent's work      |
| **Thread**         | All changes in thread  | Thread-001              |
| **Command**        | CLI command + effects  | `npm install`           |

### 5.2 Restore Behavior

**User rewinds chat** → Given option to restore:

1. Code only
2. Conversation only
3. Both

**Code restore** → Then repeat for code/commands

### 5.3 Storage Requirements

- **Least disk space**
- **Maximal actual granularity**
- **Real lossless backup**
- **Reverse cloud where possible** (user prompts this one)

### 5.4 Conflict Handling

If another agent modified same file:

- This is why **all sessions MUST be centralized**
- thegent integration tracks all agent sessions + terminal invocations

### 5.5 Reconciliation Strategies

From research:

| Strategy                 | Description                    |
| ------------------------ | ------------------------------ |
| **N-way merge**          | Merge multiple agents' changes |
| **Waiting**              | Queue edits, apply serially    |
| **Coalesce**             | Combine similar edits          |
| **Flag conflict**        | Agent resolves, never human    |
| **Optimistic + prevent** | LLM resolves + file locking    |

---

## 6. Multi-Agent Reconciliation

### 6.1 Global State Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Central Process                         │
│                 (Socket Attachment)                      │
├─────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │
│  │ Agent A │  │ Agent B │  │ Agent C │  │ Agent D │   │
│  │ Coder   │  │Reviewer │  │ Tester  │  │Research │   │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘   │
│       │            │            │            │         │
│       └────────────┴────────────┴────────────┘         │
│                         │                               │
│                    Global State                         │
│                  (Shared, Filtered)                     │
└─────────────────────────────────────────────────────────┘
```

### 6.2 Key Principle

**One process with socket attachment**:

- helios: First-party vertical optimal
- thegent: Extended and agnostic

### 6.3 Session Tracking

All agent sessions tracked centrally:

- Agent ID + session ID + thread ID
- File locks + edit queue
- Git state + shadow git journal
- Terminal invocations

### 6.4 Conflict Resolution

| Type                       | Resolution                        |
| -------------------------- | --------------------------------- |
| Same file, different hunks | Auto-merge                        |
| Same file, same hunks      | LLM resolves                      |
| Semantic conflict          | Agent flags, system escalates     |
| Temporal conflict          | Last-write-wins with notification |

**Rule**: Flag conflicts for agent threads, **NEVER humans**

---

## 7. Versioning Model (Cheap Helper)

### 7.1 Model Purpose

The cheap model handles:

- Commit message generation
- Session annotation
- Memory management
- Search summarization
- Change classification

### 7.2 Model Characteristics

| Attribute | Requirement                  |
| --------- | ---------------------------- |
| Speed     | Fast                         |
| Cost      | Cheap                        |
| Quality   | Good enough for simple tasks |

### 7.3 Current Mapping

Currently maps to `minimaxm2.5` but should be renamed:

- `THEGENT_HELPER_MODEL`
- `THEGENT_VERSIONING_MODEL`
- `THEGENT_CHEAP_MODEL`

### 7.4 Future: Local Models

Explore sub-2B models for zero cost:

- Trade-off: Memory usage vs. concurrency/frequency
- Break-even point needs analysis

---

## 8. Context Management

### 8.1 Problems to Solve

| Problem                   | Description                       |
| ------------------------- | --------------------------------- |
| **Too large**             | Context exceeds limits            |
| **Truncation loses info** | Important info cut off            |
| **Stale**                 | Model doesn't know recent changes |
| **Scattered**             | Hard to find relevant info        |
| **Thrashes/bloats**       | Quick degradation                 |

### 8.2 Solutions

| Solution            | Description           |
| ------------------- | --------------------- |
| **Summarization**   | Compress old messages |
| **Semantic search** | Find relevant chunks  |
| **Checkpointing**   | Save/restore state    |
| **Hierarchical**    | Main + sub-contexts   |
| **Episodic memory** | 20-50 layers          |

### 8.3 Context Scope

| Scope          | Description                 |
| -------------- | --------------------------- |
| **Global**     | Shared across all, filtered |
| **Per-chat**   | Chat-specific context       |
| **Per-thread** | Thread-isolated context     |
| **Per-agent**  | Agent-specific memory       |
| **Episodic**   | 20-50 layer session memory  |

---

## 9. Performance Targets

### 9.1 Current Pain Points

| Issue             | Impact                          |
| ----------------- | ------------------------------- |
| Agent spawn time  | Slow                            |
| LLM response time | Variable                        |
| Git operations    | Can be slow                     |
| Context loading   | Slow                            |
| Concurrent agents | System overload, latency spikes |

### 9.2 Targets

| Metric          | Target                                         |
| --------------- | ---------------------------------------------- |
| First token     | < 3s                                           |
| Shell startup   | < 50ms ✅                                      |
| Agent spawn     | TBD                                            |
| Task completion | Benchmark against SWE-bench/Term-bench subsets |

### 9.3 Strategy

- Multi-tiered threads/models
- Granular model picker
- Show `(Fast)` next to relevant models
- User chooses quality/speed/cost

---

## 10. Integration Architecture

### 10.1 helios vs thegent

| Aspect | helios                      | thegent            |
| ------ | --------------------------- | ------------------ |
| Focus  | First-party vertical        | Extended, agnostic |
| Agents | Direct socket attachment    | Tooling/adapters   |
| Scope  | Optimized for helios agents | Universal          |

### 10.2 External Tool Integration

| Tool               | Integration                              |
| ------------------ | ---------------------------------------- |
| Claude Code        | Inspiration, interoperability for resume |
| Gemini CLI         | Inspiration, interoperability for resume |
| Cursor Agent       | Interoperability for resume              |
| Droid              | Interoperability for resume              |
| Gemini Code Assist | Automated PR review                      |

### 10.3 Session Resume

Make helios interoperable with other CLIs:

- Resume cursor-agent sessions
- Resume droid sessions
- Resume claude sessions

```
helios attach [session-id]
```

---

## 11. Implementation Phases

### Phase 1: Threading Foundation (Week 1-2)

- [ ] Thread spawn/return protocol
- [ ] Context isolation (summary + last turn)
- [ ] Thread-state smart contract
- [ ] Background command execution
- [ ] Thread resumption API

### Phase 2: Roles System (Week 2-3)

- [ ] Role registry and discovery
- [ ] Role assignment modes
- [ ] Hierarchical delegation
- [ ] Pool pre-warming
- [ ] Role configuration

### Phase 3: Runbooks (Week 3-4)

- [ ] Runbook definition format
- [ ] Trigger mechanisms
- [ ] Project registration
- [ ] Learned pattern extraction
- [ ] Runbook CLI

### Phase 4: Git Automation (Week 4-5)

- [ ] Shadow git implementation
- [ ] Public git batching
- [ ] Multi-tenant conflict resolution
- [ ] Branch-per-thread
- [ ] Layered PR support

### Phase 5: Micro-Backups (Week 5-6)

- [ ] Granular backup storage
- [ ] Restore by level
- [ ] Reconciliation with multi-agent
- [ ] Lossless verification

### Phase 6: Integration (Week 6-8)

- [ ] Global state centralization
- [ ] Socket attachment
- [ ] External CLI resume
- [ ] Performance optimization

---

## 12. Open Questions

1. **Shadow git storage**: Temporal + ??? or MinIO/SQLite?
2. **Multi-tenant git**: Lock-based vs optimistic vs branch-per-agent?
3. **Local model break-even**: What concurrency level justifies sub-2B?
4. **Elicitation system**: How much does codex need?
5. **Thread resumption UX**: When should parent introspect child context?

---

## 13. References

- `helios-qs.md` - User answers to clarifying questions
- `TASK_TEAMMATE_PRD_V2.md` - Teammate system PRD
- `PM_SPEC_TASK_TEAMMATE.md` - Implementation spec
- `helios-consolidated.md` - Research synthesis
- thegent `hierarchical_dispatcher.py` - L^N dispatch implementation

---

_Generated: 2026-02-24_
_Status: Ready for Review_

---

# Addendum: Research Decisions (2026-02-24)

Based on deep research into MCP elicitation, Claude Code patterns, and git strategies, the following decisions have been made:

---

## A. Elicitation System

### A.1 Tool Definition

```typescript
// tools/elicit.ts
const ElicitQuestionSchema = z.object({
  id: z.string(),
  type: z.enum([
    "single_choice",
    "multi_choice",
    "text",
    "number",
    "boolean",
    "file_path",
    "range",
  ]),
  question: z.string(),
  header: z.string().max(32),
  context: z.string().optional(),
  options: z
    .array(
      z.object({
        label: z.string(),
        description: z.string().optional(),
        value: z.any(),
      }),
    )
    .optional(),
  default: z.any().optional(),
  validation: z
    .object({
      min: z.number().optional(),
      max: z.number().optional(),
      pattern: z.string().optional(),
    })
    .optional(),
  required: z.boolean().default(true),
});

const ElicitArgsSchema = z.object({
  questions: z.array(ElicitQuestionSchema).min(1).max(10),
  batch_id: z.string().optional(),
  timeout_s: z.number().default(300),
  priority: z.enum(["blocking", "high", "normal", "low"]),
});
```

### A.2 Rules (Inspired by Claude Code)

1. Max 10 questions per batch
2. Max 6 options per question
3. Header max 32 chars
4. Unique question IDs required
5. Unique option labels per question
6. Auto-timeout with decline action
7. Priority-based escalation

---

## B. Git Strategy: Hybrid Approach

### B.1 Architecture

```
┌────────────────────────────────────────────────────────────┐
│                     Git Automation Layer                    │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐    │
│  │  Optimistic │  │  N-Way      │  │   Shadow Git    │    │
│  │  Edits      │  │  Merge      │  │   (SQLite)      │    │
│  └──────┬──────┘  └──────┬──────┘  └────────┬────────┘    │
│         │                │                   │              │
│         └────────────────┴───────────────────┘              │
│                          │                                  │
│                          ▼                                  │
│              ┌─────────────────────┐                        │
│              │  Conflict Resolver  │                        │
│              │  (Auto → LLM → Flag)│                        │
│              └──────────┬──────────┘                        │
│                         │                                   │
│                         ▼                                   │
│              ┌─────────────────────┐                        │
│              │  Batch Committer    │                        │
│              │  (Turn-end commits) │                        │
│              └─────────────────────┘                        │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

### B.2 Shadow Git Schema

```sql
CREATE TABLE shadow_edits (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    thread_id TEXT,
    agent_id TEXT NOT NULL,
    timestamp REAL NOT NULL,
    file_path TEXT NOT NULL,
    edit_type TEXT NOT NULL,
    hunk_before TEXT,
    hunk_after TEXT,
    line_start INTEGER,
    line_end INTEGER,
    metadata TEXT
);
```

### B.3 Conflict Resolution Flow

```
Conflict? ──▶ Same file, diff hunks? ──▶ Yes ──▶ Auto-merge
                    │
                    No
                    │
                    ▼
             Same hunk? ──▶ No ──▶ N-way merge
                    │
                    Yes
                    │
                    ▼
             LLM merge ──▶ Success? ──▶ Yes ──▶ Apply
                    │
                    No
                    │
                    ▼
             Flag for Agent (NEVER human)
```

---

## C. Helper Model Configuration

### C.1 Model Tiers

| Tier                    | Use Case                             | Current Mapping |
| ----------------------- | ------------------------------------ | --------------- |
| `THEGENT_HELPER_MODEL`  | Commits, annotations, classification | minimaxm2.5     |
| `THEGENT_SUMMARY_MODEL` | Memory summarization                 | (configurable)  |
| `THEGENT_LOCAL_MODEL`   | Sub-2B for zero cost                 | (future)        |

### C.2 Task-Model Mapping

```yaml
task_models:
  commit_message:
    model: "${THEGENT_HELPER_MODEL}"
    max_tokens: 200
    temperature: 0.3

  change_classification:
    model: "${THEGENT_HELPER_MODEL}"
    max_tokens: 50
    temperature: 0.1

  session_annotation:
    model: "${THEGENT_HELPER_MODEL}"
    max_tokens: 500
    temperature: 0.5

  memory_summary:
    model: "${THEGENT_SUMMARY_MODEL:-claude-3-5-haiku}"
    max_tokens: 2000
    temperature: 0.4
```

---

## D. Implementation Priority

| Phase | Components                              | Week |
| ----- | --------------------------------------- | ---- |
| **1** | Elicitation tool, Shadow Git foundation | 1-2  |
| **2** | Optimistic edits, Conflict detection    | 2-3  |
| **3** | N-Way merge, LLM resolver               | 3-4  |
| **4** | Batch committer, Public git sync        | 4-5  |
| **5** | Helper model integration                | 5-6  |
| **6** | Full integration testing                | 6-7  |

---

_Decisions finalized: 2026-02-24_
