"""Stub module."""

from typing import Any


class MetricsCollector:
    """Collects metrics."""

    def __init__(self) -> None:
        self.metrics: dict[str, Any] = {}

    def record(self, metric: str, value: Any) -> None:
        """Record a metric."""
        self.metrics[metric] = value

    def get(self, metric: str) -> Any | None:
        """Get a metric."""
        return self.metrics.get(metric)


__all__ = ["MetricsCollector"]
