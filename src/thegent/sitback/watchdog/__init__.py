"""STUB MODULE - thegent.sitback.watchdog

WARNING: This is an auto-generated stub module.
The actual implementation was moved/deleted during repository restructuring.
This stub exists for backwards compatibility with existing tests.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

__all__ = ["Watchdog", "WatcherDaemon"]


class Watchdog:
    """Watchdog for monitoring."""

    def __init__(self, timeout: int = 60) -> None:
        self.timeout = timeout
        self.active = False

    def start(self) -> None:
        """Start the watchdog."""
        self.active = True

    def stop(self) -> None:
        """Stop the watchdog."""
        self.active = False

    def is_alive(self) -> bool:
        """Check if watchdog is alive."""
        return self.active


class WatcherDaemon:
    """Watcher daemon for monitoring file system changes."""

    def __init__(
        self,
        watch_paths: list[str],
        on_change: Callable[[str], None] | None = None,
        poll_interval: float = 1.0,
    ) -> None:
        """Initialize the watcher daemon.

        Args:
            watch_paths: List of paths to watch for changes.
            on_change: Callback function to invoke on file changes.
            poll_interval: Interval in seconds between polls.
        """
        self.watch_paths = watch_paths
        self.on_change = on_change
        self.poll_interval = poll_interval
        self._running = False
        self._last_states: dict[str, float] = {}

    def start(self) -> None:
        """Start the watcher daemon."""
        self._running = True

    def stop(self) -> None:
        """Stop the watcher daemon."""
        self._running = False

    def is_running(self) -> bool:
        """Check if the daemon is running."""
        return self._running

    def check_changes(self) -> list[str]:
        """Check for file system changes.

        Returns:
            List of paths that have changed.
        """
        changed = []
        for path_str in self.watch_paths:
            try:
                from pathlib import Path

                path = Path(path_str)
                if path.exists():
                    mtime = path.stat().st_mtime
                    if path_str not in self._last_states:
                        self._last_states[path_str] = mtime
                    elif self._last_states[path_str] != mtime:
                        changed.append(path_str)
                        self._last_states[path_str] = mtime
            except Exception:
                pass
        return changed

    def run_once(self) -> list[str]:
        """Run one check cycle.

        Returns:
            List of changed paths.
        """
        changed = self.check_changes()
        for path in changed:
            if self.on_change:
                self.on_change(path)
        return changed

    def watch(self) -> None:
        """Run the watcher in a loop."""
        self.start()
        while self._running:
            self.run_once()
            time.sleep(self.poll_interval)
