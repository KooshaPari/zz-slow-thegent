"""Stub module."""

from dataclasses import dataclass
from typing import Any


@dataclass
class RestToolDef:
    """REST tool definition."""

    name: str
    method: str = "GET"
    path: str = "/"
    description: str = ""


@dataclass
class RestToolResult:
    """Result of a REST tool call."""

    success: bool
    data: Any = None
    error: str = ""


class RestToMcpAdapter:
    """Adapter for REST to MCP conversion."""

    def __init__(self) -> None:
        self.routes: dict[str, Any] = {}

    def adapt(self, request: dict[str, Any]) -> dict[str, Any]:
        """Adapt a REST request to MCP format."""
        return {"result": "adapted"}


def build_openai_tool_def(tool: RestToolDef) -> dict[str, Any]:
    """Build an OpenAI tool definition from a REST tool definition."""
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": {"type": "object", "properties": {}},
        },
    }


__all__ = ["RestToMcpAdapter", "RestToolDef", "RestToolResult", "build_openai_tool_def"]
