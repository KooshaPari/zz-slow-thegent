# Multi-Tenant Agent Civilization Framework - Complete Architecture

Welcome to the comprehensive Multi-Tenant Agent Civilization Framework design. This folder contains production-ready architectural documentation for coordinating 5-20 concurrent agents across multiple projects.

**Created**: 2026-02-19
**Status**: Complete Design v1.0
**Total Documentation**: 6,116 lines across 6 documents
**Implementation Timeline**: 6 weeks (phased deployment)

---

## 📚 Documentation Set

### **Start Here** → [CIVILIZATION_ARCHITECTURE_SUMMARY.md](./CIVILIZATION_ARCHITECTURE_SUMMARY.md)

**(16 min read)**

Quick reference guide with:

- Document overview and reading paths
- Key architecture decisions with rationale
- Core concepts glossary
- File structure diagram
- State transitions and communication flows
- Failure modes and recovery strategies
- Performance characteristics and scaling limits

**Read this first** to understand the entire architecture at a glance.

---

## 📖 Core Documents

### 1. **[MULTI_TENANT_AGENT_CIVILIZATION_ARCHITECTURE.md](./MULTI_TENANT_AGENT_CIVILIZATION_ARCHITECTURE.md)**

**(938 lines, ~30 min read)**

**Complete system architecture covering:**

- Executive summary and architecture diagram (ASCII art)
- Civilization Control Plane (4 core components):
  - Agent Registry Service
  - Work Orchestrator
  - Resource Manager (civilization-scale)
  - Event Bus
- Project-scoped layer with work streams and task state machine
- Identity & discovery system with agent ID semantics
- Communication protocols (5 core patterns overview)
- Error handling, timeouts, deadlock detection
- State management with eventual consistency model
- Observability and governance frameworks
- Implementation roadmap (5 phases)
- Backwards compatibility strategy

**Best for**: System architects, leadership, getting the "big picture"

**Read when**: Designing the civilization, validating high-level decisions

---

### 2. **[AGENT_IDENTITY_AND_DISCOVERY.md](./AGENT_IDENTITY_AND_DISCOVERY.md)**

**(1,008 lines, ~35 min read)**

**Complete agent identification and service discovery covering:**

- Agent ID format: `{project}:{uuid}:L{tier}:{role-slug}`
- UUID generation and persistence strategy
- Global registry schema (complete JSON example with 50+ fields)
- Registry CRUD operations with code examples
- Three service discovery options (file-based, MCP, gossip) with comparison
- DNS-like resolution protocol with detailed examples
- Address resolution with endpoint fallback chain (MCP → HTTP → Git)
- Health checking and stale agent detection
- Registry consistency and conflict resolution
- CRDT approach for concurrent updates
- Security considerations and identity spoofing prevention

**Best for**: Engineers implementing agent identity, registry, discovery

**Read when**: Building agent registration, implementing lookup mechanisms

---

### 3. **[CROSS_PROJECT_COORDINATION_PATTERNS.md](./CROSS_PROJECT_COORDINATION_PATTERNS.md)**

**(895 lines, ~35 min read)**

**Five core communication patterns with complete protocols:**

**Pattern 1: Task Dispatch (L1 → L2/L3)**

- Synchronous path (MCP, real-time)
- Asynchronous path (queue-based, reliable)
- Detailed message schemas (JSON)
- Comparison table (sync vs async)

**Pattern 2: Cross-Project Requests (L2 ↔ L2)**

- Request-response flow with negotiation
- Message schemas (request, accepted, deferred)
- Shared deadline semantics
- Cross-project credit tracking

**Pattern 3: Peer-to-Peer Negotiation (L2 ↔ L2 same project)**

- Semaphore-based resource coordination
- Lease-based locking algorithm
- Queue fairness mechanism
- Lock acquisition and release algorithms

**Pattern 4: Status & Escalation (L2/L3 → L1)**

- Periodic heartbeat messages
- Escalation triggers and policies
- Detailed message schemas
- Action recommendations

**Pattern 5: Civilization-Wide Broadcasts (Events)**

- Event bus architecture
- Specific event schemas (resource breach, deadlock, agent failure)
- TTL and acknowledgement semantics
- Recommended actions for each event type

**Plus:**

- Error handling and timeouts (hierarchy table)
- Retry logic with exponential backoff and jitter
- Deadlock detection and prevention algorithms
- Message routing decision tree
- Endpoint fallback chain

**Best for**: Engineers building communication layer, implementing agents

**Read when**: Implementing task dispatch, cross-project requests, status updates

---

### 4. **[CIVILIZATION_SCALE_PERFORMANCE.md](./CIVILIZATION_SCALE_PERFORMANCE.md)**

**(837 lines, ~30 min read)**

**Resource orchestration and load balancing covering:**

**Global Resource Model**:

- Resource types (CPU %, memory MB, network Mbps)
- Resource state structure with civilization totals
- Available vs quota tracking

**Quota Allocation (3 algorithms)**:

- Option 1: Equal share (simplest)
- Option 2: Usage-based (adaptive)
- Option 3: Priority-based (flexible)
- Recommended hybrid approach with code examples

**Load Balancing (3 strategies)**:

- Strategy 1: Locality first (prefer same-project agents)
- Strategy 2: Load balanced (fair distribution globally)
- Strategy 3: Hybrid (locality with overflow) [RECOMMENDED]
- Complete selection algorithm with code examples

**Backpressure Mechanisms**:

- Admission control (accept/reject decision algorithm)
- Queueing strategy (when to queue)
- Queue draining (releasing queued tasks when capacity available)

**Resource Negotiation**:

- Cross-project borrowing protocol
- Quota adjustment semantics
- Reclamation mechanics (lender reclaims borrowed resources)
- Message schemas for requests and approvals

**Performance Optimization**:

- Caching and memoization (shared result cache)
- Speculative execution (pipelining tasks)
- Cross-project cache hit example

**Observability**:

- Per-agent metrics structure
- Civilization-wide metrics JSON with 30+ fields
- Health indicators and alert conditions

**Best for**: Operations, resource management, performance optimization

**Read when**: Tuning resource quotas, implementing load balancing

---

### 5. **[MULTI_TENANT_CONTROLLER_IMPLEMENTATION_PLAN.md](./MULTI_TENANT_CONTROLLER_IMPLEMENTATION_PLAN.md)**

**(1,046 lines, ~40 min read)**

**Step-by-step implementation roadmap covering:**

**Phase 1: Foundation (Week 1-2)**

- Task 1.1: Agent identity (UUID generation, persistence)
- Task 1.2: File-based registry (CRUD, git persistence)
- Task 1.3: Unified work stream (markdown format, state machine)
- Task 1.4: Heartbeat mechanism (periodic status updates)
- Task 1.5: Stale detection (mark inactive agents)
- ~10-15 tool calls total

**Phase 2: Single-Project Multi-Agent (Week 2-3)**

- Task 2.1: Sync task dispatch (L1 → L2)
- Task 2.2: Async task dispatch (queue-based)
- Task 2.3: L2 task executor (execution + storage)
- Task 2.4: Load monitoring & admission control
- ~8-12 tool calls total

**Phase 3: Cross-Project Coordination (Week 3-4)**

- Task 3.1: Global work stream (centralized)
- Task 3.2: Cross-project requests (agent-to-agent)
- Task 3.3: Global resource state (civilization-wide tracking)
- Task 3.4: Event bus (pub-sub)
- ~7-10 tool calls total

**Phase 4: Observability & Governance (Week 4-5)**

- Task 4.1: Metrics dashboard (civilization status)
- Task 4.2: Deadlock detection (cycle finding)
- Task 4.3: Audit logging (event trail)
- ~5-7 tool calls total

**Phase 5: Resilience & Optimization (Week 5-6)**

- Task 5.1: Agent failure recovery (task reassignment)
- Task 5.2: Load balancing algorithm (smart selection)
- Task 5.3: Resource borrowing (quota negotiation)
- ~6-9 tool calls total

**Plus:**

- Deployment strategy with prerequisites and checklist
- Key decision points with rationale and alternatives
- Rollback strategy for each phase
- Testing strategy (unit, integration, chaos)
- Success metrics by phase
- Timeline summary table
- Open questions for implementation review

**Total Effort**: 40-60 tool calls over 6 weeks
**Team**: 1-2 agents, 10-20 min per phase

**Best for**: Implementation leaders, sprint planners, developers

**Read when**: Planning implementation, assigning work, tracking progress

---

## 🗺️ Quick Navigation

### By Role

**Systems Architect / Designer**

1. Read: [CIVILIZATION_ARCHITECTURE_SUMMARY.md](./CIVILIZATION_ARCHITECTURE_SUMMARY.md) (16 min)
2. Read: [MULTI_TENANT_AGENT_CIVILIZATION_ARCHITECTURE.md](./MULTI_TENANT_AGENT_CIVILIZATION_ARCHITECTURE.md) (30 min)
3. Reference: [CIVILIZATION_SCALE_PERFORMANCE.md](./CIVILIZATION_SCALE_PERFORMANCE.md) (30 min)

**Implementation Lead**

1. Read: [CIVILIZATION_ARCHITECTURE_SUMMARY.md](./CIVILIZATION_ARCHITECTURE_SUMMARY.md) (16 min)
2. Read: [MULTI_TENANT_CONTROLLER_IMPLEMENTATION_PLAN.md](./MULTI_TENANT_CONTROLLER_IMPLEMENTATION_PLAN.md) (40 min)
3. Reference: [AGENT_IDENTITY_AND_DISCOVERY.md](./AGENT_IDENTITY_AND_DISCOVERY.md) for Phase 1
4. Reference: [CROSS_PROJECT_COORDINATION_PATTERNS.md](./CROSS_PROJECT_COORDINATION_PATTERNS.md) for Phase 2+

**Backend/Infrastructure Engineer**

1. Read: [AGENT_IDENTITY_AND_DISCOVERY.md](./AGENT_IDENTITY_AND_DISCOVERY.md) (35 min)
2. Read: [CROSS_PROJECT_COORDINATION_PATTERNS.md](./CROSS_PROJECT_COORDINATION_PATTERNS.md) (35 min)
3. Reference: [MULTI_TENANT_CONTROLLER_IMPLEMENTATION_PLAN.md](./MULTI_TENANT_CONTROLLER_IMPLEMENTATION_PLAN.md) (40 min)

**Operations / SRE**

1. Read: [CIVILIZATION_SCALE_PERFORMANCE.md](./CIVILIZATION_SCALE_PERFORMANCE.md) (30 min)
2. Reference: [CIVILIZATION_ARCHITECTURE_SUMMARY.md](./CIVILIZATION_ARCHITECTURE_SUMMARY.md) (16 min)
3. Reference: [CROSS_PROJECT_COORDINATION_PATTERNS.md](./CROSS_PROJECT_COORDINATION_PATTERNS.md) (error modes section)

**QA / Tester**

1. Read: [MULTI_TENANT_CONTROLLER_IMPLEMENTATION_PLAN.md](./MULTI_TENANT_CONTROLLER_IMPLEMENTATION_PLAN.md) (testing strategy section)
2. Reference: [CROSS_PROJECT_COORDINATION_PATTERNS.md](./CROSS_PROJECT_COORDINATION_PATTERNS.md) (error scenarios)
3. Reference: [CIVILIZATION_ARCHITECTURE_SUMMARY.md](./CIVILIZATION_ARCHITECTURE_SUMMARY.md) (failure modes table)

### By Phase

**Phase 1: Foundation (Agent Identity + Registry)**

- Start: [AGENT_IDENTITY_AND_DISCOVERY.md](./AGENT_IDENTITY_AND_DISCOVERY.md)
- Plan: [MULTI_TENANT_CONTROLLER_IMPLEMENTATION_PLAN.md](./MULTI_TENANT_CONTROLLER_IMPLEMENTATION_PLAN.md) § Phase 1

**Phase 2: Single-Project Multi-Agent (Task Dispatch)**

- Start: [CROSS_PROJECT_COORDINATION_PATTERNS.md](./CROSS_PROJECT_COORDINATION_PATTERNS.md) § Pattern 1
- Plan: [MULTI_TENANT_CONTROLLER_IMPLEMENTATION_PLAN.md](./MULTI_TENANT_CONTROLLER_IMPLEMENTATION_PLAN.md) § Phase 2

**Phase 3: Cross-Project Coordination**

- Start: [CROSS_PROJECT_COORDINATION_PATTERNS.md](./CROSS_PROJECT_COORDINATION_PATTERNS.md) § Patterns 2-3
- Plan: [MULTI_TENANT_CONTROLLER_IMPLEMENTATION_PLAN.md](./MULTI_TENANT_CONTROLLER_IMPLEMENTATION_PLAN.md) § Phase 3

**Phase 4: Observability**

- Start: [CIVILIZATION_SCALE_PERFORMANCE.md](./CIVILIZATION_SCALE_PERFORMANCE.md) § Observability
- Plan: [MULTI_TENANT_CONTROLLER_IMPLEMENTATION_PLAN.md](./MULTI_TENANT_CONTROLLER_IMPLEMENTATION_PLAN.md) § Phase 4

**Phase 5: Resilience & Optimization**

- Start: [CIVILIZATION_SCALE_PERFORMANCE.md](./CIVILIZATION_SCALE_PERFORMANCE.md) § Load Balancing
- Plan: [MULTI_TENANT_CONTROLLER_IMPLEMENTATION_PLAN.md](./MULTI_TENANT_CONTROLLER_IMPLEMENTATION_PLAN.md) § Phase 5

---

## 🎯 Key Highlights

### Architecture Principles

- **Distributed**: No central service needed (git-based state)
- **Resilient**: Agent failures don't cascade (isolation, task reassignment)
- **Simple**: Minimal dependencies (git, MCP, local files)
- **Observable**: Full visibility (registry, metrics, event log, audit trail)
- **Backwards Compatible**: Existing single-project swarms work unchanged

### Core Innovation

- **Civilization Control Plane**: Decentralized coordination via git + MCP
- **Agent Identity**: Global UUIDs immutable per agent, persistent across restarts
- **Multi-Tier Hierarchy**: L1 (supervisor) → L2 (worker) → L3 (simulated)
- **Hybrid Communication**: MCP (real-time) + File-based (reliable fallback)
- **Eventual Consistency**: Decentralized state with ~30s propagation

### Scaling Path

- **5-20 agents**: File-based + MCP (current design)
- **20-50 agents**: File-based + MCP + optimization (caching, load balancing)
- **50-100+ agents**: Consider centralized backend (future)

---

## 📊 Documentation Statistics

| Document                                                                                             | Lines     | Size       | Read Time    |
| ---------------------------------------------------------------------------------------------------- | --------- | ---------- | ------------ |
| [CIVILIZATION_ARCHITECTURE_SUMMARY.md](./CIVILIZATION_ARCHITECTURE_SUMMARY.md)                       | 392       | 15 KB      | 16 min       |
| [MULTI_TENANT_AGENT_CIVILIZATION_ARCHITECTURE.md](./MULTI_TENANT_AGENT_CIVILIZATION_ARCHITECTURE.md) | 938       | 32 KB      | 30 min       |
| [AGENT_IDENTITY_AND_DISCOVERY.md](./AGENT_IDENTITY_AND_DISCOVERY.md)                                 | 1,008     | 29 KB      | 35 min       |
| [CROSS_PROJECT_COORDINATION_PATTERNS.md](./CROSS_PROJECT_COORDINATION_PATTERNS.md)                   | 895       | 26 KB      | 35 min       |
| [CIVILIZATION_SCALE_PERFORMANCE.md](./CIVILIZATION_SCALE_PERFORMANCE.md)                             | 837       | 24 KB      | 30 min       |
| [MULTI_TENANT_CONTROLLER_IMPLEMENTATION_PLAN.md](./MULTI_TENANT_CONTROLLER_IMPLEMENTATION_PLAN.md)   | 1,046     | 31 KB      | 40 min       |
| **TOTAL**                                                                                            | **6,116** | **157 KB** | **~186 min** |

---

## ✅ Implementation Readiness

This architecture is ready for implementation with:

- ✅ Complete system design with ASCII diagrams
- ✅ Detailed component specifications
- ✅ Complete message schemas (JSON examples)
- ✅ Algorithm pseudocode
- ✅ File structure and persistence strategy
- ✅ Error handling and recovery procedures
- ✅ Phase-by-phase implementation plan
- ✅ Success metrics and testing strategy
- ✅ Scaling path to 100+ agents

**Ready for**: Architecture review → Implementation planning → Phased rollout

---

## 🚀 Getting Started

### For Understanding the Architecture

1. **Start here**: [CIVILIZATION_ARCHITECTURE_SUMMARY.md](./CIVILIZATION_ARCHITECTURE_SUMMARY.md) (16 min)
2. **Deep dive**: Choose based on your role (see Quick Navigation)
3. **Reference**: Use as needed during implementation

### For Implementation

1. **Review Phase 1 plan**: [MULTI_TENANT_CONTROLLER_IMPLEMENTATION_PLAN.md](./MULTI_TENANT_CONTROLLER_IMPLEMENTATION_PLAN.md) § Phase 1
2. **Read identity docs**: [AGENT_IDENTITY_AND_DISCOVERY.md](./AGENT_IDENTITY_AND_DISCOVERY.md)
3. **Start coding**: ~10-15 tool calls for Phase 1 foundation

### For Decision Making

1. **Review decisions**: [CIVILIZATION_ARCHITECTURE_SUMMARY.md](./CIVILIZATION_ARCHITECTURE_SUMMARY.md) § Key Decisions
2. **Check alternatives**: Each document has decision rationale
3. **Plan review**: Hold architecture review before Phase 1 implementation

---

## 📝 Document Index

| #   | Document                                            | Type    | Size  | Purpose                      |
| --- | --------------------------------------------------- | ------- | ----- | ---------------------------- |
| 0   | **README_CIVILIZATION_ARCHITECTURE.md**             | Index   | This  | Navigation guide             |
| 1   | **CIVILIZATION_ARCHITECTURE_SUMMARY.md**            | Summary | 15 KB | Overview + quick reference   |
| 2   | **MULTI_TENANT_AGENT_CIVILIZATION_ARCHITECTURE.md** | Core    | 32 KB | System architecture + design |
| 3   | **AGENT_IDENTITY_AND_DISCOVERY.md**                 | Spec    | 29 KB | Agent ID system + registry   |
| 4   | **CROSS_PROJECT_COORDINATION_PATTERNS.md**          | Spec    | 26 KB | Communication protocols      |
| 5   | **CIVILIZATION_SCALE_PERFORMANCE.md**               | Spec    | 24 KB | Resource orchestration       |
| 6   | **MULTI_TENANT_CONTROLLER_IMPLEMENTATION_PLAN.md**  | Plan    | 31 KB | Implementation roadmap       |

---

## 🔍 Key Concepts At a Glance

- **Civilization**: Entire ecosystem of agents across all projects
- **Agent ID**: `{project}:{uuid}:L{tier}:{role-slug}`
- **Work Stream**: Unified task list (git-based, shared)
- **Registry**: Golden source of agent identity
- **Control Plane**: Decentralized services (registry, orchestrator, resource manager, event bus)
- **Task Dispatch**: L1 assigns work to L2/L3 (sync or async)
- **Cross-Project Request**: L2 negotiates work with L2 in different project
- **Eventual Consistency**: Agents converge to consistent state over time

---

## 💡 Architecture Highlights

### Distributed Coordination Without Central Service

Uses git as distributed state store. All agents eventually consistent within ~30 seconds.

### Multi-Tier Agent Hierarchy

- **L1**: Claude Code (supervisor, human-in-loop)
- **L2**: Spawned agents (workers, autonomous)
- **L3**: Simulated agents (e.g., Cursor windows, CLI agents)

### Five Core Communication Patterns

1. **Task Dispatch**: L1 → L2/L3
2. **Cross-Project Requests**: L2 ↔ L2 (negotiated)
3. **P2P Negotiation**: L2 ↔ L2 (semaphore-based)
4. **Status & Escalation**: L2 → L1
5. **Broadcasts**: Civilization-wide events

### Global Resource Management

- Per-project quotas (CPU %, memory)
- Load balancing with locality preference
- Backpressure when overloaded
- Resource borrowing between projects

---

## 📬 Questions & Feedback

**For clarification on**:

- Architecture decisions → See [CIVILIZATION_ARCHITECTURE_SUMMARY.md](./CIVILIZATION_ARCHITECTURE_SUMMARY.md) § Key Decisions
- Agent identity → See [AGENT_IDENTITY_AND_DISCOVERY.md](./AGENT_IDENTITY_AND_DISCOVERY.md)
- Communication protocols → See [CROSS_PROJECT_COORDINATION_PATTERNS.md](./CROSS_PROJECT_COORDINATION_PATTERNS.md)
- Resource management → See [CIVILIZATION_SCALE_PERFORMANCE.md](./CIVILIZATION_SCALE_PERFORMANCE.md)
- Implementation → See [MULTI_TENANT_CONTROLLER_IMPLEMENTATION_PLAN.md](./MULTI_TENANT_CONTROLLER_IMPLEMENTATION_PLAN.md)

---

**Status**: Ready for Review & Implementation
**Created**: 2026-02-19
**Version**: 1.0
