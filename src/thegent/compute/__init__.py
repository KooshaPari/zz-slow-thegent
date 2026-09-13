"""STUB MODULE - thegent.compute

WARNING: This is an auto-generated stub module.
The actual implementation was moved/deleted during repository restructuring.
This stub exists for backwards compatibility with existing tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class RemoteTask:
    """Remote task representation."""

    task_id: str
    command: str
    node: str = ""


@dataclass
class TailscaleConfig:
    """Tailscale configuration."""

    auth_key: str = ""
    hostname: str = ""


class TailscaleManager:
    """Manager for Tailscale connections."""

    def __init__(self, config: TailscaleConfig | None = None) -> None:
        self.config = config or TailscaleConfig()

    def connect(self) -> bool:
        """Connect to Tailscale."""
        return True

    def disconnect(self) -> None:
        """Disconnect from Tailscale."""

    def get_status(self) -> dict[str, str]:
        """Get Tailscale status."""
        return {"status": "disconnected"}


@dataclass
class TailscaleNode:
    """Tailscale node information."""

    node_id: str = ""
    hostname: str = ""
    ip_address: str = ""
    status: str = "offline"


class RemoteRunner:
    """Runner for remote execution."""

    def __init__(self) -> None:
        self.nodes: list[str] = []

    def run(self, command: str, node: str | None = None) -> dict[str, Any]:
        """Run command on remote node."""
        return {"status": "ok", "output": ""}


class RemoteRunnerError(Exception):
    """Error raised when remote runner fails."""


class RemoteExecutorError(Exception):
    """Error raised when remote executor fails."""


class RemoteExecutor:
    """Executor for remote operations."""

    def __init__(self) -> None:
        self.executors: list[RemoteRunner] = []

    def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        """Execute a remote task."""
        return {"status": "executed"}


@dataclass
class RemoteResult:
    """Result of a remote operation."""

    success: bool
    output: str = ""
    error: str = ""


@dataclass
class RemoteProcess:
    """Remote process representation."""

    pid: int
    node: str
    command: str


__all__ = [
    "RemoteTask",
    "TailscaleConfig",
    "TailscaleManager",
    "TailscaleNode",
    "RemoteRunner",
    "RemoteRunnerError",
    "RemoteExecutor",
    "RemoteExecutorError",
    "RemoteResult",
    "RemoteProcess",
    "get_compute_config",
]


def get_compute_config() -> dict[str, Any]:
    """Get the compute configuration."""
    return {
        "enabled": False,
        "backend": "local",
        "max_workers": 4,
    }
