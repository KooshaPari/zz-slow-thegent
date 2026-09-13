"""Stub module."""

from dataclasses import dataclass


@dataclass
class ContentTabs:
    """Container for content tabs."""

    tabs: list = None

    def __post_init__(self) -> None:
        if self.tabs is None:
            self.tabs = []

    def add_tab(self, name: str, content: str) -> None:
        """Add a tab."""
        self.tabs.append({"name": name, "content": content})


__all__ = ["ContentTabs"]
