"""Tests for Lane 2 UX polish — spinner throttle, error explanations, ETA bar."""

from __future__ import annotations

import time

import pytest

from thegent.infra.progress import SpinnerThrottle, throttled_spinner
from thegent.ux.explanations import (
    EXPLANATION_MAP,
    explain_exception,
    explain_exit_code,
)
from thegent.ux.kpis.traffic import progress_bar, progress_bar_with_eta

# ---------------------------------------------------------------------------
# SpinnerThrottle
# ---------------------------------------------------------------------------


class TestSpinnerThrottle:
    def test_should_update_returns_true_when_interval_elapsed(self) -> None:
        throttle = SpinnerThrottle(_interval=0.01)
        assert throttle.should_update() is True

    def test_should_update_returns_false_within_min_interval(self) -> None:
        throttle = SpinnerThrottle(_interval=10.0)  # 10 seconds
        assert throttle.should_update() is True
        assert throttle.should_update() is False
        assert throttle.should_update() is False

    def test_should_update_returns_true_after_interval(self) -> None:
        throttle = SpinnerThrottle(_interval=0.01)
        throttle.should_update()  # first call
        time.sleep(0.02)
        assert throttle.should_update() is True

    def test_throttled_spinner_yields_spinner_throttle(self) -> None:
        with throttled_spinner("test", min_interval=0.1) as spin:
            assert isinstance(spin, SpinnerThrottle)
            assert spin._interval == 0.1


# ---------------------------------------------------------------------------
# explain_exit_code
# ---------------------------------------------------------------------------


class TestExplainExitCode:
    @pytest.mark.parametrize(
        ("code", "expected"),
        [
            (0, "success"),
            (1, "general error"),
            (2, "misuse"),
            (3, "policy deny"),
            (4, "replay mismatch"),
            (127, "command not found"),
            (130, "interrupted"),
        ],
    )
    def test_known_exit_codes(self, code: int, expected: str) -> None:
        result = explain_exit_code(code)
        assert expected in result

    def test_unknown_code(self) -> None:
        result = explain_exit_code(99)
        assert "exit code 99" in result

    def test_explanation_map_has_expected_keys(self) -> None:
        assert set(EXPLANATION_MAP.keys()) == {0, 1, 2, 3, 4, 127, 130}


# ---------------------------------------------------------------------------
# explain_exception
# ---------------------------------------------------------------------------


class TestExplainException:
    def test_timeout(self) -> None:
        result = explain_exception(TimeoutError("timed out"))
        assert "timeout" in result

    def test_permission(self) -> None:
        result = explain_exception(PermissionError("access denied"))
        assert "permission denied" in result

    def test_connection(self) -> None:
        result = explain_exception(ConnectionError("reset"))
        assert "connection" in result

    def test_validation(self) -> None:
        result = explain_exception(ValueError("bad input"))
        assert "validation error" in result

    def test_unknown_exception(self) -> None:
        result = explain_exception(RuntimeError("boom"))
        assert "unexpected RuntimeError" in result
        assert "boom" in result

    def test_long_message_truncated(self) -> None:
        long_msg = "x" * 100
        result = explain_exception(RuntimeError(long_msg))
        assert "…" in result


# ---------------------------------------------------------------------------
# progress_bar_with_eta
# ---------------------------------------------------------------------------


class TestProgressBarWithEta:
    def test_done_zero_shows_dash(self) -> None:
        result = progress_bar_with_eta(0, 100, 10.0)
        assert result.endswith("ETA -")

    def test_done_equals_total(self) -> None:
        result = progress_bar_with_eta(100, 100, 10.0)
        assert result.endswith("ETA 0s")

    def test_done_greater_than_total(self) -> None:
        result = progress_bar_with_eta(110, 100, 10.0)
        assert result.endswith("ETA 0s")

    def test_eta_seconds(self) -> None:
        # 50 done, 100 total, 10s elapsed => remaining = (10/50)*50 = 10s
        result = progress_bar_with_eta(50, 100, 10.0)
        assert "ETA 10s" in result

    def test_eta_minutes(self) -> None:
        # 10 done, 100 total, 100s elapsed => remaining = (100/10)*90 = 900s = 15:00
        result = progress_bar_with_eta(10, 100, 100.0)
        assert "ETA 15:00" in result

    def test_bar_format_matches_progress_bar(self) -> None:
        eta_result = progress_bar_with_eta(50, 100, 10.0)
        bar_result = progress_bar(50, 100)
        assert eta_result.startswith(bar_result)
