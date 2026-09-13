"""Metrics utilities for thegent.

Common metrics collection and reporting.
"""

from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock
from typing import Any


class MetricsCollector:
    """Thread-safe metrics collector."""

    def __init__(self) -> None:
        self._counters: dict[str, int] = defaultdict(int)
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def increment(self, name: str, value: int = 1) -> None:
        """Increment a counter."""
        with self._lock:
            self._counters[name] += value

    def decrement(self, name: str, value: int = 1) -> None:
        """Decrement a counter."""
        with self._lock:
            self._counters[name] -= value

    def gauge(self, name: str, value: float) -> None:
        """Set a gauge value."""
        with self._lock:
            self._gauges[name] = value

    def histogram(self, name: str, value: float) -> None:
        """Record a histogram value."""
        with self._lock:
            self._histograms[name].append(value)

    def get_counter(self, name: str) -> int:
        """Get counter value."""
        with self._lock:
            return self._counters.get(name, 0)

    def get_gauge(self, name: str) -> float | None:
        """Get gauge value."""
        with self._lock:
            return self._gauges.get(name)

    def get_histogram_stats(self, name: str) -> dict[str, float]:
        """Get histogram statistics."""
        with self._lock:
            values = self._histograms.get(name, [])
            if not values:
                return {"count": 0, "sum": 0, "min": 0, "max": 0, "avg": 0}
            return {
                "count": len(values),
                "sum": sum(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
            }

    def get_all(self) -> dict[str, Any]:
        """Get all metrics."""
        with self._lock:
            result = {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {
                    name: self.get_histogram_stats(name) for name in self._histograms
                },
            }
        return result

    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()


class Timer:
    """Context manager for timing operations."""

    def __init__(self, collector: MetricsCollector, name: str):
        self.collector = collector
        self.name = name
        self.start_time = 0.0

    def __enter__(self) -> Timer:
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args: Any) -> None:
        elapsed = time.perf_counter() - self.start_time
        self.collector.histogram(self.name, elapsed)


# Global collector instance
_global_collector: MetricsCollector | None = None


def get_collector() -> MetricsCollector:
    """Get global metrics collector."""
    global _global_collector
    if _global_collector is None:
        _global_collector = MetricsCollector()
    return _global_collector


def increment(name: str, value: int = 1) -> None:
    """Increment a global counter."""
    get_collector().increment(name, value)


def gauge(name: str, value: float) -> None:
    """Set a global gauge."""
    get_collector().gauge(name, value)


def histogram(name: str, value: float) -> None:
    """Record a global histogram value."""
    get_collector().histogram(name, value)


def timer(name: str) -> Timer:
    """Create a timer context manager."""
    return Timer(get_collector(), name)
