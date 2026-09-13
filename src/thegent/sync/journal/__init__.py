"""Stub module."""

from dataclasses import dataclass
from typing import Any


class LocalDecisionJournal:
    """Local journal for sync decisions."""

    def __init__(self) -> None:
        self.decisions: list[dict[str, Any]] = []

    def record(self, decision: dict[str, Any]) -> None:
        """Record a decision."""
        self.decisions.append(decision)

    def get_all(self) -> list[dict[str, Any]]:
        """Get all recorded decisions."""
        return self.decisions


__all__ = ["LocalDecisionJournal", "SyncDecisionEntry"]


@dataclass
class SyncDecisionEntry:
    """Entry for a sync decision."""

    decision_id: str
    action: str
    timestamp: float = 0.0
