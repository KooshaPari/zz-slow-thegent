# Swarm Memory & Multi-Agent Coordination (WP-1006)

This document explores advanced patterns for multi-agent coordination within the `thegent` platform, focusing on **Shared Memory** and **Decentralized Coordination**.

## 1. Blackboard Architecture (Centralized Shared Memory)

`thegent` uses Redis as a **Blackboard** where agents can read and write shared state.

- **The Blackboard**: A common data space where agents post "findings," "hypotheses," and "partial results."
- **Knowledge Sources**: Specialized agents (e.g., `researcher`, `coder`, `tester`) that monitor the blackboard for tasks they can handle.
- **Controller**: The `thegent` orchestrator that manages access to the blackboard and coordinates agent activity.

## 2. Stigmergy (Environment-Mediated Coordination)

Inspired by social insects (e.g., ants), **Stigmergy** allows agents to communicate indirectly by modifying the environment.

- **Pheromone Trails**: Agents leave "traces" in the **Unified Work Stream** (`WORK_STREAM.md`).
- **Feedback Loops**: A high concentration of "traces" (e.g., many related research seeds) triggers the **Gardener** to spawn an **Incorporator** agent to formalize the work.
- **Decentralization**: No single agent is "in charge" of the swarm; behavior emerges from local interactions with the environment (the work stream).

## 3. Distributed State Patterns in Redis

To support swarms at scale, `thegent` employs the following Redis patterns:

### 3.1 Pub/Sub for Real-Time Sync

- Agents subscribe to `thegent:runs:{run_id}:events`.
- When an agent completes a task, it publishes an event, triggering downstream agents in the DAG.

### 3.2 Redis Streams for the Shared Log

- A persistent, append-only log of all agent actions.
- Enables **Consumer Groups**: Multiple instances of the same agent type can process the work stream in parallel without duplication.

### 3.3 Redlock for Distributed Mutual Exclusion

- Used for atomic updates to the canonical `WORK_STREAM.md` and critical `RunMeta` snapshots.

## 4. Conflict Resolution (Majority Vote & Confidence Weighting)

When multiple agents propose different solutions:

1. **Majority Vote**: The simplest resolution.
2. **Confidence Weighting**: The solution with the highest `Adjusted_Trust_Score` wins.
3. **Consensus DAG**: If agents disagree, a `Reviewer` node is added to the DAG to arbitrate.

## 5. Memory Sharing Patterns

### 5.1 Shared Memory Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       SHARED MEMORY ARCHITECTURE                            │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────────────┐
    │                      AGENT LAYER                                      │
    │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐ │
    │  │ Agent A │  │ Agent B │  │ Agent C │  │ Agent D │  │ Agent E │ │
    │  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘ │
    └───────┼───────────┼───────────┼───────────┼───────────┼──────────┘
            │           │           │           │           │
            │           │           │           │           │
            └───────────┴───────────┴───────────┴──────────┘
                        │           │           │
                        ▼           ▼           ▼
    ┌──────────────────────────────────────────────────────────────────────┐
    │                    MEMORY COORDINATION LAYER                          │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐  │
    │  │  Blackboard │  │   Pheromone │  │  Session    │  │  Conflict │  │
    │  │  (Redis)    │  │   Trails    │  │   Context   │  │  Resolver │  │
    │  │             │  │ (WORK_      │  │             │  │           │  │
    │  │             │  │  STREAM)    │  │             │  │           │  │
    │  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘  │
    └──────────────────────────────────────────────────────────────────────┘
```

### 5.2 Memory Sharing Patterns Matrix

| Pattern              | Type         | Consistency | Latency | Use Case                 |
| -------------------- | ------------ | ----------- | ------- | ------------------------ |
| **Blackboard**       | Shared state | Strong      | Low     | Centralized findings     |
| **Pheromone Trails** | Indirect     | Eventual    | Medium  | Work stream coordination |
| **Session Context**  | Private      | Strong      | Zero    | Per-agent state          |
| **Event Streaming**  | Pub/Sub      | Eventual    | Low     | Real-time sync           |
| **Redis Streams**    | Log          | Eventual    | Low     | Audit trail, replay      |
| **Redlock**          | Mutex        | Strong      | Medium  | Atomic updates           |

### 5.3 Data Flow: Agent → Blackboard → Other Agents

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BLACKBOARD DATA FLOW PATTERN                              │
└─────────────────────────────────────────────────────────────────────────────┘

    1. AGENT ACTION
    ┌─────────────┐
    │   Agent     │  Writes "finding_001": {"type": "research",
    │  discovers  │                      "content": "...",
    │   info      │                      "confidence": 0.85}
    └──────┬──────┘
           │ Redis SET
           ▼
    2. BLACKBOARD UPDATE
    ┌─────────────────────────────────────┐
    │  thegent:blackboard:{session_id}    │
    │  HMSET finding_001 content ...     │
    │  SADD session_findings finding_001 │
    └─────────────────┬───────────────────┘
                      │ Pub/Sub publish
                      ▼
    3. NOTIFICATION
    ┌─────────────────────────────────────┐
    │  thegent:runs:{run_id}:events      │
    │  PUBLISH "finding_added" {id}      │
    └─────────────────┬───────────────────┘
                      │
         ┌────────────┼────────────┐
         ▼            ▼            ▼
    ┌─────────┐  ┌─────────┐  ┌─────────┐
    │ Agent A │  │ Agent B │  │ Agent C │  ← Subscribers
    │ reads   │  │ reads   │  │ ignores │
    │ and     │  │ and     │  │ (low    │
    │ reacts  │  │ reacts  │  │ conf)   │
    └─────────┘  └─────────┘  └─────────┘
```

### 5.4 Stigmergy Implementation: Pheromone Trails

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    STIGMERGY: PHEROMONE TRAIL IMPLEMENTATION                 │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────────────┐
    │                    WORK_STREAM AS PHEROMONE FIELD                      │
    └──────────────────────────────────────────────────────────────────────┘

    Agent Action: "leave trace"
    ──────────────────────────
    ┌─────────────────┐
    │ User submits    │
    │ research seed   │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────────────────────────────┐
    │ APPEND to WORK_STREAM.md                 │
    │ - Timestamp: 2026-02-17T10:00:00Z      │
    │ - Type: research_seed                   │
    │ - Intensity: 1.0                        │
    │ - Tags: [swarm, memory, coordination]   │
    └─────────────────┬───────────────────────┘
                      │
                      ▼
    ┌─────────────────────────────────────────┐
    │ GARDENER MONITORS "pheromone intensity"  │
    │ ∑ intensity by tag > threshold?         │
    └─────────────────┬───────────────────────┘
                      │
         ┌────────────┼────────────┐
         │ YES        │            │ NO
         ▼            │            ▼
    ┌─────────────┐  │    ┌─────────────────┐
    │ Spawn       │  │    │ Continue         │
    │ Incorporator│  │    │ monitoring       │
    │ Agent       │  │    │                  │
    └─────────────┘  │    └─────────────────┘
                     │
                     ▼
    ┌─────────────────────────────────────────┐
    │ Incorporator formalizes:                 │
    │ - Research seed → FR                   │
    │ - Tags → FR categories                  │
    │ - Intensity → Priority                 │
    └─────────────────────────────────────────┘
```

### 5.5 Conflict Resolution Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CONFLICT RESOLUTION WORKFLOW                               │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────────────┐
    │                      CONFLICT DETECTED                                │
    │  Multiple agents propose different solutions for same problem        │
    └──────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    ┌──────────────────────────────────────────────────────────────────────┐
    │  1. COLLECT PROPOSALS                                               │
    │  ┌─────────────────────────────────────────────────────────────┐    │
    │  │ Agent A: "Solution A" (confidence: 0.82)                  │    │
    │  │ Agent B: "Solution B" (confidence: 0.76)                  │    │
    │  │ Agent C: "Solution A" (confidence: 0.91)                  │    │
    │  └─────────────────────────────────────────────────────────────┘    │
    └──────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    ┌──────────────────────────────────────────────────────────────────────┐
    │  2. APPLY RESOLUTION STRATEGY                                       │
    │  ┌─────────────────────────────────────────────────────────────┐    │
    │  │ Case: Majority vote (Solution A wins 2-1)                  │    │
    │  │ OR Case: Confidence weighting (Agent C highest)             │    │
    │  │ OR Case: Consensus DAG (add Reviewer node)                  │    │
    │  └─────────────────────────────────────────────────────────────┘    │
    └──────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    ┌──────────────────────────────────────────────────────────────────────┐
    │  3. RECORD OUTCOME                                                  │
    │  - Write to BLACKBOARD: resolution                                   │
    │  - Emit event: "conflict_resolved"                                  │
    │  - Update WORK_STREAM: mark as resolved                            │
    └──────────────────────────────────────────────────────────────────────┘
```

---

## 6. Cross-References

| Doc                                                                                                          | Relevance                   |
| ------------------------------------------------------------------------------------------------------------ | --------------------------- |
| [PHASE_5_SCALE_ROBUSTNESS_DEPTH.md](./PHASE_5_SCALE_ROBUSTNESS_DEPTH.md)                                     | Redis, adaptive concurrency |
| [UNIFIED_WORK_STREAM_DESIGN.md](./UNIFIED_WORK_STREAM_DESIGN.md)                                             | Work stream specification   |
| [SWARM_PROCESS_AUTOMATION_DEEP_RESEARCH.md](../research/SWARM_PROCESS_AUTOMATION_DEEP_RESEARCH.md)           | Process automation          |
| [SWARM_OPTIMIZATION_SCHEDULING_DEEP_RESEARCH.md](../research/SWARM_OPTIMIZATION_SCHEDULING_DEEP_RESEARCH.md) | Scheduling theory           |

---

_Cross-ref: [PHASE_5_SCALE_ROBUSTNESS_DEPTH.md](./PHASE_5_SCALE_ROBUSTNESS_DEPTH.md) | [UNIFIED_WORK_STREAM_DESIGN.md](./UNIFIED_WORK_STREAM_DESIGN.md)_

---

## EXTENSION_SUMMARY

**Extended on**: 2026-02-17
**Extensions added**: Memory sharing patterns (§5)

| Section | Added Content                                                                                                    |
| ------- | ---------------------------------------------------------------------------------------------------------------- |
| §5.1    | Shared Memory Architecture diagram (Agent layer → Coordination layer)                                            |
| §5.2    | Memory Sharing Patterns Matrix (Blackboard, Pheromone, Session Context, Event Streaming, Redis Streams, Redlock) |
| §5.3    | Blackboard Data Flow Pattern (Agent → Redis SET → Pub/Sub → Other Agents)                                        |
| §5.4    | Stigmergy Implementation: Pheromone Trails (WORK_STREAM as pheromone field)                                      |
| §5.5    | Conflict Resolution Workflow (Collect proposals → Apply strategy → Record outcome)                               |
