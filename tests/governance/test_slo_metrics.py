"""Tests for slo_metrics module (WL-135 B90-W2-A5).

Covers: SloMetric, SloThresholds, SloEmitter, evaluate().
"""
# @trace WL-135 B90-W2-A5

from __future__ import annotations

from pathlib import Path

import orjson as json
import pytest

from thegent.governance.slo_metrics import (
    SloEmitter,
    SloMetric,
    SloThresholds,
    evaluate,
)

# --- Helpers ---


def _make_green_metric(**overrides: object) -> SloMetric:
    """Return a metric that is green on all thresholds."""
    defaults = {
        "file_loc": 800.0,
        "function_loc_p95": 40.0,
        "impl_importers": 10.0,
        "cross_boundary_import_edges": 12.0,
        "cli_help_p95_ms": 150.0,
        "run_command_p95_ms": 300.0,
        "decomposition_checkpoint_pass_rate": 1.0,
        "source": "test",
    }
    defaults.update(overrides)
    return SloMetric(**defaults)


def _make_red_metric(**overrides: object) -> SloMetric:
    """Return a metric that is red on all thresholds."""
    defaults = {
        "file_loc": 2000.0,
        "function_loc_p95": 150.0,
        "impl_importers": 40.0,
        "cross_boundary_import_edges": 50.0,
        "cli_help_p95_ms": 500.0,
        "run_command_p95_ms": 900.0,
        "decomposition_checkpoint_pass_rate": 0.90,
        "source": "test",
    }
    defaults.update(overrides)
    return SloMetric(**defaults)


_DEFAULT_THRESHOLDS = SloThresholds()


# --- SloMetric dataclass tests ---


def test_slo_metric_has_all_schema_fields() -> None:
    """SloMetric must define all schema fields from Wave-1 A4."""
    m = _make_green_metric()
    assert hasattr(m, "file_loc")
    assert hasattr(m, "function_loc_p95")
    assert hasattr(m, "impl_importers")
    assert hasattr(m, "cross_boundary_import_edges")
    assert hasattr(m, "cli_help_p95_ms")
    assert hasattr(m, "run_command_p95_ms")
    assert hasattr(m, "decomposition_checkpoint_pass_rate")
    assert hasattr(m, "timestamp")
    assert hasattr(m, "source")


def test_slo_metric_timestamp_defaults_to_utc_iso() -> None:
    """SloMetric.timestamp must default to a non-empty ISO-format string."""
    m = _make_green_metric()
    assert isinstance(m.timestamp, str)
    assert len(m.timestamp) >= 20  # e.g. 2026-02-21T00:00:00+00:00


def test_slo_metric_source_field_set_correctly() -> None:
    """SloMetric.source must store the provided value."""
    m = SloMetric(
        file_loc=1000,
        function_loc_p95=60,
        impl_importers=15,
        cross_boundary_import_edges=18,
        cli_help_p95_ms=200,
        run_command_p95_ms=400,
        decomposition_checkpoint_pass_rate=1.0,
        source="ci-pipeline",
    )
    assert m.source == "ci-pipeline"


# --- SloThresholds tests ---


def test_slo_thresholds_default_values_match_wave1_spec() -> None:
    """SloThresholds defaults must match Wave-1 A4 artifact thresholds."""
    t = SloThresholds()
    assert t.file_loc_green_max == 1200.0
    assert t.file_loc_red_min == 1800.0
    assert t.function_loc_p95_green_max == 80.0
    assert t.function_loc_p95_red_min == 120.0
    assert t.impl_importers_green_max == 20.0
    assert t.impl_importers_red_min == 35.0
    assert t.cross_boundary_import_edges_green_max == 25.0
    assert t.cross_boundary_import_edges_red_min == 40.0
    assert t.cli_help_p95_ms_green_max == 250.0
    assert t.cli_help_p95_ms_red_min == 400.0
    assert t.run_command_p95_ms_green_max == 500.0
    assert t.run_command_p95_ms_red_min == 800.0
    assert t.decomposition_checkpoint_pass_rate_green_min == 1.0
    assert t.decomposition_checkpoint_pass_rate_red_max == 0.95


# --- evaluate() tests ---


def test_evaluate_all_green_for_healthy_metric() -> None:
    """evaluate() must return all 'green' for a metric within green bounds."""
    result = evaluate(_make_green_metric(), _DEFAULT_THRESHOLDS)
    for field_name, status in result.items():
        assert status == "green", f"Expected green for {field_name}, got {status}"


def test_evaluate_all_red_for_degraded_metric() -> None:
    """evaluate() must return all 'red' for a metric beyond red thresholds."""
    result = evaluate(_make_red_metric(), _DEFAULT_THRESHOLDS)
    for field_name, status in result.items():
        assert status == "red", f"Expected red for {field_name}, got {status}"


def test_evaluate_yellow_zone_file_loc() -> None:
    """file_loc between 1200 and 1800 must be 'yellow'."""
    m = _make_green_metric(file_loc=1500.0)
    result = evaluate(m, _DEFAULT_THRESHOLDS)
    assert result["file_loc"] == "yellow"


def test_evaluate_red_trigger_file_loc_at_boundary() -> None:
    """file_loc at exactly red_min (1800) must be 'red'."""
    m = _make_green_metric(file_loc=1800.0)
    result = evaluate(m, _DEFAULT_THRESHOLDS)
    assert result["file_loc"] == "red"


def test_evaluate_green_file_loc_at_boundary() -> None:
    """file_loc at exactly green_max (1200) must be 'green'."""
    m = _make_green_metric(file_loc=1200.0)
    result = evaluate(m, _DEFAULT_THRESHOLDS)
    assert result["file_loc"] == "green"


def test_evaluate_checkpoint_pass_rate_yellow_zone() -> None:
    """Pass rate between 0.95 and 1.0 must be 'yellow'."""
    m = _make_green_metric(decomposition_checkpoint_pass_rate=0.97)
    result = evaluate(m, _DEFAULT_THRESHOLDS)
    assert result["decomposition_checkpoint_pass_rate"] == "yellow"


def test_evaluate_checkpoint_pass_rate_red_at_boundary() -> None:
    """Pass rate at exactly 0.95 must be 'red'."""
    m = _make_green_metric(decomposition_checkpoint_pass_rate=0.95)
    result = evaluate(m, _DEFAULT_THRESHOLDS)
    assert result["decomposition_checkpoint_pass_rate"] == "red"


def test_evaluate_returns_dict_with_all_seven_fields() -> None:
    """evaluate() must return exactly 7 keys (one per metric field)."""
    result = evaluate(_make_green_metric(), _DEFAULT_THRESHOLDS)
    expected_keys = {
        "file_loc",
        "function_loc_p95",
        "impl_importers",
        "cross_boundary_import_edges",
        "cli_help_p95_ms",
        "run_command_p95_ms",
        "decomposition_checkpoint_pass_rate",
    }
    assert set(result.keys()) == expected_keys


# --- SloEmitter tests ---


def test_emit_writes_valid_jsonl_line(tmp_path: Path) -> None:
    """SloEmitter.emit must append a valid JSONL line to the output file."""
    out = tmp_path / "slo-metrics.jsonl"
    emitter = SloEmitter(output_path=out)
    metric = _make_green_metric(source="emitter-test")

    emitter.emit(metric)

    assert out.exists()
    lines = out.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1

    row = json.loads(lines[0])
    assert row["source"] == "emitter-test"
    assert row["file_loc"] == pytest.approx(800.0)


def test_emit_appends_multiple_records(tmp_path: Path) -> None:
    """SloEmitter.emit must append (not overwrite) on successive calls."""
    out = tmp_path / "slo-metrics.jsonl"
    emitter = SloEmitter(output_path=out)

    emitter.emit(_make_green_metric(source="first"))
    emitter.emit(_make_red_metric(source="second"))

    lines = out.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2

    first = json.loads(lines[0])
    second = json.loads(lines[1])
    assert first["source"] == "first"
    assert second["source"] == "second"


def test_emitter_evaluate_delegates_to_module_evaluate(tmp_path: Path) -> None:
    """SloEmitter.evaluate must return same result as module-level evaluate()."""
    emitter = SloEmitter(output_path=tmp_path / "x.jsonl")
    m = _make_green_metric()
    t = _DEFAULT_THRESHOLDS
    assert emitter.evaluate(m, t) == evaluate(m, t)


def test_emitter_output_path_property(tmp_path: Path) -> None:
    """SloEmitter.output_path must return the path passed at construction."""
    p = tmp_path / "custom.jsonl"
    emitter = SloEmitter(output_path=p)
    assert emitter.output_path == p


def test_emitter_creates_parent_directory(tmp_path: Path) -> None:
    """SloEmitter.emit must create parent directories if missing."""
    out = tmp_path / "nested" / "dir" / "slo.jsonl"
    emitter = SloEmitter(output_path=out)
    emitter.emit(_make_green_metric())
    assert out.exists()


def test_emitter_jsonl_row_contains_timestamp(tmp_path: Path) -> None:
    """Emitted JSONL row must include a timestamp field."""
    out = tmp_path / "slo.jsonl"
    emitter = SloEmitter(output_path=out)
    emitter.emit(_make_green_metric())
    row = json.loads(out.read_text(encoding="utf-8").strip())
    assert "timestamp" in row
    assert len(row["timestamp"]) >= 20
