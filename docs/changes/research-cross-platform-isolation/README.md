# Cross-Platform User Isolation Research & Implementation Package

**Status**: Research Complete → Implementation Planning
**Date**: 2026-02-18
**Total Lines of Documentation**: 1100+
**Phase Duration**: 5-6 weeks

---

## Overview

This change directory contains the complete specification and implementation roadmap for **cross-platform user isolation** in thegent, enabling secure multi-tenant agent execution across macOS, Linux, and Windows.

### Key Decision: Hybrid Isolation Model

- **Sub-User (Default)**: Process-level isolation, zero permissions, ~1ms overhead
- **OS User (Opt-In)**: Full OS-level isolation, admin setup required, ~50ms overhead
- **Docker (Future)**: Container-based isolation for Phase 13+

---

## Documents

### 1. **proposal.md** (214 lines)

**Purpose**: High-level overview, problem statement, and scope

**Contents**:

- Problem: Current lack of tenant-aware isolation mechanisms
- Solution: Hybrid isolation model with file & desktop coordination
- Scope: What's included (sub-user, OS user, desktop coordinator, etc.) and excluded (containers, network isolation)
- Architecture decision: Why hybrid model over alternatives
- Success criteria & acceptance criteria
- Implementation roadmap (5 phases, 5-6 weeks)
- Risk & mitigation matrix

**Audience**: Decision makers, architects, product managers

### 2. **design.md** (378 lines)

**Purpose**: Technical architecture and detailed design specifications

**Contents**:

- System architecture diagram (isolation modes, coordinators, providers)
- Sub-user isolation implementation (lightweight, no permissions)
- OS user isolation design (full separation, admin setup)
- File-level coordination (edit lease manager with tenant awareness)
- Desktop automation coordinator (action queueing, scheduling, retry)
- User activity detection (macOS/Linux/Windows platform detection)
- Configuration reference (all options documented)
- Performance characteristics & latency budgets
- Testing checklist (per phase)
- Rollback & safety procedures

**Key Sections**:

- 1: System architecture (core components)
- 2-3: Isolation modes
- 4: File coordination (leases)
- 5-6: Desktop automation
- 7-10: Config, performance, testing, safety

**Audience**: Implementation engineers, architects

### 3. **tasks.md** (525 lines)

**Purpose**: Detailed task breakdown, milestones, and acceptance criteria

**Contents**:

- Phase 1 (Weeks 1-2): Sub-User Isolation (5 tasks)
  - Infrastructure, provider implementation, tests, executor integration, config
- Phase 2 (Week 3): Edit Lease Manager (4 tasks)
  - Refactoring, conflict detection, lock files, tests
- Phase 3 (Weeks 4-5): Desktop Coordinator (12 tasks)
  - Coordinator core, activity detection, platform providers (macOS/Linux/Windows)
- Phase 4 (Week 6): OS User Isolation (4 tasks)
  - Provider implementation, user creation, sudoers, CLI helpers
- Phase 5 (Weeks 7-8): Integration & Hardening (7 tasks)
  - Audit logging, concurrency control, benchmarking, security tests, documentation

**Format**: Each task includes:

- Task ID (e.g., 1.2.1)
- Objective (what to build)
- Acceptance criteria (how to verify done)
- Estimated LOC (for implementation-heavy tasks)

**Total Tasks**: 32+ across all phases
**Total LOC**: ~3700 lines of implementation code

**Audience**: Engineers, project managers, task tracking

---

## How to Use This Package

### For Project Planning

1. Read **proposal.md** to understand scope & decisions
2. Review **tasks.md** summary table (Phase | Tasks | Est. Week)
3. Create project timeline (5-6 weeks) & resource allocation

### For Implementation

1. Read **design.md** for technical approach
2. Follow **tasks.md** phase by phase
3. Each task has explicit acceptance criteria
4. Tests validate each task completion
5. Run full regression test suite at Phase 5

### For Stakeholder Communication

- **Executives**: proposal.md (scope, timeline, risk/mitigation)
- **Architects**: design.md (system design, components, interfaces)
- **Engineers**: tasks.md + design.md (detailed specs & implementation guide)
- **QA**: tasks.md (testing strategy, acceptance criteria per phase)

---

## Key Metrics & Targets

### Functional Requirements

| Requirement                            | Target               | Verification                         |
| -------------------------------------- | -------------------- | ------------------------------------ |
| Sub-user isolation configurable        | Yes                  | `isolation_mode: "sub-user"`         |
| OS user isolation configurable         | Yes                  | `isolation_mode: "os-user"`          |
| Desktop automation coordinator works   | 95%+ no UI conflicts | Performance tests, manual validation |
| Edit leases work cross-platform        | 100%                 | Unit tests + integration tests       |
| Per-tenant concurrency limits enforced | Yes                  | Concurrency controller tests         |

### Non-Functional Requirements (SLAs)

| Operation              | Latency (p95) | Success Rate |
| ---------------------- | ------------- | ------------ |
| Sub-user allocation    | <1ms          | >99%         |
| Lease acquire          | <50ms         | >95%         |
| Desktop action execute | <200ms        | >95%         |
| User activity check    | <50ms         | >99%         |

### Test Coverage

| Phase     | Unit Tests | Integration | E2E     | Total   |
| --------- | ---------- | ----------- | ------- | ------- |
| Phase 1   | 8          | 2           | -       | 10      |
| Phase 2   | 9          | 3           | -       | 12      |
| Phase 3   | 9          | 6           | 5+      | 20+     |
| Phase 4   | 4          | 4           | -       | 8       |
| Phase 5   | -          | -           | 5+      | 5+      |
| **Total** | **30+**    | **15+**     | **10+** | **55+** |

---

## Dependencies & Prerequisites

### External Libraries

- **macOS**: AppleScript (built-in)
- **Linux**: AT-SPI or xdotool (optional)
- **Windows**: pywinauto (new dependency)
- **Cross-platform**: No breaking new dependencies for sub-user mode

### System Permissions

- **Sub-user mode**: None required
- **OS user mode**: `sudo` or `doas` with NOPASSWD sudoers config

### Development Environment

- Python 3.9+ (async/await support)
- pytest + asyncio for testing
- All three platforms (macOS/Linux/Windows) for full testing (optional: can test one platform at a time)

---

## Timeline & Phases

```
Week 1-2: Sub-User Isolation
├─ Infrastructure setup
├─ Provider implementation
├─ Unit tests (8+)
└─ Executor integration

Week 3: Edit Lease Manager
├─ Lease refactoring
├─ Conflict detection
├─ Lock file management
└─ Unit + integration tests (9+)

Week 4-5: Desktop Coordinator (CRITICAL PATH)
├─ Coordinator core
├─ User activity detection
├─ macOS provider (AppleScript)
├─ Linux provider (AT-SPI/xdotool)
├─ Windows provider (UI Automation)
└─ Tests (15+)

Week 6: OS User Isolation
├─ Provider implementation
├─ User creation & sudoers
├─ Helper CLI commands
└─ Tests (8+)

Week 7-8: Integration & Hardening
├─ Audit logging
├─ Concurrency controller
├─ Performance benchmarking
├─ Security tests
├─ Documentation
└─ Regression testing (all existing tests)

Total: 5-6 weeks, 32+ tasks
```

---

## Dependency Management

### Within thegent

- `research-cross-platform-isolation` (this): **No dependencies**, can start immediately
- `research-cross-platform-coordination`: **Depends on this** (multi-tenant coordination policies)
- `research-phase13-tenant-boundary-tests`: **Depends on this** (testing & validation)

### Blocking Dependencies

None. This research can proceed in parallel with other Phase 10-12 work.

---

## Risk Summary & Mitigation

| Risk                             | Likelihood | Impact   | Mitigation                                                |
| -------------------------------- | ---------- | -------- | --------------------------------------------------------- |
| **Cross-tenant data leaks**      | Medium     | Critical | Penetration tests, audit logging, code review             |
| **OS user isolation complexity** | Medium     | High     | Clear documentation, helper scripts, CI tests             |
| **Desktop automation flakiness** | Medium     | High     | Extensive testing, fallback behaviors, activity detection |
| **Performance regression**       | Low        | Medium   | Benchmarking, overhead budgets per phase                  |
| **Platform-specific bugs**       | Medium     | Medium   | Three separate provider implementations, test matrix      |

**Overall Risk**: Moderate (mitigable with discipline)

---

## Success Definition

**Phase 5 Completion Criteria**:

- [ ] All 32+ tasks completed & tested
- [ ] 55+ tests pass (unit, integration, E2E)
- [ ] Zero regressions in existing codebase
- [ ] Performance SLAs met (latency, success rate)
- [ ] Security tests pass (cross-tenant isolation verified)
- [ ] Audit logging complete
- [ ] Documentation complete (deployment, troubleshooting, examples)
- [ ] Code review approved by senior architect
- [ ] Ready for release & production deployment

---

## References & Related Work

### In This Directory

- `proposal.md` - High-level overview
- `design.md` - Technical architecture
- `tasks.md` - Detailed task breakdown

### In thegent Repository

- `docs/research/CROSS_PLATFORM_RESEARCH_CONSOLIDATED.md` - Full research base
- `docs/reference/WORK_STREAM.md` - Work stream integration
- `docs/plans/02-UNIFIED-WBS.md` - WBS integration
- `FUNCTIONAL_REQUIREMENTS.md` - FR traceability (if applicable)

### Related Changes

- Phase 10-12 work stream (concurrent)
- Multi-tenant coordination (Phase 11+, depends on this)
- Tenant boundary tests (Phase 13+, depends on this)

---

## Document Maintenance

**Last Updated**: 2026-02-18
**Version**: 1.0 (Initial synthesis from research)
**Owner**: Research & Architecture team
**Review Cadence**: Monthly during implementation

**To Update**:

1. Modify relevant section (proposal/design/tasks)
2. Update "Last Updated" date
3. Increment version (x.y → x.(y+1))
4. Commit with message: "docs: update cross-platform-isolation/{proposal,design,tasks}"

---

## Quick Navigation

- **Need timeline?** → See "Timeline & Phases" above
- **Need task list?** → tasks.md "Summary: Task Checklist" table
- **Need architecture?** → design.md "System Architecture"
- **Need success criteria?** → proposal.md "Success Criteria"
- **Need test strategy?** → tasks.md "Phase X (X.Y Testing)" sections
- **Need config examples?** → design.md "Configuration Reference"

---

**Generated**: 2026-02-18
**Package Completeness**: 100% (proposal + design + tasks)
**Ready for**: Implementation kickoff
