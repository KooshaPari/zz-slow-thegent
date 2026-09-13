# Design Document: Rust Hooks Phase 2 Implementation

**Date**: 2026-02-18
**Phase**: Phase 2 (Implementation)
**Status**: Design Phase
**Duration**: 4 weeks

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Hook-by-Hook Design](#hook-by-hook-design)
3. [Library Extensions](#library-extensions)
4. [Integration Strategy](#integration-strategy)
5. [Testing & Validation](#testing--validation)
6. [Performance Optimization](#performance-optimization)
7. [Deployment & Migration](#deployment--migration)
8. [Success Metrics](#success-metrics)

---

## Architecture Overview

### System Design (Phase 1 + 2)

```
Hook Dispatcher (Rust, from Phase 1)
├── Reads hook event (e.g., Stop)
├── Spawns 12 hooks in parallel
└── Collects results

Phase 1 Hooks (2 Rust binaries)
├── quality-gate → PolicyEngine + QualityEvaluator
└── security-pipeline → SecurityScanner

Phase 2 Hooks (9 Rust binaries, Week 1-3)
├── stop-reconcile → StateManager + git operations
├── spec-verifier → SpecVerifier (expanded)
├── pre-write-validator → FileValidator
├── qa-policy-test → PolicyEngine (reused)
├── task-completion-verifier → TaskStateManager
├── post-edit-checker → AISlop + ComplexityRatchet
├── complexity-ratchet → ComplexityAnalyzer
└── (2 remaining TBD Phase 2.5+)

Shared Library (thegent-hooks crate)
├── policy/              ← Core governance logic
├── cost/                ← Token pricing
├── quality/             ← Lint + coverage parsing
├── security/            ← Secret + SAST detection
├── spec/                ← FR traceability
├── state/               ← NEW: Git + task state
├── validation/          ← NEW: File + complexity validation
├── config.rs            ← Unified config loading
├── types.rs             ← Common types
└── error.rs             ← Error handling
```

### Design Principles

1. **Reuse Over Reimplementation**: Every Phase 2 hook leverages Phase 1 library components
2. **Composability**: Small, focused libraries that combine to solve complex problems
3. **Type Safety**: Leverage Rust's type system to prevent governance rule misconfigurations
4. **Testing First**: Each component has ≥85% test coverage before integration
5. **Backward Compatibility**: 100% behavioral parity with Bash versions
6. **Performance**: All operations complete in <50ms per hook

---

## Hook-by-Hook Design

### 2.1: stop-reconcile Hook

**Current Bash**: ~180 LOC
**Target Rust**: ~120 LOC
**Phase**: Week 1

**Purpose**: Reconcile session state with git history, handle multi-agent coordination conflicts

**Bash Logic Flow**:

```bash
1. Read session metadata from stdin
2. Query git log for uncommitted changes
3. Check for dirty files (work in progress)
4. Update session ledger (escalation_queue.jsonl)
5. Exit 0 if clean, 1 if conflicts detected
```

**Rust Design**:

```rust
// hooks-library: src/state/mod.rs
pub struct StateManager {
    project_dir: PathBuf,
    session_id: String,
}

pub struct SessionState {
    pub session_id: String,
    pub last_update: DateTime<Utc>,
    pub git_status: GitStatus,
    pub dirty_files: Vec<PathBuf>,
    pub conflicts: Vec<Conflict>,
}

pub enum GitStatus {
    Clean,
    UncommittedChanges { count: usize },
    UntrackedFiles { count: usize },
    Dirty,
}

impl StateManager {
    pub fn new(project_dir: PathBuf, session_id: String) -> Result<Self>;
    pub fn check_git_status(&self) -> Result<GitStatus>;
    pub fn get_dirty_files(&self) -> Result<Vec<PathBuf>>;
    pub fn reconcile_session(&self) -> Result<SessionState>;
    pub fn detect_conflicts(&self) -> Result<Vec<Conflict>>;
    pub fn update_ledger(&self, state: &SessionState) -> Result<()>;
}

pub struct Conflict {
    pub conflict_type: ConflictType,
    pub file: PathBuf,
    pub agent_ids: Vec<String>,
    pub severity: String, // "critical", "warning"
}

pub enum ConflictType {
    SimultaneousEdit { agents: Vec<String> },
    UnmergedBranch,
    DivergentHistory,
}
```

**Hook Binary** (`stop-reconcile/src/main.rs`):

```rust
use thegent_hooks::state::{StateManager, SessionState};

fn main() -> Result<ExitCode> {
    let input = read_hook_input()?;
    let manager = StateManager::new(input.project_dir, input.session_id)?;

    let state = manager.reconcile_session()?;

    // Log to stderr
    eprintln!("HOOK stop-reconcile: session {} reconciled", state.session_id);
    eprintln!("HOOK stop-reconcile: git status = {:?}", state.git_status);

    if state.conflicts.is_empty() {
        Ok(ExitCode::from(0))
    } else {
        for conflict in &state.conflicts {
            eprintln!("HOOK stop-reconcile: CONFLICT - {:?}", conflict);
        }
        manager.update_ledger(&state)?;
        Ok(ExitCode::from(1))
    }
}
```

**Testing Strategy**:

- Unit tests for git status parsing
- Integration tests with temp git repos (clean, dirty, conflicting states)
- Multi-agent simulation (2 agents modifying same file)
- Edge cases: large repos, shallow clones, detached HEAD

**Performance**: ~30-40ms (vs ~100-120ms Bash)

---

### 2.2: spec-verifier Hook

**Current Bash**: ~220 LOC
**Target Rust**: ~130 LOC
**Phase**: Week 1

**Purpose**: Verify FR → test traceability, identify coverage gaps

**Bash Logic Flow**:

```bash
1. Parse FUNCTIONAL_REQUIREMENTS.md for FR-{CAT}-{NNN} IDs
2. Search test files for @trace, @mark.requirement(), docstring references
3. Cross-reference: FR_id → test_names (map)
4. Report orphan tests (no FR) and uncovered FRs (no test)
5. Exit 0 if coverage ≥80%, 1 otherwise
```

**Rust Design**:

```rust
// From Phase 1, expand: hooks-library: src/spec/mod.rs
pub struct SpecVerifier {
    fr_index: HashMap<String, FunctionalRequirement>,
    test_index: HashMap<String, Vec<TestRef>>,
    coverage_cache: DashMap<String, f64>,
}

pub struct FunctionalRequirement {
    pub id: String,             // FR-AUTH-001
    pub title: String,
    pub acceptance_criteria: Vec<String>,
    pub implementation_status: String,  // NEW: "not_started" | "in_progress" | "complete"
}

pub struct TestRef {
    pub test_name: String,
    pub file: PathBuf,
    pub line: usize,
    pub framework: String,  // "pytest", "vitest", etc.
    pub fr_ids: Vec<String>,
}

pub struct SpecCoverageReport {
    pub total_frs: usize,
    pub covered_frs: usize,
    pub coverage_percent: f64,
    pub orphan_tests: Vec<TestRef>,
    pub uncovered_frs: Vec<String>,
    pub status_distribution: HashMap<String, usize>,
}

impl SpecVerifier {
    // From Phase 1:
    pub fn from_spec_file(path: &Path) -> Result<Self>;
    pub fn find_tests_for_fr(&self, fr_id: &str) -> Result<Vec<TestRef>>;
    pub fn find_orphan_tests(&self) -> Result<Vec<TestRef>>;
    pub fn find_uncovered_frs(&self) -> Result<Vec<String>>;

    // NEW in Phase 2:
    pub fn scan_test_directory(&self, path: &Path) -> Result<()>;
    pub fn extract_fr_references(&self, content: &str) -> Result<Vec<String>>;
    pub fn coverage_report(&self) -> Result<SpecCoverageReport>;
    pub fn coverage_by_status(&self) -> Result<HashMap<String, f64>>;
}
```

**Hook Binary** (`spec-verifier/src/main.rs`):

```rust
use thegent_hooks::spec::{SpecVerifier, SpecCoverageReport};

fn main() -> Result<ExitCode> {
    let input = read_hook_input()?;

    // Load spec from project
    let mut verifier = SpecVerifier::from_spec_file(
        &input.project_dir.join("FUNCTIONAL_REQUIREMENTS.md")
    )?;

    // Scan test directory
    verifier.scan_test_directory(&input.project_dir.join("tests"))?;

    let report = verifier.coverage_report()?;

    eprintln!("HOOK spec-verifier: FR coverage = {:.1}%", report.coverage_percent);

    if !report.orphan_tests.is_empty() {
        eprintln!("HOOK spec-verifier: {} orphan test(s)", report.orphan_tests.len());
        for test in &report.orphan_tests {
            eprintln!("  - {} (no FR reference)", test.test_name);
        }
    }

    if !report.uncovered_frs.is_empty() {
        eprintln!("HOOK spec-verifier: {} uncovered FR(s)", report.uncovered_frs.len());
        for fr in &report.uncovered_frs {
            eprintln!("  - {}", fr);
        }
    }

    if report.coverage_percent >= 80.0 {
        Ok(ExitCode::from(0))
    } else {
        Ok(ExitCode::from(1))
    }
}
```

**Testing Strategy**:

- Unit tests for FR/test parsing (pytest markers, docstrings, comments)
- Integration tests with sample projects (varying coverage %)
- Edge cases: multi-line docstrings, complex regex, nested structures
- Performance: parse 500+ FRs and 1000+ tests in <50ms

**Performance**: ~40-50ms (vs ~150-180ms Bash)

---

### 2.3: pre-write-validator Hook

**Current Bash**: ~150 LOC
**Target Rust**: ~100 LOC
**Phase**: Week 2

**Purpose**: Validate files before Write/Edit operations (encoding, format, syntax)

**Rust Design**:

```rust
// hooks-library: src/validation/mod.rs
pub struct FileValidator {
    rules: Vec<ValidationRule>,
}

pub enum ValidationRule {
    Encoding { required: String },      // utf-8, ascii
    MaxSize { bytes: u64 },
    FileType { extensions: Vec<String> },
    SyntaxCheck { lang: String },       // "python", "rust", "typescript"
    NoControlChars,
    LineLengthLimit { max: usize },
}

pub struct ValidationResult {
    pub file: PathBuf,
    pub valid: bool,
    pub issues: Vec<ValidationIssue>,
}

pub struct ValidationIssue {
    pub severity: String,      // "error", "warning"
    pub message: String,
    pub line: Option<usize>,
}

impl FileValidator {
    pub fn new(rules: Vec<ValidationRule>) -> Self;
    pub fn validate_file(&self, path: &Path) -> Result<ValidationResult>;
    pub fn validate_content(&self, content: &str, file_type: &str) -> Result<Vec<ValidationIssue>>;
}
```

**Hook Binary** (`pre-write-validator/src/main.rs`):

```rust
fn main() -> Result<ExitCode> {
    let input = read_hook_input()?;

    let validator = FileValidator::new(vec![
        ValidationRule::Encoding { required: "utf-8".to_string() },
        ValidationRule::NoControlChars,
        ValidationRule::LineLengthLimit { max: 1000 },
    ]);

    let result = validator.validate_file(&input.file_path)?;

    if result.valid {
        eprintln!("HOOK pre-write-validator: {} is valid", input.file_path.display());
        Ok(ExitCode::from(0))
    } else {
        eprintln!("HOOK pre-write-validator: {} validation failed", input.file_path.display());
        for issue in result.issues {
            eprintln!("  - {} ({})", issue.message, issue.severity);
        }
        Ok(ExitCode::from(1))
    }
}
```

**Performance**: ~15-20ms (vs ~60-80ms Bash)

---

### 2.4-2.6: Remaining Phase 2 Hooks (Week 2-3)

Similar patterns to above. Each hook:

1. **Extends library** with new component (if needed)
2. **Implements binary** that uses library components
3. **Achieves ≥85% test coverage**
4. **Ships with 50-70% code reduction** vs Bash

**Quick Reference**:

| Hook                     | Library Component    | Estimate | Key Feature               |
| ------------------------ | -------------------- | -------- | ------------------------- |
| qa-policy-test           | PolicyEngine (reuse) | 80 LOC   | Quality gate evaluation   |
| task-completion-verifier | TaskStateManager     | 100 LOC  | Task state tracking       |
| post-edit-checker        | AISlop + Complexity  | 140 LOC  | AI slop detection         |
| complexity-ratchet       | ComplexityAnalyzer   | 110 LOC  | Enforce complexity limits |

---

## Library Extensions

### New Modules in Phase 2

#### 2.A: `state` Module

```rust
// src/state/mod.rs
pub mod git;
pub mod task;
pub mod session;

pub use git::StateManager;
pub use task::TaskStateManager;
pub use session::SessionReconciler;

pub struct ConflictResolver;

impl ConflictResolver {
    pub fn detect_conflicts(
        agent_ids: &[String],
        dirty_files: &[PathBuf],
    ) -> Result<Vec<Conflict>>;
}
```

#### 2.B: `validation` Module

```rust
// src/validation/mod.rs
pub mod file;
pub mod syntax;
pub mod encoding;

pub use file::FileValidator;
pub use syntax::SyntaxChecker;
pub use encoding::EncodingValidator;

pub enum ValidationStrategy {
    Strict,      // Reject any issue
    Permissive,  // Warnings only
}
```

#### 2.C: `analysis` Module

```rust
// src/analysis/mod.rs
pub mod complexity;
pub mod ai_slop;
pub mod dead_code;

pub use complexity::ComplexityAnalyzer;
pub use ai_slop::AISlop Detector;

pub struct AnalysisResult {
    pub issues: Vec<AnalysisIssue>,
    pub metrics: HashMap<String, f64>,
}
```

### Library API Additions (Phase 1 Expansion)

1. **SpecVerifier Enhancements**
   - `scan_test_directory()` - Automatically index all test files
   - `coverage_by_status()` - Break down coverage by FR status

2. **PolicyEngine Enhancements**
   - `evaluate_with_context()` - Full context evaluation
   - `get_violations_by_severity()` - Sort violations by impact

---

## Integration Strategy

### Hook Dispatcher Compatibility

**Phase 2 keeps full backward compatibility with Phase 1 dispatcher**:

```bash
# Current dispatcher behavior (unchanged)
hook-dispatcher stop < /tmp/hook-input.json

# Dispatcher spawns all hooks:
spawn bash hooks/quality-gate.sh           # Phase 1 (Rust now)
spawn bash hooks/security-pipeline.sh      # Phase 1 (Rust now)
spawn bash hooks/stop-reconcile.sh         # Phase 2 (Rust now)
spawn bash hooks/spec-verifier.sh          # Phase 2 (Rust now)
... (8 more) ...
```

**Phase 3+ Optimization** (optional):

```rust
// Dispatcher could recognize .rs suffix and call binary directly
// But this is not required in Phase 2
if hook_name.ends_with(".rs") {
    std::process::Command::new(hook_path)  // Direct call
} else {
    std::process::Command::new("bash")    // Shell spawn
}
```

### Configuration Management

**Centralized Config** (~/.claude/hooks/):

```yaml
# governance.yaml (shared by all hooks)
policies:
  - id: cost-cap-claude
    type: cost_cap
    provider: claude
    max_usd: 50.0

  - id: coverage-min
    type: coverage_threshold
    min_percent: 80

# Per-hook overrides (optional)
hooks:
  quality-gate:
    coverage_min: 85 # Stricter than default

  spec-verifier:
    coverage_min: 80 # Use default
```

### Backward Compatibility

**100% Behavioral Parity Verification**:

For each Bash hook being replaced:

1. **Extract behavior** from Bash version
2. **Document edge cases** (encoding, large files, special chars)
3. **Implement Rust version** with same behavior
4. **Run side-by-side tests**:
   ```bash
   for test_input in test_cases/*; do
       bash hooks/quality-gate.sh < $test_input > /tmp/bash.out
       ./target/release/quality-gate < $test_input > /tmp/rust.out
       diff /tmp/bash.out /tmp/rust.out || FAIL
   done
   ```
5. **Sign off** when all tests pass

---

## Testing & Validation

### Test Matrix (9 Hooks × 4 Dimensions)

| Hook                     | Unit (src/lib.rs) | Integration (tests/) | Cross-Platform | Parity |
| ------------------------ | ----------------- | -------------------- | -------------- | ------ |
| stop-reconcile           | 8 tests           | 5 tests              | 3 OS           | ✓      |
| spec-verifier            | 10 tests          | 6 tests              | 3 OS           | ✓      |
| pre-write-validator      | 6 tests           | 4 tests              | 3 OS           | ✓      |
| qa-policy-test           | 5 tests           | 3 tests              | 3 OS           | ✓      |
| task-completion-verifier | 7 tests           | 4 tests              | 3 OS           | ✓      |
| post-edit-checker        | 9 tests           | 5 tests              | 3 OS           | ✓      |
| complexity-ratchet       | 6 tests           | 4 tests              | 3 OS           | ✓      |
| (TBD)                    | —                 | —                    | —              | —      |
| (TBD)                    | —                 | —                    | —              | —      |

**Coverage Target**: ≥80% on all hooks (enforced by CI)

### Cross-Platform Testing

**Platforms**:

1. macOS 13+ (native)
2. Ubuntu 22.04 (Docker)
3. Windows WSL2 (simulated via GitHub Actions)

**Platform-Specific Test Cases**:

- Line endings: CRLF vs LF
- Path separators: `\` vs `/`
- Git behavior (shallow clones, worktrees)
- Signal handling (Ctrl+C, SIGTERM)
- File permissions (executable bits)

---

## Performance Optimization

### Optimization Targets (Phase 2)

| Component         | Current | Target | Technique                |
| ----------------- | ------- | ------ | ------------------------ |
| Policy loading    | 20ms    | 5ms    | mmap + lazy parse        |
| Test indexing     | 100ms   | 25ms   | parallel rayon + cache   |
| Git operations    | 80ms    | 30ms   | libgit2 instead of shell |
| Spec verification | 150ms   | 40ms   | DashMap caching          |
| File validation   | 60ms    | 15ms   | memmap for large files   |

### Optimization Techniques

1. **Lazy Initialization**

   ```rust
   lazy_static! {
       static ref POLICY_CACHE: DashMap<String, PolicyOutcome> = DashMap::new();
   }
   ```

2. **Parallel Processing** (rayon)

   ```rust
   test_files.par_iter()
       .flat_map(|f| extract_fr_references(f))
       .collect()
   ```

3. **Memory Mapping** (for large files)

   ```rust
   let mmap = unsafe { Mmap::map(&file)? };
   validate_encoding(&mmap)?;
   ```

4. **Result Caching** (between hooks)
   ```rust
   pub static RESULT_CACHE: Lazy<DashMap<String, CachedResult>> = Lazy::new(DashMap::new);
   ```

### Latency Budget (Stop Event)

```
Total Stop budget: 5-15s
Target distribution:
├── Quality-gate (parallel) ............ 25ms
├── Security-pipeline (parallel) ....... 35ms
├── Stop-reconcile (parallel) .......... 40ms
├── Spec-verifier (parallel) ........... 50ms
├── Pre-write-validator ................ 20ms
├── Post-edit-checker .................. 45ms
├── Task-completion-verifier ........... 25ms
├── Complexity-ratchet ................. 30ms
└── Overhead (dispatch + I/O) .......... 40ms
    ─────────────────────────────────────
    Total in parallel: ~200ms
    (current Bash: 800-1000ms)
```

---

## Deployment & Migration

### Rollout Strategy (Week 4)

**Phase 2a (Mandatory)**: Quality-gate + security-pipeline (already PoC'd, just ship)

- Risk: Very low (already validated in Phase 1)
- Rollback: Keep Bash versions, revert dispatcher config

**Phase 2b (High Priority)**: Stop-reconcile, spec-verifier

- Risk: Medium (new implementations, Phase 2 specific)
- Validation: 1 week in staging before production

**Phase 2c (Final)**: Remaining 5 hooks

- Risk: Low-Medium (patterns established)
- Validation: 1 week in staging

**Rollback Procedure** (<5 min):

```bash
# If issue detected:
cd ~/.claude/hooks/
rm quality-gate security-pipeline ...
git checkout HEAD -- quality-gate.sh security-pipeline.sh ...
# Dispatcher continues to work with Bash versions
```

### Installation & Build

```bash
# Build all Phase 2 hooks
cd thegent-hooks/
cargo build --release

# Install to ~/.claude/hooks/
cp target/release/stop-reconcile ~/.claude/hooks/stop-reconcile
cp target/release/spec-verifier ~/.claude/hooks/spec-verifier
... (7 more) ...

# Verify
ls -la ~/.claude/hooks/ | grep -E "(quality-gate|security-pipeline|stop-reconcile|...)"
```

### Version Pinning

```toml
[package]
name = "thegent-hooks"
version = "2.0.0"  # Phase 2 release

[dependencies]
serde = "1.0"
regex = "1.9"
tokio = "1.35"  # Optional, for Phase 3
```

**Compatibility Matrix**:

- `thegent-hooks 1.x`: Phase 1 (quality-gate, security-pipeline)
- `thegent-hooks 2.x`: Phase 1 + 2 (all 9 hooks)
- `thegent-hooks 3.x`: Phase 2 + async optimization (future)

---

## Success Metrics

### Completion Criteria

| Criterion            | Definition                      | Target              | Success |
| -------------------- | ------------------------------- | ------------------- | ------- |
| All 9 hooks migrated | Rust binary for each            | 9/9                 | ✓       |
| Test coverage        | ≥80% on all hooks               | —                   | ✓       |
| Performance          | ≥60% latency reduction          | 150-250ms           | ✓       |
| Parity               | 100% behavioral match with Bash | All tests pass      | ✓       |
| Cross-platform       | Works on 3 OS                   | macOS + Linux + WSL | ✓       |
| Documentation        | Implementation guide + runbook  | Complete            | ✓       |

### Quality Metrics

- [ ] Zero unsafe code in application logic
- [ ] All dependencies audited (cargo-audit)
- [ ] No clippy warnings (strict linting)
- [ ] All tests passing on CI (100%)
- [ ] Code review sign-off (all files)

### Operational Metrics

- [ ] Deployment success (0 critical incidents)
- [ ] Rollback time <5 min
- [ ] Monitoring in place (performance, errors)
- [ ] Runbook documented

---

## Appendix: Library Module Map

```
thegent-hooks/
├── src/
│   ├── lib.rs
│   ├── config.rs                    # Load YAML/JSON configs
│   ├── types.rs                     # Common types (HookError, etc.)
│   ├── error.rs                     # Error handling
│   │
│   ├── policy/                      # ✓ Phase 1
│   │   ├── mod.rs
│   │   ├── engine.rs               # PolicyEngine (load + evaluate rules)
│   │   └── types.rs                # PolicyRule, PolicyOutcome
│   │
│   ├── cost/                        # ✓ Phase 1
│   │   ├── mod.rs
│   │   ├── calculator.rs           # Token → cost estimation
│   │   └── providers.rs            # Pricing data
│   │
│   ├── quality/                     # ✓ Phase 1
│   │   ├── mod.rs
│   │   ├── evaluator.rs            # Parse lint/coverage
│   │   └── metrics.rs              # Lint + coverage types
│   │
│   ├── security/                    # ✓ Phase 1
│   │   ├── mod.rs
│   │   ├── scanner.rs              # Secret + SAST detection
│   │   └── patterns.rs             # Regex patterns
│   │
│   ├── spec/                        # ✓ Phase 1 (expand in Phase 2)
│   │   ├── mod.rs
│   │   ├── verifier.rs             # FR index + traceability
│   │   └── traceability.rs         # FR ↔ test mapping
│   │
│   ├── state/                       # NEW: Phase 2
│   │   ├── mod.rs
│   │   ├── git.rs                  # Git operations, StateManager
│   │   ├── task.rs                 # Task state tracking
│   │   └── session.rs              # Session reconciliation
│   │
│   ├── validation/                  # NEW: Phase 2
│   │   ├── mod.rs
│   │   ├── file.rs                 # FileValidator
│   │   ├── syntax.rs               # Syntax checking
│   │   └── encoding.rs             # Encoding validation
│   │
│   └── analysis/                    # NEW: Phase 2
│       ├── mod.rs
│       ├── complexity.rs           # Complexity analysis
│       ├── ai_slop.rs              # AI slop detection
│       └── dead_code.rs            # Dead code analysis
│
├── tests/
│   ├── integration_tests.rs        # Full suite
│   └── fixtures/                   # Test data
│
└── Cargo.toml
```

---

**Status**: Ready for implementation
**Version**: 1.0
**Next**: Begin Week 1 execution
