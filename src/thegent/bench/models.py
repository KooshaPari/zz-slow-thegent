"""Bench models module."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BenchRecord:
    """Record for benchmark data."""

    benchmark: str
    score: float
    unit: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "benchmark": self.benchmark,
            "score": self.score,
            "unit": self.unit,
            "metadata": self.metadata,
        }


__all__ = ["BenchRecord"]
