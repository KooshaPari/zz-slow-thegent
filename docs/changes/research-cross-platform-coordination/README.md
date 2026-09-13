# Cross-Platform Coordination Research – Master Index

**Research ID**: `RESEARCH-CPlatform-001`
**Status**: Approved for Implementation
**Last Updated**: 2026-02-18
**Research Track**: Infrastructure / Agent Orchestration

---

## Overview

This research initiative addresses the gap in **coordinating multi-platform agent execution** across macOS, Linux, and Windows. As the agent swarm scales, we need unified capability detection, constraint-based dispatch, and graceful fallback strategies.

**Outcome**: A platform-aware task dispatch system that enables heterogeneous infrastructure (cloud CI, local dev, hybrid deployments) with zero manual configuration.

---

## Documents in This Research Package

### 1. **proposal.md** – Strategic Vision

- **Purpose**: Define problem, success criteria, business value
- **Audience**: Stakeholders, decision-makers
- **Key Sections**:
  - Problem statement and risks
  - Success criteria and deliverables
  - Timeline and resource estimate
  - Next steps and kickoff
- **Status**: Approved ✓

### 2. **design.md** – Technical Architecture

- **Purpose**: Detailed architecture, data models, algorithms, integration points
- **Audience**: Architects, implementers, code reviewers
- **Key Sections**:
  - Component breakdown (detector, registry, dispatcher, fallbacks)
  - Data structures and APIs
  - Integration points (CLI, MCP, decorators)
  - Error handling and diagnostics
  - Testing strategy and rollout plan
- **Status**: Ready for implementation ✓

### 3. **tasks.md** – Implementation Roadmap

- **Purpose**: Work breakdown, task list, dependencies, timeline
- **Audience**: Implementers, project coordinators
- **Key Sections**:
  - 7 phases with detailed tasks
  - Dependency DAG
  - Task estimates and owners
  - Definition of done
  - Risk mitigation
- **Status**: Ready for dispatch ✓

---

## Quick Reference

| Question               | Answer                                             | Link                          |
| ---------------------- | -------------------------------------------------- | ----------------------------- |
| What are we building?  | Platform-aware dispatch system                     | proposal.md §1                |
| Why do we need it?     | Multi-platform agents need constraints             | proposal.md §2                |
| How does it work?      | Detect → Registry → Dispatch → Fallback            | design.md §1                  |
| What do I build first? | Platform detector module                           | tasks.md §Phase 1             |
| How long will it take? | ~2-3 weeks wall-clock (parallel agents)            | proposal.md §4                |
| What are the risks?    | Detection slowness, tool detection false positives | design.md §Risk & Mitigations |

---

## Getting Started

### For Stakeholders

1. Read **proposal.md** – Problem, vision, success criteria
2. Review success metrics and timeline
3. Approve or request adjustments
4. Sign off on resource allocation

### For Architects & Tech Leads

1. Read **design.md** – Full architecture overview
2. Review data models, algorithms, integration points
3. Identify any design gaps or concerns
4. Coordinate with adjacent systems (MCP, CLI)

### For Implementers

1. Read **tasks.md** – Full task breakdown
2. Review phases, dependencies, estimates
3. Pick a task or phase to start
4. Follow the DAG to maintain dependencies
5. Log progress to CONVERSATION_DUMP

---

## Key Architectural Decisions

| Decision                           | Rationale                       | Tradeoff                                          |
| ---------------------------------- | ------------------------------- | ------------------------------------------------- |
| In-memory cache + disk persistence | Fast lookups, survives restarts | ~50MB disk space                                  |
| 1-hour TTL by default              | Balance freshness vs. overhead  | Manual refresh available                          |
| Tool substitution fallbacks        | Graceful degradation            | May lose functionality                            |
| Decorator + YAML syntax            | Multiple API styles             | Learning curve                                    |
| CLI + MCP + Programmatic APIs      | Multiple use cases              | Code duplication risk (mitigated via shared core) |

---

## Integration Touchpoints

```
┌─ proposal.md (Strategic)
├─ design.md (Technical)
│  ├─ Platform Detector
│  ├─ Capability Registry (integrates with MCP, CLI)
│  ├─ Dispatch Logic (integrates with thegent run/bg)
│  ├─ Fallback Strategies
│  └─ Error Diagnostics
├─ tasks.md (Operational)
│  ├─ Phase 1-2: Core (Detector, Registry, Constraints)
│  ├─ Phase 3: Dispatch (CLI, Integration)
│  ├─ Phase 4: MCP Tools & Decorators
│  ├─ Phase 5: Testing (Unit, Integration, Multi-platform)
│  ├─ Phase 6: Documentation
│  └─ Phase 7: Merge & Handoff
└─ README.md (This file – Index & Overview)
```

---

## Workstream Items

After approval, the following items should be added to `WORK_STREAM.md`:

1. **research-platform-detection** – Implement capability detector (Phase 1, T1.1-1.4)
2. **research-platform-registry** – Build registry and constraints (Phase 2, T2.1-2.3)
3. **research-platform-dispatch** – Implement dispatch orchestrator (Phase 3, T3.1-3.3)
4. **research-platform-mcp** – Add MCP tools and decorators (Phase 4, T4.1-4.2)
5. **qa-platform-coordination** – Multi-platform testing (Phase 5, T5.1-5.3)
6. **docs-platform-guide** – Documentation and guides (Phase 6, T6.1-6.3)
7. **integrate-platform-coordination** – Code review and merge (Phase 7, T7.1-7.2)

---

## Success Metrics (Post-Launch)

- [ ] **Dispatch Performance**: <100ms p95 decision time
- [ ] **Coverage**: 100% of new agents declare platform constraints
- [ ] **Reliability**: 95%+ dispatch success rate on multi-platform matrix
- [ ] **Automation**: Zero manual platform workarounds in CI/CD
- [ ] **Resilience**: Fallback strategies cover 80%+ of tool unavailability scenarios
- [ ] **Adoption**: Observed in real agent usage within 2 weeks of launch

---

## Knowledge Map

**Related Documents**:

- `docs/guides/PLATFORM_COMPATIBILITY_GUIDE.md` – Agent developer guide (post-launch)
- `docs/reference/PLATFORM_CAPABILITY_REGISTRY.md` – Tool catalog (post-launch)
- `docs/reference/PLATFORM_ARCHITECTURE.md` – Architecture deep-dive (post-launch)

**Related Systems**:

- **MCP Server** – Capability registry exposed via resources/tools
- **CLI** – `thegent platform *` commands
- **Task Dispatch** – `thegent run`, `thegent bg` integrate dispatch
- **Agent Decorators** – `@PlatformConstraint` decorator

**Related Research**:

- Multi-platform CI/CD (separate initiative)
- Agent capability introspection (related, not blocking)
- Environment capability discovery (related, overlaps partially)

---

## Approval & Sign-Off

| Role           | Name         | Status  | Date |
| -------------- | ------------ | ------- | ---- |
| Product Owner  | thegent team | Pending | —    |
| Technical Lead | thegent team | Pending | —    |
| Architect      | thegent team | Pending | —    |

---

## Session Continuity

**For hand-off to next agent/session**:

1. Read this README first
2. Pick a phase or task from tasks.md
3. Check dependencies (DAG in tasks.md §Phase 1-7)
4. Reference design.md for technical details
5. Log progress to `docs/research/CONVERSATION_DUMP_YYYY-MM-DD.md`

**Cursor/Codex recovery**:

- If session crashes, find prior session logs in `.thegent/sessions/`
- Export via `thegent prompts dump <session_id>`
- Merge findings into CONVERSATION_DUMP

---

## Notes for Implementers

- **Code quality**: All code must pass ruff, mypy, tests
- **Documentation**: Write docs during implementation, not after
- **Testing**: Unit tests alongside code, integration tests in Phase 5
- **Communication**: Daily updates to CONVERSATION_DUMP
- **Review**: Each phase should have code review before next phase
- **Parallelization**: Phases 1-2 and 4-5 can run in parallel after Phase 3 foundations

---

## Revision History

| Version | Date       | Author           | Changes                                 |
| ------- | ---------- | ---------------- | --------------------------------------- |
| 1.0     | 2026-02-18 | Agent Researcher | Initial draft (proposal, design, tasks) |

---

## Contact & Escalation

- **Questions**: Add to CONVERSATION_DUMP or post issue in escalation queue
- **Blockers**: Escalate to thegent tech lead
- **Updates**: Revision to this README should be made after each phase completes

---

## Appendix: Quick Links

- [Proposal – Full Problem & Vision](proposal.md)
- [Design – Technical Architecture](design.md)
- [Tasks – Work Breakdown & Timeline](tasks.md)
- [Agent Developer Guide](../../../guides/PLATFORM_COMPATIBILITY_GUIDE.md) _(post-launch)_
- [Capability Registry](../../../reference/PLATFORM_CAPABILITY_REGISTRY.md) _(post-launch)_

---

**Last Updated**: 2026-02-18
**Next Review**: After Phase 2 (Day 4)
**Archive**: Move to `docs/changes/archive/` when complete
