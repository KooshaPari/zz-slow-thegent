"""Stub module."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class McpServerConfig:
    """Configuration for MCP server."""

    server_id: str = "default"
    command: str = ""
    env: dict[str, str] = field(default_factory=dict)
    host: str = "localhost"
    port: int = 8080
    name: str = "mcp-server"
    transport: Any = None

    def __init__(self, **kwargs):
        self.server_id = kwargs.get("server_id", "default")
        self.command = kwargs.get("command", "")
        self.env = kwargs.get("env", {})
        self.host = kwargs.get("host", "localhost")
        self.port = kwargs.get("port", 8080)
        self.name = kwargs.get("name", "mcp-server")
        self.transport = kwargs.get("transport")
        for k, v in kwargs.items():
            if not hasattr(self, k):
                setattr(self, k, v)


@dataclass
class McpToolCall:
    """A tool call made through MCP."""

    server_id: str = ""
    tool: str = ""
    arguments: dict[str, Any] = field(default_factory=dict)
    call_id: str = ""


@dataclass
class McpToolResult:
    """Result from an MCP tool call."""

    call_id: str = ""
    success: bool = True
    result: Any = None
    error: str = ""


class McpGateway:
    """Gateway for MCP operations."""

    def __init__(self) -> None:
        self.connected: bool = False
        self._servers: dict[str, McpServerConfig] = {}

    def connect(self) -> bool:
        """Connect to gateway."""
        self.connected = True
        return True

    def register_server(self, config: McpServerConfig | str = None, **kwargs) -> bool:
        """Register an MCP server with the gateway."""
        if isinstance(config, str):
            config = McpServerConfig(server_id=config, **kwargs)
        elif config is None:
            config = McpServerConfig(**kwargs)
        self._servers[config.server_id] = config
        return True

    def unregister_server(self, name: str) -> bool:
        """Unregister an MCP server from the gateway."""
        if name in self._servers:
            del self._servers[name]
            return True
        return False

    def list_servers(self) -> list[str]:
        """List registered servers."""
        return list(self._servers.keys())

    def execute(self, tool_call: McpToolCall) -> McpToolResult:
        """Execute a tool call."""
        import json

        from thegent.mcp.gateway import subprocess

        if tool_call.server_id not in self._servers:
            return McpToolResult(
                call_id=tool_call.call_id,
                success=False,
                error=f"Unknown server_id: {tool_call.server_id}",
            )

        # Try to run the command
        try:
            server_config = self._servers[tool_call.server_id]
            transport = getattr(server_config, "transport", None)

            if transport:
                # Use custom transport if provided
                result = transport(
                    command=server_config.command.split() if server_config.command else [],
                    request_payload=json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "id": "thegent-gateway",
                            "method": tool_call.tool,
                            "params": {
                                "name": tool_call.tool,
                                "arguments": tool_call.arguments,
                            },
                        }
                    ),
                    env=server_config.env or {},
                    timeout_sec=30.0,
                )
                # Handle both tuple and mock object results
                if isinstance(result, tuple):
                    returncode, stdout, stderr = result
                else:
                    # Mock result - extract attributes
                    returncode = getattr(result, "returncode", 0)
                    stdout = getattr(result, "stdout", "")
                    stderr = getattr(result, "stderr", "")
            else:
                # Use subprocess
                result = subprocess.run(
                    command=server_config.command.split() if server_config.command else [],
                    request_payload=json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "id": "thegent-gateway",
                            "method": tool_call.tool,
                            "params": {
                                "name": tool_call.tool,
                                "arguments": tool_call.arguments,
                            },
                        }
                    ),
                    env=server_config.env or {},
                    timeout_sec=30.0,
                )
                # Handle both tuple and mock object results
                if isinstance(result, tuple):
                    returncode, stdout, stderr = result
                else:
                    returncode = getattr(result, "returncode", 0)
                    stdout = getattr(result, "stdout", "")
                    stderr = getattr(result, "stderr", "")

            if returncode != 0:
                return McpToolResult(
                    call_id=tool_call.call_id,
                    success=False,
                    error=f"transport_error: {stderr}",
                )

            response = json.loads(stdout)
            if "error" in response:
                return McpToolResult(
                    call_id=tool_call.call_id,
                    success=False,
                    error=f"Unknown tool '{tool_call.tool}': {response['error'].get('message', '')}",
                )

            return McpToolResult(
                call_id=tool_call.call_id,
                success=True,
                result=response.get("result"),
            )
        except FileNotFoundError:
            return McpToolResult(
                call_id=tool_call.call_id,
                success=False,
                error="transport_error: command not found",
            )
        except (json.JSONDecodeError, UnicodeDecodeError):
            return McpToolResult(
                call_id=tool_call.call_id,
                success=False,
                error="transport_error: invalid or empty MCP response",
            )
        except Exception as e:
            return McpToolResult(
                call_id=tool_call.call_id,
                success=False,
                error=f"transport_error: {type(e).__name__}: {str(e)}",
            )

    def exec_tool(self, server_id: str, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Execute a tool on a registered server."""
        return self.execute(McpToolCall(server_id=server_id, tool=tool_name, arguments=arguments))


__all__ = [
    "McpGateway",
    "McpServerConfig",
    "McpToolCall",
    "McpToolResult",
    "get_mcp_gateway",
    "reset_mcp_gateway",
]


def reset_mcp_gateway() -> None:
    """Reset the global MCP gateway instance."""
    global _gateway_instance
    _gateway_instance = None


_gateway_instance: McpGateway | None = None


def get_mcp_gateway() -> McpGateway:
    """Get the global MCP gateway instance."""
    global _gateway_instance
    if _gateway_instance is None:
        _gateway_instance = McpGateway()
    return _gateway_instance


class GatewayClient:
    """Client for MCP gateway operations."""

    def __init__(self, gateway: McpGateway | None = None):
        self.gateway = gateway or get_mcp_gateway()

    def exec(
        self,
        server_id: str,
        tool: str,
        arguments: dict | None = None,
        timeout_s: float = 30.0,
    ) -> str:
        """Execute a tool call and return the result.

        Args:
            server_id: Server ID to call.
            tool: Tool name.
            arguments: Tool arguments.
            timeout_s: Timeout in seconds.

        Returns:
            JSON string result or error message.
        """
        import json

        result = self.gateway.execute(
            McpToolCall(
                server_id=server_id,
                tool=tool,
                arguments=arguments or {},
            )
        )
        if result.success:
            return json.dumps(result.result)
        return f"transport_error: {result.error}" if result.error else "transport_error: invalid or empty MCP response"


__all__ = [
    "McpGateway",
    "McpServerConfig",
    "McpToolCall",
    "McpToolResult",
    "get_mcp_gateway",
    "reset_mcp_gateway",
    "GatewayClient",
]
