"""Task decomposition and planning engine.

Pure planning logic with no CLI imports.
Decomposes high-level tasks into executable subtasks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class TaskSpec:
    """Specification for a decomposed task."""

    task_id: str
    description: str
    agent_name: str | None = None
    model_name: str | None = None
    dependencies: list[str] = None
    parameters: dict[str, Any] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.parameters is None:
            self.parameters = {}


class Planner:
    """Task decomposer with no CLI dependencies.

    Decomposes high-level task contracts into concrete,
    executable task specifications.
    """

    def decompose(self, task_spec: dict[str, Any]) -> list[TaskSpec]:
        """Decompose a task into subtasks.

        Args:
            task_spec: High-level task specification

        Returns:
            List of executable TaskSpec objects
        """
        # Placeholder decomposition logic
        # Will be enhanced in Phase 3-4
        task_id = task_spec.get("task_id", "unknown")
        description = task_spec.get("description", "")

        return [
            TaskSpec(
                task_id=task_id,
                description=description,
                agent_name=task_spec.get("agent"),
                model_name=task_spec.get("model"),
            )
        ]

    def plan_execution_sequence(
        self,
        tasks: list[TaskSpec],
    ) -> list[list[TaskSpec]]:
        """Create execution schedule (phases) from tasks.

        Args:
            tasks: List of task specifications

        Returns:
            List of execution phases (each phase is parallelizable)
        """
        # Simple sequential scheduling for now
        return [[task] for task in tasks]


__all__ = [
    "Planner",
    "TaskSpec",
]
