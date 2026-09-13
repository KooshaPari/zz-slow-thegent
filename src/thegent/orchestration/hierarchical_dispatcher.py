"""Hierarchical dispatcher for L^N agent dispatch.

@trace WL-138
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# Constants
MAX_HIERARCHY_DEPTH = 5
SESSION_AGENT_CAP = 50
SYSTEM_AGENT_CAP = 200


class AgentLifecycleState(Enum):
    """Lifecycle states for hierarchical agents."""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    PRUNED = "pruned"


@dataclass
class HierarchicalAgent:
    """Represents an agent in the hierarchical dispatch system."""

    agent_id: str
    session_id: str
    parent_id: str | None = None
    depth: int = 0
    state: AgentLifecycleState = AgentLifecycleState.PENDING
    task_prompt: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    last_heartbeat: float = field(default_factory=time.time)
    children: set[str] = field(default_factory=set)

    def update_heartbeat(self) -> None:
        """Update the last heartbeat timestamp."""
        self.last_heartbeat = time.time()

    def is_stale(self, threshold: float = 60.0) -> bool:
        """Check if agent is stale based on heartbeat threshold."""
        # Only RUNNING agents can be stale
        if self.state == AgentLifecycleState.RUNNING:
            return (time.time() - self.last_heartbeat) > threshold
        return False


@dataclass
class HierarchicalDispatchRequest:
    """Request to dispatch a hierarchical agent."""

    prompt: str = ""  # Alias for task_prompt for backward compatibility
    task_prompt: str = ""
    session_id: str = ""
    parent_id: str | None = None
    depth: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Ensure task_prompt is set from prompt if needed."""
        if self.task_prompt == "" and self.prompt != "":
            self.task_prompt = self.prompt
        elif self.task_prompt == "":
            self.task_prompt = ""


class AgentCapExceededError(Exception):
    """Raised when agent cap (per-session or system-wide) is exceeded."""


class MaxDepthExceededError(Exception):
    """Raised when maximum hierarchy depth is exceeded."""


class SessionAgentRegistry:
    """Registry for agents within a session."""

    def __init__(self, session_cap: int = 10) -> None:
        self.session_cap = session_cap
        self._agents: dict[str, HierarchicalAgent] = {}

    def register(self, agent: HierarchicalAgent) -> None:
        """Register an agent in this session."""
        if len(self._agents) >= self.session_cap:
            raise AgentCapExceededError(
                f"Session agent cap ({self.session_cap}) exceeded"
            )
        self._agents[agent.agent_id] = agent

    def get(self, agent_id: str) -> HierarchicalAgent | None:
        """Get an agent by ID."""
        return self._agents.get(agent_id)

    def list_agents(self) -> list[HierarchicalAgent]:
        """List all agents in this session."""
        return list(self._agents.values())

    def active_count(self) -> int:
        """Count active agents (RUNNING or FINISHED)."""
        return sum(
            1
            for a in self._agents.values()
            if a.state in (AgentLifecycleState.RUNNING, AgentLifecycleState.FINISHED)
        )

    def running_count(self) -> int:
        """Count running agents."""
        return sum(
            1 for a in self._agents.values() if a.state == AgentLifecycleState.RUNNING
        )

    def count(self) -> int:
        """Count all agents in this session."""
        return len(self._agents)

    def can_spawn(self) -> bool:
        """Check if a new agent can be spawned in this session."""
        return len(self._agents) < self.session_cap

    @property
    def agents(self) -> dict[str, HierarchicalAgent]:
        """Access agents dict for test compatibility."""
        return self._agents

    def clear(self) -> None:
        """Clear all agents from this session."""
        self._agents.clear()


class HierarchicalAgentRegistry:
    """Global registry for all hierarchical agents."""

    def __init__(self, system_cap: int = 100, session_cap: int = 10) -> None:
        self.system_cap = system_cap
        self.session_cap = session_cap
        self._sessions: dict[str, SessionAgentRegistry] = {}
        self._total_agents: int = 0

    def _get_session_registry(self, session_id: str) -> SessionAgentRegistry:
        """Get or create a session registry."""
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionAgentRegistry(self.session_cap)
        return self._sessions[session_id]

    def register(self, agent: HierarchicalAgent) -> None:
        """Register an agent globally and in its session."""
        if self._total_agents >= self.system_cap:
            raise AgentCapExceededError(
                f"System agent cap ({self.system_cap}) exceeded"
            )

        # Track parent-child relationship
        if agent.parent_id:
            parent = self.get_agent(agent.parent_id)
            if parent:
                parent.children.add(agent.agent_id)

        session_registry = self._get_session_registry(agent.session_id)
        session_registry.register(agent)
        self._total_agents += 1

    # Alias for test compatibility
    def register_agent(self, agent: HierarchicalAgent) -> None:
        """Register an agent (alias for register)."""
        self.register(agent)

    def get_agent(self, agent_id: str) -> HierarchicalAgent | None:
        """Get an agent by ID from any session."""
        for session in self._sessions.values():
            agent = session.get(agent_id)
            if agent:
                return agent
        return None

    def get_children(self, parent_id: str) -> list[HierarchicalAgent]:
        """Get all children of an agent."""
        children = []
        for session in self._sessions.values():
            for agent in session.list_agents():
                if agent.parent_id == parent_id:
                    children.append(agent)
        return children

    def get_descendants(self, agent_id: str) -> list[HierarchicalAgent]:
        """Get all descendants of an agent recursively."""
        descendants = []
        to_process = [agent_id]
        while to_process:
            current = to_process.pop()
            children = self.get_children(current)
            for child in children:
                descendants.append(child)
                to_process.append(child.agent_id)
        return descendants

    def total_active_count(self) -> int:
        """Get total active agents count."""
        return self._total_agents

    def prune_finished_stale(self, stale_threshold: float = 60.0) -> int:
        """Prune finished and stale agents, return count of pruned."""
        pruned = 0
        current_time = time.time()
        for session_registry in self._sessions.values():
            to_remove = []
            for agent_id, agent in session_registry.agents.items():
                # Check staleness based on heartbeat
                heartbeat_stale = (
                    current_time - agent.last_heartbeat
                ) > stale_threshold

                # FINISHED/COMPLETED agents that are stale should be pruned
                is_terminal = agent.state in (
                    AgentLifecycleState.COMPLETED,
                    AgentLifecycleState.FINISHED,
                )
                if is_terminal and heartbeat_stale:
                    to_remove.append(agent_id)
                    pruned += 1
                # RUNNING agents that are stale should be marked PRUNED
                elif agent.state == AgentLifecycleState.RUNNING and heartbeat_stale:
                    agent.state = AgentLifecycleState.PRUNED
                    pruned += 1
            for agent_id in to_remove:
                del session_registry.agents[agent_id]
                self._total_agents -= 1
        return pruned

    def get_system_stats(self) -> dict[str, Any]:
        """Get system-wide statistics."""
        return {
            "total_active": self._total_agents,
            "system_cap": self.system_cap,
            "session_cap": self.session_cap,
            "session_count": len(self._sessions),
        }

    def get(self, agent_id: str, session_id: str) -> HierarchicalAgent | None:
        """Get an agent by ID."""
        session_registry = self._sessions.get(session_id)
        if session_registry:
            return session_registry.get(agent_id)
        return None

    def list_session_agents(self, session_id: str) -> list[HierarchicalAgent]:
        """List all agents in a session."""
        session_registry = self._sessions.get(session_id)
        if session_registry:
            return session_registry.list_agents()
        return []

    def count(self) -> int:
        """Count total agents."""
        return self._total_agents

    def count_session(self, session_id: str) -> int:
        """Count agents in a session."""
        session_registry = self._sessions.get(session_id)
        if session_registry:
            return session_registry.count()
        return 0

    def clear_session(self, session_id: str) -> None:
        """Clear all agents from a session."""
        session_registry = self._sessions.get(session_id)
        if session_registry:
            self._total_agents -= session_registry.count()
            session_registry.clear()
            del self._sessions[session_id]

    def reset(self) -> None:
        """Reset the entire registry."""
        self._sessions.clear()
        self._total_agents = 0


class HierarchicalDispatcher:
    """Dispatches agents hierarchically with L^N constraints."""

    def __init__(
        self,
        registry: HierarchicalAgentRegistry | None = None,
        capability_index: Any | None = None,
        base_dispatcher: Any | None = None,
    ) -> None:
        self.registry = registry or _global_registry
        self.capability_index = capability_index
        self.base_dispatcher = base_dispatcher

    async def dispatch(self, request: HierarchicalDispatchRequest) -> HierarchicalAgent:
        """Dispatch a new hierarchical agent."""
        if request.depth >= MAX_HIERARCHY_DEPTH:
            raise MaxDepthExceededError(
                f"Max hierarchy depth ({MAX_HIERARCHY_DEPTH}) exceeded"
            )

        agent_id = f"agent-{request.session_id}-{self.registry.count_session(request.session_id)}"
        agent = HierarchicalAgent(
            agent_id=agent_id,
            session_id=request.session_id,
            parent_id=request.parent_id,
            depth=request.depth,
            state=AgentLifecycleState.PENDING,
            task_prompt=request.task_prompt,
            metadata=request.metadata,
        )

        self.registry.register(agent)
        return agent

    # Alias for test compatibility
    async def dispatch_hierarchical(
        self, request: HierarchicalDispatchRequest
    ) -> HierarchicalAgent:
        """Dispatch a new hierarchical agent (alias for dispatch)."""
        return await self.dispatch(request)

    def can_spawn_child(self, parent_agent_id: str) -> bool:
        """Check if a child agent can be spawned under the parent."""
        parent = self.registry.get_agent(parent_agent_id)
        if not parent:
            return False
        return not parent.depth >= MAX_HIERARCHY_DEPTH

    def get_agent_tree(self, root_agent_id: str) -> dict[str, Any]:
        """Get the agent tree starting from a root agent."""
        root = self.registry.get_agent(root_agent_id)
        if not root:
            return {}

        children = self.registry.get_children(root_agent_id)
        return {
            "agent_id": root.agent_id,
            "session_id": root.session_id,
            "depth": root.depth,
            "state": root.state.value,
            "children": [self.get_agent_tree(child.agent_id) for child in children],
        }


# Global registry instance
_global_registry: HierarchicalAgentRegistry = HierarchicalAgentRegistry()


def get_global_registry() -> HierarchicalAgentRegistry:
    """Get the global agent registry."""
    return _global_registry


def reset_global_registry() -> None:
    """Reset the global agent registry."""
    global _global_registry
    _global_registry.reset()


__all__ = [
    "MAX_HIERARCHY_DEPTH",
    "AgentCapExceededError",
    "AgentLifecycleState",
    "HierarchicalAgent",
    "HierarchicalAgentRegistry",
    "HierarchicalDispatcher",
    "HierarchicalDispatchRequest",
    "MaxDepthExceededError",
    "SessionAgentRegistry",
    "get_global_registry",
    "reset_global_registry",
]
