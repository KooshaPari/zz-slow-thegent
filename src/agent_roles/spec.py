"""Agent roles spec module."""

from __future__ import annotations


class AgentRoleSpec:
    """Specification for an agent role."""

    def __init__(self, role: str) -> None:
        self.role = role
        self.capabilities: list[str] = []

    def to_dict(self) -> dict[str, Any]:
        return {"role": self.role, "capabilities": self.capabilities}


__all__ = ["AgentRoleSpec"]
