"""CLI apps package for thegent."""

from __future__ import annotations

from typing import Any


class AuditApp:
    """Audit CLI application."""

    def __init__(self) -> None:
        self.name = "audit"


audit: Any = AuditApp()


__all__ = ["audit", "AuditApp"]
