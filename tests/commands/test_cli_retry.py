"""Tests for tenacity-based EAGAIN retry in cli_impl.py.

Verifies:
- _retry_if_eagain predicate returns True only for EAGAIN/EWOULDBLOCK
- _spawn_with_eagain_retry retries up to 5 attempts on EAGAIN then re-raises
- _spawn_with_eagain_retry succeeds on transient EAGAIN (passes after N failures)
- _spawn_with_eagain_retry does NOT retry on other OSErrors (e.g. ENOENT)
- _backoff_delay returns values in expected range for various attempt numbers

# @trace FR-CLI-001
"""

from __future__ import annotations

import errno
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from thegent.cli.commands.impl import (
    _EAGAIN_ERRNOS,
    _backoff_delay,
    _retry_if_eagain,
    _spawn_with_eagain_retry,
)

# ---------------------------------------------------------------------------
# _retry_if_eagain predicate
# ---------------------------------------------------------------------------


class TestRetryIfEagain:
    """Unit tests for the EAGAIN retry predicate."""

    def test_returns_true_for_eagain(self) -> None:
        exc = OSError(errno.EAGAIN, "Resource temporarily unavailable")
        assert _retry_if_eagain(exc) is True

    def test_returns_true_for_ewouldblock(self) -> None:
        exc = OSError(errno.EWOULDBLOCK, "Resource temporarily unavailable")
        assert _retry_if_eagain(exc) is True

    def test_returns_false_for_enoent(self) -> None:
        exc = OSError(errno.ENOENT, "No such file or directory")
        assert _retry_if_eagain(exc) is False

    def test_returns_false_for_eperm(self) -> None:
        exc = OSError(errno.EPERM, "Operation not permitted")
        assert _retry_if_eagain(exc) is False

    def test_returns_false_for_non_oserror(self) -> None:
        assert _retry_if_eagain(ValueError("bad")) is False
        assert _retry_if_eagain(RuntimeError("oops")) is False

    def test_eagain_errnos_set_contains_both(self) -> None:
        assert errno.EAGAIN in _EAGAIN_ERRNOS
        assert errno.EWOULDBLOCK in _EAGAIN_ERRNOS


# ---------------------------------------------------------------------------
# _spawn_with_eagain_retry behaviour
# ---------------------------------------------------------------------------


class TestSpawnWithEagainRetry:
    """Integration-style unit tests for the tenacity-decorated spawn wrapper."""

    def _make_popen_args(self) -> dict:
        """Return minimal keyword args for _spawn_with_eagain_retry."""
        return {
            "cwd": "/tmp",
            "env": {"PATH": "/usr/bin"},
            "stdin": subprocess.DEVNULL,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
        }

    def test_succeeds_on_first_attempt(self) -> None:
        mock_proc = MagicMock(spec=subprocess.Popen)
        with patch(
            "thegent.cli.commands.impl.subprocess.Popen", return_value=mock_proc
        ) as mock_popen:
            result = _spawn_with_eagain_retry(
                ["echo", "hello"], **self._make_popen_args()
            )

        assert result is mock_proc
        assert mock_popen.call_count == 1

    def test_retries_on_eagain_then_succeeds(self) -> None:
        """Fails twice with EAGAIN, succeeds on third attempt."""
        eagain_exc = OSError(errno.EAGAIN, "try again")
        mock_proc = MagicMock(spec=subprocess.Popen)

        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise eagain_exc
            return mock_proc

        with patch(
            "thegent.cli.commands.impl.subprocess.Popen", side_effect=side_effect
        ):
            result = _spawn_with_eagain_retry(["echo"], **self._make_popen_args())

        assert result is mock_proc
        assert call_count == 3

    def test_reraises_after_max_attempts(self) -> None:
        """After 5 EAGAIN failures tenacity should re-raise the OSError."""
        eagain_exc = OSError(errno.EAGAIN, "always busy")

        with patch(
            "thegent.cli.commands.impl.subprocess.Popen", side_effect=eagain_exc
        ):
            with pytest.raises(OSError) as exc_info:
                _spawn_with_eagain_retry(["echo"], **self._make_popen_args())

        assert exc_info.value.errno == errno.EAGAIN

    def test_does_not_retry_on_enoent(self) -> None:
        """Non-EAGAIN OSError must propagate immediately (no retry)."""
        enoent_exc = OSError(errno.ENOENT, "no such file")

        with patch(
            "thegent.cli.commands.impl.subprocess.Popen", side_effect=enoent_exc
        ) as mock_popen:
            with pytest.raises(OSError) as exc_info:
                _spawn_with_eagain_retry(["bad-cmd"], **self._make_popen_args())

        # tenacity should NOT have retried — only one Popen call
        assert mock_popen.call_count == 1
        assert exc_info.value.errno == errno.ENOENT

    def test_does_not_retry_on_value_error(self) -> None:
        """Non-OSError exceptions must propagate immediately."""
        with patch(
            "thegent.cli.commands.impl.subprocess.Popen",
            side_effect=ValueError("bad args"),
        ) as mock_popen:
            with pytest.raises(ValueError):
                _spawn_with_eagain_retry(["echo"], **self._make_popen_args())

        assert mock_popen.call_count == 1

    def test_call_uses_start_new_session(self) -> None:
        """Verify start_new_session=True is always passed to Popen."""
        mock_proc = MagicMock(spec=subprocess.Popen)
        with patch(
            "thegent.cli.commands.impl.subprocess.Popen", return_value=mock_proc
        ) as mock_popen:
            _spawn_with_eagain_retry(["echo"], **self._make_popen_args())

        _, kwargs = mock_popen.call_args
        assert kwargs.get("start_new_session") is True


# ---------------------------------------------------------------------------
# _backoff_delay helper
# ---------------------------------------------------------------------------


class TestBackoffDelay:
    """Tests for the DAG retry backoff helper."""

    def test_returns_float(self) -> None:
        result = _backoff_delay(0)
        assert isinstance(result, float)

    def test_zero_attempt_range(self) -> None:
        # attempt=0 → max is min(2**0, 60) = 1.0 → delay in [0, 1]
        for _ in range(50):
            d = _backoff_delay(0)
            assert 0 <= d <= 1.0, f"delay {d} out of range for attempt=0"

    def test_high_attempt_capped_at_max_delay(self) -> None:
        # attempt=10 → 2**10=1024 > 60 → capped at 60
        for _ in range(50):
            d = _backoff_delay(10)
            assert 0 <= d <= 60.0, f"delay {d} exceeds max_delay for attempt=10"

    def test_custom_max_delay(self) -> None:
        for _ in range(50):
            d = _backoff_delay(5, max_delay=10.0)
            assert 0 <= d <= 10.0, f"delay {d} exceeds custom max_delay=10"

    def test_delay_increases_on_average_with_attempt(self) -> None:
        """Higher attempt values should yield higher average delays."""
        samples_low = [_backoff_delay(0) for _ in range(200)]
        samples_high = [_backoff_delay(3) for _ in range(200)]
        avg_low = sum(samples_low) / len(samples_low)
        avg_high = sum(samples_high) / len(samples_high)
        # avg for attempt=3 should be ~ 4x higher than attempt=0
        assert avg_high > avg_low, "Higher attempt should yield higher average delay"
