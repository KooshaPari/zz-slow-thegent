"""Stub module."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SyncEngineConfig:
    """Sync engine configuration."""

    enabled: bool = True
    interval: int = 60


__all__ = ["SyncEngineConfig", "enforce_max_changes_per_cycle"]


def enforce_max_changes_per_cycle(changes: list[Any], max_changes: int) -> list[Any]:
    """Enforce maximum changes per sync cycle."""
    return changes[:max_changes]
