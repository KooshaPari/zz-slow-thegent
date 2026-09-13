"""STUB MODULE - thegent.automation

WARNING: This is an auto-generated stub module.
The actual implementation was moved/deleted during repository restructuring.
This stub exists for backwards compatibility with existing tests.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class AutomationResult:
    """Result of an automation operation."""

    success: bool
    output: str = ""
    error: str = ""


@dataclass
class DesktopState:
    """State of a virtual desktop."""

    id: str
    name: str
    active: bool = False


class MacOSSandbox:
    """Sandbox for macOS automation."""

    def __init__(self) -> None:
        self.enabled: bool = False


__all__ = ["AutomationResult", "DesktopState", "MacOSSandbox"]
