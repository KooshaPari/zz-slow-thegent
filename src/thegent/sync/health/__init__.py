"""Stub module."""

from dataclasses import dataclass


@dataclass
class ConnectorHealth:
    """Health status of a connector."""

    name: str = ""
    healthy: bool = True
    latency_ms: float = 0.0


__all__ = ["ConnectorHealth", "render_health_scoreboard"]


def render_health_scoreboard(healths: list[ConnectorHealth]) -> str:
    """Render a health scoreboard from connector health statuses."""
    lines = ["Health Scoreboard:"]
    for h in healths:
        status = "OK" if h.healthy else "FAIL"
        lines.append(f"  {h.name}: {status} ({h.latency_ms:.2f}ms)")
    return "\n".join(lines)
