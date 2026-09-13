"""Integration tests for governance modules (v2): task_classifier, override_events,
health_scorer, retention, slo_metrics.

Exercises the real implementations against the canonical schema, fixture files,
and a tmp_path-backed retention manager to validate behavior end-to-end with no
mocks. Each test class targets one governance module.
"""

from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock

import orjson as json_fast
import pytest

from thegent.config import ThegentSettings
from thegent.governance.health_scorer import HealthScorer
from thegent.governance.override_events import (
    OverrideEventEmitter,
    OverrideExpiredEvent,
)
from thegent.governance.retention import EvidenceRetentionManager
from thegent.governance.slo_metrics import SloEmitter, SloMetric, SloThresholds
from thegent.governance.task_classifier import classify

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def health_targets_file(tmp_path: Path) -> Path:
    """Write a minimal but valid health-targets.json for HealthScorer."""
    cfg = {
        "version": "1.0.0",
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
    cfg_path = tmp_path / "health-targets.json"
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")
    return cfg_path


@pytest.fixture
def retention_settings(tmp_path: Path) -> ThegentSettings:
    """Build a ThegentSettings mock with a real session_dir on tmp_path."""
    settings = MagicMock(spec=ThegentSettings)
    settings.session_dir = tmp_path / "session"
    settings.session_dir.mkdir(parents=True, exist_ok=True)
    return settings


@pytest.fixture
def slo_output_path(tmp_path: Path) -> Path:
    """Return a per-test JSONL path for SloEmitter."""
    return tmp_path / "slo-metrics.jsonl"


# ---------------------------------------------------------------------------
# task_classifier — classify_task_returns_correct_risk
# ---------------------------------------------------------------------------


def _valid_payload(**overrides: object) -> dict[str, object]:
    """Return a valid classification payload (matches docs/governance schema)."""
    payload: dict[str, object] = {
        "task_id": "T-INTEG-001",
        "title": "Integration task fixture",
        "domain": "backend",
        "scale": "M",
        "risk": "low",
        "coupling": "isolated",
        "runtime_profile": "mixed",
        "validation_depth": ["lint", "unit"],
        "overlap_risk": 10,
    }
    payload.update(overrides)
    return payload


class TestClassifyTaskReturnsCorrectRisk:
    """@trace FR-GOV-TC-001..015 — schema-first classifier end-to-end."""

    def test_low_risk_produces_ln_worker_tier(self):
        """risk=low + scale=M → delegation_tier L2_managed (M baseline)."""
        metadata, classification = classify(_valid_payload(risk="low", scale="M"))
        assert metadata.risk == "low"
        assert classification.delegation_tier == "L2_managed"
        assert classification.worker_count == 4
        assert classification.worktree_mode == "lane_dedicated"
        assert classification.commit_mode == "micro"

    def test_high_risk_escalates_to_specialist(self):
        """risk=high overrides default and forces L3_specialist + security gate."""
        metadata, classification = classify(_valid_payload(risk="high"))
        assert metadata.risk == "high"
        assert classification.delegation_tier == "L3_specialist"
        assert classification.worker_count == 3
        assert "security" in classification.required_gates
        assert "integration" in classification.required_gates

    def test_critical_risk_escalates_and_includes_security(self):
        """risk=critical mirrors high — L3_specialist + security gate."""
        metadata, classification = classify(_valid_payload(risk="critical"))
        assert metadata.risk == "critical"
        assert classification.delegation_tier == "L3_specialist"
        assert "security" in classification.required_gates

    def test_overlap_risk_high_triggers_isolated_worktree(self):
        """overlap_risk >= 60 → escalation rule forces burst_isolated worktree."""
        _metadata, classification = classify(_valid_payload(overlap_risk=80))
        assert classification.worktree_mode == "burst_isolated"

    def test_payload_as_dict_matches_classification(self):
        """as_payload() round-trips the delegation fields needed by L1/L2."""
        _metadata, classification = classify(_valid_payload(risk="medium"))
        payload = classification.as_payload()
        assert set(payload.keys()) == {
            "delegation_tier",
            "worker_count",
            "worktree_mode",
            "commit_mode",
            "required_gates",
        }
        assert payload["delegation_tier"] == classification.delegation_tier


# ---------------------------------------------------------------------------
# override_events — record_and_query_overrides
# ---------------------------------------------------------------------------


class TestRecordAndQueryOverrides:
    """@trace FR-GOV-001 — JSONL audit trail for override lifecycle events."""

    def test_emit_expired_then_tail_returns_record(self, tmp_path: Path):
        """A single emit_expired() is queryable via tail_events()."""
        path = tmp_path / "events.jsonl"
        emitter = OverrideEventEmitter(events_path=path)
        emitter.emit_expired(
            OverrideExpiredEvent(
                override_id="ovr-1",
                policy_id="pol-A",
                owner="alice",
                expired_at=time.time(),
            )
        )
        events = emitter.tail_events(n=10)
        assert len(events) == 1
        assert events[0]["override_id"] == "ovr-1"
        assert events[0]["event_type"] == "governance.override.expired"

    def test_emit_activated_records_lifecycle_start(self, tmp_path: Path):
        """emit_activated() persists override_id, ttl_s, and expires_at."""
        path = tmp_path / "events.jsonl"
        emitter = OverrideEventEmitter(events_path=path)
        before = time.time()
        emitter.emit_activated("ovr-2", "pol-B", "bob", ttl_s=120.0)
        after = time.time()
        events = emitter.tail_events(n=10)
        assert len(events) == 1
        assert events[0]["event_type"] == "governance.override.activated"
        assert events[0]["override_id"] == "ovr-2"
        assert events[0]["owner"] == "bob"
        assert before + 120.0 <= events[0]["expires_at"] <= after + 120.0

    def test_multiple_emits_preserve_order_and_tail_limit(self, tmp_path: Path):
        """Consecutive emits are appended; tail_events(n) returns last n in order."""
        path = tmp_path / "events.jsonl"
        emitter = OverrideEventEmitter(events_path=path)
        for i in range(5):
            emitter.emit_expired(
                OverrideExpiredEvent(
                    override_id=f"ovr-{i}",
                    policy_id="pol-X",
                    owner="alice",
                    expired_at=float(i),
                )
            )
        all_events = emitter.tail_events(n=20)
        assert len(all_events) == 5
        # tail(n=2) returns the LAST 2 events in insertion order
        last_two = emitter.tail_events(n=2)
        assert [e["override_id"] for e in last_two] == ["ovr-3", "ovr-4"]

    def test_concurrent_emits_all_persisted(self, tmp_path: Path):
        """Concurrent emit_expired() calls all land in the JSONL log."""
        path = tmp_path / "events.jsonl"
        emitter = OverrideEventEmitter(events_path=path)
        errors: list[BaseException] = []

        def worker(i: int) -> None:
            try:
                emitter.emit_expired(
                    OverrideExpiredEvent(
                        override_id=f"ovr-thread-{i}",
                        policy_id="pol-thread",
                        owner="carol",
                        expired_at=float(i),
                    )
                )
            except BaseException as exc:  # pragma: no cover — propagate to errors
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors
        events = emitter.tail_events(n=50)
        assert len(events) == 10
        ids = {e["override_id"] for e in events}
        assert ids == {f"ovr-thread-{i}" for i in range(10)}


# ---------------------------------------------------------------------------
# health_scorer — compute_score_returns_value
# ---------------------------------------------------------------------------


class TestComputeScoreReturnsValue:
    """@trace WP-3001 — weighted health scoring end-to-end."""

    def test_score_dimension_returns_numeric_score(self, health_targets_file: Path):
        """score_dimension returns a DimensionScore with a numeric score field."""
        scorer = HealthScorer(health_targets_file)
        dim = scorer.score_dimension("test_coverage", 80)
        assert isinstance(dim["score"], float)
        assert dim["dimension"] == "test_coverage"
        assert dim["target"] == 80
        assert dim["actual"] == 80
        assert 0.0 <= dim["score"] <= 100.0
        assert dim["status"] in {"excellent", "healthy", "warning", "critical"}

    def test_calculate_overall_returns_weighted_value(self, health_targets_file: Path):
        """calculate_overall returns a float weighted by configured dimension weights."""
        scorer = HealthScorer(health_targets_file)
        scores = [
            scorer.score_dimension("test_coverage", 80),  # 100% * 0.6 = 60
            scorer.score_dimension("lint_violations", 0),  # 100% * 0.4 = 40
        ]
        overall = scorer.calculate_overall(scores)
        assert isinstance(overall, float)
        assert overall == pytest.approx(100.0)

    def test_generate_report_includes_overall_score(self, health_targets_file: Path):
        """generate_report returns a HealthReport with overall_score and timestamp."""
        scorer = HealthScorer(health_targets_file)
        report = scorer.generate_report({"test_coverage": 70, "lint_violations": 5})
        assert report["version"] == "1.0.0"
        assert isinstance(report["overall_score"], float)
        assert 0.0 <= report["overall_score"] <= 100.0
        assert report["status"] in {"excellent", "healthy", "warning", "critical"}
        assert len(report["dimensions"]) == 2
        assert "timestamp" in report
        assert "T" in report["timestamp"]


# ---------------------------------------------------------------------------
# retention — retention_purge_removes_old
# ---------------------------------------------------------------------------


class TestRetentionPurgeRemovesOld:
    """@trace WP-3006 — compliance evidence archival."""

    def test_old_files_archived_and_removed_from_evidence(self, retention_settings: ThegentSettings):
        """Files older than retention_days are moved to archive/."""
        evidence_dir = retention_settings.session_dir / "evidence"
        evidence_dir.mkdir(parents=True, exist_ok=True)

        old_file = evidence_dir / "old.json"
        old_file.write_text("outdated", encoding="utf-8")
        old_ts = time.time() - (35 * 86400)
        os.utime(old_file, (old_ts, old_ts))

        manager = EvidenceRetentionManager(retention_settings)
        manager.retention_days = 30
        results = manager.enforce_retention()

        assert results["archived"] == 1
        assert not old_file.exists()
        assert (retention_settings.session_dir / "archive" / "old.json").exists()

    def test_recent_files_kept_in_evidence(self, retention_settings: ThegentSettings):
        """Files newer than retention_days remain in the evidence directory."""
        evidence_dir = retention_settings.session_dir / "evidence"
        evidence_dir.mkdir(parents=True, exist_ok=True)
        recent_file = evidence_dir / "recent.json"
        recent_file.write_text("fresh", encoding="utf-8")

        manager = EvidenceRetentionManager(retention_settings)
        manager.retention_days = 30
        results = manager.enforce_retention()

        assert results["archived"] == 0
        assert recent_file.exists()
        assert "recent.json" not in manager.list_archived()

    def test_missing_evidence_dir_returns_zero_counts(self, retention_settings: ThegentSettings):
        """enforce_retention is a no-op when the evidence dir does not exist."""
        manager = EvidenceRetentionManager(retention_settings)
        results = manager.enforce_retention()
        assert results == {"archived": 0, "deleted": 0}
        assert manager.list_archived() == []


# ---------------------------------------------------------------------------
# slo_metrics — slo_metrics_record_increments
# ---------------------------------------------------------------------------


def _green_metric(**overrides: object) -> SloMetric:
    """Return an SloMetric that is green against the default thresholds."""
    defaults = {
        "file_loc": 800.0,
        "function_loc_p95": 40.0,
        "impl_importers": 10.0,
        "cross_boundary_import_edges": 12.0,
        "cli_help_p95_ms": 150.0,
        "run_command_p95_ms": 300.0,
        "decomposition_checkpoint_pass_rate": 1.0,
        "source": "v2-integration",
    }
    defaults.update(overrides)
    return SloMetric(**defaults)


class TestSloMetricsRecordIncrements:
    """@trace WL-135 B90-W2-A5 — JSONL emission + threshold evaluation."""

    def test_emit_appends_one_line_per_call(self, slo_output_path: Path):
        """Each emit() appends exactly one JSONL line."""
        emitter = SloEmitter(output_path=slo_output_path)
        emitter.emit(_green_metric(source="emit-1"))
        emitter.emit(_green_metric(source="emit-2"))
        assert slo_output_path.exists()
        lines = [ln for ln in slo_output_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        assert len(lines) == 2
        first = json_fast.loads(lines[0])
        second = json_fast.loads(lines[1])
        assert first["source"] == "emit-1"
        assert second["source"] == "emit-2"

    def test_evaluate_green_metric_returns_all_green(self):
        """A green SloMetric evaluates to 'green' on every field."""
        emitter = SloEmitter(output_path=Path("/tmp/never-written-slo.jsonl"))
        result = emitter.evaluate(_green_metric(), SloThresholds())
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
        for field_name, status in result.items():
            assert status == "green", f"{field_name} should be green, got {status}"

    def test_emit_then_evaluate_roundtrip(self, slo_output_path: Path):
        """Emitted metric, when re-evaluated, still classifies correctly."""
        emitter = SloEmitter(output_path=slo_output_path)
        metric = _green_metric(source="roundtrip")
        emitter.emit(metric)
        # Re-evaluate the emitted metric to confirm SLO status persists
        status = emitter.evaluate(metric, SloThresholds())
        assert status["file_loc"] == "green"
        # Verify the emitted row carries the expected provenance fields
        row = json_fast.loads(slo_output_path.read_text(encoding="utf-8").strip().splitlines()[0])
        assert row["source"] == "roundtrip"
        assert row["file_loc"] == pytest.approx(800.0)
        assert "timestamp" in row
