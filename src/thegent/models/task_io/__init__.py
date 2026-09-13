"""Task I/O module."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any


class TaskError(Exception):
    """Task error exception."""

    def __init__(self, message: str, task_id: str | None = None) -> None:
        super().__init__(message)
        self.task_id = task_id


@dataclass
class TaskInput:
    """Task input data."""

    task_id: str
    prompt: str
    context: dict[str, Any] | None = None
    options: dict[str, Any] | None = None


@dataclass
class TaskOutput:
    """Task output data."""

    task_id: str
    result: str
    success: bool = True
    error: str | None = None


@dataclass
class TaskSpec:
    """Task specification."""
    name: str
    description: str = ""


__all__ = ["TaskError", "TaskInput", "TaskOutput", "TaskSpec", "get_task_io"]


class TaskIO:
    """Task I/O handler."""

    def __init__(self) -> None:
        self.inputs: list[TaskInput] = []
        self.outputs: list[TaskOutput] = []

    def submit(self, task_id: str, prompt: str) -> None:
        """Submit a task."""
        self.inputs.append(TaskInput(task_id=task_id, prompt=prompt))

    def complete(self, task_id: str, result: str) -> None:
        """Complete a task."""
        self.outputs.append(TaskOutput(task_id=task_id, result=result))


def get_task_io() -> TaskIO:
    """Get the global task I/O instance."""
    return TaskIO()
