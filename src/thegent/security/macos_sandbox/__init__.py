"""Stub module."""

from enum import Enum


class SandboxLevel(Enum):
    """Sandbox level enumeration."""

    NONE = "none"
    BASIC = "basic"
    RESTRICTED = "restricted"
    FULL = "full"


SANDBOX_LEVEL_ENV_VAR = "THEGENT_SANDBOX_LEVEL"

__all__ = [
    "SandboxLevel",
    "SANDBOX_LEVEL_ENV_VAR",
    "SANDBOX_PROFILE_DIR",
    "MacOSSandbox",
]


class MacOSSandbox:
    """macOS sandbox wrapper."""

    def __init__(self, level: SandboxLevel = SandboxLevel.BASIC) -> None:
        self.level = level

    def is_enabled(self) -> bool:
        """Check if sandbox is enabled."""
        return self.level != SandboxLevel.NONE


SANDBOX_PROFILE_DIR = "/usr/local/etc/thegent/sandbox"
