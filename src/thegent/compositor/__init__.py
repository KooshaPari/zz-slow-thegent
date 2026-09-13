"""STUB MODULE - thegent.compositor

WARNING: This is an auto-generated stub module.
The actual implementation was moved/deleted during repository restructuring.
This stub exists for backwards compatibility with existing tests.
"""

from __future__ import annotations

from typing import Any


class Compositor:
    """Compositor for UI elements."""

    def __init__(self) -> None:
        self._elements: list[Any] = []

    def add_element(self, element: Any) -> None:
        """Add an element."""
        self._elements.append(element)


class PaneManager:
    """Manager for compositor panes."""

    def __init__(self) -> None:
        self.panes: list = []


class SessionState:
    """Session state for compositor."""

    def __init__(self) -> None:
        self.state: dict = {}


__all__ = ["Compositor", "PaneManager", "SessionState"]
