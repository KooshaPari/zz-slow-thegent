"""Stub module."""

from __future__ import annotations

from typing import Any


class DiscoveryClient:
    """Client for service discovery."""

    def __init__(self) -> None:
        self.services: dict = {}

    def discover(self, service_name: str) -> dict | None:
        """Discover a service."""
        return self.services.get(service_name)


def _fallback_processes() -> dict[str, int]:
    """Get fallback process info."""
    return {"python": 1}


__all__ = [
    "DiscoveryClient",
    "_fallback_processes",
    "_fallback_sessions",
    "_fallback_tools",
]


def _fallback_tools() -> dict[str, bool]:
    """Get fallback tool availability information.

    Returns:
        Dictionary mapping tool names to availability status.
    """
    return {"shell": True, "read": True, "write": True, "edit": True}


def _fallback_sessions() -> list[dict[str, Any]]:
    """Get fallback session information.

    Returns:
        List of session dictionaries.
    """
    return [{"id": "default", "status": "active"}]
