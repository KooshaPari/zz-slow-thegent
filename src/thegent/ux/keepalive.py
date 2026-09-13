"""Terminal keepalive for long-running tasks.

Provides periodic output to stdout to prevent terminal timeouts during
long-running operations. Designed for CLI tools that may take minutes
or hours to complete.

Classes:
    KeepaliveConfig: Configuration for terminal keepalive behavior.
    TerminalKeepalive: Manages a background thread that periodically prints a message.

Functions:
    keepalive: Convenience context manager for terminal keepalive.
"""

from __future__ import annotations

import sys
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass
class KeepaliveConfig:
    """Configuration for terminal keepalive behavior.

    Attributes:
        interval_s: Seconds between keepalive messages (default: 30).
        message: Message to print on each tick (default: ".").
        newline_every: Print a newline after this many messages (default: 10).
            Set to 0 to disable automatic newlines.
        enabled: If False, no output is produced (default: True).
    """

    interval_s: float = 30.0
    message: str = "."
    newline_every: int = 10
    enabled: bool = True


class TerminalKeepalive:
    """Prints periodic messages to stdout to prevent terminal timeouts.

    Uses a background daemon thread that periodically writes to stdout
    when running in an interactive terminal.

    Args:
        config: KeepaliveConfig instance with desired behavior.
    """

    def __init__(self, config: KeepaliveConfig) -> None:
        self._config = config
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._tick_count = 0

    @staticmethod
    def _is_tty() -> bool:
        """Check if stdout is a TTY. Returns False on any error."""
        try:
            return sys.stdout.isatty()
        except (AttributeError, OSError):
            return False

    def _run_loop(self) -> None:
        """Background thread loop that prints keepalive messages."""
        interval = self._config.interval_s
        message = self._config.message
        newline_every = self._config.newline_every

        while not self._stop_event.wait(interval):
            self._tick_count += 1
            try:
                if newline_every > 0 and self._tick_count % newline_every == 0:
                    sys.stdout.write("\n")
                    sys.stdout.flush()
                else:
                    sys.stdout.write(message)
                    sys.stdout.flush()
            except OSError:
                # Swallow broken pipe / closed stdout errors
                pass

    def start(self) -> None:
        """Start the keepalive background thread.

        Idempotent: calling start() multiple times does not create
        additional threads.
        """
        if not self._config.enabled:
            return

        if not self._is_tty():
            return

        if self._thread is not None and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the keepalive background thread.

        Safe to call even if the thread was never started.
        Idempotent: calling stop() multiple times is safe.
        """
        if self._thread is None:
            return

        self._stop_event.set()
        self._thread.join(timeout=1.0)
        self._thread = None

        # Always print trailing newline after stopping
        try:
            if self._tick_count > 0:
                sys.stdout.write("\n")
                sys.stdout.flush()
        except OSError:
            pass

    def __enter__(self) -> TerminalKeepalive:
        """Start keepalive on context manager entry."""
        self.start()
        return self

    def __exit__(self, *_: object) -> None:
        """Stop keepalive on context manager exit."""
        try:
            self.stop()
        except Exception:
            # Ensure thread cleanup even if stop() raises
            self._thread = None
            raise


@contextmanager
def keepalive(
    interval_s: float = 30.0,
    message: str = ".",
    newline_every: int = 10,
) -> Iterator[TerminalKeepalive]:
    """Convenience context manager for terminal keepalive.

    Args:
        interval_s: Seconds between keepalive messages.
        message: Message to print on each tick.
        newline_every: Print a newline after this many messages.

    Yields:
        TerminalKeepalive instance.

    Example:
        with keepalive(interval_s=10, message=".") as ka:
            # Long-running task here
            pass
    """
    config = KeepaliveConfig(
        interval_s=interval_s,
        message=message,
        newline_every=newline_every,
        enabled=True,
    )
    ka = TerminalKeepalive(config)
    try:
        ka.start()
        yield ka
    finally:
        ka.stop()
