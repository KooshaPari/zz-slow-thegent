"""Sitback module for background processing."""

from __future__ import annotations

from typing import Any

from .watchdog import Watchdog

__all__ = [
    "Watchdog",
    "probe_harness_status",
    "get_harness_info",
    "_probe_harness_status",
]


def _probe_harness_status() -> dict[str, Any]:
    """Probe harness status."""
    return {"status": "ok"}


def probe_harness_status() -> dict[str, Any]:
    """Probe the harness status."""
    return {"status": "running", "mode": "sitback"}


def get_harness_info() -> dict[str, Any]:
    """Get harness information."""
    return {
        "name": "sitback",
        "version": "1.0.0",
        "mode": "background",
    }
