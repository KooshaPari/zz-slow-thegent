---
task_id: research-hook-rust-phase1
status: in_progress
---

# WBS: Rust Hooks Phase 1 - Research & PoC

**Phase**: Phase 1 (1 week)
**Start**: Week of 2026-02-18
**End**: Week of 2026-02-25
**Status**: Proposed
**Total Effort**: ~40 hours (1 FTE × 1 week)

---

## Phase 1 Work Breakdown Structure (WBS)

### Phase 1.0: Kickoff & Planning (Day 1, 4h)

#### 1.0.1 — Research Kickoff & Context Sharing

- **Objective**: Align team on goals, scope, dependencies
- **Input**: Proposal & design docs, current hook scripts
- **Output**: Shared understanding, Q&A captured
- **Duration**: 2h
- **Acceptance Criteria**:
  - [ ] Rust engineer understands 5 core pain points
  - [ ] Governance expert reviews proposal for accuracy
  - [ ] Scheduling confirmed for all phases
- **Dependencies**: None
- **Owner**: Research Lead

#### 1.0.2 — Set Up Development Environment

- **Objective**: Prepare Rust build, testing, and CI
- **Input**: Project templates, Cargo.toml patterns
- **Output**:
  - New Cargo workspace: `thegent-hooks/`
  - Local builds working (macOS, Ubuntu in Docker)
  - GitHub Actions CI skeleton
- **Duration**: 2h
- **Acceptance Criteria**:
  - [ ] `cargo build --release` succeeds on macOS
  - [ ] `cargo build --release` succeeds in Ubuntu 22.04 container
  - [ ] `cargo test` passes
  - [ ] CI workflow can build and test
- **Dependencies**: 1.0.1
- **Owner**: Rust Engineer

---

### Phase 1.1: Governance Library PoC (Days 2-3, 12h)

#### 1.1.1 — Extract & Design Common Types

- **Objective**: Define shared data types used across all components
- **Input**: Existing hook script implementations, QA config samples
- **Output**:
  - `src/types.rs` (PolicyRule, QualityMetrics, SecurityFinding, etc.)
  - `src/error.rs` (HookError enum)
  - `src/config.rs` (load YAML/JSON configs)
- **Duration**: 3h
- **Acceptance Criteria**:
  - [ ] All types serialize/deserialize via serde
  - [ ] Error handling covers 90% of use cases
  - [ ] Config loader supports both YAML and JSON
  - [ ] Unit tests for type serialization (100% coverage)
- **Dependencies**: 1.0.2
- **Owner**: Rust Engineer

#### 1.1.2 — Implement PolicyEngine

- **Objective**: Build governance rule loader and evaluator
- **Input**: Design spec (§1.1 in design.md), existing governance.yaml samples
- **Output**:
  - `src/policy/engine.rs` (~150 LOC)
  - `src/policy/types.rs` (PolicyRule, PolicyOutcome)
  - 10+ unit tests
- **Duration**: 4h
- **Acceptance Criteria**:
  - [ ] Load 20+ governance rules from YAML without error
  - [ ] Evaluate context against rules, return violations
  - [ ] Cache results via DashMap (50% hit rate on repeated evals)
  - [ ] 85%+ test coverage for PolicyEngine
- **Dependencies**: 1.1.1
- **Owner**: Rust Engineer

#### 1.1.3 — Implement CostCalculator

- **Objective**: Build token-to-cost estimation engine
- **Input**: Pricing data (Claude, Gemini, GPT), model list
- **Output**:
  - `src/cost/calculator.rs` (~100 LOC)
  - `src/cost/providers.rs` (hardcoded pricing + loading from config)
  - 5+ unit tests
- **Duration**: 2h
- **Acceptance Criteria**:
  - [ ] Estimate cost for 10 known models
  - [ ] Accuracy within ±5% of official pricing
  - [ ] Cost-to-value ratio calculation for routing
  - [ ] Handle unknown model fallback gracefully
- **Dependencies**: 1.1.1
- **Owner**: Rust Engineer

#### 1.1.4 — Implement QualityEvaluator (Core)

- **Objective**: Parse lint output (ruff, oxlint) and aggregate metrics
- **Input**: Sample ruff/oxlint JSON outputs, coverage.py format
- **Output**:
  - `src/quality/evaluator.rs` (~120 LOC)
  - JSON parser for ruff, oxlint, coverage
  - 8+ unit tests
- **Duration**: 3h
- **Acceptance Criteria**:
  - [ ] Parse 100+ ruff JSON issues correctly
  - [ ] Parse oxlint output and map to LintIssue struct
  - [ ] Extract coverage % from JSON (multiple tools)
  - [ ] 85%+ test coverage
- **Dependencies**: 1.1.1
- **Owner**: Rust Engineer

---

### Phase 1.2: Quality-Gate PoC Implementation (Days 4-5, 12h)

#### 1.2.1 — Create quality-gate Binary Skeleton

- **Objective**: Set up Rust binary that matches Bash interface
- **Input**: Bash quality-gate.sh script, design spec
- **Output**:
  - New binary crate: `thegent-hooks-quality-gate/`
  - `main.rs` with stdin/stdout/exit code handling
  - Signature matches existing Bash hook
- **Duration**: 2h
- **Acceptance Criteria**:
  - [ ] Binary accepts JSON on stdin
  - [ ] Prints to stderr on failures
  - [ ] Exit code 0/1/124 implemented
  - [ ] Help text documents usage
- **Dependencies**: 1.1.4
- **Owner**: Rust Engineer

#### 1.2.2 — Implement quality-gate Logic

- **Objective**: Rewrite Bash quality-gate.sh as Rust using library
- **Input**:
  - Bash script (~300 LOC)
  - PolicyEngine, QualityEvaluator
  - Test cases from existing Bash implementation
- **Output**:
  - `quality-gate/src/main.rs` (~150 LOC, 50% reduction)
  - Calls PolicyEngine + QualityEvaluator
  - All error cases mapped to Bash equivalents
- **Duration**: 4h
- **Acceptance Criteria**:
  - [ ] Rust version produces identical output to Bash (for test cases)
  - [ ] Exit codes match Bash equivalents
  - [ ] Performance 3-5× faster than Bash
  - [ ] Handles 10+ edge cases correctly
- **Dependencies**: 1.2.1
- **Owner**: Rust Engineer

#### 1.2.3 — Write Integration Tests

- **Objective**: Verify quality-gate works end-to-end
- **Input**:
  - Sample project directories (pass/fail scenarios)
  - Existing Bash test cases
- **Output**:
  - `tests/integration_tests.rs` (~200 LOC, 10+ tests)
  - Test fixtures (temp projects with known coverage, lint)
- **Duration**: 3h
- **Acceptance Criteria**:
  - [ ] 10 test scenarios pass (coverage high/low, lints, suppressions, etc.)
  - [ ] All tests run in <100ms each
  - [ ] Cross-platform: macOS, Ubuntu, WSL simulation
- **Dependencies**: 1.2.2
- **Owner**: Rust Engineer

#### 1.2.4 — Benchmark & Compare

- **Objective**: Measure Rust vs Bash latency, memory, CPU
- **Input**:
  - Baseline Bash quality-gate.sh timing
  - Rust binary
  - Benchmark harness (run each 10×)
- **Output**:
  - Benchmark report (latency, memory, CPU %)
  - Detailed timing breakdown
  - Statistical analysis (mean, stddev)
- **Duration**: 3h
- **Acceptance Criteria**:
  - [ ] Rust ≥50% faster than Bash (confidence interval 95%)
  - [ ] Memory usage <10MB for Rust (vs ~20MB Bash)
  - [ ] Results reproducible on 3 platforms
  - [ ] Report includes statistical breakdown
- **Dependencies**: 1.2.3
- **Owner**: Rust Engineer

---

### Phase 1.3: Proof-of-Concept Security-Pipeline (Days 5-6, 8h)

#### 1.3.1 — Implement SecurityScanner

- **Objective**: Build secret detection + SAST integration layer
- **Input**:
  - Security patterns (from dispatcher main.rs)
  - SAST rule templates (semgrep, bandit)
- **Output**:
  - `src/security/scanner.rs` (~150 LOC)
  - Regex-based secret detection
  - SAST rule loader (JSON format)
  - 8+ unit tests
- **Duration**: 4h
- **Acceptance Criteria**:
  - [ ] Detect 8+ secret patterns (OpenAI, GitHub, Slack, AWS, etc.)
  - [ ] False positive rate <5% on test corpus
  - [ ] Parse semgrep JSON output
  - [ ] 85%+ test coverage
- **Dependencies**: 1.1.1
- **Owner**: Rust Engineer

#### 1.3.2 — Create security-pipeline Binary

- **Objective**: PoC security-pipeline hook in Rust
- **Input**:
  - Bash security-pipeline.sh (~250 LOC)
  - SecurityScanner
- **Output**:
  - `thegent-hooks-security-pipeline/src/main.rs` (~120 LOC)
  - Calls SecurityScanner
  - Returns 0/1 + findings on stderr
- **Duration**: 2h
- **Acceptance Criteria**:
  - [ ] Detects test secrets accurately
  - [ ] Output format matches Bash version
  - [ ] Performance 3-5× faster
- **Dependencies**: 1.3.1
- **Owner**: Rust Engineer

#### 1.3.3 — Cross-Platform Testing (Security)

- **Objective**: Verify security-pipeline on all platforms
- **Input**:
  - Test project with known secrets
  - Platform-specific environments
- **Output**:
  - Test results for macOS, Linux, WSL
  - Platform compatibility report
- **Duration**: 2h
- **Acceptance Criteria**:
  - [ ] All tests pass on macOS 13+
  - [ ] All tests pass on Ubuntu 22.04
  - [ ] All tests pass on WSL2
  - [ ] No platform-specific regressions
- **Dependencies**: 1.3.2
- **Owner**: Rust Engineer

---

### Phase 1.4: Technical Specification (Days 6-7, 6h)

#### 1.4.1 — Write Technical Specification

- **Objective**: Document architecture, decisions, trade-offs
- **Input**:
  - Design doc (design.md)
  - PoC learnings from 1.1-1.3
  - Benchmark results
- **Output**:
  - `technical-specification.md` (10-15 pages)
  - Architecture decisions explained
  - Integration paths documented
  - Risk mitigation strategies
- **Duration**: 3h
- **Acceptance Criteria**:
  - [ ] Spec covers all 5 core components (PolicyEngine, Cost, Quality, Security, Spec)
  - [ ] Performance targets and results documented
  - [ ] Integration points with existing systems described
  - [ ] Phase 2 roadmap outlined
- **Dependencies**: 1.3.3, benchmark results
- **Owner**: Rust Engineer + Governance Expert

#### 1.4.2 — Create Implementation Guide

- **Objective**: Document how to write new Rust hooks
- **Input**:
  - quality-gate PoC code
  - security-pipeline PoC code
  - Testing patterns
- **Output**:
  - `implementation-guide.md` (10-15 pages)
  - Step-by-step guide for new hooks
  - Code patterns and templates
  - Testing framework documentation
  - CI/CD setup instructions
- **Duration**: 2h
- **Acceptance Criteria**:
  - [ ] New engineer can write hook from guide
  - [ ] Examples for all 5 library components
  - [ ] Testing patterns cover unit + integration + e2e
- **Dependencies**: 1.3.3
- **Owner**: Rust Engineer

#### 1.4.3 — Phase 2 Roadmap & Review

- **Objective**: Plan next phase, document decisions
- **Input**:
  - Phase 1 completion checklist
  - Hook inventory (9 remaining)
  - Performance analysis
- **Output**:
  - `phase-2-roadmap.md` (3-5 pages)
  - Prioritized hook rewrite list
  - Resource estimate
  - Success criteria
  - Risk assessment
- **Duration**: 1h
- **Acceptance Criteria**:
  - [ ] All 9 remaining hooks prioritized
  - [ ] 4-week timeline for Phase 2
  - [ ] Resource requirements stated
  - [ ] Governance team reviews and approves
- **Dependencies**: 1.4.1
- **Owner**: Research Lead

---

### Phase 1.5: Final Review & Delivery (Day 7, 2h)

#### 1.5.1 — Code Review & QA

- **Objective**: Final quality gate before delivery
- **Input**:
  - All Phase 1 deliverables (code, tests, docs)
  - Governance checklist
- **Output**:
  - Code review complete
  - All tests passing (CI green)
  - Documentation reviewed
  - Ready for Phase 2
- **Duration**: 1h
- **Acceptance Criteria**:
  - [ ] All Phase 1 tests passing on CI
  - [ ] Code coverage ≥85%
  - [ ] Documentation complete and reviewed
  - [ ] No critical issues blocking Phase 2
- **Dependencies**: All Phase 1 tasks
- **Owner**: Code Reviewer

#### 1.5.2 — Deliver & Handoff

- **Objective**: Prepare phase 1 output for team
- **Input**:
  - Technical spec, implementation guide, PoC code
- **Output**:
  - Phase 1 delivery package (GitHub repo)
  - Meeting: Present findings to governance team
  - Decision: Proceed to Phase 2 or iterate
- **Duration**: 1h
- **Acceptance Criteria**:
  - [ ] All deliverables in GitHub
  - [ ] Presentation delivered
  - [ ] Phase 2 approval obtained
- **Dependencies**: 1.5.1
- **Owner**: Research Lead

---

## Dependency Graph (DAG)

```
1.0.1 (Kickoff)
  ↓
1.0.2 (Env Setup)
  ↓
  ├─→ 1.1.1 (Common Types)
  │    ├─→ 1.1.2 (PolicyEngine)
  │    ├─→ 1.1.3 (CostCalculator)
  │    └─→ 1.1.4 (QualityEvaluator)
  │         ├─→ 1.2.1 (quality-gate Binary)
  │         │    └─→ 1.2.2 (quality-gate Logic)
  │         │         └─→ 1.2.3 (quality-gate Tests)
  │         │              └─→ 1.2.4 (Benchmark)
  │         │
  │         └─→ 1.3.1 (SecurityScanner)
  │              └─→ 1.3.2 (security-pipeline Binary)
  │                   └─→ 1.3.3 (Cross-Platform Tests)
  │
  └─→ 1.4.1 (Technical Spec) ← 1.2.4, 1.3.3
       ├─→ 1.4.2 (Implementation Guide)
       └─→ 1.4.3 (Phase 2 Roadmap)
            └─→ 1.5.1 (Code Review)
                 └─→ 1.5.2 (Delivery)
```

**Critical Path**: 1.0.1 → 1.0.2 → 1.1.1 → 1.1.4 → 1.2.2 → 1.2.4 → 1.4.1 → 1.5.2 (7 tasks, ~35h)

---

## Task Status Tracking

| Task ID | Title                    | Owner    | Status  | Est. (h) | Actual (h) | % Complete |
| ------- | ------------------------ | -------- | ------- | -------- | ---------- | ---------- |
| 1.0.1   | Kickoff                  | Lead     | pending | 2        | —          | 0%         |
| 1.0.2   | Env Setup                | Eng      | pending | 2        | —          | 0%         |
| 1.1.1   | Common Types             | Eng      | pending | 3        | —          | 0%         |
| 1.1.2   | PolicyEngine             | Eng      | pending | 4        | —          | 0%         |
| 1.1.3   | CostCalculator           | Eng      | pending | 2        | —          | 0%         |
| 1.1.4   | QualityEvaluator         | Eng      | pending | 3        | —          | 0%         |
| 1.2.1   | quality-gate Skeleton    | Eng      | pending | 2        | —          | 0%         |
| 1.2.2   | quality-gate Logic       | Eng      | pending | 4        | —          | 0%         |
| 1.2.3   | quality-gate Tests       | Eng      | pending | 3        | —          | 0%         |
| 1.2.4   | Benchmark & Compare      | Eng      | pending | 3        | —          | 0%         |
| 1.3.1   | SecurityScanner          | Eng      | pending | 4        | —          | 0%         |
| 1.3.2   | security-pipeline Binary | Eng      | pending | 2        | —          | 0%         |
| 1.3.3   | Cross-Platform Tests     | Eng      | pending | 2        | —          | 0%         |
| 1.4.1   | Technical Spec           | Eng+Lead | pending | 3        | —          | 0%         |
| 1.4.2   | Implementation Guide     | Eng      | pending | 2        | —          | 0%         |
| 1.4.3   | Phase 2 Roadmap          | Lead     | pending | 1        | —          | 0%         |
| 1.5.1   | Code Review & QA         | Reviewer | pending | 1        | —          | 0%         |
| 1.5.2   | Delivery & Handoff       | Lead     | pending | 1        | —          | 0%         |

**Total Planned**: 40 hours | **Total Actual**: — | **% Complete**: 0%

---

## Risk Register

| Risk                                     | Impact        | Likelihood | Mitigation                                |
| ---------------------------------------- | ------------- | ---------- | ----------------------------------------- |
| Rust learning curve delays 1.1-1.2       | 8h slip       | Medium     | Pair programming, code templates ready    |
| Dependency version conflicts             | Build failure | Low        | Use exact pinned versions, pre-audit      |
| Cross-platform test issues (WSL)         | 2h slip       | Medium     | Early testing on WSL in 1.0.2             |
| Performance targets not met              | Scope change  | Low        | Fallback: profile and document findings   |
| Governance expert unavailable for review | 1h slip       | Low        | Prep review materials in advance          |
| Benchmark variance (noisy results)       | 1h slip       | Medium     | Run 20× iterations, use statistical tools |

---

## Success Criteria (Phase 1 Complete)

- [x] **Code Delivered**: All Rust code in GitHub, compiles without warnings
- [x] **Tests Pass**: 85%+ coverage, all integration tests green on CI
- [x] **Documentation**: Spec, guide, roadmap complete and reviewed
- [x] **PoC Working**: quality-gate and security-pipeline binaries function correctly
- [x] **Performance**: Benchmarks show ≥50% latency improvement
- [x] **Cross-Platform**: Tests pass on macOS, Linux, WSL
- [x] **Phase 2 Approved**: Governance team sign-off on roadmap

---

## Appendix: Template Checklist

**Daily Standup** (Each morning):

- [ ] Previous task completion % vs estimate
- [ ] Blockers encountered
- [ ] Today's focus
- [ ] Risk escalation (if any)

**Task Completion** (When done):

- [ ] Code committed and pushed
- [ ] Tests passing locally + CI
- [ ] Documentation updated
- [ ] Code review complete
- [ ] Owner sign-off

**Phase Completion** (End of week):

- [ ] All 18 tasks marked complete
- [ ] Artifacts in shared location
- [ ] Delivery meeting scheduled
- [ ] Phase 2 decision communicated

---

**Status**: Ready for execution
**Version**: 1.0
**Last Updated**: 2026-02-18
