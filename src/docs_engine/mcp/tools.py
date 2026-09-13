"""MCP tools - STUB."""

from __future__ import annotations

from typing import Any


class MCPTools:
    def __init__(self, *args, **kwargs):
        pass

    def register(self, tool, *args, **kwargs):
        pass

    def list_tools(self, *args, **kwargs) -> list[dict[str, Any]]:
        return []


def register_tools(registry: Any) -> None:
    """Register tools with the given registry."""


__all__ = ["MCPTools", "register_tools"]
