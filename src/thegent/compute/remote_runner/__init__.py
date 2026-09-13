"""Stub module."""

from dataclasses import dataclass
from typing import Any


@dataclass
class RemoteProcess:
    """Remote process representation."""

    pid: int
    node: str
    command: str


class RemoteRunner:
    """Runner for remote execution."""

    def __init__(self) -> None:
        self.nodes: list[str] = []

    def run(self, command: str, node: str | None = None) -> dict[str, Any]:
        """Run command on remote node."""
        return {"status": "ok", "output": ""}


__all__ = ["RemoteProcess", "RemoteRunner", "RemoteRunnerError", "load_config_from_env"]


def load_config_from_env() -> dict[str, Any]:
    """Load configuration from environment variables."""
    import os

    return {
        "host": os.environ.get("REMOTE_RUNNER_HOST", "localhost"),
        "port": int(os.environ.get("REMOTE_RUNNER_PORT", "8080")),
    }


class RemoteRunnerError(Exception):
    """Exception raised for remote runner errors."""
