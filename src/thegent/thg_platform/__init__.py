"""Platform module."""

from __future__ import annotations

__all__ = ["Platform"]


class Platform:
    """Platform abstraction."""

    @staticmethod
    def paths() -> dict[str, str]:
        """Get platform paths."""
        return {"home": "/Users"}
