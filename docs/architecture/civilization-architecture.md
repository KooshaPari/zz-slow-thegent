# Multi-Tenant Agent Civilization Framework - Architecture Summary

**Status**: Complete Architecture Design
**Date**: 2026-02-19
**Scope**: 5-20 concurrent agents across multiple projects
**Documents**: 5 comprehensive specifications

---

## Document Overview

This architecture is documented across 5 comprehensive design documents:

### 1. **MULTI_TENANT_AGENT_CIVILIZATION_ARCHITECTURE.md**

**Purpose**: System overview, core components, communication patterns
**Key Sections**:

- Executive summary and architecture diagram
- Civilization Control Plane (agent registry, work orchestrator, resource manager, event bus)
- Project-scoped layer (work stream, task state machine, metadata)
- Task state machine (PENDING → CLAIMED → BLOCKED/COMPLETED/FAILED)
- Communication patterns overview (5 core patterns)
- Error handling, timeouts, deadlock detection
- State management and consistency model
- Observability and governance
- Implementation roadmap (5 phases over 6 weeks)
- Backwards compatibility strategy

**Read First**: Start here for system understanding.

### 2. **AGENT_IDENTITY_AND_DISCOVERY.md**

**Purpose**: Agent naming scheme, registry architecture, service discovery
**Key Sections**:

- Agent ID format: `{project}:{uuid}:L{tier}:{role-slug}`
- UUID generation and persistence (`~/.claude/civilization/{project}/{role}.agent-id`)
- Global registry schema (JSON structure with 100+ fields per agent)
- Registry CRUD operations (register, lookup, update, list)
- Service discovery mechanisms (3 options: file-based, MCP, gossip)
- DNS-like lookup protocol with fallbacks
- Address resolution (endpoint priority: MCP → HTTP → Git)
- Health checking and stale agent detection
- Security considerations (identity spoofing prevention)

**When Needed**: Understanding agent identity and how agents find each other.

### 3. **CROSS_PROJECT_COORDINATION_PATTERNS.md**

**Purpose**: Communication protocols for inter-agent coordination
**Key Sections**:

- Pattern 1: Task Dispatch (L1 → L2/L3, sync + async)
- Pattern 2: Cross-Project Requests (L2 ↔ L2 negotiated work)
- Pattern 3: Peer-to-Peer Negotiation (L2 ↔ L2 semaphore-based resource sharing)
- Pattern 4: Status & Escalation (L2 → L1 heartbeat + escalation)
- Pattern 5: Civilization-Wide Broadcasts (events, deadlock alerts, failures)
- Message schemas for all patterns (detailed JSON examples)
- Error handling and retry logic (exponential backoff with jitter)
- Deadlock detection and prevention algorithms
- Message routing decision tree and endpoint fallback chain

**When Needed**: Understanding how agents communicate and coordinate.

### 4. **CIVILIZATION_SCALE_PERFORMANCE.md**

**Purpose**: Resource orchestration and load balancing
**Key Sections**:

- Global resource model (CPU %, memory MB, network Mbps)
- Per-project quota allocation (equal share, usage-based, priority-based)
- Load balancing strategies (3 options: locality-first, load-balanced, hybrid)
- Backpressure mechanisms (admission control, queueing, queue draining)
- Resource borrowing and negotiation (cross-project quota sharing)
- Performance optimization (caching, speculation)
- Observability and metrics (per-agent, civilization-wide dashboards)

**When Needed**: Understanding resource management and load balancing.

### 5. **MULTI_TENANT_CONTROLLER_IMPLEMENTATION_PLAN.md**

**Purpose**: Step-by-step implementation roadmap
**Key Sections**:

- Phase 1 (Week 1-2): Foundation (identity, registry, heartbeat, work stream)
- Phase 2 (Week 2-3): Single-project multi-agent (task dispatch, execution)
- Phase 3 (Week 3-4): Cross-project coordination (requests, global state, events)
- Phase 4 (Week 4-5): Observability (metrics, deadlock detection, audit logging)
- Phase 5 (Week 5-6): Resilience (failure recovery, load balancing, borrowing)
- Deployment strategy (prerequisites, gradual rollout)
- Testing strategy (unit, integration, chaos)
- Success metrics and timeline
- Key decision points and rollback strategy

**When Needed**: Planning implementation and tracking progress.

---

## Quick Reference Guide

### For System Architects

→ Read: **MULTI_TENANT_AGENT_CIVILIZATION_ARCHITECTURE.md** (15 min)
→ Then: **CIVILIZATION_SCALE_PERFORMANCE.md** (10 min)

### For Engineers Implementing Phase 1

→ Read: **AGENT_IDENTITY_AND_DISCOVERY.md** (Agent IDs, registry)
→ Then: **MULTI_TENANT_CONTROLLER_IMPLEMENTATION_PLAN.md** (Phase 1 tasks)

### For Engineers Implementing Phase 2+

→ Read: **CROSS_PROJECT_COORDINATION_PATTERNS.md** (communication protocols)
→ Then: **CIVILIZATION_SCALE_PERFORMANCE.md** (resource orchestration)

### For Ops/SRE

→ Read: **CIVILIZATION_SCALE_PERFORMANCE.md** (metrics, quotas)
→ Then: **CROSS_PROJECT_COORDINATION_PATTERNS.md** (failure modes)

### For QA/Testing

→ Read: **MULTI_TENANT_CONTROLLER_IMPLEMENTATION_PLAN.md** (testing strategy)
→ Then: **CROSS_PROJECT_COORDINATION_PATTERNS.md** (error scenarios)

---

## Key Architecture Decisions

### 1. Distributed Eventual Consistency

**Decision**: Git-based state (not centralized backend)
**Rationale**: Decentralized, works offline, simple integration
**Trade-off**: ~30-second propagation delay vs centralized <100ms

### 2. Hybrid Communication

**Decision**: MCP (real-time) + File-based (reliable fallback)
**Rationale**: Best of both worlds (speed + reliability)
**Trade-off**: More complex than single approach

### 3. Soft Resource Limits

**Decision**: Queue tasks when overloaded, don't kill
**Rationale**: Fair scheduling, no task loss
**Trade-off**: May temporarily exceed quota

### 4. Agent-Centric Identity

**Decision**: UUID generated per agent, immutable
**Rationale**: Unique identity persists across restarts
**Trade-off**: Requires local storage of UUID

### 5. Multi-Tier Hierarchy

**Decision**: L1 (supervisor) → L2 (worker) → L3 (simulated)
**Rationale**: Matches existing Claude Code structure
**Trade-off**: Asymmetric (only L1 creates L2/L3)

---

## Core Concepts

| Concept                   | Definition                                     | Example                                        |
| ------------------------- | ---------------------------------------------- | ---------------------------------------------- |
| **Civilization**          | Entire ecosystem of agents across all projects | All 20 agents working together                 |
| **Agent ID**              | Global unique identifier                       | `kush:8d3f2c1a-...:L2:runner-1`                |
| **Work Stream**           | Unified task list (git-based, shared)          | `WORK_STREAM.md` in `~/.claude/civilization/`  |
| **Registry**              | Golden source of agent identity/location       | `registry.json` with all agents                |
| **Task Dispatch**         | L1 assigns work to L2/L3                       | Synchronous (MCP) or async (queue)             |
| **Cross-Project Request** | L2 asks L2 in different project for help       | Negotiated, with deadline sharing              |
| **Backpressure**          | Rejecting tasks when overloaded                | Return NACK to dispatcher                      |
| **Deadlock**              | Cyclic blocking (Project A → B → A)            | Detect every 60s, alert + recommend resolution |

---

## File Structure

```
~/.claude/civilization/                    # Shared across all projects
├── registry.json                          # Golden registry (agents, projects)
├── WORK_STREAM.md                         # Global work stream (all tasks)
├── resource_state.json                    # Current resource usage
├── event_log.ndjson                       # Append-only event log
├── audit.log                              # Audit trail (all actions)
├── metrics.json                           # Civilization-wide metrics
├── {project}/
│   ├── claude-code.agent-id               # UUID for L1 agent
│   ├── runner-1.agent-id
│   └── researcher-1.agent-id
├── queues/
│   ├── kush:runner-1.mq                   # Message queue for agent
│   └── atoms:researcher-1.mq
├── semaphores/
│   ├── kush/github-api-key                # Lock for shared resource
│   └── atoms/database-connection
└── cache/
    ├── research-http-libs.json            # Shared results cache
    └── api-design-patterns.json
```

---

## State Transitions Diagram

```
Task Lifecycle:
  PENDING (unassigned)
    ↓ [agent claims]
    CLAIMED (assigned, agent working)
    ├─→ BLOCKED (waiting on cross-project dependency)
    │   ├─→ PENDING (unblock event received, retry)
    │   └─→ FAILED (deadline exceeded while blocked)
    ├─→ IN_PROGRESS (agent actively working)
    ├─→ FAILED (agent error/crash)
    │   └─→ PENDING (ready for retry)
    └─→ COMPLETED (task done, output stored)

Agent Lifecycle:
  INACTIVE (not running)
    ↓ [agent starts, registers]
    ACTIVE (sending heartbeats)
    ├─→ STALE (missed 3 heartbeats)
    │   └─→ ACTIVE (heartbeat recovered)
    └─→ INACTIVE (agent stops)
```

---

## Communication Flows

### Synchronous Task Dispatch

```
L1 (kush:claude-code)
  │
  ├─ Resolve agent endpoint (registry lookup)
  ├─ Connect MCP: kush:runner-1
  ├─ Send: task_dispatch_message (task_id, prompt, timeout)
  │
  └─→ kush:runner-1 (L2)
        ├─ Receive task_dispatch
        ├─ Check capacity: OK
        ├─ Send ACK (status=CLAIMED, start_time)
        └─ Begin work
  │
  ← ACK received
  └─ Record: task CLAIMED by runner-1
```

### Cross-Project Request

```
kush:runner-1 (L2)
  │
  ├─ Query registry: agents(project=atoms, capability=research, status=idle)
  ├─ Result: [atoms:researcher-1 available]
  ├─ Send: cross_project_request (description, deadline, incentives)
  │
  └─→ atoms:researcher-1 (L2)
        ├─ Receive request
        ├─ Evaluate: capacity? specialization? timeline?
        ├─ Send response: ACCEPTED + start_time
        └─ Begin work on behalf of kush
  │
  ← ACCEPTED received
  ├─ Create task in WORK_STREAM: scope=[kush, atoms]
  ├─ Mark: blocking on atoms:research-task
  └─ Wait for completion event
        └─ On event: continue with borrowed results
```

---

## Failure Modes & Recovery

| Failure Mode          | Detection                            | Recovery                               |
| --------------------- | ------------------------------------ | -------------------------------------- |
| Agent crash           | Heartbeat timeout (3 missed)         | Reassign tasks to available agent      |
| Task timeout          | Task active > deadline               | Escalate to L1, mark FAILED            |
| Cross-project blocked | Task.time_blocked > deadline - 30min | Escalate (normal), suggest alternative |
| Deadlock (cycle)      | Transitive blocking check            | Alert L1, recommend kill+retry         |
| Resource exhaustion   | Admission control rejects            | Queue task, retry when available       |
| Network partition     | MCP timeout                          | Fall back to file-based communication  |
| Registry corruption   | Git conflict                         | Manual reconciliation (rare)           |

---

## Performance Characteristics

| Metric                      | Value         | Notes               |
| --------------------------- | ------------- | ------------------- |
| Task dispatch (sync)        | <1 second     | MCP real-time       |
| Task dispatch (async)       | 1-5 seconds   | File poll-based     |
| Registry lookup (cache hit) | ~10 ms        | In-memory           |
| Registry lookup (file)      | ~50 ms        | Disk read           |
| Registry lookup (git pull)  | ~1 second     | Network + merge     |
| Cross-project request ack   | ~5-10 seconds | Negotiation         |
| Event propagation           | ~30 seconds   | Git commit + push   |
| Deadlock detection          | ~60 seconds   | Periodic check      |
| Resource quota rebalance    | ~10 seconds   | Recalculate on tick |

---

## Scaling Characteristics

| Aspect                | 5 Agents         | 20 Agents        | 100+ Agents               |
| --------------------- | ---------------- | ---------------- | ------------------------- |
| **Registry size**     | ~10 KB           | ~50 KB           | ~500 KB                   |
| **Lookup latency**    | ~50 ms           | ~50 ms           | ~500 ms (git pull)        |
| **Task dispatch**     | <1 sec           | <1 sec           | ~2 sec (contention)       |
| **Event propagation** | ~30 sec          | ~30 sec          | ~60 sec (merge conflicts) |
| **Recommended arch**  | File-based + MCP | File-based + MCP | Central service           |

**Inflection point**: Beyond ~50 agents, consider migrating to centralized backend.

---

## Next Steps

1. **Review Architecture** (30 min)
   - Read MULTI_TENANT_AGENT_CIVILIZATION_ARCHITECTURE.md
   - Review diagrams, core components, communication patterns
   - Identify any questions or concerns

2. **Validate Decisions** (30 min)
   - Review key architecture decisions (eventual consistency, hybrid communication, etc.)
   - Confirm alignment with project goals
   - Identify missing requirements or constraints

3. **Plan Implementation** (30 min)
   - Review MULTI_TENANT_CONTROLLER_IMPLEMENTATION_PLAN.md
   - Phase 1 (Foundation) estimated ~10-15 tool calls
   - Assign owner and set timeline

4. **Prototype Phase 1** (1-2 hours)
   - Implement agent identity (task 1.1)
   - Implement file-based registry (task 1.2)
   - Implement unified work stream (task 1.3)
   - Test with 2 agents in 1 project

5. **Iterate & Improve**
   - After Phase 1 complete, gather feedback
   - Plan Phase 2 (single-project multi-agent)
   - Continue phased rollout

---

## Architecture Quality Attributes

| Attribute                   | Achieved                                 | How                                       |
| --------------------------- | ---------------------------------------- | ----------------------------------------- |
| **Scalability**             | 5-20 agents → 100+ (future)              | Decentralized, horizontal scaling         |
| **Resilience**              | Agent failures don't cascade             | Isolation, task reassignment              |
| **Simplicity**              | No central service needed                | Git-based state, file-based queues        |
| **Observability**           | Full visibility into civilization        | Registry, metrics, event log, audit trail |
| **Backwards Compatibility** | Existing swarms work unchanged           | Opt-in global features                    |
| **Correctness**             | Deadlock detection, eventual consistency | Regular validation checks                 |
| **Fairness**                | Resources allocated per quota            | Soft limits, queue-based backpressure     |

---

## Assumptions & Constraints

### Assumptions

1. Git available and stable (core dependency)
2. Agents have persistent local storage (~/.claude/civilization/)
3. Network available for MCP (but fallback works offline)
4. Single civilization ID (global-001)
5. < 100 agents in initial deployment

### Constraints

1. Eventual consistency (not strong consistency)
2. ~30 second event propagation delay
3. File-based scalability limit at ~50 agents
4. No built-in security isolation (Project A can read Project B data)
5. Manual quota assignment (no auto-tuning)

---

## Document Authors & Reviewers

**Architecture Design**: Claude Code (Haiku 4.5)
**Date**: 2026-02-19
**Status**: Ready for implementation review

**Reviewers Needed**:

- [ ] Architecture lead (validate design decisions)
- [ ] Implementation lead (validate feasibility)
- [ ] Ops/SRE lead (validate observability)
- [ ] Security lead (validate security assumptions)

---

## Glossary

See individual documents for detailed glossaries:

- **AGENT_IDENTITY_AND_DISCOVERY.md** - Identity & discovery terms
- **CROSS_PROJECT_COORDINATION_PATTERNS.md** - Communication & coordination terms
- **CIVILIZATION_SCALE_PERFORMANCE.md** - Resource & performance terms
- **MULTI_TENANT_AGENT_CIVILIZATION_ARCHITECTURE.md** - Core architecture terms

---

## Contact & Questions

For questions about specific aspects:

- **Architecture/Design**: See MULTI_TENANT_AGENT_CIVILIZATION_ARCHITECTURE.md
- **Agent Identity**: See AGENT_IDENTITY_AND_DISCOVERY.md
- **Communication**: See CROSS_PROJECT_COORDINATION_PATTERNS.md
- **Performance**: See CIVILIZATION_SCALE_PERFORMANCE.md
- **Implementation**: See MULTI_TENANT_CONTROLLER_IMPLEMENTATION_PLAN.md
