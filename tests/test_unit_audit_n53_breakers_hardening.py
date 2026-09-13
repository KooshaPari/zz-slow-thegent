"""AUDIT-N+53: governance/breakers hardening spec (SOTA pass-37).

15 invariants FR-GOV-CB-001..015 covering CircuitBreaker init,
threshold guard, check_spike, trip, is_tripped, reset, corrupt-line
resilience, path absolute guard, and canonical ``__all__``.

Source: src/thegent/governance/breakers.py

@trace AUDIT-N+53  FR-GOV-CB-001..015
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from thegent.governance import breakers as _mod
from thegent.governance.breakers import CircuitBreaker

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# FR-GOV-CB-001 -- CircuitBreaker is constructible with session_dir
# ---------------------------------------------------------------------------


class TestCBInit:
    """FR-GOV-CB-001: ``CircuitBreaker(session_dir)`` stores paths."""

    def test_init_sets_session_dir(self, tmp_path: Path) -> None:
        cb = CircuitBreaker(tmp_path)
        assert cb.session_dir == tmp_path

    def test_init_sets_breaker_file(self, tmp_path: Path) -> None:
        cb = CircuitBreaker(tmp_path)
        assert cb.breaker_file == tmp_path / "circuit_breakers.jsonl"

    def test_default_threshold_is_one_usd(self, tmp_path: Path) -> None:
        cb = CircuitBreaker(tmp_path)
        assert cb.threshold_usd_per_min == 1.0


# ---------------------------------------------------------------------------
# FR-GOV-CB-002 -- absolute session_dir required
# ---------------------------------------------------------------------------


class TestCBPathGuard:
    """FR-GOV-CB-002: ``session_dir`` must be absolute."""

    def test_rejects_relative_path(self) -> None:
        with pytest.raises(ValueError, match="absolute"):
            CircuitBreaker(Path("relative/session"))

    def test_accepts_absolute_path(self, tmp_path: Path) -> None:
        cb = CircuitBreaker(tmp_path)
        assert cb.session_dir.is_absolute()


# ---------------------------------------------------------------------------
# FR-GOV-CB-003 -- threshold must be > 0
# ---------------------------------------------------------------------------


class TestCBThresholdGuard:
    """FR-GOV-CB-003: non-positive thresholds raise ``ValueError``."""

    def test_rejects_zero_threshold(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="threshold"):
            CircuitBreaker(tmp_path, threshold_usd_per_min=0.0)

    def test_rejects_negative_threshold(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="threshold"):
            CircuitBreaker(tmp_path, threshold_usd_per_min=-1.0)

    def test_accepts_custom_positive_threshold(self, tmp_path: Path) -> None:
        cb = CircuitBreaker(tmp_path, threshold_usd_per_min=2.5)
        assert cb.threshold_usd_per_min == 2.5


# ---------------------------------------------------------------------------
# FR-GOV-CB-004 / FR-GOV-CB-005 -- check_spike
# ---------------------------------------------------------------------------


class TestCBCheckSpike:
    """FR-GOV-CB-004/005: ``check_spike`` trips when cost exceeds threshold."""

    def test_below_threshold_returns_false(self, tmp_path: Path) -> None:
        cb = CircuitBreaker(tmp_path, threshold_usd_per_min=1.0)
        assert cb.check_spike(0.5) is False
        assert cb.is_tripped() is False

    def test_above_threshold_returns_true_and_trips(self, tmp_path: Path) -> None:
        cb = CircuitBreaker(tmp_path, threshold_usd_per_min=1.0)
        assert cb.check_spike(1.5) is True
        assert cb.is_tripped() is True

    def test_exact_threshold_does_not_trip(self, tmp_path: Path) -> None:
        """Strict ``>`` so equality is not a spike."""
        cb = CircuitBreaker(tmp_path, threshold_usd_per_min=1.0)
        assert cb.check_spike(1.0) is False
        assert cb.is_tripped() is False


# ---------------------------------------------------------------------------
# FR-GOV-CB-006 / FR-GOV-CB-007 -- trip persists JSONL event
# ---------------------------------------------------------------------------


class TestCBTrip:
    """FR-GOV-CB-006/007: ``trip`` appends a JSONL event with reason/value."""

    def test_trip_creates_breaker_file(self, tmp_path: Path) -> None:
        cb = CircuitBreaker(tmp_path)
        cb.trip("manual trip", 9.9)
        assert cb.breaker_file.exists()

    def test_trip_event_fields(self, tmp_path: Path) -> None:
        cb = CircuitBreaker(tmp_path)
        cb.trip("manual trip", 9.9)
        event = json.loads(cb.breaker_file.read_text(encoding="utf-8").splitlines()[-1])
        assert event["event"] == "tripped"
        assert event["reason"] == "manual trip"
        assert event["value"] == 9.9
        assert "timestamp" in event

    def test_trip_creates_session_dir(self, tmp_path: Path) -> None:
        session = tmp_path / "nested" / "session"
        cb = CircuitBreaker(session)
        cb.trip("boot", 1.1)
        assert session.is_dir()


# ---------------------------------------------------------------------------
# FR-GOV-CB-008 / FR-GOV-CB-009 -- is_tripped
# ---------------------------------------------------------------------------


class TestCBIsTripped:
    """FR-GOV-CB-008/009: ``is_tripped`` reads the last JSONL event."""

    def test_false_when_no_file(self, tmp_path: Path) -> None:
        cb = CircuitBreaker(tmp_path)
        assert cb.is_tripped() is False

    def test_false_when_empty_file(self, tmp_path: Path) -> None:
        cb = CircuitBreaker(tmp_path)
        cb.breaker_file.write_text("", encoding="utf-8")
        assert cb.is_tripped() is False

    def test_true_after_trip(self, tmp_path: Path) -> None:
        cb = CircuitBreaker(tmp_path)
        cb.trip("x", 1.0)
        assert cb.is_tripped() is True


# ---------------------------------------------------------------------------
# FR-GOV-CB-010 -- corrupt-line resilience
# ---------------------------------------------------------------------------


class TestCBCorruptResilience:
    """FR-GOV-CB-010: corrupt trailing JSONL lines do not crash ``is_tripped``."""

    def test_corrupt_last_line_returns_false(self, tmp_path: Path) -> None:
        cb = CircuitBreaker(tmp_path)
        cb.breaker_file.write_text("{not-json\n", encoding="utf-8")
        assert cb.is_tripped() is False

    def test_skips_corrupt_middle_keeps_last_valid(self, tmp_path: Path) -> None:
        cb = CircuitBreaker(tmp_path)
        good = json.dumps({"event": "tripped", "reason": "ok", "value": 1.0, "timestamp": "t"})
        cb.breaker_file.write_text(f"{{bad\n{good}\n", encoding="utf-8")
        assert cb.is_tripped() is True


# ---------------------------------------------------------------------------
# FR-GOV-CB-011 / FR-GOV-CB-012 -- reset
# ---------------------------------------------------------------------------


class TestCBReset:
    """FR-GOV-CB-011/012: ``reset`` clears the tripped state."""

    def test_reset_clears_tripped(self, tmp_path: Path) -> None:
        cb = CircuitBreaker(tmp_path)
        cb.trip("x", 1.0)
        assert cb.is_tripped() is True
        cb.reset()
        assert cb.is_tripped() is False

    def test_reset_appends_reset_event(self, tmp_path: Path) -> None:
        cb = CircuitBreaker(tmp_path)
        cb.trip("x", 1.0)
        cb.reset()
        event = json.loads(cb.breaker_file.read_text(encoding="utf-8").splitlines()[-1])
        assert event["event"] == "reset"

    def test_reset_is_noop_when_no_file(self, tmp_path: Path) -> None:
        cb = CircuitBreaker(tmp_path)
        cb.reset()  # must not raise
        assert cb.is_tripped() is False


# ---------------------------------------------------------------------------
# FR-GOV-CB-013 -- last_event helper
# ---------------------------------------------------------------------------


class TestCBLastEvent:
    """FR-GOV-CB-013: ``last_event`` returns the most recent parsed event or None."""

    def test_last_event_none_when_empty(self, tmp_path: Path) -> None:
        cb = CircuitBreaker(tmp_path)
        assert cb.last_event() is None

    def test_last_event_returns_trip(self, tmp_path: Path) -> None:
        cb = CircuitBreaker(tmp_path)
        cb.trip("spike", 3.0)
        ev = cb.last_event()
        assert ev is not None
        assert ev["event"] == "tripped"
        assert ev["reason"] == "spike"


# ---------------------------------------------------------------------------
# FR-GOV-CB-014 / FR-GOV-CB-015 -- __all__ + public surface
# ---------------------------------------------------------------------------


class TestCBAll:
    """FR-GOV-CB-014/015: canonical public surface."""

    def test_all_exposes_circuit_breaker(self) -> None:
        assert "CircuitBreaker" in _mod.__all__

    def test_module_exports_circuit_breaker(self) -> None:
        assert _mod.CircuitBreaker is CircuitBreaker
