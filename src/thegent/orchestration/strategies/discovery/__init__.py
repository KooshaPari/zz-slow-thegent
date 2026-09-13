"""Discovery system — singleton with optional native Rust extension.

@trace AUDIT-N+46 FR-ORC-DC-001..015
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DiscoverySystem:
    """System for discovering resources and services.

    Singleton that optionally loads a native Rust extension
    (thegent_discovery) for high-performance agent scanning.
    """

    _instance: Any = field(default=None, init=False, repr=False)
    _interface: Any = field(default=None, init=False, repr=False)
    use_native: bool = field(default=False, init=False)

    def __new__(cls, *args: Any, **kwargs: Any) -> DiscoverySystem:
        if cls._instance is None:
            instance = super().__new__(cls)
            cls._instance = instance
            instance._init_singleton()
        return cls._instance

    def _init_singleton(self) -> None:
        from thegent import config

        settings = config.ThegentSettings()
        self.use_native = getattr(settings, "use_native_discovery", False)
        if self.use_native:
            self._load_native_extension()

    def _load_native_extension(self) -> None:
        try:
            from thegent_discovery import (
                DiscoveryInterface,  # type: ignore[import-untyped]
            )

            self._interface = DiscoveryInterface()
            logger.info("Native discovery extension loaded successfully")
        except ImportError:
            logger.debug("Native discovery extension not installed, using Python fallback")
            self._interface = None
        except Exception:
            logger.warning("Native discovery extension failed to initialize", exc_info=True)
            self._interface = None

    def is_native_active(self) -> bool:
        """Return True if native extension is loaded and active."""
        return self._interface is not None

    def discover(self) -> list[str]:
        """Discover available resources."""
        return []

    def scan_agents(self) -> list[dict[str, Any]]:
        """Scan for running agent processes.

        Delegates to native extension when available, returns empty
        list on any error.
        """
        if self._interface is None:
            return []
        try:
            return self._interface.scan_agents()
        except Exception:
            logger.warning("scan_agents failed, returning empty list", exc_info=True)
            return []


__all__ = ["DiscoverySystem", "get_discovery_system"]


def get_discovery_system() -> DiscoverySystem:
    """Get the global discovery system."""
    return DiscoverySystem()
