<DONE>
# Local Research Audit: Agent Hierarchy & Multi-Agent Systems

> **Date**: 2026-02-18
> **Status**: Comprehensive Audit Complete
> **Scope**: All local codebase research on agent hierarchies, teams, and multi-agent coordination

---

## Executive Summary

This audit identifies **extensive existing research** on multi-agent systems, hierarchies, and coordination patterns across the codebase. Key findings:

- **3 coordination strategies** identified (hierarchical, P2P, hybrid)
- **Multiple framework implementations** (CrewAI patterns, MetaGPT references, AutoGen patterns)
- **Production-ready patterns** from crun, smolgents, heliosShield
- **Hierarchical blackboard** system already designed
- **File-based IPC** coordination protocol documented
- **Team/swarm patterns** extensively researched

---

## 1. Coordination Strategies

### 1.1 CRUN Deep Dive (trace/docs/reference/CRUN_DEEP_DIVE.md)

**Three Coordination Strategies:**

#### Strategy 1: Hierarchical (Leader-Follower)
- Centralized coordination with leader agent
- Leader assigns tasks to workers
- Parallel execution of assignments
- **Recommendation**: Use for multi-view orchestration

#### Strategy 2: Peer-to-Peer (Bidding)
- Decentralized coordination via bidding
- Tasks announced to all agents
- Collect bids (cost estimates)
- Select winners (lowest cost)
- **Recommendation**: Use for normal load scenarios

#### Strategy 3: Hybrid (Adaptive)
- Adaptive strategy switching based on load
- High load (>0.7) → Hierarchical
- Normal load → P2P
- **Recommendation**: Use for trace's view orchestration

**Key Patterns:**
- DAG-based execution with TopologicalSorter
- PERT/Monte Carlo planning
- State persistence via SQLAlchemy
- OpenTelemetry observability
- ReAct agent pattern

---

## 2. Framework Implementations

### 2.1 SmolGents Architecture (smolgents/docs/ARCHITECTURE.md)

**Execution Modes:**
- **Sequential**: Tasks executed one after another
- **Hierarchical**: Based on agent hierarchy (managers first)
- **Custom**: User-defined execution logic

**CrewExecutor Hierarchical Implementation:**
```python
def execute_hierarchical(self):
    # Sort agents by role (managers first)
    sorted_agents = sorted(
        agents, key=lambda a: (0 if "manager" in a.role.lower() or "lead" in a.role.lower() else 1, a.role)
    )

    # Assign priority tasks to managers
    manager_agents = [a for a in sorted_agents if "manager" in a.role.lower()]
    worker_agents = [a for a in sorted_agents if a not in manager_agents]

    # Assign tasks hierarchically
    priority_tasks = tasks[: len(manager_agents)]
    regular_tasks = tasks[len(manager_agents) :]
```

**Key Components:**
- TaskExecutor: Synchronous task execution
- CrewExecutor: Multi-agent orchestration
- RouterManager: Unified routing interface
- AgentSelector: Capability-based selection
- LoadBalancer: Agent load tracking

---

### 2.2 Multi-Swarm Hierarchy (thegent/docs/reference/MULTI_SWARM_HIERARCHY_DEPTH.md)

**Hierarchical Blackboard System:**

#### Global Blackboard
- Stores high-level goals and "Global Constants"
- Orchestrated by Commander Swarm (high-level planners)

#### Regional Blackboards (Swarms)
- Each functional swarm has its own regional blackboard
- Agents coordinate locally using Stigmergy
- Modify regional `WORK_STREAM.md`

**Multi-Swarm Communication:**
- Stigmergic Handoff via "Handoff Artifacts"
- Frontend Swarm completes UI → posts Conformance_Artifact
- Security Swarm detects artifact → triggers Pen-Test Cycle
- Indirect coordination allows independent scaling

**Scaling Mechanics:**
- Redis databases partitioned by Swarm_ID
- Global Shared Log provides unified audit trail
- Each swarm has Adaptive Concurrency Controller
- Hysteresis per swarm (different scales per swarm)

**Federated Governance:**
- Global Policies: Mandatory for all swarms
- Local Policies: Specific to swarm

---

## 3. Agent Mesh & Coordination

### 3.1 File-Based IPC Protocol (heliosShield/compass_artifact_wf-0975646a-645a-4dd9-82ca-5d096f2e188a_text_markdown.md)

**Core Architecture:**
- File-based IPC on tmpfs (`/dev/shm/`)
- Maildir pattern for lock-free message queues
- Atomic `rename()` for crash-safe operations
- `flock` for mutual exclusion
- `inotifywait` for event-driven reactivity

**Coordination Directory Structure:**
```
/dev/shm/agent-coord/
├── registry/           # Agent capability manifests (JSON)
├── heartbeats/         # Liveness timestamps
├── tasks/
│   ├── new/            # Unclaimed tasks (Maildir)
│   ├── claimed/        # Active work
│   └── done/           # Completed tasks
├── messages/           # Per-agent Maildir inboxes
├── intents/            # "I'm about to modify X" broadcasts
├── locks/              # File ownership (mkdir-based)
└── state/              # Shared work plan (JSON + flock)
```

**Key Patterns:**
- Task claiming via atomic `mkdir`
- Heartbeat-based failure detection
- Intent broadcasting prevents conflicts
- Directory-level partitioning (assign `src/auth/` to one agent)

**Message Envelope Format:**
```json
{
  "id": "msg-uuid",
  "sender": "claude-code-1",
  "recipient": "aider-1",
  "timestamp": "2026-02-09T10:30:00Z",
  "type": "task_result",
  "ttl_seconds": 600,
  "payload": { "task_id": "task-042", "status": "completed" }
}
```

**Lamport Timestamps** for causal ordering

---

### 3.2 Agent Mesh Research (heliosShield/agent-mesh-research-r3-consensus-escalation-2026.md)

**Claude Code Agent Teams:**
- Team lead coordinates, spawns teammates
- Teammates work independently in own context windows
- Shared task list with dependency tracking
- Peer-to-peer messaging via JSON inboxes
- Split pane mode via tmux/iTerm2

**TeammateTool Operations (13 total):**
- spawnTeam, spawn, write, broadcast, read, list, shutdown
- Directory: `~/.claude/teams/{name}/inboxes/{agent}.json`
- Task files: `~/.claude/tasks/{team-name}/{n}.json`
- `blockedBy` dependency tracking with auto-unblock

**Mesh Layer Interface Pattern:**
- Treat each CLI process as atomic unit
- Don't reach into CLI internal hierarchies
- Use standard coordination primitives

---

## 4. Delegation Patterns

### 4.1 Manager Pattern (heliosShield/agents.md, trace/claude.md)

**CRITICAL**: Operate as strategic manager, not worker. Delegate to subagents.

**Keep in Main Context:**
- User intent and requirements
- Strategic decisions and trade-offs
- Summaries of completed work
- Critical architectural knowledge

**Delegate to Subagents:**
- File exploration (>3 files)
- Pattern searches across codebase
- Multi-file implementations
- Long command sequences
- Test execution

**Subagent Swarm (Async Orchestration):**
- Call task agents async (don't block)
- Max 50 concurrent task agents at a time
- Work in between (planning, monitoring)
- Reawaken on completion
- Spawn more agents or continue work

**Delegation Quick Reference:**
| Need | Delegate To | Example Prompt |
|------|-------------|----------------|
| Find code patterns | `Explore` | "Find all error handling patterns" |
| Design approach | `Plan` | "Design auth implementation strategy" |
| Run commands | `Bash` | "Run test suite and report failures" |
| Multi-step implementation | `general-purpose` | "Implement and test feature X" |

---

### 4.2 Microagent Delegation Research (smolgents/RESEARCH_MICROAGENT_DELEGATION.md)

**Multi-Agent Task Decomposition Framework:**

**Problem:** Single monolithic agents struggle with:
- Token limit constraints
- Role overload (reasoning, planning, tool selection, execution)
- Inefficient resource utilization
- Error propagation from early missteps

**Solution:** Decompose into specialized agents:
```
User Query
    ↓
[Intent Router Agent] ← Classifies task type
    ↓
  ┌─────────────────────────────────────────┐
  ├─→ [Task Decomposer Agent]
  ├─→ [Tool Router Agent]
  ├─→ [Model Selector Agent]
  ├─→ [Specialized Domain Agent]
  ├─→ [Validator Agent]
  └─→ [Memory/Context Agent]
```

**Key Design Principles:**
1. **Solvability**: Each subtask independently solvable
2. **Completeness**: All aspects decomposed
3. **Non-Redundancy**: No overlapping responsibilities

**Results:**
- Knapsack problem: 3% → 95% accuracy
- Task assignment: Up to 100% accuracy
- Travel planning: 2.92% → 42.68% success rate (14x improvement)

**Model Routing Economics:**
- Phi-3 (local): ~$0.10/1M tokens
- Claude 3.5 Haiku: ~$0.80/1M tokens
- Claude 3.5 Sonnet: ~$3.00/1M tokens
- GPT-4 Turbo: ~$10.00/1M tokens

**Routing Decision Framework:**
1. Lightweight Complexity Estimation (5-10 tokens)
2. k-Nearest Neighbor Matching
3. Hierarchical Filtering

**Cost Savings:**
- Anthropic: 27% cost savings within Q1
- Industry average: 30-50% cost reduction
- Up to 80% savings with routing + prompt optimization

---

## 5. Team & Swarm Patterns

### 5.1 Kimaki Multi-Agent System (kimaki/COMPREHENSIVE-MULTI-AGENT-PLAN.md)

**Agent Pool Registry:**
```typescript
interface AgentRegistration {
  id: string
  name: string
  pronunciation: string
  role: string
  personality: string
  systemPrompt: string
  voice: string
  expertise: string[]

  // Project assignments
  projects: Array<{
    projectId: string
    role: 'primary' | 'secondary' | 'consultant'
    permissions: string[]
  }>

  // Collaboration rules
  collaborationRules: {
    canInitiateWith: string[]
    mustConsultWith: string[]
    ignoreAgents: string[]
    autoJoinTopics: string[]
  }
}
```

**Project Context Manager:**
- Maintains context for each project
- Assigned agents with roles (lead, contributor, consultant)
- Conversation history
- Knowledge base (codebase, documentation, decisions)
- Integrations (GitHub, Jira, Slack)

**Conversation Rules Engine:**
- Ignore Rules (when agents should NOT interact)
- Collaboration Rules (when agents SHOULD interact)
- Moderation Rules (user as moderator)
- Autonomous Rules (agents discuss without user)

---

### 5.2 Teammates Research (thegent/docs/research/TEAMMATES_RESEARCH_AND_PLAN.md)

**Claude Code Teammates Characteristics:**
- Delegation: Primary orchestrator breaks down tasks
- Specialization: Teammates have specific roles
- Collaboration: Multiple agents work on same codebase
- Context Handoff: Structured data (XML tags) for instructions/results

**Implementation Strategy: "Teammate Swarm"**

**Orchestration (Thegent Layer):**
- `thegent sitback` as primary entry point
- `thegent teammates list`: Discover specialized personas
- `thegent teammates delegate <persona> <prompt>`: Spawn async sub-agent
- Status Tracking: Use EvidenceGraph to link actions

**Coordination (heliosShield Layer):**
- Git Parallelism (Phase 6): Multiple agents commit concurrently
- Smart Merge (Phase 7): AST-aware conflict resolution
- Task Coordination (Phase 11): Filesystem-native task queue

**Handoff Protocol (Task Tool Layer):**
- `<Thought>`: Internal reasoning
- `<Action>`: The delegated task
- `<Result>`: The teammate's output
- `<Handoff>`: Explicit transfer with confidence scores

**TeammateManager Implementation:**
- `list_personas()`: Discover teammates from agent markdown files
- `delegate()`: Delegate task to teammate
- `update_status()`: Update delegation status
- `get_delegations()`: List all delegations

---

## 6. Production Patterns

### 6.1 heliosShield Coordination (heliosShield/docs/architecture/)

**System Hierarchy:**
```
heliosShield/
├── bin/harness                 # Dispatcher + CLI
├── proxy/                      # Symlink farm (intercepted commands)
├── lib/core.sh                 # Core orchestration/strategies
├── lib/readcache.sh            # Read-path warm and stat-cache helpers
├── mesh.sh                     # IPC/mailbox/WAL/discovery primitives
├── rules.conf                  # Strategy policy rules
├── etc/agents.conf             # Agent detection patterns
└── var/                        # Runtime locks/cache/coordination state
```

**Runtime Planes:**
- Control Plane: Rule resolution, strategy dispatch, queue arbitration
- Data Plane: Command execution, cache read/write, lock handoff
- State Plane: `var/cache`, `var/locks`, `var/coordination`

**Strategies:**
- `coalesce`: Dedupe + cache (flock + cache files)
- `queue`: Bounded parallelism (ticket queue + slot locks)
- `priority_q`: Explicit priority (queue alias)
- `debounce`: Absorb bursts (sleep delay)
- `passthrough`: Zero overhead (direct exec)

---

## 7. Key Findings & Patterns

### 7.1 Common Patterns Across Systems

1. **Hierarchical Coordination**
   - Leader-Follower pattern (CRUN)
   - Manager-Worker pattern (SmolGents)
   - Commander Swarm pattern (Multi-Swarm)

2. **Task Assignment**
   - Role-based assignment (managers first)
   - Capability-based selection
   - Load-balanced distribution

3. **Communication**
   - File-based IPC (Maildir pattern)
   - Message envelopes (JSON)
   - Lamport timestamps for ordering

4. **Delegation**
   - Manager pattern (strategic vs worker)
   - Async swarm orchestration
   - Max 50 concurrent agents

5. **Team Organization**
   - Functional teams (domain expertise)
   - Project teams (temporary)
   - Ad-hoc teams (task-scoped)

---

### 7.2 Implementation Gaps

**What Exists:**
- ✅ Coordination strategies (hierarchical, P2P, hybrid)
- ✅ Execution modes (sequential, hierarchical, custom)
- ✅ File-based IPC protocol
- ✅ Delegation patterns
- ✅ Team/swarm concepts

**What's Missing:**
- ❌ Unified hierarchy manager implementation
- ❌ Explicit parent-child relationship tracking
- ❌ Team management API
- ❌ Cross-team collaboration protocol
- ❌ Hierarchy visualization tools

---

## 8. Recommendations

### 8.1 Leverage Existing Patterns

1. **Use CRUN's Hybrid Coordination**
   - Adaptive strategy switching
   - Hierarchical under load, P2P normally

2. **Adopt SmolGents Execution Modes**
   - Hierarchical execution with role-based assignment
   - Manager-first task assignment

3. **Implement File-Based IPC**
   - Maildir pattern for messages
   - Atomic operations for coordination
   - Heartbeat-based failure detection

4. **Follow Manager Pattern**
   - Strategic managers delegate to workers
   - Max 50 concurrent agents
   - Async swarm orchestration

### 8.2 Build on Existing Research

1. **Extend Multi-Swarm Hierarchy**
   - Global/Regional blackboard system
   - Stigmergic handoff patterns
   - Federated governance

2. **Integrate Teammate System**
   - TeammateManager already exists
   - Add hierarchy support
   - Enhance delegation protocol

3. **Use heliosShield Coordination**
   - Git parallelism for concurrent work
   - Smart merge for conflict resolution
   - Task queue for coordination

---

## 9. References

### Key Documents Reviewed

1. **Coordination & Execution**
   - `trace/docs/reference/CRUN_DEEP_DIVE.md`
   - `smolgents/docs/ARCHITECTURE.md`
   - `smolgents/src/executors/crew_executor.py`

2. **Hierarchy & Swarms**
   - `thegent/docs/reference/MULTI_SWARM_HIERARCHY_DEPTH.md`
   - `heliosShield/compass_artifact_wf-0975646a-645a-4dd9-82ca-5d096f2e188a_text_markdown.md`

3. **Delegation & Teams**
   - `heliosShield/agents.md`
   - `trace/claude.md`
   - `smolgents/RESEARCH_MICROAGENT_DELEGATION.md`
   - `thegent/docs/research/TEAMMATES_RESEARCH_AND_PLAN.md`

4. **Multi-Agent Systems**
   - `kimaki/COMPREHENSIVE-MULTI-AGENT-PLAN.md`
   - `kimaki/MULTI-AGENT-COMMUNICATION-ARCHITECTURE.md`
   - `heliosShield/agent-mesh-research-r3-consensus-escalation-2026.md`

5. **Coordination Protocols**
   - `heliosShield/docs/architecture/00-system-overview.md`
   - `heliosShield/docs/architecture/04-flow-atlas.md`

---

## 10. Next Steps

1. **Synthesize with Web Research**
   - Compare local patterns with CrewAI, MetaGPT, AutoGen
   - Identify best practices from industry frameworks
   - Validate design against academic research

2. **Create Unified Design**
   - Integrate findings into hierarchy design
   - Build on existing patterns
   - Fill identified gaps

3. **Implementation Plan**
   - Leverage existing code (SmolGents, heliosShield)
   - Extend TeammateManager
   - Implement hierarchy manager

---

**Status**: Local audit complete. Ready for web research synthesis.
