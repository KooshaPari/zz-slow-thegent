"""Stub module."""

from dataclasses import dataclass


@dataclass
class GpuInfo:
    """GPU information."""

    name: str = ""
    memory_total: int = 0
    memory_used: int = 0


class GpuMonitor:
    """Monitor for GPU resources."""

    def __init__(self) -> None:
        self.gpus: list[GpuInfo] = []

    def get_available_gpus(self) -> list[GpuInfo]:
        """Get list of available GPUs."""
        return self.gpus


__all__ = ["GpuInfo", "GpuMonitor", "GpuMonitorError"]


class GpuMonitorError(Exception):
    """Error in GPU monitoring."""
