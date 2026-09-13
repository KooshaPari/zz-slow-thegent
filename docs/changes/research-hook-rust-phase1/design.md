# Design Document: Rust Hooks Architecture

**Date**: 2026-02-18
**Phase**: Phase 1 (Research & PoC)
**Status**: Design In Progress

## Architecture Overview

The Rust hooks initiative restructures the hook system from a distributed Bash script model into a modular Rust library + binary model.

### Current State (Baseline)

```
hook-dispatcher (Rust binary)
├── Spawns bash shells for each hook
├── Passes JSON via stdin/files
├── Waits for exit codes
└── Parallel execution for Stop mode

Hooks (Bash scripts)
├── quality-gate.sh → loads rg, jq, calls external tools
├── security-pipeline.sh → calls gitleaks, semgrep, etc.
├── stop-reconcile.sh → parses git output, updates state
└── ...11 more
```

**Pain Points**:

- 50ms startup per hook (bash + tool loading)
- External tools (rg, jq, semgrep) spawned per operation
- No type checking, shared governance logic duplicated
- Hard to test, difficult to add features

### Target State (Rust Hooks Phase 1+)

```
hook-dispatcher (Rust binary, existing)
├── Recognizes Rust hooks vs Bash hooks
├── Calls Rust hooks directly (no spawning)
└── Same JSON interface

thegent-hooks (Rust library)
├── policy_engine: Load and evaluate governance rules
├── cost_calculator: Token → cost estimation
├── quality_evaluator: Parse lint output, aggregate metrics
├── security_scanner: Pattern matching for secrets, SAST integration
├── spec_verifier: FR → test traceability
└── Common types & error handling

Hook binaries (Rust, Phase 1+)
├── quality-gate (wraps policy_engine + quality_evaluator)
├── security-pipeline (wraps security_scanner)
├── stop-reconcile (wraps git/state management)
└── [Remaining hooks in Phase 2+]
```

**Benefits**:

- ~10ms startup (80% reduction)
- Native regex, JSON, no subprocesses for core logic
- Type-safe governance rules
- 85% test coverage via cargo test
- Reusable library for all hooks

---

## Core Components Design

### 1. Governance Library (`thegent-hooks`)

**Crate Structure**:

```
thegent-hooks/
├── Cargo.toml
├── src/
│   ├── lib.rs
│   ├── policy/
│   │   ├── mod.rs
│   │   ├── engine.rs        # PolicyEngine implementation
│   │   └── types.rs         # PolicyRule, PolicyConfig structs
│   ├── cost/
│   │   ├── mod.rs
│   │   ├── calculator.rs    # CostCalculator implementation
│   │   └── providers.rs     # Pricing data for Claude, Gemini, etc.
│   ├── quality/
│   │   ├── mod.rs
│   │   ├── evaluator.rs     # QualityEvaluator implementation
│   │   └── metrics.rs       # Complexity, coverage, lint aggregation
│   ├── security/
│   │   ├── mod.rs
│   │   ├── scanner.rs       # SecurityScanner implementation
│   │   └── patterns.rs      # Secret regexes, SAST rules
│   ├── spec/
│   │   ├── mod.rs
│   │   ├── verifier.rs      # SpecVerifier implementation
│   │   └── traceability.rs  # FR/test mapping
│   ├── types.rs             # Common types, errors
│   └── config.rs            # Load config from YAML/JSON
└── tests/
    └── integration_tests.rs
```

#### 1.1 PolicyEngine

**Purpose**: Load governance rules and evaluate against project state.

**Public API**:

```rust
pub struct PolicyEngine {
    rules: Vec<PolicyRule>,
    cache: Arc<DashMap<String, PolicyOutcome>>,
}

pub enum PolicyRule {
    CostCap { provider: String, max_usd: f64, period: Duration },
    CoverageThreshold { min_percent: u32, tool: String },
    ComplexityLimit { max_cyclomatic: u32, max_cognitive: u32 },
    LintSuppressionLimit { max_new_per_file: usize },
    SecurityGate { require_scan: bool, max_findings: usize },
}

impl PolicyEngine {
    pub fn from_yaml(path: &Path) -> Result<Self>;
    pub fn from_json(data: &str) -> Result<Self>;
    pub fn evaluate(&self, context: &EvaluationContext) -> Result<PolicyOutcome>;
    pub fn get_violations(&self) -> Vec<PolicyViolation>;
}

pub struct PolicyOutcome {
    pub passed: bool,
    pub violations: Vec<PolicyViolation>,
    pub warnings: Vec<String>,
    pub metrics: HashMap<String, f64>,
}

pub struct EvaluationContext {
    pub project_dir: PathBuf,
    pub changed_files: Vec<PathBuf>,
    pub current_cost_spend: f64,
    pub test_coverage: f64,
    pub lint_errors: usize,
    pub linter_suppressions: Vec<String>,
}
```

**Example Usage** (in quality-gate hook):

```rust
use thegent_hooks::policy::{PolicyEngine, EvaluationContext};

fn main() -> Result<ExitCode> {
    let engine = PolicyEngine::from_yaml(".claude/governance.yaml")?;
    let context = EvaluationContext::from_env()?;

    let outcome = engine.evaluate(&context)?;

    if !outcome.passed {
        eprintln!("GOVERNANCE VIOLATIONS:");
        for v in &outcome.violations {
            eprintln!("  - {}", v.message);
        }
        return Ok(ExitCode::from(1));
    }

    Ok(ExitCode::from(0))
}
```

#### 1.2 CostCalculator

**Purpose**: Token-based cost estimation for routing decisions.

**Public API**:

```rust
pub struct CostCalculator {
    providers: HashMap<String, ProviderPricing>,
}

pub struct ProviderPricing {
    pub name: String,
    pub input_cost_per_1k: f64,
    pub output_cost_per_1k: f64,
}

impl CostCalculator {
    pub fn from_config(path: &Path) -> Result<Self>;
    pub fn estimate_cost(
        &self,
        model: &str,
        input_tokens: usize,
        output_tokens: usize,
    ) -> Result<f64>;
    pub fn cost_to_value_ratio(
        &self,
        model: &str,
        tokens: usize,
        task_value: f64,
    ) -> Result<f64>;
    pub fn get_provider(&self, model: &str) -> Result<&ProviderPricing>;
}
```

**Supported Models** (seeded from pricing data):

- `claude-opus-4.6`, `claude-sonnet-4.6`, `claude-haiku-4.5`
- `gpt-5-mini`, `gpt-5.3-codex`
- `gemini-3-flash`, `gemini-4`
- Proxy providers: minimax, kiro, nim, glm

**Data Source**:

```yaml
# ~/.claude/hooks-config/pricing.yaml
providers:
  claude:
    opus-4.6:
      input_cost_per_1k: 0.015
      output_cost_per_1k: 0.075
    haiku-4.5:
      input_cost_per_1k: 0.00080
      output_cost_per_1k: 0.0024
  gemini:
    3-flash:
      input_cost_per_1k: 0.075
      output_cost_per_1k: 0.30
```

#### 1.3 QualityEvaluator

**Purpose**: Parse and aggregate quality metrics across multiple tools.

**Public API**:

```rust
pub struct QualityEvaluator;

pub struct QualityMetrics {
    pub lint_errors: usize,
    pub lint_warnings: usize,
    pub coverage_percent: f64,
    pub cyclomatic_complexity: u32,
    pub cognitive_complexity: u32,
    pub dead_code_count: usize,
    pub suppressions: Vec<Suppression>,
}

pub struct Suppression {
    pub file: PathBuf,
    pub rule: String,
    pub justification: Option<String>,
    pub is_new: bool,
}

impl QualityEvaluator {
    pub fn parse_ruff_output(output: &str) -> Result<Vec<LintIssue>>;
    pub fn parse_oxlint_output(output: &str) -> Result<Vec<LintIssue>>;
    pub fn parse_coverage_json(path: &Path) -> Result<f64>;
    pub fn parse_complexity_json(path: &Path) -> Result<ComplexityMetrics>;
    pub fn aggregate_metrics(files: &[&Path]) -> Result<QualityMetrics>;
}

pub struct LintIssue {
    pub file: PathBuf,
    pub line: usize,
    pub rule: String,
    pub severity: String, // "error", "warning"
    pub message: String,
}
```

**Tool Integration Matrix**:

| Tool        | Format | Parser                    | Status  |
| ----------- | ------ | ------------------------- | ------- |
| ruff        | JSON   | `parse_ruff_json()`       | PoC     |
| oxlint      | JSON   | `parse_oxlint_json()`     | PoC     |
| coverage.py | JSON   | `parse_coverage_json()`   | Phase 2 |
| pytest-cov  | JSON   | `parse_pytest_cov_json()` | Phase 2 |
| semgrep     | JSON   | `parse_semgrep_json()`    | Phase 2 |

#### 1.4 SecurityScanner

**Purpose**: Detect secrets, SAST findings, and supply chain risks.

**Public API**:

```rust
pub struct SecurityScanner {
    secret_patterns: Vec<Regex>,
    sast_rules: HashMap<String, SastRule>,
}

pub struct SecurityFinding {
    pub severity: String, // "critical", "high", "medium", "low"
    pub finding_type: String, // "secret", "sast", "supply-chain"
    pub file: PathBuf,
    pub line: usize,
    pub message: String,
}

impl SecurityScanner {
    pub fn new() -> Result<Self>;
    pub fn scan_directory(&self, path: &Path) -> Result<Vec<SecurityFinding>>;
    pub fn scan_file(&self, path: &Path) -> Result<Vec<SecurityFinding>>;
    pub fn scan_content(&self, content: &str) -> Result<Vec<SecurityFinding>>;
    pub fn check_secrets(&self, content: &str) -> Result<Vec<SecretFinding>>;
}

pub struct SecretFinding {
    pub pattern: String,
    pub entropy: f64,
    pub location: String,
}
```

**Secret Patterns** (compiled regex):

```rust
lazy_static! {
    static ref SECRETS: Vec<Regex> = vec![
        Regex::new(r"sk-[a-zA-Z0-9]{48}").unwrap(),       // OpenAI
        Regex::new(r"AIza[0-9A-Za-z-_]{35}").unwrap(),    // Google
        Regex::new(r"xox[baprs]-[0-9]{12}").unwrap(),     // Slack
        Regex::new(r"ghp_[a-zA-Z0-9]{36}").unwrap(),      // GitHub PAT
        Regex::new(r"sq0atp-[0-9A-Za-z-_]{22}").unwrap(), // Square
        Regex::new(r"-----BEGIN [A-Z ]+ PRIVATE KEY-----").unwrap(),
    ];
}
```

#### 1.5 SpecVerifier

**Purpose**: Verify FR → test traceability and coverage.

**Public API**:

```rust
pub struct SpecVerifier {
    fr_index: HashMap<String, FunctionalRequirement>,
}

pub struct FunctionalRequirement {
    pub id: String,           // FR-AUTH-001
    pub title: String,
    pub acceptance_criteria: Vec<String>,
}

pub struct TestTraceability {
    pub fr_id: String,
    pub tests: Vec<TestRef>,
    pub coverage_percent: f64,
}

impl SpecVerifier {
    pub fn from_spec_file(path: &Path) -> Result<Self>;
    pub fn find_tests_for_fr(&self, fr_id: &str) -> Result<Vec<TestRef>>;
    pub fn find_orphan_tests(&self) -> Result<Vec<TestRef>>;
    pub fn find_uncovered_frs(&self) -> Result<Vec<String>>;
    pub fn coverage_report(&self) -> Result<SpecCoverageReport>;
}

pub struct SpecCoverageReport {
    pub total_frs: usize,
    pub covered_frs: usize,
    pub coverage_percent: f64,
    pub orphan_tests: Vec<TestRef>,
    pub uncovered_frs: Vec<String>,
}
```

---

### 2. Hook Binary Interface

**Pattern**: Each Rust hook is a standalone binary that uses the thegent-hooks library.

**Structure**:

```
thegent-hooks-quality-gate/
├── Cargo.toml
├── src/
│   └── main.rs
└── tests/
    └── integration_tests.rs

thegent-hooks-security-pipeline/
├── Cargo.toml
├── src/
│   └── main.rs
└── tests/
    └── integration_tests.rs
```

**Input/Output Contract** (same as Bash hooks):

**Stdin** (JSON):

```json
{
  "tool_name": "Write",
  "file_path": "/path/to/file.py",
  "project_dir": "/path/to/project",
  "session_id": "abc-123",
  "cwd": "/path/to/project"
}
```

**Exit Codes**:

- 0: Success (policy passed)
- 1: Failure (violations found, actionable)
- 124: Timeout
- 127+: Reserved for future use

**Stderr** (logging):

```
HOOK quality-gate: evaluating governance policy
HOOK quality-gate: loaded 5 rules from /path/to/policy.yaml
HOOK quality-gate: VIOLATION - coverage 65% < threshold 80%
HOOK quality-gate: VIOLATION - new lint suppressions (2) without justification
```

---

### 3. Configuration

**Governance Rules** (YAML):

```yaml
# ~/.claude/hooks/governance.yaml
policies:
  - id: cost-cap
    type: cost_cap
    provider: claude
    max_usd: 50.0
    period_days: 7
    enabled: true

  - id: coverage-threshold
    type: coverage_threshold
    min_percent: 80
    tools: [pytest, coverage]
    enabled: true

  - id: complexity-limit
    type: complexity_limit
    max_cyclomatic: 10
    max_cognitive: 15
    enabled: true

  - id: lint-suppressions
    type: lint_suppressions
    max_new_per_file: 3
    require_justification: true
    enabled: true

  - id: security-gate
    type: security_gate
    require_scan: true
    max_findings: 0
    enabled: true
```

**Quality Thresholds** (JSON):

```json
{
  "hooks": {
    "quality_gate": {
      "lint_error_limit": 10,
      "new_suppressions_limit": 3,
      "require_suppressions_justification": true
    },
    "security_pipeline": {
      "max_critical_findings": 0,
      "max_high_findings": 3,
      "require_sbom": false
    }
  }
}
```

---

### 4. Error Handling & Logging

**Custom Error Type**:

```rust
use thiserror::Error;

#[derive(Error, Debug)]
pub enum HookError {
    #[error("policy violation: {0}")]
    PolicyViolation(String),

    #[error("config error: {0}")]
    ConfigError(#[from] serde_json::Error),

    #[error("io error: {0}")]
    IoError(#[from] std::io::Error),

    #[error("regex error: {0}")]
    RegexError(#[from] regex::Error),

    #[error("timeout")]
    Timeout,
}

pub type Result<T> = std::result::Result<T, HookError>;
```

**Logging** (structured, to stderr):

```rust
eprintln!("HOOK quality-gate: {}", message);
eprintln!("HOOK quality-gate ERROR: {}", error);
eprintln!("HOOK quality-gate DEBUG: {}", debug_info);
```

---

### 5. Testing Strategy

**Unit Tests** (src/lib.rs):

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_policy_engine_loads_yaml() { }

    #[test]
    fn test_cost_calculator_estimates_correctly() { }

    #[test]
    fn test_quality_evaluator_parses_ruff_output() { }

    #[test]
    fn test_security_scanner_detects_secrets() { }
}
```

**Integration Tests** (tests/integration_tests.rs):

```rust
#[test]
fn test_quality_gate_end_to_end_pass() {
    // Create temp project with coverage > 80%
    // Run quality-gate hook
    // Assert exit code 0
}

#[test]
fn test_quality_gate_end_to_end_fail_low_coverage() {
    // Create temp project with coverage < 80%
    // Run quality-gate hook
    // Assert exit code 1
}
```

**Cross-Platform Testing**:

- macOS: Native build + test
- Linux: CI container (Ubuntu 22.04)
- Windows: WSL simulation (GitHub Actions)

**Coverage Target**: ≥ 85% (enforced by CI gate)

---

### 6. Performance Optimization

**Key Optimizations**:

1. **Lazy Static Regex**: Compile patterns once

   ```rust
   lazy_static! {
       static ref SECRET_REGEXES: Vec<Regex> = vec![...];
   }
   ```

2. **Parallel File Scanning**: Use rayon for multi-threaded analysis

   ```rust
   use rayon::prelude::*;

   files.par_iter()
       .flat_map(|f| scan_file(f))
       .collect()
   ```

3. **Caching**: DashMap for inter-hook result sharing

   ```rust
   static CACHE: Lazy<DashMap<String, PolicyOutcome>> =
       Lazy::new(DashMap::new);
   ```

4. **Early Exit**: Stop scanning on first critical finding
   ```rust
   if finding.severity == "critical" {
       return Err(HookError::PolicyViolation(msg));
   }
   ```

**Expected Latency Improvements**:

| Operation                       | Bash  | Rust | Gain |
| ------------------------------- | ----- | ---- | ---- |
| Parse 100 ruff JSON issues      | 150ms | 25ms | 83%  |
| Scan directory for secrets      | 200ms | 40ms | 80%  |
| Evaluate 10 policy rules        | 100ms | 15ms | 85%  |
| Aggregate coverage from 3 tools | 180ms | 30ms | 83%  |

---

## Integration Points

### With Existing Dispatcher

**No changes to hook-dispatcher Rust binary required for Phase 1**.

The dispatcher continues to:

1. Resolve hooks directory
2. Spawn hook scripts
3. Pass JSON via stdin
4. Collect stdout/stderr
5. Evaluate exit code

For Phase 2+, could add direct Rust hook execution (no spawning), but out of scope for Phase 1.

### With Quality Gates & Policy Engine

**Backward Compatible**: Existing Bash hooks continue to work. Rust hooks coexist.

**Gradual Migration**:

- Phase 1: Rust quality-gate, security-pipeline, stop-reconcile (3 hooks)
- Phase 1.5: Update dispatcher to recognize Rust vs Bash (optional optimization)
- Phase 2+: Migrate remaining 9 hooks incrementally

---

## Deployment & Versioning

### Build & Distribution

**Build**:

```bash
cargo build --release
# Outputs: target/release/quality-gate, target/release/security-pipeline, etc.
```

**Installation**:

```bash
# Copy to ~/.claude/hooks/
cp target/release/quality-gate ~/.claude/hooks/quality-gate-rs
cp target/release/security-pipeline ~/.claude/hooks/security-pipeline-rs
```

**Dispatcher Update** (Phase 2):
Hook dispatcher recognizes `.rs` suffix → calls directly (no bash spawn)

### Versioning

**Semantic Versioning**:

- `thegent-hooks 1.0.0` - PoC (Phase 1)
- `thegent-hooks 1.1.0` - Core library stable (Phase 1.5)
- `thegent-hooks 2.0.0` - Async runtime added (Phase 2)

**Compatibility**: Guarantee backward compatibility for JSON input/output contract across minor versions.

---

## Success Metrics

### Phase 1 Completion Criteria

| Criterion                   | Target | Status      |
| --------------------------- | ------ | ----------- |
| Governance library compiles | ✓      | Design      |
| quality-gate PoC in Rust    | ✓      | Design      |
| Performance 50% faster      | ✓      | Design      |
| 85%+ test coverage          | ✓      | Design      |
| Runs on macOS + Linux + WSL | ✓      | Design      |
| Tech spec documented        | ✓      | In Progress |

### Phase 1.1 Specific

- [ ] thegent-hooks library public API frozen
- [ ] CostCalculator estimates match pricing data
- [ ] SecurityScanner detects 100% of test secrets
- [ ] PolicyEngine evaluates complex rule sets (100+ rules)

### Phase 1.2 Quality-Gate PoC

- [ ] quality-gate rewrite complete (~150 LoC)
- [ ] Passes all existing integration tests
- [ ] 5x parallel execution benchmark shows 60% latency reduction
- [ ] Works on macOS 13+, Ubuntu 22.04+, WSL2

---

## Risk Mitigation

| Risk                       | Mitigation                                     |
| -------------------------- | ---------------------------------------------- |
| Rust learning curve        | Provide templates, patterns, code review       |
| Async complexity           | Phase 1 is sync; Phase 2 optional async        |
| Breaking API changes       | Semantic versioning, deprecation warnings      |
| Tool integration gaps      | Phase 2 covers remaining tools (semgrep, etc.) |
| Dependency vulnerabilities | Weekly audits via `cargo-audit`                |

---

## Appendix: Benchmark Methodology

**Baseline Run** (10 iterations, average):

```bash
time hook-dispatcher stop < hook-input.json
# Example: 1200ms (12 hooks × 100ms avg)
```

**PoC Rust Run** (10 iterations, average):

```bash
time ./quality-gate < hook-input.json
# Expected: 300-400ms total (quality-gate + security-pipeline + stop-reconcile)
# vs. 600ms for same 3 in Bash
```

**Metrics Collected**:

- Wall-clock time (start to exit)
- CPU time (user + system)
- Memory usage (peak RSS)
- Exit code and stderr output

---

**Status**: Design complete, ready for PoC implementation
**Version**: 1.0
**Next**: Begin Phase 1.1 (Governance Library PoC)
