"""Request routing and dispatch with dependency injection.

Pure routing logic with no CLI imports.
Routes requests to appropriate agents/models based on rules.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any, Optional


class Router:
    """Request router with injected agent/model factories.

    Routes tasks to agents and models based on routing rules.
    No direct imports from agents/models or CLI.
    """

    def __init__(
        self,
        agent_factory: Callable | None = None,
        model_factory: Callable | None = None,
    ):
        """Initialize router with injected factories.

        Args:
            agent_factory: Factory for creating agents
            model_factory: Factory for creating models
        """
        self.agent_factory = agent_factory
        self.model_factory = model_factory

    def select_agent(self, task_spec: dict[str, Any]) -> str | None:
        """Select an agent for a task.

        Args:
            task_spec: Task specification

        Returns:
            Selected agent name or None
        """
        # Simple selection logic
        agent = task_spec.get("agent")
        if agent:
            return agent

        # Default fallback
        return "default_agent"

    def select_model(self, task_spec: dict[str, Any]) -> str | None:
        """Select a model for a task.

        Args:
            task_spec: Task specification

        Returns:
            Selected model name or None
        """
        # Simple selection logic
        model = task_spec.get("model")
        if model:
            return model

        # Default fallback
        return "default_model"

    def route(self, task_spec: dict[str, Any]) -> dict[str, Any]:
        """Route a task to agent and model.

        Args:
            task_spec: Task specification

        Returns:
            Routing decision with agent and model selections
        """
        return {
            "agent": self.select_agent(task_spec),
            "model": self.select_model(task_spec),
            "task_id": task_spec.get("task_id"),
        }


__all__ = [
    "Router",
]
