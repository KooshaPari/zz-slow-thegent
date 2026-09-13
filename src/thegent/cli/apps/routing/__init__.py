"""Stub module."""

from typing import TYPE_CHECKING, Any


class RoutingApp:
    """Routing application stub."""

    def route(self, request: dict[str, Any]) -> dict[str, Any]:
        return {"routed": True}


app = RoutingApp()

__all__ = ["app", "RoutingApp"]
