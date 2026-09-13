"""Stub module."""

from typing import Any


def extract_fail_closed_signals(alerts: list[dict[str, Any]]) -> list[str]:
    """Extract fail-closed signals from governance alerts."""
    return []


def parse_last_alert_summary(alerts: list[dict[str, Any]]) -> dict[str, Any]:
    """Parse the last alert summary."""
    return {"count": len(alerts), "last": alerts[-1] if alerts else None}


def render_markdown_summary(alerts: list[dict[str, Any]]) -> str:
    """Render governance alerts as markdown summary."""
    return f"## Governance Alert Summary\n\nTotal: {len(alerts)} alerts"


__all__ = [
    "extract_fail_closed_signals",
    "parse_last_alert_summary",
    "render_markdown_summary",
]
