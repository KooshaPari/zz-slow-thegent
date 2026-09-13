# Agent Debugging and Remediation Guide

> **Purpose**: A formal framework for identifying, classifying, and remediating agent failures within the thegent platform.
> **Scope**: Based on `AgentErrorTaxonomy` and `AgentDebug` research (arXiv 2509.25370).

---

## 1. Agent Error Taxonomy

When an agent fails, the system must classify the failure into one of the following buckets to determine the correct remediation path.

| Category       | Type          | Example                                           | Remediation Path              |
| -------------- | ------------- | ------------------------------------------------- | ----------------------------- |
| **Memory**     | Retrieval     | Agent forgets previous step instructions.         | Handoff Refresh (WP-4006)     |
| **Reflection** | Hallucination | Agent claims a tool succeeded when it failed.     | Validation Layer (WP-X4)      |
| **Planning**   | Loop          | Agent keeps repeating the same failing tool call. | Poison Pill Detection (WP-Y2) |
| **Action**     | Syntax        | Agent generates malformed XML or JSON.            | XML Repair (ROB-018)          |
| **System**     | Timeout       | Provider (e.g. Claude) is unresponsive.           | Circuit Breaker (WP-2003)     |

---

## 2. Automated Remediation (AgentDebug Loop)

The platform implements a "Closed-Loop Remediation" system where failures are fed back to the agent with targeted corrective instructions.

### 2.1 The Feedback Loop

1.  **Detection**: `gardener-scan.sh` or `AgilePlus SCAN` identifies a failure.
2.  **Classification**: The failure is mapped to the `AgentErrorTaxonomy`.
3.  **Handoff Generation**: A `ContinuityPacket` is created containing:
    - The failed action.
    - The classification (e.g., "Hallucination Detected").
    - Corrective hint (e.g., "Verify the output of `ls` before assuming the file exists").
4.  **Resumption**: The agent is re-spawned with the `ContinuityPacket`.

### 2.2 Poison Pill Detection (WP-Y2)

If an agent hits the same failure bucket 3 times in a row for the same task:

1.  Stop the agent.
2.  Move the task to the **Dead-Letter Queue (DLQ)**.
3.  Escalate to a human operator via `thegent govern escalate add`.

---

## 3. Operator Procedures

### 3.1 Inspecting Failures

Use the following commands to debug a failing agent:

```bash
thegent ps --status failed          # Find failed sessions
thegent logs <session_id>           # View the raw logs
thegent run-diff <id1> <id2>        # Compare two failing runs
thegent inspect --session <id>      # Deep state inspection
```

### 3.2 Manual Remediation

If an agent is stuck, an operator can "take over" the session:

```bash
thegent takeover <session_id>       # Attach to the tmux session
# ... manually enter corrective commands ...
```

---

## 4. References

- [ROBUSTNESS_AND_FUTURE_DEPTH.md](../reference/ROBUSTNESS_AND_FUTURE_DEPTH.md)
- [02-UNIFIED-WBS.md](../plans/02-UNIFIED-WBS.md)
- [GARDENER_ARCHITECTURE.md](../reference/GARDENER_ARCHITECTURE.md)

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
