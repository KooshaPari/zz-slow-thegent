"""Tests for thegent.ux.keepalive — terminal keepalive for long-running tasks.

Covers (FR-UX-KEEPALIVE-*):
- KeepaliveConfig defaults                                   (FR-UX-KEEPALIVE-001)
- KeepaliveConfig custom values                              (FR-UX-KEEPALIVE-002)
- TerminalKeepalive disabled: no output, no thread           (FR-UX-KEEPALIVE-003)
- TerminalKeepalive no-tty: no output                        (FR-UX-KEEPALIVE-004)
- TerminalKeepalive context manager start/stop               (FR-UX-KEEPALIVE-005)
- TerminalKeepalive start() is idempotent                    (FR-UX-KEEPALIVE-006)
- TerminalKeepalive stop() before start() is safe            (FR-UX-KEEPALIVE-007)
- TerminalKeepalive stop() prints trailing newline           (FR-UX-KEEPALIVE-008)
- TerminalKeepalive stop() idempotent (call twice)           (FR-UX-KEEPALIVE-009)
- TerminalKeepalive prints message on tick                   (FR-UX-KEEPALIVE-010)
- TerminalKeepalive newline_every respected                  (FR-UX-KEEPALIVE-011)
- TerminalKeepalive newline_every=0 means no auto newline    (FR-UX-KEEPALIVE-012)
- TerminalKeepalive exception in __exit__ still stops        (FR-UX-KEEPALIVE-013)
- TerminalKeepalive stdout OSError swallowed                 (FR-UX-KEEPALIVE-014)
- keepalive() convenience context manager yields instance    (FR-UX-KEEPALIVE-015)
- keepalive() custom interval_s and message propagated       (FR-UX-KEEPALIVE-016)
- keepalive() no-tty: no output                              (FR-UX-KEEPALIVE-017)
- keepalive() exception inside context stops cleanly         (FR-UX-KEEPALIVE-018)
- TerminalKeepalive _is_tty() returns False on AttributeError (FR-UX-KEEPALIVE-019)
- TerminalKeepalive _is_tty() returns False on OSError       (FR-UX-KEEPALIVE-020)
- TerminalKeepalive multiple ticks respect newline_every     (FR-UX-KEEPALIVE-021)
- TerminalKeepalive disabled=False in KeepaliveConfig        (FR-UX-KEEPALIVE-022)
- TerminalKeepalive thread is daemon thread                  (FR-UX-KEEPALIVE-023)
"""

from __future__ import annotations

import io
import time
from contextlib import contextmanager
from typing import TYPE_CHECKING, cast
from unittest.mock import MagicMock, patch

if TYPE_CHECKING:
    from collections.abc import Generator

import pytest

from thegent.ux.keepalive import KeepaliveConfig, TerminalKeepalive, keepalive

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _TtyStringIO(io.StringIO):
    """StringIO that reports isatty() == True."""

    def isatty(self) -> bool:
        return True


class _NonTtyStringIO(io.StringIO):
    """StringIO that reports isatty() == False."""

    def isatty(self) -> bool:
        return False


@contextmanager
def _tty_stdout(buf: _TtyStringIO) -> Generator[_TtyStringIO]:
    """Patch sys.stdout with a TTY-reporting StringIO."""
    with patch("sys.stdout", buf):
        yield buf


@contextmanager
def _non_tty_stdout(buf: _NonTtyStringIO) -> Generator[_NonTtyStringIO]:
    """Patch sys.stdout with a non-TTY StringIO."""
    with patch("sys.stdout", buf):
        yield buf


def _fast_config(**kwargs: object) -> KeepaliveConfig:
    """KeepaliveConfig with a very short interval for test speed."""
    defaults: dict[str, object] = {
        "interval_s": 0.05,
        "message": ".",
        "newline_every": 10,
        "enabled": True,
    }
    defaults.update(kwargs)
    return KeepaliveConfig(
        interval_s=cast("float", defaults["interval_s"]),
        message=cast("str", defaults["message"]),
        newline_every=cast("int", defaults["newline_every"]),
        enabled=cast("bool", defaults["enabled"]),
    )


# ---------------------------------------------------------------------------
# FR-UX-KEEPALIVE-001: KeepaliveConfig defaults
# ---------------------------------------------------------------------------


def test_keepalive_config_defaults():
    """@trace FR-UX-KEEPALIVE-001"""
    cfg = KeepaliveConfig()
    assert cfg.interval_s == 30.0
    assert cfg.message == "."
    assert cfg.newline_every == 10
    assert cfg.enabled is True


# ---------------------------------------------------------------------------
# FR-UX-KEEPALIVE-002: KeepaliveConfig custom values
# ---------------------------------------------------------------------------


def test_keepalive_config_custom():
    """@trace FR-UX-KEEPALIVE-002"""
    cfg = KeepaliveConfig(interval_s=5.0, message="*", newline_every=3, enabled=False)
    assert cfg.interval_s == 5.0
    assert cfg.message == "*"
    assert cfg.newline_every == 3
    assert cfg.enabled is False


# ---------------------------------------------------------------------------
# FR-UX-KEEPALIVE-003: disabled mode — no output, no thread
# ---------------------------------------------------------------------------


def test_disabled_no_thread_no_output():
    """@trace FR-UX-KEEPALIVE-003"""
    buf = _TtyStringIO()
    with _tty_stdout(buf):
        cfg = _fast_config(enabled=False)
        ka = TerminalKeepalive(cfg)
        ka.start()
        assert ka._thread is None
        ka.stop()
    assert buf.getvalue() == ""


# ---------------------------------------------------------------------------
# FR-UX-KEEPALIVE-004: non-tty stdout — no output
# ---------------------------------------------------------------------------


def test_non_tty_no_output():
    """@trace FR-UX-KEEPALIVE-004"""
    buf = _NonTtyStringIO()
    with _non_tty_stdout(buf):
        cfg = _fast_config()
        ka = TerminalKeepalive(cfg)
        ka.start()
        assert ka._thread is None
        ka.stop()
    assert buf.getvalue() == ""


# ---------------------------------------------------------------------------
# FR-UX-KEEPALIVE-005: context manager start / stop
# ---------------------------------------------------------------------------


def test_context_manager_starts_and_stops():
    """@trace FR-UX-KEEPALIVE-005"""
    buf = _TtyStringIO()
    captured_thread = None
    with _tty_stdout(buf):
        cfg = _fast_config(interval_s=10.0)  # long interval so no tick fires
        with TerminalKeepalive(cfg) as ka:
            assert ka._thread is not None
            assert ka._thread.is_alive()
            # Capture the thread reference *before* __exit__ so the
            # post-exit assertion can verify the stop() contract
            # without dereferencing the attribute that __exit__ sets
            # to None (FR-UX-KEEPALIVE-009: stop() idempotent).
            captured_thread = ka._thread
    # After __exit__ thread must be stopped.
    assert captured_thread is not None
    assert not captured_thread.is_alive()


# ---------------------------------------------------------------------------
# FR-UX-KEEPALIVE-006: start() is idempotent
# ---------------------------------------------------------------------------


def test_start_idempotent():
    """@trace FR-UX-KEEPALIVE-006"""
    buf = _TtyStringIO()
    with _tty_stdout(buf):
        cfg = _fast_config(interval_s=10.0)
        ka = TerminalKeepalive(cfg)
        ka.start()
        thread_first = ka._thread
        ka.start()  # second call must not create a new thread
        assert ka._thread is thread_first
        ka.stop()


# ---------------------------------------------------------------------------
# FR-UX-KEEPALIVE-007: stop() before start() is safe
# ---------------------------------------------------------------------------


def test_stop_before_start_is_safe():
    """@trace FR-UX-KEEPALIVE-007"""
    cfg = _fast_config()
    ka = TerminalKeepalive(cfg)
    # Should not raise even though no thread was ever started
    ka.stop()


# ---------------------------------------------------------------------------
# FR-UX-KEEPALIVE-008: stop() prints trailing newline after ticks occurred
# ---------------------------------------------------------------------------


def test_stop_prints_trailing_newline_after_tick():
    """@trace FR-UX-KEEPALIVE-008"""
    buf = _TtyStringIO()
    with _tty_stdout(buf):
        cfg = _fast_config(interval_s=0.01, newline_every=100)
        with TerminalKeepalive(cfg):
            # Sleep long enough for at least one tick to fire reliably
            # on loaded CI workers (interval_s=0.01 → ~10 ticks in 0.1s).
            time.sleep(0.1)
    output = buf.getvalue()
    # At least one "." must have been printed, and output must end with "\n"
    assert "." in output
    assert output.endswith("\n")


# ---------------------------------------------------------------------------
# FR-UX-KEEPALIVE-009: stop() is idempotent (call twice)
# ---------------------------------------------------------------------------


def test_stop_idempotent():
    """@trace FR-UX-KEEPALIVE-009"""
    buf = _TtyStringIO()
    with _tty_stdout(buf):
        cfg = _fast_config(interval_s=10.0)
        ka = TerminalKeepalive(cfg)
        ka.start()
        ka.stop()
        ka.stop()  # second stop must not raise


# ---------------------------------------------------------------------------
# FR-UX-KEEPALIVE-010: message printed on each tick
# ---------------------------------------------------------------------------


def test_message_printed_on_tick():
    """@trace FR-UX-KEEPALIVE-010"""
    buf = _TtyStringIO()
    with _tty_stdout(buf):
        cfg = _fast_config(interval_s=0.02, message="X", newline_every=100)
        with TerminalKeepalive(cfg):
            # Sleep long enough for at least one tick to fire reliably
            # on loaded CI workers (interval_s=0.02 → ~5 ticks in 0.1s).
            time.sleep(0.1)
    output = buf.getvalue()
    assert "X" in output


# ---------------------------------------------------------------------------
# FR-UX-KEEPALIVE-011: newline_every respected
# ---------------------------------------------------------------------------


def test_newline_every_respected():
    """@trace FR-UX-KEEPALIVE-011"""
    buf = _TtyStringIO()
    with _tty_stdout(buf):
        cfg = _fast_config(interval_s=0.01, message=".", newline_every=3)
        with TerminalKeepalive(cfg):
            # Sleep well above (newline_every * interval_s) so the tick
            # count is deterministic on loaded CI workers (0.5s allows
            # ~50 ticks at 0.01s — comfortably exceeding the 3-tick
            # embedded-newline threshold even with scheduler jitter).
            time.sleep(0.5)
    output = buf.getvalue()
    # With newline_every=3 there should be at least one embedded newline
    # (plus the trailing newline from stop())
    assert output.count("\n") >= 2


# ---------------------------------------------------------------------------
# FR-UX-KEEPALIVE-012: newline_every=0 means no auto newline (only trailing)
# ---------------------------------------------------------------------------


def test_newline_every_zero_no_auto_newline():
    """@trace FR-UX-KEEPALIVE-012"""
    buf = _TtyStringIO()
    with _tty_stdout(buf):
        cfg = _fast_config(interval_s=0.01, message=".", newline_every=0)
        with TerminalKeepalive(cfg):
            # Sleep long enough for multiple ticks to fire reliably on
            # loaded CI workers (interval_s=0.01 → ~30 ticks in 0.3s).
            time.sleep(0.3)
    output = buf.getvalue()
    # Exactly one newline (the trailing one from stop())
    assert output.count("\n") == 1


# ---------------------------------------------------------------------------
# FR-UX-KEEPALIVE-013: exception inside __exit__ still stops thread
# ---------------------------------------------------------------------------


def test_exception_inside_context_stops_thread():
    """@trace FR-UX-KEEPALIVE-013"""
    buf = _TtyStringIO()
    with _tty_stdout(buf):
        cfg = _fast_config(interval_s=10.0)
        ka = TerminalKeepalive(cfg)
        with pytest.raises(RuntimeError, match="intentional"), ka:
            raise RuntimeError("intentional")
    # Thread must be stopped despite the exception
    assert ka._thread is None or not ka._thread.is_alive()


# ---------------------------------------------------------------------------
# FR-UX-KEEPALIVE-014: stdout OSError swallowed (no crash)
# ---------------------------------------------------------------------------


def test_stdout_oserror_swallowed():
    """@trace FR-UX-KEEPALIVE-014"""
    broken = MagicMock()
    broken.isatty.return_value = True
    broken.write.side_effect = OSError("broken pipe")

    with patch("sys.stdout", broken):
        cfg = _fast_config(interval_s=0.02)
        with TerminalKeepalive(cfg):
            # Sleep long enough for at least one tick to fire reliably
            # on loaded CI workers (interval_s=0.02 → ~5 ticks in 0.1s).
            time.sleep(0.1)
    # No exception propagated; test passes if we reach here.


# ---------------------------------------------------------------------------
# FR-UX-KEEPALIVE-015: keepalive() context manager yields instance
# ---------------------------------------------------------------------------


def test_keepalive_cm_yields_instance():
    """@trace FR-UX-KEEPALIVE-015"""
    buf = _TtyStringIO()
    with _tty_stdout(buf), keepalive(interval_s=10.0, message=".") as ka:
        assert isinstance(ka, TerminalKeepalive)


# ---------------------------------------------------------------------------
# FR-UX-KEEPALIVE-016: keepalive() propagates interval_s and message
# ---------------------------------------------------------------------------


def test_keepalive_cm_propagates_config():
    """@trace FR-UX-KEEPALIVE-016"""
    buf = _TtyStringIO()
    with _tty_stdout(buf), keepalive(interval_s=7.5, message="~") as ka:
        assert ka._config.interval_s == 7.5
        assert ka._config.message == "~"


# ---------------------------------------------------------------------------
# FR-UX-KEEPALIVE-017: keepalive() no-tty — no output
# ---------------------------------------------------------------------------


def test_keepalive_cm_no_tty_no_output():
    """@trace FR-UX-KEEPALIVE-017"""
    buf = _NonTtyStringIO()
    with _non_tty_stdout(buf), keepalive(interval_s=0.01) as ka:
        time.sleep(0.1)
    assert buf.getvalue() == ""
    assert ka._thread is None


# ---------------------------------------------------------------------------
# FR-UX-KEEPALIVE-018: keepalive() exception inside context stops cleanly
# ---------------------------------------------------------------------------


def test_keepalive_cm_exception_stops_cleanly():
    """@trace FR-UX-KEEPALIVE-018"""
    buf = _TtyStringIO()
    with _tty_stdout(buf), pytest.raises(ValueError, match="boom"):
        with keepalive(interval_s=10.0) as ka:
            raise ValueError("boom")
    assert ka._thread is None or not ka._thread.is_alive()


# ---------------------------------------------------------------------------
# FR-UX-KEEPALIVE-019: _is_tty() returns False on AttributeError
# ---------------------------------------------------------------------------


def test_is_tty_attribute_error():
    """@trace FR-UX-KEEPALIVE-019"""
    mock_stdout = MagicMock()
    mock_stdout.isatty.side_effect = AttributeError("no isatty")
    with patch("sys.stdout", mock_stdout):
        assert TerminalKeepalive._is_tty() is False


# ---------------------------------------------------------------------------
# FR-UX-KEEPALIVE-020: _is_tty() returns False on OSError
# ---------------------------------------------------------------------------


def test_is_tty_oserror():
    """@trace FR-UX-KEEPALIVE-020"""
    mock_stdout = MagicMock()
    mock_stdout.isatty.side_effect = OSError("io error")
    with patch("sys.stdout", mock_stdout):
        assert TerminalKeepalive._is_tty() is False


# ---------------------------------------------------------------------------
# FR-UX-KEEPALIVE-021: multiple ticks respect newline_every boundary
# ---------------------------------------------------------------------------


def test_multiple_ticks_newline_boundary():
    """@trace FR-UX-KEEPALIVE-021"""
    buf = _TtyStringIO()
    with _tty_stdout(buf):
        cfg = _fast_config(interval_s=0.01, message=".", newline_every=2)
        with TerminalKeepalive(cfg):
            # Sleep well above (newline_every * interval_s) so the tick
            # count is deterministic on loaded CI workers (~0.5s allows
            # for ~50 ticks at 0.01s, comfortably exceeding the 3-newline
            # threshold even with thread-scheduling jitter).
            time.sleep(0.5)
    output = buf.getvalue()
    # With newline_every=2, every 2nd dot triggers a newline.
    # With >=25 ticks + trailing newline we expect >= 3 newlines.
    assert output.count("\n") >= 3


# ---------------------------------------------------------------------------
# FR-UX-KEEPALIVE-022: KeepaliveConfig enabled=False propagates to class
# ---------------------------------------------------------------------------


def test_disabled_config_propagates():
    """@trace FR-UX-KEEPALIVE-022"""
    buf = _TtyStringIO()
    with _tty_stdout(buf):
        cfg = KeepaliveConfig(interval_s=0.01, enabled=False)
        with TerminalKeepalive(cfg) as ka:
            time.sleep(0.1)
    assert buf.getvalue() == ""
    assert ka._thread is None


# ---------------------------------------------------------------------------
# FR-UX-KEEPALIVE-023: background thread is a daemon thread
# ---------------------------------------------------------------------------


def test_thread_is_daemon():
    """@trace FR-UX-KEEPALIVE-023"""
    buf = _TtyStringIO()
    with _tty_stdout(buf):
        cfg = _fast_config(interval_s=10.0)
        ka = TerminalKeepalive(cfg)
        ka.start()
        assert ka._thread is not None
        assert ka._thread.daemon is True
        ka.stop()
