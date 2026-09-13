# Gardener Architecture

## Overview

The Gardener system implements an automatic "headless gardener" that maintains infrastructure, tests, and docs without human intervention. It's modeled after 4X game mechanics where "hunger" states trigger automatic responses.

## Based On Research

### Agent-Driven Development

- Multi-agent frameworks (CrewAI, LangGraph, AutoGen)
- Perceive → Reason → Act → Reflect → Store loops
- Sub-agent decomposition patterns

### Vibecoding & Swarm Development

- Intent over implementation
- Division of labor
- Emergent coordination through shared state

### Human-Driven Development (SDLC, DDD)

- Agile ceremonies (sprint planning, daily standup, retrospective)
- DDD bounded contexts
- RACI matrices for accountability

## Core Concepts

### Hunger States

| Hunger              | Detection              | Response                      |
| ------------------- | ---------------------- | ----------------------------- |
| test_coverage       | Coverage < 80%         | Spawn qa-test-coverage-expert |
| lint_violations     | ruff errors > 0        | Spawn lint-fix agent          |
| doc_disorganization | Missing docs/ dirs     | Spawn code-documentor         |
| fragmented_research | Research in wrong loc  | Move to unified stream        |
| missing_specs       | No SPEC.md for feature | Queue for formalization       |
| technical_debt      | Complexity > 10        | Queue for debt elimination    |
| stale_items         | No progress > 7 days   | Boost priority                |
| agent_failure       | Circuit breaker OPEN   | Spawn recovery agent          |

### 4X Mapping

| 4X Action         | Dev Equivalent          |
| ----------------- | ----------------------- |
| Building houses   | Creating test files     |
| Building barracks | Adding implementation   |
| Research tech     | Adding documentation    |
| Defending         | Fixing security issues  |
| Exploring         | Research new approaches |

## Gardener Loop

```
SCAN → PRIORITIZE → ROUTE → EXECUTE → VERIFY → REPORT
```

### 1. SCAN

Checks all hunger states via `gardener-scan.sh`

### 2. PRIORITIZE

Ranks by urgency:

- Critical: Within 5 min
- High: Within 1 hour
- Medium: Within 24 hours
- Low: Next batch

### 3. ROUTE

Matches hunger to bounded context (qa, docs, code, governance, research)

### 4. EXECUTE

Spawns agents to address issues

### 5. VERIFY

Confirms resolution, updates hunger states

### 6. REPORT

Logs actions, updates XP, unlocks achievements

## Trigger System

### Hybrid Triggers

1. **FS Watcher** - Monitor src/, docs/, specs/ for changes
2. **Git Triggers** - On commit, branch, PR events
3. **Time-based** - Periodic heartbeat (default: 1 hour)
4. **Manual** - Explicit approval gates between stages

## Unified Work Stream

```
specs/
├── intake/           # Raw ideas (backlog)
├── breadth/         # Multi-angle research
├── depth/           # Technical design
├── devil-advocate/  # Challenge/validation
├── synthesis/       # Combined findings
├── formalizing/     # Creating SPECs
├── approved/        # Ready for implementation
├── implementing/    # Being built
├── verifying/      # In review/testing
└── archived/       # Completed
```

## Event Types

- `idea:new` - New idea in intake
- `research:complete` - Research stage done
- `spec:approved` - Formalization approved
- `implementation:complete` - Code done
- `review:passed` - Quality gates passed
- `hunger:detected` - Issue found
- `task:started/completed/failed` - State transitions

## XP System

| Action                  | XP   |
| ----------------------- | ---- |
| Complete research stage | +50  |
| Pass quality gate       | +100 |
| Fix critical bug        | +75  |
| Add test coverage       | +25  |
| Complete implementation | +150 |
| Pass code review        | +50  |

### Levels

1. 0 XP: Basic agents
2. 500 XP: Research pipeline
3. 1500 XP: Full gardener
4. 5000 XP: Parallel execution
5. 15000 XP: Advanced orchestration

## Continuity Packets

Agents pass structured handoffs:

```json
{
  "packet_id": "cp_abc123",
  "run_id": "run_xyz",
  "phase": "breadth",
  "progress": 0.65,
  "summary": "Completed angle-1 and angle-2",
  "owner": "breadth-agent",
  "handoff_to": "depth-agent"
}
```

## Files

- `hooks/gardener-loop.sh` - Main loop
- `hooks/gardener-scan.sh` - Hunger detection
- `hooks/gardener-spawn.sh` - Agent spawning
- `hooks/hook-config.yaml` - Gardener config
- `contracts/garden-state.json` - State tracking
- `specs/` - Unified work stream

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
