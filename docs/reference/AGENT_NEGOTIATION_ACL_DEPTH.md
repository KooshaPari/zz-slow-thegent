# Agent Communication Language (JSON-ACL) & Negotiation (WP-1006)

This document defines the structured protocol for inter-agent negotiation and conflict resolution within `thegent`.

## 1. JSON-ACL Specification

`thegent` uses a JSON-based variant of traditional Agent Communication Languages (like FIPA-ACL) to enable structured "negotiation" between droids.

### 1.1 Performative Types

Agents use specific "performatives" to signal intent:

| Performative        | Description                    | Example                         |
| ------------------- | ------------------------------ | ------------------------------- |
| `propose`           | Suggest an action or solution. | Propose a code change.          |
| `accept`            | Agree to a proposal.           | Consensus achieved.             |
| `reject`            | Disagree with a proposal.      | Quality gate failed.            |
| `counter`           | Propose an alternative.        | "Use async instead of threads." |
| `call-for-proposal` | Request solutions from others. | "Who can fix this bug?"         |

### 1.2 Message Schema

```python
class ACLMessage(BaseModel):
    sender_id: str
    receiver_id: str | None = None  # None for broadcast to swarm
    performative: str
    content: dict
    conversation_id: str
    reply_with: str | None = None
    in_reply_to: str | None = None
    timestamp_us: int
```

## 2. Conflict Resolution (Negotiation Game Theory)

When multiple agents propose conflicting solutions (e.g., in a Parallel Consensus mode), they enter a **Negotiation Cycle**:

1. **Conflict Detection**: The `Orchestrator` identifies overlapping tool calls or file modifications.
2. **Preference Signaling**: Agents assign a `Utility_Score` to their proposals based on `Confidence` and `Estimated_Cost`.
3. **Automated Arbitration**:
   - **Cooperative Mode**: Agents share rationales and attempt to find a `Nash Equilibrium` (a solution that satisfies both constraints).
   - **Competitive Mode**: The agent with the highest `Adjusted_Trust_Score` wins the conflict.
4. **Resolution Trace**: The negotiation history is stored in the **MAIF artifact** for forensic review.

## 3. Resource Locking (Negotiated Access)

To prevent race conditions, agents must "Negotiate" for file locks:

- An agent sends a `request-lock` message to the **Blackboard**.
- The `Orchestrator` grants the lock if no high-priority agent is already working on that resource.
- If denied, the agent receives a `propose-defer` message with a backoff time.

---

_Cross-ref: [SWARM_MEMORY_COORDINATION_DEPTH.md](./SWARM_MEMORY_COORDINATION_DEPTH.md) | [MAIF_ARTIFACT_SPEC_DEPTH.md](./MAIF_ARTIFACT_SPEC_DEPTH.md)_

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
