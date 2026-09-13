"""Unit tests for health score computation, bands, normalization, and trend detection."""

from __future__ import annotations

from typing import TYPE_CHECKING

import orjson as json

if TYPE_CHECKING:
    from pathlib import Path

import pytest
from pydantic import ValidationError

from thegent.governance.health_score import (
    DimensionScore,
    HealthBand,
    HealthScore,
    HealthScoreComputer,
    _band_from_normalized,
    get_band,
)

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PERFECT_VALUES: dict[str, float] = {
    "test_coverage": 80,
    "lint_violations": 0,
    "complexity_index": 0,
    "security_findings": 0,
    "spec_traceability": 80,
    "doc_organization": 100,
    "freshness": 0,
    "agent_health": 0,
}

WORST_VALUES: dict[str, float] = {
    "test_coverage": 0,
    "lint_violations": 50,
    "complexity_index": 30,
    "security_findings": 20,
    "spec_traceability": 0,
    "doc_organization": 0,
    "freshness": 20,
    "agent_health": 10,
}

MIXED_VALUES: dict[str, float] = {
    "test_coverage": 60,
    "lint_violations": 3,
    "complexity_index": 5,
    "security_findings": 0,
    "spec_traceability": 40,
    "doc_organization": 70,
    "freshness": 2,
    "agent_health": 1,
}

_TARGETS_DATA: dict = {
    "version": "1.0.0",
    "dimensions": {
        "test_coverage": {
            "weight": 0.20,
            "target": 80,
            "unit": "percent",
            "direction": "higher_is_better",
        },
        "lint_violations": {
            "weight": 0.15,
            "target": 0,
            "unit": "count",
            "direction": "lower_is_better",
        },
        "complexity_index": {
            "weight": 0.15,
            "target": 10,
            "unit": "cyclomatic_avg",
            "direction": "lower_is_better",
        },
        "security_findings": {
            "weight": 0.15,
            "target": 0,
            "unit": "count",
            "direction": "lower_is_better",
        },
        "spec_traceability": {
            "weight": 0.10,
            "target": 80,
            "unit": "percent",
            "direction": "higher_is_better",
        },
        "doc_organization": {
            "weight": 0.10,
            "target": 100,
            "unit": "percent",
            "direction": "higher_is_better",
        },
        "freshness": {
            "weight": 0.10,
            "target": 0,
            "unit": "stale_items",
            "direction": "lower_is_better",
        },
        "agent_health": {
            "weight": 0.05,
            "target": 0,
            "unit": "open_breakers",
            "direction": "lower_is_better",
        },
    },
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def targets_path(tmp_path: Path) -> Path:
    """Write health-targets.json to tmp_path and return its path.

    Traces to: FR-GOV-001
    """
    p = tmp_path / "health-targets.json"
    p.write_text(json.dumps(_TARGETS_DATA).decode())
    return p


@pytest.fixture
def computer(targets_path: Path) -> HealthScoreComputer:
    """Return a HealthScoreComputer loaded from the temp targets.

    Traces to: FR-GOV-001
    """
    return HealthScoreComputer(targets_path)


# ---------------------------------------------------------------------------
# get_band
# ---------------------------------------------------------------------------


def test_get_band_excellent() -> None:
    """Score 95 maps to EXCELLENT band.

    Traces to: FR-GOV-001
    """
    assert get_band(95) == HealthBand.EXCELLENT


def test_get_band_healthy() -> None:
    """Score 75 maps to HEALTHY band.

    Traces to: FR-GOV-001
    """
    assert get_band(75) == HealthBand.HEALTHY


def test_get_band_warning() -> None:
    """Score 50 maps to WARNING band.

    Traces to: FR-GOV-001
    """
    assert get_band(50) == HealthBand.WARNING


def test_get_band_critical() -> None:
    """Score 20 maps to CRITICAL band.

    Traces to: FR-GOV-001
    """
    assert get_band(20) == HealthBand.CRITICAL


def test_get_band_boundaries() -> None:
    """Boundary values map to correct bands: 90/89, 70/69, 40/39.

    Traces to: FR-GOV-001
    """
    assert get_band(90) == HealthBand.EXCELLENT
    assert get_band(89) == HealthBand.HEALTHY
    assert get_band(70) == HealthBand.HEALTHY
    assert get_band(69) == HealthBand.WARNING
    assert get_band(40) == HealthBand.WARNING
    assert get_band(39) == HealthBand.CRITICAL


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------


def test_normalize_higher_is_better(computer: HealthScoreComputer) -> None:
    """Higher-is-better: 80/80 -> 1.0, 40/80 -> 0.5.

    Traces to: FR-GOV-001
    """
    assert computer._normalize(80.0, 80.0, "higher_is_better") == 1.0
    assert computer._normalize(40.0, 80.0, "higher_is_better") == 0.5
    assert computer._normalize(100.0, 80.0, "higher_is_better") == 1.0
    assert computer._normalize(0.0, 80.0, "higher_is_better") == 0.0


def test_normalize_lower_is_better(computer: HealthScoreComputer) -> None:
    """Lower-is-better: lint 0/0 -> 1.0, lint 5/0 -> 0.5, lint 10/0 -> 0.0.

    Traces to: FR-GOV-001
    """
    assert computer._normalize(0.0, 0.0, "lower_is_better") == 1.0
    assert computer._normalize(5.0, 0.0, "lower_is_better") == 0.5
    assert computer._normalize(10.0, 0.0, "lower_is_better") == 0.0


def test_normalize_lower_is_better_nonzero_target(computer: HealthScoreComputer) -> None:
    """Lower-is-better with nonzero target: 0/10 -> 1.0, 5/10 -> 0.5, 10/10 -> 0.0.

    Traces to: FR-GOV-001
    """
    assert computer._normalize(0.0, 10.0, "lower_is_better") == 1.0
    assert computer._normalize(5.0, 10.0, "lower_is_better") == 0.5
    assert computer._normalize(10.0, 10.0, "lower_is_better") == 0.0
    assert computer._normalize(20.0, 10.0, "lower_is_better") == 0.0


# ---------------------------------------------------------------------------
# Compute
# ---------------------------------------------------------------------------


def test_compute_all_perfect(computer: HealthScoreComputer) -> None:
    """All dimensions at target produce score >= 95 (actually 100).

    Traces to: FR-GOV-001
    """
    result = computer.compute(PERFECT_VALUES)
    assert result.score >= 95
    assert result.score == 100.0
    assert result.band == HealthBand.EXCELLENT
    assert result.trend == "stable"
    assert len(result.dimensions) == 8


def test_compute_all_worst(computer: HealthScoreComputer) -> None:
    """All dimensions at worst-case produce score < 20.

    Traces to: FR-GOV-001
    """
    result = computer.compute(WORST_VALUES)
    assert result.score < 20
    assert result.band == HealthBand.CRITICAL


def test_compute_mixed(computer: HealthScoreComputer) -> None:
    """Mixed good/bad dimensions produce a mid-range score.

    Traces to: FR-GOV-001
    """
    result = computer.compute(MIXED_VALUES)
    assert 20 < result.score < 95
    assert result.band in (HealthBand.HEALTHY, HealthBand.WARNING)


# ---------------------------------------------------------------------------
# Trend detection
# ---------------------------------------------------------------------------


def test_compute_with_trend_improving(computer: HealthScoreComputer) -> None:
    """Current 100 vs previous 70 -> improving.

    Traces to: FR-GOV-001
    """
    result = computer.compute_with_trend(PERFECT_VALUES, previous_score=70.0)
    assert result.trend == "improving"


def test_compute_with_trend_degrading(computer: HealthScoreComputer) -> None:
    """Current score much lower than previous -> degrading.

    Traces to: FR-GOV-001
    """
    result = computer.compute_with_trend(WORST_VALUES, previous_score=80.0)
    assert result.trend == "degrading"


def test_compute_with_trend_stable(computer: HealthScoreComputer) -> None:
    """Small delta (within +/-2) -> stable.

    Traces to: FR-GOV-001
    """
    result = computer.compute_with_trend(PERFECT_VALUES, previous_score=99.0)
    assert result.trend == "stable"


def test_compute_with_trend_none_previous(computer: HealthScoreComputer) -> None:
    """No previous score -> defaults to stable.

    Traces to: FR-GOV-001
    """
    result = computer.compute_with_trend(PERFECT_VALUES, previous_score=None)
    assert result.trend == "stable"


# ---------------------------------------------------------------------------
# Dimension status assignment
# ---------------------------------------------------------------------------


def test_dimension_status_assignment(computer: HealthScoreComputer) -> None:
    """Dimension status reflects normalized value: green/yellow/red via bands.

    Traces to: FR-GOV-001
    """
    result = computer.compute(PERFECT_VALUES)
    for dim in result.dimensions.values():
        assert dim.status == HealthBand.EXCELLENT
        assert dim.normalized == 1.0

    result_bad = computer.compute(WORST_VALUES)
    cov = result_bad.dimensions["test_coverage"]
    assert cov.normalized == 0.0
    assert cov.status == HealthBand.CRITICAL


def test_band_from_normalized_boundaries() -> None:
    """Per-dimension band derivation at boundary values.

    Traces to: FR-GOV-001
    """
    assert _band_from_normalized(1.0) == HealthBand.EXCELLENT
    assert _band_from_normalized(0.9) == HealthBand.EXCELLENT
    assert _band_from_normalized(0.89) == HealthBand.HEALTHY
    assert _band_from_normalized(0.7) == HealthBand.HEALTHY
    assert _band_from_normalized(0.69) == HealthBand.WARNING
    assert _band_from_normalized(0.4) == HealthBand.WARNING
    assert _band_from_normalized(0.39) == HealthBand.CRITICAL
    assert _band_from_normalized(0.0) == HealthBand.CRITICAL


# ---------------------------------------------------------------------------
# Missing / partial dimensions
# ---------------------------------------------------------------------------


def test_missing_dimensions(computer: HealthScoreComputer) -> None:
    """Passing a partial dict does not crash; missing dims get worst-case defaults.

    Traces to: FR-GOV-001
    """
    result = computer.compute({"test_coverage": 80})
    assert result.score > 0
    assert result.dimensions["test_coverage"].normalized == 1.0
    assert "lint_violations" in result.dimensions
    assert len(result.dimensions) == 8


def test_empty_dimensions(computer: HealthScoreComputer) -> None:
    """Empty dict produces score 0 with all dims defaulted.

    Traces to: FR-GOV-001
    """
    result = computer.compute({})
    assert result.score == 0.0
    assert result.band == HealthBand.CRITICAL
    assert len(result.dimensions) == 8


# ---------------------------------------------------------------------------
# Model validation
# ---------------------------------------------------------------------------


def test_health_score_model_fields() -> None:
    """HealthScore model accepts valid data and sets defaults.

    Traces to: FR-GOV-001
    """
    hs = HealthScore(
        score=85.0,
        dimensions={},
        band=HealthBand.HEALTHY,
        trend="stable",
    )
    assert hs.score == 85.0
    assert hs.computed_at is not None
    assert hs.cycle_id is None


def test_dimension_score_rejects_invalid_weight() -> None:
    """DimensionScore rejects weight > 1.0.

    Traces to: FR-GOV-001
    """
    with pytest.raises(ValidationError):
        DimensionScore(
            name="x",
            weight=1.5,
            raw_value=0,
            normalized=0,
            target=0,
            direction="higher_is_better",
            status=HealthBand.CRITICAL,
        )


def test_health_band_str_values() -> None:
    """HealthBand members are strings with expected values.

    Traces to: FR-GOV-001
    """
    assert HealthBand.EXCELLENT == "excellent"
    assert HealthBand.HEALTHY == "healthy"
    assert HealthBand.WARNING == "warning"
    assert HealthBand.CRITICAL == "critical"
    assert isinstance(HealthBand.EXCELLENT, str)


def test_default_raw_values() -> None:
    """Worst-case defaults: higher_is_better -> 0, lower_is_better -> 2x target.

    Traces to: FR-GOV-001
    """
    assert HealthScoreComputer._default_raw(80, "higher_is_better") == 0.0
    assert HealthScoreComputer._default_raw(10, "lower_is_better") == 20.0
    assert HealthScoreComputer._default_raw(0, "lower_is_better") == 10.0
