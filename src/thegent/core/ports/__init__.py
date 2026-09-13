"""Port/adapter interfaces for thegent (hexagonal architecture).

Defines abstract base classes and protocols that other layers depend on.
No implementation; used for dependency injection.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, Generic, Protocol, TypeVar, runtime_checkable

T = TypeVar("T")


@runtime_checkable
class AgentInterface(Protocol):
    """Protocol for agent implementations."""

    @property
    def name(self) -> str:
        """Agent identifier."""
        ...

    @property
    def description(self) -> str:
        """Human-readable description."""
        ...

    async def invoke(self, input_data: Any) -> Any:
        """Invoke the agent with input, return output."""
        ...


@runtime_checkable
class ModelInterface(Protocol):
    """Protocol for LLM model implementations."""

    @property
    def model_id(self) -> str:
        """Model identifier (e.g., 'gpt-4', 'claude-opus')."""
        ...

    @property
    def provider(self) -> str:
        """Model provider (e.g., 'openai', 'anthropic')."""
        ...

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text from prompt."""
        ...


@runtime_checkable
class RouterInterface(Protocol):
    """Protocol for routing/dispatch logic."""

    async def route(
        self, request: Any, agents: list[AgentInterface], models: list[ModelInterface]
    ) -> tuple[AgentInterface | None, ModelInterface | None]:
        """Route request to appropriate agent and model."""
        ...


@runtime_checkable
class LoggerInterface(Protocol):
    """Protocol for logging."""

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        ...

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        ...

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        ...

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        ...


EventHandler = Callable[[Any], None]
Unsubscribe = Callable[[], None]


@runtime_checkable
class EventBusInterface(Protocol):
    """Canonical protocol for event publishing and subscription (WL150).

    Unified surface used across ``thegent.execution.executor``,
    ``thegent.ux.cockpit_bridge``, and the Phase 3/4 hardening lanes.

    Notes:
        * ``subscribe`` returns an idempotent *unsubscriber* callable.
        * ``publish`` is the canonical name; ``emit`` is a deprecated alias
          retained for back-compat with call sites that have already
          adopted the legacy shape.
        * ``publish`` MUST NOT raise on handler errors; implementations
          should isolate handler exceptions so a single bad subscriber
          cannot bring down the bus.  Strict variants may opt-in to
          re-raising via a subclass/flag.
    """

    def subscribe(self, event_type: str, handler: EventHandler) -> Unsubscribe:
        """Subscribe ``handler`` to ``event_type``.

        Returns:
            Idempotent callable that, when invoked, removes the subscription.
        """
        ...

    def publish(self, event_type: str, data: Any) -> None:
        """Publish ``event_type`` with ``data`` payload to all subscribers."""
        ...

    def emit(self, event_type: str, data: Any) -> None:
        """Deprecated alias for :meth:`publish`.

        Retained so that code which adopted the older ``emit`` naming
        keeps working under the canonical protocol.
        """
        ...


class ExecutorInterface(ABC):
    """Abstract interface for task execution."""

    @abstractmethod
    async def execute(self, task: Any) -> Any:
        """Execute a task and return result."""
        ...


class PlannerInterface(ABC):
    """Abstract interface for task planning/decomposition."""

    @abstractmethod
    async def plan(self, objective: str) -> list[Any]:
        """Decompose objective into tasks."""
        ...


class ExecutionPort(Protocol):
    """Port for agents to invoke execution logic without importing CLI.

    This breaks the circular dependency: agents can call execution through
    this abstract interface, which is provided by the CLI adapter at runtime.
    """

    def run_task(
        self,
        agent: str | None = None,
        prompt: str = "",
        cd: str = "",
        mode: str = "write",
        timeout: int = 300,
        model: str | None = None,
        provider: str | None = None,
    ) -> dict[str, Any]:
        """Execute a task via the execution engine.

        Args:
            agent: Agent name to use (None for default)
            prompt: Task prompt
            cd: Working directory
            mode: Execution mode ('write', 'read', etc.)
            timeout: Timeout in seconds
            model: Model override
            provider: Provider override

        Returns:
            Result dict with execution output
        """
        ...

    def get_dag_status(self, cd: str = "") -> dict[str, Any]:
        """Get current DAG/WBS status.

        Args:
            cd: Working directory

        Returns:
            Status dict
        """
        ...


__all__ = [
    "AgentInterface",
    "ModelInterface",
    "RouterInterface",
    "LoggerInterface",
    "EventBusInterface",
    "EventHandler",
    "Unsubscribe",
    "ExecutorInterface",
    "PlannerInterface",
    "ExecutionPort",
]
