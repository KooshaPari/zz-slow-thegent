"""Stub module."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


class NetworkMonitor:
    """Monitor for network resources."""

    def __init__(self) -> None:
        self.latency_ms: float = 0.0

    def get_status(self) -> dict[str, Any]:
        """Get network status."""
        return {"latency_ms": self.latency_ms, "connected": True}

    def measure_latency(self, host: str) -> float:
        """Measure latency to a host."""
        return 0.0


__all__ = ["NetworkMonitor", "BandwidthSample", "NetworkStats"]


@dataclass
class BandwidthSample:
    """A bandwidth measurement sample."""

    timestamp: str
    download_bps: float = 0.0
    upload_bps: float = 0.0
    latency_ms: float = 0.0

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class NetworkStats:
    """Network statistics."""

    bytes_sent: int = 0
    bytes_received: int = 0
    packets_sent: int = 0
    packets_received: int = 0
    errors_in: int = 0
    errors_out: int = 0
    timestamp: str = ""
