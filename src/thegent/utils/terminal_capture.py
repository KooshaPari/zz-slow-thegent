"""Multi-backend terminal output capture.

Provides a unified interface for capturing the last N lines of terminal output
across multiple backends: tmux, zmx, /proc fd, termitty, and a null fallback.

Selection order (first available wins):
1. tmux  -- ``capture-pane`` via subprocess
2. zmx   -- ZmxBackend.capture() if zmx binary present
3. proc  -- read /proc/{pid}/fd/1 on Linux
4. termitty -- VirtualTerminal.process_output() on already-captured bytes
5. none  -- empty result

FR-SES-001: Session backend must be pluggable and auto-detected.
FR-SES-002: Missing backend must not raise at import time.
FR-SES-003: All backend methods must return typed results, never raise on
            subprocess failure -- caller decides how to handle.
"""

from __future__ import annotations

import logging
import os
import platform
import shutil
import subprocess
from dataclasses import dataclass, field

from thegent.infra.shim_subprocess import run as shim_run

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass
class CaptureResult:
    """Result of a terminal capture operation.

    # @trace FR-SES-001
    """

    lines: list[str] = field(default_factory=list)
    backend: str = "none"  # "tmux" | "zmx" | "termitty" | "proc" | "none"
    pane_id: str | None = None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _is_tmux_available() -> bool:
    """Return True if the tmux binary is on PATH."""
    return shutil.which("tmux") is not None


def _trim_to_n(raw_lines: list[str], n: int) -> list[str]:
    """Return the last *n* lines from *raw_lines*."""
    return raw_lines[-n:] if len(raw_lines) > n else raw_lines


def _capture_via_tmux(pane_id: str, n: int) -> CaptureResult | None:
    """Attempt to capture *n* lines from a tmux pane.

    Returns a CaptureResult on success, None when tmux is unavailable or
    the capture fails.

    # @trace FR-SES-002, FR-SES-003
    """
    if not _is_tmux_available():
        logger.debug("tmux not on PATH; skipping tmux backend")
        return None

    cmd = ["tmux", "capture-pane", "-p", "-t", pane_id, "-S", f"-{n}"]
    try:
        result = shim_run(cmd, capture_output=True, text=True, timeout=10, check=False)
        if result.returncode != 0:
            logger.debug(
                "tmux capture-pane exited %d for pane %r: %s",
                result.returncode,
                pane_id,
                result.stderr.strip(),
            )
            return None
        lines = _trim_to_n(result.stdout.splitlines(), n)
        return CaptureResult(lines=lines, backend="tmux", pane_id=pane_id)
    except (OSError, subprocess.TimeoutExpired) as exc:
        logger.debug("tmux capture failed: %s", exc)
        return None


def _capture_via_zmx(session_name: str, n: int) -> CaptureResult | None:
    """Attempt to capture *n* lines from a zmx session.

    Returns a CaptureResult on success, None when ZmxBackend is unavailable
    or the capture fails.

    # @trace FR-SES-002, FR-SES-003
    """
    try:
        from thegent.session.zmx_backend import ZmxBackend
    except ImportError:
        logger.debug("ZmxBackend import failed; skipping zmx backend")
        return None

    backend = ZmxBackend()
    if not backend.available:
        logger.debug("zmx binary not available; skipping zmx backend")
        return None

    output = backend.capture(session_name, last_lines=n)
    if not output:
        logger.debug("zmx capture returned empty output for session %r", session_name)
        return None

    lines = _trim_to_n(output.splitlines(), n)
    return CaptureResult(lines=lines, backend="zmx", pane_id=session_name)


def _capture_via_proc(pid: int, n: int) -> CaptureResult | None:
    """Attempt to read *n* lines from /proc/{pid}/fd/1 on Linux.

    This works only on Linux where /proc is available and the target process
    has its stdout connected to a readable pipe or pty.

    Returns a CaptureResult on success, None on any failure.

    # @trace FR-SES-002, FR-SES-003
    """
    if platform.system() != "Linux":
        logger.debug("/proc not available on %s; skipping proc backend", platform.system())
        return None

    fd_path = f"/proc/{pid}/fd/1"
    try:
        with open(fd_path, "rb") as fh:
            data = fh.read(1024 * 1024)  # read up to 1 MiB
    except OSError as exc:
        logger.debug("Cannot read %s: %s", fd_path, exc)
        return None

    text = data.decode("utf-8", errors="replace")
    lines = _trim_to_n(text.splitlines(), n)
    return CaptureResult(lines=lines, backend="proc", pane_id=str(pid))


def _capture_via_termitty(raw_bytes: bytes, n: int) -> CaptureResult | None:
    """Process *raw_bytes* through a Termitty VirtualTerminal and return last *n* lines.

    Returns a CaptureResult on success, None when termitty is not installed.

    # @trace FR-SES-002, FR-SES-003
    """
    try:
        from termitty import VirtualTerminal  # type: ignore[reportMissingImports]
    except ImportError:
        logger.debug("termitty not installed; skipping termitty backend")
        return None

    # Use a wide virtual terminal (220 columns) to avoid unwanted wrapping
    vt = VirtualTerminal(width=220, height=max(n, 24))
    vt.process_output(raw_bytes)
    screen_text: str = vt.get_screen_text()
    raw_lines = screen_text.splitlines()
    # Strip trailing blank lines produced by the empty screen rows
    while raw_lines and not raw_lines[-1].strip():
        raw_lines.pop()
    lines = _trim_to_n(raw_lines, n)
    return CaptureResult(lines=lines, backend="termitty", pane_id=None)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


class TerminalCapture:
    """Unified multi-backend terminal output capture.

    Instantiate once and call :meth:`capture_last_n_lines` or
    :meth:`capture_by_pid` as needed.  All methods return a
    :class:`CaptureResult` -- they never raise.

    # @trace FR-SES-001
    """

    def capture_last_n_lines(
        self,
        n: int = 50,
        pane_id: str | None = None,
    ) -> CaptureResult:
        """Capture the last *n* lines of terminal output.

        Backend selection order:
        1. tmux  -- if a *pane_id* is given and tmux is available
        2. zmx   -- if a *pane_id* is given (treated as session name) and zmx is available
        3. termitty -- reads the controlling tty of the current process
        4. none  -- empty fallback

        Args:
            n: Number of lines to capture (default 50).
            pane_id: tmux pane id (e.g. ``%0``) **or** zmx session name.
                     When None the tmux/zmx backends are skipped.

        Returns:
            A :class:`CaptureResult` with ``backend`` indicating which path
            was used.

        # @trace FR-SES-001, FR-SES-003
        """
        # 1. tmux
        if pane_id:
            result = _capture_via_tmux(pane_id, n)
            if result is not None:
                return result

        # 2. zmx
        if pane_id:
            result = _capture_via_zmx(pane_id, n)
            if result is not None:
                return result

        # 3. termitty -- feed bytes from current tty if readable
        tty_bytes = self._read_current_tty_bytes()
        if tty_bytes:
            result = _capture_via_termitty(tty_bytes, n)
            if result is not None:
                return result

        # 4. none
        logger.debug("All terminal capture backends failed; returning empty result")
        return CaptureResult(lines=[], backend="none", pane_id=pane_id)

    def capture_by_pid(self, pid: int, n: int = 50) -> CaptureResult:
        """Capture the last *n* lines of output from process *pid*.

        Backend selection order:
        1. /proc/{pid}/fd/1 -- Linux only
        2. termitty          -- feed any bytes obtained from other sources
        3. none              -- empty fallback

        Args:
            pid: Target process ID.
            n:   Number of lines to capture (default 50).

        Returns:
            A :class:`CaptureResult` with ``backend`` indicating which path
            was used and ``pane_id`` set to ``str(pid)``.

        # @trace FR-SES-001, FR-SES-003
        """
        # 1. /proc fd
        result = _capture_via_proc(pid, n)
        if result is not None:
            return result

        # 2. termitty with whatever bytes we can read from /proc
        raw = self._read_proc_bytes(pid)
        if raw:
            result = _capture_via_termitty(raw, n)
            if result is not None:
                result.pane_id = str(pid)
                return result

        # 3. none
        logger.debug("capture_by_pid(%d): all backends failed", pid)
        return CaptureResult(lines=[], backend="none", pane_id=str(pid))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _read_current_tty_bytes() -> bytes:
        """Try to read bytes from the current process's controlling tty.

        Returns empty bytes on any failure (no tty, permission error, etc.).
        """
        try:
            tty_dev = os.ttyname(1)  # fd 1 = stdout
            with open(tty_dev, "rb") as fh:
                return fh.read(65536)
        except OSError:
            return b""

    @staticmethod
    def _read_proc_bytes(pid: int) -> bytes:
        """Try to read bytes from /proc/{pid}/fd/1 (Linux only).

        Returns empty bytes on any failure.
        """
        if platform.system() != "Linux":
            return b""
        try:
            with open(f"/proc/{pid}/fd/1", "rb") as fh:
                return fh.read(1024 * 1024)
        except OSError:
            return b""
