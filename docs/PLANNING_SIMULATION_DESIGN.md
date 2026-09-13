# Planning Simulation Design (G-CA-04)

**Status:** Design
**Date:** 2026-02-14
**Scope:** PERT overlays, resource contention simulation, continuity risk scoring

---

## 1. Purpose

This document defines the design for planning simulation overlays that augment WBS/DAG governance with probabilistic confidence, resource contention analysis, and continuity risk scoring. Per cross-analysis matrix Delta D: D1 (PERT), D2 (resource contention), D3 (continuity risk).

---

## 2. D1: PERT Uncertainty Overlays

### 2.1 Goal

Overlay probabilistic confidence on WBS milestones instead of binary done/not-done. Transfer pattern from Crun: Monte Carlo schedule risk quantification with percentile confidence bands.

### 2.2 Data Model

```python
@dataclass
class PERTNode:
    task_id: str
    optimistic_days: float  # best-case duration
    most_likely_days: float  # expected duration
    pessimistic_days: float  # worst-case duration
    predecessors: list[str]


@dataclass
class PERTResult:
    task_id: str
    expected_duration: float
    variance: float
    critical_path: bool
    total_float: float
    confidence_p50: float
    confidence_p90: float
```

### 2.3 API

- `pert_forward_pass(nodes: list[PERTNode]) -> dict[str, PERTResult]` — compute expected duration, variance, critical path
- `pert_monte_carlo(nodes: list[PERTNode], iterations: int = 1000) -> dict[str, dict]` — percentile confidence bands per milestone
- `pert_overlay_to_wbs(wbs: dict, pert_results: dict) -> dict` — attach confidence to WBS milestones

### 2.4 Integration

- `thegent plan analyze --pert` — run PERT overlay and output milestone confidence report
- WBS governance gate: block promotion if critical-path confidence < threshold (e.g. P90 < 0.7)

---

## 3. D2: Resource Contention Simulation

### 3.1 Goal

Simulate resource contention for heavy parallel DAG waves. Detect when multiple tasks compete for the same resource (e.g. agent capacity, model quota) in the same time window.

### 3.2 Data Model

```python
@dataclass
class ResourceProfile:
    resource_id: str
    capacity: int | float  # e.g. concurrent runs, API quota
    unit: str  # "concurrent" | "quota_per_hour"


@dataclass
class TaskResourceDemand:
    task_id: str
    resource_id: str
    demand: float
    start_float: float
    duration_float: float


@dataclass
class ContentionResult:
    resource_id: str
    time_window: tuple[float, float]
    peak_demand: float
    capacity: float
    contention_ratio: float
    affected_tasks: list[str]
```

### 3.3 API

- `simulate_resource_contention(tasks: list, resources: list[ResourceProfile], schedule: dict) -> list[ContentionResult]` — identify contention windows
- `level_resources(tasks: list, resources: list, strategy: str) -> dict` — apply leveling (e.g. delay non-critical tasks)
- `get_parallel_wave_contention(dag: dict, wave_size: int) -> list[ContentionResult]` — analyze N-way parallel wave

### 3.4 Integration

- `thegent plan analyze --resources` — report contention hotspots
- DAG governance: warn when wave N exceeds resource capacity

---

## 4. D3: Continuity Risk Scoring

### 4.1 Goal

Score shift handoff reliability: risk that open work loses context or stalls when ownership changes (e.g. shift change, handoff to different operator).

### 4.2 Data Model

```python
@dataclass
class ContinuityRiskInput:
    open_tasks: list[dict]
    handoff_windows: list[tuple[datetime, datetime]]
    snapshot_freshness: dict[str, datetime]
    owner_coverage: dict[str, list[str]]


@dataclass
class ContinuityRiskResult:
    risk_score: float  # 0.0-1.0
    factors: list[str]
    high_risk_tasks: list[str]
    recommendations: list[str]
```

### 4.3 API

- `score_continuity_risk(input: ContinuityRiskInput) -> ContinuityRiskResult` — compute risk from open tasks, handoff windows, snapshot age
- `continuity_heatmap(runs: list, time_buckets: int) -> dict` — near-real-time risk heatmap per time bucket

### 4.4 Integration

- `thegent plan analyze --continuity` — report continuity risk before handoff
- Governance: block handoff if continuity risk > threshold; require snapshot refresh

---

## 5. Implementation Location

- **Design:** `docs/PLANNING_SIMULATION_DESIGN.md` (this document)
- **Scaffold:** `src/thegent/planning/simulation.py` — placeholder APIs
- **CLI:** `thegent plan analyze` — wire PERT, resources, continuity flags

---

## 6. Priority

| Component              | Priority | Effort        |
| ---------------------- | -------- | ------------- |
| D1 PERT overlays       | P2       | M (1–2 weeks) |
| D2 Resource contention | P2       | M (1 week)    |
| D3 Continuity risk     | P2       | S (3–5 days)  |

---

## 7. References

- Cross-analysis: `docs/docset/thegent-cross-analysis-matrix-2026-02-14.md` §6.4
- Mega research: Crun PERT/CPM, Monte Carlo (agent ab39cc7)
- PRD: `docs/docset/thegent-orchestration-optimization-prd.md` — continuity risk heatmap (WBS 169.16)
