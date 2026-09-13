"""Stub module."""

from dataclasses import dataclass
from typing import Any


@dataclass
class AgentRunResult:
    """Result of running an agent."""

    success: bool
    output: str = ""
    errors: list[str] | None = None


def run_agent(task: dict[str, Any]) -> AgentRunResult:
    """Run an agent with the given task."""
    return AgentRunResult(success=True, output="Agent completed")


try:
    from typer import Typer

    app = Typer()
except ImportError:
    app = None


__all__ = ["AgentRunResult", "run_agent", "app"]
