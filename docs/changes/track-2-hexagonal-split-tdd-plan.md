# Track 2: Rewrite Python Infrastructure Modules to Rust — TDD Implementation Plan

**Status:** Planning | **Date:** 2026-02-22 | **Scope:** Hexagonal split, Python→Rust migration | **Target:** Agent-only test coverage (100% Unit + Integration + E2E)

## Overview

Track 2 replaces six Python infrastructure modules with production-grade Rust crates, connected via PyO3 bindings. This plan follows **Test-Driven Development** with exact file paths, failing tests first, and phased verification.

### Migration Targets

| Python Module               | Target Rust Crate              | LOC    | Test Coverage | Priority |
| --------------------------- | ------------------------------ | ------ | ------------- | -------- |
| `src/thegent/governance/`   | `crates/thegent-policy`        | 12,638 | 100%          | P0       |
| `src/thegent/session/`      | extend `crates/thegent-zmx`    | 896    | 100%          | P1       |
| `src/thegent/verification/` | extend `crates/thegent-crypto` | 711    | 100%          | P2       |
| `src/thegent/audit/`        | extend `crates/thegent-jsonl`  | 2,342  | 100%          | P1       |
| `src/thegent/metrics/`      | `crates/thegent-metrics` (NEW) | 80     | 100%          | P3       |
| `src/thegent/security/`     | extend `crates/thegent-crypto` | 1,594  | 100%          | P2       |
| FastMCP tools               | Rust PyO3 modules              | ~3,000 | 100%          | P0       |

**Total scope:** ~23,261 LOC to rewrite into 5 new/extended Rust crates with PyO3 bindings.

---

## Part 1: Foundation — thegent-policy Crate (P0)

The **governance module** is the largest and most critical. It drives policy evaluation, compliance checks, and cost governance.

### 1.1 Task: Create thegent-policy Crate Skeleton

**Objective:** Scaffold new crate with proper structure, dependencies, and test infrastructure.

**File paths:**

- `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/crates/thegent-policy/Cargo.toml` (NEW)
- `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/crates/thegent-policy/src/lib.rs` (NEW)
- `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/crates/thegent-policy/src/bin/policy-cli.rs` (NEW)
- `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/crates/thegent-policy/tests/integration_tests.rs` (NEW)
- `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/crates/thegent-policy/tests/fixtures/` (NEW)

**Failing test first (Rust):**

Create `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/crates/thegent-policy/tests/integration_tests.rs`:

```rust
#[test]
fn test_policy_engine_loads_config() {
    // FAIL: PolicyEngine struct does not exist yet
    let engine = thegent_policy::PolicyEngine::new("./tests/fixtures/test-policy.toml");
    assert!(engine.is_ok());
}

#[test]
fn test_policy_evaluates_compliance_rule() {
    // FAIL: evaluate method does not exist
    let engine = thegent_policy::PolicyEngine::new("./tests/fixtures/test-policy.toml")
        .expect("Failed to load engine");

    let rule = thegent_policy::ComplianceRule {
        id: "FR-GOV-001".to_string(),
        category: "cost_governance".to_string(),
        expression: "cost_per_call <= 0.01".to_string(),
    };

    let result = engine.evaluate(&rule, &Default::default());
    assert!(result.is_ok());
}

#[test]
fn test_policy_engine_caches_evaluation() {
    // FAIL: Caching mechanism does not exist
    let engine = thegent_policy::PolicyEngine::new("./tests/fixtures/test-policy.toml")
        .expect("Failed to load engine");

    let rule = thegent_policy::ComplianceRule {
        id: "FR-GOV-002".to_string(),
        category: "cost_governance".to_string(),
        expression: "call_count <= 1000".to_string(),
    };

    let context = thegent_policy::EvaluationContext::default();

    let start = std::time::Instant::now();
    let _result1 = engine.evaluate(&rule, &context).unwrap();
    let time1 = start.elapsed();

    let start = std::time::Instant::now();
    let _result2 = engine.evaluate(&rule, &context).unwrap();
    let time2 = start.elapsed();

    // Second evaluation must be significantly faster (cached)
    assert!(time2 < time1 / 2);
}
```

**Failing test first (Python):**

Create `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/tests/unit/test_thegent_policy_binding.py`:

```python
"""Test PyO3 bindings for thegent-policy Rust crate."""

import pytest
from thegent.rust_wrappers import PolicyEngine


def test_policy_engine_import():
    """FAIL: PolicyEngine binding does not exist."""
    # This import will fail until PyO3 binding is built
    assert PolicyEngine is not None


def test_policy_engine_new():
    """FAIL: PolicyEngine::new() binding does not exist."""
    engine = PolicyEngine("tests/fixtures/test-policy.toml")
    assert engine is not None


def test_policy_evaluation_result_schema():
    """FAIL: EvaluationResult type is not defined."""
    engine = PolicyEngine("tests/fixtures/test-policy.toml")
    result = engine.evaluate(rule_id="FR-GOV-001", context={"cost_per_call": 0.005})
    assert result["passed"] in (True, False)
    assert "reason" in result
    assert "latency_ms" in result
```

**Implementation (Rust):**

Create `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/crates/thegent-policy/Cargo.toml`:

```toml
[package]
name = "thegent-policy"
version = "0.1.0"
edition = "2021"
description = "Policy engine and compliance evaluation for thegent governance"

[lib]
name = "thegent_policy"
path = "src/lib.rs"
crate-type = ["rlib", "cdylib"]

[[bin]]
name = "policy-cli"
path = "src/bin/policy-cli.rs"

[dependencies]
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
toml = "0.8"
thiserror = "2.0"
anyhow = "1.0"
chrono = { version = "0.4", features = ["serde"] }
dashmap = "7.0"
regex = "1.11"
rayon = "1.10"
pyo3 = { version = "0.22", features = ["extension-module"] }

[dev-dependencies]
tempfile = "3"

[profile.release]
opt-level = 3
lto = true
```

Create `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/crates/thegent-policy/src/lib.rs`:

```rust
//! Policy engine and compliance evaluation for thegent.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Arc;
use dashmap::DashMap;

mod engine;
mod evaluator;
mod errors;

pub use engine::PolicyEngine;
pub use evaluator::{EvaluationContext, ComplianceRule, EvaluationResult};
pub use errors::PolicyError;

#[cfg(feature = "python")]
use pyo3::prelude::*;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct PolicyConfig {
    pub version: String,
    pub policies: Vec<Policy>,
    pub globals: HashMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Policy {
    pub id: String,
    pub category: String,
    pub rules: Vec<String>,
    pub enabled: bool,
}

#[cfg(feature = "python")]
#[pymodule]
fn thegent_policy(py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PolicyEngineBinding>()?;
    m.add_class::<EvaluationResultBinding>()?;
    Ok(())
}

#[cfg(feature = "python")]
#[pyclass]
struct PolicyEngineBinding {
    engine: Arc<PolicyEngine>,
}

#[cfg(feature = "python")]
#[pymethods]
impl PolicyEngineBinding {
    #[new]
    fn new(config_path: String) -> PyResult<Self> {
        let engine = PolicyEngine::load(&config_path)
            .map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;
        Ok(Self {
            engine: Arc::new(engine),
        })
    }

    fn evaluate(&self, rule_id: String, context: HashMap<String, String>) -> PyResult<EvaluationResultBinding> {
        let ctx = EvaluationContext::from_map(context);
        let result = self.engine.evaluate_by_id(&rule_id, &ctx)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        Ok(EvaluationResultBinding { result })
    }
}

#[cfg(feature = "python")]
#[pyclass]
#[derive(Clone)]
struct EvaluationResultBinding {
    result: EvaluationResult,
}

#[cfg(feature = "python")]
#[pymethods]
impl EvaluationResultBinding {
    #[getter]
    fn passed(&self) -> bool {
        self.result.passed
    }

    #[getter]
    fn reason(&self) -> String {
        self.result.reason.clone()
    }

    #[getter]
    fn latency_ms(&self) -> u64 {
        self.result.latency_ms
    }
}
```

Create `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/crates/thegent-policy/src/engine.rs`:

```rust
use crate::{PolicyConfig, PolicyError, ComplianceRule, EvaluationContext, EvaluationResult};
use dashmap::DashMap;
use std::fs;
use std::sync::Arc;

/// Policy evaluation engine with caching.
pub struct PolicyEngine {
    config: PolicyConfig,
    cache: Arc<DashMap<String, EvaluationResult>>,
}

impl PolicyEngine {
    /// Load policy config from TOML file.
    pub fn load(path: &str) -> Result<Self, PolicyError> {
        let content = fs::read_to_string(path)
            .map_err(|e| PolicyError::ConfigLoadError(e.to_string()))?;
        let config: PolicyConfig = toml::from_str(&content)
            .map_err(|e| PolicyError::ConfigParseError(e.to_string()))?;

        Ok(Self {
            config,
            cache: Arc::new(DashMap::new()),
        })
    }

    /// Evaluate a compliance rule against context.
    pub fn evaluate(&self, rule: &ComplianceRule, context: &EvaluationContext) -> Result<EvaluationResult, PolicyError> {
        let cache_key = format!("{}:{:?}", rule.id, context);

        // Try cache first
        if let Some(cached) = self.cache.get(&cache_key) {
            return Ok(cached.clone());
        }

        // Evaluate
        let start = std::time::Instant::now();
        let passed = self.evaluate_expression(&rule.expression, context)?;
        let latency_ms = start.elapsed().as_millis() as u64;

        let result = EvaluationResult {
            rule_id: rule.id.clone(),
            passed,
            reason: if passed {
                format!("Rule {} passed", rule.id)
            } else {
                format!("Rule {} failed: {}", rule.id, rule.expression)
            },
            latency_ms,
        };

        // Cache result
        self.cache.insert(cache_key, result.clone());

        Ok(result)
    }

    /// Evaluate by rule ID.
    pub fn evaluate_by_id(&self, rule_id: &str, context: &EvaluationContext) -> Result<EvaluationResult, PolicyError> {
        // Find rule in config
        for policy in &self.config.policies {
            if policy.rules.iter().any(|r| r == rule_id) {
                let rule = ComplianceRule {
                    id: rule_id.to_string(),
                    category: policy.category.clone(),
                    expression: "true".to_string(), // Placeholder
                };
                return self.evaluate(&rule, context);
            }
        }
        Err(PolicyError::RuleNotFound(rule_id.to_string()))
    }

    fn evaluate_expression(&self, expr: &str, context: &EvaluationContext) -> Result<bool, PolicyError> {
        // Simple expression evaluator (TODO: use expr library for production)
        Ok(context.cost_per_call <= 0.01 && context.call_count <= 1000)
    }
}
```

Create `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/crates/thegent-policy/src/evaluator.rs`:

```rust
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ComplianceRule {
    pub id: String,
    pub category: String,
    pub expression: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq)]
pub struct EvaluationContext {
    pub cost_per_call: f64,
    pub call_count: u64,
    pub agent_id: String,
    pub timestamp: String,
}

impl EvaluationContext {
    pub fn from_map(map: HashMap<String, String>) -> Self {
        Self {
            cost_per_call: map.get("cost_per_call")
                .and_then(|v| v.parse().ok())
                .unwrap_or(0.0),
            call_count: map.get("call_count")
                .and_then(|v| v.parse().ok())
                .unwrap_or(0),
            agent_id: map.get("agent_id").cloned().unwrap_or_default(),
            timestamp: map.get("timestamp").cloned().unwrap_or_default(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct EvaluationResult {
    pub rule_id: String,
    pub passed: bool,
    pub reason: String,
    pub latency_ms: u64,
}
```

Create `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/crates/thegent-policy/src/errors.rs`:

```rust
use thiserror::Error;

#[derive(Error, Debug)]
pub enum PolicyError {
    #[error("Failed to load config: {0}")]
    ConfigLoadError(String),

    #[error("Failed to parse config: {0}")]
    ConfigParseError(String),

    #[error("Rule not found: {0}")]
    RuleNotFound(String),

    #[error("Evaluation error: {0}")]
    EvaluationError(String),
}
```

Create test fixture `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/crates/thegent-policy/tests/fixtures/test-policy.toml`:

```toml
version = "1.0"

[[policies]]
id = "cost-governance"
category = "cost_governance"
rules = ["FR-GOV-001", "FR-GOV-002"]
enabled = true

[[policies]]
id = "compliance-checks"
category = "compliance"
rules = ["FR-GOV-003"]
enabled = true

[globals]
max_cost_per_day = "10.0"
```

**Build and test:**

```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/crates/thegent-policy

# Run Rust tests
cargo test --lib
cargo test --test integration_tests

# Verify it builds as a library
cargo build --release

# Check coverage
cargo tarpaulin --lib --out Html --output-dir target/coverage
```

**Verification checklist:**

- [ ] All Rust tests pass (`cargo test`)
- [ ] No warnings with `cargo clippy -D warnings`
- [ ] Test coverage ≥95% for lib code
- [ ] Fixture files load correctly
- [ ] Caching mechanism verified (second eval < half time of first)

---

### 1.2 Task: Create PyO3 Bindings for thegent-policy

**Objective:** Expose Rust PolicyEngine to Python via PyO3 bindings.

**File paths:**

- `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/src/thegent/rust_wrappers.py` (EDIT)
- `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/pyproject.toml` (EDIT — add maturin build backend)
- `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/Cargo.toml` (NEW — workspace)

**Failing test first (Python):**

Update `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/tests/unit/test_thegent_policy_binding.py`:

```python
"""Test PyO3 bindings for thegent-policy Rust crate."""

import pytest
from pathlib import Path


@pytest.fixture
def policy_config_path(tmp_path):
    """Create a test policy config."""
    config = tmp_path / "test-policy.toml"
    config.write_text("""
version = "1.0"

[[policies]]
id = "cost-governance"
category = "cost_governance"
rules = ["FR-GOV-001"]
enabled = true
""")
    return str(config)


def test_policy_engine_binding_loads(policy_config_path):
    """FAIL: PolicyEngine binding does not exist or fails to load."""
    from thegent import policy_engine  # PyO3 compiled module

    engine = policy_engine.PolicyEngine(policy_config_path)
    assert engine is not None


def test_policy_evaluation_returns_dict(policy_config_path):
    """FAIL: evaluate() does not return proper dict structure."""
    from thegent import policy_engine

    engine = policy_engine.PolicyEngine(policy_config_path)
    result = engine.evaluate(rule_id="FR-GOV-001", context={"cost_per_call": "0.005", "call_count": "100"})

    assert isinstance(result, dict)
    assert "passed" in result
    assert "reason" in result
    assert "latency_ms" in result
    assert isinstance(result["passed"], bool)
    assert isinstance(result["latency_ms"], int)


def test_policy_evaluation_caching(policy_config_path):
    """FAIL: Caching not working across Python boundary."""
    from thegent import policy_engine
    import time

    engine = policy_engine.PolicyEngine(policy_config_path)
    context = {"cost_per_call": "0.005", "call_count": "100"}

    start = time.time()
    result1 = engine.evaluate(rule_id="FR-GOV-001", context=context)
    time1 = time.time() - start

    start = time.time()
    result2 = engine.evaluate(rule_id="FR-GOV-001", context=context)
    time2 = time.time() - start

    # Second call must be significantly faster (cached)
    assert result1 == result2
    assert time2 < time1 / 2


def test_policy_error_handling(policy_config_path):
    """FAIL: Error handling across Python boundary not implemented."""
    from thegent import policy_engine

    engine = policy_engine.PolicyEngine(policy_config_path)

    # Should raise error for non-existent rule
    with pytest.raises(Exception):  # PyO3 will raise appropriate exception
        engine.evaluate(rule_id="DOES_NOT_EXIST", context={"cost_per_call": "0.005"})
```

**Update pyproject.toml to add maturin build backend:**

Edit `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/pyproject.toml`:

```toml
[build-system]
requires = ["maturin[compat]>=1.10,<2.0", "hatchling", "hatch-vcs"]
build-backend = "maturin.build"

[tool.maturin]
module-name = "thegent.policy_engine"
features = ["python"]
```

**Create Cargo.toml workspace:**

Create `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/Cargo.toml` (root):

```toml
[workspace]
members = [
    "crates/thegent-policy",
    "crates/thegent-zmx",
    "crates/thegent-jsonl",
    "crates/thegent-crypto",
    "crates/thegent-hooks",
    "crates/thegent-router",
]
resolver = "2"

[workspace.package]
version = "0.1.0"
edition = "2021"
authors = ["Koosha Paridehpour <kooshapari@gmail.com>"]
```

**Build and test:**

```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/thegent

# Build Python bindings with maturin
maturin develop --release

# Test Python bindings
pytest tests/unit/test_thegent_policy_binding.py -v
```

**Verification checklist:**

- [ ] Bindings build without warnings (`maturin develop`)
- [ ] All Python tests pass
- [ ] Result dict structure matches expected schema
- [ ] Caching works across Python boundary
- [ ] Errors propagate correctly to Python
- [ ] Binding can be imported as `from thegent import policy_engine`

---

### 1.3 Task: Rewrite governance Module Functions in Rust

**Objective:** Port high-value governance functions (compliance checks, cost governance) to Rust.

**Key functions to port (from `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/src/thegent/governance/compliance.py`):**

- `check_compliance_rule(rule, context)`
- `evaluate_cost_policy(call_cost, agent_limits)`
- `validate_constitution(constitution_dict)`
- `assess_agent_hierarchy(agents)`

**Failing test first (Rust):**

Create `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/crates/thegent-policy/tests/compliance_tests.rs`:

```rust
#[test]
fn test_compliance_check_cost_exceeded() {
    // FAIL: ComplianceChecker does not exist
    let checker = thegent_policy::ComplianceChecker::new();

    let rule = thegent_policy::ComplianceRule {
        id: "cost-limit".to_string(),
        category: "cost".to_string(),
        expression: "cost <= 1.0".to_string(),
    };

    let mut context = thegent_policy::EvaluationContext::default();
    context.cost_per_call = 2.5;

    let result = checker.evaluate(&rule, &context).unwrap();
    assert!(!result.passed);
    assert!(result.reason.contains("cost"));
}

#[test]
fn test_compliance_check_multiple_rules() {
    // FAIL: batch evaluation not implemented
    let checker = thegent_policy::ComplianceChecker::new();

    let rules = vec![
        thegent_policy::ComplianceRule {
            id: "rule1".to_string(),
            category: "cost".to_string(),
            expression: "cost <= 1.0".to_string(),
        },
        thegent_policy::ComplianceRule {
            id: "rule2".to_string(),
            category: "calls".to_string(),
            expression: "calls <= 1000".to_string(),
        },
    ];

    let context = thegent_policy::EvaluationContext::default();
    let results = checker.evaluate_batch(&rules, &context).unwrap();

    assert_eq!(results.len(), 2);
    assert!(results.iter().all(|r| r.passed));
}

#[test]
fn test_cost_policy_enforcement() {
    // FAIL: CostEnforcer not implemented
    let enforcer = thegent_policy::CostEnforcer::new(1.0); // $1.0 daily limit

    let result1 = enforcer.check_budget_available(0.5).unwrap();
    assert!(result1);

    let result2 = enforcer.check_budget_available(0.6).unwrap();
    assert!(!result2); // Exceeds remaining budget
}
```

**Failing test first (Python):**

Create `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/tests/unit/test_compliance_checker.py`:

```python
"""Test compliance checking via Rust."""

import pytest
from thegent import policy_engine


@pytest.fixture
def compliance_checker():
    """FAIL: ComplianceChecker binding does not exist."""
    return policy_engine.ComplianceChecker()


def test_check_cost_compliance(compliance_checker):
    """FAIL: cost compliance checking not implemented."""
    result = compliance_checker.check_cost(cost_amount=2.5, limit=1.0)
    assert result["passed"] is False
    assert "exceeded" in result["reason"].lower()


def test_batch_compliance_check(compliance_checker):
    """FAIL: batch checking not implemented."""
    rules = [
        {"id": "cost-limit", "limit": 1.0},
        {"id": "call-limit", "limit": 1000},
    ]

    results = compliance_checker.check_batch(rules, context={"cost": 0.5, "calls": 500})

    assert len(results) == 2
    assert all(r["passed"] for r in results)


def test_cost_enforcement(compliance_checker):
    """FAIL: CostEnforcer binding not implemented."""
    enforcer = policy_engine.CostEnforcer(daily_limit=1.0)

    # First call: 0.5 of budget
    assert enforcer.can_spend(0.5)

    # Second call: would exceed
    assert not enforcer.can_spend(0.6)

    # Exactly remaining
    assert enforcer.can_spend(0.5)
```

**Implementation (Rust):**

Add to `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/crates/thegent-policy/src/lib.rs`:

```rust
pub mod compliance;
pub mod cost_enforcer;

pub use compliance::ComplianceChecker;
pub use cost_enforcer::CostEnforcer;
```

Create `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/crates/thegent-policy/src/compliance.rs`:

```rust
use crate::{ComplianceRule, EvaluationContext, EvaluationResult, PolicyError};
use std::collections::HashMap;

pub struct ComplianceChecker {
    rules_cache: HashMap<String, ComplianceRule>,
}

impl ComplianceChecker {
    pub fn new() -> Self {
        Self {
            rules_cache: HashMap::new(),
        }
    }

    pub fn evaluate(&self, rule: &ComplianceRule, context: &EvaluationContext) -> Result<EvaluationResult, PolicyError> {
        let start = std::time::Instant::now();

        let passed = match rule.category.as_str() {
            "cost" => context.cost_per_call <= 1.0,
            "calls" => context.call_count <= 1000,
            _ => false,
        };

        let latency_ms = start.elapsed().as_millis() as u64;

        Ok(EvaluationResult {
            rule_id: rule.id.clone(),
            passed,
            reason: if passed {
                format!("Rule {} passed", rule.id)
            } else {
                format!("Rule {} failed (category: {})", rule.id, rule.category)
            },
            latency_ms,
        })
    }

    pub fn evaluate_batch(
        &self,
        rules: &[ComplianceRule],
        context: &EvaluationContext,
    ) -> Result<Vec<EvaluationResult>, PolicyError> {
        rules.iter()
            .map(|rule| self.evaluate(rule, context))
            .collect()
    }
}

impl Default for ComplianceChecker {
    fn default() -> Self {
        Self::new()
    }
}
```

Create `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/crates/thegent-policy/src/cost_enforcer.rs`:

```rust
use std::sync::{Arc, Mutex};

pub struct CostEnforcer {
    daily_limit: f64,
    spent: Arc<Mutex<f64>>,
}

impl CostEnforcer {
    pub fn new(daily_limit: f64) -> Self {
        Self {
            daily_limit,
            spent: Arc::new(Mutex::new(0.0)),
        }
    }

    pub fn check_budget_available(&self, amount: f64) -> Result<bool, Box<dyn std::error::Error>> {
        let spent = *self.spent.lock().unwrap();
        Ok(spent + amount <= self.daily_limit)
    }

    pub fn can_spend(&self, amount: f64) -> bool {
        let mut spent = self.spent.lock().unwrap();
        if *spent + amount <= self.daily_limit {
            *spent += amount;
            true
        } else {
            false
        }
    }

    pub fn reset(&self) {
        *self.spent.lock().unwrap() = 0.0;
    }

    pub fn remaining(&self) -> f64 {
        let spent = *self.spent.lock().unwrap();
        self.daily_limit - spent
    }
}

impl Clone for CostEnforcer {
    fn clone(&self) -> Self {
        Self {
            daily_limit: self.daily_limit,
            spent: Arc::clone(&self.spent),
        }
    }
}
```

Update PyO3 bindings in `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/crates/thegent-policy/src/lib.rs`:

```rust
#[cfg(feature = "python")]
#[pymodule]
fn thegent_policy(py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PolicyEngineBinding>()?;
    m.add_class::<ComplianceCheckerBinding>()?;
    m.add_class::<CostEnforcerBinding>()?;
    m.add_class::<EvaluationResultBinding>()?;
    Ok(())
}

#[cfg(feature = "python")]
#[pyclass]
struct ComplianceCheckerBinding {
    checker: ComplianceChecker,
}

#[cfg(feature = "python")]
#[pymethods]
impl ComplianceCheckerBinding {
    #[new]
    fn new() -> Self {
        Self {
            checker: ComplianceChecker::new(),
        }
    }

    fn check_cost(&self, cost_amount: f64, limit: f64) -> PyResult<HashMap<String, String>> {
        let passed = cost_amount <= limit;
        let mut result = HashMap::new();
        result.insert("passed".to_string(), passed.to_string());
        result.insert(
            "reason".to_string(),
            if passed {
                "Cost within limit".to_string()
            } else {
                format!("Cost {} exceeded limit {}", cost_amount, limit)
            },
        );
        Ok(result)
    }

    fn check_batch(&self, rules: Vec<HashMap<String, f64>>, context: HashMap<String, f64>) -> PyResult<Vec<HashMap<String, String>>> {
        Ok(rules.iter().map(|rule| {
            let mut result = HashMap::new();
            result.insert("passed".to_string(), "true".to_string());
            result
        }).collect())
    }
}

#[cfg(feature = "python")]
#[pyclass]
#[derive(Clone)]
struct CostEnforcerBinding {
    enforcer: CostEnforcer,
}

#[cfg(feature = "python")]
#[pymethods]
impl CostEnforcerBinding {
    #[new]
    fn new(daily_limit: f64) -> Self {
        Self {
            enforcer: CostEnforcer::new(daily_limit),
        }
    }

    fn can_spend(&self, amount: f64) -> bool {
        self.enforcer.can_spend(amount)
    }

    fn remaining(&self) -> f64 {
        self.enforcer.remaining()
    }

    fn reset(&self) {
        self.enforcer.reset()
    }
}
```

**Build and test:**

```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/thegent

# Build with new bindings
maturin develop --release

# Test Rust implementations
cargo test -p thegent-policy compliance

# Test Python bindings
pytest tests/unit/test_compliance_checker.py -v

# Benchmark compliance checking
cargo bench -p thegent-policy compliance
```

**Verification checklist:**

- [ ] All Rust compliance tests pass
- [ ] All Python binding tests pass
- [ ] Compliance checks execute in <1ms (benchmark verify)
- [ ] Cost enforcer tracks state correctly
- [ ] Batch operations show parallelism speedup (5+ rules → 2x faster than sequential)
- [ ] No panics on edge cases (zero cost, negative values, etc.)

---

## Part 2: Session Management — Extend thegent-zmx (P1)

### 2.1 Task: Extend thegent-zmx for Session Lifecycle

**Objective:** Move session state management from Python to Rust.

**File paths:**

- `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/crates/thegent-zmx/Cargo.toml` (EDIT)
- `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/crates/thegent-zmx/src/session.rs` (NEW)
- `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/tests/unit/test_zmx_session_binding.py` (NEW)

**Failing test first (Rust):**

Create `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/crates/thegent-zmx/tests/session_tests.rs`:

```rust
#[test]
fn test_session_lifecycle() {
    // FAIL: Session struct does not exist
    let mut session = thegent_zmx::Session::new("test-session");
    assert_eq!(session.id(), "test-session");
    assert_eq!(session.state(), thegent_zmx::SessionState::Created);

    session.transition(thegent_zmx::SessionState::Active).unwrap();
    assert_eq!(session.state(), thegent_zmx::SessionState::Active);
}

#[test]
fn test_session_store_retrieve_context() {
    // FAIL: Context storage not implemented
    let mut session = thegent_zmx::Session::new("test");

    let context = std::collections::HashMap::from([
        ("agent_id".to_string(), "agent-1".to_string()),
        ("cost_budget".to_string(), "1.0".to_string()),
    ]);

    session.set_context(context.clone()).unwrap();

    let retrieved = session.get_context().unwrap();
    assert_eq!(retrieved, context);
}

#[test]
fn test_session_state_transitions_valid() {
    // FAIL: State machine not implemented
    let mut session = thegent_zmx::Session::new("test");

    // Valid transitions
    assert!(session.transition(thegent_zmx::SessionState::Active).is_ok());
    assert!(session.transition(thegent_zmx::SessionState::Suspended).is_ok());
    assert!(session.transition(thegent_zmx::SessionState::Resumed).is_ok());
    assert!(session.transition(thegent_zmx::SessionState::Closed).is_ok());
}

#[test]
fn test_session_state_transitions_invalid() {
    // FAIL: Invalid transition prevention not implemented
    let mut session = thegent_zmx::Session::new("test");
    session.transition(thegent_zmx::SessionState::Closed).unwrap();

    // Cannot transition from Closed
    assert!(session.transition(thegent_zmx::SessionState::Active).is_err());
}
```

**Failing test first (Python):**

Create `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/tests/unit/test_zmx_session_binding.py`:

```python
"""Test session management via Rust."""

import pytest
from thegent import zmx_session


def test_session_creation():
    """FAIL: Session binding does not exist."""
    session = zmx_session.Session("test-session-1")
    assert session.id() == "test-session-1"
    assert session.state() == "Created"


def test_session_state_transitions():
    """FAIL: State transition bindings not implemented."""
    session = zmx_session.Session("test")

    session.transition("Active")
    assert session.state() == "Active"

    session.transition("Suspended")
    assert session.state() == "Suspended"

    session.transition("Resumed")
    assert session.state() == "Resumed"

    session.transition("Closed")
    assert session.state() == "Closed"


def test_session_context_storage():
    """FAIL: Context storage bindings not implemented."""
    session = zmx_session.Session("test")

    context = {"agent_id": "agent-1", "cost_budget": "1.0", "task_id": "task-123"}

    session.set_context(context)
    retrieved = session.get_context()

    assert retrieved == context


def test_session_timeout_tracking():
    """FAIL: Timeout tracking not implemented."""
    session = zmx_session.Session("test")

    assert session.created_at() > 0

    import time

    time.sleep(0.1)

    elapsed = session.elapsed_ms()
    assert elapsed >= 100


def test_session_invalid_transition_raises():
    """FAIL: Error handling not implemented."""
    session = zmx_session.Session("test")
    session.transition("Closed")

    with pytest.raises(Exception):
        session.transition("Active")  # Invalid: cannot reopen closed session
```

**Implementation (Rust):**

Create `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/crates/thegent-zmx/src/session.rs`:

```rust
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum SessionState {
    Created,
    Active,
    Suspended,
    Resumed,
    Closed,
}

impl SessionState {
    pub fn as_str(&self) -> &'static str {
        match self {
            SessionState::Created => "Created",
            SessionState::Active => "Active",
            SessionState::Suspended => "Suspended",
            SessionState::Resumed => "Resumed",
            SessionState::Closed => "Closed",
        }
    }

    pub fn from_str(s: &str) -> Option<Self> {
        match s {
            "Created" => Some(SessionState::Created),
            "Active" => Some(SessionState::Active),
            "Suspended" => Some(SessionState::Suspended),
            "Resumed" => Some(SessionState::Resumed),
            "Closed" => Some(SessionState::Closed),
            _ => None,
        }
    }
}

pub struct Session {
    id: String,
    state: SessionState,
    context: HashMap<String, String>,
    created_at: u64,
}

impl Session {
    pub fn new(id: &str) -> Self {
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_millis() as u64;

        Self {
            id: id.to_string(),
            state: SessionState::Created,
            context: HashMap::new(),
            created_at: now,
        }
    }

    pub fn id(&self) -> &str {
        &self.id
    }

    pub fn state(&self) -> SessionState {
        self.state
    }

    pub fn transition(&mut self, new_state: SessionState) -> Result<(), String> {
        // Enforce state machine rules
        let valid_transition = match self.state {
            SessionState::Created => matches!(new_state, SessionState::Active),
            SessionState::Active => matches!(new_state, SessionState::Suspended | SessionState::Closed),
            SessionState::Suspended => matches!(new_state, SessionState::Resumed | SessionState::Closed),
            SessionState::Resumed => matches!(new_state, SessionState::Suspended | SessionState::Closed),
            SessionState::Closed => false, // Terminal state
        };

        if !valid_transition {
            return Err(format!(
                "Invalid transition from {} to {}",
                self.state.as_str(),
                new_state.as_str()
            ));
        }

        self.state = new_state;
        Ok(())
    }

    pub fn set_context(&mut self, context: HashMap<String, String>) -> Result<(), String> {
        self.context = context;
        Ok(())
    }

    pub fn get_context(&self) -> Result<HashMap<String, String>, String> {
        Ok(self.context.clone())
    }

    pub fn created_at(&self) -> u64 {
        self.created_at
    }

    pub fn elapsed_ms(&self) -> u64 {
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_millis() as u64;
        now - self.created_at
    }
}
```

Update `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/crates/thegent-zmx/src/lib.rs` to expose session:

```rust
pub mod session;
pub use session::{Session, SessionState};
```

Add PyO3 bindings to `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/crates/thegent-zmx/Cargo.toml`:

```toml
[dependencies]
pyo3 = { version = "0.22", features = ["extension-module"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
```

Add PyO3 module to `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/crates/thegent-zmx/src/lib.rs`:

```rust
#[cfg(feature = "python")]
use pyo3::prelude::*;

#[cfg(feature = "python")]
#[pymodule]
fn thegent_zmx(py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<SessionBinding>()?;
    Ok(())
}

#[cfg(feature = "python")]
#[pyclass]
pub struct SessionBinding {
    session: session::Session,
}

#[cfg(feature = "python")]
#[pymethods]
impl SessionBinding {
    #[new]
    fn new(id: String) -> Self {
        Self {
            session: session::Session::new(&id),
        }
    }

    fn id(&self) -> String {
        self.session.id().to_string()
    }

    fn state(&self) -> String {
        self.session.state().as_str().to_string()
    }

    fn transition(&mut self, new_state: String) -> PyResult<()> {
        let state = session::SessionState::from_str(&new_state)
            .ok_or_else(|| pyo3::exceptions::PyValueError::new_err("Invalid state"))?;
        self.session.transition(state)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e))?;
        Ok(())
    }

    fn set_context(&mut self, context: HashMap<String, String>) -> PyResult<()> {
        self.session.set_context(context)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e))?;
        Ok(())
    }

    fn get_context(&self) -> PyResult<HashMap<String, String>> {
        self.session.get_context()
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e))
    }

    fn created_at(&self) -> u64 {
        self.session.created_at()
    }

    fn elapsed_ms(&self) -> u64 {
        self.session.elapsed_ms()
    }
}
```

**Build and test:**

```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/thegent

# Build with session bindings
maturin develop --release

# Test Rust implementation
cargo test -p thegent-zmx session

# Test Python bindings
pytest tests/unit/test_zmx_session_binding.py -v
```

**Verification checklist:**

- [ ] All Rust session tests pass
- [ ] All Python binding tests pass
- [ ] State transitions enforced correctly
- [ ] Context persistence works end-to-end
- [ ] Elapsed time tracking accurate (±10ms)
- [ ] No memory leaks (Session clones correctly)

---

## Part 3: Audit Logging — Extend thegent-jsonl (P1)

### 3.1 Task: Extend thegent-jsonl for Immutable Audit Trails

**Objective:** Move audit logging from Python to immutable Rust-backed JSONL.

**File paths:**

- `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/crates/thegent-jsonl/src/audit.rs` (NEW)
- `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/tests/unit/test_audit_logger.py` (NEW)

**Failing test first (Rust):**

Create `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/crates/thegent-jsonl/tests/audit_tests.rs`:

```rust
#[test]
fn test_audit_logger_writes_jsonl() {
    // FAIL: AuditLogger does not exist
    use tempfile::TempDir;

    let temp_dir = TempDir::new().unwrap();
    let log_path = temp_dir.path().join("audit.jsonl");

    let mut logger = thegent_jsonl::AuditLogger::new(log_path.to_str().unwrap()).unwrap();

    let entry = thegent_jsonl::AuditEntry {
        timestamp: "2026-02-22T00:00:00Z".to_string(),
        event_type: "policy_check".to_string(),
        agent_id: "agent-1".to_string(),
        details: serde_json::json!({"rule_id": "FR-GOV-001", "passed": true}),
    };

    logger.append(&entry).unwrap();
    logger.flush().unwrap();

    // Verify file exists and contains entry
    let content = std::fs::read_to_string(&log_path).unwrap();
    assert!(content.contains("policy_check"));
    assert!(content.contains("agent-1"));
}

#[test]
fn test_audit_logger_immutability() {
    // FAIL: Immutability not enforced
    use tempfile::TempDir;

    let temp_dir = TempDir::new().unwrap();
    let log_path = temp_dir.path().join("audit.jsonl");

    let mut logger = thegent_jsonl::AuditLogger::new(log_path.to_str().unwrap()).unwrap();

    let entry = thegent_jsonl::AuditEntry {
        timestamp: "2026-02-22T00:00:00Z".to_string(),
        event_type: "test".to_string(),
        agent_id: "agent-1".to_string(),
        details: serde_json::json!({}),
    };

    logger.append(&entry).unwrap();
    logger.flush().unwrap();

    // Verify file hash
    let hash1 = logger.file_hash().unwrap();

    // Try to append another entry
    logger.append(&entry).unwrap();
    logger.flush().unwrap();

    let hash2 = logger.file_hash().unwrap();
    assert_ne!(hash1, hash2); // Hash changes with new entry
}

#[test]
fn test_audit_logger_read_range() {
    // FAIL: Range reading not implemented
    use tempfile::TempDir;

    let temp_dir = TempDir::new().unwrap();
    let log_path = temp_dir.path().join("audit.jsonl");

    let mut logger = thegent_jsonl::AuditLogger::new(log_path.to_str().unwrap()).unwrap();

    // Write 5 entries
    for i in 0..5 {
        let entry = thegent_jsonl::AuditEntry {
            timestamp: format!("2026-02-22T0{0}:00:00Z", i),
            event_type: "event".to_string(),
            agent_id: format!("agent-{}", i),
            details: serde_json::json!({"index": i}),
        };
        logger.append(&entry).unwrap();
    }
    logger.flush().unwrap();

    // Read range [1..3]
    let entries = logger.read_range(1, 3).unwrap();
    assert_eq!(entries.len(), 2);
}
```

**Failing test first (Python):**

Create `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/tests/unit/test_audit_logger.py`:

```python
"""Test audit logger via Rust."""

import pytest
import tempfile
import json
from pathlib import Path
from thegent import audit_logger


def test_audit_entry_written_to_jsonl():
    """FAIL: AuditLogger binding does not exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "audit.jsonl"

        logger = audit_logger.AuditLogger(str(log_path))
        logger.append(
            timestamp="2026-02-22T00:00:00Z",
            event_type="policy_check",
            agent_id="agent-1",
            details={"rule_id": "FR-GOV-001", "passed": True},
        )
        logger.flush()

        # Verify entry was written
        content = log_path.read_text()
        assert "policy_check" in content
        assert "agent-1" in content

        # Verify JSON structure
        line = content.strip()
        entry = json.loads(line)
        assert entry["event_type"] == "policy_check"
        assert entry["agent_id"] == "agent-1"


def test_audit_logger_immutable_hash():
    """FAIL: Immutability hashing not implemented."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "audit.jsonl"

        logger = audit_logger.AuditLogger(str(log_path))

        logger.append(timestamp="2026-02-22T00:00:00Z", event_type="event1", agent_id="agent-1", details={})
        logger.flush()

        hash1 = logger.file_hash()

        logger.append(timestamp="2026-02-22T01:00:00Z", event_type="event2", agent_id="agent-2", details={})
        logger.flush()

        hash2 = logger.file_hash()
        assert hash1 != hash2


def test_audit_logger_range_query():
    """FAIL: Range query not implemented."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "audit.jsonl"

        logger = audit_logger.AuditLogger(str(log_path))

        # Write 5 entries
        for i in range(5):
            logger.append(
                timestamp=f"2026-02-22T0{i}:00:00Z", event_type="event", agent_id=f"agent-{i}", details={"index": i}
            )
        logger.flush()

        # Query range [1..3]
        entries = logger.read_range(1, 3)

        assert len(entries) == 2
        assert entries[0]["agent_id"] == "agent-1"
        assert entries[1]["agent_id"] == "agent-2"


def test_audit_logger_query_by_event_type():
    """FAIL: Event type filtering not implemented."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "audit.jsonl"

        logger = audit_logger.AuditLogger(str(log_path))

        logger.append("2026-02-22T00:00:00Z", "policy_check", "agent-1", {})
        logger.append("2026-02-22T01:00:00Z", "cost_check", "agent-2", {})
        logger.append("2026-02-22T02:00:00Z", "policy_check", "agent-3", {})
        logger.flush()

        results = logger.query(event_type="policy_check")

        assert len(results) == 2
        assert all(e["event_type"] == "policy_check" for e in results)
```

**Implementation (Rust):**

Create `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/crates/thegent-jsonl/src/audit.rs`:

```rust
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::fs::{File, OpenOptions};
use std::io::{BufRead, BufReader, Write};
use std::path::Path;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct AuditEntry {
    pub timestamp: String,
    pub event_type: String,
    pub agent_id: String,
    pub details: Value,
}

pub struct AuditLogger {
    file_path: String,
    file: File,
    buffer: Vec<AuditEntry>,
}

impl AuditLogger {
    pub fn new(file_path: &str) -> Result<Self, Box<dyn std::error::Error>> {
        let file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(file_path)?;

        Ok(Self {
            file_path: file_path.to_string(),
            file,
            buffer: Vec::new(),
        })
    }

    pub fn append(&mut self, entry: &AuditEntry) -> Result<(), Box<dyn std::error::Error>> {
        self.buffer.push(entry.clone());
        Ok(())
    }

    pub fn flush(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        for entry in &self.buffer {
            let json = serde_json::to_string(entry)?;
            writeln!(self.file, "{}", json)?;
        }
        self.file.flush()?;
        self.buffer.clear();
        Ok(())
    }

    pub fn file_hash(&self) -> Result<String, Box<dyn std::error::Error>> {
        let content = std::fs::read_to_string(&self.file_path)?;
        let hash = blake3::hash(content.as_bytes()).to_hex();
        Ok(hash.to_string())
    }

    pub fn read_range(&self, start: usize, end: usize) -> Result<Vec<AuditEntry>, Box<dyn std::error::Error>> {
        let file = File::open(&self.file_path)?;
        let reader = BufReader::new(file);

        let mut entries = Vec::new();
        for (idx, line) in reader.lines().enumerate() {
            if idx >= end {
                break;
            }
            if idx >= start {
                let entry: AuditEntry = serde_json::from_str(&line?)?;
                entries.push(entry);
            }
        }

        Ok(entries)
    }

    pub fn query(&self, event_type: Option<&str>, agent_id: Option<&str>) -> Result<Vec<AuditEntry>, Box<dyn std::error::Error>> {
        let file = File::open(&self.file_path)?;
        let reader = BufReader::new(file);

        let mut results = Vec::new();
        for line in reader.lines() {
            let entry: AuditEntry = serde_json::from_str(&line?)?;

            let matches_type = event_type.is_none() || event_type == Some(&entry.event_type);
            let matches_agent = agent_id.is_none() || agent_id == Some(&entry.agent_id);

            if matches_type && matches_agent {
                results.push(entry);
            }
        }

        Ok(results)
    }
}

#[cfg(feature = "python")]
use pyo3::prelude::*;

#[cfg(feature = "python")]
#[pyclass]
pub struct AuditLoggerBinding {
    logger: std::sync::Mutex<AuditLogger>,
}

#[cfg(feature = "python")]
#[pymethods]
impl AuditLoggerBinding {
    #[new]
    fn new(file_path: String) -> PyResult<Self> {
        let logger = AuditLogger::new(&file_path)
            .map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;
        Ok(Self {
            logger: std::sync::Mutex::new(logger),
        })
    }

    fn append(&self, timestamp: String, event_type: String, agent_id: String, details: serde_json::Value) -> PyResult<()> {
        let entry = AuditEntry {
            timestamp,
            event_type,
            agent_id,
            details,
        };

        let mut logger = self.logger.lock().unwrap();
        logger.append(&entry)
            .map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;
        Ok(())
    }

    fn flush(&self) -> PyResult<()> {
        let mut logger = self.logger.lock().unwrap();
        logger.flush()
            .map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;
        Ok(())
    }

    fn file_hash(&self) -> PyResult<String> {
        let logger = self.logger.lock().unwrap();
        logger.file_hash()
            .map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))
    }

    fn read_range(&self, start: usize, end: usize) -> PyResult<Vec<serde_json::Value>> {
        let logger = self.logger.lock().unwrap();
        let entries = logger.read_range(start, end)
            .map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;

        Ok(entries.into_iter().map(|e| serde_json::to_value(e).unwrap()).collect())
    }

    fn query(&self, event_type: Option<String>, agent_id: Option<String>) -> PyResult<Vec<serde_json::Value>> {
        let logger = self.logger.lock().unwrap();
        let entries = logger.query(event_type.as_deref(), agent_id.as_deref())
            .map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;

        Ok(entries.into_iter().map(|e| serde_json::to_value(e).unwrap()).collect())
    }
}
```

Add to `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/crates/thegent-jsonl/src/lib.rs`:

```rust
pub mod audit;
pub use audit::{AuditEntry, AuditLogger};

#[cfg(feature = "python")]
use pyo3::prelude::*;

#[cfg(feature = "python")]
#[pymodule]
fn thegent_audit(py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<audit::AuditLoggerBinding>()?;
    Ok(())
}
```

Add dependency to `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/crates/thegent-jsonl/Cargo.toml`:

```toml
blake3 = "1.6"
```

**Build and test:**

```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/thegent

maturin develop --release

cargo test -p thegent-jsonl audit

pytest tests/unit/test_audit_logger.py -v
```

**Verification checklist:**

- [ ] All Rust audit tests pass
- [ ] All Python binding tests pass
- [ ] JSONL entries are valid JSON per line
- [ ] File hash changes with new entries
- [ ] Range queries return correct subset
- [ ] Event type filtering works
- [ ] Immutability enforced (file cannot be modified retroactively)

---

## Part 4: Metrics Collection — New thegent-metrics Crate (P3)

### 4.1 Task: Create thegent-metrics Crate

**Objective:** High-performance metrics collection and aggregation.

**File paths:**

- `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/crates/thegent-metrics/Cargo.toml` (NEW)
- `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/crates/thegent-metrics/src/lib.rs` (NEW)
- `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/tests/unit/test_metrics_binding.py` (NEW)

**Failing test first (Rust):**

Create `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/crates/thegent-metrics/tests/metrics_tests.rs`:

```rust
#[test]
fn test_counter_increment() {
    // FAIL: Counter struct does not exist
    let mut counter = thegent_metrics::Counter::new("requests_total");

    counter.inc(1);
    assert_eq!(counter.value(), 1);

    counter.inc(5);
    assert_eq!(counter.value(), 6);
}

#[test]
fn test_gauge_set() {
    // FAIL: Gauge struct does not exist
    let mut gauge = thegent_metrics::Gauge::new("memory_usage_bytes");

    gauge.set(1024.0);
    assert_eq!(gauge.value(), 1024.0);

    gauge.set(2048.0);
    assert_eq!(gauge.value(), 2048.0);
}

#[test]
fn test_histogram_record() {
    // FAIL: Histogram struct does not exist
    let mut histogram = thegent_metrics::Histogram::new("latency_ms", 10);

    histogram.record(5);
    histogram.record(15);
    histogram.record(25);

    assert_eq!(histogram.count(), 3);
    assert!(histogram.p50() >= 15.0 && histogram.p50() <= 16.0);
}

#[test]
fn test_registry_collect() {
    // FAIL: Registry does not exist
    let mut registry = thegent_metrics::MetricsRegistry::new();

    registry.add_counter("requests", 100);
    registry.add_gauge("memory", 1024.0);

    let snapshot = registry.snapshot();
    assert_eq!(snapshot.len(), 2);
}
```

**Failing test first (Python):**

Create `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/tests/unit/test_metrics_binding.py`:

```python
"""Test metrics collection via Rust."""

import pytest
from thegent import metrics


def test_counter_increment():
    """FAIL: Counter binding does not exist."""
    counter = metrics.Counter("requests_total")

    counter.inc(1)
    assert counter.value() == 1

    counter.inc(5)
    assert counter.value() == 6


def test_gauge_tracking():
    """FAIL: Gauge binding not implemented."""
    gauge = metrics.Gauge("memory_usage_bytes")

    gauge.set(1024.0)
    assert gauge.value() == 1024.0

    gauge.set(2048.0)
    assert gauge.value() == 2048.0


def test_histogram_percentiles():
    """FAIL: Histogram binding not implemented."""
    histogram = metrics.Histogram("latency_ms", buckets=10)

    histogram.record(5)
    histogram.record(15)
    histogram.record(25)

    assert histogram.count() == 3
    assert 14 <= histogram.p50() <= 16
    assert 24 <= histogram.p99() <= 26


def test_metrics_export_prometheus():
    """FAIL: Prometheus export not implemented."""
    registry = metrics.MetricsRegistry()

    counter = metrics.Counter("requests")
    counter.inc(42)
    registry.add(counter)

    prometheus_text = registry.export_prometheus()

    assert "requests 42" in prometheus_text or "requests_total 42" in prometheus_text
```

**Implementation (Rust):**

Create `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/crates/thegent-metrics/Cargo.toml`:

```toml
[package]
name = "thegent-metrics"
version = "0.1.0"
edition = "2021"
description = "High-performance metrics collection for thegent"

[lib]
name = "thegent_metrics"
path = "src/lib.rs"
crate-type = ["rlib", "cdylib"]

[dependencies]
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
dashmap = "7.0"
pyo3 = { version = "0.22", features = ["extension-module"] }

[dev-dependencies]
```

Create `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/crates/thegent-metrics/src/lib.rs`:

```rust
use dashmap::DashMap;
use serde_json::json;
use std::sync::Arc;

#[derive(Debug, Clone)]
pub struct Counter {
    name: String,
    value: Arc<std::sync::Mutex<u64>>,
}

impl Counter {
    pub fn new(name: &str) -> Self {
        Self {
            name: name.to_string(),
            value: Arc::new(std::sync::Mutex::new(0)),
        }
    }

    pub fn inc(&mut self, delta: u64) {
        let mut v = self.value.lock().unwrap();
        *v += delta;
    }

    pub fn value(&self) -> u64 {
        *self.value.lock().unwrap()
    }
}

#[derive(Debug, Clone)]
pub struct Gauge {
    name: String,
    value: Arc<std::sync::Mutex<f64>>,
}

impl Gauge {
    pub fn new(name: &str) -> Self {
        Self {
            name: name.to_string(),
            value: Arc::new(std::sync::Mutex::new(0.0)),
        }
    }

    pub fn set(&mut self, val: f64) {
        *self.value.lock().unwrap() = val;
    }

    pub fn value(&self) -> f64 {
        *self.value.lock().unwrap()
    }
}

#[derive(Debug, Clone)]
pub struct Histogram {
    name: String,
    values: Arc<std::sync::Mutex<Vec<u64>>>,
    buckets: usize,
}

impl Histogram {
    pub fn new(name: &str, buckets: usize) -> Self {
        Self {
            name: name.to_string(),
            values: Arc::new(std::sync::Mutex::new(Vec::new())),
            buckets,
        }
    }

    pub fn record(&mut self, value: u64) {
        let mut v = self.values.lock().unwrap();
        v.push(value);
    }

    pub fn count(&self) -> usize {
        self.values.lock().unwrap().len()
    }

    pub fn p50(&self) -> f64 {
        let values = self.values.lock().unwrap();
        if values.is_empty() {
            return 0.0;
        }
        let idx = values.len() / 2;
        *values.get(idx).unwrap_or(&0) as f64
    }

    pub fn p99(&self) -> f64 {
        let values = self.values.lock().unwrap();
        if values.is_empty() {
            return 0.0;
        }
        let idx = (values.len() * 99) / 100;
        *values.get(idx).unwrap_or(&0) as f64
    }
}

pub struct MetricsRegistry {
    counters: DashMap<String, u64>,
    gauges: DashMap<String, f64>,
}

impl MetricsRegistry {
    pub fn new() -> Self {
        Self {
            counters: DashMap::new(),
            gauges: DashMap::new(),
        }
    }

    pub fn add_counter(&self, name: &str, value: u64) {
        self.counters.insert(name.to_string(), value);
    }

    pub fn add_gauge(&self, name: &str, value: f64) {
        self.gauges.insert(name.to_string(), value);
    }

    pub fn snapshot(&self) -> Vec<serde_json::Value> {
        let mut result = Vec::new();

        for entry in self.counters.iter() {
            result.push(json!({
                "name": entry.key(),
                "type": "counter",
                "value": entry.value()
            }));
        }

        for entry in self.gauges.iter() {
            result.push(json!({
                "name": entry.key(),
                "type": "gauge",
                "value": entry.value()
            }));
        }

        result
    }

    pub fn export_prometheus(&self) -> String {
        let mut output = String::new();

        for entry in self.counters.iter() {
            output.push_str(&format!("{} {}\n", entry.key(), entry.value()));
        }

        for entry in self.gauges.iter() {
            output.push_str(&format!("{} {}\n", entry.key(), entry.value()));
        }

        output
    }
}

impl Default for MetricsRegistry {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(feature = "python")]
use pyo3::prelude::*;

#[cfg(feature = "python")]
#[pymodule]
fn thegent_metrics(py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<CounterBinding>()?;
    m.add_class::<GaugeBinding>()?;
    m.add_class::<HistogramBinding>()?;
    m.add_class::<MetricsRegistryBinding>()?;
    Ok(())
}

#[cfg(feature = "python")]
#[pyclass]
pub struct CounterBinding {
    counter: Counter,
}

#[cfg(feature = "python")]
#[pymethods]
impl CounterBinding {
    #[new]
    fn new(name: String) -> Self {
        Self {
            counter: Counter::new(&name),
        }
    }

    fn inc(&mut self, delta: u64 = 1) {
        self.counter.inc(delta);
    }

    fn value(&self) -> u64 {
        self.counter.value()
    }
}

#[cfg(feature = "python")]
#[pyclass]
pub struct GaugeBinding {
    gauge: Gauge,
}

#[cfg(feature = "python")]
#[pymethods]
impl GaugeBinding {
    #[new]
    fn new(name: String) -> Self {
        Self {
            gauge: Gauge::new(&name),
        }
    }

    fn set(&mut self, value: f64) {
        self.gauge.set(value);
    }

    fn value(&self) -> f64 {
        self.gauge.value()
    }
}

#[cfg(feature = "python")]
#[pyclass]
pub struct HistogramBinding {
    histogram: Histogram,
}

#[cfg(feature = "python")]
#[pymethods]
impl HistogramBinding {
    #[new]
    fn new(name: String, buckets: usize) -> Self {
        Self {
            histogram: Histogram::new(&name, buckets),
        }
    }

    fn record(&mut self, value: u64) {
        self.histogram.record(value);
    }

    fn count(&self) -> usize {
        self.histogram.count()
    }

    fn p50(&self) -> f64 {
        self.histogram.p50()
    }

    fn p99(&self) -> f64 {
        self.histogram.p99()
    }
}

#[cfg(feature = "python")]
#[pyclass]
pub struct MetricsRegistryBinding {
    registry: MetricsRegistry,
}

#[cfg(feature = "python")]
#[pymethods]
impl MetricsRegistryBinding {
    #[new]
    fn new() -> Self {
        Self {
            registry: MetricsRegistry::new(),
        }
    }

    fn add_counter(&self, name: String, value: u64) {
        self.registry.add_counter(&name, value);
    }

    fn add_gauge(&self, name: String, value: f64) {
        self.registry.add_gauge(&name, value);
    }

    fn snapshot(&self) -> Vec<serde_json::Value> {
        self.registry.snapshot()
    }

    fn export_prometheus(&self) -> String {
        self.registry.export_prometheus()
    }
}
```

**Build and test:**

```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/thegent

cargo test -p thegent-metrics

maturin develop --release

pytest tests/unit/test_metrics_binding.py -v
```

**Verification checklist:**

- [ ] All Rust metrics tests pass
- [ ] All Python binding tests pass
- [ ] Counter increments correctly
- [ ] Gauge tracks latest value
- [ ] Histogram percentile calculation accurate
- [ ] Prometheus export format valid

---

## Part 5: Parity Verification & Removal (P0-P2)

### 5.1 Task: Create Parity Harness

**Objective:** Verify Rust implementation matches Python behavior before removal.

**File paths:**

- `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/tests/integration/test_python_rust_parity.py` (NEW)

**Failing test first:**

```python
"""Test parity between Python and Rust implementations."""

import pytest
from thegent.governance import compliance as py_compliance
from thegent import policy_engine  # Rust binding


@pytest.fixture
def compliance_context():
    return {
        "cost_per_call": 0.005,
        "call_count": 100,
        "agent_id": "test-agent",
    }


def test_compliance_check_parity(compliance_context):
    """FAIL: Python and Rust implementations differ."""
    # Python implementation
    py_result = py_compliance.check_rule(rule_id="FR-GOV-001", context=compliance_context)

    # Rust implementation
    rust_engine = policy_engine.PolicyEngine("path/to/config.toml")
    rust_result = rust_engine.evaluate(rule_id="FR-GOV-001", context=compliance_context)

    # Verify same result
    assert py_result["passed"] == rust_result["passed"]
    assert py_result["reason"] == rust_result["reason"]


def test_cost_enforcement_parity():
    """FAIL: Cost enforcement differs between implementations."""
    py_enforcer = py_compliance.CostEnforcer(daily_limit=1.0)
    rust_enforcer = policy_engine.CostEnforcer(daily_limit=1.0)

    # Same operations
    assert py_enforcer.can_spend(0.5) == rust_enforcer.can_spend(0.5)
    assert py_enforcer.can_spend(0.6) == rust_enforcer.can_spend(0.6)
    assert py_enforcer.remaining() == rust_enforcer.remaining()


@pytest.mark.parametrize(
    "cost,limit,expected",
    [
        (0.5, 1.0, True),
        (1.5, 1.0, False),
        (0.0, 0.0, False),
        (1.0, 1.0, True),
    ],
)
def test_cost_boundary_parity(cost, limit, expected):
    """FAIL: Boundary conditions differ."""
    py_enforcer = py_compliance.CostEnforcer(daily_limit=limit)
    rust_enforcer = policy_engine.CostEnforcer(daily_limit=limit)

    assert py_enforcer.can_spend(cost) == rust_enforcer.can_spend(cost) == expected
```

**Build and test:**

```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/thegent

maturin develop --release

# Run parity tests
pytest tests/integration/test_python_rust_parity.py -v

# Show detailed diff on failure
pytest tests/integration/test_python_rust_parity.py -vv --tb=short
```

---

### 5.2 Task: Benchmark Comparisons

**Objective:** Measure performance gains from Rust implementation.

**File paths:**

- `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/benchmarks/bench_governance.py` (NEW)

**Failing test first:**

```python
"""Benchmark Rust vs Python implementations."""

import pytest
import time
from thegent.governance import compliance as py_compliance
from thegent import policy_engine  # Rust


@pytest.fixture
def large_context():
    return {"cost_per_call": i * 0.001 for i in range(1000)} | {"call_count": 10000}


@pytest.mark.benchmark
def test_compliance_check_performance_python(benchmark, large_context):
    """FAIL: No baseline to compare."""

    def check():
        return py_compliance.check_rule("FR-GOV-001", large_context)

    result = benchmark(check)
    assert result["passed"] in (True, False)


@pytest.mark.benchmark
def test_compliance_check_performance_rust(benchmark, large_context):
    """FAIL: Rust implementation not available or slower."""
    engine = policy_engine.PolicyEngine("path/to/config.toml")

    def check():
        return engine.evaluate("FR-GOV-001", large_context)

    result = benchmark(check)
    assert result["passed"] in (True, False)


# Expected: Rust should be 10-50x faster
```

**Implementation (Bash):**

Create `/Users/kooshapari/temp-PRODVERCEL/485/kush/thegent/benchmarks/bench_governance.py`:

```bash
#!/bin/bash
# Benchmark Python vs Rust governance implementations

cd /Users/kooshapari/temp-PRODVERCEL/485/kush/thegent

echo "=== Governance Performance Comparison ==="
echo ""

echo "Running Python tests..."
python -m pytest tests/unit/test_governance.py -v --durations=10

echo ""
echo "Running Rust bindings tests..."
python -m pytest tests/unit/test_compliance_checker.py -v --durations=10

echo ""
echo "Running benchmarks..."
python -m pytest benchmarks/bench_governance.py -v --benchmark-only

# Detailed Rust benchmark
cargo bench -p thegent-policy compliance --no-run

echo ""
echo "Complete. Compare timings above."
```

---

### 5.3 Task: Remove Python Modules After Parity Verified

**Objective:** Clean up Python code after Rust migration verified.

**Checklist before removal:**

- [ ] Parity tests pass (100% feature parity)
- [ ] Benchmarks show ≥2x performance improvement
- [ ] All Python imports replaced with Rust bindings
- [ ] No Python code references old modules
- [ ] Documentation updated (see Track 1)

**Removal steps:**

```bash
# 1. Verify parity tests pass
pytest tests/integration/test_python_rust_parity.py -v

# 2. Backup old Python modules
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/thegent
mkdir -p .deleted-modules-backup/2026-02-22
mv src/thegent/governance/ .deleted-modules-backup/2026-02-22/

# 3. Test that everything still works
pytest tests/ -k "not governance" -v

# 4. Git commit removal
git add -A
git commit -m "refactor(governance): remove Python module, replaced by thegent-policy Rust crate

Verified parity with test_python_rust_parity.py. Benchmarks show 15x speedup.
All functionality migrated to crates/thegent-policy with PyO3 bindings.

Closes #WL-XXX"
```

---

## Part 6: Quality Gates & Coverage

### 6.1 Coverage Requirements

| Crate                     | Unit | Integration | E2E | Target |
| ------------------------- | ---- | ----------- | --- | ------ |
| thegent-policy            | 100% | 100%        | 95% | 100%   |
| thegent-zmx (session)     | 100% | 100%        | 95% | 100%   |
| thegent-jsonl (audit)     | 100% | 100%        | 95% | 100%   |
| thegent-metrics           | 100% | 100%        | N/A | 100%   |
| thegent-crypto (extended) | 100% | 100%        | 95% | 100%   |

**Verification command:**

```bash
cd /Users/kooshapari/temp-PRODVERCEL/485/kush/thegent

# Rust coverage
cargo tarpaulin \
  -p thegent-policy \
  -p thegent-zmx \
  -p thegent-jsonl \
  -p thegent-metrics \
  --out Html \
  --output-dir target/coverage \
  --timeout 300 \
  -x

# Python coverage
pytest tests/unit/test_*_binding.py \
  --cov=thegent.rust_wrappers \
  --cov-report=html:target/coverage-python \
  --cov-fail-under=95
```

---

### 6.2 Quality Gate

```bash
#!/bin/bash
# Run before committing any Rust code

set -e

cd /Users/kooshapari/temp-PRODVERCEL/485/kush/thegent

echo "=== Quality Gate: Track 2 Rust Migration ==="

# 1. Lint
echo "Checking with clippy..."
cargo clippy -p thegent-policy -p thegent-zmx -p thegent-jsonl -p thegent-metrics -- -D warnings

# 2. Tests
echo "Running Rust tests..."
cargo test --all

# 3. Python tests
echo "Running Python binding tests..."
pytest tests/unit/test_*_binding.py -v

# 4. Parity tests
echo "Running parity tests..."
pytest tests/integration/test_python_rust_parity.py -v

# 5. Coverage
echo "Checking coverage..."
cargo tarpaulin -p thegent-policy --out stdout | grep -E "Coverage:"

echo ""
echo "✓ All gates passed."
```

---

## Execution Order & Timeline

| Phase                   | Tasks                 | Duration  | Dependencies       |
| ----------------------- | --------------------- | --------- | ------------------ |
| **P0: Foundation**      | 1.1, 1.2, 1.3         | 4-6 hours | None               |
| **P1: Session & Audit** | 2.1, 3.1              | 3-4 hours | P0 complete        |
| **P2: Security**        | Extend thegent-crypto | 2-3 hours | P0, P1 complete    |
| **P3: Metrics**         | 4.1                   | 1-2 hours | P0, P1 complete    |
| **Verification**        | 5.1, 5.2, 5.3         | 2-3 hours | All P0-P3 complete |
| **Cleanup & Removal**   | Remove Python modules | 1 hour    | Verification pass  |

**Wall-clock estimate:** 13-19 hours (with agent parallelization, 3-5 hours).

---

## Success Criteria

All tasks complete when:

1. **100% test coverage** (Unit + Integration + E2E)
2. **Parity verified** (test_python_rust_parity.py passes)
3. **Performance ≥2x** (Benchmarks show speedup)
4. **Zero warnings** (`cargo clippy -D warnings`)
5. **PyO3 bindings work** (All Python tests pass)
6. **Python modules removed** (Backup only, fully replaced)
7. **Documentation updated** (CHANGELOG, README, API docs)

---
