"""MacOS desktop automation module."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class AutomationError(Exception):
    """Error during automation."""


@dataclass
class AutomationResult:
    """Result of an automation operation."""

    success: bool
    message: str = ""
    data: dict[str, Any] | None = None


__all__ = ["AutomationError", "AutomationResult", "MacOSDesktopAutomation"]


class MacOSDesktopAutomation:
    """MacOS desktop automation."""

    def __init__(self) -> None:
        pass

    def screenshot(self) -> bytes:
        """Take a screenshot."""
        return b""
