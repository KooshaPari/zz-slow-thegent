---
task_id: research-compute-offload
status: in_progress
---

# Implementation Tasks: Mac ↔ PC Compute Offload

**Document Version:** 1.0
**Change ID:** research-compute-offload
**Date:** 2026-02-18
**Status:** WIP
**Total Effort**: ~15 agent-days

---

## Phase 1: Research & Design (Week 1) — **Status: PLANNING**

### T1.1: Stakeholder Research & Requirements Gathering

- **Objective**: Interview thegent team and users; document use cases
- **Effort**: 1 agent-day
- **Owner**: (TBD)
- **Dependencies**: None
- **Deliverables**:
  - List of ≥3 real use cases (cross-platform workflows)
  - Network assumptions (LAN vs internet)
  - Security requirements (auth model, isolation level)
  - Integration preferences (when/where to offload)
- **Success Criteria**:
  - All stakeholders consulted
  - Requirements documented in design.md
  - Go/no-go decision made

### T1.2: Competitive Analysis

- **Objective**: Research similar systems (Kubernetes federation, Nomad, Temporal, Terraform)
- **Effort**: 1.5 agent-days
- **Owner**: (TBD)
- **Dependencies**: T1.1
- **Deliverables**:
  - Comparison matrix (protocol choice, registry model, routing)
  - Lessons learned doc
- **Success Criteria**:
  - ≥4 systems analyzed
  - Key patterns identified

### T1.3: Architecture & Protocol Design

- **Objective**: Design bridge protocol, compute catalog, routing logic
- **Effort**: 1.5 agent-days
- **Owner**: (TBD)
- **Dependencies**: T1.1, T1.2
- **Deliverables**:
  - Bridge protocol YAML spec (ExecutionRequest, ExecutionResponse)
  - Compute catalog JSON schema
  - Routing policy enumeration
  - Design decisions log (why HTTP vs gRPC, JSON vs Protobuf, etc.)
- **Success Criteria**:
  - Design.md complete with all sections
  - Protocol examples provided
  - All design decisions documented with rationale

---

## Phase 2: Prototype Implementation (Week 2-3) — **Status: PENDING**

### T2.1: Compute Catalog Module

- **Objective**: Implement `ComputeCatalog` + `CapabilityProfile` classes
- **Effort**: 1.5 agent-days
- **Owner**: (TBD)
- **Dependencies**: T1.3
- **Deliverables**:
  - `src/thegent/offload/compute_catalog.py` (400 LOC)
  - Unit tests (70% coverage)
  - Example catalog JSON file
- **Success Criteria**:
  - `ComputeCatalog` loads/saves JSON
  - Methods: `register_environment()`, `get_online_environments()`, `find_by_hostname()`
  - Tests: load, save, register, query
  - Example with ≥3 environments populated

### T2.2: Capability Resolver Module

- **Objective**: Implement `CapabilityResolver` for probing local environment
- **Effort**: 1.5 agent-days
- **Owner**: (TBD)
- **Dependencies**: T1.3, T2.1
- **Deliverables**:
  - `src/thegent/offload/capability_resolver.py` (300 LOC)
  - Tests for ≥10 capability types (python, node, rust, git, docker, etc.)
  - `CapabilityCache` with TTL
- **Success Criteria**:
  - Probes ≥15 tools/languages correctly
  - Cache TTL working (verified in unit tests)
  - Test pass rate ≥90%
  - Handles missing tools gracefully

### T2.3: Workload Classifier Module

- **Objective**: Implement `WorkloadClassifier` with ≥5 heuristics
- **Effort**: 2 agent-days
- **Owner**: (TBD)
- **Dependencies**: T1.3, T2.1
- **Deliverables**:
  - `src/thegent/offload/workload_classifier.py` (400 LOC)
  - Heuristics: language detect, framework detect, tool detect, OS-specific commands, dependency scanning
  - Tests for ≥5 workload types (Python, Swift, Node, Rust, .NET)
- **Success Criteria**:
  - Classify Python correctly in ≥3 example prompts
  - Detect Swift → prefer macOS
  - Detect xcodebuild → macOS only
  - Confidence scores 0.5-1.0 range
  - Edge case: empty prompt returns default classification

### T2.4: Offload Router Module

- **Objective**: Implement `OffloadRouter` with ≥3 routing policies
- **Effort**: 1.5 agent-days
- **Owner**: (TBD)
- **Dependencies**: T1.3, T2.1, T2.3
- **Deliverables**:
  - `src/thegent/offload/offload_router.py` (300 LOC)
  - Policies: `COST_OPTIMAL`, `LATENCY_OPTIMAL`, `CAPABILITY_OPTIMAL`
  - Tests: verify correct route selection per policy
- **Success Criteria**:
  - Route selection respects policy
  - Returns reason for routing decision
  - Handles "no suitable environment" gracefully
  - Cost scoring accurate (vs mock catalog)

### T2.5: Bridge Protocol Module

- **Objective**: Define `ExecutionRequest` + `ExecutionResponse` Pydantic models
- **Effort**: 1 agent-day
- **Owner**: (TBD)
- **Dependencies**: T1.3
- **Deliverables**:
  - `src/thegent/offload/bridge_protocol.py` (200 LOC)
  - Pydantic models with validators
  - JSON schema generation
  - Example payloads for ≥3 workflows
- **Success Criteria**:
  - Models validate correctly
  - JSON schema can be generated
  - Round-trip serialization works (dict → model → dict)
  - Examples provided in docstrings

### T2.6: Remote Executor Server

- **Objective**: Implement FastAPI-based remote executor
- **Effort**: 2.5 agent-days
- **Owner**: (TBD)
- **Dependencies**: T2.5, T2.2
- **Deliverables**:
  - `src/thegent/offload/remote_executor.py` (500 LOC)
  - Endpoints: POST `/v1/offload/execute`, GET `/v1/health`
  - Subprocess execution in sandbox
  - Cost estimation + token counting
  - Tests: mock subprocess, validate response
- **Success Criteria**:
  - Server starts and listens on 0.0.0.0:9000
  - Health check returns 200
  - Execute endpoint receives request, returns response
  - Timeout handling (subprocess.TimeoutExpired)
  - Cost computation plausible

### T2.7: Offload Client Module

- **Objective**: Implement `OffloadClient` for invoking remote executor
- **Effort**: 1 agent-day
- **Owner**: (TBD)
- **Dependencies**: T2.5, T2.6
- **Deliverables**:
  - `src/thegent/offload/offload_client.py` (150 LOC)
  - Async HTTP client using `httpx`
  - Methods: `execute()`, `health_check()`
  - Error handling + retry logic
- **Success Criteria**:
  - Sends valid ExecutionRequest
  - Parses ExecutionResponse
  - Handles 200/error responses
  - Health check returns bool

### T2.8: Integration with thegent Agent Runner

- **Objective**: Wire offload into `AgentRunner.run()` decision logic
- **Effort**: 2 agent-days
- **Owner**: (TBD)
- **Dependencies**: T2.1-T2.7
- **Deliverables**:
  - Modify `src/thegent/agent_runner.py` to support offload
  - Add offload settings to `ThegentSettings`
  - Feature flag: `THGENT_OFFLOAD_ENABLED`
  - Fallback flow (offload fails → run locally)
- **Success Criteria**:
  - Feature flag works (enabled/disabled)
  - Offload only attempted if enabled
  - Fallback to local execution on error
  - Logging for offload decisions
  - ≥80% test coverage for new code

### T2.9: Unit Tests & Coverage

- **Objective**: Achieve ≥70% coverage across all offload modules
- **Effort**: 2 agent-days
- **Owner**: (TBD)
- **Dependencies**: T2.1-T2.8
- **Deliverables**:
  - `tests/thegent/offload/` test suite
  - Mock catalog, mock executor, mock HTTP client
  - Positive + negative test cases
  - Coverage report (CI integration optional)
- **Success Criteria**:
  - Overall coverage ≥70%
  - All modules have unit tests
  - Test pass rate 100%
  - No lint violations (ruff, mypy)

---

## Phase 3: Validation & Documentation (Week 3) — **Status: PENDING**

### T3.1: End-to-End Offload Workflow Test

- **Objective**: Deploy prototype to 2+ environments (Mac + Linux VM); validate real offload
- **Effort**: 2 agent-days
- **Owner**: (TBD)
- **Dependencies**: T2.1-T2.9
- **Deliverables**:
  - Populate compute catalog with 2+ test environments
  - Execute ≥3 real tasks (Python repo analysis, Node hello world, Rust compilation check)
  - Measurement: latency, cost, success rate
  - Log real offload decisions + outcomes
- **Success Criteria**:
  - ≥3 tasks successfully offloaded and executed on remote
  - Success rate ≥90% (2 out of ≥3 tasks succeed)
  - Latency < 5s per task (classification + routing + execution)
  - Output from remote executor matches expected format

### T3.2: Runbook & Setup Documentation

- **Objective**: Write step-by-step guide for deploying offload infrastructure
- **Effort**: 1.5 agent-days
- **Owner**: (TBD)
- **Dependencies**: T3.1
- **Deliverables**:
  - `docs/changes/research-compute-offload/runbook.md` (2000+ words)
  - Sections:
    - Prerequisites (ports, network, auth)
    - Install thegent on each environment
    - Register environments in catalog
    - Start remote executor servers
    - Configure client (settings, feature flags)
    - Test offload workflow (manual step-by-step)
    - Troubleshooting common issues
- **Success Criteria**:
  - New user can follow runbook start-to-finish
  - Includes ≥5 troubleshooting scenarios
  - Commands copy-pastable

### T3.3: Findings & Decision Document

- **Objective**: Synthesize research findings; propose next steps
- **Effort**: 1 agent-day
- **Owner**: (TBD)
- **Dependencies**: T3.1, T3.2
- **Deliverables**:
  - Update `design.md` with findings section:
    - What worked well
    - Unexpected challenges
    - Performance characteristics
    - Answers to all 10 research questions
  - Production readiness assessment (yes/no/needs_work)
  - Recommendations for Phase 13+ (if pursuing production)
- **Success Criteria**:
  - All 10 research questions answered (yes/no/maybe)
  - Go/no-go recommendation clear
  - Next phase roadmap provided

### T3.4: Code Quality & Documentation

- **Objective**: Add docstrings, type hints, and comments to all code
- **Effort**: 1 agent-day
- **Owner**: (TBD)
- **Dependencies**: T2.1-T2.9
- **Deliverables**:
  - Docstrings for all public classes + methods
  - Type hints for all function parameters + returns
  - README.md in `src/thegent/offload/` explaining module purpose
  - Inline comments for non-obvious logic
- **Success Criteria**:
  - Sphinx can generate API docs without errors
  - Type coverage ≥90% (mypy check)
  - No linting violations (ruff, pylint)

---

## Phase 4: Decision & Handoff (End of Week 3) — **Status: PENDING**

### T4.1: Presentation & Stakeholder Review

- **Objective**: Present prototype and findings to thegent team
- **Effort**: 0.5 agent-day
- **Owner**: (TBD)
- **Dependencies**: T3.1-T3.4
- **Deliverables**:
  - Slide deck (≥10 slides): architecture, prototype results, findings, decision matrix
  - Live demo (if possible) or recorded walkthrough
  - Q&A response document
- **Success Criteria**:
  - Stakeholders understand design + tradeoffs
  - Go/no-go decision made
  - Path forward clear (produce, archive, extend)

### T4.2: Code Archival & Handoff

- **Objective**: Clean up prototype; mark as @experimental; prepare for handoff or merging
- **Effort**: 1 agent-day
- **Owner**: (TBD)
- **Dependencies**: T3.4
- **Deliverables**:
  - Mark all code `@experimental` (docstring decorator)
  - Add `OFFLOAD_README.md` with disclaimer (research-stage)
  - Commit to feature branch `research/compute-offload`
  - PR with summary: scope, what worked, what didn't, recommendations
- **Success Criteria**:
  - Code is clean, well-documented, and reviewable
  - PR has clear summary
  - All tests passing
  - No tech debt TODOs (document as future work)

### T4.3: Lessons Learned & Future Roadmap

- **Objective**: Update docs/research/CONVERSATION*DUMP*\*.md with findings
- **Effort**: 0.5 agent-day
- **Owner**: (TBD)
- **Dependencies**: T3.3
- **Deliverables**:
  - `docs/research/CONVERSATION_DUMP_2026-02-18_OFFLOAD.md`:
    - Issues addressed
    - Findings (yes to all research questions? trade-offs?)
    - Prototype artifacts (code location, test results)
    - Open questions (for future research)
    - Recommendations (pursue production? archive?)
- **Success Criteria**:
  - Document provides clear context for future developer picking up this work

---

## Dependency Graph (DAG)

```
T1.1 (Stakeholder Research)
  ↓
T1.2 (Competitive Analysis)
  ↓
T1.3 (Design)
  ├─→ T2.1 (Catalog Module)
  │     ├─→ T2.3 (Classifier) ─→ T2.4 (Router)
  │     └─→ T2.8 (Integration)
  │
  ├─→ T2.2 (Capability Resolver) ─→ T2.6 (Remote Executor) ─→ T2.8
  │
  └─→ T2.5 (Bridge Protocol) ─→ T2.6 (Remote Executor) ─→ T2.7 (Client) ─→ T2.8

T2.1-T2.8 (all) ─→ T2.9 (Unit Tests) ─→ T3.1 (E2E Validation) ─→ T3.2 (Runbook)

T3.1, T3.2 ─→ T3.3 (Findings) ─→ T4.1 (Presentation)

T2.1-T2.9, T3.3 ─→ T3.4 (Code Quality) ─→ T4.2 (Handoff)

T4.1, T4.2 ─→ T4.3 (Lessons Learned)
```

**Critical Path**: T1.1 → T1.2 → T1.3 → T2.{1-8} → T2.9 → T3.1 → T3.2 → T3.3 → T4.1 (**~13 days**)

**Parallel Tracks**:

- T2.1, T2.2, T2.5 can start immediately after T1.3
- T2.3, T2.4 can start after T2.1
- T2.6, T2.7 can start after T2.5
- T3.4 (docs) can start after T2.9

---

## Success Metrics

| Metric                     | Target                              | Validation                     |
| -------------------------- | ----------------------------------- | ------------------------------ |
| **Prototype Completeness** | All 7 modules implemented           | Code review + tests passing    |
| **Test Coverage**          | ≥70%                                | `pytest --cov` report          |
| **E2E Validation**         | ≥3 tasks offloaded successfully     | Manual testing + logs          |
| **Performance**            | <5s offload latency per task        | Measured during T3.1           |
| **Documentation**          | Design + runbook + lessons learned  | Reader can follow from scratch |
| **Code Quality**           | No lint/type errors; ≥8/10 readable | ruff + mypy + review           |
| **Research Questions**     | All 10 answered                     | Section in findings doc        |

---

## Risk Mitigation

| Risk                                      | Probability | Impact                  | Mitigation                                                         |
| ----------------------------------------- | ----------- | ----------------------- | ------------------------------------------------------------------ |
| Network unreliability                     | Medium      | Task timeouts           | Add configurable timeouts; test on LAN only                        |
| Integration complexity with policy engine | Medium      | Schedule slip           | Simplify policy integration; iterate later                         |
| Workload classification mismatches        | Medium      | Wrong platform selected | Start simple; add logging to collect misclassifications            |
| Prototype becomes "tech debt"             | Low         | Maintenance burden      | Mark @experimental; clear handoff doc; no promises                 |
| Stakeholder skepticism                    | Low         | Scope reduction         | Manage expectations early (research-stage); show working prototype |

---

## Resource Allocation

**Total Effort**: ~15 agent-days

**Suggested Allocation** (if 2 agents assigned):

- **Agent A** (Infrastructure): T1.1, T2.1, T2.2, T2.5, T2.6, T3.1 (8 days)
- **Agent B** (Logic): T1.2, T1.3, T2.3, T2.4, T2.7, T2.8, T2.9 (7 days)
- **Parallel**: T3.2, T3.3, T3.4, T4.1, T4.2, T4.3 (all agents)

**Estimated Timeline**: 2-3 weeks (sprint-based)

---

## Approval & Sign-Off

| Item              | Owner            | Date       | Status  |
| ----------------- | ---------------- | ---------- | ------- |
| Task breakdown    | (auto-generated) | 2026-02-18 | Draft   |
| Phase 1 approval  | (TBD)            | (TBD)      | Pending |
| Phase 2 approval  | (TBD)            | (TBD)      | Pending |
| Phase 3 approval  | (TBD)            | (TBD)      | Pending |
| **Final handoff** | (TBD)            | (TBD)      | Pending |

---

## Appendix: Task Template for Each Phase

### Phase 1 Task Template

```
[ ] T1.X: Task Name
    - Effort: X agent-days
    - Owner: (TBD)
    - Dependencies: [prior tasks]
    - Deliverables:
      - Artifact 1
      - Artifact 2
    - Success Criteria:
      - Criterion 1
      - Criterion 2
```

### Phase 2 Task Template

```
[ ] T2.X: Module Impl
    - Effort: X agent-days
    - Owner: (TBD)
    - Dependencies: [design, prior modules]
    - Code: src/thegent/offload/module_name.py (~N LOC)
    - Tests: tests/thegent/offload/test_module_name.py
    - Success Criteria:
      - Methods implemented: [list]
      - Coverage ≥70%
      - Tests pass 100%
```

---

**End of Task Breakdown Document**
