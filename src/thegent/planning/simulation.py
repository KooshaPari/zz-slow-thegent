"""Planning simulation module for PERT analysis, resource contention, and continuity risk."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class ContentionResult:
    """Result of contention detection."""

    resource_id: str
    time_window: tuple[float, float]
    peak_demand: float
    available_capacity: float
    contention_ratio: float
    affected_tasks: list[str] = field(default_factory=list)


@dataclass
class ContinuityRiskInput:
    """Input for continuity risk analysis."""

    open_tasks: list[dict[str, Any]] = field(default_factory=list)
    handoff_windows: list[dict[str, Any]] = field(default_factory=list)
    snapshot_freshness: dict[str, datetime] = field(default_factory=dict)
    owner_coverage: dict[str, str] = field(default_factory=dict)


@dataclass
class ContinuityRiskResult:
    """Result of continuity risk analysis."""

    risk_score: float
    factors: list[str]
    high_risk_tasks: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


@dataclass
class PERTNode:
    """Node for PERT (Program Evaluation and Review Technique) analysis."""

    task_id: str
    optimistic_days: float
    most_likely_days: float
    pessimistic_days: float
    predecessors: list[str] = field(default_factory=list)

    @property
    def expected(self) -> float:
        """Calculate expected duration."""
        return (self.optimistic_days + 4 * self.most_likely_days + self.pessimistic_days) / 6


@dataclass
class PERTResult:
    """Result of PERT analysis."""

    task_id: str
    expected_duration: float
    variance: float
    critical_path: bool
    total_float: float = 0.0
    confidence_p50: float = 0.5
    confidence_p90: float = 0.9


@dataclass
class SimulationResult:
    """Result of a simulation run."""

    risk_score: float = 0.0
    warnings: list[str] | None = None
    recommendations: list[str] | None = None


@dataclass
class ResourceProfile:
    """Profile for resource estimation."""

    resource_id: str
    capacity: float
    unit: str = "concurrent"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "resource_id": self.resource_id,
            "capacity": self.capacity,
            "unit": self.unit,
        }


@dataclass
class TaskResourceDemand:
    """Demand for a resource by a task."""

    task_id: str
    resource_id: str
    demand: float
    start_float: float = 0.0
    duration_float: float = 0.0


def pert_forward_pass(nodes: list[PERTNode]) -> dict[str, PERTResult]:
    """Perform PERT forward pass calculation.

    Args:
        nodes: List of PERT nodes.

    Returns:
        Dictionary mapping task_id to PERTResult.
    """
    results: dict[str, PERTResult] = {}

    for node in nodes:
        # Calculate expected duration
        expected = (node.optimistic_days + 4 * node.most_likely_days + node.pessimistic_days) / 6
        variance = ((node.pessimistic_days - node.optimistic_days) / 6) ** 2

        results[node.task_id] = PERTResult(
            task_id=node.task_id,
            expected_duration=expected,
            variance=variance,
            critical_path=False,
            total_float=0.0,
            confidence_p50=0.5,
            confidence_p90=0.9,
        )

    return results


def simulate_resource_contention(
    tasks: list[dict[str, Any]],
    resources: list[ResourceProfile],
    schedule: dict[str, dict[str, float]],
) -> list[ContentionResult]:
    """Simulate resource contention.

    Args:
        tasks: List of task dictionaries.
        resources: List of resource profiles.
        schedule: Dictionary mapping task_id to schedule info.

    Returns:
        List of contention results (stub returns empty list).
    """
    return []


def score_continuity_risk(input_data: ContinuityRiskInput) -> ContinuityRiskResult:
    """Score continuity risk based on task state and handoff readiness.

    Args:
        input_data: Input data for continuity risk analysis.

    Returns:
        ContinuityRiskResult with risk score and recommendations.
    """
    risk_score = 0.0
    factors: list[str] = []
    high_risk_tasks: list[str] = []
    recommendations: list[str] = []

    now = datetime.now(UTC)

    for task in input_data.open_tasks:
        task_id = task.get("id") or task.get("task_id")
        if not task_id:
            continue

        snapshot_time = input_data.snapshot_freshness.get(task_id)
        if snapshot_time is None:
            # No snapshot = no risk
            continue

        # Handle naive datetimes
        if snapshot_time.tzinfo is None:
            snapshot_time = snapshot_time.replace(tzinfo=UTC)

        age = now - snapshot_time
        age_hours = age.total_seconds() / 3600

        if age_hours > 24:
            # Add 0.2 risk for stale snapshot (older than 24h)
            risk_score += 0.2
            factors.append(f"Stale snapshot for {task_id}: {age_hours:.1f}h old")
            high_risk_tasks.append(task_id)

    # Cap at 1.0
    risk_score = min(1.0, risk_score)

    # Add recommendations if risk is high
    if risk_score > 0.5:
        recommendations.append("Refresh snapshots before handoff")

    return ContinuityRiskResult(
        risk_score=risk_score,
        factors=factors,
        high_risk_tasks=high_risk_tasks,
        recommendations=recommendations,
    )


def simulate_continuity_risk(input_data: ContinuityRiskInput) -> SimulationResult:
    """Simulate continuity risk based on input parameters."""
    risk_score = 0.0
    warnings = []

    if input_data.open_tasks and len(input_data.open_tasks) > 5:
        risk_score += 0.2
        warnings.append("High task count may cause coordination issues")

    return SimulationResult(risk_score=risk_score, warnings=warnings, recommendations=[])


__all__ = [
    "ContentionResult",
    "ContinuityRiskInput",
    "ContinuityRiskResult",
    "PERTNode",
    "PERTResult",
    "ResourceProfile",
    "SimulationResult",
    "TaskResourceDemand",
    "pert_forward_pass",
    "score_continuity_risk",
    "simulate_resource_contention",
    "simulate_continuity_risk",
]
