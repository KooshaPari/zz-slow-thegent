"""Orchestration playbooks module."""

from __future__ import annotations

from typing import Any

__all__ = ["Playbook", "PlaybookExecutor", "get_playbook_for_failure"]


class Playbook:
    """Base playbook for orchestration."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.steps: list[dict] = []

    def add_step(self, step: dict) -> None:
        """Add a step to the playbook."""
        self.steps.append(step)

    def execute(self) -> dict:
        """Execute the playbook."""
        return {"status": "executed", "steps": len(self.steps)}


class PlaybookExecutor:
    """Executor for playbooks."""

    def __init__(self) -> None:
        self.playbooks: dict[str, Playbook] = {}

    def register(self, playbook: Playbook) -> None:
        """Register a playbook."""
        self.playbooks[playbook.name] = playbook

    def execute(self, name: str) -> dict:
        """Execute a playbook by name."""
        if name not in self.playbooks:
            return {"error": f"Playbook not found: {name}"}
        return self.playbooks[name].execute()


def get_playbook_for_failure(failure_type: str) -> list[str]:
    """Get the appropriate playbook steps for a failure type.

    Args:
        failure_type: The type of failure that occurred

    Returns:
        List of playbook step names to handle the failure
    """
    failure_lower = failure_type.lower()
    if "timeout" in failure_lower or "timed out" in failure_lower:
        return ["retry_with_backoff", "escalate"]
    if "rate limit" in failure_lower or "429" in failure_lower:
        return ["backoff", "retry"]
    if "auth" in failure_lower or "401" in failure_lower:
        return ["reauthenticate", "retry"]
    return ["log", "escalate"]
