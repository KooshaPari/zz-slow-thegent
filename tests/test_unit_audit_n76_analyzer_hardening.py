"""Hardening invariants for ``governance.analyzer`` — AUDIT-N+76.

15 invariants FR-GOV-AN-001 .. FR-GOV-AN-015 covering Finding defaults,
Finding field bounds, HealthAnalyzer init, analyse routing, severity
calculation, priority/backlog boost, effort estimation, past-attempt
counting, description generation, and priority ranking.

Source: src/thegent/governance/analyzer.py

@trace AUDIT-N+76  FR-GOV-AN-001..015
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from thegent.governance.analyzer import (
    Finding,
    HealthAnalyzer,
    _count_past_attempts,
    _describe,
)
from thegent.governance.scanner import DimensionScan, ScanResult

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

_VALID_TARGETS: dict[str, Any] = {
    "dimensions": {
        "test_coverage": {
            "direction": "higher_is_better",
            "target": 80.0,
            "weight": 1.0,
        },
        "lint_violations": {
            "direction": "lower_is_better",
            "target": 0.0,
            "weight": 1.5,
        },
        "doc_organization": {
            "direction": "higher_is_better",
            "target": 90.0,
            "weight": 0.5,
        },
        "complexity_index": {
            "direction": "lower_is_better",
            "target": 5.0,
            "weight": 2.0,
        },
    }
}


def _write_targets(path: Path, data: dict[str, Any] | None = None) -> Path:
    """Write a health-targets JSON file and return the path."""
    target = path / "health_targets.json"
    target.write_text(json.dumps(data or _VALID_TARGETS))
    return target


def _make_scan(
    dimension: str,
    current: float,
    target: float,
    *,
    delta: float | None = None,
    affected_files: list[str] | None = None,
) -> DimensionScan:
    """Shorthand for a DimensionScan."""
    return DimensionScan(
        dimension=dimension,
        current_value=current,
        target_value=target,
        delta=delta if delta is not None else current - target,
        affected_files=affected_files or [],
    )


def _make_result(dimensions: dict[str, DimensionScan]) -> ScanResult:
    """Shorthand for a ScanResult."""
    return ScanResult(dimensions=dimensions)


# ---------------------------------------------------------------------------
# FR-GOV-AN-001
# ---------------------------------------------------------------------------


class TestFRGOVAN001FindingFieldDefaults:
    def test_finding_id_is_auto_generated(self) -> None:
        f1 = Finding(
            dimension="d",
            severity=0.5,
            priority=1.0,
            current_value=0,
            target_value=1,
            delta=1,
            description="x",
        )
        f2 = Finding(
            dimension="d",
            severity=0.5,
            priority=1.0,
            current_value=0,
            target_value=1,
            delta=1,
            description="x",
        )
        assert f1.finding_id.startswith("f_")
        assert f1.finding_id != f2.finding_id

    def test_affected_files_defaults_empty(self) -> None:
        f = Finding(
            dimension="d",
            severity=0.5,
            priority=1.0,
            current_value=0,
            target_value=1,
            delta=1,
            description="x",
        )
        assert f.affected_files == []

    def test_estimated_effort_defaults_to_one(self) -> None:
        f = Finding(
            dimension="d",
            severity=0.5,
            priority=1.0,
            current_value=0,
            target_value=1,
            delta=1,
            description="x",
        )
        assert f.estimated_effort_tool_calls == 1


# ---------------------------------------------------------------------------
# FR-GOV-AN-002
# ---------------------------------------------------------------------------


class TestFRGOVAN002FindingSeverityBounds:
    def test_severity_at_zero(self) -> None:
        f = Finding(
            dimension="d",
            severity=0.0,
            priority=1.0,
            current_value=0,
            target_value=1,
            delta=1,
            description="x",
        )
        assert f.severity == 0.0

    def test_severity_at_one(self) -> None:
        f = Finding(
            dimension="d",
            severity=1.0,
            priority=1.0,
            current_value=0,
            target_value=1,
            delta=1,
            description="x",
        )
        assert f.severity == 1.0

    def test_severity_below_zero_rejected(self) -> None:
        with pytest.raises(Exception):
            Finding(
                dimension="d",
                severity=-0.1,
                priority=1.0,
                current_value=0,
                target_value=1,
                delta=1,
                description="x",
            )

    def test_severity_above_one_rejected(self) -> None:
        with pytest.raises(Exception):
            Finding(
                dimension="d",
                severity=1.1,
                priority=1.0,
                current_value=0,
                target_value=1,
                delta=1,
                description="x",
            )


# ---------------------------------------------------------------------------
# FR-GOV-AN-003
# ---------------------------------------------------------------------------


class TestFRGOVAN003FindingPriorityBounds:
    def test_priority_at_zero(self) -> None:
        f = Finding(
            dimension="d",
            severity=0.5,
            priority=0.0,
            current_value=0,
            target_value=1,
            delta=1,
            description="x",
        )
        assert f.priority == 0.0

    def test_priority_positive(self) -> None:
        f = Finding(
            dimension="d",
            severity=0.5,
            priority=5.0,
            current_value=0,
            target_value=1,
            delta=1,
            description="x",
        )
        assert f.priority == 5.0

    def test_priority_negative_rejected(self) -> None:
        with pytest.raises(Exception):
            Finding(
                dimension="d",
                severity=0.5,
                priority=-1.0,
                current_value=0,
                target_value=1,
                delta=1,
                description="x",
            )


# ---------------------------------------------------------------------------
# FR-GOV-AN-004
# ---------------------------------------------------------------------------


class TestFRGOVAN004HealthAnalyzerInitLoadsTargets:
    def test_loads_dimensions(self, tmp_path: Path) -> None:
        path = _write_targets(tmp_path)
        ha = HealthAnalyzer(path)
        assert "test_coverage" in ha._targets
        assert "lint_violations" in ha._targets
        assert len(ha._targets) == 4


# ---------------------------------------------------------------------------
# FR-GOV-AN-005
# ---------------------------------------------------------------------------


class TestFRGOVAN005HealthAnalyzerInitMissingFileRaises:
    def test_file_not_found(self, tmp_path: Path) -> None:
        missing = tmp_path / "nonexistent.json"
        with pytest.raises(FileNotFoundError, match="not found"):
            HealthAnalyzer(missing)

    def test_invalid_json_raises_valueerror(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.json"
        bad.write_text("{{not valid json")
        with pytest.raises(ValueError, match="not valid JSON"):
            HealthAnalyzer(bad)


# ---------------------------------------------------------------------------
# FR-GOV-AN-006
# ---------------------------------------------------------------------------


class TestFRGOVAN006AnalyzeExcludesGreenDimensions:
    def test_green_higher_is_better_excluded(self, tmp_path: Path) -> None:
        path = _write_targets(tmp_path)
        ha = HealthAnalyzer(path)
        scan = _make_scan("test_coverage", current=85.0, target=80.0)
        result = _make_result({"test_coverage": scan})
        findings = ha.analyze(result)
        assert all(f.dimension != "test_coverage" for f in findings)

    def test_green_lower_is_better_excluded(self, tmp_path: Path) -> None:
        path = _write_targets(tmp_path)
        ha = HealthAnalyzer(path)
        scan = _make_scan("lint_violations", current=0.0, target=0.0)
        result = _make_result({"lint_violations": scan})
        findings = ha.analyze(result)
        assert all(f.dimension != "lint_violations" for f in findings)


# ---------------------------------------------------------------------------
# FR-GOV-AN-007
# ---------------------------------------------------------------------------


class TestFRGOVAN007AnalyzeSeverityHigherIsBetter:
    def test_severity_calculation(self, tmp_path: Path) -> None:
        path = _write_targets(tmp_path)
        ha = HealthAnalyzer(path)
        # current=40, target=80 → severity = max(0, 1 - 40/80) = 0.5
        scan = _make_scan("test_coverage", current=40.0, target=80.0)
        result = _make_result({"test_coverage": scan})
        findings = ha.analyze(result)
        assert len(findings) == 1
        assert findings[0].severity == pytest.approx(0.5, abs=0.001)


# ---------------------------------------------------------------------------
# FR-GOV-AN-008
# ---------------------------------------------------------------------------


class TestFRGOVAN008AnalyzeSeverityLowerIsBetter:
    def test_severity_calculation_nonzero_target(self, tmp_path: Path) -> None:
        path = _write_targets(tmp_path)
        ha = HealthAnalyzer(path)
        # scanner dimension 'technical_debt' → target key 'complexity_index'
        # target=5.0 (lower_is_better), current=10.0 → severity = min(1, 10/5) = 1.0
        scan = _make_scan("technical_debt", current=10.0, target=5.0)
        result = _make_result({"technical_debt": scan})
        findings = ha.analyze(result)
        assert len(findings) == 1
        assert findings[0].severity == pytest.approx(1.0, abs=0.001)

    def test_severity_calculation_zero_target(self, tmp_path: Path) -> None:
        path = _write_targets(tmp_path)
        ha = HealthAnalyzer(path)
        # current=5, target=0 → severity = min(1, 5/10) = 0.5
        scan = _make_scan("lint_violations", current=5.0, target=0.0)
        result = _make_result({"lint_violations": scan})
        findings = ha.analyze(result)
        assert len(findings) == 1
        assert findings[0].severity == pytest.approx(0.5, abs=0.001)


# ---------------------------------------------------------------------------
# FR-GOV-AN-009
# ---------------------------------------------------------------------------


class TestFRGOVAN009AnalyzePriorityIncludesBacklogBoost:
    def test_priority_increases_with_attempts(self, tmp_path: Path) -> None:
        path = _write_targets(tmp_path)
        ha = HealthAnalyzer(path)
        scan = _make_scan("test_coverage", current=40.0, target=80.0)
        result = _make_result({"test_coverage": scan})
        baseline = ha.analyze(result)
        assert len(baseline) == 1
        base_priority = baseline[0].priority

        backlog = [
            {"dimension": "test_coverage"},
            {"dimension": "test_coverage"},
        ]
        boosted = ha.analyze(result, backlog_items=backlog)
        assert len(boosted) == 1
        # 2 past attempts → multiplier = 1 + 0.1 * 2 = 1.2
        assert boosted[0].priority == pytest.approx(base_priority * 1.2, abs=0.01)


# ---------------------------------------------------------------------------
# FR-GOV-AN-010
# ---------------------------------------------------------------------------


class TestFRGOVAN010EstimateEffortKnownDimension:
    def test_known_returns_table_value(self) -> None:
        assert HealthAnalyzer._estimate_effort("test_coverage") == 2
        assert HealthAnalyzer._estimate_effort("lint_violations") == 1
        assert HealthAnalyzer._estimate_effort("technical_debt") == 3


# ---------------------------------------------------------------------------
# FR-GOV-AN-011
# ---------------------------------------------------------------------------


class TestFRGOVAN011EstimateEffortUnknownDefaults:
    def test_unknown_returns_three(self) -> None:
        assert HealthAnalyzer._estimate_effort("nonexistent_dimension") == 3


# ---------------------------------------------------------------------------
# FR-GOV-AN-012
# ---------------------------------------------------------------------------


class TestFRGOVAN012CountPastAttemptsTallies:
    def test_counts_per_dimension(self) -> None:
        backlog = [
            {"dimension": "test_coverage"},
            {"dimension": "lint_violations"},
            {"dimension": "test_coverage"},
            {"dimension": "test_coverage"},
        ]
        counts = _count_past_attempts(backlog)
        assert counts["test_coverage"] == 3
        assert counts["lint_violations"] == 1

    def test_skips_entries_without_dimension(self) -> None:
        backlog = [{"dimension": "x"}, {"other_key": "y"}, {}]
        counts = _count_past_attempts(backlog)
        assert counts == {"x": 1}


# ---------------------------------------------------------------------------
# FR-GOV-AN-013
# ---------------------------------------------------------------------------


class TestFRGOVAN013DescribeReturnsKnownDescriptions:
    def test_known_dimension(self) -> None:
        scan = _make_scan("test_coverage", current=60.0, target=80.0)
        desc = _describe("test_coverage", scan)
        assert "60%" in desc
        assert "80%" in desc
        assert "Test coverage" in desc

    def test_lint_violations(self) -> None:
        scan = _make_scan("lint_violations", current=7.0, target=0.0)
        desc = _describe("lint_violations", scan)
        assert "7" in desc
        assert "lint violation" in desc


# ---------------------------------------------------------------------------
# FR-GOV-AN-014
# ---------------------------------------------------------------------------


class TestFRGOVAN014DescribeReturnsFallback:
    def test_unknown_dimension_returns_fallback(self) -> None:
        scan = _make_scan("custom_metric", current=3.0, target=10.0)
        desc = _describe("custom_metric", scan)
        assert "custom_metric" in desc
        assert "3.0" in desc
        assert "10.0" in desc


# ---------------------------------------------------------------------------
# FR-GOV-AN-015
# ---------------------------------------------------------------------------


class TestFRGOVAN015FindingsSortedByPriorityDescending:
    def test_sorted_highest_first(self, tmp_path: Path) -> None:
        # Use scanner dimension names mapped via _SCANNER_TO_TARGET.
        # test_coverage → target key test_coverage (higher_is_better, weight=1.0)
        # lint_violations → target key lint_violations (lower_is_better, weight=1.5)
        targets = {
            "dimensions": {
                "test_coverage": {
                    "direction": "higher_is_better",
                    "target": 100.0,
                    "weight": 1.0,
                },
                "lint_violations": {
                    "direction": "lower_is_better",
                    "target": 0.0,
                    "weight": 1.5,
                },
            }
        }
        path = _write_targets(tmp_path, targets)
        ha = HealthAnalyzer(path)
        # test_coverage: current=50, target=100 → severity 0.5, priority = 0.5*1.0 = 0.5
        # lint_violations: current=5, target=0 → severity 0.5, priority = 0.5*1.5 = 0.75
        result = _make_result(
            {
                "test_coverage": _make_scan("test_coverage", current=50.0, target=100.0),
                "lint_violations": _make_scan("lint_violations", current=5.0, target=0.0),
            }
        )
        findings = ha.analyze(result)
        assert len(findings) == 2
        assert findings[0].priority >= findings[1].priority
        assert findings[0].dimension == "lint_violations"
        assert findings[1].dimension == "test_coverage"
