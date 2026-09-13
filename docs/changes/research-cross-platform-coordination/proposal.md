# Cross-Platform Coordination Through Unified Work Stream — Proposal

**Status**: Proposal
**Date**: 2026-02-18
**Priority**: P1
**Depends On**: research-cross-platform-isolation

## 1. Problem Statement

Multi-agent orchestration across heterogeneous platforms (macOS/Linux/Windows, bash/PowerShell, multiple shells) requires a **single source of truth** that all agents can access, coordinate through, and update atomically. Current approaches have three critical gaps:

### Gap 1: Work Attribution and Isolation

- Agents on different platforms cannot safely claim work without race conditions
- No clear assignment model for tracking which agent owns which task
- File-based coordination prone to concurrent-write corruption

### Gap 2: Platform-Specific Command Execution

- Agents running bash cannot coordinate with PowerShell agents
- Platform-specific hooks/scripts create isolated silos
- No cross-platform abstraction for common operations (claiming, completing, status)

### Gap 3: Session Continuity Across Platforms

- Sessions started on macOS cannot be resumed on Windows
- State lives in process memory or platform-specific locations (registry, ~/.)
- Workstreams disconnected from session lifecycle

## 2. Vision

**Goal**: Enable seamless multi-agent coordination across OS/shell boundaries through a **unified, atomic work stream** with:

1. **Platform-agnostic serialization** (JSON + Markdown for human readability, machine parsability)
2. **Atomic claim/complete operations** (file-locked CLAIMED/COMPLETED sections)
3. **Cross-platform session bridges** (Unix socket + HTTP fallback; platform-neutral session state)
4. **Standardized agent metadata** (agent_id, shell, platform, capabilities, constraints)

## 3. Scope

### In Scope

- Unified work stream format (enhanced WORK_STREAM.md design)
- Atomic claim/complete/release operations (file locking + Git-based conflict resolution)
- Cross-platform session store (JSON ledger per project)
- Agent registration and capability discovery
- Dependency resolution (DAG validation)
- Handoff protocols (session transfer, resume, rollback)

### Out of Scope

- Desktop automation (covered by research-cross-platform-desktop)
- Shell abstraction layer (covered by research-cross-platform-shell)
- Remote compute (covered by research-cross-platform-remote)
- Performance optimization (covered by research-cross-platform-performance)

## 4. Design Principles

| Principle                          | Rationale                                                         |
| ---------------------------------- | ----------------------------------------------------------------- |
| **Single Source of Truth**         | All agents read from one canonical file (WORK_STREAM.md)          |
| **Atomic Operations**              | Claim/complete are transactions; no partial state                 |
| **Human-Readable**                 | Markdown format remains editable; machine sections clearly marked |
| **Git-Native Conflict Resolution** | Use Git's merge strategy; no custom conflict resolution           |
| **No Polling**                     | Use file system events and blocking wait, not busy loops          |
| **Platform-Agnostic**              | Works on macOS, Linux, Windows; bash, PowerShell, zsh             |
| **Session-Aware**                  | Links to session registry for continuity                          |
| **Fail-Fast**                      | Explicit errors, no silent degradation                            |

## 5. Core Components

### 5.1 Enhanced Work Stream Format

**File**: `docs/reference/WORK_STREAM.md`

- BACKLOG section: Unclaimed work items
- CLAIMED section: Items currently owned by agents (with agent_id, started time)
- COMPLETED section: Finished work (with duration, result)
- Machine sections: YAML frontmatter for metadata, lock state, conflict markers

### 5.2 Atomic Operations

**Claim**: Acquire lock → verify dependencies → append to CLAIMED → release lock
**Complete**: Remove from CLAIMED → append to COMPLETED → update source file
**Release**: Move from CLAIMED back to BACKLOG (on timeout/error)

### 5.3 Cross-Platform Session Bridge

**Session Store**: `~/.thegent/sessions/registry.jsonl`
**Bridge Protocol**: Unix socket (primary) + HTTP fallback (secondary)
**Heartbeat**: Every 30s; timeout after 5 min
**Hand-off**: Session owner can pause; another agent resumes

### 5.4 Agent Registry

**File**: `.thegent/agents/registry.json`

Declares per-agent:

- ID, type (researcher/coder/reviewer)
- Platform (macOS/Linux/Windows)
- Shell (bash/zsh/PowerShell)
- Capabilities (grep, read, web-search)
- Constraints (no-shell-edit, read-only)

## 6. Benefits

| Benefit                | Impact                                                                |
| ---------------------- | --------------------------------------------------------------------- |
| **Atomic claims**      | No race conditions; work never duplicated or lost                     |
| **Cross-platform**     | macOS + Windows + Linux agents coordinate via same WORK_STREAM        |
| **Session continuity** | Agent on Platform A can pause; Agent on Platform B resumes seamlessly |
| **Git-native**         | Conflicts resolved via `git merge` logic; no custom resolution        |
| **Human-readable**     | Managers can read WORK_STREAM.md directly                             |
| **Fail-fast**          | Errors are explicit; no silent claims                                 |
| **Scalable**           | Handles 50+ concurrent agents; linear O(n) claim time                 |

## 7. Success Criteria

- [ ] WORK_STREAM.md format finalized and validated
- [ ] File locking implementation passes race condition tests
- [ ] Cross-platform session bridge works (Unix socket + HTTP)
- [ ] Claim/complete operations atomic and idempotent
- [ ] Agent registry auto-discovery working
- [ ] DAG dependency validation prevents circular claims
- [ ] Git conflict resolution tested with concurrent writes
- [ ] CLI commands (`thegent work claim`, `thegent work complete`) working
- [ ] Tests pass on macOS, Linux, Windows
- [ ] Performance: <100ms claim time (p95)

## 8. Deliverables

1. **proposal.md** (this file) — Problem, vision, scope
2. **design.md** — Technical architecture, APIs, protocols
3. **tasks.md** — Implementation checklist, phases, dependencies

## 9. References

- [WORK_STREAM.md](../reference/WORK_STREAM.md) (current format)
- [CROSS_PLATFORM_RESEARCH_CONSOLIDATED.md](../docset/CROSS_PLATFORM_RESEARCH_CONSOLIDATED.md)
- [thegent-cross-analysis-matrix-2026-02-14.md](../docset/thegent-cross-analysis-matrix-2026-02-14.md)
