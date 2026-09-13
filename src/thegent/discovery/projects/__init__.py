"""Stub module."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProjectInfo:
    """Information about a discovered project."""

    name: str
    path: str
    metadata: dict[str, Any] = field(default_factory=dict)


class ProjectRegistry:
    """Registry for discovered projects."""

    def __init__(self) -> None:
        self._projects: dict[str, ProjectInfo] = {}

    def register(self, project: ProjectInfo) -> None:
        """Register a project."""
        self._projects[project.name] = project

    def get(self, name: str) -> ProjectInfo | None:
        """Get a project by name."""
        return self._projects.get(name)

    def list_all(self) -> list[ProjectInfo]:
        """List all registered projects."""
        return list(self._projects.values())


__all__ = ["ProjectInfo", "ProjectRegistry"]
