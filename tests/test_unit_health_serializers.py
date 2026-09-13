"""Unit tests for health gate/report serializers."""

import csv
import hashlib
import io

import orjson as json
import pytest

from thegent.cli.commands.cli import (
    _serialize_health_gate_csv,
    _serialize_health_gate_jsonl,
    _serialize_health_gate_md,
    _serialize_health_report_csv,
    _serialize_health_report_jsonl,
    _serialize_health_report_md,
    _serialize_health_trend_csv,
    _serialize_health_trend_jsonl,
    _serialize_health_trend_md,
)


def _gate_fixture(blocked_count: int = 1) -> dict:
    """Minimal gate payload matching impl contract."""
    total = 10
    healthy = total - blocked_count
    return {
        "schema_version": "health-schema-v1",
        "payload_type": "session_contract_health_gate",
        "payload_signature": {"algorithm": "sha256", "value": "abc123"},
        "status": "blocked" if blocked_count > 0 else "passed",
        "healthy_ratio": 0.9,
        "threshold": 1.0,
        "pass": blocked_count == 0,
        "total": total,
        "healthy_count": healthy,
        "unhealthy_count": blocked_count,
        "blocked_count": blocked_count,
        "top_blocked_count": min(blocked_count, 200),
        "blocked_sessions_cap": 200,
        "total_sessions": total,
        "healthy_sessions": healthy,
        "unhealthy_sessions": blocked_count,
        "blocked_sessions_count": blocked_count,
        "blocked_ratio": blocked_count / total if total else 0.0,
        "strict_checks_enabled": True,
        "summary": {
            "health": {"healthy": 9, "warning": 0, "error": 1, "missing": 0},
            "strict_checks_enabled": True,
        },
        "blocked_sessions": [
            {
                "session_id": "s1",
                "state": "done",
                "health": "error",
                "issues": ["missing_contract:provider"],
            }
        ][:blocked_count],
        "generated_at_utc": "2026-02-14T12:00:00Z",
        "generated_query": {
            "owner": "alice",
            "all": True,
            "strict": True,
            "min_healthy_ratio": 1.0,
        },
    }


def _report_fixture(blocked_count: int = 1) -> dict:
    """Minimal report payload matching impl contract."""
    total = 10
    healthy = total - blocked_count
    blocked = [
        {
            "session_id": "s1",
            "owner": "alice",
            "state": "done",
            "health": "error",
            "issues": ["missing_contract:provider"],
            "remediation": ["Ensure route_contract includes provider metadata."],
            "started_at_utc": "2026-02-14T11:00:00Z",
            "agent": "gemini",
        }
    ][:blocked_count]
    return {
        "schema_version": "health-schema-v1",
        "payload_type": "session_contract_health_report",
        "payload_signature": {"algorithm": "sha256", "value": "def456"},
        "status": "blocked" if blocked_count > 0 else "passed",
        "pass": blocked_count == 0,
        "total": total,
        "total_sessions": total,
        "blocked_count": blocked_count,
        "blocked_sessions": blocked_count,
        "blocked_sessions_count": blocked_count,
        "top_blocked_count": min(blocked_count, 25),
        "blocked_ratio": blocked_count / total if total else 0.0,
        "health": {"healthy": 9, "warning": 0, "error": 1, "missing": 0},
        "healthy_count": healthy,
        "healthy_sessions": healthy,
        "unhealthy_count": blocked_count,
        "unhealthy_sessions": blocked_count,
        "strict_checks_enabled": True,
        "top_blocked": blocked,
        "generated_at_utc": "2026-02-14T12:00:00Z",
        "generated_query": {
            "owner": "alice",
            "all": True,
            "strict": True,
            "top_blocked": 25,
        },
        "issue_breakdown": [],
        "owner_breakdown": {},
    }


def _trend_fixture() -> dict:
    return {
        "schema_version": "health-schema-v1",
        "schema_compat_mode": "compat",
        "payload_type": "session_contract_health_trend",
        "trend_payload_type": "session_contract_health_report",
        "payload_signature": {"algorithm": "sha256", "value": "789abc"},
        "generated_at_utc": "2026-02-14T12:15:00Z",
        "snapshot_count": 2,
        "limit": 10,
        "snapshot_retention_max_lines": 5000,
        "scope_key": {
            "payload_type": "session_contract_health_report",
            "owner": "alice",
            "all": False,
            "strict": True,
            "policy_profile": "strict_ci",
            "top_blocked": 25,
        },
        "scope_owner": "alice",
        "scope_all": False,
        "scope_strict": True,
        "scope_policy_profile": "strict_ci",
        "scope_min_healthy_ratio": None,
        "scope_top_blocked": 25,
        "delta_summary": {"blocked_ratio_delta": 0.1, "blocked_count_delta": 1},
        "latest": {},
        "oldest": {},
        "snapshots": [
            {
                "captured_at_utc": "2026-02-14T12:00:00Z",
                "status": "passed",
                "pass": True,
                "total": 10,
                "healthy_count": 10,
                "unhealthy_count": 0,
                "blocked_count": 0,
                "blocked_ratio": 0.0,
                "issue_types": [],
            },
            {
                "captured_at_utc": "2026-02-14T12:10:00Z",
                "status": "blocked",
                "pass": False,
                "total": 10,
                "healthy_count": 9,
                "unhealthy_count": 1,
                "blocked_count": 1,
                "blocked_ratio": 0.1,
                "issue_types": ["missing_contract:provider"],
            },
        ],
    }


@pytest.mark.unit
class TestHealthGateSerializers:
    """Tests for gate CSV, JSONL, and MD serializers."""

    def test_gate_csv_has_summary_and_blocked_rows(self) -> None:
        # @trace FR-CTR-013
        gate = _gate_fixture(blocked_count=1)
        out = _serialize_health_gate_csv(gate)
        rows = list(csv.reader(io.StringIO(out)))
        assert len(rows) >= 2
        assert rows[0][4] == "record_type"
        assert rows[1][4] == "summary"
        if len(rows) > 2:
            assert rows[2][4] == "blocked_session"

    def test_gate_csv_blocked_row_has_query_context(self) -> None:
        # @trace FR-CTR-013
        gate = _gate_fixture(blocked_count=1)
        out = _serialize_health_gate_csv(gate)
        rows = list(csv.reader(io.StringIO(out)))
        header = rows[0]
        owner_idx = header.index("owner")
        strict_idx = header.index("strict")
        blocked_row = rows[2]
        assert blocked_row[owner_idx] == "alice"
        assert blocked_row[strict_idx] == "True"

    def test_gate_jsonl_blocked_row_has_generated_query(self) -> None:
        # @trace FR-CTR-013
        gate = _gate_fixture(blocked_count=1)
        out = _serialize_health_gate_jsonl(gate)
        lines = [l for l in out.strip().split("\n") if l]
        assert len(lines) >= 2
        blocked = json.loads(lines[1])
        assert blocked["record_type"] == "blocked_session"
        assert "generated_query" in blocked
        assert blocked["generated_query"].get("owner") == "alice"
        assert blocked["generated_query"].get("strict") is True

    def test_gate_jsonl_summary_first(self) -> None:
        # @trace FR-CTR-013
        gate = _gate_fixture(blocked_count=1)
        out = _serialize_health_gate_jsonl(gate)
        first = json.loads(out.split("\n")[0])
        assert first["record_type"] == "summary"
        assert first["payload_type"] == "session_contract_health_gate"

    def test_gate_md_has_schema_and_status(self) -> None:
        # @trace FR-CTR-013
        gate = _gate_fixture(blocked_count=1)
        out = _serialize_health_gate_md(gate)
        assert "health-schema-v1" in out
        assert "session_contract_health_gate" in out
        assert "status" in out
        assert "generated_query" in out


@pytest.mark.unit
class TestHealthReportSerializers:
    """Tests for report CSV, JSONL, and MD serializers."""

    def test_report_csv_has_summary_and_blocked_rows(self) -> None:
        # @trace FR-CTR-013
        report = _report_fixture(blocked_count=1)
        out = _serialize_health_report_csv(report)
        rows = list(csv.reader(io.StringIO(out)))
        assert len(rows) >= 2
        record_idx = rows[0].index("record_type")
        assert rows[1][record_idx] == "summary"
        if len(rows) > 2:
            assert rows[2][record_idx] == "blocked_session"

    def test_report_csv_blocked_row_has_query_context(self) -> None:
        # @trace FR-CTR-013
        report = _report_fixture(blocked_count=1)
        out = _serialize_health_report_csv(report)
        rows = list(csv.reader(io.StringIO(out)))
        header = rows[0]
        gq_owner_idx = header.index("generated_query_owner")
        assert len(rows) >= 3
        blocked_row = rows[2]
        assert blocked_row[gq_owner_idx] == "alice"

    def test_report_jsonl_blocked_row_has_query_context(self) -> None:
        # @trace FR-CTR-013
        report = _report_fixture(blocked_count=1)
        out = _serialize_health_report_jsonl(report)
        lines = [l for l in out.strip().split("\n") if l]
        assert len(lines) >= 2
        blocked = json.loads(lines[1])
        assert blocked["record_type"] == "blocked_session"
        assert "generated_query" in blocked
        assert blocked["generated_query"].get("owner") == "alice"
        assert blocked["generated_query"].get("strict") is True

    def test_report_jsonl_summary_first(self) -> None:
        # @trace FR-CTR-013
        report = _report_fixture(blocked_count=1)
        out = _serialize_health_report_jsonl(report)
        first = json.loads(out.split("\n")[0])
        assert first["record_type"] == "summary"
        assert first["payload_type"] == "session_contract_health_report"

    def test_report_md_has_schema_and_status(self) -> None:
        # @trace FR-CTR-013
        report = _report_fixture(blocked_count=1)
        out = _serialize_health_report_md(report)
        assert "health-schema-v1" in out or "schema_version" in out
        assert "session_contract_health_report" in out or "payload_type" in out
        assert "status" in out or "blocked" in out


@pytest.mark.unit
class TestHealthSerializerEdgeCases:
    """Edge cases: empty blocked, no payload_signature."""

    def test_gate_jsonl_empty_blocked_sessions(self) -> None:
        # @trace FR-CTR-013
        gate = _gate_fixture(blocked_count=0)
        gate["blocked_sessions"] = []
        out = _serialize_health_gate_jsonl(gate)
        lines = [l for l in out.strip().split("\n") if l]
        assert len(lines) == 1
        assert json.loads(lines[0])["record_type"] == "summary"

    def test_report_jsonl_empty_top_blocked(self) -> None:
        # @trace FR-CTR-013
        report = _report_fixture(blocked_count=0)
        report["top_blocked"] = []
        out = _serialize_health_report_jsonl(report)
        lines = [l for l in out.strip().split("\n") if l]
        assert len(lines) == 1
        assert json.loads(lines[0])["record_type"] == "summary"

    def test_gate_csv_handles_missing_payload_signature(self) -> None:
        # @trace FR-CTR-013
        gate = _gate_fixture(blocked_count=0)
        del gate["payload_signature"]
        out = _serialize_health_gate_csv(gate)
        assert "sha256" in out
        assert len(out) > 0


@pytest.mark.unit
class TestHealthTrendSerializers:
    def test_trend_md_has_core_fields(self) -> None:
        # @trace FR-CTR-013
        trend = _trend_fixture()
        trend["scope_payload_type"] = "top-level-payload-type"
        trend["scope_key_json"] = "top-level-scope-key-json"
        trend["delta_summary_json"] = "top-level-delta-summary-json"
        trend["latest_issue_types_json"] = "top-level-issue-types-json"
        trend["latest_issue_types_hash"] = "top-level-issue-types-hash"
        trend["snapshot_ids_csv"] = "snap-a, snap-b"
        trend["snapshot_ids_hash"] = "snap-hash"
        trend["snapshot_window_seconds"] = 123
        trend["snapshot_window_hash"] = "window-hash"
        trend["snapshot_interval_seconds_avg"] = 456
        trend["snapshot_interval_hash"] = "interval-hash"
        trend["snapshot_density_per_hour"] = 3.25
        trend["snapshot_density_hash"] = "density-hash"
        trend["snapshot_freshness_seconds"] = 789
        trend["snapshot_freshness_hash"] = "freshness-hash"
        trend["snapshot_issue_churn_count"] = 2
        trend["snapshot_issue_churn_hash"] = "churn-hash"
        trend["snapshot_health_volatility"] = 4.0
        trend["snapshot_health_volatility_hash"] = hashlib.sha256(
            str(trend["snapshot_health_volatility"]).encode("utf-8")
        ).hexdigest()
        out = _serialize_health_trend_md(trend)
        assert "Session Contract Health Trend" in out
        assert "session_contract_health_trend" in out
        assert "generated_at_utc" in out
        assert "compat_mode" in out
        assert "compat_aliases" in out
        assert "compat_aliases_count" in out
        assert "snapshot_retention_max_lines" in out
        assert "latest_status" in out
        assert "latest_pass" in out
        assert "latest_captured_at_utc" in out
        assert "latest_blocked_ratio" in out
        assert "latest_blocked_count" in out
        assert "latest_issue_types_count" in out
        assert "latest_issue_types_csv" in out
        assert "latest_issue_types_json" in out
        assert "top-level-issue-types-json" in out
        assert "latest_issue_types_hash" in out
        assert "top-level-issue-types-hash" in out
        assert "snapshot_ids_csv" in out
        assert "snap-a, snap-b" in out
        assert "snapshot_ids_hash" in out
        assert "snap-hash" in out
        assert "snapshot_window_seconds" in out
        assert "123" in out
        assert "snapshot_window_hash" in out
        assert "window-hash" in out
        assert "snapshot_interval_seconds_avg" in out
        assert "456" in out
        assert "snapshot_interval_hash" in out
        assert "interval-hash" in out
        assert "snapshot_density_per_hour" in out
        assert "3.25" in out
        assert "snapshot_density_hash" in out
        assert "density-hash" in out
        assert "snapshot_freshness_seconds" in out
        assert "789" in out
        assert "snapshot_freshness_hash" in out
        assert "freshness-hash" in out
        assert "snapshot_issue_churn_count" in out
        assert "2" in out
        assert "snapshot_issue_churn_hash" in out
        assert "churn-hash" in out
        assert "snapshot_health_volatility" in out
        assert "4.0" in out
        assert "snapshot_health_volatility_hash" in out
        assert trend["snapshot_health_volatility_hash"] in out
        assert "scope_owner" in out
        assert "scope_payload_type" in out
        assert "top-level-payload-type" in out
        assert "scope_key_json" in out
        assert "top-level-scope-key-json" in out
        assert "delta_summary_json" in out
        assert "top-level-delta-summary-json" in out
        assert "scope_all" in out
        assert "scope_strict" in out
        assert "scope_policy_profile" in out

    def test_trend_md_uses_fallback_volatility_hash_when_missing(self) -> None:
        # @trace FR-CTR-013
        trend = _trend_fixture()
        trend.pop("snapshot_health_volatility", None)
        trend.pop("snapshot_health_volatility_hash", None)
        expected_hash = hashlib.sha256(str(None).encode("utf-8")).hexdigest()
        out = _serialize_health_trend_md(trend)
        assert "snapshot_health_volatility" in out
        assert "snapshot_health_volatility: None" in out
        assert "snapshot_health_volatility_hash" in out
        assert expected_hash in out

    def test_trend_serializers_normalize_malformed_issue_types(self) -> None:
        # @trace FR-CTR-013
        trend = _trend_fixture()
        trend["latest"]["issue_types"] = "abc"
        trend["snapshots"][0]["issue_types"] = {"left": 1, "right": 2}
        trend.pop("latest_issue_types_json", None)
        trend.pop("latest_issue_types_csv", None)
        trend.pop("latest_issue_types_hash", None)
        trend.pop("latest_issue_types_count", None)

        md = _serialize_health_trend_md(trend)
        assert "latest_issue_types_count: 1" in md
        assert "latest_issue_types_csv: abc" in md
        assert 'latest_issue_types_json: ["abc"]' in md

        csv_out = _serialize_health_trend_csv(trend)
        rows = list(csv.reader(io.StringIO(csv_out)))
        latest_count_idx = rows[0].index("latest_issue_types_count")
        latest_csv_idx = rows[0].index("latest_issue_types_csv")
        snapshot_issue_types_idx = rows[0].index("issue_types")
        assert rows[1][latest_count_idx] == "1"
        assert rows[1][latest_csv_idx] == "abc"
        assert rows[2][snapshot_issue_types_idx] == "left, right"

        jsonl_out = _serialize_health_trend_jsonl(trend)
        lines = [l for l in jsonl_out.strip().split("\n") if l]
        first = json.loads(lines[0])
        second = json.loads(lines[1])
        assert first["latest_issue_types_count"] == 1
        assert first["latest_issue_types_csv"] == "abc"
        assert first["latest_issue_types_json"] == '["abc"]'
        assert second["issue_types"] == {"left": 1, "right": 2}

    def test_trend_csv_summary_and_snapshot_rows(self) -> None:
        # @trace FR-CTR-013
        trend = _trend_fixture()
        trend["scope_payload_type"] = "top-level-payload-type"
        trend["scope_key_json"] = "top-level-scope-key-json"
        trend["delta_summary_json"] = "top-level-delta-summary-json"
        trend["latest_status"] = "top-level-status"
        trend["latest_pass"] = True
        trend["latest_captured_at_utc"] = "2026-02-14T12:11:00Z"
        trend["latest_blocked_ratio"] = 0.33
        trend["latest_blocked_count"] = 17
        trend["latest_issue_types_csv"] = "top-level-issue-types-csv"
        trend["latest_issue_types_json"] = "top-level-issue-types-json"
        trend["latest_issue_types_hash"] = "top-level-issue-types-hash"
        trend["snapshot_ids_csv"] = "snap-a, snap-b"
        trend["snapshot_ids_hash"] = "snap-hash"
        trend["snapshot_window_seconds"] = 123
        trend["snapshot_window_hash"] = "window-hash"
        trend["snapshot_interval_seconds_avg"] = 456
        trend["snapshot_interval_hash"] = "interval-hash"
        trend["snapshot_density_per_hour"] = 3.25
        trend["snapshot_density_hash"] = "density-hash"
        trend["snapshot_freshness_seconds"] = 789
        trend["snapshot_freshness_hash"] = "freshness-hash"
        trend["snapshot_issue_churn_count"] = 2
        trend["snapshot_issue_churn_hash"] = "churn-hash"
        trend["snapshot_health_volatility"] = 4.0
        trend["snapshot_health_volatility_hash"] = hashlib.sha256(
            str(trend["snapshot_health_volatility"]).encode("utf-8")
        ).hexdigest()
        trend["blocked_ratio_delta"] = 0.75
        trend["blocked_count_delta"] = 8
        out = _serialize_health_trend_csv(trend)
        rows = list(csv.reader(io.StringIO(out)))
        assert rows[0][6] == "record_type"
        assert "compat_mode" in rows[0]
        assert "compat_aliases_json" in rows[0]
        assert "compat_aliases_count" in rows[0]
        assert "generated_at_utc" in rows[0]
        assert "latest_status" in rows[0]
        assert "latest_pass" in rows[0]
        assert "latest_captured_at_utc" in rows[0]
        assert "latest_blocked_ratio" in rows[0]
        assert "latest_blocked_count" in rows[0]
        assert "latest_issue_types_count" in rows[0]
        assert "latest_issue_types_csv" in rows[0]
        assert "latest_issue_types_json" in rows[0]
        assert "latest_issue_types_hash" in rows[0]
        assert "snapshot_ids_csv" in rows[0]
        assert "snapshot_ids_hash" in rows[0]
        assert "snapshot_window_seconds" in rows[0]
        assert "snapshot_window_hash" in rows[0]
        assert "snapshot_interval_seconds_avg" in rows[0]
        assert "snapshot_interval_hash" in rows[0]
        assert "snapshot_density_per_hour" in rows[0]
        assert "snapshot_density_hash" in rows[0]
        assert "snapshot_freshness_seconds" in rows[0]
        assert "snapshot_freshness_hash" in rows[0]
        assert "snapshot_issue_churn_count" in rows[0]
        assert "snapshot_issue_churn_hash" in rows[0]
        assert "snapshot_health_volatility" in rows[0]
        assert "snapshot_health_volatility_hash" in rows[0]
        assert "scope_owner" in rows[0]
        assert "scope_payload_type" in rows[0]
        assert "scope_key_json" in rows[0]
        assert "delta_summary_json" in rows[0]
        assert "scope_all" in rows[0]
        assert "scope_strict" in rows[0]
        assert "scope_policy_profile" in rows[0]
        assert rows[1][6] == "summary"
        assert rows[2][6] == "snapshot"
        latest_status_idx = rows[0].index("latest_status")
        latest_pass_idx = rows[0].index("latest_pass")
        latest_captured_at_idx = rows[0].index("latest_captured_at_utc")
        latest_blocked_ratio_idx = rows[0].index("latest_blocked_ratio")
        latest_blocked_count_idx = rows[0].index("latest_blocked_count")
        latest_issue_types_csv_idx = rows[0].index("latest_issue_types_csv")
        latest_issue_types_json_idx = rows[0].index("latest_issue_types_json")
        latest_issue_types_hash_idx = rows[0].index("latest_issue_types_hash")
        snapshot_ids_csv_idx = rows[0].index("snapshot_ids_csv")
        snapshot_ids_hash_idx = rows[0].index("snapshot_ids_hash")
        snapshot_window_seconds_idx = rows[0].index("snapshot_window_seconds")
        snapshot_window_hash_idx = rows[0].index("snapshot_window_hash")
        snapshot_interval_seconds_avg_idx = rows[0].index("snapshot_interval_seconds_avg")
        snapshot_interval_hash_idx = rows[0].index("snapshot_interval_hash")
        snapshot_density_per_hour_idx = rows[0].index("snapshot_density_per_hour")
        snapshot_density_hash_idx = rows[0].index("snapshot_density_hash")
        snapshot_freshness_seconds_idx = rows[0].index("snapshot_freshness_seconds")
        snapshot_freshness_hash_idx = rows[0].index("snapshot_freshness_hash")
        snapshot_issue_churn_count_idx = rows[0].index("snapshot_issue_churn_count")
        snapshot_issue_churn_hash_idx = rows[0].index("snapshot_issue_churn_hash")
        snapshot_health_volatility_idx = rows[0].index("snapshot_health_volatility")
        snapshot_health_volatility_hash_idx = rows[0].index("snapshot_health_volatility_hash")
        ratio_idx = rows[0].index("blocked_ratio_delta")
        count_idx = rows[0].index("blocked_count_delta")
        scope_payload_type_idx = rows[0].index("scope_payload_type")
        scope_key_json_idx = rows[0].index("scope_key_json")
        delta_summary_json_idx = rows[0].index("delta_summary_json")
        assert rows[1][latest_status_idx] == "top-level-status"
        assert rows[1][latest_pass_idx] == "True"
        assert rows[1][latest_captured_at_idx] == "2026-02-14T12:11:00Z"
        assert rows[1][latest_blocked_ratio_idx] == "0.33"
        assert rows[1][latest_blocked_count_idx] == "17"
        assert rows[1][latest_issue_types_csv_idx] == "top-level-issue-types-csv"
        assert rows[1][latest_issue_types_json_idx] == "top-level-issue-types-json"
        assert rows[1][latest_issue_types_hash_idx] == "top-level-issue-types-hash"
        assert rows[1][snapshot_ids_csv_idx] == "snap-a, snap-b"
        assert rows[1][snapshot_ids_hash_idx] == "snap-hash"
        assert rows[1][snapshot_window_seconds_idx] == "123"
        assert rows[1][snapshot_window_hash_idx] == "window-hash"
        assert rows[1][snapshot_interval_seconds_avg_idx] == "456"
        assert rows[1][snapshot_interval_hash_idx] == "interval-hash"
        assert rows[1][snapshot_density_per_hour_idx] == "3.25"
        assert rows[1][snapshot_density_hash_idx] == "density-hash"
        assert rows[1][snapshot_freshness_seconds_idx] == "789"
        assert rows[1][snapshot_freshness_hash_idx] == "freshness-hash"
        assert rows[1][snapshot_issue_churn_count_idx] == "2"
        assert rows[1][snapshot_issue_churn_hash_idx] == "churn-hash"
        assert rows[1][snapshot_health_volatility_idx] == "4.0"
        assert rows[1][snapshot_health_volatility_hash_idx] == trend["snapshot_health_volatility_hash"]
        assert rows[2][latest_status_idx] == "top-level-status"
        assert rows[2][latest_pass_idx] == "True"
        assert rows[2][latest_captured_at_idx] == "2026-02-14T12:11:00Z"
        assert rows[2][latest_blocked_ratio_idx] == "0.33"
        assert rows[2][latest_blocked_count_idx] == "17"
        assert rows[2][latest_issue_types_csv_idx] == "top-level-issue-types-csv"
        assert rows[2][latest_issue_types_json_idx] == "top-level-issue-types-json"
        assert rows[2][latest_issue_types_hash_idx] == "top-level-issue-types-hash"
        assert rows[2][snapshot_ids_csv_idx] == "snap-a, snap-b"
        assert rows[2][snapshot_ids_hash_idx] == "snap-hash"
        assert rows[2][snapshot_window_seconds_idx] == "123"
        assert rows[2][snapshot_window_hash_idx] == "window-hash"
        assert rows[2][snapshot_interval_seconds_avg_idx] == "456"
        assert rows[2][snapshot_interval_hash_idx] == "interval-hash"
        assert rows[2][snapshot_density_per_hour_idx] == "3.25"
        assert rows[2][snapshot_density_hash_idx] == "density-hash"
        assert rows[2][snapshot_freshness_seconds_idx] == "789"
        assert rows[2][snapshot_freshness_hash_idx] == "freshness-hash"
        assert rows[2][snapshot_issue_churn_count_idx] == "2"
        assert rows[2][snapshot_issue_churn_hash_idx] == "churn-hash"
        assert rows[2][snapshot_health_volatility_idx] == "4.0"
        assert rows[2][snapshot_health_volatility_hash_idx] == trend["snapshot_health_volatility_hash"]
        assert rows[1][scope_payload_type_idx] == "top-level-payload-type"
        assert rows[2][scope_payload_type_idx] == "top-level-payload-type"
        assert rows[1][scope_key_json_idx] == "top-level-scope-key-json"
        assert rows[2][scope_key_json_idx] == "top-level-scope-key-json"
        assert rows[1][delta_summary_json_idx] == "top-level-delta-summary-json"
        assert rows[2][delta_summary_json_idx] == "top-level-delta-summary-json"
        assert rows[1][ratio_idx] == "0.75"
        assert rows[1][count_idx] == "8"
        assert rows[2][ratio_idx] == "0.75"
        assert rows[2][count_idx] == "8"

    def test_trend_csv_defaults_empty_compat_when_missing(self) -> None:
        # @trace FR-CTR-013
        trend = _trend_fixture()
        trend["snapshots"] = []
        trend.pop("compat", None)
        trend.pop("compat_aliases_count", None)
        out = _serialize_health_trend_csv(trend)
        rows = list(csv.reader(io.StringIO(out)))
        assert len(rows) == 2
        compat_mode_idx = rows[0].index("compat_mode")
        compat_aliases_idx = rows[0].index("compat_aliases_json")
        compat_aliases_count_idx = rows[0].index("compat_aliases_count")
        assert rows[1][compat_mode_idx] == "compat"
        assert rows[1][compat_aliases_idx] == "{}"
        assert rows[1][compat_aliases_count_idx] == "0"

    def test_trend_csv_fallback_hash_when_volatility_missing(self) -> None:
        # @trace FR-CTR-013
        trend = _trend_fixture()
        trend.pop("snapshot_health_volatility", None)
        trend.pop("snapshot_health_volatility_hash", None)
        expected_hash = hashlib.sha256(str(None).encode("utf-8")).hexdigest()
        out = _serialize_health_trend_csv(trend)
        rows = list(csv.reader(io.StringIO(out)))
        assert rows[0][0] == "schema_version"
        snapshot_health_volatility_idx = rows[0].index("snapshot_health_volatility")
        snapshot_health_volatility_hash_idx = rows[0].index("snapshot_health_volatility_hash")
        assert rows[1][snapshot_health_volatility_idx] == "None"
        assert rows[1][snapshot_health_volatility_hash_idx] == expected_hash
        assert rows[2][snapshot_health_volatility_idx] == "None"
        assert rows[2][snapshot_health_volatility_hash_idx] == expected_hash

    def test_trend_jsonl_summary_first_and_snapshot_next(self) -> None:
        # @trace FR-CTR-013
        trend = _trend_fixture()
        trend["scope_payload_type"] = "top-level-payload-type"
        trend["scope_key_json"] = "top-level-scope-key-json"
        trend["delta_summary_json"] = "top-level-delta-summary-json"
        trend["latest_status"] = "top-level-status"
        trend["latest_pass"] = True
        trend["latest_captured_at_utc"] = "2026-02-14T12:11:00Z"
        trend["latest_blocked_ratio"] = 0.33
        trend["latest_blocked_count"] = 17
        trend["latest_issue_types_count"] = 11
        trend["latest_issue_types_csv"] = "top-level-issue-types-csv"
        trend["latest_issue_types_json"] = "top-level-issue-types-json"
        trend["latest_issue_types_hash"] = "top-level-issue-types-hash"
        trend["snapshot_ids_csv"] = "snap-a, snap-b"
        trend["snapshot_ids_hash"] = "snap-hash"
        trend["snapshot_window_seconds"] = 123
        trend["snapshot_window_hash"] = "window-hash"
        trend["snapshot_interval_seconds_avg"] = 456
        trend["snapshot_interval_hash"] = "interval-hash"
        trend["snapshot_density_per_hour"] = 3.25
        trend["snapshot_density_hash"] = "density-hash"
        trend["snapshot_freshness_seconds"] = 789
        trend["snapshot_freshness_hash"] = "freshness-hash"
        trend["snapshot_issue_churn_count"] = 2
        trend["snapshot_issue_churn_hash"] = "churn-hash"
        trend["snapshot_health_volatility"] = 4.0
        trend["snapshot_health_volatility_hash"] = hashlib.sha256(
            str(trend["snapshot_health_volatility"]).encode("utf-8")
        ).hexdigest()
        trend["compat"] = {"mode": "compat", "aliases": {"legacy": "compat"}}
        trend["blocked_ratio_delta"] = 0.66
        trend["blocked_count_delta"] = 5
        out = _serialize_health_trend_jsonl(trend)
        lines = [l for l in out.strip().split("\n") if l]
        assert len(lines) >= 2
        first = json.loads(lines[0])
        second = json.loads(lines[1])
        assert first["record_type"] == "summary"
        assert second["record_type"] == "snapshot"
        assert second["trend_payload_type"] == "session_contract_health_report"
        assert first["generated_at_utc"] == "2026-02-14T12:15:00Z"
        assert second["generated_at_utc"] == "2026-02-14T12:15:00Z"
        assert first["latest_status"] == "top-level-status"
        assert first["latest_pass"] is True
        assert second["latest_status"] == "top-level-status"
        assert second["latest_pass"] is True
        assert second["blocked_ratio_delta"] == 0.66
        assert second["blocked_count_delta"] == 5
        assert first["latest_captured_at_utc"] == "2026-02-14T12:11:00Z"
        assert first["latest_blocked_ratio"] == 0.33
        assert first["latest_blocked_count"] == 17
        assert "latest_issue_types_count" in first
        assert first["latest_issue_types_count"] == 11
        assert first["latest_issue_types_csv"] == "top-level-issue-types-csv"
        assert first["latest_issue_types_json"] == "top-level-issue-types-json"
        assert first["latest_issue_types_hash"] == "top-level-issue-types-hash"
        assert first["snapshot_ids_csv"] == "snap-a, snap-b"
        assert first["snapshot_ids_hash"] == "snap-hash"
        assert first["snapshot_window_seconds"] == 123
        assert first["snapshot_window_hash"] == "window-hash"
        assert first["snapshot_interval_seconds_avg"] == 456
        assert first["snapshot_interval_hash"] == "interval-hash"
        assert first["snapshot_density_per_hour"] == 3.25
        assert first["snapshot_density_hash"] == "density-hash"
        assert first["snapshot_freshness_seconds"] == 789
        assert first["snapshot_freshness_hash"] == "freshness-hash"
        assert first["snapshot_issue_churn_count"] == 2
        assert first["snapshot_issue_churn_hash"] == "churn-hash"
        assert first["snapshot_health_volatility"] == 4.0
        assert first["snapshot_health_volatility_hash"] == trend["snapshot_health_volatility_hash"]
        assert "compat" in first
        assert first["compat"]["mode"] == "compat"
        assert second["latest_captured_at_utc"] == "2026-02-14T12:11:00Z"
        assert second["latest_blocked_ratio"] == 0.33
        assert second["latest_blocked_count"] == 17
        assert "latest_issue_types_count" in second
        assert second["latest_issue_types_count"] == 11
        assert second["latest_issue_types_csv"] == "top-level-issue-types-csv"
        assert second["latest_issue_types_json"] == "top-level-issue-types-json"
        assert second["latest_issue_types_hash"] == "top-level-issue-types-hash"
        assert second["snapshot_ids_csv"] == "snap-a, snap-b"
        assert second["snapshot_ids_hash"] == "snap-hash"
        assert second["snapshot_window_seconds"] == 123
        assert second["snapshot_window_hash"] == "window-hash"
        assert second["snapshot_interval_seconds_avg"] == 456
        assert second["snapshot_interval_hash"] == "interval-hash"
        assert second["snapshot_density_per_hour"] == 3.25
        assert second["snapshot_density_hash"] == "density-hash"
        assert second["snapshot_freshness_seconds"] == 789
        assert second["snapshot_freshness_hash"] == "freshness-hash"
        assert second["snapshot_issue_churn_count"] == 2
        assert second["snapshot_issue_churn_hash"] == "churn-hash"
        assert second["snapshot_health_volatility"] == 4.0
        assert second["snapshot_health_volatility_hash"] == trend["snapshot_health_volatility_hash"]
        assert second["compat_mode"] == "compat"
        assert "compat_aliases" in second
        assert first["compat_aliases_count"] == 1
        assert second["compat_aliases_count"] == 1
        assert "scope_owner" in first
        assert first["scope_payload_type"] == "top-level-payload-type"
        assert first["scope_key_json"] == "top-level-scope-key-json"
        assert first["delta_summary_json"] == "top-level-delta-summary-json"
        assert "scope_all" in first
        assert "scope_strict" in first
        assert "scope_policy_profile" in first
        assert "scope_owner" in second
        assert second["scope_payload_type"] == "top-level-payload-type"
        assert second["scope_key_json"] == "top-level-scope-key-json"
        assert second["delta_summary_json"] == "top-level-delta-summary-json"
        assert "scope_all" in second
        assert "scope_strict" in second
        assert "scope_policy_profile" in second

    def test_trend_jsonl_fallback_hash_when_volatility_missing(self) -> None:
        # @trace FR-CTR-013
        trend = _trend_fixture()
        trend.pop("snapshot_health_volatility", None)
        trend.pop("snapshot_health_volatility_hash", None)
        expected_hash = hashlib.sha256(str(None).encode("utf-8")).hexdigest()
        out = _serialize_health_trend_jsonl(trend)
        lines = [l for l in out.strip().split("\n") if l]
        first = json.loads(lines[0])
        second = json.loads(lines[1])
        assert first["snapshot_health_volatility"] is None
        assert first["snapshot_health_volatility_hash"] == expected_hash
        assert second["snapshot_health_volatility"] is None
        assert second["snapshot_health_volatility_hash"] == expected_hash

    def test_trend_jsonl_defaults_empty_compat_and_no_snapshots(self) -> None:
        # @trace FR-CTR-013
        trend = _trend_fixture()
        trend["snapshots"] = []
        trend.pop("compat", None)
        trend.pop("compat_aliases_count", None)
        out = _serialize_health_trend_jsonl(trend)
        lines = [l for l in out.strip().split("\n") if l]
        assert len(lines) == 1
        first = json.loads(lines[0])
        assert first["compat"]["mode"] == "compat"
        assert first["compat"]["aliases"] == {}
        assert first["compat_aliases_count"] == 0
