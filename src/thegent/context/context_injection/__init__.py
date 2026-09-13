"""Stub module."""

from typing import Any


class ContextInjector:
    """Injector for context into operations."""

    def __init__(self) -> None:
        self.context: dict[str, Any] = {}

    def inject(self, key: str, value: Any) -> None:
        """Inject context value."""
        self.context[key] = value

    def get(self, key: str) -> Any | None:
        """Get context value."""
        return self.context.get(key)


__all__ = ["ContextInjector"]
