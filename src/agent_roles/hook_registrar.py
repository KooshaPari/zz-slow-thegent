"""Hook registrar for agent roles."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


class HookRegistrar:
    """Manages registration and invocation of hooks."""

    def __init__(self) -> None:
        self._hooks: dict[str, list[Callable[..., Any]]] = {}

    def register(self, event: str, hook: Callable[..., Any]) -> None:
        """Register a hook for an event.

        Args:
            event: The event name to hook into.
            hook: The callable to invoke when the event occurs.
        """
        if event not in self._hooks:
            self._hooks[event] = []
        self._hooks[event].append(hook)

    def unregister(self, event: str, hook: Callable[..., Any]) -> bool:
        """Unregister a hook from an event.

        Args:
            event: The event name.
            hook: The hook to remove.

        Returns:
            True if the hook was found and removed.
        """
        if event not in self._hooks:
            return False
        try:
            self._hooks[event].remove(hook)
            return True
        except ValueError:
            return False

    def invoke(self, event: str, *args: Any, **kwargs: Any) -> list[Any]:
        """Invoke all hooks for an event.

        Args:
            event: The event name.
            *args: Positional arguments to pass to hooks.
            **kwargs: Keyword arguments to pass to hooks.

        Returns:
            List of return values from hooks.
        """
        results = []
        hooks = self._hooks.get(event, [])
        for hook in hooks:
            try:
                result = hook(*args, **kwargs)
                results.append(result)
            except Exception:
                pass
        return results


# Global hook registrar
_registrar = HookRegistrar()


def register(event: str, hook: Callable[..., Any]) -> None:
    """Register a hook with the global registrar."""
    _registrar.register(event, hook)


def unregister(event: str, hook: Callable[..., Any]) -> bool:
    """Unregister a hook from the global registrar."""
    return _registrar.unregister(event, hook)


def invoke(event: str, *args: Any, **kwargs: Any) -> list[Any]:
    """Invoke hooks for an event using the global registrar."""
    return _registrar.invoke(event, *args, **kwargs)


__all__ = ["HookRegistrar", "register", "unregister", "invoke"]
