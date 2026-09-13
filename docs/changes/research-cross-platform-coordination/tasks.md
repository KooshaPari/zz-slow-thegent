# Cross-Platform Coordination Through Unified Work Stream — Tasks

**Status**: Task Planning
**Date**: 2026-02-18
**Baseline**: proposal.md, design.md

## Implementation Phases

### Phase 1: Work Stream Format & File Locking (Days 1-2)

#### T1.1: Enhance WORK_STREAM.md Format

**Estimate**: 4 tool calls | 20 min
**Owner**: Agent A
**Depends on**: None
**Status**: Pending

**Tasks**:

- [ ] Add YAML frontmatter to WORK_STREAM.md (version, metadata, lock state)
- [ ] Add Platform and Shell columns to BACKLOG table
- [ ] Document machine-readable sections (clear boundaries for parsing)
- [ ] Create examples of valid/invalid entries

**Acceptance Criteria**:

- Format supports all three sections (BACKLOG, CLAIMED, COMPLETED)
- Platform/shell constraints are optional (default: "any")
- YAML frontmatter is parseable and versioned
- Markdown is human-editable without tools

---

#### T1.2: File Locking Implementation

**Estimate**: 6 tool calls | 30 min
**Owner**: Agent A
**Depends on**: None
**Status**: Pending

**Tasks**:

- [ ] Implement `FileLock` class (Unix: fcntl, Windows: msvcrt, fallback: filelock)
- [ ] Add timeout handling (default: 10s, configurable)
- [ ] Implement lock recovery (stale lock cleanup)
- [ ] Add tests for race conditions (10+ concurrent agents)
- [ ] Test on macOS, Linux, Windows

**Acceptance Criteria**:

- Lock acquisition <10ms typical case
- Timeout works correctly on all platforms
- Stale locks cleaned up after 5 min
- Race condition tests pass (no duplicates, no lost claims)

---

### Phase 2: Session Bridge & Agent Registry (Days 3-4)

#### T2.1: Session Store & Registry

**Estimate**: 5 tool calls | 25 min
**Owner**: Agent B
**Depends on**: None
**Status**: Pending

**Tasks**:

- [ ] Create session store: `~/.thegent/sessions/registry.jsonl`
- [ ] Implement session registration (UUID-based session IDs)
- [ ] Add session state tracking (in_progress, paused, completed)
- [ ] Implement heartbeat mechanism (30s interval, 300s timeout)
- [ ] Add session rollback on timeout (move work back to BACKLOG)

**Acceptance Criteria**:

- Sessions persist across process restarts
- Heartbeat correctly detects stale sessions
- Timeout correctly releases locks
- Session state machine is correct

---

#### T2.2: Agent Registry

**Estimate**: 4 tool calls | 20 min
**Owner**: Agent B
**Depends on**: None
**Status**: Pending

**Tasks**:

- [ ] Create agent registry: `.thegent/agents/registry.json`
- [ ] Add agent metadata (id, type, platform, shell, capabilities)
- [ ] Implement capability discovery (from agent definitions)
- [ ] Add constraint validation per agent
- [ ] Implement registry lookup by agent_id

**Acceptance Criteria**:

- Registry auto-discovers agents from definitions
- Constraints are enforced at claim time
- Clear error messages for unsupported platforms/shells

---

#### T2.3: Cross-Platform Session Bridge

**Estimate**: 6 tool calls | 30 min
**Owner**: Agent B
**Depends on**: T2.1
**Status**: Pending

**Tasks**:

- [ ] Implement Unix socket bridge (primary): `~/.thegent/sessions/bridge.sock`
- [ ] Implement HTTP fallback (secondary): `http://localhost:37847/sessions`
- [ ] Add session registration protocol (JSON messages)
- [ ] Implement heartbeat/ping protocol
- [ ] Test bridge on macOS (Unix socket), Windows (HTTP fallback)

**Acceptance Criteria**:

- Unix socket works on macOS/Linux
- HTTP fallback works when socket unavailable
- Heartbeat keeps sessions alive
- Cross-platform hand-offs work (session survives platform change)

---

### Phase 3: Atomic Operations (Days 5-6)

#### T3.1: Claim Operation

**Estimate**: 7 tool calls | 35 min
**Owner**: Agent C
**Depends on**: T1.2, T2.1, T2.2
**Status**: Pending

**Tasks**:

- [ ] Implement `claim_work()` function (acquires lock, validates deps, appends to CLAIMED)
- [ ] Add dependency validation (DAG check, circular detection)
- [ ] Add platform/shell constraint matching
- [ ] Implement session registration on claim
- [ ] Add comprehensive error handling and diagnostics

**Acceptance Criteria**:

- Claim succeeds for valid work
- Claim fails clearly for already-claimed work
- Dependency validation prevents invalid claims
- Session registration creates heartbeat task
- Error messages are actionable

---

#### T3.2: Complete Operation

**Estimate**: 5 tool calls | 25 min
**Owner**: Agent C
**Depends on**: T1.2, T3.1
**Status**: Pending

**Tasks**:

- [ ] Implement `complete_work()` function (moves from CLAIMED to COMPLETED)
- [ ] Calculate duration (started → completed)
- [ ] Update source file (e.g., 02-UNIFIED-WBS.md) to DONE status
- [ ] Update session state (idle)
- [ ] Add result tracking (commit SHA, duration, metadata)

**Acceptance Criteria**:

- Complete succeeds for claimed work
- Complete fails clearly if work not claimed by agent
- Source files are updated atomically
- Duration is calculated correctly
- Session state reflects completion

---

#### T3.3: Hand-off Protocol

**Estimate**: 5 tool calls | 25 min
**Owner**: Agent C
**Depends on**: T2.1, T3.1
**Status**: Pending

**Tasks**:

- [ ] Implement `hand_off_work()` for cross-platform transfer
- [ ] Create checkpoint (git SHA, files modified)
- [ ] Register new session for target agent
- [ ] Update CLAIMED (agent field changes)
- [ ] Pause source session

**Acceptance Criteria**:

- Hand-off creates clean handover point (git checkpoint)
- Target agent can resume from checkpoint
- Source session paused but work retained
- Both agents can track work ownership history

---

### Phase 4: DAG Validation & CLI (Days 7-8)

#### T4.1: DAG Validator

**Estimate**: 5 tool calls | 25 min
**Owner**: Agent D
**Depends on**: T1.1, T3.1
**Status**: Pending

**Tasks**:

- [ ] Implement topological sort for work stream
- [ ] Detect circular dependencies (Tarjan's algorithm)
- [ ] Validate all CLAIMED deps are satisfied
- [ ] Check platform/shell compatibility at claim time
- [ ] Add detailed error reporting

**Acceptance Criteria**:

- Circular dependencies detected and reported
- Unsatisfied deps prevent claiming
- Platform constraints validated
- Error messages list exact issues

---

#### T4.2: CLI Commands

**Estimate**: 6 tool calls | 30 min
**Owner**: Agent D
**Depends on**: T3.1, T3.2, T3.3, T4.1
**Status**: Pending

**Tasks**:

- [ ] Implement `thegent work claim <id> --agent <agent_id>`
- [ ] Implement `thegent work complete <id> --agent <agent_id> --result <result>`
- [ ] Implement `thegent work status <id>`
- [ ] Implement `thegent work claimed --agent <agent_id>`
- [ ] Implement `thegent work handoff <id> --from <agent_a> --to <agent_b>`
- [ ] Implement `thegent work show` (display full stream)

**Acceptance Criteria**:

- All commands work end-to-end
- Output is clear (table format for lists)
- Help text is comprehensive
- Commands complete in <1s

---

### Phase 5: Testing (Days 9-10)

#### T5.1: Unit Tests

**Estimate**: 8 tool calls | 40 min
**Owner**: Agent E
**Depends on**: All core implementation
**Status**: Pending

**Tasks**:

- [ ] Test file locking (no race conditions)
- [ ] Test claim/complete workflows
- [ ] Test hand-off protocol
- [ ] Test DAG validation
- [ ] Test platform/shell constraint matching
- [ ] Test error handling

**Test Coverage Target**: ≥85%

**Acceptance Criteria**:

- All tests pass
- Coverage ≥85%
- Race condition tests pass with 10+ concurrent agents

---

#### T5.2: Cross-Platform Integration Tests

**Estimate**: 6 tool calls | 30 min
**Owner**: Agent E
**Depends on**: T5.1
**Status**: Pending

**Tasks**:

- [ ] Test claim/complete on macOS (darwin/zsh)
- [ ] Test claim/complete on Linux (linux/bash)
- [ ] Test hand-off from macOS → Linux
- [ ] Test hand-off from Linux → Windows
- [ ] Test session bridge (Unix socket + HTTP)
- [ ] Test concurrent claims from multiple agents

**Acceptance Criteria**:

- All workflows work on ≥3 platforms
- Hand-offs preserve state correctly
- Session bridge handles fallback correctly
- Concurrent operations produce no duplicates

---

### Phase 6: Documentation & Handoff (Day 11)

#### T6.1: API Documentation

**Estimate**: 4 tool calls | 20 min
**Owner**: Agent F
**Depends on**: All implementation
**Status**: Pending

**Location**: `docs/reference/WORK_STREAM_API.md`

**Tasks**:

- [ ] Document claim/complete/handoff APIs
- [ ] Document error codes and messages
- [ ] Document platform/shell constraint format
- [ ] Provide Python examples for agents

**Acceptance Criteria**:

- API is clearly documented
- Examples are runnable
- Error handling is clear

---

#### T6.2: Developer Guide

**Estimate**: 3 tool calls | 15 min
**Owner**: Agent F
**Depends on**: T6.1
**Status**: Pending

**Location**: `docs/guides/UNIFIED_WORK_STREAM_GUIDE.md`

**Tasks**:

- [ ] Document how agents claim work
- [ ] Document how to declare platform constraints
- [ ] Document hand-off workflow
- [ ] Provide troubleshooting tips

**Acceptance Criteria**:

- Guide is clear and actionable
- Examples cover basic and advanced scenarios

---

## Dependency Graph

```
T1.1 (Format) → T1.2 (File Locking)
  ├─→ T2.1 (Session Store)
  ├─→ T2.2 (Agent Registry)
  │    └─→ T2.3 (Session Bridge) → T3.1 (Claim) → T3.2 (Complete)
  │                                    └─→ T3.3 (Hand-off)
  └─→ T4.1 (DAG Validator) → T4.2 (CLI)

T5.1 (Unit Tests) → T5.2 (Integration Tests)
T6.1 (API Docs) → T6.2 (Guide)
```

## Timeline

| Phase                 | Tasks            | Est. Time        | Days                 |
| --------------------- | ---------------- | ---------------- | -------------------- |
| 1: Format & Locking   | T1.1, T1.2       | 50 min           | 1                    |
| 2: Session & Registry | T2.1, T2.2, T2.3 | 75 min           | 1                    |
| 3: Atomic Ops         | T3.1, T3.2, T3.3 | 65 min           | 1                    |
| 4: Validation & CLI   | T4.1, T4.2       | 55 min           | 1                    |
| 5: Testing            | T5.1, T5.2       | 70 min           | 2                    |
| 6: Docs               | T6.1, T6.2       | 35 min           | 1                    |
| **Total**             | **11 tasks**     | **~350 min**     | **~7 days** (serial) |
| **Parallel**          | Groups by phase  | **~2 hrs/phase** | **~3-4 days**        |

## Definition of Done

- [ ] All code passes linting (ruff, mypy)
- [ ] Unit test coverage ≥85%
- [ ] Integration tests pass on macOS, Linux, Windows
- [ ] All CLI commands working and documented
- [ ] Documentation complete and reviewed
- [ ] Feature merged to main
- [ ] WORK_STREAM.md incorporator updated
- [ ] Agent developers trained

---

## Dependency Graph (DAG)

```
T1.1 (Detect OS/Arch)
  ├─→ T1.2 (Tool Detection)
  ├─→ T1.3 (Memory/Disk/GPU)
  └─→ T1.4 (Data Model) ──→ T2.1 (Constraint Matching) ──→ T3.1 (Dispatch)
        └─→ T2.3 (Registry) ──→ T3.1
                  ├─→ T3.2 (Integration)
                  ├─→ T3.3 (CLI)
                  ├─→ T4.1 (MCP)
                  └─→ T4.2 (Decorators)

T5.1 (Unit Tests) ──→ T5.2 (Integration Tests) ──→ T5.3 (Multi-Platform CI)
T6.1 (Agent Guide), T6.2 (Registry Docs), T6.3 (Architecture)
T7.1 (Review & Merge) ──→ T7.2 (Handoff)
```

---

## Timeline

| Phase                    | Days   | Start     | End        | Status      |
| ------------------------ | ------ | --------- | ---------- | ----------- |
| 1: Detection             | 2      | Day 1     | Day 2      | Pending     |
| 2: Constraint & Registry | 2      | Day 3     | Day 4      | Pending     |
| 3: Dispatch              | 2      | Day 5     | Day 6      | Pending     |
| 4: MCP Integration       | 1      | Day 7     | Day 7      | Pending     |
| 5: Testing               | 2      | Day 8     | Day 9      | Pending     |
| 6: Documentation         | 1      | Day 10    | Day 10     | Pending     |
| 7: Integration           | 1      | Day 11    | Day 11     | Pending     |
| **Total**                | **11** | **Day 1** | **Day 11** | **Pending** |

**Wall-clock with parallel agents**: ~6-7 days (agents A-E working in parallel)

---

## Definition of Done

- [ ] All code passes linting (ruff, mypy, type checks)
- [ ] Unit test coverage ≥80%
- [ ] Integration tests pass on ≥2 platforms
- [ ] Multi-platform CI matrix green
- [ ] Documentation complete and reviewed
- [ ] No outstanding review comments
- [ ] Feature merged to main branch
- [ ] Agent developers notified and trained
- [ ] Capability discovered in real agent usage (post-launch)

---

## Risk Mitigation

| Risk                              | Mitigation                                    |
| --------------------------------- | --------------------------------------------- |
| Tool detection too slow           | Parallel detection, cache TTL, lazy detection |
| False positives in tool detection | Version validation, smoke tests               |
| Cross-platform quirks             | Comprehensive test matrix, community feedback |
| Agent adoption friction           | Simple decorator, clear docs, examples        |

---

## Success Metrics

- [ ] Dispatch decisions made in <100ms p95
- [ ] 100% of new agents declare platform constraints
- [ ] 95%+ dispatch success rate on multi-platform matrix
- [ ] Zero manual platform workarounds in CI/CD
- [ ] Fallback strategies cover 80%+ of tool unavailability scenarios

---

## Rollback Plan

If issues arise:

1. Disable dispatch for tasks without constraints (use all executors)
2. Keep fallback registry but skip constraint validation
3. Disable multi-platform CI temporarily
4. Root cause analysis and patch
5. Re-enable features incrementally

---

## Notes for Agents

- **Parallel execution**: T1.x and T2.x can run in parallel (dependencies only at phase boundaries)
- **Code review**: Each phase should have code review before next phase starts
- **Testing as you go**: Unit tests alongside implementation, not after
- **Documentation**: Docs should be written during implementation, not as afterthought
- **Communication**: Log progress to CONVERSATION_DUMP daily

---

## Contact & Escalation

- **Technical Lead**: thegent core team
- **Blockers**: File issue in escalation queue (`docs/reference/ESCALATION_QUEUE.md`)
- **Questions**: Post to `docs/research/CONVERSATION_DUMP_YYYY-MM-DD.md`
