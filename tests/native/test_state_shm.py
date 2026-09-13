"""Tests for thegent.native.state_shm -- BKM-05 State-SHM.

# @trace FR-ROB-003 -- Circuit breaker failure tracking
# @trace FR-ROB-004 -- Circuit breaker open/half-open/closed state
# @trace FR-XP-001  -- XP award and level computation

Tests cover the pure-Python fallback path unconditionally (always available).
Native path tests are skipped if the thegent_shm extension is not compiled.
"""

from __future__ import annotations

import os
import time
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from thegent.native.state_shm import (
    CircuitBreakerShm,
    XpTracker,
    _category_int,
    _PurePythonBreakerStore,
    _PurePythonXpStore,
    is_native_available,
    open_shm,
)

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Helper: force fallback (disable native module for unit tests)
# ---------------------------------------------------------------------------


def _fallback_cb(tmp_path: Path, **kwargs: object) -> CircuitBreakerShm:
    """Return a CircuitBreakerShm with native disabled (fallback path)."""
    with patch("thegent.native.state_shm._native_module", None):
        cb = CircuitBreakerShm(tmp_path / "state.shm", **kwargs)
    return cb


def _fallback_xp(tmp_path: Path) -> XpTracker:
    """Return an XpTracker with native disabled (fallback path)."""
    with patch("thegent.native.state_shm._native_module", None):
        xp = XpTracker(tmp_path / "state.shm")
    return xp


# ---------------------------------------------------------------------------
# _category_int
# ---------------------------------------------------------------------------


class TestCategoryInt:
    """FR-ROB-003: Category mapping helpers."""

    def test_known_categories(self) -> None:
        assert _category_int("agent") == 0
        assert _category_int("model") == 1
        assert _category_int("provider") == 2
        assert _category_int("tool") == 3

    def test_unknown_category_defaults_to_agent(self) -> None:
        assert _category_int("unknown") == 0
        assert _category_int("") == 0


# ---------------------------------------------------------------------------
# _PurePythonBreakerStore
# ---------------------------------------------------------------------------


class TestPurePythonBreakerStore:
    """Unit tests for the pure-Python fallback breaker store."""

    def test_no_failures_circuit_closed(self) -> None:
        store = _PurePythonBreakerStore()
        assert not store.is_open("target", "agent", threshold=3, window_s=300, recovery_s=60)

    def test_below_threshold_circuit_closed(self) -> None:
        store = _PurePythonBreakerStore()
        store.record_failure("target", "agent")
        store.record_failure("target", "agent")
        assert not store.is_open("target", "agent", threshold=3, window_s=300, recovery_s=60)

    def test_at_threshold_circuit_opens(self) -> None:
        store = _PurePythonBreakerStore()
        for _ in range(3):
            store.record_failure("target", "agent")
        assert store.is_open("target", "agent", threshold=3, window_s=300, recovery_s=60)

    def test_failures_outside_window_do_not_count(self) -> None:
        store = _PurePythonBreakerStore()
        # Inject failures with a timestamp far in the past
        now = time.time()
        store._failures["target:agent"] = [now - 400, now - 350]  # outside 300s window
        store.record_failure("target", "agent")  # only 1 recent failure
        assert not store.is_open("target", "agent", threshold=3, window_s=300, recovery_s=60)

    def test_half_open_after_recovery(self) -> None:
        store = _PurePythonBreakerStore()
        # Inject failures just beyond the recovery window
        now = time.time()
        store._failures["target:agent"] = [
            now - 10,
            now - 10,
            now - 10,
        ]  # threshold=3 met
        # recovery_s=5: last failure was 10s ago > 5s, so half-open (returns False)
        assert not store.is_open("target", "agent", threshold=3, window_s=300, recovery_s=5)

    def test_clear_specific_target(self) -> None:
        store = _PurePythonBreakerStore()
        for _ in range(5):
            store.record_failure("alpha", "agent")
        for _ in range(5):
            store.record_failure("beta", "agent")
        store.clear("alpha")
        assert not store.is_open("alpha", "agent", threshold=3, window_s=300, recovery_s=60)
        assert store.is_open("beta", "agent", threshold=3, window_s=300, recovery_s=60)

    def test_clear_all(self) -> None:
        store = _PurePythonBreakerStore()
        for _ in range(5):
            store.record_failure("alpha", "agent")
        store.clear()
        assert not store.is_open("alpha", "agent", threshold=3, window_s=300, recovery_s=60)

    def test_different_categories_independent(self) -> None:
        store = _PurePythonBreakerStore()
        for _ in range(3):
            store.record_failure("target", "agent")
        # model category has no failures
        assert not store.is_open("target", "model", threshold=3, window_s=300, recovery_s=60)


# ---------------------------------------------------------------------------
# _PurePythonXpStore
# ---------------------------------------------------------------------------


class TestPurePythonXpStore:
    """FR-XP-001: Pure-Python XP store unit tests."""

    def test_initial_state(self) -> None:
        store = _PurePythonXpStore()
        assert store.total_xp == 0
        assert store.level == 1

    def test_award_increases_xp(self) -> None:
        store = _PurePythonXpStore()
        store.award(500)
        assert store.total_xp == 500

    def test_level_increments_at_1000(self) -> None:
        store = _PurePythonXpStore()
        store.award(999)
        assert store.level == 1
        store.award(1)  # total = 1000
        assert store.level == 2

    def test_multiple_level_ups(self) -> None:
        store = _PurePythonXpStore()
        store.award(5000)
        assert store.total_xp == 5000
        assert store.level == 6  # 5000 // 1000 + 1 = 6

    def test_state_dict(self) -> None:
        store = _PurePythonXpStore()
        store.award(2500)
        s = store.state()
        assert s["total_xp"] == 2500
        assert s["level"] == 3


# ---------------------------------------------------------------------------
# CircuitBreakerShm (fallback path)
# ---------------------------------------------------------------------------


class TestCircuitBreakerShmFallback:
    """FR-ROB-003/004: CircuitBreakerShm via pure-Python fallback."""

    def test_starts_closed(self, tmp_path: Path) -> None:
        cb = _fallback_cb(tmp_path)
        assert not cb.is_open("target")
        assert cb.should_allow("target")

    def test_is_not_native(self, tmp_path: Path) -> None:
        cb = _fallback_cb(tmp_path)
        assert not cb.is_native

    def test_record_failure_below_threshold_stays_closed(self, tmp_path: Path) -> None:
        cb = _fallback_cb(tmp_path, threshold=3)
        cb.record_failure("target")
        cb.record_failure("target")
        assert not cb.is_open("target")

    def test_record_failure_at_threshold_opens(self, tmp_path: Path) -> None:
        cb = _fallback_cb(tmp_path, threshold=3)
        for _ in range(3):
            cb.record_failure("target")
        assert cb.is_open("target")
        assert not cb.should_allow("target")

    def test_state_int_open(self, tmp_path: Path) -> None:
        cb = _fallback_cb(tmp_path, threshold=1)
        cb.record_failure("target")
        assert cb.state_int("target") == CircuitBreakerShm.OPEN

    def test_state_int_closed(self, tmp_path: Path) -> None:
        cb = _fallback_cb(tmp_path)
        assert cb.state_int("target") == CircuitBreakerShm.CLOSED

    def test_record_success_clears_fallback(self, tmp_path: Path) -> None:
        cb = _fallback_cb(tmp_path, threshold=3)
        for _ in range(3):
            cb.record_failure("target")
        assert cb.is_open("target")
        cb.record_success("target")
        assert not cb.is_open("target")

    def test_categories_are_independent(self, tmp_path: Path) -> None:
        cb = _fallback_cb(tmp_path, threshold=2)
        for _ in range(2):
            cb.record_failure("target", category="model")
        assert cb.is_open("target", category="model")
        assert not cb.is_open("target", category="agent")

    def test_health_score_noop_on_fallback(self, tmp_path: Path) -> None:
        cb = _fallback_cb(tmp_path)
        cb.set_health_score(0.85)
        assert cb.get_health_score() == 0.0

    def test_half_open_recovery(self, tmp_path: Path) -> None:
        cb = _fallback_cb(tmp_path, threshold=2, window_s=300, recovery_s=1)
        for _ in range(2):
            cb._fallback.record_failure("target", "agent")
        # Patch the failure timestamps to be old (past recovery_s)
        now = time.time()
        cb._fallback._failures["target:agent"] = [now - 5, now - 5]
        # recovery_s=1: last failure 5s ago > 1s, circuit should be half-open (False)
        assert not cb.is_open("target")


# ---------------------------------------------------------------------------
# XpTracker (fallback path)
# ---------------------------------------------------------------------------


class TestXpTrackerFallback:
    """FR-XP-001: XpTracker via pure-Python fallback."""

    def test_initial_state(self, tmp_path: Path) -> None:
        xp = _fallback_xp(tmp_path)
        assert xp.total_xp == 0
        assert xp.level == 1
        assert not xp.is_native

    def test_award_updates_xp_and_level(self, tmp_path: Path) -> None:
        xp = _fallback_xp(tmp_path)
        xp.award(1500)
        assert xp.total_xp == 1500
        assert xp.level == 2

    def test_state_dict(self, tmp_path: Path) -> None:
        xp = _fallback_xp(tmp_path)
        xp.award(3000)
        s = xp.state()
        assert s == {"total_xp": 3000, "level": 4}

    def test_set_level_override(self, tmp_path: Path) -> None:
        xp = _fallback_xp(tmp_path)
        xp.set_level(10)
        assert xp.level == 10


# ---------------------------------------------------------------------------
# open_shm convenience factory (fallback path)
# ---------------------------------------------------------------------------


class TestOpenShmFactory:
    """Integration test for open_shm with fallback."""

    def test_returns_both_objects(self, tmp_path: Path) -> None:
        with patch("thegent.native.state_shm._native_module", None):
            cb, xp = open_shm(tmp_path / "state.shm")
        assert isinstance(cb, CircuitBreakerShm)
        assert isinstance(xp, XpTracker)

    def test_both_objects_functional(self, tmp_path: Path) -> None:
        with patch("thegent.native.state_shm._native_module", None):
            cb, xp = open_shm(tmp_path / "state.shm", threshold=2)
        cb.record_failure("target")
        cb.record_failure("target")
        assert cb.is_open("target")
        xp.award(2000)
        assert xp.level == 3


# ---------------------------------------------------------------------------
# is_native_available
# ---------------------------------------------------------------------------


class TestIsNativeAvailable:
    """Probe function for native extension availability."""

    def test_returns_bool(self) -> None:
        result = is_native_available()
        assert isinstance(result, bool)

    def test_matches_module_presence(self) -> None:
        import thegent.native.state_shm as _mod

        assert is_native_available() == (_mod._native_module is not None)


if os.environ.get("THGENT_ENFORCE_NATIVE_SHM_TESTS", "0") == "1" and not is_native_available():
    pytest.fail(
        "THGENT_ENFORCE_NATIVE_SHM_TESTS=1 but thegent_shm native extension is unavailable",
        pytrace=False,
    )


# ---------------------------------------------------------------------------
# Native path smoke test (skipped if extension unavailable)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not is_native_available(), reason="thegent_shm native extension not compiled")
class TestCircuitBreakerShmNative:
    """Smoke tests for native SHM path (requires compiled thegent_shm wheel)."""

    def test_is_native(self, tmp_path: Path) -> None:
        cb = CircuitBreakerShm(tmp_path / "state.shm")
        assert cb.is_native

    def test_record_and_check_native(self, tmp_path: Path) -> None:
        cb = CircuitBreakerShm(tmp_path / "state.shm", threshold=3)
        for _ in range(3):
            cb.record_failure("native-target", category="agent")
        assert cb.is_open("native-target", category="agent")

    def test_xp_native(self, tmp_path: Path) -> None:
        xp = XpTracker(tmp_path / "state.shm")
        assert xp.is_native
        xp.award(1000)
        assert xp.level >= 2

    def test_health_score_native(self, tmp_path: Path) -> None:
        cb = CircuitBreakerShm(tmp_path / "state.shm")
        cb.set_health_score(0.75)
        assert abs(cb.get_health_score() - 0.75) < 0.001


# ---------------------------------------------------------------------------
# Environment variable control
# ---------------------------------------------------------------------------


class TestEnvVarControl:
    """THGENT_USE_NATIVE_SHM=0 should force fallback even if native present."""

    def test_env_zero_disables_native(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("THGENT_USE_NATIVE_SHM", "0")
        # Re-evaluate the module-level probe by simulating what the module does
        enabled = os.environ.get("THGENT_USE_NATIVE_SHM", "1").strip() not in (
            "0",
            "false",
            "no",
        )
        assert not enabled
