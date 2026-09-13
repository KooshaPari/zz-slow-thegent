"""AUDIT-N+69: governance/slo_metrics hardening spec (SOTA pass-69).

22 invariants FR-GOV-SLO-001..022 covering SloMetric dataclass shape,
SloThresholds immutability and defaults, evaluate-field helpers,
module-level evaluate(), SloEmitter output/emit/evaluate delegation,
and timestamp ISO-8601 validity.

Source: src/thegent/governance/slo_metrics.py

@trace AUDIT-N+69  FR-GOV-SLO-001..022
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import ClassVar

import pytest

from thegent.governance.slo_metrics import (
    SloEmitter,
    SloMetric,
    SloThresholds,
    _evaluate_field_higher_is_better,
    _evaluate_field_lower_is_better,
    evaluate,
)

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _green_metric() -> SloMetric:
    """Return a metric where every field is in the green zone."""
    return SloMetric(
        file_loc=500.0,
        function_loc_p95=30.0,
        impl_importers=5.0,
        cross_boundary_import_edges=2.0,
        cli_help_p95_ms=80.0,
        run_command_p95_ms=200.0,
        decomposition_checkpoint_pass_rate=1.0,
    )


def _red_metric() -> SloMetric:
    """Return a metric where every field is in the red zone."""
    return SloMetric(
        file_loc=2500.0,
        function_loc_p95=200.0,
        impl_importers=50.0,
        cross_boundary_import_edges=60.0,
        cli_help_p95_ms=600.0,
        run_command_p95_ms=1200.0,
        decomposition_checkpoint_pass_rate=0.80,
    )


# ---------------------------------------------------------------------------
# FR-GOV-SLO-001 / FR-GOV-SLO-002 -- SloMetric shape and defaults
# ---------------------------------------------------------------------------


class TestSloMetricShape:
    """FR-GOV-SLO-001/002."""

    def test_has_7_numeric_fields_plus_timestamp_and_source(self) -> None:
        m = SloMetric(
            file_loc=1.0,
            function_loc_p95=2.0,
            impl_importers=3.0,
            cross_boundary_import_edges=4.0,
            cli_help_p95_ms=5.0,
            run_command_p95_ms=6.0,
            decomposition_checkpoint_pass_rate=7.0,
        )
        assert m.file_loc == 1.0
        assert m.function_loc_p95 == 2.0
        assert m.impl_importers == 3.0
        assert m.cross_boundary_import_edges == 4.0
        assert m.cli_help_p95_ms == 5.0
        assert m.run_command_p95_ms == 6.0
        assert m.decomposition_checkpoint_pass_rate == 7.0

    def test_defaults_source_and_timestamp(self) -> None:
        m = SloMetric(
            file_loc=0.0,
            function_loc_p95=0.0,
            impl_importers=0.0,
            cross_boundary_import_edges=0.0,
            cli_help_p95_ms=0.0,
            run_command_p95_ms=0.0,
            decomposition_checkpoint_pass_rate=1.0,
        )
        assert m.source == "unknown"
        assert isinstance(m.timestamp, str)
        # Verify it parses as valid ISO-8601
        dt = datetime.fromisoformat(m.timestamp.replace("Z", "+00:00"))
        assert dt.tzinfo is not None


# ---------------------------------------------------------------------------
# FR-GOV-SLO-003 / FR-GOV-SLO-004 / FR-GOV-SLO-005 / FR-GOV-SLO-006
# SloThresholds immutability and defaults
# ---------------------------------------------------------------------------


class TestSloThresholdsDefaults:
    """FR-GOV-SLO-003/004/005/006."""

    def test_is_frozen(self) -> None:
        t = SloThresholds()
        with pytest.raises(AttributeError):
            t.file_loc_green_max = 999.0  # type: ignore[misc]

    def test_file_loc_green_max_default(self) -> None:
        assert SloThresholds().file_loc_green_max == 1200.0

    def test_file_loc_red_min_default(self) -> None:
        assert SloThresholds().file_loc_red_min == 1800.0

    def test_function_loc_p95_green_max_default(self) -> None:
        assert SloThresholds().function_loc_p95_green_max == 80.0


# ---------------------------------------------------------------------------
# FR-GOV-SLO-007 / FR-GOV-SLO-008 / FR-GOV-SLO-009
# _evaluate_field_lower_is_better
# ---------------------------------------------------------------------------


class TestEvalLowerIsBetter:
    """FR-GOV-SLO-007/008/009."""

    def test_green_when_below_green_max(self) -> None:
        assert _evaluate_field_lower_is_better(500.0, 1200.0, 1800.0) == "green"

    def test_green_at_boundary(self) -> None:
        assert _evaluate_field_lower_is_better(1200.0, 1200.0, 1800.0) == "green"

    def test_red_when_above_red_min(self) -> None:
        assert _evaluate_field_lower_is_better(2000.0, 1200.0, 1800.0) == "red"

    def test_red_at_boundary(self) -> None:
        assert _evaluate_field_lower_is_better(1800.0, 1200.0, 1800.0) == "red"

    def test_yellow_between(self) -> None:
        assert _evaluate_field_lower_is_better(1500.0, 1200.0, 1800.0) == "yellow"


# ---------------------------------------------------------------------------
# FR-GOV-SLO-010 / FR-GOV-SLO-011 / FR-GOV-SLO-012
# _evaluate_field_higher_is_better
# ---------------------------------------------------------------------------


class TestEvalHigherIsBetter:
    """FR-GOV-SLO-010/011/012."""

    def test_green_when_above_green_min(self) -> None:
        assert _evaluate_field_higher_is_better(1.0, 1.0, 0.95) == "green"

    def test_green_above_threshold(self) -> None:
        assert _evaluate_field_higher_is_better(1.05, 1.0, 0.95) == "green"

    def test_red_when_below_red_max(self) -> None:
        assert _evaluate_field_higher_is_better(0.80, 1.0, 0.95) == "red"

    def test_red_at_boundary(self) -> None:
        assert _evaluate_field_higher_is_better(0.95, 1.0, 0.95) == "red"

    def test_yellow_between(self) -> None:
        assert _evaluate_field_higher_is_better(0.97, 1.0, 0.95) == "yellow"


# ---------------------------------------------------------------------------
# FR-GOV-SLO-013 / FR-GOV-SLO-014 / FR-GOV-SLO-015 / FR-GOV-SLO-016
# evaluate() — keys, all-green, all-red, mixed
# ---------------------------------------------------------------------------


class TestEvaluate:
    """FR-GOV-SLO-013/014/015/016."""

    _EXPECTED_KEYS: ClassVar[set[str]] = {
        "file_loc",
        "function_loc_p95",
        "impl_importers",
        "cross_boundary_import_edges",
        "cli_help_p95_ms",
        "run_command_p95_ms",
        "decomposition_checkpoint_pass_rate",
    }

    def test_returns_all_7_keys(self) -> None:
        result = evaluate(_green_metric(), SloThresholds())
        assert set(result.keys()) == self._EXPECTED_KEYS

    def test_all_green_metric(self) -> None:
        result = evaluate(_green_metric(), SloThresholds())
        assert all(v == "green" for v in result.values())

    def test_all_red_metric(self) -> None:
        result = evaluate(_red_metric(), SloThresholds())
        assert all(v == "red" for v in result.values())

    def test_mixed_statuses(self) -> None:
        m = SloMetric(
            file_loc=500.0,  # green (lower is better)
            function_loc_p95=100.0,  # yellow (between 80 and 120)
            impl_importers=50.0,  # red (>= 35)
            cross_boundary_import_edges=2.0,  # green
            cli_help_p95_ms=300.0,  # yellow (between 250 and 400)
            run_command_p95_ms=200.0,  # green
            decomposition_checkpoint_pass_rate=0.97,  # yellow (between 0.95 and 1.0)
        )
        result = evaluate(m, SloThresholds())
        assert result["file_loc"] == "green"
        assert result["function_loc_p95"] == "yellow"
        assert result["impl_importers"] == "red"
        assert result["cross_boundary_import_edges"] == "green"
        assert result["cli_help_p95_ms"] == "yellow"
        assert result["run_command_p95_ms"] == "green"
        assert result["decomposition_checkpoint_pass_rate"] == "yellow"


# ---------------------------------------------------------------------------
# FR-GOV-SLO-017 / FR-GOV-SLO-018 / FR-GOV-SLO-019
# SloEmitter output_path, emit file creation, emit mkdir
# ---------------------------------------------------------------------------


class TestSloEmitter:
    """FR-GOV-SLO-017/018/019."""

    def test_output_path_returns_configured_path(self) -> None:
        p = Path("/tmp/test-slo.jsonl")
        emitter = SloEmitter(output_path=p)
        assert emitter.output_path == p

    def test_emit_creates_jsonl_file(self, tmp_path: Path) -> None:
        out = tmp_path / "metrics.jsonl"
        emitter = SloEmitter(output_path=out)
        m = _green_metric()
        emitter.emit(m)
        assert out.exists()
        lines = out.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["file_loc"] == 500.0

    def test_emit_creates_parent_directories(self, tmp_path: Path) -> None:
        out = tmp_path / "nested" / "dir" / "metrics.jsonl"
        emitter = SloEmitter(output_path=out)
        emitter.emit(_green_metric())
        assert out.exists()


# ---------------------------------------------------------------------------
# FR-GOV-SLO-020 -- SloEmitter.evaluate delegates to module-level evaluate()
# ---------------------------------------------------------------------------


class TestSloEmitterEvaluate:
    """FR-GOV-SLO-020."""

    def test_delegates_to_module_level_evaluate(self) -> None:
        emitter = SloEmitter()
        m = _green_metric()
        t = SloThresholds()
        result = emitter.evaluate(m, t)
        assert result == evaluate(m, t)


# ---------------------------------------------------------------------------
# FR-GOV-SLO-021 -- decomposition_checkpoint_pass_rate default behavior
# ---------------------------------------------------------------------------


class TestCheckpointPassRate:
    """FR-GOV-SLO-021."""

    def test_perfect_rate_is_green(self) -> None:
        assert _evaluate_field_higher_is_better(1.0, 1.0, 0.95) == "green"

    def test_low_rate_is_red(self) -> None:
        assert _evaluate_field_higher_is_better(0.90, 1.0, 0.95) == "red"

    def test_boundary_rate_is_yellow(self) -> None:
        # 0.96 is between red_max=0.95 and green_min=1.0
        assert _evaluate_field_higher_is_better(0.96, 1.0, 0.95) == "yellow"


# ---------------------------------------------------------------------------
# FR-GOV-SLO-022 -- timestamp format is valid ISO-8601
# ---------------------------------------------------------------------------


class TestTimestampFormat:
    """FR-GOV-SLO-022."""

    def test_timestamp_is_valid_iso(self) -> None:
        m = SloMetric(
            file_loc=0.0,
            function_loc_p95=0.0,
            impl_importers=0.0,
            cross_boundary_import_edges=0.0,
            cli_help_p95_ms=0.0,
            run_command_p95_ms=0.0,
            decomposition_checkpoint_pass_rate=1.0,
        )
        dt = datetime.fromisoformat(m.timestamp.replace("Z", "+00:00"))
        assert dt.tzinfo is not None
        assert dt.year >= 2024

    def test_custom_timestamp_preserved(self) -> None:
        custom_ts = "2025-01-15T12:00:00+00:00"
        m = SloMetric(
            file_loc=0.0,
            function_loc_p95=0.0,
            impl_importers=0.0,
            cross_boundary_import_edges=0.0,
            cli_help_p95_ms=0.0,
            run_command_p95_ms=0.0,
            decomposition_checkpoint_pass_rate=1.0,
            timestamp=custom_ts,
        )
        assert m.timestamp == custom_ts
