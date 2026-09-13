"""MCP Server tools and skills."""

from __future__ import annotations

import json as _json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


class _ToolResult:
    """A simple ToolResult-like class for compatibility."""

    def __init__(
        self,
        content: str = "",
        structured_content: dict[str, Any] | None = None,
        meta: dict[str, Any] | None = None,
    ) -> None:
        self.content = content
        self.structured_content = structured_content or {}
        self.meta = meta or {}


class DiscoverySkillBackend:
    """Backend for skill discovery."""

    def __init__(self) -> None:
        self._skills: dict[str, Any] = {}

    def list_skills(self) -> list[dict[str, Any]]:
        """List all available skills."""
        return list(self._skills.values())

    def activate_skill(self, skill_name: str) -> dict[str, Any] | None:
        """Activate a skill by name."""
        return self._skills.get(skill_name)

    def discover(self) -> list[Any]:
        """Discover available skills."""
        return list(self._skills.values())

    def get(self, name: str) -> Any | None:
        """Get a skill by name."""
        return self._skills.get(name)


def thegent_activate_skill_impl(
    skill_name: str,
    backend: Any | None = None,
    error_result_impl: Any | None = None,
) -> Any:
    """Implementation for thegent_activate_skill tool."""
    if error_result_impl is not None and (not skill_name or not skill_name.strip()):
        return error_result_impl("skill_name must be non-empty", "Provide a valid skill name")

    if backend is not None and hasattr(backend, "activate_skill"):
        result = backend.activate_skill(skill_name)
        if result is None:
            if error_result_impl:
                return error_result_impl(
                    f"Skill '{skill_name}' not found",
                    "Activate an existing skill",
                    extra={"skill_name": skill_name},
                )
            return _ToolResult(
                content=_json.dumps({"error": f"Skill '{skill_name}' not found", "skill_name": skill_name}),
                structured_content={"error": f"Skill '{skill_name}' not found", "skill_name": skill_name},
            )
        return _ToolResult(
            content=_json.dumps({"skill": result}),
            structured_content={"skill": result},
        )

    return _ToolResult(
        content=_json.dumps({"skill": {"name": skill_name, "content": f"# {skill_name}\nInstructions for {skill_name}"}}),
        structured_content={"skill": {"name": skill_name, "content": f"# {skill_name}\nInstructions for {skill_name}"}},
    )


def thegent_list_skills_impl(backend: Any | None = None) -> Any:
    """Implementation for thegent_list_skills tool."""
    if backend is not None and hasattr(backend, "list_skills"):
        skills = backend.list_skills()
        return _ToolResult(
            content=_json.dumps({"skills": sorted(skills, key=lambda s: s.get("name", ""))}),
            structured_content={"skills": sorted(skills, key=lambda s: s.get("name", ""))},
        )
    return _ToolResult(
        content=_json.dumps({"skills": []}),
        structured_content={"skills": []},
    )

class MCPSkillRegistry:
    """Registry for MCP server skills."""

    def __init__(self) -> None:
        self._skills: dict[str, Any] = {}

    def register(self, name: str, skill: Any) -> None:
        """Register a skill."""
        self._skills[name] = skill

    def get(self, name: str) -> Any | None:
        """Get a skill by name."""
        return self._skills.get(name)

    def list_skills(self) -> list[str]:
        """List all registered skill names."""
        return list(self._skills.keys())


# Global registry instance
registry = MCPSkillRegistry()


def register_skill(name: str, skill: Any) -> None:
    """Register a skill with the global registry."""
    registry.register(name, skill)


def get_skill(name: str) -> Any | None:
    """Get a skill by name from the global registry."""
    return registry.get(name)


__all__ = [
    "MCPSkillRegistry",
    "register_skill",
    "get_skill",
    "registry",
    "DiscoverySkillBackend",
    "thegent_activate_skill_impl",
    "thegent_list_skills_impl",
]
