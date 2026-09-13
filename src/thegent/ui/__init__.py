"""STUB MODULE - thegent.ui

WARNING: This is an auto-generated stub module.
The actual implementation was moved/deleted during repository restructuring.
This stub exists for backwards compatibility with existing tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class CompositorProfiler:
    """Profiler for compositor performance."""

    def __init__(self) -> None:
        self._stats: dict[str, Any] = {}

    def start(self) -> None:
        """Start profiling."""

    def stop(self) -> dict[str, Any]:
        """Stop profiling and return results."""
        return self._stats.copy()


@dataclass
class RenderProfile:
    """Profile data for a render operation."""
    duration_ms: float = 0.0
    components_rendered: int = 0
    cache_hits: int = 0


__all__ = ["CompositorProfiler", "RenderProfile"]
