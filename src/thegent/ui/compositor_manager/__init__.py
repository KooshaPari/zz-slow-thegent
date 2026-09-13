"""Stub module."""

from dataclasses import dataclass
from typing import Any


@dataclass
class CompositorSlot:
    """A slot in the compositor layout."""

    name: str
    position: tuple[int, int] = (0, 0)
    size: tuple[int, int] = (80, 24)


@dataclass
class Layout:
    """Layout for the compositor."""

    name: str = "default"
    slots: list[CompositorSlot] | None = None


class CompositorManager:
    """Manages compositor instances and layouts."""

    def __init__(self) -> None:
        self._compositors: dict[str, Any] = {}
        self._layouts: dict[str, Layout] = {}

    def add_compositor(self, name: str, compositor: Any) -> None:
        """Add a compositor by name."""
        self._compositors[name] = compositor

    def get_compositor(self, name: str) -> Any | None:
        """Get a compositor by name."""
        return self._compositors.get(name)

    def add_layout(self, layout: Layout) -> None:
        """Add a layout."""
        self._layouts[layout.name] = layout

    def get_layout(self, name: str) -> Layout | None:
        """Get a layout by name."""
        return self._layouts.get(name)


__all__ = ["CompositorManager", "CompositorSlot", "Layout"]
