"""Compositor components module."""

from __future__ import annotations


class DiffViewerPanel:
    """Diff viewer panel component."""

    def __init__(self) -> None:
        self.name = "diff_viewer"


class FooterStatusBar:
    """Footer status bar component."""

    def __init__(self) -> None:
        self.visible = True


class HeaderWidget:
    """Header widget component."""

    def __init__(self) -> None:
        self.title = ""


__all__ = [
    "DiffViewerPanel",
    "FooterStatusBar",
    "HeaderWidget",
    "MetricsPanel",
    "OutputWidget",
    "ProgressIndicator",
    "SidebarWidget",
    "StatusWidget",
]


class StatusWidget:
    """Status widget component."""

    def __init__(self) -> None:
        self.name = "status"
        self.status: str = "idle"


class SidebarWidget:
    """Sidebar widget component."""

    def __init__(self) -> None:
        self.name = "sidebar"
        self.collapsed: bool = False


class ProgressIndicator:
    """Progress indicator component."""

    def __init__(self) -> None:
        self.name = "progress"
        self.value: float = 0.0
        self.max: float = 100.0


class OutputWidget:
    """Output widget component."""

    def __init__(self) -> None:
        self.name = "output"
        self.content: str = ""


class MetricsPanel:
    """Metrics panel component."""

    def __init__(self) -> None:
        self.name = "metrics"
        self.metrics: dict[str, float] = {}
