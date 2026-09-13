"""Unit tests for CLI observability service helper slices."""

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from thegent.cli.services import observability as observability_service


@pytest.mark.unit
def test_build_observe_summary_escalation_orders_rows_and_computes_deltas() -> None:
    now = datetime(2026, 2, 21, 12, 0, tzinfo=UTC)
    pending = [
        {
            "run_id": "run-not-sla",
            "priority": 9,
            "past_sla": False,
            "blocked_at_utc": "2026-02-21T10:00:00+00:00",
            "escalate_by_utc": "2026-02-21T13:00:00+00:00",
        },
        {
            "run_id": "run-past-sla",
            "priority": 3,
            "past_sla": True,
            "blocked_at_utc": "2026-02-21T08:00:00+00:00",
            "escalate_by_utc": "2026-02-21T11:00:00+00:00",
        },
        {
            "run_id": "run-missing-escalate-by",
            "priority": 7,
            "past_sla": True,
            "blocked_at_utc": "2026-02-21T09:00:00+00:00",
            "escalate_by_utc": None,
        },
    ]

    result = observability_service.build_observe_summary_escalation(
        pending=pending,
        past_sla=pending[:2],
        now=now,
        top_escalations=2,
    )

    assert result["past_sla_count"] == 2
    top = result["top_rows"]
    assert len(top) == 2
    assert top[0]["run_id"] == "run-missing-escalate-by"
    assert top[0]["minutes_overdue"] is None
    assert top[0]["minutes_remaining"] is None
    assert top[1]["run_id"] == "run-past-sla"
    assert top[1]["minutes_overdue"] == 60.0
    assert top[1]["blocked_to_now_seconds"] == 14400.0


@pytest.mark.unit
def test_build_observe_summary_trend_builds_summary_and_deltas() -> None:
    now = datetime(2026, 2, 21, 12, 0, tzinfo=UTC)

    def build_scope_fn(**kwargs: Any) -> dict[str, Any]:
        return {"payload_type": "observe_summary", **kwargs}

    def hash_scope_fn(scope: dict[str, Any]) -> str:
        assert scope["payload_type"] == "observe_summary"
        return "sig-123"

    def load_snapshots_fn(signature: str, key_json: str, limit: int) -> list[dict[str, Any]]:
        assert signature == "sig-123"
        assert '"payload_type":"observe_summary"' in key_json
        assert limit == 2
        return [
            {
                "captured_at_utc": (now - timedelta(hours=1)).isoformat(),
                "total_events": 80,
                "fallback_rate": 0.2,
                "success_rate": 0.8,
                "avg_confidence": 0.7,
                "structural_drift_pct": 1.5,
                "semantic_drift_pct": 2.5,
                "drift_structural_rate_pct": 2.0,
                "drift_semantic_rate_pct": 3.0,
                "backlog_count": 1,
                "past_sla_count": 0,
            },
            {
                "captured_at_utc": (now - timedelta(hours=2)).isoformat(),
                "total_events": 60,
                "fallback_rate": 0.3,
                "success_rate": 0.7,
                "avg_confidence": 0.6,
                "structural_drift_pct": 1.0,
                "semantic_drift_pct": 2.0,
                "drift_structural_rate_pct": 1.5,
                "drift_semantic_rate_pct": 2.5,
                "backlog_count": 3,
                "past_sla_count": 2,
            },
        ]

    def parse_timestamp_fn(value: str | None) -> datetime | None:
        return datetime.fromisoformat(value) if value else None

    def freshness_bucket_fn(
        freshness_seconds: int | None,
        *,
        fresh_seconds: int,
        warm_seconds: int,
        stale_seconds: int,
    ) -> str:
        assert fresh_seconds == 3600
        assert warm_seconds == 21600
        assert stale_seconds == 86400
        if freshness_seconds is None:
            return "unknown"
        if freshness_seconds <= fresh_seconds:
            return "fresh"
        return "stale"

    def classify_health_fn(**kwargs: Any) -> dict[str, Any]:
        assert kwargs["enabled"] is True
        return {
            "trend_snapshot_health": "good",
            "trend_snapshot_health_score": 98,
            "trend_snapshot_health_breakdown": {"policy_signature": "abc"},
            "trend_snapshot_recommendations": ["Trend quality is healthy."],
        }

    result = observability_service.build_observe_summary_trend(
        trend_samples=3,
        provider="codex",
        drift_window=50,
        structural_budget_pct=5.0,
        semantic_budget_pct=10.0,
        limit=500,
        top_escalations=10,
        now=now,
        kpis={
            "total": 100,
            "fallback_rate": 0.1,
            "success_rate": 0.9,
            "avg_confidence": 0.8,
            "structural_drift_pct": 2.0,
            "semantic_drift_pct": 3.0,
        },
        budget={"structural_rate_pct": 2.2, "semantic_rate_pct": 3.3},
        backlog_count=5,
        past_sla_count=1,
        build_scope_fn=build_scope_fn,
        hash_scope_fn=hash_scope_fn,
        load_snapshots_fn=load_snapshots_fn,
        parse_timestamp_fn=parse_timestamp_fn,
        freshness_bucket_fn=freshness_bucket_fn,
        classify_health_fn=classify_health_fn,
    )

    trend = result["trend_summary"]
    assert result["trend_scope_signature"] == "sig-123"
    assert result["trend_samples_requested"] == 3
    assert trend["enabled"] is True
    assert trend["trend_previous_samples_requested"] == 2
    assert trend["history_sample_count"] == 2
    assert trend["baseline_available"] is True
    assert trend["total_events_delta"] == 40.0
    assert trend["backlog_count_delta"] == 2.0
    assert trend["past_sla_count_delta"] == -1.0
    assert trend["trend_snapshot_health"] == "good"
