# Pareto Routing with Hysteresis — Technical Design

## Architecture Overview

### System Diagram

```
┌─────────────────────────────────────────────────────┐
│           Task Dispatcher                           │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │   ParetoRouter        │
         │  (Decision Logic)     │
         └───────────┬───────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
  ┌──────────┐ ┌──────────┐ ┌──────────┐
  │ Risk     │ │Hysteresis│ │Route     │
  │Calculator│ │Manager   │ │Executor  │
  └──────────┘ └──────────┘ └──────────┘
        │            │            │
        └────────────┼────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌──────────────────┐     ┌──────────────────┐
│ Lifecycle Loop   │     │ The Gent Loop    │
│ (Fast/Cheap)     │     │ (Plan/Review)    │
└──────────────────┘     └──────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Language | File |
|-----------|-----------------|----------|------|
| **ParetoRouter** | Route selection, hysteresis orchestration | Rust | `crates/thegent-router/src/router.rs` |
| **RiskCalculator** | Risk scoring (complexity, cost, dependencies) | Rust | `crates/thegent-router/src/risk.rs` |
| **HysteresisManager** | Dwell time tracking, band checks | Rust | `crates/thegent-router/src/hysteresis.rs` |
| **RouteExecutor** | Route-specific task execution | Python | `src/thegent/routing/executor.py` |
| **AuditLogger** | Routing decisions, metrics | Python | `src/thegent/routing/audit.py` |

---

## Rust Implementation

### Core Data Structures

```rust
// crates/thegent-router/src/lib.rs

use std::time::{Duration, Instant};
use serde::{Deserialize, Serialize};

/// Task risk assessment
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RiskAssessment {
    pub score: f64,          // 0.0 (low) to 1.0 (high)
    pub complexity: f64,     // 0.0 to 1.0
    pub cost_factor: f64,    // 0.0 to 1.0
    pub dependencies: f64,   // 0.0 to 1.0
    pub breakdown: RiskBreakdown,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RiskBreakdown {
    pub complexity_score: f64,
    pub cost_impact: f64,
    pub external_deps: usize,
    pub security_risk: bool,
}

/// Routing mode enum
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum RoutingMode {
    Lifecycle,  // 80%, fast/cheap
    TheGent,    // 20%, plan-heavy/review-heavy
}

/// Routing decision
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RoutingDecision {
    pub task_id: String,
    pub mode: RoutingMode,
    pub risk_score: f64,
    pub hysteresis_applied: bool,
    pub dwell_remaining: Option<Duration>,
    pub timestamp: u64,
}

/// Main router state
pub struct ParetoRouter {
    low_risk_threshold: f64,      // Typically 0.3
    high_risk_threshold: f64,     // Typically 0.7
    hysteresis_band: (f64, f64),  // (low, high)
    dwell_time: Duration,         // Typically 5 minutes
    max_dwell: Duration,          // Typically 30 minutes

    // Tracking state
    current_modes: std::collections::HashMap<String, SessionState>,
    metrics: RouterMetrics,
}

struct SessionState {
    mode: RoutingMode,
    switched_at: Option<Instant>,
}

#[derive(Debug, Clone, Default)]
pub struct RouterMetrics {
    pub total_decisions: u64,
    pub lifecycle_count: u64,
    pub thegent_count: u64,
    pub hysteresis_activations: u64,
    pub route_changes: u64,
}
```

### Risk Calculation

```rust
// crates/thegent-router/src/risk.rs

pub struct RiskCalculator {
    complexity_weight: f64,    // 0.40
    cost_weight: f64,          // 0.35
    dependency_weight: f64,    // 0.25
}

pub struct Task {
    pub id: String,
    pub title: String,
    pub description: String,
    pub estimated_cost_cents: u32,
    pub complexity: Complexity,
    pub external_dependencies: Vec<String>,
    pub security_sensitive: bool,
    pub tags: Vec<String>,
}

#[derive(Debug, Clone, Copy)]
pub enum Complexity {
    Simple,      // 0.1
    Moderate,    // 0.4
    Complex,     // 0.7
    VeryComplex, // 0.95
}

impl RiskCalculator {
    pub fn assess_risk(&self, task: &Task) -> RiskAssessment {
        let complexity_score = self.assess_complexity(task);
        let cost_factor = self.assess_cost(task);
        let dependency_factor = self.assess_dependencies(task);
        let security_factor = if task.security_sensitive { 0.3 } else { 0.0 };

        // Composite score
        let score = (
            complexity_score * self.complexity_weight +
            cost_factor * self.cost_weight +
            dependency_factor * self.dependency_weight +
            security_factor  // Non-negotiable security addition
        ).min(1.0).max(0.0);

        RiskAssessment {
            score,
            complexity: complexity_score,
            cost_factor,
            dependencies: dependency_factor,
            breakdown: RiskBreakdown {
                complexity_score,
                cost_impact: cost_factor,
                external_deps: task.external_dependencies.len(),
                security_risk: task.security_sensitive,
            },
        }
    }

    fn assess_complexity(&self, task: &Task) -> f64 {
        match task.complexity {
            Complexity::Simple => 0.1,
            Complexity::Moderate => 0.4,
            Complexity::Complex => 0.7,
            Complexity::VeryComplex => 0.95,
        }
    }

    fn assess_cost(&self, task: &Task) -> f64 {
        // Map cost in cents to 0.0-1.0 scale
        // 0-10 cents → 0.0, 100+ cents → 1.0
        let cost = task.estimated_cost_cents as f64;
        (cost / 100.0).min(1.0)
    }

    fn assess_dependencies(&self, task: &Task) -> f64 {
        // 0 deps → 0.0, 5+ deps → 1.0
        (task.external_dependencies.len() as f64 / 5.0).min(1.0)
    }
}
```

### Hysteresis Manager

```rust
// crates/thegent-router/src/hysteresis.rs

pub struct HysteresisManager {
    band_low: f64,      // 0.3
    band_high: f64,     // 0.7
    dwell_time: Duration,
    max_dwell: Duration,
}

pub struct HysteresisState {
    session_id: String,
    current_mode: RoutingMode,
    switched_at: Option<Instant>,
    entered_band_at: Option<Instant>,
}

impl HysteresisManager {
    pub fn should_switch(
        &self,
        state: &HysteresisState,
        new_risk_score: f64,
        old_risk_score: f64,
    ) -> (bool, HysteresisReason) {
        // Case 1: Risk clearly outside band → always switch
        if !self.in_hysteresis_band(new_risk_score) {
            return (true, HysteresisReason::OutsideBand);
        }

        // Case 2: In band, check dwell time
        if let Some(switched_at) = state.switched_at {
            if switched_at.elapsed() < self.dwell_time {
                return (false, HysteresisReason::DwellTimeActive);
            }
        }

        // Case 3: Exceeded max dwell → force re-evaluation
        if let Some(entered_at) = state.entered_band_at {
            if entered_at.elapsed() > self.max_dwell {
                return (true, HysteresisReason::MaxDwellExceeded);
            }
        }

        // Case 4: Large risk change (>0.2) → override dwell
        if (new_risk_score - old_risk_score).abs() > 0.2 {
            return (true, HysteresisReason::LargeRiskChange);
        }

        (false, HysteresisReason::DwellActive)
    }

    fn in_hysteresis_band(&self, score: f64) -> bool {
        score >= self.band_low && score <= self.band_high
    }
}

pub enum HysteresisReason {
    OutsideBand,
    DwellTimeActive,
    MaxDwellExceeded,
    LargeRiskChange,
    DwellActive,
}
```

### Router Main Logic

```rust
// crates/thegent-router/src/router.rs

impl ParetoRouter {
    pub fn new(
        low_threshold: f64,
        high_threshold: f64,
        dwell_time: Duration,
        max_dwell: Duration,
    ) -> Self {
        let hysteresis_band = (low_threshold, high_threshold);

        Self {
            low_risk_threshold: low_threshold,
            high_risk_threshold: high_threshold,
            hysteresis_band,
            dwell_time,
            max_dwell,
            current_modes: std::collections::HashMap::new(),
            metrics: RouterMetrics::default(),
        }
    }

    pub fn route(
        &mut self,
        session_id: &str,
        task: &Task,
        risk: &RiskAssessment,
    ) -> RoutingDecision {
        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_secs();

        // Get or create session state
        let old_state = self.current_modes.get(session_id).cloned();
        let old_risk = risk.score; // Simplified; real impl tracks previous

        // Hysteresis check
        let hysteresis_mgr = HysteresisManager {
            band_low: self.hysteresis_band.0,
            band_high: self.hysteresis_band.1,
            dwell_time: self.dwell_time,
            max_dwell: self.max_dwell,
        };

        let (should_switch, reason) = if let Some(state) = &old_state {
            hysteresis_mgr.should_switch(
                &HysteresisState {
                    session_id: session_id.to_string(),
                    current_mode: state.mode,
                    switched_at: state.switched_at,
                    entered_band_at: None, // Simplified
                },
                risk.score,
                old_risk,
            )
        } else {
            (true, HysteresisReason::OutsideBand)
        };

        // Determine mode
        let new_mode = if should_switch {
            if risk.score < self.low_risk_threshold {
                RoutingMode::Lifecycle
            } else {
                RoutingMode::TheGent
            }
        } else if let Some(state) = &old_state {
            state.mode
        } else {
            // Default: risk > 0.5 → TheGent, else Lifecycle
            if risk.score > 0.5 {
                RoutingMode::TheGent
            } else {
                RoutingMode::Lifecycle
            }
        };

        // Update state
        let switched = old_state.as_ref().map(|s| s.mode) != Some(new_mode);
        if switched {
            self.current_modes.insert(
                session_id.to_string(),
                SessionState {
                    mode: new_mode,
                    switched_at: Some(Instant::now()),
                },
            );
            self.metrics.route_changes += 1;
        }

        // Update metrics
        match new_mode {
            RoutingMode::Lifecycle => self.metrics.lifecycle_count += 1,
            RoutingMode::TheGent => self.metrics.thegent_count += 1,
        }
        self.metrics.total_decisions += 1;
        if reason != HysteresisReason::DwellActive {
            self.metrics.hysteresis_activations += 1;
        }

        RoutingDecision {
            task_id: task.id.clone(),
            mode: new_mode,
            risk_score: risk.score,
            hysteresis_applied: !should_switch,
            dwell_remaining: old_state.and_then(|s| {
                s.switched_at.map(|t| {
                    let elapsed = t.elapsed();
                    if elapsed < self.dwell_time {
                        self.dwell_time - elapsed
                    } else {
                        Duration::ZERO
                    }
                })
            }),
            timestamp: now,
        }
    }

    pub fn get_metrics(&self) -> RouterMetrics {
        self.metrics.clone()
    }
}
```

---

## Python Integration

### Route Executor

```python
# src/thegent/routing/executor.py

from enum import Enum
from typing import Protocol
import asyncio


class Route(Enum):
    LIFECYCLE = "lifecycle"
    THE_GENT = "the_gent"


class RouteExecutor(Protocol):
    """Protocol for route-specific executors"""

    async def execute(self, task: Task) -> TaskResult: ...


class LifecycleExecutor:
    """Fast, automated execution for low-risk tasks"""

    def __init__(self, model="gpt-5-mini", timeout_sec=60):
        self.model = model
        self.timeout_sec = timeout_sec

    async def execute(self, task: Task) -> TaskResult:
        """Execute task with minimal planning/review"""
        # Direct execution via MCP or local agent
        try:
            result = await asyncio.wait_for(
                self._run_task(task),
                timeout=self.timeout_sec,
            )
            return result
        except asyncio.TimeoutError:
            return TaskResult(
                status="timeout",
                task_id=task.id,
                error="Execution exceeded time limit",
            )

    async def _run_task(self, task: Task) -> TaskResult:
        # Dispatch to fast agent
        pass


class TheGentExecutor:
    """Plan-heavy, review-heavy execution for high-risk tasks"""

    def __init__(self, planner_model="claude-opus", timeout_sec=300):
        self.planner_model = planner_model
        self.timeout_sec = timeout_sec

    async def execute(self, task: Task) -> TaskResult:
        """Execute task with planning, implementation, review"""
        try:
            # Phase 1: Plan
            plan = await self._plan(task)

            # Phase 2: Implement
            result = await self._implement(task, plan)

            # Phase 3: Review
            review = await self._review(task, plan, result)

            return TaskResult(
                status="success",
                task_id=task.id,
                plan=plan,
                implementation=result,
                review=review,
            )
        except Exception as e:
            return TaskResult(
                status="error",
                task_id=task.id,
                error=str(e),
            )

    async def _plan(self, task: Task) -> Plan:
        # Invoke planner
        pass

    async def _implement(self, task: Task, plan: Plan) -> Implementation:
        # Execute plan
        pass

    async def _review(self, task: Task, plan: Plan, impl: Implementation) -> Review:
        # Operator review
        pass
```

### Routing Orchestrator

```python
# src/thegent/routing/orchestrator.py


class RoutingOrchestrator:
    """Main orchestrator for Pareto routing"""

    def __init__(self):
        self.router = thegent_router.ParetoRouter(
            low_threshold=0.3,
            high_threshold=0.7,
            dwell_time_secs=300,  # 5 minutes
            max_dwell_secs=1800,  # 30 minutes
        )

        self.lifecycle_executor = LifecycleExecutor()
        self.thegent_executor = TheGentExecutor()

        self.audit_logger = AuditLogger()

    async def route_and_execute(self, task: Task, session_id: str) -> TaskResult:
        """Main entry point: route task and execute"""

        # Step 1: Assess risk
        risk = self._assess_risk(task)

        # Step 2: Route
        decision = self.router.route(session_id, task, risk)

        # Step 3: Log decision
        await self.audit_logger.log_routing_decision(decision, risk)

        # Step 4: Execute via appropriate route
        if decision.mode == thegent_router.RoutingMode.Lifecycle:
            result = await self.lifecycle_executor.execute(task)
        else:  # TheGent
            result = await self.thegent_executor.execute(task)

        # Step 5: Log result
        await self.audit_logger.log_task_result(task.id, decision, result)

        return result

    def _assess_risk(self, task: Task) -> thegent_router.RiskAssessment:
        """Convert Python task to Rust risk assessment"""
        risk_calc = thegent_router.RiskCalculator(
            complexity_weight=0.40,
            cost_weight=0.35,
            dependency_weight=0.25,
        )

        rust_task = thegent_router.Task(
            id=task.id,
            title=task.title,
            description=task.description,
            estimated_cost_cents=task.cost_cents,
            complexity=self._map_complexity(task),
            external_dependencies=task.dependencies,
            security_sensitive=task.is_security_sensitive(),
            tags=task.tags,
        )

        return risk_calc.assess_risk(rust_task)

    def _map_complexity(self, task: Task) -> thegent_router.Complexity:
        if "simple" in task.tags.lower():
            return thegent_router.Complexity.Simple
        elif "moderate" in task.tags.lower():
            return thegent_router.Complexity.Moderate
        elif "complex" in task.tags.lower():
            return thegent_router.Complexity.Complex
        else:
            return thegent_router.Complexity.VeryComplex

    def get_routing_stats(self) -> dict:
        """Get routing metrics for monitoring"""
        metrics = self.router.get_metrics()
        return {
            "total_decisions": metrics.total_decisions,
            "lifecycle_count": metrics.lifecycle_count,
            "thegent_count": metrics.thegent_count,
            "lifecycle_percentage": (
                metrics.lifecycle_count / metrics.total_decisions * 100 if metrics.total_decisions > 0 else 0
            ),
            "hysteresis_activations": metrics.hysteresis_activations,
            "route_changes": metrics.route_changes,
        }
```

### Audit Logging

```python
# src/thegent/routing/audit.py


class AuditLogger:
    """Log routing decisions for compliance and debugging"""

    def __init__(self, log_path="logs/routing.jsonl"):
        self.log_path = log_path

    async def log_routing_decision(
        self,
        decision: thegent_router.RoutingDecision,
        risk: thegent_router.RiskAssessment,
    ):
        """Log routing decision with full context"""
        entry = {
            "event": "routing_decision",
            "timestamp": decision.timestamp,
            "task_id": decision.task_id,
            "mode": decision.mode.name,
            "risk_score": decision.risk_score,
            "risk_breakdown": {
                "complexity": risk.breakdown.complexity_score,
                "cost_impact": risk.breakdown.cost_impact,
                "external_deps": risk.breakdown.external_deps,
                "security_risk": risk.breakdown.security_risk,
            },
            "hysteresis_applied": decision.hysteresis_applied,
            "dwell_remaining_ms": (
                decision.dwell_remaining.total_seconds() * 1000 if decision.dwell_remaining else None
            ),
        }

        # Write to log file
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    async def log_task_result(
        self,
        task_id: str,
        decision: thegent_router.RoutingDecision,
        result: TaskResult,
    ):
        """Log task execution result"""
        entry = {
            "event": "task_result",
            "timestamp": time.time(),
            "task_id": task_id,
            "route": decision.mode.name,
            "status": result.status,
            "error": result.error or None,
        }

        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
```

---

## Data Structures

### Task

```python
@dataclass
class Task:
    id: str
    title: str
    description: str
    cost_cents: int
    complexity_tag: str  # "simple", "moderate", "complex", "very_complex"
    dependencies: List[str]  # External service/API names
    tags: List[str]

    def is_security_sensitive(self) -> bool:
        return any(tag in ("security", "auth", "crypto") for tag in self.tags)
```

### TaskResult

```python
@dataclass
class TaskResult:
    task_id: str
    status: str  # "success", "error", "timeout"
    error: Optional[str] = None
    plan: Optional[Plan] = None
    implementation: Optional[Implementation] = None
    review: Optional[Review] = None
```

---

## Configuration

### Config File: `thegent.routing.toml`

```toml
[routing.pareto]
low_risk_threshold = 0.3
high_risk_threshold = 0.7

[routing.hysteresis]
dwell_time_secs = 300      # 5 minutes
max_dwell_secs = 1800      # 30 minutes
band_margin = 0.2

[routing.risk_calculation]
complexity_weight = 0.40
cost_weight = 0.35
dependency_weight = 0.25

[routing.lifecycle]
model = "gpt-5-mini"
timeout_secs = 60

[routing.the_gent]
planner_model = "claude-opus"
timeout_secs = 300

[routing.audit]
log_path = "logs/routing.jsonl"
log_level = "info"
```

---

## Testing Strategy

### Unit Tests

- Risk calculator: test all complexity levels, cost ranges, dependency counts
- Hysteresis: test dwell time enforcement, max dwell override, large changes
- Router: test mode selection, metrics tracking

### Integration Tests

- End-to-end routing: task → risk → decision → execution
- Fallback handling: missing dependencies, timeout scenarios
- Cost tracking: verify cost attribution to routes

### Load Tests

- 1M tasks with varying risk scores
- Verify 80/20 split achieved
- Verify hysteresis prevents oscillation

---

## Monitoring & Observability

### Metrics to Track

| Metric | Type | Alerting |
|--------|------|----------|
| Lifecycle % | Gauge | Alert if <75% or >85% |
| Avg risk (Lifecycle) | Gauge | Alert if >0.3 |
| Avg risk (TheGent) | Gauge | Alert if <0.6 |
| Route changes/min | Counter | Alert if >10/min |
| Hysteresis activations | Counter | Informational |
| Routing latency p99 | Histogram | Alert if >5ms |

### Dashboards

1. **Routing Overview**: Split, metrics, trends
2. **Risk Distribution**: Histogram of risk scores
3. **Hysteresis Health**: Dwell time enforcement, max dwell hits
4. **Cost Attribution**: Cost by route

---

## Error Handling

| Scenario | Handling | Recovery |
|----------|----------|----------|
| Risk calc fails | Log error, default to TheGent | Retry with fresh assessment |
| Executor timeout | Escalate to The Gent (from Lifecycle) | Manual review |
| Audit log full | Rotate log file | No impact on routing |
| Invalid task | Reject with validation error | User must fix task |

---

## Deployment

### Rollout Strategy

1. **Shadow Mode** (Week 1): Run routing in parallel, don't use decisions
2. **Canary** (Week 2): Route 1% of traffic, monitor metrics
3. **Gradual** (Week 3): Increase to 25%, 50%, 75%
4. **Full** (Week 4): 100% traffic

### Rollback Procedure

- Metrics alert: automatic fallback to single-route mode
- Manual: `thegent routing disable-pareto`

---

**Document Version**: 1.0
**Last Updated**: 2026-02-18
**Status**: Ready for implementation
