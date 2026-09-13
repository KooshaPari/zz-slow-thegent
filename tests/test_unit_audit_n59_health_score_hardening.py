"""AUDIT-N+59: governance/health_score hardening spec (SOTA pass-37).

15 invariants FR-GOV-HS-001..015 covering HealthScoreComputer init,
absolute-path guard, corrupt-JSON guard, score bounds, get_band bands,
compute_with_trend trends, and canonical ``__all__``.

Source: src/thegent/governance/health_score.py

@trace AUDIT-N+59  FR-GOV-HS-001..015
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from thegent.governance import health_score as _mod
from thegent.governance.health_score import (
    HealthBand,
    HealthScoreComputer,
    get_band,
)

pytestmark = pytest.mark.unit

# Minimal valid health-targets fixture for tests.
_VALID_TARGETS: dict = {
    "version": "1.0.0",
    "dimensions": {
        "alpha": {
            "weight": 0.6,
            "target": 100,
            "unit": "percent",
            "direction": "higher_is_better",
        },
        "beta": {
            "weight": 0.4,
            "target": 10,
            "unit": "count",
            "direction": "lower_is_better",
        },
    },
}


def _write_targets(tmp_path: Path, data: dict | str | None = None) -> Path:
    """Write a health-targets.json into *tmp_path* and return its path."""
    p = tmp_path / "health-targets.json"
    if data is None:
        p.write_text(json.dumps(_VALID_TARGETS), encoding="utf-8")
    elif isinstance(data, str):
        p.write_text(data, encoding="utf-8")
    else:
        p.write_text(json.dumps(data), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# FR-GOV-HS-001 -- constructible with absolute path to valid JSON
# ---------------------------------------------------------------------------


class TestHSInit:
    """FR-GOV-HS-001: ``HealthScoreComputer(path)`` loads valid targets."""

    def test_constructs_with_valid_file(self, tmp_path: Path) -> None:
        path = _write_targets(tmp_path)
        computer = HealthScoreComputer(path)
        assert "alpha" in computer._dimensions
        assert "beta" in computer._dimensions


# ---------------------------------------------------------------------------
# FR-GOV-HS-002 -- rejects relative path
# ---------------------------------------------------------------------------


class TestHSPathGuard:
    """FR-GOV-HS-002: ``health_targets_path`` must be absolute."""

    def test_rejects_relative_path(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="absolute"):
            HealthScoreComputer(Path("relative/path/targets.json"))

    def test_accepts_absolute_path(self, tmp_path: Path) -> None:
        path = _write_targets(tmp_path)
        HealthScoreComputer(path)
        assert path.is_absolute()


# ---------------------------------------------------------------------------
# FR-GOV-HS-003 -- rejects non-existent file
# ---------------------------------------------------------------------------


class TestHSFileGuard:
    """FR-GOV-HS-003: non-existent path raises ``FileNotFoundError``."""

    def test_rejects_nonexistent_file(self) -> None:
        with pytest.raises(FileNotFoundError):
            HealthScoreComputer(Path("/tmp/does-not-exist-N59.json"))


# ---------------------------------------------------------------------------
# FR-GOV-HS-004 -- rejects corrupt JSON
# ---------------------------------------------------------------------------


class TestHSCorruptGuard:
    """FR-GOV-HS-004: corrupt JSON raises ``ValueError`` with message."""

    def test_rejects_corrupt_json(self, tmp_path: Path) -> None:
        path = _write_targets(tmp_path, "{not valid json!!!")
        with pytest.raises(ValueError, match=r"corrupt|invalid JSON"):
            HealthScoreComputer(path)

    def test_rejects_empty_file(self, tmp_path: Path) -> None:
        path = _write_targets(tmp_path, "")
        with pytest.raises(ValueError, match=r"corrupt|invalid JSON"):
            HealthScoreComputer(path)


# ---------------------------------------------------------------------------
# FR-GOV-HS-005 -- get_band EXCELLENT for score >= 90
# ---------------------------------------------------------------------------


class TestBandExcellent:
    """FR-GOV-HS-005: ``get_band(>=90)`` returns ``EXCELLENT``."""

    def test_score_90_is_excellent(self) -> None:
        assert get_band(90) == HealthBand.EXCELLENT

    def test_score_100_is_excellent(self) -> None:
        assert get_band(100) == HealthBand.EXCELLENT


# ---------------------------------------------------------------------------
# FR-GOV-HS-006 -- get_band HEALTHY for score >= 70 and < 90
# ---------------------------------------------------------------------------


class TestBandHealthy:
    """FR-GOV-HS-006: ``get_band([70, 90))`` returns ``HEALTHY``."""

    def test_score_70_is_healthy(self) -> None:
        assert get_band(70) == HealthBand.HEALTHY

    def test_score_89_is_healthy(self) -> None:
        assert get_band(89) == HealthBand.HEALTHY


# ---------------------------------------------------------------------------
# FR-GOV-HS-007 -- get_band WARNING for score >= 40 and < 70
# ---------------------------------------------------------------------------


class TestBandWarning:
    """FR-GOV-HS-007: ``get_band([40, 70))`` returns ``WARNING``."""

    def test_score_40_is_warning(self) -> None:
        assert get_band(40) == HealthBand.WARNING

    def test_score_69_is_warning(self) -> None:
        assert get_band(69) == HealthBand.WARNING


# ---------------------------------------------------------------------------
# FR-GOV-HS-008 -- get_band CRITICAL for score < 40
# ---------------------------------------------------------------------------


class TestBandCritical:
    """FR-GOV-HS-008: ``get_band(<40)`` returns ``CRITICAL``."""

    def test_score_0_is_critical(self) -> None:
        assert get_band(0) == HealthBand.CRITICAL

    def test_score_39_is_critical(self) -> None:
        assert get_band(39) == HealthBand.CRITICAL


# ---------------------------------------------------------------------------
# FR-GOV-HS-009 -- compute returns score in [0, 100]
# ---------------------------------------------------------------------------


class TestComputeBounds:
    """FR-GOV-HS-009: ``compute`` score is always within [0, 100]."""

    def test_score_within_bounds_all_present(self, tmp_path: Path) -> None:
        path = _write_targets(tmp_path)
        computer = HealthScoreComputer(path)
        result = computer.compute({"alpha": 80, "beta": 5})
        assert 0.0 <= result.score <= 100.0

    def test_score_within_bounds_no_values(self, tmp_path: Path) -> None:
        path = _write_targets(tmp_path)
        computer = HealthScoreComputer(path)
        result = computer.compute({})
        assert 0.0 <= result.score <= 100.0

    def test_score_perfect(self, tmp_path: Path) -> None:
        path = _write_targets(tmp_path)
        computer = HealthScoreComputer(path)
        result = computer.compute({"alpha": 100, "beta": 0})
        assert result.score == 100.0

    def test_score_zero(self, tmp_path: Path) -> None:
        path = _write_targets(tmp_path)
        computer = HealthScoreComputer(path)
        result = computer.compute({"alpha": 0, "beta": 100})
        assert result.score == 0.0


# ---------------------------------------------------------------------------
# FR-GOV-HS-010 -- compute_with_trend returns 'improving' when delta >= 2.0
# ---------------------------------------------------------------------------


class TestTrendImproving:
    """FR-GOV-HS-010: trend is ``improving`` when delta >= 2.0."""

    def test_improving_delta(self, tmp_path: Path) -> None:
        path = _write_targets(tmp_path)
        computer = HealthScoreComputer(path)
        result = computer.compute_with_trend(
            {"alpha": 100, "beta": 0}, previous_score=50.0
        )
        assert result.trend == "improving"


# ---------------------------------------------------------------------------
# FR-GOV-HS-011 -- compute_with_trend returns 'degrading' when delta <= -2.0
# ---------------------------------------------------------------------------


class TestTrendDegrading:
    """FR-GOV-HS-011: trend is ``degrading`` when delta <= -2.0."""

    def test_degrading_delta(self, tmp_path: Path) -> None:
        path = _write_targets(tmp_path)
        computer = HealthScoreComputer(path)
        result = computer.compute_with_trend(
            {"alpha": 0, "beta": 100}, previous_score=90.0
        )
        assert result.trend == "degrading"


# ---------------------------------------------------------------------------
# FR-GOV-HS-012 -- compute_with_trend returns 'stable' for small delta
# ---------------------------------------------------------------------------


class TestTrendStable:
    """FR-GOV-HS-012: trend is ``stable`` for small delta."""

    def test_stable_small_delta(self, tmp_path: Path) -> None:
        path = _write_targets(tmp_path)
        computer = HealthScoreComputer(path)
        first = computer.compute({"alpha": 50, "beta": 5})
        result = computer.compute_with_trend(
            {"alpha": 50, "beta": 5}, previous_score=first.score
        )
        assert result.trend == "stable"


# ---------------------------------------------------------------------------
# FR-GOV-HS-013 -- compute_with_trend returns 'stable' when previous is None
# ---------------------------------------------------------------------------


class TestTrendNone:
    """FR-GOV-HS-013: trend is ``stable`` when ``previous_score is None``."""

    def test_stable_when_none(self, tmp_path: Path) -> None:
        path = _write_targets(tmp_path)
        computer = HealthScoreComputer(path)
        result = computer.compute_with_trend(
            {"alpha": 50, "beta": 5}, previous_score=None
        )
        assert result.trend == "stable"


# ---------------------------------------------------------------------------
# FR-GOV-HS-014 / FR-GOV-HS-015 -- __all__ exports
# ---------------------------------------------------------------------------


class TestHSAll:
    """FR-GOV-HS-014/015: canonical public surface."""

    def test_all_exposes_health_score_computer(self) -> None:
        assert "HealthScoreComputer" in _mod.__all__

    def test_all_exposes_get_band(self) -> None:
        assert "get_band" in _mod.__all__

    def test_all_exposes_health_band(self) -> None:
        assert "HealthBand" in _mod.__all__
