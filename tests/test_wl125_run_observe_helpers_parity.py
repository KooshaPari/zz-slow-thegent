from __future__ import annotations

from typing import Any

from thegent.cli.commands import impl


def test_wl125_hash_observe_summary_payload_wrapper_delegates(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    def _fake(payload: dict[str, Any]) -> dict[str, str]:
        captured["payload"] = payload
        return {"algorithm": "sha256", "value": "wrapped"}

    monkeypatch.setattr(
        "thegent.cli.commands.impl.run_observe_helpers.hash_observe_summary_payload",
        _fake,
    )

    payload = {"payload_type": "observe_summary"}
    result = impl._hash_observe_summary_payload(payload)

    assert result == {"algorithm": "sha256", "value": "wrapped"}
    assert captured["payload"] == payload


def test_wl125_classify_observe_summary_trend_health_wrapper_delegates(
    monkeypatch,
) -> None:
    captured: dict[str, Any] = {}

    def _fake(**kwargs: Any) -> dict[str, Any]:
        captured.update(kwargs)
        return {"trend_snapshot_health": "warning", "trend_snapshot_health_score": 81}

    monkeypatch.setattr(
        "thegent.cli.commands.impl.run_observe_helpers.classify_observe_summary_trend_health",
        _fake,
    )

    result = impl._classify_observe_summary_trend_health(
        enabled=True,
        baseline_available=False,
        trend_snapshot_coverage_pct=75.0,
        trend_snapshot_deficit=1,
        trend_snapshot_invalid_timestamps=0,
        trend_snapshot_freshness_bucket="warm",
        trend_snapshot_gap_count=0,
        trend_sampling_mode="enabled",
    )

    assert result["trend_snapshot_health"] == "warning"
    assert captured["enabled"] is True
    assert captured["baseline_available"] is False
    assert captured["trend_snapshot_coverage_pct"] == 75.0
    assert captured["trend_snapshot_deficit"] == 1
    assert captured["trend_snapshot_freshness_bucket"] == "warm"


def test_wl125_load_observe_summary_snapshots_wrapper_delegates(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    def _fake(scope_signature: str, scope_key_json: str, limit: int) -> list[dict[str, Any]]:
        captured["scope_signature"] = scope_signature
        captured["scope_key_json"] = scope_key_json
        captured["limit"] = limit
        return [{"record_type": "observe_summary_snapshot"}]

    monkeypatch.setattr(
        "thegent.cli.commands.impl.run_observe_helpers.load_observe_summary_snapshots",
        _fake,
    )

    result = impl._load_observe_summary_snapshots("sig", "{}", 5)

    assert result == [{"record_type": "observe_summary_snapshot"}]
    assert captured == {"scope_signature": "sig", "scope_key_json": "{}", "limit": 5}


def test_wl125_append_observe_summary_snapshot_wrapper_delegates(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    def _fake(
        payload: dict[str, Any],
        trend_scope_key: dict[str, Any],
        trend_scope_signature: str,
        scope_key_json: str,
        trend_snapshot_ids: list[str],
        trend_summary: dict[str, Any],
    ) -> None:
        captured["payload"] = payload
        captured["trend_scope_key"] = trend_scope_key
        captured["trend_scope_signature"] = trend_scope_signature
        captured["scope_key_json"] = scope_key_json
        captured["trend_snapshot_ids"] = trend_snapshot_ids
        captured["trend_summary"] = trend_summary

    monkeypatch.setattr(
        "thegent.cli.commands.impl.run_observe_helpers.append_observe_summary_snapshot",
        _fake,
    )

    payload = {"payload_type": "observe_summary"}
    trend_scope_key = {"payload_type": "observe_summary", "limit": 100}
    trend_summary = {"trend_snapshot_health": "good"}
    impl._append_observe_summary_snapshot(
        payload,
        trend_scope_key,
        "sig-123",
        '{"payload_type":"observe_summary","limit":100}',
        ["2026-02-21T00:00:00+00:00"],
        trend_summary,
    )

    assert captured["payload"] == payload
    assert captured["trend_scope_key"] == trend_scope_key
    assert captured["trend_scope_signature"] == "sig-123"
    assert captured["trend_summary"] == trend_summary


def test_wl125_classify_observe_summary_trend_health_functional_good_case(
    monkeypatch,
) -> None:
    policy_vars = (
        "THGENT_OBSERVE_SUMMARY_TREND_HEALTH_GOOD_THRESHOLD",
        "THGENT_OBSERVE_SUMMARY_TREND_HEALTH_WARNING_THRESHOLD",
        "THGENT_OBSERVE_SUMMARY_TREND_HEALTH_DEGRADED_THRESHOLD",
        "THGENT_OBSERVE_SUMMARY_TREND_HEALTH_MIN_COVERAGE_PCT",
        "THGENT_OBSERVE_SUMMARY_TREND_HEALTH_MAX_INVALID_TIMESTAMPS",
        "THGENT_OBSERVE_SUMMARY_TREND_HEALTH_COVERAGE_PENALTY_PER_PCT",
        "THGENT_OBSERVE_SUMMARY_TREND_HEALTH_DEFICIT_PENALTY_PER_MISSING_SAMPLE",
        "THGENT_OBSERVE_SUMMARY_TREND_HEALTH_INVALID_TIMESTAMP_PENALTY_PER_EVENT",
        "THGENT_OBSERVE_SUMMARY_TREND_HEALTH_STALE_PENALTY",
        "THGENT_OBSERVE_SUMMARY_TREND_HEALTH_CRITICAL_PENALTY",
        "THGENT_OBSERVE_SUMMARY_TREND_HEALTH_UNKNOWN_OR_FUTURE_PENALTY",
        "THGENT_OBSERVE_SUMMARY_TREND_HEALTH_GAP_PENALTY",
        "THGENT_OBSERVE_SUMMARY_TREND_HEALTH_MISSING_BASELINE_PENALTY",
    )
    for var in policy_vars:
        monkeypatch.delenv(var, raising=False)

    result = impl._classify_observe_summary_trend_health(
        enabled=True,
        baseline_available=True,
        trend_snapshot_coverage_pct=100.0,
        trend_snapshot_deficit=0,
        trend_snapshot_invalid_timestamps=0,
        trend_snapshot_freshness_bucket="fresh",
        trend_snapshot_gap_count=0,
        trend_sampling_mode="enabled",
    )

    assert result["trend_snapshot_health"] == "good"
    assert result["trend_snapshot_health_score"] == 100
    assert result["trend_snapshot_recommendations"] == ["Trend quality is healthy."]
