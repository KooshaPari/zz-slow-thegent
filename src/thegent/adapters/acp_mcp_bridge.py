"""MCP <-> ACP Bridge adapter.

Bridges MCP (Model Context Protocol) tools to ACP agent calls and vice versa.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from thegent.adapters.acp_client import (
    ACPClient,
    ACPClientError,
    ACPResult,
    ACPServerUnreachableError,
)

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class BridgeError(Exception):
    """Base exception for bridge errors."""


class MCPToolNotFoundError(BridgeError):
    """Raised when an MCP tool is not found."""

    def __init__(self, tool_name: str) -> None:
        self.tool_name = tool_name
        super().__init__(f"MCP tool not found: {tool_name}")


class ACPAgentCallError(BridgeError):
    """Raised when an ACP agent call fails."""

    def __init__(self, agent_url: str, detail: str) -> None:
        self.agent_url = agent_url
        self.detail = detail
        super().__init__(f"ACP agent call failed ({agent_url}): {detail}")


# ---------------------------------------------------------------------------
# ACPToolDescriptor
# ---------------------------------------------------------------------------


@dataclass
class ACPToolDescriptor:
    """Descriptor for an MCP tool exposed to ACP."""

    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)
    version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "version": self.version,
        }


# ---------------------------------------------------------------------------
# AcpMcpBridge
# ---------------------------------------------------------------------------


class AcpMcpBridge:
    """Bridge between MCP tools and ACP agent calls."""

    def __init__(
        self,
        acp_client: ACPClient,
        mcp_app: Any = None,
        mcp_server_url: str | None = None,
    ) -> None:
        """Initialize the bridge.

        Args:
            acp_client: ACP client for agent communication.
            mcp_app: Optional MCP app for tool discovery.
            mcp_server_url: Optional MCP server URL.
        """
        self._acp_client = acp_client
        self._mcp_app = mcp_app
        self._mcp_server_url = mcp_server_url

    async def mcp_tool_to_acp_task(
        self,
        tool_name: str,
        args: dict[str, Any],
        timeout: float | None = None,
    ) -> ACPResult:
        """Call an MCP tool via ACP agent.

        Args:
            tool_name: Name of the MCP tool to call.
            args: Tool arguments.
            timeout: Optional timeout in seconds.

        Returns:
            ACPResult from the agent.

        Raises:
            MCPToolNotFoundError: If the tool is not found.
            ACPServerUnreachableError: If the ACP server is unreachable.
            ACPClientError: On ACP client errors.
        """
        if not tool_name:
            raise ValueError("tool_name cannot be empty")

        context = {
            "tool_name": tool_name,
            "args": args,
        }

        task = f"Execute MCP tool: {tool_name}"

        return await self._acp_client.send_task(task, context=context, timeout=timeout)

    async def acp_agent_to_mcp_tool(
        self,
        agent_url: str,
        task: str,
        payload: dict[str, Any],
    ) -> str:
        """Execute an MCP tool via a one-shot ACP agent call.

        Args:
            agent_url: URL of the ACP agent.
            task: Task description.
            payload: Tool payload/context.

        Returns:
            Result text from the agent.

        Raises:
            ValueError: If agent_url or task is empty.
            ACPServerUnreachableError: If the agent is unreachable.
            ACPAgentCallError: On agent call failures.
        """
        if not agent_url:
            raise ValueError("agent_url cannot be empty")
        if not task:
            raise ValueError("task cannot be empty")

        # Create a one-shot client for this agent
        client = ACPClient(base_url=agent_url)

        try:
            result = await client.send_task(task, context=payload)
            return result.result
        except ACPServerUnreachableError:
            raise
        except ACPClientError as e:
            raise ACPAgentCallError(agent_url, str(e)) from e
        finally:
            await client.close()

    def get_mcp_tool_manifest(self) -> list[dict[str, Any]]:
        """Get the manifest of available MCP tools.

        Returns:
            List of tool descriptors as dictionaries.
        """
        if self._mcp_app is None:
            return []

        try:
            tools = self._mcp_app.get_tools()
        except Exception:
            return []

        manifest = []
        for name, tool in tools.items():
            # Get description
            description = getattr(tool, "description", None)
            if not description:
                description = getattr(tool, "__doc__", "") or ""

            # Get parameters
            parameters = getattr(tool, "parameters", {})

            descriptor = ACPToolDescriptor(
                name=name,
                description=description,
                parameters=parameters,
            )
            manifest.append(descriptor.to_dict())

        return manifest
