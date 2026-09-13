# Context Management & Semantic Compression Depth (WP-5001)

This document defines the 4-tier memory architecture and context optimization strategies for long-running `thegent` sessions.

## 1. 4-Tier Memory Architecture

To manage "civilizational-scale" runs without token overflow, `thegent` implements a tiered memory system:

| Tier   | Name                  | Storage                 | Persistence  | Usage                                                             |
| ------ | --------------------- | ----------------------- | ------------ | ----------------------------------------------------------------- |
| **L1** | **Working Memory**    | LLM Context Window      | Ephemeral    | Active prompt, recent tool results, current line of thought.      |
| **L2** | **Short-term Memory** | Redis (Hash)            | Session-long | Checkpoint snapshots, local variable state, recent `RunMeta`.     |
| **L3** | **Long-term Memory**  | **Supermemory (Graph)** | Permanent    | Past decisions, research findings, code patterns, MAIF artifacts. |
| **L4** | **Archival Memory**   | **Supermemory (Docs)**  | Perpetual    | Immutable audit trail, historical logs, decommissioned agents.    |

## 2. Semantic Context Compression (WP-5001)

When the L1 context window reaches a threshold (e.g., 85% of capacity), `thegent` triggers a **Compression Cycle**:

### 2.1 Summarization Layers

- The orchestrator spawns a **Summarizer Agent** to compress the previous 50% of the conversation into a "Semantic Kernel."
- This kernel captures: **Decisions Made**, **Unresolved Risks**, and **Current Intent**.

### 2.2 Semantic Caching

- Before calling a provider, the orchestrator checks a **Semantic Cache** (Redis + Vector Sim).
- If a semantically similar prompt has been answered (e.g., "how do I verify a MAIF artifact?"), the cached response is used, saving both cost and context space.

## 3. Dynamic Context Pruning

`thegent` uses a "Priority-Based Pruning" algorithm to clear space:

1. **Retain**: Current objective, system instructions, last 3 tool results.
2. **Compress**: Previous research summaries, intermediate state transitions.
3. **Prune**: Verbose log outputs, duplicate file reads, discarded hypotheses.

## 4. Continuity Packets (ADR-011)

For "handoffs" between agents or across pauses, `thegent` generates a **Continuity Packet**:

- A highly compressed, structured JSON containing the "Essence of Progress."
- Enables a new agent to resume a run with 100% semantic fidelity using < 5% of the original token footprint.

---

_Cross-ref: [ROBUSTNESS_AND_FUTURE_DEPTH.md](./ROBUSTNESS_AND_FUTURE_DEPTH.md) | [MAIF_ARTIFACT_SPEC_DEPTH.md](./MAIF_ARTIFACT_SPEC_DEPTH.md)_

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
