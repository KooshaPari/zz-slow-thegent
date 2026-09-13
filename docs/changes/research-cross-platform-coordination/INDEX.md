# Cross-Platform Coordination Through Unified Work Stream

**Index**: Research Change Documents

## Overview

This research explores how multi-agent systems can coordinate work across heterogeneous platforms (macOS, Linux, Windows) and shells (bash, zsh, PowerShell) through a **unified, atomic work stream** as a single source of truth.

**Problem**: Currently, no mechanism exists for agents on different platforms to safely claim work without race conditions or platform-specific side effects.

**Solution**:

1. Enhanced `docs/reference/WORK_STREAM.md` format with platform/shell constraints
2. File locking for atomic claim/complete operations
3. Cross-platform session bridges for continuity
4. CLI and MCP tools for agent interaction

## Documents

### 1. [proposal.md](proposal.md) — Problem & Vision

**Audience**: Decision makers, architects
**Read Time**: 5-10 min

- Problem statement (3 critical gaps)
- Design principles (8 core principles)
- Scope definition
- Success criteria

**Key Question**: Why is cross-platform work coordination hard?
**Answer**: No atomic work claiming mechanism; agents fail silently on unsupported platforms; sessions can't move between OSes.

### 2. [design.md](design.md) — Technical Architecture

**Audience**: Architects, engineers
**Read Time**: 15-20 min

- Data models (work stream, agent registry, session store)
- Core algorithms (claim, complete, hand-off, DAG validation)
- File locking strategy (platform-specific implementations)
- Session bridge protocol (Unix socket + HTTP fallback)
- Performance targets and testing strategy

**Key Innovation**: File locking as primary coordination mechanism (works cross-platform, Git-safe, auditable).

### 3. [tasks.md](tasks.md) — Implementation Plan

**Audience**: Implementation team, project leads
**Read Time**: 10-15 min

- 6 phases, 11 tasks
- Dependency graph (DAG)
- Timeline (~3-4 days with parallel agents)
- Definition of Done
- Parallel execution strategy

**Key Milestone**: Phase 1 (Format & Locking) → foundation for all other phases.

## Quick Start for Implementers

### Phase 1: Format & Locking (Day 1)

```bash
# T1.1: Enhance WORK_STREAM.md format
# T1.2: Implement file locking (fcntl/msvcrt)
```

**Owner**: Agent A
**Time**: 50 min
**Dependencies**: None

### Phase 2: Session & Registry (Day 2)

```bash
# T2.1: Session store (jsonl registry)
# T2.2: Agent registry (metadata + discovery)
# T2.3: Session bridge (Unix socket + HTTP fallback)
```

**Owner**: Agent B
**Time**: 75 min
**Dependencies**: Phase 1

### Phases 3-6: Complete Implementation (Days 3-4)

Follow task checklist in `tasks.md` for detailed steps.

## Architecture at a Glance

```
┌─────────────────────────────────────────────────────┐
│          Unified Work Stream (WORK_STREAM.md)       │
│  ┌──────────┬───────────┬──────────────────────┐   │
│  │ BACKLOG  │ CLAIMED   │   COMPLETED          │   │
│  │ (pending)│(in-flight)│   (done)             │   │
│  └──────────┴───────────┴──────────────────────┘   │
└─────────────────────────────────────────────────────┘
             ▲                   ▲
    ┌────────┴────────┬─────────┴──────┬───────────┐
    │                 │                │           │
┌──────────────┐ ┌────────────┐ ┌──────────────────┐
│ File Locking │ │   Agent    │ │  Session Bridge  │
│   (atomic)   │ │  Registry  │ │   (continuity)   │
└──────────────┘ └────────────┘ └──────────────────┘
```

## Key Concepts

| Concept                  | Explanation                                                                      |
| ------------------------ | -------------------------------------------------------------------------------- |
| **Atomic Claims**        | Only one agent can claim work at a time (file lock prevents race conditions)     |
| **Platform Constraints** | Work can declare supported platforms/shells (e.g., "darwin,linux" or "bash,zsh") |
| **Session Continuity**   | Sessions survive platform changes (Agent on macOS can hand off to Windows)       |
| **DAG Validation**       | Dependency graph validated at claim time (prevents circular deps)                |
| **File Locking**         | Unix (fcntl) + Windows (msvcrt) + Python fallback; <10ms typical                 |
| **Session Bridge**       | Unix socket (primary) + HTTP fallback (secondary) for cross-platform hand-offs   |

## Success Criteria

- [ ] All agents declare platform/shell constraints
- [ ] Claim/complete operations are atomic (no race conditions)
- [ ] Hand-off works across platforms (macOS → Windows → Linux)
- [ ] DAG validation prevents circular dependencies
- [ ] Cross-platform tests pass on ≥3 platforms
- [ ] Performance: <100ms claim time (p95)
- [ ] Agent developers adopt new coordination model

## Integration with Existing Systems

- **WORK_STREAM.md**: Enhanced format; backward compatible
- **Work Incorporator**: Merges fragments into unified stream (already exists)
- **CLI**: New `thegent work *` commands
- **MCP**: New tools for agent-level access
- **Session Bridge**: Lightweight (~100 LOC) infrastructure addition

## Next Steps

1. **Review**: Stakeholders review proposal.md + design.md
2. **Kickoff**: Implementation team starts Phase 1 (Format & Locking)
3. **Parallel**: Phases 2-4 can run in parallel after Phase 1
4. **Testing**: Phase 5 (comprehensive testing on all platforms)
5. **Launch**: Phase 6 (documentation) + training

## Questions?

See [CONVERSATION_DUMP_2026-02-18-CROSS_PLATFORM.md](../../research/CONVERSATION_DUMP_2026-02-18-CROSS_PLATFORM.md) for research notes and design rationale.
