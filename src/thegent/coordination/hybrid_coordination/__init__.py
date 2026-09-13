"""Stub module."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, StrEnum
from typing import Any


class CoordinationMode(StrEnum):
    """Coordination modes."""

    SYNC = "sync"
    ASYNC = "async"


@dataclass
class CoordinationMetrics:
    """Metrics for coordination."""

    total_operations: int = 0
    successful_operations: int = 0


@dataclass
class HybridCoordinationStrategy:
    """Strategy for hybrid coordination."""

    mode: CoordinationMode = CoordinationMode.SYNC
    timeout: int = 30
    metrics: CoordinationMetrics | None = None

    def coordinate(self, task: Any) -> Any:
        """Coordinate a task using the hybrid strategy."""
        return {}


__all__ = ["CoordinationMetrics", "CoordinationMode", "HybridCoordinationStrategy"]
