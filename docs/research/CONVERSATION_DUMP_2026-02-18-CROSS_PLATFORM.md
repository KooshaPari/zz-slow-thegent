<DONE>
# Cross-Platform Coordination Research — Conversation Dump

**Date**: 2026-02-18
**Agent**: Claude Haiku 4.5
**Status**: Synthesis Complete
**Token Budget Used**: ~350/521 tool calls

---

## Executive Summary

Synthesized comprehensive development writeup for **cross-platform agent coordination through unified work stream**. Generated three core documents (proposal.md, design.md, tasks.md) totaling 1,259 lines of architectural specification and implementation guidance.

**Key Innovation**: Atomic work claiming across heterogeneous platforms (macOS/Linux/Windows, bash/PowerShell) using file locking + Git merge strategy + session bridges.

---

## Artifacts Generated

### 1. proposal.md (135 lines)

**Purpose**: Problem statement, vision, design principles, scope

**Sections**:

- Problem Statement (3 gaps: work attribution, platform silos, session continuity)
- Vision (unified atomic work stream)
- Scope (in-scope vs out-of-scope)
- Design Principles (8 core principles)
- Core Components (work stream format, atomic ops, session bridge, agent registry)
- Benefits (atomic claims, cross-platform, continuity, git-native)
- Success Criteria (10 acceptance items)

**Key Insight**: Failure in current approach is **three-fold**:

1. No atomic work claiming (race conditions)
2. No platform-aware dispatch (agents fail silently)
3. No session continuity across platforms (work stuck on one OS)

---

### 2. design.md (435 lines)

**Purpose**: Technical architecture, data models, algorithms, protocols

**Sections**:

- Architecture Overview (diagram)
- Core Data Models:
  - Work Stream format (BACKLOG, CLAIMED, COMPLETED tables + YAML frontmatter)
  - Agent Registry (metadata: id, type, platform, shell, capabilities, constraints)
  - Session Registry (newline-delimited JSON, heartbeat-based)
- Core Algorithms:
  - Claim Work (7 steps: detect platform, acquire lock, validate deps, register session)
  - Complete Work (move from CLAIMED → COMPLETED, update source file)
  - Hand-off Protocol (cross-platform session transfer with checkpoint)
  - DAG Validation (topological sort + cycle detection)
- File Locking Strategy (platform-specific: Unix fcntl, Windows msvcrt, fallback filelock)
- Cross-Platform Session Bridge (Unix socket primary + HTTP fallback)
- Performance Targets (<100ms claim time p95, <150ms complete, <200ms hand-off)
- Testing Strategy (unit, integration, multi-platform matrix)
- Future Enhancements (versioning, batch ops, priority-based claiming, SLA enforcement)

**Key Design Decision**: **File locking as primary coordination mechanism** rather than database/shared memory. Rationale:

- Works across all platforms (Unix, Windows)
- Git-safe (no special tooling needed)
- Human-auditable (plain Markdown file)
- Scalable to 50+ concurrent agents (linear O(n) claim time)

---

### 3. tasks.md (455 lines)

**Purpose**: Implementation checklist, phased execution, dependencies, timeline

**Phases** (6 phases, 11 tasks total, ~7 days serial / ~3-4 days parallel):

| Phase                 | Tasks            | Est. Time | Days |
| --------------------- | ---------------- | --------- | ---- |
| 1: Format & Locking   | T1.1, T1.2       | 50 min    | 1    |
| 2: Session & Registry | T2.1, T2.2, T2.3 | 75 min    | 1    |
| 3: Atomic Ops         | T3.1, T3.2, T3.3 | 65 min    | 1    |
| 4: DAG & CLI          | T4.1, T4.2       | 55 min    | 1    |
| 5: Testing            | T5.1, T5.2       | 70 min    | 2    |
| 6: Docs               | T6.1, T6.2       | 35 min    | 1    |

**Key Tasks**:

- T1.1: Enhance WORK_STREAM.md format (add YAML frontmatter, Platform/Shell columns)
- T1.2: File locking implementation (Unix: fcntl, Windows: msvcrt, with race condition tests)
- T2.1: Session store (jsonl registry, heartbeat, timeout recovery)
- T2.2: Agent registry (metadata, capability discovery, constraint validation)
- T2.3: Cross-platform session bridge (Unix socket + HTTP fallback)
- T3.1: Claim operation (lock, validate deps, register session)
- T3.2: Complete operation (move to COMPLETED, update source, update session)
- T3.3: Hand-off protocol (cross-platform transfer with checkpoint)
- T4.1: DAG validator (topological sort, cycle detection)
- T4.2: CLI commands (claim, complete, handoff, status, show)
- T5.1/T5.2: Unit + integration tests (≥85% coverage, cross-platform matrix)
- T6.1/T6.2: API docs + developer guide

**Definition of Done**:

- ✅ All code passes linting (ruff, mypy)
- ✅ Unit test coverage ≥85%
- ✅ Integration tests pass on macOS, Linux, Windows
- ✅ All CLI commands working and documented
- ✅ Documentation complete and reviewed
- ✅ Feature merged to main
- ✅ WORK_STREAM.md incorporator updated
- ✅ Agent developers trained

---

## Key Architectural Decisions

### 1. Single Source of Truth

All agents read from **one canonical file**: `docs/reference/WORK_STREAM.md`

**Rationale**:

- Git-compatible (standard merge strategies)
- Human-readable (managers can debug)
- No external dependencies (no database needed)
- Auditable (full history in git)

### 2. Atomic Operations via File Locking

Claim/complete are **transactions** protected by file locks:

1. Acquire lock (10s timeout)
2. Re-read file (prevent TOCTOU race)
3. Apply delta
4. Write atomically
5. Release lock

**Rationale**:

- Works cross-platform (Unix + Windows primitives)
- Simple (no distributed transaction protocol)
- Proven (OS kernel guarantees exclusivity)

### 3. Session Bridges for Continuity

Sessions survive platform changes via **dual-transport bridge**:

- Primary: Unix socket (`~/.thegent/sessions/bridge.sock`)
- Secondary: HTTP fallback (`http://localhost:37847/sessions`)

**Rationale**:

- Fast local communication (Unix socket)
- Resilient (HTTP fallback when socket unavailable)
- Cross-platform (socket on Unix, HTTP on Windows)

### 4. DAG Validation at Claim Time

Dependency validation prevents invalid claims:

1. Check all `Depends` items are in COMPLETED
2. Detect circular dependencies (Tarjan's algorithm)
3. Fail-fast if unmet

**Rationale**:

- Prevents work from getting stuck on unmet deps
- Enables intelligent task sequencing
- Supports complex multi-phase projects

---

## Critical Implementation Notes

### File Locking Strategy

```python
# Unix: fcntl.flock() with timeout
# Windows: os.open() with O_CREAT | O_EXCL (atomic)
# Fallback: filelock library (pure Python)

# Timeout: 10s default (configurable)
# Retry: exponential backoff (0.1s → 1s)
# Recovery: stale locks cleaned up after 5 min no heartbeat
```

### Claim Workflow (7 Steps)

```
1. Detect platform/shell (macOS/Linux/Windows, bash/zsh/pwsh)
2. Parse WORK_STREAM.md
3. Find work in BACKLOG (fail if already claimed)
4. Verify platform/shell compatibility (fail if unsupported)
5. Validate dependencies (fail if not completed)
6. Acquire file lock (timeout 10s)
7. Move from BACKLOG → CLAIMED + register session
```

### Hand-off Protocol (Session Transfer)

```
Agent A (macOS):
  1. Holds claim on task-1
  2. Creates checkpoint (git SHA, files modified)

Agent B (Windows):
  1. Reads CLAIMED, finds task-1
  2. Registers new session (parent_session_id = Agent A's session)
  3. Reads checkpoint, resumes from git

Agent A:
  1. Pauses session (retains claim but releases OS lock)
```

---

## Cross-Platform Considerations

### Platform Detection

```python
# Detect at claim time
platform = detect_platform()  # darwin, linux, win32
shell = detect_shell()  # bash, zsh, pwsh, cmd

# Validate against work constraints
if not work.platform_compatible(platform):
    raise ClaimError(f"Platform {platform} not in {work.platform}")
```

### Shell Support

- Unix: bash, zsh, sh, ksh, fish
- Windows: pwsh (PowerShell Core), cmd (cmd.exe)
- Constraint example: `shell: "bash,zsh"` (agent must use one of these)

### Session Bridge Fallback

- Unix socket (macOS/Linux): Fast local IPC
- HTTP fallback (Windows, or when socket unavailable): Standard port + fallback protocol

---

## Integration Points

### 1. Work Incorporator

Existing incorporator agent merges fragments into WORK_STREAM:

- Reads: `docs/plans/`, `docs/research/`, `docs/docset/`
- Writes: `docs/reference/WORK_STREAM.md`
- Deduplication: Already implemented

### 2. CLI Commands

New commands integrate seamlessly:

```bash
thegent work claim task-1 --agent agent-macos-1 --deadline 2026-02-20T00:00:00Z
thegent work complete task-1 --agent agent-macos-1 --result DONE
thegent work handoff task-1 --from agent-macos-1 --to agent-windows-1
thegent work status task-1
thegent work claimed --agent agent-macos-1
thegent work show
```

### 3. MCP Tools

Agents can query/manipulate work stream programmatically:

```python
# MCP tool: thegent_work_claim
# MCP tool: thegent_work_complete
# MCP resource: thegent://workstream/backlog
# MCP resource: thegent://workstream/claimed
```

---

## Success Metrics

**Atomic Operations**:

- ✅ No work item claimed by multiple agents (race condition test passes)
- ✅ No work item lost on error (rollback test passes)
- ✅ Claim time <100ms (p95) on typical machine

**Cross-Platform**:

- ✅ Agent on macOS can claim work declared for Linux
- ✅ Hand-off from macOS → Windows works (session survives)
- ✅ CI matrix passes on ≥3 platforms (macOS, Linux, Windows)

**Reliability**:

- ✅ Session timeout correctly releases locks (heartbeat test)
- ✅ DAG validation prevents circular deps (topological sort test)
- ✅ File locking prevents concurrent writes (atomicity test)

---

## Open Questions for Implementation Team

1. **Git auto-commit**: Should we auto-commit WORK_STREAM changes to git history, or leave that to user?
2. **Conflict resolution**: What happens if two agents try to claim same work simultaneously? (Answer: file lock ensures one wins, other gets clear error)
3. **Escalation**: If work times out (stale claim), who moves it back to BACKLOG? (Answer: heartbeat timeout triggers auto-release)
4. **Metrics**: Should we emit Prometheus metrics for claim/complete latencies? (Answer: Yes, for observability)

---

## Handoff Notes for Next Agent

### To Implement

1. Start with **Phase 1 (Format & Locking)** — foundation task
2. Then **Phase 2 (Session & Registry)** — parallelizable with Phase 1
3. Then **Phases 3-4** (Atomic Ops, DAG, CLI) — depend on Phases 1-2
4. Then **Phase 5** (Testing) — comprehensive coverage
5. Then **Phase 6** (Docs) — final polish

### Critical Success Factors

- **File locking** must be correct (race condition tests are non-negotiable)
- **Cross-platform testing** must include Windows (not just macOS/Linux)
- **Session bridge fallback** must work (test socket → HTTP gracefully)
- **DAG validation** must prevent circular deps (edge case in complex projects)

### Parallel Execution

- T1.x can run in parallel (both depend on Phase 1)
- T2.x can run in parallel with T3.x (different components)
- T5.x (testing) must wait for T1-T4 (implementation)

---

## References

- [proposal.md](../changes/research-cross-platform-coordination/proposal.md) — Full problem statement + vision
- [design.md](../changes/research-cross-platform-coordination/design.md) — Technical architecture + algorithms
- [tasks.md](../changes/research-cross-platform-coordination/tasks.md) — Implementation checklist
- [WORK_STREAM.md](../reference/WORK_STREAM.md) — Current work stream format
- [thegent-cross-analysis-matrix-2026-02-14.md](../docset/thegent-cross-analysis-matrix-2026-02-14.md) — Design pattern synthesis

---

## Session Metrics

| Metric                      | Value                       |
| --------------------------- | --------------------------- |
| **Documents Generated**     | 3 (proposal, design, tasks) |
| **Total Lines**             | 1,259                       |
| **Design Depth**            | 11 tasks across 6 phases    |
| **Implementation Timeline** | ~3-4 days (parallel agents) |
| **Token Budget Used**       | ~350/521 tool calls         |
| **Time to Completion**      | ~15 min (single agent)      |

---

## Final Status

✅ **COMPLETE**: Cross-platform coordination research writeup finalized

**Deliverables**:

- ✅ `docs/changes/research-cross-platform-coordination/proposal.md`
- ✅ `docs/changes/research-cross-platform-coordination/design.md`
- ✅ `docs/changes/research-cross-platform-coordination/tasks.md`
- ✅ `docs/changes/research-cross-platform-coordination/README.md` (generated)

**Next Step**: Route to implementation team for Phase 1 (Format & Locking)
