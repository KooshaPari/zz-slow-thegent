"""STUB MODULE - thegent.thegent_platform

WARNING: This is an auto-generated stub module.
The actual implementation was moved/deleted during repository restructuring.
This stub exists for backwards compatibility with existing tests.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class PlatformEnum(Enum):
    """Platform enumeration."""
    MACOS = "macos"
    LINUX = "linux"
    WINDOWS = "windows"
    UNKNOWN = "unknown"


# Alias for backwards compatibility
Platform = PlatformEnum


def detect_platform() -> PlatformEnum:
    """Detect the current platform.

    Returns:
        PlatformEnum value for the current platform.
    """
    import platform
    import sys

    system = platform.system().lower()
    return {
        "darwin": PlatformEnum.MACOS,
        "linux": PlatformEnum.LINUX,
        "windows": PlatformEnum.WINDOWS,
    }.get(system, PlatformEnum.UNKNOWN)


class ThegentPlatform:
    """Thegent platform core class."""

    def __init__(self) -> None:
        self.config: dict[str, Any] = {}

    def initialize(self) -> bool:
        """Initialize the platform."""
        return True

    def shutdown(self) -> None:
        """Shutdown the platform."""


__all__ = ["ThegentPlatform", "detect_platform", "Platform", "PlatformEnum"]
