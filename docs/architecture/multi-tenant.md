# Multi-Tenant Cross-Project Agent Civilization Architecture

**Status**: Architecture Design v1.0
**Date**: 2026-02-19
**Scope**: 5-20 concurrent L1 agents across multiple projects with cross-project coordination
**Target**: Production deployment supporting heterogeneous agent types (Claude Code, Cursor, CLI agents)

---

## Executive Summary

The **Agent Civilization Framework** enables coordinated execution of 5-20 concurrent agent teams across multiple projects with:

- **Unified identity system** for all agents (L1/L2/L3) across all projects
- **Global work orchestration** with cross-project dependencies
- **Civilization-scale resource management** (shared CPU/memory/network pools)
- **Peer-to-peer coordination** for horizontally distributed agent networks
- **Hierarchical + peer relationships** supporting both traditional supervision and lateral collaboration
- **Backwards compatibility** with existing single-project swarms

**Key insight**: The civilization is a **distributed system with eventual consistency**, not a centralized orchestrator. Agents are sovereign; the framework provides coordination protocols, not control.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CIVILIZATION CONTROL PLANE                           │
│  (Shared services: Registry, Work Orchestrator, Resource Manager, Event Bus) │
└─────────────────────────────────────────────────────────────────────────────┘
                            ▲           ▲           ▲
                            │           │           │
                            │ (discovery, coordination, backpressure)
                            │           │           │
        ┌───────────────────┴───────────┴───────────┴────────────────┐
        │                                                              │
┌───────▼─────────┐  ┌───────────────┐  ┌──────────────────────────┐
│   PROJECT: KUSH │  │ PROJECT: ATOMS │  │  PROJECT: THEGENT       │
├─────────────────┤  ├───────────────┤  ├──────────────────────────┤
│ L1: Claude Code │  │ L1: Claude    │  │ L1: Claude Code          │
│  ├─ L2: Runner  │  │  ├─ L2: Plan  │  │  ├─ L2: Researcher       │
│  ├─ L2: Coder   │  │  ├─ L2: Free  │  │  ├─ L2: Implementer      │
│  └─ L2: Tester  │  │  └─ L3: Cur01 │  │  ├─ L2: Reviewer         │
│                 │  │                 │  │  └─ L3: Cursor-01      │
│ L3: Cursor-1    │  └───────────────┘  └──────────────────────────┘
│ L3: Cursor-2    │
└─────────────────┘

              ▲
              │ async messaging
              │ resource requests
              │ task claims
              │
┌─────────────▼────────────────────────────────────────────────────┐
│              CIVILIZATION STATE LAYER (Git + MCP)                 │
│  - Global registry (agents, projects, capabilities)               │
│  - Work stream (canonical single source of truth for all tasks)   │
│  - State files (per-project + civilization-wide metrics)          │
│  - Event log (audit trail of all agent actions)                   │
└───────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Civilization Control Plane

#### Agent Registry Service

- **Responsibility**: Golden source of truth for all agent identity, location, capabilities
- **Data**: Agent ID → metadata (project, tier, role, capabilities, availability, endpoint)
- **Implementation**:
  - Primary: Git-based (`.claude/civilization/registry.json`) committed frequently
  - Cache: In-memory + MCP endpoint for fast lookup
  - Sync: Event-driven invalidation + periodic git pull
- **Queries**:
  - Find all L2 agents in project X
  - Find all agents with capability "research"
  - Find available agents (not blocked, not overloaded)
  - Reverse lookup: agent_id → project:location

#### Work Orchestrator

- **Responsibility**: Maintain global work stream with cross-project dependencies, dispatch tasks to agents
- **Data**: Unified work stream (git-based `WORK_STREAM.md`) with metadata:
  - Task ID, description, status (PENDING/CLAIMED/BLOCKED/COMPLETED)
  - Claiming agent, assigned project(s)
  - Dependencies (blocks/blocked_by across projects)
  - Priority, deadline, estimated effort
  - Resource requirements (CPU, memory)
- **Operations**:
  - Claim: Agent claims work → record in WORK_STREAM, push to git
  - Dispatch: Find best agent for task (specialization, load, locality)
  - Unblock: When task X completes, notify waiting agents for dependent tasks
  - Escalate: If task is stuck, promote to higher tier or cross-project help
- **Implementation**: Coordinated via git + async event loop (no central server)

#### Resource Manager (Civilization-Scale)

- **Responsibility**: Fair allocation of civilization-wide compute/memory/network resources
- **Data**:
  - Global resource pool: {cpu_cores: N, memory_gb: M, network_bps: B}
  - Per-project quota: {project_id: {cpu: %, memory: %, network: %}}
  - Per-agent usage: {agent_id: {cpu_current: %, memory_current: %, tasks_active: N}}
- **Operations**:
  - Allocate: Check if agent can claim task (within quota, within available resources)
  - Deallocate: Release resources when agent completes/fails
  - Rebalance: Move work from overloaded to idle agents
  - Borrow: Allow project X to borrow from project Y's quota temporarily
- **Implementation**: Lazy evaluation + periodic reconciliation (no locks)

#### Event Bus

- **Responsibility**: Async pub-sub for agent lifecycle events
- **Events**:
  - `agent.started`, `agent.stopped`, `agent.failed`
  - `task.claimed`, `task.completed`, `task.failed`, `task.blocked`
  - `resource.threshold_breach` (CPU > 90%, memory > 85%)
  - `civilization.deadlock_detected`, `civilization.cascade_failure`
- **Implementation**: Git-based event log + MCP subscriptions (agents subscribe to relevant topics)
- **Durability**: Event log persisted in git; agents query on startup to recover

### 2. Project-Scoped Layer

#### Work Stream (Per-Project + Global)

- **Global stream**: `WORK_STREAM.md` in shared home (e.g., `~/.claude/civilization/WORK_STREAM.md`)
- **Per-project streams**: `docs/reference/WORK_STREAM.md` in each project (local view)
- **Sync strategy**:
  - L1 agents pull global stream, merge with project-specific items
  - Tasks can have `scope: [kush, atoms]` for cross-project visibility
  - Conflict resolution: Last-write-wins with timestamp + agent_id

#### Task State Machine

```
PENDING (unassigned, no blockers)
  ↓ claim
CLAIMED (assigned to agent, agent_id recorded)
  ├─ progress (agent is actively working)
  ├─→ BLOCKED (waiting on cross-project dependency)
  │    ↓ (dependency completes, broadcast event)
  │    → PENDING/CLAIMED (attempt continue)
  ├─→ FAILED (agent crashed, task available for retry)
  │    ↓ (backoff, re-claim)
  │    → PENDING
  └─→ COMPLETED (task done, broadcast unblock to dependents)
```

#### Per-Project Metadata

- Available agents (L2/L3 within project)
- Agent capabilities and current load
- Local resource quotas and usage
- Dependencies on external projects

---

## Identity & Discovery System

### Agent ID Scheme

**Format**: `{project}:{uuid}:L{1-3}:{role-slug}`

**Examples**:

```
kush:8d3f2c1a-5e7b-4d2f-9e1c-6a8b3f2d1e0a:L1:claude-code
kush:a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d:L2:runner-1
kush:f9e8d7c6-b5a4-3c2b-1a09-8f7e6d5c4b3a:L2:researcher-1
atoms:7e8f9a0b-1c2d-3e4f-5a6b-7c8d-9e0f:L1:claude
atoms:3d4e5f6a-7b8c-9d0e-1f2a-3b4c-5d6e:L3:cursor-01

thegent:5c6d7e8f-9a0b-1c2d-3e4f-5a6b-7c8d:L2:reviewer-1
```

**Uniqueness Constraints**:

- UUID generated at agent startup, persisted in agent's home
- (project, role-slug) may not be unique, but (project, uuid) is globally unique
- Example: Multiple L2:runner agents in same project have different UUIDs

### Global Registry Schema

**Location**: `~/.claude/civilization/registry.json` (shared across all projects)

```json
{
  "metadata": {
    "version": "1.0",
    "last_updated": "2026-02-19T14:30:00Z",
    "civilization_id": "global-001"
  },
  "agents": [
    {
      "id": "kush:8d3f2c1a-5e7b-4d2f-9e1c-6a8b3f2d1e0a:L1:claude-code",
      "project": "kush",
      "tier": "L1",
      "role": "claude-code",
      "uuid": "8d3f2c1a-5e7b-4d2f-9e1c-6a8b3f2d1e0a",
      "capabilities": [
        "read_files",
        "write_files",
        "run_bash",
        "delegate_to_l2",
        "researcher",
        "planner",
        "implementer"
      ],
      "status": "active",
      "endpoints": {
        "mcp": "localhost:3847",
        "http": "http://localhost:8317",
        "git_home": "/Users/kooshapari/temp-PRODVERCEL/485/kush"
      },
      "resources": {
        "cpu_quota_percent": 40,
        "memory_quota_gb": 8,
        "max_concurrent_l2": 5
      },
      "current_load": {
        "l2_active": 2,
        "tasks_claimed": 3,
        "cpu_usage_percent": 25,
        "memory_usage_mb": 1500
      },
      "last_heartbeat": "2026-02-19T14:29:55Z",
      "parent_id": null
    },
    {
      "id": "kush:a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d:L2:runner-1",
      "project": "kush",
      "tier": "L2",
      "role": "runner-1",
      "uuid": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
      "parent_id": "kush:8d3f2c1a-5e7b-4d2f-9e1c-6a8b3f2d1e0a:L1:claude-code",
      "capabilities": [
        "read_files",
        "write_files",
        "run_tests",
        "delegate_to_l3"
      ],
      "status": "active",
      "endpoints": {
        "mcp": "localhost:3847",
        "message_queue": "~/.claude/civilization/queues/l2_runner_1.mq"
      },
      "resources": {
        "cpu_quota_percent": 15,
        "memory_quota_gb": 3,
        "max_concurrent_tasks": 2
      },
      "current_load": {
        "tasks_active": 1,
        "cpu_usage_percent": 10,
        "memory_usage_mb": 450
      },
      "last_heartbeat": "2026-02-19T14:29:58Z"
    },
    {
      "id": "atoms:7e8f9a0b-1c2d-3e4f-5a6b-7c8d-9e0f:L1:claude",
      "project": "atoms",
      "tier": "L1",
      "role": "claude",
      "uuid": "7e8f9a0b-1c2d-3e4f-5a6b-7c8d-9e0f",
      "capabilities": ["read_files", "delegate_to_l2"],
      "status": "active",
      "endpoints": {
        "mcp": "localhost:3848"
      },
      "resources": {
        "cpu_quota_percent": 35,
        "memory_quota_gb": 6
      },
      "last_heartbeat": "2026-02-19T14:29:56Z",
      "parent_id": null
    },
    {
      "id": "atoms:3d4e5f6a-7b8c-9d0e-1f2a-3b4c-5d6e:L3:cursor-01",
      "project": "atoms",
      "tier": "L3",
      "role": "cursor-01",
      "uuid": "3d4e5f6a-7b8c-9d0e-1f2a-3b4c-5d6e",
      "parent_id": "atoms:7e8f9a0b-1c2d-3e4f-5a6b-7c8d-9e0f:L1:claude",
      "capabilities": ["read_files", "write_files", "run_bash"],
      "status": "active",
      "endpoints": {
        "mcp": "localhost:3849",
        "message_queue": "~/.claude/civilization/queues/l3_cursor_01.mq"
      },
      "current_load": {
        "tasks_active": 0
      },
      "last_heartbeat": "2026-02-19T14:29:52Z"
    }
  ],
  "projects": [
    {
      "name": "kush",
      "resource_quota": {
        "cpu_percent": 40,
        "memory_gb": 8,
        "network_bps": 10000000
      },
      "current_usage": {
        "cpu_percent": 28,
        "memory_gb": 2.3,
        "network_bps": 1200000
      }
    },
    {
      "name": "atoms",
      "resource_quota": {
        "cpu_percent": 35,
        "memory_gb": 6,
        "network_bps": 8000000
      },
      "current_usage": {
        "cpu_percent": 15,
        "memory_gb": 1.8,
        "network_bps": 800000
      }
    },
    {
      "name": "thegent",
      "resource_quota": {
        "cpu_percent": 25,
        "memory_gb": 5,
        "network_bps": 6000000
      },
      "current_usage": {
        "cpu_percent": 8,
        "memory_gb": 0.9,
        "network_bps": 400000
      }
    }
  ]
}
```

### Service Discovery Mechanisms

**Option 1: File-Based Registry (Recommended for Simplicity)**

- **Location**: `~/.claude/civilization/registry.json`
- **Discovery**: Agents read file at startup + subscribe to file change events (via watchdog)
- **Latency**: ~100ms (git pull + file read)
- **Consistency**: Eventually consistent (agents sync on push/pull)
- **Scalability**: Works well for 5-20 agents; beyond 50, consider sharding

**Option 2: MCP Service Registry (Recommended for Real-Time)**

- **Architecture**: Dedicated MCP server exposing registry as resource + tools
- **Discovery**: Agents query MCP endpoint at startup, cache locally
- **Latency**: <50ms (local gRPC/MCP call)
- **Consistency**: Strong (all agents see same view immediately)
- **Implementation**: FastMCP service with `thegent://civilization/registry` resource
- **Fallback**: File-based if MCP unavailable

**Option 3: Gossip Protocol (Recommended for Resilience)**

- **Architecture**: Agents periodically exchange metadata with random peers
- **Discovery**: P2P heartbeats + periodic full reconciliation
- **Latency**: 1-5s (bounded gossip rounds)
- **Consistency**: Eventually consistent with high probability
- **Implementation**: Each agent broadcasts heartbeat via message queue
- **Use Case**: If control plane is unreliable or offline

**Recommendation**: Hybrid approach:

- Primary: MCP service (Option 2) for fast updates
- Secondary: File-based (Option 1) as fallback
- Tertiary: Gossip (Option 3) for P2P validation

### Address Resolution Protocol

```
query(agent_id="atoms:7e8f9a0b-...:L1:claude")
  ↓
registry.lookup(agent_id)
  ↓
{
  "endpoints": {
    "mcp": "localhost:3848",
    "http": "http://localhost:8317",
    "git_home": "/path/to/atoms"
  }
}
  ↓
dial(endpoint, timeout=5s)
  ├─ if success: cache locally, set TTL=30s
  └─ if failure: try next endpoint, mark agent as unavailable
```

**Endpoint Priority** (try in order):

1. MCP (lowest latency, preferred for task dispatch)
2. HTTP (fallback, if MCP unavailable)
3. Git home (fallback, use shared state via git)
4. Message queue (async communication, no real-time requirement)

---

## Communication Protocols

### Pattern 1: Task Dispatch (L1 → L2/L3)

**Synchronous path (for urgent tasks):**

```
L1 creates task in WORK_STREAM.md
  ↓
L1 calls `claim_task(task_id, agent_id)`
  ├─ Registry lookup: agent_id → endpoints
  ├─ Connect to agent MCP endpoint
  └─ Send message: {task_id, prompt, deadline, dependencies}
       ↓
     L2/L3 receives dispatch
       ├─ Reserve resources (CPU, memory)
       ├─ Ack to L1: {status: "CLAIMED", start_time}
       └─ Begin work
       ↓
     L2/L3 completes, sends: {status: "COMPLETED", output, time_spent}
  ↓
L1 receives completion, updates WORK_STREAM.md, broadcasts unblock events
```

**Asynchronous path (for bulk dispatch):**

```
L1 writes task to WORK_STREAM.md + message queue (~/.claude/civilization/queues/l2_runner_1.mq)
  ↓
L2 polls queue periodically (every 1s), finds new task
  ├─ Reads queue entry
  ├─ Reserves resources
  └─ Updates WORK_STREAM: status="CLAIMED", claimed_by="kush:a1b2....:L2:runner-1"
       ↓ (git push)
  ↓
L2 works on task
  ├─ Sends progress events to queue
  ├─ Updates WORK_STREAM if blocked (cross-project dependency)
  └─ On completion, updates WORK_STREAM: status="COMPLETED"
       ↓ (git push triggers event broadcast)
```

**Message Schema:**

```json
{
  "type": "task_dispatch",
  "task_id": "research-library-http",
  "source_agent_id": "kush:8d3f2c1a-5e7b-4d2f-9e1c-6a8b3f2d1e0a:L1:claude-code",
  "target_agent_id": "kush:a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d:L2:runner-1",
  "prompt": "Research and recommend HTTP libraries...",
  "context": {
    "project": "kush",
    "deadline": "2026-02-19T16:00:00Z",
    "dependencies": ["research-api-design"]
  },
  "resource_request": {
    "cpu_percent": 20,
    "memory_mb": 512
  },
  "timeout_seconds": 600
}
```

### Pattern 2: Cross-Project Coordination (L2 ↔ L2)

**Scenario: L2 in Project A needs help from L2 in Project B**

```
L2-A (kush:runner-1) realizes it needs Project B work
  ↓ looks up agents in Project B
  ├─ Registry query: agents(project="atoms", tier="L2", capability="research")
  └─ Finds: [atoms:...:L2:researcher-1] (currently idle)
       ↓
  L2-A broadcasts request: {request_id, description, deadline, reward}
  (via message queue + event bus)
       ↓
  L2-B sees request, evaluates:
    ├─ Do I have capacity? (2 active tasks, max 3, so yes)
    ├─ Is this in my specialization? (researcher, yes)
    ├─ What's the deadline? (3 hours, reasonable)
    └─ Decide: ACCEPT or DEFER
       ↓
  L2-B responds: {request_id, status="ACCEPTED", start_time, expected_completion}
       ↓
  L2-A receives, creates cross-project task:
    - Task ID: "atoms:research-library-async"
    - Assigned to: atoms:...:L2:researcher-1
    - Blocks: kush:runner-1's work
    - Deadline: shared
       ↓
  L2-B works on task, updates shared WORK_STREAM.md
       ↓
  On completion:
    - L2-B updates WORK_STREAM: status="COMPLETED", output_location="/atoms/docs/research/..."
    - Event broadcast: "task.completed:atoms:research-library-async"
    - L2-A's event bus wakes up L2-A (unblock event)
    - L2-A continues with borrowed results
```

**Message Schema (Cross-Project Request):**

```json
{
  "type": "cross_project_request",
  "request_id": "atoms:research-library-async",
  "source_agent_id": "kush:a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d:L2:runner-1",
  "source_project": "kush",
  "target_project": "atoms",
  "target_capabilities": ["research"],
  "description": "Research async libraries for project kush",
  "deadline": "2026-02-19T17:00:00Z",
  "resource_commitment": {
    "cpu_percent": 25,
    "memory_mb": 1024,
    "duration_minutes": 120
  },
  "incentives": {
    "priority_boost": 2,
    "cross_project_credit": true
  }
}
```

### Pattern 3: Peer-to-Peer Negotiation (L2 ↔ L2 same project)

**Scenario: Two L2 agents sharing a resource (rate-limited API key)**

```
Runner-1 and Runner-2 both need to hit the same API
  ↓ each checks local resource semaphore
  ├─ Semaphore location: ~/.claude/civilization/semaphores/{project}/{resource_id}
  ├─ File contains: {holder_id, lease_until, request_queue}
  ├─ Lock mechanism: atomic file write (write-lock via git push)
  └─ Wait list: append to request_queue, poll until available
       ↓
  Runner-1 acquires lock, updates file:
    {holder_id: "runner-1", lease_until: T+60s, queue: ["runner-2"]}
       ↓
  Runner-1 uses API with throttling, releases lock early if done
       ↓
  Runner-2 acquires lock when runner-1 releases
```

**Message Schema (P2P Negotiation):**

```json
{
  "type": "peer_negotiation",
  "source_agent_id": "kush:a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d:L2:runner-1",
  "target_agent_id": "kush:f9e8d7c6-b5a4-3c2b-1a09-8f7e6d5c4b3a:L2:researcher-1",
  "resource_id": "github-api-key",
  "operation": "request_lock",
  "deadline": "2026-02-19T14:45:00Z",
  "priority": 5
}
```

### Pattern 4: Status & Escalation (L2/L3 → L1)

**L2 agent sends status update to L1 parent:**

```
L2 periodically (every 5 min) sends:
{
  "type": "status_update",
  "source_agent_id": "kush:a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d:L2:runner-1",
  "target_agent_id": "kush:8d3f2c1a-5e7b-4d2f-9e1c-6a8b3f2d1e0a:L1:claude-code",
  "timestamp": "2026-02-19T14:35:00Z",
  "metrics": {
    "tasks_completed_session": 3,
    "cpu_usage_percent": 12,
    "memory_usage_mb": 450,
    "tasks_active": 1,
    "queue_depth": 2
  },
  "current_task": {
    "task_id": "research-library-http",
    "progress_percent": 65,
    "started": "2026-02-19T14:30:00Z",
    "estimated_completion": "2026-02-19T14:50:00Z"
  },
  "alerts": []
}
```

**L2 escalates if blocked:**

```
L2 waiting on cross-project task (atoms:research-library-async)
  └─ After 30 min (or deadline - 30 min), sends escalation:
{
  "type": "escalation",
  "source_agent_id": "kush:a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d:L2:runner-1",
  "target_agent_id": "kush:8d3f2c1a-5e7b-4d2f-9e1c-6a8b3f2d1e0a:L1:claude-code",
  "reason": "BLOCKED_ON_EXTERNAL_TASK",
  "blocking_task_id": "atoms:research-library-async",
  "blocking_agent_id": "atoms:7e8f9a0b-1c2d-3e4f-5a6b-7c8d-9e0f:L1:claude",
  "time_blocked_minutes": 32,
  "deadline_minutes": 28,
  "suggested_actions": [
    "check_status_atoms_research_library_async",
    "allocate_additional_resources_atoms",
    "find_alternative_implementation"
  ]
}
```

### Pattern 5: Civilization-Wide Broadcast (Events)

**Event: Resource threshold breach (CPU > 90%)**

```
Resource Manager detects civilization CPU usage = 92%
  ├─ Publishes event to event bus
  └─ All agents subscribe to "resource.threshold_breach" receive:
{
  "type": "resource_threshold_breach",
  "timestamp": "2026-02-19T14:36:00Z",
  "resource": "cpu",
  "threshold": 90,
  "current_value": 92,
  "civilization_metrics": {
    "cpu_usage_percent": 92,
    "memory_usage_percent": 78,
    "network_usage_percent": 45
  },
  "recommended_actions": [
    "defer_non_urgent_tasks",
    "request_borrowed_quota_from_idle_projects",
    "increase_civilization_quota_if_possible"
  ],
  "affected_projects": ["kush", "atoms"]
}
```

**Event: Deadlock Detected**

```
Deadlock detector finds:
  Project X task A → blocked on Project Y task B
  Project Y task B → blocked on Project X task C
  Project X task C → waiting for resources held by task A (cycle!)
       ↓
Publishes: {
  "type": "civilization.deadlock_detected",
  "cycle": [
    "kush:task-1 (blocked on atoms:task-2)",
    "atoms:task-2 (blocked on kush:task-3)",
    "kush:task-3 (waiting on L2 resources held by kush:task-1)"
  ],
  "recommended_resolution": "kill_task_kush:task-1_and_retry"
}
```

---

## Error Handling & Timeouts

### Task Timeout Policy

| Scenario                 | Timeout                     | Action                                |
| ------------------------ | --------------------------- | ------------------------------------- |
| L2 task (claimed)        | 30 min (default)            | Escalate to L1, offer retry           |
| Cross-project dependency | deadline - 30 min (earlier) | Escalate, find alternative            |
| L3 task (long-running)   | 2 hours (default)           | Send heartbeat check, allow extension |
| Resource allocation wait | 5 min                       | Reject task, offer queue position     |

### Retry Logic

```
task_dispatch(task_id, agent_id, retry_count=0)
  ├─ if retry_count > 3: {status: FAILED, reason: "max_retries"}
  └─ try:
      ├─ dial(agent_endpoint, timeout=5s)
      ├─ send(task_dispatch_message)
      └─ wait(response, timeout=task_timeout)
         ↓
         ├─ if timeout:
         │   ├─ backoff: min(2^retry_count * 5s, 60s)
         │   └─ retry(task_id, agent_id, retry_count+1)
         ├─ if connection_error:
         │   └─ mark agent unavailable, find alternative
         ├─ if agent_declined (overloaded):
         │   ├─ update resource_manager(agent_id, overloaded=true)
         │   └─ find_alternative_agent(task_id)
         └─ if success: done
```

### Deadlock Detection & Prevention

**Detection** (runs every 60s):

```
for each cross_project_task T with deadline D:
  ├─ if time_blocked(T) > D - 30min:
  │   └─ check for cycle via transitive blocking
  │       ├─ if cycle found: DEADLOCK
  │       └─ if no cycle: escalate (normal blocking)
  └─ if time_active(T) > T.timeout:
      └─ TIMEOUT (not deadlock)
```

**Prevention** (configured in WORK_STREAM.md):

```
{
  "task_id": "kush:task-1",
  "max_blocking_time_minutes": 60,
  "cycle_prevention": {
    "disable_cross_project_blocks": false,
    "max_transitive_depth": 5
  }
}
```

---

## State Management & Consistency

### Source of Truth Hierarchy

| State          | Primary                                      | Cache                           | Sync Method                         |
| -------------- | -------------------------------------------- | ------------------------------- | ----------------------------------- |
| Agent registry | Git (`~/.claude/civilization/registry.json`) | MCP (in-mem), local agent state | git pull, MCP subscribe, gossip     |
| Work stream    | Git (`WORK_STREAM.md`)                       | In-agent memory                 | git pull/push, event broadcast      |
| Resource usage | Git (`resource_state.json`)                  | MCP (in-mem), per-agent         | periodic reconciliation (every 60s) |
| Event log      | Git (`event_log.ndjson`)                     | MCP stream                      | append-only, git push               |
| Task output    | Project-local filesystem                     | N/A                             | direct read from task agent         |

### Consistency Model: Eventual Consistency + CRDTs

**Why eventual consistency?**

- Cross-home-directory operations (cannot use centralized locks)
- Agent autonomy (agents decide independently when to sync)
- Offline tolerance (agents can work when git is unavailable)

**Conflict Resolution for WORK_STREAM.md:**

```
Agent A: updates task status → CLAIMED at T1 by agent A
Agent B: updates same task → CLAIMED at T1.5 by agent B

On merge:
  ├─ Last-write-wins: agent B's update (later timestamp)
  ├─ But mark conflict: {task_id, conflicted_at: T1.5, agents: [A, B]}
  └─ Alert L1: "Task claimed by B, but A had claimed first"
       ├─ L1 decides: (probably revoke B's claim, reassign)
       └─ Record in event log: {type: "claim_conflict_resolved"}
```

**CRDT Approach** (optional, for high-concurrency projects):

- Use YATA-style CRDTs for work stream
- Each agent maintains local version of WORK_STREAM
- Periodic 3-way merge: {local, git, remote}
- Result: deterministic convergence, no conflicts

### Recovery After Agent Failure

**Scenario: L2 runner-1 crashes mid-task**

```
L2 was working on task-1 (status="PROGRESS")
  ↓ (runner-1 heartbeat expires, missed 3 consecutive)
  ↓
L1 detects failure: {
  "type": "agent_failure",
  "agent_id": "kush:runner-1:L2",
  "tasks_in_progress": ["task-1"],
  "last_heartbeat": "2026-02-19T14:35:00Z"
}
  ├─ Options:
  │  ├─ Retry: Restart runner-1 via ProcessCompose, resume task-1
  │  ├─ Reassign: Find another agent, give them task-1, supply context
  │  └─ Fail: Mark task-1 FAILED, escalate to L1
  │
  └─ Preferred: Retry with backoff (runner-1 dead for 5s, restart)
      ├─ On restart, runner-1 reads WORK_STREAM.md, finds task-1 (status=PROGRESS)
      ├─ Resumes work with context:
      │  └─ Last known state: {output_dir, line_count, timestamp}
      └─ On completion: Updates WORK_STREAM status=COMPLETED
```

---

## Observability & Governance

### Civilization-Wide Metrics

**Location**: `~/.claude/civilization/metrics.json` (updated every 10s)

```json
{
  "timestamp": "2026-02-19T14:37:00Z",
  "civilization": {
    "total_agents": 9,
    "agents_active": 7,
    "agents_idle": 2,
    "resource_usage": {
      "cpu_percent": 28,
      "memory_gb": 4.1,
      "network_bps": 2400000
    },
    "work_metrics": {
      "tasks_pending": 5,
      "tasks_claimed": 8,
      "tasks_blocked": 2,
      "tasks_completed_today": 34,
      "avg_task_duration_minutes": 12.5
    },
    "cross_project_metrics": {
      "requests_active": 1,
      "requests_completed_today": 8,
      "avg_wait_time_minutes": 8.2
    }
  },
  "projects": [
    {
      "name": "kush",
      "agents": {
        "L1": 1,
        "L2": 3,
        "L3": 2
      },
      "resource_usage": {
        "cpu_percent": 28,
        "memory_gb": 2.3,
        "quota_remaining": {
          "cpu_percent": 12,
          "memory_gb": 5.7
        }
      },
      "work_metrics": {
        "tasks_claimed": 5,
        "tasks_blocked": 1,
        "blocked_on_external": ["atoms:research-library-async"]
      }
    }
  ],
  "alerts": [
    {
      "severity": "WARNING",
      "message": "Project kush CPU usage 28% approaching quota 40%"
    }
  ]
}
```

### Per-Project Status Dashboard

**Location**: `docs/reference/CIVILIZATION_STATUS.md` (per-project)

```markdown
# Civilization Status - Project KUSH

**Last Updated**: 2026-02-19 14:37 UTC

## Agents

| Agent ID     | Tier | Role        | Status | Load | Uptime | Last Heartbeat |
| ------------ | ---- | ----------- | ------ | ---- | ------ | -------------- |
| claude-code  | L1   | supervisor  | active | 40%  | 8h 23m | 14:36:58       |
| runner-1     | L2   | task_runner | active | 50%  | 2h 15m | 14:36:57       |
| researcher-1 | L2   | research    | idle   | 0%   | 5h 12m | 14:36:55       |
| cursor-1     | L3   | editor      | active | 20%  | 1h 30m | 14:36:52       |
| cursor-2     | L3   | editor      | active | 15%  | 45m    | 14:36:50       |

## Work Stream

- Pending: 2 tasks
- Claimed: 3 tasks (3 agents active)
- Blocked: 1 task (waiting on atoms:research-library-async)
- Completed today: 12 tasks

## Cross-Project Dependencies

| Task         | Blocked On               | Project | Status      | Wait Time |
| ------------ | ------------------------ | ------- | ----------- | --------- |
| feature-auth | atoms:research-async-lib | atoms   | IN_PROGRESS | 32 min    |

## Resource Usage

- CPU: 28% / 40% (quota: 12% remaining)
- Memory: 2.3 GB / 8 GB
- Network: 2.4 Mbps / 10 Mbps

## Alerts

- ⚠️ CPU approaching quota (12% remaining, 3 tasks queued)
- ⚠️ Task feature-auth blocked on external project (deadline 28 min)
```

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)

- [ ] Create agent identity scheme (ID format, UUID generation)
- [ ] Implement file-based registry (`~/.claude/civilization/registry.json`)
- [ ] Implement unified WORK_STREAM.md (git-based)
- [ ] Add task claim/complete operations
- [ ] Heartbeat mechanism (agents send periodic status)

### Phase 2: Single-Project Multi-Agent (Week 2-3)

- [ ] L1 → L2/L3 task dispatch (synchronous path)
- [ ] L2 ↔ L2 peer coordination (semaphore-based)
- [ ] Resource manager (per-project quotas)
- [ ] Task timeout + escalation

### Phase 3: Cross-Project Coordination (Week 3-4)

- [ ] MCP service registry (real-time updates)
- [ ] Cross-project task requests
- [ ] Cross-project dependency tracking
- [ ] Event bus (git-based + MCP)

### Phase 4: Observability & Governance (Week 4-5)

- [ ] Civilization metrics dashboard
- [ ] Event log (audit trail)
- [ ] Deadlock detection
- [ ] Agent failure recovery

### Phase 5: Resilience & Optimization (Week 5-6)

- [ ] Circuit breaker for unhealthy agents
- [ ] Resource borrowing (quota negotiation)
- [ ] Load balancing algorithm
- [ ] Gossip protocol (P2P fallback)

---

## Backwards Compatibility

**Single-project swarms remain unchanged:**

- Existing `WORK_STREAM.md` in project directory works as before
- New coordination layer is opt-in (agents can ignore global WORK_STREAM)
- Civilization features disabled if `~/.claude/civilization/` does not exist

**Migration path:**

1. Deploy coordination infrastructure (Phase 1-2)
2. Projects onboard individually (create registry entries, enable global WORK_STREAM)
3. Cross-project features activate once 2+ projects enabled

---

## Glossary

| Term                   | Definition                                                                 |
| ---------------------- | -------------------------------------------------------------------------- |
| **Civilization**       | The entire ecosystem of agents across all projects                         |
| **Control Plane**      | Shared services (registry, work orchestrator, resource manager, event bus) |
| **L1 Agent**           | Top-level agent (Claude Code, Cursor, etc.) that spawns L2/L3              |
| **L2 Agent**           | Sub-agent spawned by L1, executes work packages                            |
| **L3 Agent**           | Simulated agent (e.g., Cursor window), no internal task tool               |
| **Task**               | Unit of work (claim, execute, complete, or fail)                           |
| **Cross-Project Task** | Task assigned to agent in different project than requester                 |
| **WORK_STREAM.md**     | Unified work stream (global + per-project views)                           |
| **Registry**           | Source of truth for all agent identity, location, capabilities             |
| **Event Bus**          | Async pub-sub for lifecycle events                                         |
| **Resource Manager**   | Allocates CPU, memory, network across civilization                         |

---

## Questions for Implementation Review

1. **Consistency vs Performance**: Should we use git (eventual consistency, simple) or centralized backend (strong consistency, complex)?
2. **Agent Discovery**: MCP service registry + file fallback, or pure gossip protocol?
3. **Resource Enforcement**: Hard limits (reject tasks) or soft limits (queue with priority)?
4. **Failure Isolation**: Does one project's failure cascade to others, or is it contained?
5. **Cross-Project Security**: Should agents in Project A be able to read Project B's output? How to enforce?
