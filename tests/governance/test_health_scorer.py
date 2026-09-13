"""Tests for governance/health_scorer.py - Health score calculator.

Additional coverage beyond tests/test_governance_health_scorer.py:
- Edge cases for normalize_score
- HealthScorer file not found error
- Unknown dimension error
- Zero weight handling
- Negative value handling
- Band boundary conditions
- Version field extraction

Traces to: WP-3001
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from thegent.governance.health_scorer import (
    HealthScorer,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def basic_config() -> dict:
    """Basic health config for testing."""
    return {
        "version": "2.0.0",
        "dimensions": {
            "test_coverage": {
                "weight": 0.6,
                "target": 80,
                "direction": "higher_is_better",
            },
            "lint_violations": {
                "weight": 0.4,
                "target": 10,
                "direction": "lower_is_better",
            },
        },
        "bands": {
            "excellent": {"min": 90, "label": "Excellent"},
            "healthy": {"min": 70, "label": "Healthy"},
            "warning": {"min": 40, "label": "Warning"},
            "critical": {"min": 0, "label": "Critical"},
        },
    }


@pytest.fixture
def config_file(basic_config: dict, tmp_path: Path) -> Path:
    """Create a config file and return its path."""
    config_path = tmp_path / "health-targets.json"
    with open(config_path, "w") as f:
        f.write(json.dumps(basic_config))
    return config_path


# ---------------------------------------------------------------------------
# Initialization tests
# ---------------------------------------------------------------------------


class TestHealthScorerInit:
    """Tests for HealthScorer initialization."""

    def test_init_loads_config(self, config_file: Path, basic_config: dict) -> None:
        """HealthScorer loads config from file."""
        scorer = HealthScorer(config_file)
        assert scorer.config == basic_config

    def test_init_raises_on_missing_file(self, tmp_path: Path) -> None:
        """HealthScorer raises FileNotFoundError for missing config."""
        with pytest.raises(FileNotFoundError, match="not found"):
            HealthScorer(tmp_path / "missing.json")

    def test_init_accepts_string_path(self, config_file: Path) -> None:
        """HealthScorer accepts string path as well as Path."""
        scorer = HealthScorer(str(config_file))
        assert scorer.config is not None

    def test_init_extracts_dimensions(self, config_file: Path) -> None:
        """HealthScorer extracts dimensions dict."""
        scorer = HealthScorer(config_file)
        assert "test_coverage" in scorer.dimensions
        assert "lint_violations" in scorer.dimensions

    def test_init_extracts_bands(self, config_file: Path) -> None:
        """HealthScorer extracts bands dict."""
        scorer = HealthScorer(config_file)
        assert "excellent" in scorer.bands
        assert "critical" in scorer.bands


# ---------------------------------------------------------------------------
# normalize_score edge cases
# ---------------------------------------------------------------------------


class TestNormalizeScoreEdgeCases:
    """Edge case tests for normalize_score."""

    def test_normalize_zero_target_higher_is_better(self, config_file: Path) -> None:
        """normalize_score with zero target for higher_is_better."""
        scorer = HealthScorer(config_file)
        # Zero target: any actual is 0% if non-zero
        assert scorer.normalize_score(0, 0, "higher_is_better") == 100.0
        assert scorer.normalize_score(10, 0, "higher_is_better") == 0.0

    def test_normalize_zero_target_lower_is_better(self, config_file: Path) -> None:
        """normalize_score with zero target for lower_is_better."""
        scorer = HealthScorer(config_file)
        assert scorer.normalize_score(0, 0, "lower_is_better") == 100.0
        assert scorer.normalize_score(10, 0, "lower_is_better") == 0.0

    def test_normalize_negative_actual_higher_is_better(self, config_file: Path) -> None:
        """normalize_score with negative actual for higher_is_better."""
        scorer = HealthScorer(config_file)
        # Negative actual should return 0 for higher_is_better
        assert scorer.normalize_score(-10, 100, "higher_is_better") == 0.0

    def test_normalize_above_target_higher_is_better(self, config_file: Path) -> None:
        """normalize_score caps at 100 for above-target higher_is_better."""
        scorer = HealthScorer(config_file)
        assert scorer.normalize_score(150, 100, "higher_is_better") == 100.0

    def test_normalize_negative_actual_lower_is_better(self, config_file: Path) -> None:
        """normalize_score with negative actual for lower_is_better."""
        scorer = HealthScorer(config_file)
        # Negative actual could produce >100 for lower_is_better
        result = scorer.normalize_score(-10, 100, "lower_is_better")
        # Should be capped at 100
        assert result <= 100.0

    def test_normalize_above_target_lower_is_better(self, config_file: Path) -> None:
        """normalize_score for lower_is_better when actual > target."""
        scorer = HealthScorer(config_file)
        # If target is 10 and actual is 20, score = (1 - 20/10) * 100 = -100
        # Should be capped at 0
        result = scorer.normalize_score(20, 10, "lower_is_better")
        assert result >= 0.0

    def test_normalize_exact_target_higher_is_better(self, config_file: Path) -> None:
        """normalize_score at exact target gives 100 for higher_is_better."""
        scorer = HealthScorer(config_file)
        assert scorer.normalize_score(80, 80, "higher_is_better") == 100.0

    def test_normalize_exact_target_lower_is_better(self, config_file: Path) -> None:
        """normalize_score at exact target gives 0 for lower_is_better."""
        scorer = HealthScorer(config_file)
        # At target means "just acceptable", so 0 score
        assert scorer.normalize_score(10, 10, "lower_is_better") == 0.0


# ---------------------------------------------------------------------------
# dimension_status tests
# ---------------------------------------------------------------------------


class TestDimensionStatus:
    """Tests for dimension_status method."""

    def test_dimension_status_excellent(self, config_file: Path) -> None:
        """dimension_status returns excellent for high scores."""
        scorer = HealthScorer(config_file)
        assert scorer.dimension_status(95) == "excellent"

    def test_dimension_status_healthy(self, config_file: Path) -> None:
        """dimension_status returns healthy for moderate scores."""
        scorer = HealthScorer(config_file)
        assert scorer.dimension_status(75) == "healthy"

    def test_dimension_status_warning(self, config_file: Path) -> None:
        """dimension_status returns warning for low scores."""
        scorer = HealthScorer(config_file)
        assert scorer.dimension_status(50) == "warning"

    def test_dimension_status_critical(self, config_file: Path) -> None:
        """dimension_status returns critical for very low scores."""
        scorer = HealthScorer(config_file)
        assert scorer.dimension_status(10) == "critical"

    def test_dimension_status_boundary_exact(self, config_file: Path) -> None:
        """dimension_status at exact boundary value."""
        scorer = HealthScorer(config_file)
        # At 90 should be excellent
        assert scorer.dimension_status(90) == "excellent"
        # At 70 should be healthy
        assert scorer.dimension_status(70) == "healthy"
        # At 40 should be warning
        assert scorer.dimension_status(40) == "warning"

    def test_dimension_status_just_below_boundary(self, config_file: Path) -> None:
        """dimension_status just below boundary."""
        scorer = HealthScorer(config_file)
        # Just below 90 should be healthy
        assert scorer.dimension_status(89) == "healthy"
        # Just below 70 should be warning
        assert scorer.dimension_status(69) == "warning"

    def test_dimension_status_zero(self, config_file: Path) -> None:
        """dimension_status at zero."""
        scorer = HealthScorer(config_file)
        assert scorer.dimension_status(0) == "critical"

    def test_dimension_status_hundred(self, config_file: Path) -> None:
        """dimension_status at 100."""
        scorer = HealthScorer(config_file)
        assert scorer.dimension_status(100) == "excellent"


# ---------------------------------------------------------------------------
# score_dimension tests
# ---------------------------------------------------------------------------


class TestScoreDimension:
    """Tests for score_dimension method."""

    def test_score_dimension_returns_dimension_score(self, config_file: Path) -> None:
        """score_dimension returns DimensionScore TypedDict."""
        scorer = HealthScorer(config_file)
        result = scorer.score_dimension("test_coverage", 60)
        assert isinstance(result, dict)
        assert "dimension" in result
        assert "weight" in result
        assert "target" in result
        assert "actual" in result
        assert "direction" in result
        assert "score" in result
        assert "status" in result

    def test_score_dimension_unknown_raises(self, config_file: Path) -> None:
        """score_dimension raises ValueError for unknown dimension."""
        scorer = HealthScorer(config_file)
        with pytest.raises(ValueError, match="Unknown dimension"):
            scorer.score_dimension("nonexistent", 50)

    def test_score_dimension_uses_default_weight(self, tmp_path: Path) -> None:
        """score_dimension uses default weight of 0.0 if not specified."""
        config = {
            "version": "1.0.0",
            "dimensions": {"test_dim": {"target": 100, "direction": "higher_is_better"}},
            "bands": {"ok": {"min": 0}},
        }
        config_path = tmp_path / "config.json"
        with open(config_path, "w") as f:
            json.dump(config, f)
        scorer = HealthScorer(config_path)
        result = scorer.score_dimension("test_dim", 50)
        assert result["weight"] == 0.0

    def test_score_dimension_uses_default_direction(self, tmp_path: Path) -> None:
        """score_dimension uses default direction if not specified."""
        config = {
            "version": "1.0.0",
            "dimensions": {"test_dim": {"weight": 1.0, "target": 100}},
            "bands": {"ok": {"min": 0}},
        }
        config_path = tmp_path / "config.json"
        with open(config_path, "w") as f:
            json.dump(config, f)
        scorer = HealthScorer(config_path)
        result = scorer.score_dimension("test_dim", 50)
        assert result["direction"] == "higher_is_better"

    def test_score_dimension_includes_all_fields(self, config_file: Path) -> None:
        """score_dimension includes all expected fields."""
        scorer = HealthScorer(config_file)
        result = scorer.score_dimension("test_coverage", 75)
        assert result["dimension"] == "test_coverage"
        assert result["actual"] == 75
        assert result["target"] == 80
        assert result["weight"] == 0.6
        assert result["direction"] == "higher_is_better"


# ---------------------------------------------------------------------------
# calculate_overall tests
# ---------------------------------------------------------------------------


class TestCalculateOverall:
    """Tests for calculate_overall method."""

    def test_calculate_overall_empty_scores(self, config_file: Path) -> None:
        """calculate_overall returns 0 for empty scores list."""
        scorer = HealthScorer(config_file)
        assert scorer.calculate_overall([]) == 0.0

    def test_calculate_overall_single_score(self, config_file: Path) -> None:
        """calculate_overall with single score returns that score."""
        scorer = HealthScorer(config_file)
        scores = [scorer.score_dimension("test_coverage", 80)]
        result = scorer.calculate_overall(scores)
        # Single dimension with weight 0.6, score at target = 100
        assert result == 100.0

    def test_calculate_overall_zero_total_weight(self, tmp_path: Path) -> None:
        """calculate_overall returns 0 when total weight is 0."""
        config = {
            "version": "1.0.0",
            "dimensions": {
                "dim1": {"weight": 0.0, "target": 100, "direction": "higher_is_better"},
                "dim2": {"weight": 0.0, "target": 100, "direction": "higher_is_better"},
            },
            "bands": {"ok": {"min": 0}},
        }
        config_path = tmp_path / "config.json"
        with open(config_path, "w") as f:
            json.dump(config, f)
        scorer = HealthScorer(config_path)
        scores = [
            scorer.score_dimension("dim1", 50),
            scorer.score_dimension("dim2", 75),
        ]
        assert scorer.calculate_overall(scores) == 0.0

    def test_calculate_overall_weighted_average(self, config_file: Path) -> None:
        """calculate_overall computes weighted average correctly."""
        scorer = HealthScorer(config_file)
        scores = [
            scorer.score_dimension("test_coverage", 80),  # 100% * 0.6 = 60
            scorer.score_dimension("lint_violations", 0),  # 100% * 0.4 = 40
        ]
        result = scorer.calculate_overall(scores)
        assert result == 100.0


# ---------------------------------------------------------------------------
# generate_report tests
# ---------------------------------------------------------------------------


class TestGenerateReport:
    """Tests for generate_report method."""

    def test_generate_report_returns_health_report(self, config_file: Path) -> None:
        """generate_report returns HealthReport TypedDict."""
        scorer = HealthScorer(config_file)
        report = scorer.generate_report({"test_coverage": 75, "lint_violations": 5})
        assert isinstance(report, dict)
        assert "version" in report
        assert "overall_score" in report
        assert "status" in report
        assert "dimensions" in report
        assert "timestamp" in report

    def test_generate_report_includes_version(self, config_file: Path) -> None:
        """generate_report includes version from config."""
        scorer = HealthScorer(config_file)
        report = scorer.generate_report({"test_coverage": 75, "lint_violations": 5})
        assert report["version"] == "2.0.0"

    def test_generate_report_includes_dimensions(self, config_file: Path) -> None:
        """generate_report includes all dimension scores."""
        scorer = HealthScorer(config_file)
        report = scorer.generate_report({"test_coverage": 75, "lint_violations": 5})
        assert len(report["dimensions"]) == 2

    def test_generate_report_skips_unknown_dimensions(self, config_file: Path) -> None:
        """generate_report skips measurements for unknown dimensions."""
        scorer = HealthScorer(config_file)
        report = scorer.generate_report(
            {
                "test_coverage": 75,
                "unknown_dimension": 100,
            }
        )
        assert len(report["dimensions"]) == 1
        assert report["dimensions"][0]["dimension"] == "test_coverage"

    def test_generate_report_rounds_overall_score(self, config_file: Path) -> None:
        """generate_report rounds overall score to 1 decimal."""
        scorer = HealthScorer(config_file)
        report = scorer.generate_report({"test_coverage": 75, "lint_violations": 5})
        # Check that overall_score has at most 1 decimal place
        overall = report["overall_score"]
        assert overall == round(overall, 1)

    def test_generate_report_timestamp_is_iso_format(self, config_file: Path) -> None:
        """generate_report timestamp is ISO format."""
        scorer = HealthScorer(config_file)
        report = scorer.generate_report({"test_coverage": 75, "lint_violations": 5})
        # Check that timestamp looks like ISO format
        assert "T" in report["timestamp"]

    def test_generate_report_empty_measurements(self, config_file: Path) -> None:
        """generate_report handles empty measurements."""
        scorer = HealthScorer(config_file)
        report = scorer.generate_report({})
        assert report["overall_score"] == 0.0
        assert report["dimensions"] == []

    def test_generate_report_default_version(self, tmp_path: Path) -> None:
        """generate_report uses default version if not in config."""
        config = {
            "dimensions": {"dim": {"weight": 1.0, "target": 100, "direction": "higher_is_better"}},
            "bands": {"ok": {"min": 0}},
        }
        config_path = tmp_path / "config.json"
        with open(config_path, "w") as f:
            json.dump(config, f)
        scorer = HealthScorer(config_path)
        report = scorer.generate_report({"dim": 50})
        assert report["version"] == "1.0.0"


# ---------------------------------------------------------------------------
# TypedDict validation tests
# ---------------------------------------------------------------------------


class TestTypedDictShapes:
    """Tests for TypedDict shapes."""

    def test_dimension_score_has_required_keys(self, config_file: Path) -> None:
        """DimensionScore has all required keys."""
        scorer = HealthScorer(config_file)
        result = scorer.score_dimension("test_coverage", 50)
        required_keys = {
            "dimension",
            "weight",
            "target",
            "actual",
            "direction",
            "score",
            "status",
        }
        assert set(result.keys()) == required_keys

    def test_health_report_has_required_keys(self, config_file: Path) -> None:
        """HealthReport has all required keys."""
        scorer = HealthScorer(config_file)
        report = scorer.generate_report({"test_coverage": 50})
        required_keys = {
            "version",
            "overall_score",
            "status",
            "dimensions",
            "timestamp",
        }
        assert set(report.keys()) == required_keys

    def test_dimensions_in_report_are_dimension_scores(self, config_file: Path) -> None:
        """dimensions in HealthReport are DimensionScore dicts."""
        scorer = HealthScorer(config_file)
        report = scorer.generate_report({"test_coverage": 50})
        for dim in report["dimensions"]:
            assert "dimension" in dim
            assert "score" in dim
            assert "status" in dim
