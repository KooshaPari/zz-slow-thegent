"""Port lease management for testing."""

from __future__ import annotations

import socket


class PortLeaseManager:
    """Manager for allocating and releasing test ports."""

    def __init__(self) -> None:
        """Initialize the port lease manager."""
        self._leased_ports: set[int] = set()

    def allocate(self, port_hint: int | None = None) -> int:
        """Allocate a port for testing.

        Args:
            port_hint: Optional port number to try first.

        Returns:
            Allocated port number.
        """
        if port_hint is not None and self._is_port_available(port_hint):
            self._leased_ports.add(port_hint)
            return port_hint

        # Try a range of ports
        for port in range(8000, 9000):
            if self._is_port_available(port):
                self._leased_ports.add(port)
                return port

        raise RuntimeError("No available ports in range 8000-9000")

    def release(self, port: int) -> None:
        """Release a previously allocated port.

        Args:
            port: Port number to release.
        """
        self._leased_ports.discard(port)

    def _is_port_available(self, port: int) -> bool:
        """Check if a port is available.

        Args:
            port: Port number to check.

        Returns:
            True if port is available, False otherwise.
        """
        if port in self._leased_ports:
            return False
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.1)
                sock.bind(("127.0.0.1", port))
                return True
        except OSError:
            return False

    def get_leased_ports(self) -> list[int]:
        """Get list of currently leased ports.

        Returns:
            List of leased port numbers.
        """
        return list(self._leased_ports)


__all__ = ["PortLeaseManager"]
