"""Session hook for research engine."""

from __future__ import annotations


def on_session_start(session_id: str) -> None:
    """Called when a session starts."""


def on_session_end(session_id: str) -> None:
    """Called when a session ends."""


def inject_session_context(session_id: str, context: dict[str, Any]) -> dict[str, Any]:
    """Inject session context into a request."""
    return context


__all__ = ["on_session_start", "on_session_end", "inject_session_context"]
