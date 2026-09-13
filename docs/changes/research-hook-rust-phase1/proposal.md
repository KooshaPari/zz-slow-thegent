# Research Proposal: Rust Hooks Implementation Phase 1

**Date**: 2026-02-18
**Phase**: Research & Design
**Status**: Proposed
**Duration**: 1 week

## Executive Summary

The hook system is currently implemented as a hybrid Bash/Rust architecture. The Rust `hook-dispatcher` binary orchestrates lifecycle events (PreToolUse, PostToolUse, Stop, SessionStart, etc.), while individual hook scripts remain in Bash. This creates a maintenance burden: Bash dependencies (rg, jq, fd), cross-platform portability issues, and performance bottlenecks from subprocess spawning.

**Phase 1 Research Objective**: Evaluate the feasibility and ROI of rewriting core hook implementations in Rust, starting with the highest-impact, highest-frequency hooks (quality-gate, stop-reconcile, security-pipeline).

**Expected Outcome**: A detailed technical specification with performance benchmarks, architecture decisions, and a phased implementation roadmap for Rust-based hooks.

---

## Problem Statement

### Current Architecture Limitations

1. **Performance**: Each hook script spawns bash, loads environment, executes logic, returns. On Stop (5-15s budget), running 12 advisory hooks in parallel still wastes 200-500ms on shell overhead.

2. **Portability**: Bash assumes GNU coreutils (rg, jq, fd). macOS users need Homebrew. Windows (WSL) has compatibility quirks. Tests fail on CI without pre-installed tools.

3. **Type Safety**: Bash is dynamically typed. Governance rules (cost caps, quality thresholds) are hardcoded or parsed from JSON at runtime. No compile-time validation.

4. **Testing**: Bash scripts are hard to unit test. Integration tests mock all subprocess calls. Coverage is low.

5. **Reusability**: Governance logic duplicated across hooks. No shared library for cost calculations, quality metrics, or policy evaluation.

6. **Observability**: No structured logging or metrics. Debugging requires reading stderr output.

### Business Impact

- **Reliability**: Bash scripts fail silently on PATH issues, encoding errors, or signal handling edge cases.
- **Developer Experience**: Adding new hooks requires Bash knowledge. Governance rule changes touch multiple files.
- **Maintenance**: Each Bash hook is 200-500 LOC with custom error handling, no framework support.

---

## Research Objectives

### Primary Goals

1. **Performance Analysis**: Measure end-to-end Stop latency with native Rust hooks vs. Bash shells.
   - Baseline: Current Bash + rg + jq pipeline
   - Target: 50% reduction in spawn + execute time

2. **Feasibility Assessment**: Determine which hooks are best candidates for Rust rewrite.
   - Identify dependencies (libc, tokio, regex, serde)
   - Assess cross-platform support (macOS, Linux, Windows/WSL)
   - Prototype core governance logic

3. **Architecture Design**: Define Rust hook patterns that integrate with dispatcher.
   - Shared governance library (policy engine, cost calculator, quality evaluator)
   - Hook interface (stdin/stdout JSON contract)
   - Error handling and logging conventions

4. **Migration Strategy**: Create a phased roadmap for incremental Rust adoption.
   - Phase 1.1: Extract governance logic into library
   - Phase 1.2: Rewrite 3 high-impact hooks (quality-gate, security-pipeline, stop-reconcile)
   - Phase 1.3: Build framework for remaining hooks
   - Phase 2: Convert remaining 9 hooks

---

## Scope

### Included in Phase 1

- **Research & Analysis** (Days 1-2):
  - Profile current Bash hooks (CPU, memory, latency)
  - Evaluate Rust dependencies (security, maintenance burden)
  - Interview 2-3 hook developers for pain points

- **Architecture & Design** (Days 2-3):
  - Design shared governance library
  - Define hook interface contract
  - Prototype cost calculator in Rust
  - Create dependency map (what hooks use what libraries)

- **Proof of Concept** (Days 4-5):
  - Rewrite `quality-gate.sh` (300 LOC) → Rust (150 LOC estimated)
  - Benchmark: 5x parallel runs, compare latency to Bash
  - Test on macOS, Linux (CI), Windows (WSL simulation)

- **Specification** (Days 6-7):
  - Document findings in technical spec
  - Create implementation guide with code patterns
  - Propose Phase 2 roadmap (4-week implementation)

### Excluded (Post-Phase 1)

- Full implementation of remaining hooks
- Integration with Claude Code plugin system
- Production deployment and monitoring

---

## Technical Approach

### Performance Profiling

**Baseline Measurement**:

```bash
# Measure current Stop dispatcher latency
time hook-dispatcher stop < /tmp/hook-input.json

# Profile individual hook execution
strace -c bash hooks/quality-gate.sh
```

**Expected Findings**:

- Bash startup: ~50ms per hook (12 hooks × 50ms = 600ms total in sequential)
- Parallel reduction: 600ms → ~150ms (spawn overhead)
- rg/jq/fd invocation overhead: 30-50% of hook execution time

**Rust Optimization Targets**:

- Native binary: ~10ms startup (60× faster)
- Embedded regex/json: no subprocess calls
- Parallel threading: better CPU utilization than bash background jobs

### Governance Library Design

**Core Components**:

1. **PolicyEngine**:
   - Load governance rules from JSON/YAML
   - Evaluate cost caps, quality thresholds, SLO gates
   - Return pass/fail with diagnostic data

2. **CostCalculator**:
   - Token prediction from model name + input token count
   - Provider pricing lookup (Claude, Gemini, GPT)
   - Cost-to-value ratio computation

3. **QualityEvaluator**:
   - Lint results parsing (ruff, oxlint, golangci)
   - Test coverage aggregation
   - Complexity metrics (cyclomatic, cognitive, dead code)

4. **SecurityScanner**:
   - Secret pattern detection (builtin regex, not external tools)
   - SAST integration hooks
   - Supply chain auditing (SBOM generation)

5. **SpecVerifier**:
   - FR → Test traceability
   - Orphan test detection
   - Spec coverage % calculation

### Rust Hook Interface

**Input Contract** (stdin):

```json
{
  "tool_name": "Write",
  "file_path": "/path/to/file.py",
  "project_dir": "/path/to/project",
  "session_id": "session-123",
  "cwd": "/path/to/project"
}
```

**Output Contract** (stdout/stderr):

```
- Exit code 0: success
- Exit code 1-127: failure (propagate)
- Exit code 255: timeout
```

**Environment Variables** (passed from dispatcher):

```
- PROJECT_DIR, CWD
- FILE_PATH, TOOL_NAME
- QUALITY_CONFIG, VERIFY_DIR
- RG_CMD, JQ_CMD, FD_CMD (for tools still needed)
```

### Dependencies

**Required Crates**:

- `serde_json`: JSON parsing (already in use)
- `regex`: Pattern matching for secrets, governance rules
- `tokio`: Async I/O (optional for parallel hooks)
- `clap`: CLI arg parsing (for standalone hook execution)
- `tracing`: Structured logging (for observability)

**Avoided**:

- `subprocess` / `std::process`: Minimize subprocesses (one of the problems we're solving)
- `async-trait`: Stick to concrete types for simplicity

**Risk Assessment**:

- All crates are high-maturity with active maintenance
- Tokio is battle-tested in production
- No new external dependencies beyond what dispatcher uses

---

## Success Criteria

### Performance Targets

| Metric                           | Current (Bash) | Target (Rust) | Success            |
| -------------------------------- | -------------- | ------------- | ------------------ |
| Single hook latency              | 100-200ms      | 20-40ms       | ✓ 50-75% reduction |
| Parallel Stop latency (12 hooks) | 800-1200ms     | 300-500ms     | ✓ 60% reduction    |
| Memory per hook                  | 15-20MB        | 2-5MB         | ✓ 75% reduction    |
| Startup overhead                 | ~50ms          | ~10ms         | ✓ 80% reduction    |

### Quality Targets

| Criteria                   | Target                                    |
| -------------------------- | ----------------------------------------- |
| Code coverage (Rust hooks) | ≥ 85%                                     |
| Type safety                | No unsafe blocks (except where necessary) |
| Cross-platform tests       | 3 platforms (macOS, Linux, WSL)           |
| Error handling             | All error paths tested                    |

### Feasibility Targets

| Decision                                     | Target | Confidence |
| -------------------------------------------- | ------ | ---------- |
| Governance logic extractable to Rust library | Yes    | High       |
| 50% code reduction vs. Bash                  | Yes    | High       |
| No performance regression                    | Yes    | Medium     |
| Community adoption (no vendor lock-in)       | Yes    | High       |

---

## Risks & Mitigations

| Risk                                  | Impact                | Likelihood | Mitigation                                        |
| ------------------------------------- | --------------------- | ---------- | ------------------------------------------------- |
| Rust binary size larger than expected | Deployment friction   | Low        | Static linking is acceptable; ~20MB is typical    |
| Cross-platform testing complexity     | Schedule slip         | Medium     | Use Docker + WSL for CI; accept macos manual test |
| Dependency version conflicts          | Build failures        | Low        | Pinned versions, pre-commit checks for updates    |
| Performance not meeting targets       | Research inconclusive | Low        | Fallback: rewrite only hot-path functions         |
| Developer resistance to Rust          | Adoption friction     | Low        | Provide templates and patterns; oss in hooks/lib/ |

---

## Deliverables

### Phase 1 Output

1. **Technical Specification** (5-8 pages)
   - Architecture design document
   - Governance library interface
   - Hook interface specification
   - Dependency audit report

2. **Performance Report** (3-5 pages)
   - Baseline measurements (current Bash)
   - PoC benchmark results (Rust quality-gate)
   - Comparison analysis and recommendations

3. **Implementation Guide** (10-15 pages)
   - Rust hook development patterns
   - Governance library usage examples
   - Testing framework and CI setup
   - Deployment and versioning strategy

4. **Proof of Concept**
   - Rust quality-gate implementation (~150 LOC)
   - Integration tests on 3 platforms
   - Performance benchmark suite

5. **Phase 2 Roadmap** (2-3 pages)
   - Prioritized hook rewrite list (4-week sprints)
   - Resource requirements
   - Risk mitigation strategies
   - Success metrics

---

## Timeline

| Phase | Milestone              | Week        |
| ----- | ---------------------- | ----------- |
| 1.1   | Research & Analysis    | Day 1-2     |
| 1.2   | Architecture Design    | Day 2-3     |
| 1.3   | Governance Library PoC | Day 4-5     |
| 1.4   | Spec & Reporting       | Day 6-7     |
| Done  | Phase 1 Delivery       | End of Week |

---

## Resource Requirements

**Team**: 1 Rust engineer (familiar with governance domain)
**Infrastructure**:

- macOS, Linux CI, WSL environment for testing
- No additional hardware required

**Budget**: Research only, no implementation costs in Phase 1

---

## Open Questions

1. **Async vs Sync**: Should hooks use tokio for parallel I/O, or stick to sync Rust?
   - Answer: Sync for Phase 1 (simpler testing); revisit in Phase 2

2. **Embedded Governance Rules**: Hardcode governance policies in binary, or load from YAML?
   - Answer: Load from YAML (allows runtime updates without recompile)

3. **Logging Strategy**: Structured logging to file, or pass-through to stderr?
   - Answer: Pass-through initially; add structured logging in Phase 2 if needed

4. **Versioning**: One binary for all hooks, or separate binaries?
   - Answer: One binary with subcommands (quality-gate, security-pipeline, etc.)

---

## Next Steps

1. **Get approval** from governance team to proceed
2. **Schedule research kickoff** (Day 1)
3. **Assign Rust engineer** and pair with hook maintainer
4. **Create Phase 2 planning session** after Phase 1 completes
5. **Share findings** with broader team for adoption planning

---

## Appendix: Current Hook Inventory

| Hook Name                   | Lines | Frequency            | Impact  | Candidate |
| --------------------------- | ----- | -------------------- | ------- | --------- |
| quality-gate.sh             | 300   | Stop (always)        | High    | ✓ Yes     |
| security-pipeline.sh        | 250   | Stop (always)        | High    | ✓ Yes     |
| stop-reconcile.sh           | 180   | Stop (always)        | Medium  | ✓ Yes     |
| spec-verifier.sh            | 220   | Stop (optional)      | Medium  | ~ Phase 2 |
| pre-write-validator.sh      | 150   | PreToolUse (often)   | Medium  | ~ Phase 2 |
| qa-policy-test.sh           | 120   | PostToolUse (often)  | Low     | Phase 2   |
| task-completion-verifier.sh | 100   | TaskCompleted (rare) | Low     | Phase 3   |
| **Remaining 9**             | ~1200 | Mixed                | Low-Med | Phase 2-3 |

**Total LoC**: ~2500 Bash
**Estimated Rust equivalent**: ~1200 LoC (50% reduction via type system + stdlib)

---

**Status**: Ready for review and approval
**Version**: 1.0
**Author**: [AI Research Team]
