"""Tests for health score calculator."""

import tempfile
from pathlib import Path

import orjson as json

from thegent.governance.health_scorer import HealthScorer


def test_health_scorer_initialization():
    """Test that health scorer loads config correctly."""
    # Create a minimal config
    config = {
        "version": "1.0.0",
        "dimensions": {
            "test_coverage": {
                "weight": 0.5,
                "target": 80,
                "direction": "higher_is_better",
            },
            "lint_violations": {
                "weight": 0.5,
                "target": 0,
                "direction": "lower_is_better",
            },
        },
        "bands": {
            "excellent": {"min": 90, "label": "Excellent"},
            "healthy": {"min": 70, "label": "Healthy"},
            "critical": {"min": 0, "label": "Critical"},
        },
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "health-targets.json"
        with open(config_file, "w") as f:
            json.dump(config, f)

        scorer = HealthScorer(config_file)
        assert scorer.config == config


def test_normalize_score_higher_is_better():
    """Test score normalization for higher-is-better metrics."""
    config = {
        "version": "1.0.0",
        "dimensions": {
            "coverage": {
                "weight": 1.0,
                "target": 80,
                "direction": "higher_is_better",
            }
        },
        "bands": {"excellent": {"min": 90, "label": "Excellent"}},
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "health-targets.json"
        with open(config_file, "w") as f:
            json.dump(config, f)

        scorer = HealthScorer(config_file)

        # At target (80 out of 80) = 100%
        assert scorer.normalize_score(80, 80, "higher_is_better") == 100.0

        # Half of target (40 out of 80) = 50%
        assert scorer.normalize_score(40, 80, "higher_is_better") == 50.0

        # Above target (100 out of 80) = capped at 100%
        assert scorer.normalize_score(100, 80, "higher_is_better") == 100.0


def test_normalize_score_lower_is_better():
    """Test score normalization for lower-is-better metrics."""
    config = {
        "version": "1.0.0",
        "dimensions": {
            "violations": {
                "weight": 1.0,
                "target": 10,
                "direction": "lower_is_better",
            }
        },
        "bands": {"excellent": {"min": 90, "label": "Excellent"}},
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "health-targets.json"
        with open(config_file, "w") as f:
            json.dump(config, f)

        scorer = HealthScorer(config_file)

        # At target (10 violations) = 0%
        assert scorer.normalize_score(10, 10, "lower_is_better") == 0.0

        # Half of target (5 violations) = 50%
        assert scorer.normalize_score(5, 10, "lower_is_better") == 50.0

        # Zero violations = 100%
        assert scorer.normalize_score(0, 10, "lower_is_better") == 100.0


def test_dimension_status():
    """Test status label calculation."""
    config = {
        "version": "1.0.0",
        "dimensions": {},
        "bands": {
            "excellent": {"min": 90, "label": "Excellent"},
            "healthy": {"min": 70, "label": "Healthy"},
            "warning": {"min": 40, "label": "Warning"},
            "critical": {"min": 0, "label": "Critical"},
        },
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "health-targets.json"
        with open(config_file, "w") as f:
            json.dump(config, f)

        scorer = HealthScorer(config_file)

        assert scorer.dimension_status(95) == "excellent"
        assert scorer.dimension_status(80) == "healthy"
        assert scorer.dimension_status(50) == "warning"
        assert scorer.dimension_status(10) == "critical"


def test_score_dimension():
    """Test individual dimension scoring."""
    config = {
        "version": "1.0.0",
        "dimensions": {
            "coverage": {
                "weight": 0.5,
                "target": 80,
                "direction": "higher_is_better",
            }
        },
        "bands": {
            "excellent": {"min": 90, "label": "Excellent"},
            "healthy": {"min": 70, "label": "Healthy"},
            "critical": {"min": 0, "label": "Critical"},
        },
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "health-targets.json"
        with open(config_file, "w") as f:
            json.dump(config, f)

        scorer = HealthScorer(config_file)
        result = scorer.score_dimension("coverage", 75)

        assert result["dimension"] == "coverage"
        assert result["actual"] == 75
        assert result["target"] == 80
        assert result["score"] == 93.75  # 75/80 * 100
        assert result["status"] == "excellent"
        assert result["weight"] == 0.5


def test_calculate_overall():
    """Test overall weighted score calculation."""
    config = {
        "version": "1.0.0",
        "dimensions": {
            "coverage": {"weight": 0.7, "target": 80, "direction": "higher_is_better"},
            "violations": {"weight": 0.3, "target": 10, "direction": "lower_is_better"},
        },
        "bands": {"excellent": {"min": 0, "label": "Excellent"}},
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "health-targets.json"
        with open(config_file, "w") as f:
            json.dump(config, f)

        scorer = HealthScorer(config_file)

        scores = [
            scorer.score_dimension("coverage", 80),  # 100%
            scorer.score_dimension("violations", 0),  # 100%
        ]

        overall = scorer.calculate_overall(scores)
        assert overall == 100.0  # Perfect score


def test_generate_report():
    """Test full health report generation."""
    config = {
        "version": "1.0.0",
        "dimensions": {
            "coverage": {"weight": 0.6, "target": 80, "direction": "higher_is_better"},
            "violations": {"weight": 0.4, "target": 5, "direction": "lower_is_better"},
        },
        "bands": {
            "excellent": {"min": 90, "label": "Excellent"},
            "healthy": {"min": 70, "label": "Healthy"},
            "critical": {"min": 0, "label": "Critical"},
        },
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "health-targets.json"
        with open(config_file, "w") as f:
            json.dump(config, f)

        scorer = HealthScorer(config_file)
        report = scorer.generate_report({"coverage": 75, "violations": 3})

        assert report["overall_score"] > 0
        assert len(report["dimensions"]) == 2
        assert report["version"] == "1.0.0"
        assert "timestamp" in report
