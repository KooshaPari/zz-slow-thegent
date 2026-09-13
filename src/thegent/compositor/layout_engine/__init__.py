"""Compositor layout engine module."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Direction(Enum):
    """Layout direction."""

    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class LayoutEngine:
    """Layout engine for compositor."""

    def __init__(self) -> None:
        self.direction = Direction.HORIZONTAL

    def layout(self, elements: list) -> dict:
        """Layout elements."""
        return {"layout": "default"}


__all__ = ["Direction", "LayoutEngine", "LayoutNode", "Padding", "Size", "SizeUnit"]


class SizeUnit(Enum):
    """Size unit for layout elements."""

    PIXELS = "px"
    PERCENT = "%"
    AUTO = "auto"


@dataclass
class Size:
    """Size for layout elements."""

    width: int = 0
    height: int = 0


@dataclass
class Padding:
    """Padding for layout elements."""

    top: int = 0
    right: int = 0
    bottom: int = 0
    left: int = 0


class LayoutNode:
    """A node in the layout tree."""

    def __init__(self, name: str, children: list[LayoutNode] | None = None) -> None:
        self.name = name
        self.children = children or []
        self.width: int = 0
        self.height: int = 0

    def add_child(self, node: LayoutNode) -> None:
        """Add a child node."""
        self.children.append(node)
