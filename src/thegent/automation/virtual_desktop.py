"""Virtual desktop automation module."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DesktopConfig:
    """Configuration for virtual desktop."""
    name: str
    memory_mb: int = 1024
    cpu_count: int = 2
    display: str = ":0"


__all__ = ["DesktopConfig", "DesktopState", "DesktopSession", "InputEvent", "ScreenFrame", "VirtualDesktopManager", "get_desktop_manager"]


def get_desktop_manager() -> VirtualDesktopManager:
    """Get the global desktop manager instance."""
    global _desktop_manager
    if _desktop_manager is None:
        _desktop_manager = VirtualDesktopManager()
    return _desktop_manager


_desktop_manager: VirtualDesktopManager | None = None


@dataclass
class InputEvent:
    """An input event for virtual desktop."""
    event_type: str = "key"
    key_code: int = 0
    x: int = 0
    y: int = 0


class DesktopSession:
    """A virtual desktop session."""
    def __init__(self, name: str) -> None:
        self.name = name
        self.active = False


@dataclass
class ScreenFrame:
    """A screen frame capture."""
    width: int = 1920
    height: int = 1080
    data: bytes = b""


@dataclass
class DesktopState:
    """State of a virtual desktop."""
    name: str
    running: bool = False
    memory_mb: int = 0
    cpu_count: int = 0


class VirtualDesktopManager:
    """Manager for virtual desktops."""

    def __init__(self) -> None:
        self._desktops: dict[str, DesktopSession] = {}

    def create(self, config: DesktopConfig) -> DesktopSession:
        """Create a virtual desktop."""
        session = DesktopSession(name=config.name)
        self._desktops[config.name] = session
        return session

    def list(self) -> list[DesktopSession]:
        """List all virtual desktops."""
        return list(self._desktops.values())
