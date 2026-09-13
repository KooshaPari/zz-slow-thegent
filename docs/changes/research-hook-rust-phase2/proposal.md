# Research Proposal: Rust Hooks Implementation Phase 2

**Date**: 2026-02-18
**Phase**: Implementation (Phase 2)
**Status**: Proposed
**Duration**: 4 weeks

## Executive Summary

Phase 1 research (completed) established the feasibility and performance gains of rewriting Bash hooks to Rust. The governance library (`thegent-hooks`) achieved 50%+ code reduction, 85%+ test coverage, and demonstrated 60-80% latency improvements on quality-gate and security-pipeline proof-of-concepts.

**Phase 2 Implementation Objective**: Migrate the remaining 9 high-impact Bash hooks to Rust using the proven Phase 1 patterns and library. Achieve 100% hook coverage, retire all Bash hook implementations, and deliver a unified Rust-based hook system with integrated governance, security, and quality assurance.

**Expected Outcome**: Production-ready Rust hook suite deployed to thegent, measurable reduction in hook latency (600ms → 150-200ms on Stop event), zero governance regressions, and a maintainable codebase with 80%+ test coverage.

---

## Problem Statement (Context from Phase 1)

### Phase 1 Findings

Phase 1 research confirmed:

1. **Performance bottleneck verified**: Bash hook startup + subprocess overhead accounts for 60-70% of Stop event latency (600-800ms for 12 hooks in parallel)
2. **Code duplication confirmed**: Governance logic (cost caps, coverage thresholds, lint validation) duplicated across 5+ hook scripts
3. **Type safety gap identified**: Bash's dynamic typing creates silent failures when policy rules are malformed or incomplete
4. **Testing debt**: Bash hooks have <30% test coverage; integration tests require complex mocking of external tools
5. **Maintenance friction**: Adding new governance rules requires updating multiple hooks and YAML configs

### Phase 1 Proof of Concept Results

| Metric                   | Bash      | Rust    | Improvement          |
| ------------------------ | --------- | ------- | -------------------- |
| Single hook latency      | 120-150ms | 25-35ms | **70-80% reduction** |
| Startup overhead         | ~50ms     | ~10ms   | **80% reduction**    |
| Memory per hook          | 18-20MB   | 3-5MB   | **75-80% reduction** |
| Test coverage            | ~20%      | 85%     | **4× improvement**   |
| Code size (quality-gate) | 300 LOC   | 150 LOC | **50% reduction**    |

### Current Hook Inventory (Remaining Candidates)

| Hook                        | Status     | Lines | Frequency     | Complexity | Phase 2 Priority |
| --------------------------- | ---------- | ----- | ------------- | ---------- | ---------------- |
| quality-gate.sh             | ✓ Rust PoC | 300   | Stop          | High       | P1 (ship now)    |
| security-pipeline.sh        | ✓ Rust PoC | 250   | Stop          | High       | P1 (ship now)    |
| stop-reconcile.sh           | Bash       | 180   | Stop          | Medium     | P1 (week 1)      |
| spec-verifier.sh            | Bash       | 220   | Stop          | Medium     | P1 (week 1)      |
| pre-write-validator.sh      | Bash       | 150   | PreToolUse    | Medium     | P2 (week 2)      |
| qa-policy-test.sh           | Bash       | 120   | PostToolUse   | Low        | P2 (week 2)      |
| task-completion-verifier.sh | Bash       | 100   | TaskCompleted | Low        | P2 (week 3)      |
| post-edit-checker.sh        | Bash       | 160   | PostToolUse   | Medium     | P2 (week 3)      |
| complexity-ratchet.sh       | Bash       | 140   | Stop          | Medium     | P2 (week 4)      |
| **Remaining 4**             | Bash       | ~400  | Mixed         | Low        | P3 (future)      |

**Total Bash LoC (to migrate)**: ~1,620
**Estimated Rust equivalent**: ~800 LoC (50% reduction via type safety + stdlib)

---

## Business Drivers

### Performance SLA

- **Current**: Stop event latency 600-1200ms (budget: 5-15s, uses 10%)
- **Target**: Stop event latency 150-250ms (reduces to 3-5% of budget)
- **Benefit**: Headroom for additional safety checks without blocking user workflow

### Developer Experience

- **Current**: Hook modifications require Bash expertise, YAML editing, manual integration testing
- **Target**: Centralized governance library, type-safe APIs, reusable code patterns
- **Benefit**: 50% faster to add/modify governance rules

### Reliability & Observability

- **Current**: Bash scripts fail silently on encoding errors, PATH issues, signal handling quirks
- **Target**: Structured errors, type checking at compile time, comprehensive logging
- **Benefit**: Production incidents reduced via static guarantees

### Maintenance Cost

- **Current**: ~2500 LOC Bash to maintain, duplicate logic across hooks
- **Target**: ~1200 LOC Rust + 400 LOC library reuse
- **Benefit**: 50% reduction in test and maintenance burden

---

## Phase 2 Scope

### Included

**Implementation (Weeks 1-4)**:

1. **Week 1**: Migrate high-impact stop hooks (stop-reconcile, spec-verifier)
   - Reuse Phase 1 patterns
   - Full test coverage
   - Cross-platform validation

2. **Week 2**: Migrate PreToolUse & PostToolUse hooks (pre-write-validator, qa-policy-test)
   - Expand library for tool-specific logic
   - Async I/O optimization (optional)
   - Integration testing

3. **Week 3**: Migrate completion & verification hooks (task-completion-verifier, post-edit-checker)
   - State machine patterns (git, file tracking)
   - Error recovery paths
   - Performance optimization

4. **Week 4**: Finalization & Production Readiness
   - Integration testing across all 9 hooks
   - Performance profiling on real workloads
   - CI/CD pipeline hardening
   - Deployment playbook

**Deliverables**:

- 9 production-ready Rust hooks (binaries in `~/.claude/hooks/`)
- Updated hook-dispatcher to recognize `.rs` binaries
- Migration guide (Bash → Rust patterns)
- Performance report (before/after)
- Deployment & rollback procedures

### Excluded (Post-Phase 2)

- Remaining 4 low-priority hooks (Phase 3+)
- Async/parallel hook execution optimization (Phase 3+)
- Distributed hook execution (Phase 4+)
- Public API/SDK for external hook developers (Phase 4+)

---

## Technical Approach

### Reuse Phase 1 Foundations

**Governance Library** (`thegent-hooks` crate):

- `PolicyEngine` - Already stable, supports cost caps, coverage thresholds, lint gates
- `CostCalculator` - Token pricing for all major models
- `QualityEvaluator` - Parse ruff, oxlint, coverage metrics
- `SecurityScanner` - Secret detection, SAST rule integration
- `SpecVerifier` - FR → test traceability

**Hook Binary Template**:

```rust
use thegent_hooks::*;

fn main() -> Result<ExitCode> {
    let input = read_stdin_json::<HookInput>()?;
    let engine = load_hook_config(&input.project_dir)?;

    // Hook-specific logic here

    Ok(exit_code)
}
```

### Hook Migration Strategy

**High-Impact Hooks First** (Week 1):

- `stop-reconcile.sh`: Git state tracking, session reconciliation
  - Library: New `StateManager` for git operations
  - Estimate: ~120 LOC Rust (vs 180 Bash)

- `spec-verifier.sh`: FR coverage verification
  - Library: Expand `SpecVerifier` with full coverage analysis
  - Estimate: ~130 LOC Rust (vs 220 Bash)

**Medium-Impact Hooks** (Weeks 2-3):

- `pre-write-validator.sh`: File validation before writes
- `post-edit-checker.sh`: AI slop detection, complexity ratchet
- `qa-policy-test.sh`: Quality gate evaluation
- `task-completion-verifier.sh`: Task state verification

**Optimization Opportunities**:

- Lazy-load governance configs (shared across hooks)
- Parallel file scanning via `rayon`
- mmap for large file analysis
- Result caching between Stop event hooks

### Dependencies & Integration

**No changes to hook-dispatcher required** (backward compatible):

- Dispatcher continues to spawn hook binaries as before
- Existing JSON input/output contract unchanged
- Phase 2+: Optional dispatcher optimization to recognize Rust binaries and skip bash shell

**Config Location**:

```
~/.claude/hooks/
├── governance.yaml          # Shared policy rules
├── pricing.yaml             # Model pricing data
├── quality-thresholds.json  # Quality gate settings
└── hooks/                   # Compiled binaries
    ├── quality-gate         # Rust binary (Phase 1)
    ├── security-pipeline    # Rust binary (Phase 1)
    ├── stop-reconcile       # Rust binary (Phase 2, week 1)
    ├── spec-verifier        # Rust binary (Phase 2, week 1)
    └── ... (remaining in week 2-3)
```

---

## Success Criteria

### Performance Targets

| Metric                           | Current (Bash) | Target (Rust) | Success            |
| -------------------------------- | -------------- | ------------- | ------------------ |
| Average hook latency             | 80-150ms       | 20-35ms       | ✓ 60-75% reduction |
| Parallel Stop latency (12 hooks) | 700-1000ms     | 150-200ms     | ✓ 75-80% reduction |
| Memory overhead per hook         | 15-20MB        | 2-5MB         | ✓ 75% reduction    |
| Startup + dispatch time          | 600-800ms      | 120-180ms     | ✓ 75% reduction    |

### Quality Targets

| Criterion                         | Target                                |
| --------------------------------- | ------------------------------------- |
| Test coverage (all Rust hooks)    | ≥80% (enforced by CI gate)            |
| Type safety                       | No unsafe blocks in application logic |
| Cross-platform validation         | 3 platforms (macOS, Linux, WSL)       |
| Integration test pass rate        | 100%                                  |
| Regression: governance violations | 0 (parity with Bash)                  |

### Operational Targets

| Target                        | Success                                      |
| ----------------------------- | -------------------------------------------- |
| 9 hooks successfully migrated | All 9 shipping to production                 |
| Production deployment         | Zero critical incidents post-deploy          |
| Rollback capability           | <5 min to revert to Bash (optional fallback) |
| Developer adoption            | 100% of new hooks written in Rust            |
| Maintenance burden            | 50% reduction in governance rule updates     |

---

## Risks & Mitigations

| Risk                                         | Impact        | Likelihood | Mitigation                                                       |
| -------------------------------------------- | ------------- | ---------- | ---------------------------------------------------------------- |
| Performance regression on specific hooks     | 4h slip       | Low        | Profile each hook in week 4; async optimization available        |
| Dependency conflicts (tokio, regex versions) | Build failure | Low        | Pre-audit dependencies; use exact pinned versions                |
| Cross-platform issues (esp. WSL)             | 8h slip       | Medium     | Early WSL testing in week 1; dedicated test suite                |
| Integration test brittleness                 | Flaky tests   | Medium     | Use test fixtures (temp projects); mock external tools           |
| Bash hook behavior parity issues             | 12h rework    | Low        | Run Bash vs Rust side-by-side in staging; capture all edge cases |
| Governance expert unavailable                | 2h slip       | Low        | Document decision rationale in code; pre-review specifications   |
| Team learning curve on Rust                  | 6h slip       | Medium     | Code reviews + pair programming; templates provided              |

---

## Detailed Timeline

### Week 1: High-Impact Stop Hooks

| Day | Task                                     | Effort | Owner | Notes                                   |
| --- | ---------------------------------------- | ------ | ----- | --------------------------------------- |
| Mon | 2.1.1 - Setup Phase 2 Workspace          | 2h     | Eng   | Copy Phase 1 patterns; create workspace |
| Tue | 2.1.2 - stop-reconcile Planning          | 1h     | Eng   | Analyze git operations, state tracking  |
|     | 2.1.3 - Implement StateManager           | 3h     | Eng   | Git log, branch, state parsing          |
| Wed | 2.1.4 - stop-reconcile Implementation    | 3h     | Eng   | Rewrite logic, error handling           |
| Thu | 2.1.5 - stop-reconcile Tests             | 2h     | Eng   | Unit + integration tests                |
|     | 2.2.1 - spec-verifier Planning           | 1h     | Eng   | FR index, test tracing                  |
| Fri | 2.2.2 - Implement SpecVerifier Library   | 3h     | Eng   | Expand from Phase 1; coverage analysis  |
|     | 2.2.3 - spec-verifier Implementation     | 2h     | Eng   | Rewrite logic                           |
|     | 2.2.4 - spec-verifier Tests & Benchmarks | 2h     | Eng   | Validation, performance                 |

**Week 1 Total**: 19h (parallel execution possible)

### Week 2: Medium-Priority Hooks (PreToolUse & PostToolUse)

| Day | Task                                  | Effort | Owner | Notes                      |
| --- | ------------------------------------- | ------ | ----- | -------------------------- |
| Mon | 2.3.1 - pre-write-validator Planning  | 1h     | Eng   | File validation, linting   |
| Tue | 2.3.2 - Implement pre-write-validator | 3h     | Eng   | Rewrite logic              |
|     | 2.3.3 - Tests for pre-write-validator | 2h     | Eng   | Edge cases, error handling |
| Wed | 2.4.1 - qa-policy-test Planning       | 1h     | Eng   | Quality gate evaluation    |
|     | 2.4.2 - Implement qa-policy-test      | 2h     | Eng   | Use PolicyEngine library   |
| Thu | 2.4.3 - qa-policy-test Tests          | 1h     | Eng   | Integration tests          |
| Fri | Performance optimization review       | 2h     | Eng   | Profile all Week 2 hooks   |
|     | Integration testing (Week 1 + 2)      | 2h     | Eng   | Cross-hook validation      |

**Week 2 Total**: 14h

### Week 3: Completion & Verification Hooks

| Day | Task                                       | Effort | Owner | Notes                         |
| --- | ------------------------------------------ | ------ | ----- | ----------------------------- |
| Mon | 2.5.1 - task-completion-verifier Planning  | 1h     | Eng   | Task state, session tracking  |
| Tue | 2.5.2 - Implement task-completion-verifier | 2h     | Eng   | Rewrite logic                 |
|     | 2.5.3 - Tests for task-completion-verifier | 1h     | Eng   | State machine validation      |
| Wed | 2.6.1 - post-edit-checker Planning         | 1h     | Eng   | AI slop detection, complexity |
|     | 2.6.2 - Implement post-edit-checker        | 3h     | Eng   | Rewrite + ai-slop patterns    |
| Thu | 2.6.3 - post-edit-checker Tests            | 2h     | Eng   | AI slop test vectors          |
| Fri | Integration testing (all Week 3 hooks)     | 2h     | Eng   | Cross-hook validation         |
|     | Cross-platform testing                     | 2h     | Eng   | macOS, Linux, WSL             |

**Week 3 Total**: 14h

### Week 4: Finalization & Production Readiness

| Day | Task                                | Effort | Owner    | Notes                                |
| --- | ----------------------------------- | ------ | -------- | ------------------------------------ |
| Mon | 4.1.1 - End-to-End Testing          | 3h     | Eng      | All 9 hooks in Stop event            |
|     | 4.1.2 - Performance Profiling       | 2h     | Eng      | Latency, memory, CPU                 |
| Tue | 4.1.3 - Regression Testing          | 2h     | Eng      | Bash vs Rust parity                  |
|     | 4.1.4 - Cross-Platform Validation   | 2h     | Eng      | macOS, Linux, WSL deployment         |
| Wed | 4.2.1 - Deployment Playbook         | 2h     | Eng+Lead | Step-by-step, rollback procedures    |
|     | 4.2.2 - Documentation Updates       | 2h     | Lead     | Hook migration guide, best practices |
| Thu | 4.3.1 - Code Review & QA            | 2h     | Reviewer | Final quality gate                   |
| Fri | 4.4.1 - Delivery & Signoff          | 1h     | Lead     | Present results, capture lessons     |
|     | 4.4.2 - Phase 3 Planning (optional) | 2h     | Lead     | Future optimization opportunities    |

**Week 4 Total**: 18h

**Total Phase 2 Effort**: ~65 hours (1.6 FTE × 4 weeks)

---

## Dependencies & Preconditions

### Phase 1 Completion

- thegent-hooks library stable and published
- quality-gate and security-pipeline PoC complete with full test suite
- Phase 1 documentation (technical spec, implementation guide) finalized
- No critical issues in Phase 1 codebase

### Infrastructure

- Rust build toolchain (rustc 1.70+)
- GitHub Actions CI (with cross-platform testing)
- Docker for Linux builds
- WSL2 environment for Windows validation

### Team

- 1 Rust engineer (full-time for 4 weeks)
- 1 Governance/QA expert (0.25 FTE for reviews)
- 1 Code reviewer (0.1 FTE for final QA)

### Knowledge & Approvals

- Phase 1 findings approved by governance team
- Architecture reviewed by platform team
- Performance targets accepted as success criteria

---

## Success Indicators (Measurable)

### Quantitative

- [ ] 9 Rust hooks deployed (from 9 Bash)
- [ ] Stop event latency: 700-1000ms → 150-250ms (measured)
- [ ] Test coverage: ≥80% across all hooks (reported by CI)
- [ ] Zero governance regressions (governance violations same as Bash)
- [ ] 100% integration test pass rate on 3 platforms

### Qualitative

- [ ] Rust hooks follow established patterns (code review sign-off)
- [ ] Documentation is clear enough for team to maintain (peer review)
- [ ] Deployment goes smoothly (ops team sign-off)
- [ ] No critical incidents post-deploy (SRE sign-off)
- [ ] Team confident to write new hooks in Rust (team feedback)

---

## Next Steps (Upon Approval)

1. **Week 0**: Final Phase 1 cleanup, dependency audit
2. **Week 1**: Kickoff Phase 2, begin high-impact hooks
3. **Weekly**: Standups + code reviews
4. **End of Week 4**: Delivery + retrospective

---

## Appendix A: Bash Hook Parity Matrix

All 9 Phase 2 hooks will maintain 100% behavioral parity with Bash versions:

| Hook                     | Input | Output              | Exit Codes | Governance Rules       | Migration Test            |
| ------------------------ | ----- | ------------------- | ---------- | ---------------------- | ------------------------- |
| stop-reconcile           | JSON  | stderr + state file | 0/1        | Session reconciliation | Functional equiv test     |
| spec-verifier            | JSON  | stderr + report     | 0/1        | FR coverage ≥80%       | Coverage comparison       |
| pre-write-validator      | JSON  | stderr              | 0/1/124    | File validation        | Path/encoding edge cases  |
| qa-policy-test           | JSON  | stderr              | 0/1        | Policy evaluation      | Rule matching             |
| task-completion-verifier | JSON  | stderr              | 0/1        | Task state + session   | State machine validation  |
| post-edit-checker        | JSON  | stderr              | 0/1        | Complexity + AI slop   | AI slop detection vectors |
| complexity-ratchet       | JSON  | stderr              | 0/1        | Complexity limits      | Cyclomatic complexity     |
| (TBD Phase 2.5)          | —     | —                   | —          | —                      | —                         |
| (TBD Phase 2.5)          | —     | —                   | —          | —                      | —                         |

---

## Appendix B: Performance Targets Justification

**Stop Event Budget**: 5-15 seconds (user workflow threshold)

Current hook latency breakdown:

- 12 hooks in parallel: 700-1000ms (baseline)
- Each hook: 50ms startup + 30-100ms execution
- Total: 10-15% of available budget

Phase 2 target:

- 12 hooks in parallel: 150-250ms (native Rust startup + execution)
- Each hook: 10ms startup + 10-25ms execution
- Total: 2-5% of available budget

**Gain**: Frees 600-750ms for additional safety checks or user-facing operations.

---

**Status**: Ready for review and approval
**Version**: 1.0
**Author**: [Research Team]
