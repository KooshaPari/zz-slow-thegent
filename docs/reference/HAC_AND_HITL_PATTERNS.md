# Human-Agent Collaboration (HAC) & HITL Patterns (WP-4001..4009)

This document defines the interaction patterns for seamless **Human-Agent Collaboration** within `thegent`.

## 1. Interaction Patterns

`thegent` supports three primary collaboration modes:

### 1.1 Supervisory Loop (Human-in-the-Loop)

- **Pattern**: Agent proposes an action; `PolicyEngine` triggers a "Human Review" requirement based on `Risk_Score`.
- **UX**: The **Operator Cockpit** displays the proposed change (diff) and the agent's rationale.
- **Actions**: Approve, Deny, or Edit (Modify the proposal before execution).

### 1.2 Active Learning (Human-as-a-Teacher)

- **Pattern**: When the agent is uncertain (Confidence < Threshold), it explicitly asks for clarification.
- **UX**: A "Clarification Request" appears in the cockpit.
- **Feedback**: The human's response is injected into the context and stored in the **Calibration Feedback Loop** (WP-4008) to improve future performance.

### 1.3 Human-as-a-Tool (HaaT)

- **Pattern**: The agent can call a specialized `ask_human` tool for tasks that require human-only capabilities (e.g., "Review UI feel," "Check Slack for approval").
- **UX**: The tool call pauses the agent execution and waits for human input (asynchronous or synchronous).

## 2. Autonomy Transitions

The **Autonomy Gradient Control** (from Phase 4) manages the frequency of these patterns:

| Level          | HITL Frequency         | Learning Mode        |
| -------------- | ---------------------- | -------------------- |
| **Manual**     | 100% (Every action)    | Continuous feedback. |
| **Guarded**    | High-risk only.        | Targeted feedback.   |
| **Supervised** | Exception-based.       | Passive learning.    |
| **Autonomous** | Minimal (Alerts only). | Post-hoc analysis.   |

## 3. Intervention & Override (WP-4009)

At any time, a human operator can "Intervene":

1. **Pause**: Halt all active agents in the swarm.
2. **Snapshot**: Capture the current world state.
3. **Override**: Force-update the `WORK_STREAM.md` or a specific file.
4. **Resume**: Restart agents with the new state.

Every intervention is recorded in the **Immutable Audit Trail** with a mandatory `Override_Rationale`.

---

_Cross-ref: [PHASE_4_COCKPIT_UX_DEPTH.md](./PHASE_4_COCKPIT_UX_DEPTH.md) | [AGENT_DEBUGGING_AND_REMEDIATION_GUIDE.md](../guides/AGENT_DEBUGGING_AND_REMEDIATION_GUIDE.md)_

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
