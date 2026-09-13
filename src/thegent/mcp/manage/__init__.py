"""Stub module."""

from typing import Any

DEFAULT_MCP_URL = "http://localhost:8080"


def mcp_down() -> bool:
    """Check if MCP server is down."""
    return False


def mcp_up() -> bool:
    """Check if MCP server is up."""
    return True


def _get_mcp_url(server_name: str) -> str:
    """Get MCP server URL for a given server name.

    Args:
        server_name: Name of the MCP server.

    Returns:
        URL string for the server.
    """
    import os

    env_var = f"MCP_URL_{server_name.upper().replace('-', '_')}"
    return os.environ.get(env_var, DEFAULT_MCP_URL)


def _ensure_mcp_servers(servers: list[str]) -> dict[str, bool]:
    """Ensure MCP servers are available and running.

    Args:
        servers: List of server names to check.

    Returns:
        Dictionary mapping server names to availability status.
    """
    results = {}
    for server in servers:
        url = _get_mcp_url(server)
        results[server] = url != ""  # Stub: assume available if URL is set
    return results


__all__ = [
    "DEFAULT_MCP_URL",
    "mcp_down",
    "mcp_up",
    "_get_mcp_url",
    "_ensure_mcp_servers",
    "_remote_config",
    "install_to_claude_desktop",
    "migrate_to_unimount",
    "install_to_client",
    "install_to_claude_code",
    "install_to_codex",
    "install_to_cursor",
    "install_to_droid",
]


def install_to_cursor(server_name: str) -> bool:
    """Install MCP server to Cursor.

    Args:
        server_name: Name of the MCP server to install.

    Returns:
        True if installation succeeded.
    """
    return True


def install_to_droid(server_name: str) -> bool:
    """Install MCP server to Droid.

    Args:
        server_name: Name of the MCP server to install.

    Returns:
        True if installation succeeded.
    """
    return True


def install_to_claude_code(server_name: str) -> bool:
    """Install MCP server to Claude Code.

    Args:
        server_name: Name of the MCP server to install.

    Returns:
        True if installation succeeded.
    """
    return True


def install_to_codex(server_name: str) -> bool:
    """Install MCP server to Codex.

    Args:
        server_name: Name of the MCP server to install.

    Returns:
        True if installation succeeded.
    """
    return True


def migrate_to_unimount(server_name: str) -> bool:
    """Migrate MCP server configuration to unimount format.

    Args:
        server_name: Name of the MCP server to migrate.

    Returns:
        True if migration succeeded.
    """
    return True


def install_to_client(server_name: str, client: str = "claude") -> bool:
    """Install MCP server to a specific client.

    Args:
        server_name: Name of the MCP server.
        client: Client name to install to.

    Returns:
        True if installation succeeded.
    """
    return True


def _remote_config() -> dict[str, Any]:
    """Get remote MCP configuration.

    Returns:
        Dictionary with remote MCP configuration.
    """
    return {
        "enabled": False,
        "url": DEFAULT_MCP_URL,
    }


def install_to_claude_desktop(server_name: str) -> bool:
    """Install MCP server to Claude Desktop.

    Args:
        server_name: Name of the MCP server to install.

    Returns:
        True if installation succeeded, False otherwise.
    """
    return True


def service_install(server_name: str, **kwargs: Any) -> bool:
    """Install MCP server as a system service.

    Args:
        server_name: Name of the MCP server to install.
        **kwargs: Additional keyword arguments.

    Returns:
        True if installation succeeded.
    """
    return True


def service_start(server_name: str, **kwargs: Any) -> bool:
    """Start MCP server as a system service.

    Args:
        server_name: Name of the MCP server to start.
        **kwargs: Additional keyword arguments.

    Returns:
        True if service started successfully.
    """
    return True


def service_status(server_name: str, **kwargs: Any) -> dict[str, Any]:
    """Get MCP server service status.

    Args:
        server_name: Name of the MCP server.
        **kwargs: Additional keyword arguments.

    Returns:
        Status dictionary with running state.
    """
    return {"server_name": server_name, "running": False, "status": "unknown"}


def service_stop(server_name: str, **kwargs: Any) -> bool:
    """Stop MCP server service.

    Args:
        server_name: Name of the MCP server to stop.
        **kwargs: Additional keyword arguments.

    Returns:
        True if service stopped successfully.
    """
    return True


def service_uninstall(server_name: str, **kwargs: Any) -> bool:
    """Uninstall MCP server service.

    Args:
        server_name: Name of the MCP server to uninstall.
        **kwargs: Additional keyword arguments.

    Returns:
        True if service uninstalled successfully.
    """
    return True
