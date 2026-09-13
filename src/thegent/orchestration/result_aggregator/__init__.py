"""Stub module."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AggregatedResult:
    """Aggregated result from multiple execution runs."""

    id: str = ""
    run_ids: list[str] = field(default_factory=list)
    status: str = "pending"
    summary: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_run(self, run_id: str) -> None:
        """Add a run ID to the aggregation."""
        self.run_ids.append(run_id)

    def is_complete(self) -> bool:
        """Check if all runs are complete."""
        return all(r.get("status") in ("completed", "failed", "cancelled") for r in self.summary.get("runs", []))

    def get_error_count(self) -> int:
        """Get the count of errors."""
        return len(self.errors)


class ResultAggregator:
    """Aggregates results from multiple execution runs."""

    def __init__(self) -> None:
        self._results: dict[str, AggregatedResult] = {}

    def aggregate(self, run_id: str) -> AggregatedResult:
        """Aggregate results for a run."""
        if run_id not in self._results:
            self._results[run_id] = AggregatedResult(id=run_id)
        return self._results[run_id]

    def add_result(self, run_id: str, result: dict) -> None:
        """Add a result to the aggregation."""
        agg = self.aggregate(run_id)
        agg.summary[run_id] = result

    def get_aggregated(self, run_id: str) -> AggregatedResult | None:
        """Get the aggregated result for a run."""
        return self._results.get(run_id)


__all__ = ["AggregatedResult", "ResultAggregator"]
