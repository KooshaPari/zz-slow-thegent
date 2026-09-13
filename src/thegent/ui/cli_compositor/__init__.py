"""Stub module."""

from typing import Any


class CliCompositor:
    """CLI-based compositor."""

    def __init__(self) -> None:
        self._panes: list[Any] = []

    def add_pane(self, pane: Any) -> None:
        """Add a pane to the compositor."""
        self._panes.append(pane)

    def render(self) -> str:
        """Render the compositor to CLI output."""
        return ""


class ProgressPanel:
    """CLI panel for displaying progress."""

    def __init__(self, title: str = "") -> None:
        self.title = title
        self._progress: float = 0.0

    def set_progress(self, value: float) -> None:
        """Set the progress value (0.0 to 1.0)."""
        self._progress = max(0.0, min(1.0, value))

    def render(self) -> str:
        """Render the progress panel."""
        bar_width = 40
        filled = int(bar_width * self._progress)
        bar = "=" * filled + "-" * (bar_width - filled)
        return f"[{self.title}] [{bar}] {self._progress * 100:.1f}%"


class StatusPanel:
    """CLI panel for displaying status."""

    def __init__(self, title: str = "") -> None:
        self.title = title
        self._status: str = "idle"

    def set_status(self, status: str) -> None:
        """Set the status text."""
        self._status = status

    def render(self) -> str:
        """Render the status panel."""
        return f"[{self.title}] {self._status}"


def make_cli_compositor() -> CliCompositor:
    """Factory function to create a CLI compositor."""
    return CliCompositor()


__all__ = ["CliCompositor", "ProgressPanel", "StatusPanel", "make_cli_compositor"]
