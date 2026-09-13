"""Stub module."""

from dataclasses import dataclass


@dataclass
class DiskIoStats:
    """Disk I/O statistics."""

    read_bytes: int = 0
    write_bytes: int = 0
    read_count: int = 0
    write_count: int = 0


@dataclass
class DiskQueueSample:
    """Sample of disk queue depth."""

    timestamp: float = 0.0
    queue_depth: int = 0
    read_latency_ms: float = 0.0
    write_latency_ms: float = 0.0


class DiskMonitor:
    """Monitor for disk resources."""

    def get_stats(self) -> DiskIoStats:
        """Get disk I/O statistics."""
        return DiskIoStats()


__all__ = ["DiskIoStats", "DiskMonitor", "DiskQueueSample"]
