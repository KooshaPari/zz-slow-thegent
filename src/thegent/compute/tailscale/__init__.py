"""Stub module."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class TailscaleConfig:
    """Tailscale configuration."""

    auth_key: str = ""
    hostname: str = ""


class TailscaleClient:
    """Client for Tailscale operations."""

    def __init__(self) -> None:
        self.connected: bool = False

    def connect(self) -> bool:
        """Connect to Tailscale."""
        self.connected = True
        return True


class TailscaleError(Exception):
    """Exception raised for Tailscale errors."""


__all__ = [
    "TailscaleConfig",
    "TailscaleClient",
    "TailscaleError",
    "TailscaleManager",
    "TailscaleNode",
]


class TailscaleManager:
    """Manager for Tailscale operations."""

    def __init__(self) -> None:
        self.client = TailscaleClient()

    def get_node(self, name: str) -> dict[str, Any] | None:
        """Get a Tailscale node by name."""
        return None


@dataclass
class TailscaleNode:
    """Represents a Tailscale node."""

    name: str = ""
    ip_address: str = ""
    online: bool = False
