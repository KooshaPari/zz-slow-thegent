# Agentic CI/CD & Self-Healing Loops (WP-2004)

This document defines the patterns for **Autonomous Software Rehabilitation**, where `thegent` agents detect, classify, and repair their own errors.

## 1. The Self-Healing Loop (Rehabilitation)

When a `quality-gate.sh` or `async-test-runner` fails after an agent's edit, `thegent` triggers a **Rehabilitation Cycle**:

1. **Error Classification**: The **AgentDebug** framework (from `AGENT_DEBUGGING_AND_REMEDIATION_GUIDE.md`) classifies the failure (e.g., `ACTION_SYSTEM` vs `PLANNING_LOGIC`).
2. **Context Injection**: The full stack trace, recent diffs, and the failing test file are injected into a new **Healer Agent**'s context.
3. **Hypothesis Generation**: The Healer Agent proposes 3 potential fixes.
4. **Simulation Validation**: Each fix is run in the **Replay Sandbox** against the failing test.
5. **Commitment**: The fix that passes the test _and_ all existing regression tests is automatically committed.

## 2. Agentic CI/CD Integration

`thegent` transforms the CI/CD pipeline from a "Passive Gate" to an "Active Agentic Service":

| CI Phase          | Agentic Action                                                       |
| ----------------- | -------------------------------------------------------------------- |
| **Lint/Build**    | Auto-fix trivial violations (e.g., imports, formatting).             |
| **Test**          | Spawns a Healer Agent on failure.                                    |
| **Security Scan** | Spawns a Security Patch Agent on finding a vulnerability.            |
| **Merge**         | **Incorporator Agent** merges the PR after passing the Healer cycle. |

## 3. Poison Pill Detection (WP-2004)

To avoid infinite repair loops:

- **Tries**: A specific bug is given a maximum of 3 rehabilitation attempts.
- **Poison Pill**: If the same error persists after 3 tries, the task is marked as a "Poison Pill" and escalated to the **Dead-Letter Queue (DLQ)** for human intervention.

## 4. Rehabilitation Ledger

Every self-healing action is recorded in the **Rehabilitation Ledger**:

- **Root Cause**: The identified reason for the failure.
- **Fix Pattern**: The code pattern used to resolve the issue.
- **Verification**: Evidence that the fix works.

---

_Cross-ref: [AGENT_DEBUGGING_AND_REMEDIATION_GUIDE.md](../guides/AGENT_DEBUGGING_AND_REMEDIATION_GUIDE.md) | [SIMULATION_AND_SANDBOX_DEPTH.md](./SIMULATION_AND_SANDBOX_DEPTH.md)_

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
