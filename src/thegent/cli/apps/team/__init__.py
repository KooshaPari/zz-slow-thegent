"""CLI team module."""

from __future__ import annotations

from typing import Any


class TeamApp:
    """Team CLI application."""

    def __init__(self) -> None:
        self.name = "team"


app: Any = TeamApp()


__all__ = ["app", "TeamApp"]
