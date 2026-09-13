# Multi-Agent Orchestration Mode Catalog

**Status:** Authoritative
**Date:** 2026-02-14
**Scope:** sequential_delegation, parallel_consensus, review_loop (G-KD-04)

---

## 1. Purpose

Formalizes multi-agent orchestration patterns as supported modes per Kush docs D-D and Kagentop MultiAgentOrchestration. Mode selection policy tied to risk, urgency, and confidence.

---

## 2. Modes

| Mode                      | Description                                                                        | Phases                        | Use Case                                                                      | Risk   |
| ------------------------- | ---------------------------------------------------------------------------------- | ----------------------------- | ----------------------------------------------------------------------------- | ------ |
| **sequential_delegation** | Step-wise specialization: each agent hands off to the next in sequence             | planner → operator → ...      | Multi-step workflows where each step requires different expertise             | medium |
| **parallel_consensus**    | Independent solution synthesis: multiple agents run in parallel, result aggregated | operator, operator, ...       | Critical tasks requiring quorum or consensus (e.g. low-confidence escalation) | low    |
| **review_loop**           | Planner/Operator/Reviewer enforcement: explicit phase gates with approval          | planner → operator → reviewer | Governance-heavy workflows with explicit review gates                         | high   |

---

## 3. Mode Selection Policy

| Condition                       | Suggested Mode        |
| ------------------------------- | --------------------- |
| confidence < 0.5                | parallel_consensus    |
| risk = high, urgency ≠ critical | review_loop           |
| default                         | sequential_delegation |

---

## 4. Implementation Mapping

| Mode                  | Current thegent Feature                                                    |
| --------------------- | -------------------------------------------------------------------------- |
| parallel_consensus    | DAG task `quorum` field; multi-agent runs with leader/follower arbitration |
| sequential_delegation | DAG `depends_on`; handoff via task completion                              |
| review_loop           | CSMPhase.REVIEWER; governance gates; `decision_reason_code` validation     |

---

## 5. Discovery

- **CLI:** `thegent modes` or `thegent modes --format json`
- **MCP tool:** `thegent_list_modes`
- **Resource:** `thegent://modes` or `thegent://modes{?mode}`
- **Meta:** `thegent://meta` includes `orchestration_modes` list

---

## 6. Implementation Location

- **Catalog:** `src/thegent/orchestration_modes.py`
- **CLI:** `thegent modes` (main.py)
- **MCP:** `thegent_list_modes` tool, `thegent://modes` resource

---

## See also

- [WORK_STREAM.md](reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](plans/00-MASTER-INDEX.md) — plan index
