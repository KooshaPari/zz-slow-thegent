# Cross-Platform User Isolation Implementation - Proposal

**Date**: 2026-02-18
**Status**: Research Complete → Implementation Planning
**Source**: `CROSS_PLATFORM_RESEARCH_CONSOLIDATED.md`

---

## 1. Executive Summary

This proposal outlines the implementation strategy for **cross-platform user isolation** in thegent, enabling secure multi-tenant agent execution across macOS, Linux, and Windows.

### 1.1 Problem Statement

Current thegent architecture lacks tenant-aware isolation mechanisms, creating risk when:

- Multiple agents execute concurrently
- Untrusted agents must be sandboxed
- Production deployments require strong isolation guarantees
- Desktop automation conflicts arise from concurrent UI actions

### 1.2 Proposed Solution

**Hybrid User Isolation Model**:

- **Default (Development)**: Sub-user isolation (process-level, no permissions required)
- **Opt-in (Production)**: OS user isolation (full OS-level separation, requires admin)
- **Future (Enterprise)**: Container-based isolation (Docker/systemd-nspawn)

**Multi-Tenant Coordination**:

- File-level: Tenant-aware edit leases
- UI Automation: Desktop automation coordinator with activity detection
- Process: Tenant-aware concurrency limits

---

## 2. Scope & Scale

### 2.1 What's Included

| Component                          | Scope                                             | Effort     |
| ---------------------------------- | ------------------------------------------------- | ---------- |
| **Sub-user Isolation**             | Process-level user context, default mode          | M (Medium) |
| **OS User Isolation**              | Full OS user switching (sudoers config), optional | M          |
| **Desktop Automation Coordinator** | Multi-tenant UI action scheduling                 | L (Large)  |
| **Edit Lease Manager**             | Tenant-aware file locks                           | S (Small)  |
| **Concurrency Controller**         | Per-tenant execution limits                       | S          |
| **Cross-Platform Providers**       | macOS/Linux/Windows implementations               | L          |
| **Security & Compliance**          | Audit logging, capability enforcement             | M          |

### 2.2 What's Excluded (Future/Backlog)

- Container-based isolation (Phase 13+)
- Network isolation (separate VLAN/namespace)
- Encrypted inter-tenant communication channels
- Tenant-aware resource quotas (CPU, memory, disk)

---

## 3. Architecture Decision

### 3.1 User Isolation Hybrid Model

```
┌──────────────────────────────────────────────────┐
│         Thegent Multi-Tenant Architecture        │
├──────────────────────────────────────────────────┤
│                                                  │
│  ┌────────────────────────────────────────────┐ │
│  │  Sub-User Isolation (DEFAULT)              │ │
│  │  • Process-level context (uid/gid)         │ │
│  │  • No filesystem isolation                 │ │
│  │  • No permissions required                 │ │
│  │  • ~1ms overhead per action                │ │
│  └────────────────────────────────────────────┘ │
│                                                  │
│  ┌────────────────────────────────────────────┐ │
│  │  OS User Isolation (OPT-IN)                │ │
│  │  • Full OS-level isolation                 │ │
│  │  • Separate home, .config, .local          │ │
│  │  • Requires sudoers + doas/sudo config     │ │
│  │  • ~50ms overhead per action               │ │
│  └────────────────────────────────────────────┘ │
│                                                  │
│  ┌────────────────────────────────────────────┐ │
│  │  Docker Isolation (FUTURE - Phase 13+)     │ │
│  │  • Container-based full isolation          │ │
│  │  • Network namespace included              │ │
│  │  • ~500ms overhead per action              │ │
│  └────────────────────────────────────────────┘ │
│                                                  │
└──────────────────────────────────────────────────┘
```

### 3.2 Coordination Mechanisms

**File-Level Coordination**:

- Extend `EditLeaseManager` with tenant awareness
- File locks: `/run/thegent/leases/{tenant_id}/{hash(filepath)}.lock`
- Conflict resolution: User > Agent (FIFO for agent-agent)

**UI Automation Coordination**:

- Desktop Automation Coordinator monitors:
  - Current active window (user focus)
  - Pending agent actions (queue)
  - Desktop resource availability
- Scheduling: User actions preempt agents; agents batch by tenant

**Process Concurrency**:

- Per-tenant concurrency caps (configurable)
- Shared pool for user actions (unlimited priority)
- Escalation queue for backpressure

---

## 4. Key Design Decisions

| Decision                     | Rationale                                      | Trade-offs                       |
| ---------------------------- | ---------------------------------------------- | -------------------------------- |
| **Sub-user default**         | Fast, zero-permission, suitable for dev        | Less isolation than OS users     |
| **FIFO for agent conflicts** | Deterministic, simple, fair                    | No priority scheduling           |
| **Native desktop providers** | Platform-optimized, no dependencies            | Maintenance burden (3 platforms) |
| **Activity detection**       | Detect user focus; prevent agent UI collisions | Added latency/complexity         |
| **Hybrid model**             | Balance dev velocity with prod security        | Operational complexity           |

---

## 5. Success Criteria

### Functional Requirements

- [ ] Sub-user isolation configurable via `isolation_mode: "sub-user"`
- [ ] OS user isolation configurable via `isolation_mode: "os-user"`
- [ ] Desktop automation coordinator prevents 95%+ of UI conflicts
- [ ] Edit leases work across all 3 platforms
- [ ] Per-tenant concurrency limits enforced

### Non-Functional Requirements

- [ ] Isolation overhead: <5ms (sub-user), <100ms (OS user)
- [ ] Edit lease latency: <50ms (p95)
- [ ] Desktop automation decision latency: <200ms (p95)
- [ ] Success rate: >95% for isolated actions

### Compliance & Security

- [ ] Audit log: all tenant isolation events
- [ ] Capability matrix: document per-tenant capabilities
- [ ] Penetration test: attempt cross-tenant data access (fail expected)

---

## 6. Implementation Roadmap

### Phase 1: Sub-User Isolation (Weeks 1-2)

- Implement `SubUserIsolationProvider`
- Extend process execution to set uid/gid context
- Add config: `isolation_mode`, `sub_user_prefix`
- Tests: 10+ scenarios (file access, env vars, credentials)

### Phase 2: Edit Lease Manager Enhancement (Week 3)

- Extend `EditLeaseManager` with tenant ID tracking
- Implement file lock paths: `/run/thegent/leases/{tenant_id}/`
- Conflict detection & logging
- Tests: 5+ multi-tenant edit scenarios

### Phase 3: Desktop Automation Coordinator (Week 4-5)

- Implement `DesktopAutomationCoordinator`
- Platform providers: macOS (AppleScript), Linux (AT-SPI), Windows (UI Automation)
- User activity detection (window focus, active app)
- Action queue & scheduling logic
- Tests: 15+ scenarios (concurrency, preemption, user activity)

### Phase 4: OS User Isolation (Week 6)

- Implement `OSUserIsolationProvider`
- Sudoers config generator
- Test on macOS (doas), Linux (sudo), Windows (RunAs)
- Tests: 8+ scenarios (permissions, home directory, isolation)

### Phase 5: Integration & Hardening (Week 7-8)

- Wire isolation mode into agent executor
- Concurrency controller integration
- Audit logging, telemetry
- Documentation & troubleshooting
- Performance benchmarking (SLA verification)

---

## 7. Risk & Mitigation

| Risk                             | Impact   | Mitigation                                                |
| -------------------------------- | -------- | --------------------------------------------------------- |
| **Cross-tenant data leaks**      | Critical | Penetration tests, audit logging, code review             |
| **OS user isolation complexity** | High     | Clear documentation, helper scripts, CI tests             |
| **Desktop automation flakiness** | High     | Extensive testing, fallback behaviors, activity detection |
| **Performance regression**       | Medium   | Benchmarking, overhead budgets per phase                  |
| **Platform-specific bugs**       | Medium   | Three separate provider implementations, test matrix      |

---

## 8. Acceptance Criteria

**Definition of Done**:

1. All phases 1-5 implemented and tested
2. All success criteria (functional, non-functional, compliance) met
3. Documentation complete (design.md, deployment guide, troubleshooting)
4. Performance benchmarks meet SLAs
5. Security review passed
6. No test regressions in existing codebase

---

## References

- **Consolidated Research**: `docs/research/CROSS_PLATFORM_RESEARCH_CONSOLIDATED.md`
- **Work Stream Item**: `research-cross-platform-isolation` (P1, no dependencies)
- **Related Items**:
  - `research-cross-platform-coordination` (depends on this)
  - `research-phase13-tenant-boundary-tests` (depends on this)
