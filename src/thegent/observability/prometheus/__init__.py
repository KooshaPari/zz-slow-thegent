"""Prometheus metrics integration."""

from __future__ import annotations

from typing import Any


def get_prometheus_metrics() -> dict[str, Any]:
    """Get Prometheus metrics."""
    return {}


class MetricsCollector:
    """Collector for Prometheus metrics."""

    def __init__(self) -> None:
        self.metrics: dict[str, Any] = {}

    def collect(self) -> dict[str, Any]:
        """Collect metrics."""
        return self.metrics


__all__ = [
    "get_prometheus_metrics",
    "MetricsCollector",
    "get_metrics_collector",
    "reset_metrics_collector",
]


def reset_metrics_collector() -> None:
    """Reset the global metrics collector."""


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    return MetricsCollector()
