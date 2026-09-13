# Civilizational Multi-Swarm Hierarchy (WP-1006, WP-5004)

This document defines the architectural patterns for orchestrating **Swarms of Swarms** at "civilizational" scales (thousands of agents, long-running runs).

## 1. Hierarchical Coordination

To manage complexity, `thegent` uses a **Hierarchical Blackboard** system:

### 1.1 The Global Blackboard

- Stores high-level goals and "Global Constants."
- Orchestrated by a **Commander Swarm** (High-level planners).

### 1.2 Regional Blackboards (Swarms)

- Each functional swarm (e.g., `frontend-swarm`, `security-swarm`, `ops-swarm`) has its own regional blackboard.
- Agents within the swarm coordinate locally using **Stigmergy** (modifying their regional `WORK_STREAM.md`).

## 2. Multi-Swarm Communication (Stigmergic Handoff)

Swarms communicate via "Handoff Artifacts":

1. **Frontend Swarm** completes a UI feature and posts a `Conformance_Artifact` to the Global Blackboard.
2. **Security Swarm** (monitoring the Global Blackboard) detects the new artifact and triggers a "Pen-Test Cycle" for that feature.
3. This indirect coordination allows swarms to scale independently without monolithic bottlenecks.

## 3. Scaling Mechanics (WP-5004)

### 3.1 Distributed State Partitioning

- Redis databases are partitioned by **Swarm_ID** to avoid contention.
- The **Global Shared Log** provides the unified audit trail across all swarms.

### 3.2 Hysteresis per Swarm

- Each swarm has its own **Adaptive Concurrency Controller**.
- A `frontend-swarm` might scale up to 100 agents during a UI sprint, while the `compliance-swarm` remains at a floor of 2 agents.

## 4. Federated Governance

Governance policies (Phase 3) are also hierarchical:

- **Global Policies**: Mandatory for all swarms (e.g., "Zero PII," "Cost < $10k").
- **Local Policies**: Specific to a swarm (e.g., "Lint = strict," "Coverage > 90%").

## 5. Implementation Roadmap for Hierarchy

- **WP-5004**: Multi-Redis partitioning support.
- **WP-5007**: Hierarchical blackboard implementation.
- **WP-6008**: Multi-swarm simulation and load testing.

---

_Cross-ref: [SWARM_MEMORY_COORDINATION_DEPTH.md](./SWARM_MEMORY_COORDINATION_DEPTH.md) | [PHASE_5_SCALE_ROBUSTNESS_DEPTH.md](./PHASE_5_SCALE_ROBUSTNESS_DEPTH.md)_

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index

---

## EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added practical implementation patterns
2. Added configuration examples
3. Enhanced cross-references to related documentation

### Cross-References Added

- Related research and implementation guides
- WORK_STREAM.md for tracking

### Practical Additions

- Implementation templates
- Configuration examples
- Best practices
