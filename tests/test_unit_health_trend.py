"""Unit tests for health policy/baseline/trend behavior in cli_impl."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import orjson as json
import pytest
import typer

from thegent.cli.commands import impl as cli_impl

if TYPE_CHECKING:
    from pathlib import Path


def _build_audit(total: int, healthy: int, *, owner: str = "alice") -> dict:
    warning = 0
    error = max(total - healthy, 0)
    rows = []
    for i in range(total):
        is_healthy = i < healthy
        rows.append(
            {
                "session_id": f"s{i}",
                "owner": owner,
                "contract_state": "complete",
                "contract_health": "healthy" if is_healthy else "error",
                "contract_issues": [] if is_healthy else ["missing_contract:provider"],
                "started_at_utc": "2026-02-14T12:00:00Z",
                "agent": "gemini",
            }
        )
    return {
        "rows": rows,
        "summary": {
            "total": total,
            "complete": total,
            "partial": 0,
            "request_only": 0,
            "contract_only": 0,
            "untracked": 0,
            "strict_checks_enabled": False,
            "health": {
                "healthy": healthy,
                "warning": warning,
                "error": error,
                "missing": 0,
            },
        },
    }


@pytest.mark.unit
class TestHealthPolicyAndTrend:
    def test_gate_policy_profile_overrides_threshold(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # @trace FR-GOV-002
        monkeypatch.setattr(
            cli_impl,
            "session_contract_audit_impl",
            lambda **_: _build_audit(total=10, healthy=9),
        )
        payload = cli_impl.session_contract_health_gate_impl(
            strict=False,
            min_healthy_ratio=0.5,
            policy_profile="strict_ci",
        )
        assert payload["policy_profile"] == "strict_ci"
        assert payload["threshold"] == 1.0
        assert payload["strict_checks_enabled"] is True
        assert payload["pass"] is False
        assert "ratio_below_threshold" in payload["decision_reasons"]

    def test_gate_baseline_regression_triggers_block(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        # @trace FR-GOV-002
        snapshot_path = tmp_path / "health-snapshots.jsonl"
        monkeypatch.setenv("THGENT_HEALTH_SNAPSHOT_PATH", str(snapshot_path))
        monkeypatch.setattr(
            cli_impl,
            "session_contract_audit_impl",
            lambda **_: _build_audit(total=10, healthy=10),
        )
        first = cli_impl.session_contract_health_gate_impl(
            policy_profile="warn_only",
            no_worse_than_baseline=False,
        )
        assert first["pass"] is True

        monkeypatch.setattr(
            cli_impl,
            "session_contract_audit_impl",
            lambda **_: _build_audit(total=10, healthy=9),
        )
        second = cli_impl.session_contract_health_gate_impl(
            policy_profile="warn_only",
            no_worse_than_baseline=True,
            regression_tolerance=0.0,
        )
        assert second["pass"] is False
        assert "baseline_regression" in second["decision_reasons"]
        assert second["trend_summary"]["baseline_available"] is True
        assert second["trend_summary"]["blocked_count_delta"] == 1

    def test_report_profile_rule_and_compat_aliases(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # @trace FR-GOV-002
        monkeypatch.setattr(
            cli_impl,
            "session_contract_audit_impl",
            lambda **_: _build_audit(total=10, healthy=9),
        )
        payload = cli_impl.session_contract_health_report_impl(
            policy_profile="prod_release",
        )
        assert payload["policy_profile"] == "prod_release"
        assert payload["pass"] is False
        assert "blocked_ratio_exceeds_profile" in payload["decision_reasons"]
        assert payload["compat"]["aliases"]["total_sessions"] == "total"
        assert payload["compat"]["aliases"]["blocked_sessions_count"] == "blocked_count"

    def test_health_trend_impl_returns_deltas(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        # @trace FR-GOV-002
        snapshot_path = tmp_path / "health-snapshots.jsonl"
        monkeypatch.setenv("THGENT_HEALTH_SNAPSHOT_PATH", str(snapshot_path))
        # Use fixed timestamps 600s apart so snapshot_window_seconds and snapshot_interval are deterministic
        t0 = datetime(2026, 2, 14, 12, 0, 0, tzinfo=UTC)
        t1 = datetime(2026, 2, 14, 12, 10, 0, tzinfo=UTC)
        t2 = datetime(2026, 2, 14, 12, 11, 0, tzinfo=UTC)
        times = iter([t0, t1, t2, t2, t2, t2])

        class MockDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                return next(times)

        # Patch in multiple places to be sure
        monkeypatch.setattr("thegent.cli.commands.impl.datetime", MockDateTime)
        import thegent.cli.commands.impl as mod

        monkeypatch.setattr(mod, "datetime", MockDateTime)

        monkeypatch.setattr(
            cli_impl,
            "session_contract_audit_impl",
            lambda **_: _build_audit(total=10, healthy=10),
        )
        cli_impl.session_contract_health_gate_impl(policy_profile="warn_only")
        monkeypatch.setattr(
            cli_impl,
            "session_contract_audit_impl",
            lambda **_: _build_audit(total=10, healthy=8),
        )
        cli_impl.session_contract_health_gate_impl(policy_profile="warn_only")

        trend = cli_impl.session_contract_health_trend_impl(
            payload_type="session_contract_health_gate",
            policy_profile="warn_only",
            limit=10,
        )
        assert trend["payload_type"] == "session_contract_health_trend"
        assert trend["trend_payload_type"] == "session_contract_health_gate"
        assert trend["scope_payload_type"] == "session_contract_health_gate"
        assert trend["scope_key_json"] == json.dumps(trend["scope_key"], sort_keys=True).decode()
        assert trend["scope_policy_profile"] == "warn_only"
        assert trend["scope_min_healthy_ratio"] == 0.0
        assert trend["scope_top_blocked"] is None
        assert trend["compat"]["aliases"]["scope.owner"] == "scope_owner"
        assert trend["compat"]["aliases"]["scope.top_blocked"] == "scope_top_blocked"
        assert trend["compat_aliases_count"] == len(trend["compat"]["aliases"])
        assert trend["latest_status"] == (trend.get("latest") or {}).get("status", "")
        assert trend["latest_pass"] == (trend.get("latest") or {}).get("pass", None)
        assert trend["latest_captured_at_utc"] == (trend.get("latest") or {}).get("captured_at_utc", "")
        assert trend["latest_blocked_ratio"] == (trend.get("latest") or {}).get("blocked_ratio", None)
        assert trend["latest_blocked_count"] == (trend.get("latest") or {}).get("blocked_count", None)
        assert trend["latest_issue_types_count"] == len((trend.get("latest") or {}).get("issue_types", []) or [])
        assert trend["latest_issue_types_json"] == json.dumps(
            (trend.get("latest").decode() or {}).get("issue_types", []) or []
        )
        assert (
            trend["latest_issue_types_hash"]
            == hashlib.sha256(trend["latest_issue_types_json"].encode("utf-8")).hexdigest()
        )
        expected_snapshot_ids_csv = ", ".join(
            [
                str((s or {}).get("captured_at_utc", ""))
                for s in (trend.get("snapshots", []) or [])
                if (s or {}).get("captured_at_utc", "")
            ]
        )
        assert trend["snapshot_ids_csv"] == expected_snapshot_ids_csv
        assert trend["snapshot_ids_hash"] == hashlib.sha256(expected_snapshot_ids_csv.encode("utf-8")).hexdigest()
        assert trend["snapshot_window_seconds"] == 600
        assert (
            trend["snapshot_window_hash"]
            == hashlib.sha256(str(trend["snapshot_window_seconds"]).encode("utf-8")).hexdigest()
        )
        assert trend["snapshot_interval_seconds_avg"] == 600
        assert (
            trend["snapshot_interval_hash"]
            == hashlib.sha256(str(trend["snapshot_interval_seconds_avg"]).encode("utf-8")).hexdigest()
        )
        assert trend["snapshot_density_per_hour"] == pytest.approx(12.0)
        assert (
            trend["snapshot_density_hash"]
            == hashlib.sha256(str(trend["snapshot_density_per_hour"]).encode("utf-8")).hexdigest()
        )
        assert trend["snapshot_issue_churn_count"] == 1
        assert (
            trend["snapshot_issue_churn_hash"]
            == hashlib.sha256(str(trend["snapshot_issue_churn_count"]).encode("utf-8")).hexdigest()
        )
        assert trend["snapshot_health_volatility"] == pytest.approx(0.1)
        assert (
            trend["snapshot_health_volatility_hash"]
            == hashlib.sha256(str(trend["snapshot_health_volatility"]).encode("utf-8")).hexdigest()
        )
        assert (
            trend["snapshot_freshness_hash"]
            == hashlib.sha256(str(trend["snapshot_freshness_seconds"]).encode("utf-8")).hexdigest()
        )
        if trend["snapshot_freshness_seconds"] is not None:
            assert isinstance(trend["snapshot_freshness_seconds"], int)
        assert trend["latest_issue_types_csv"] == ", ".join(
            [str(v) for v in ((trend.get("latest") or {}).get("issue_types", []) or [])]
        )
        assert trend["snapshot_count"] >= 2
        assert trend["delta_summary"]["blocked_count_delta"] == 2
        assert trend["delta_summary"]["blocked_ratio_delta"] == pytest.approx(0.2)
        assert trend["blocked_count_delta"] == trend["delta_summary"]["blocked_count_delta"]
        assert trend["blocked_ratio_delta"] == trend["delta_summary"]["blocked_ratio_delta"]
        assert trend["delta_summary_json"] == json.dumps(trend["delta_summary"], sort_keys=True).decode()
        assert trend["snapshot_retention_max_lines"] >= 100

        lines = snapshot_path.read_text(encoding="utf-8").splitlines()
        assert len(lines) >= 2
        first = json.loads(lines[0])
        assert first["record_type"] == "health_snapshot"

    def test_health_gate_impl_appends_normalized_issue_types_for_blocked_sessions(
        # @trace FR-GOV-002
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        snapshot_path = tmp_path / "health-snapshots.jsonl"
        monkeypatch.setenv("THGENT_HEALTH_SNAPSHOT_PATH", str(snapshot_path))
        monkeypatch.setattr(
            cli_impl,
            "session_contract_audit_impl",
            lambda **_: {
                "rows": [
                    {
                        "session_id": "s1",
                        "contract_state": "partial",
                        "contract_health": "error",
                        "contract_issues": "missing_contract:provider",
                        "started_at_utc": "2026-02-14T12:00:00Z",
                        "agent": "gemini",
                    }
                ],
                "summary": {
                    "total": 1,
                    "healthy": 0,
                    "warning": 0,
                    "error": 1,
                    "missing": 0,
                    "strict_checks_enabled": False,
                    "health": {"healthy": 0, "warning": 0, "error": 1, "missing": 0},
                    "total_sessions": 1,
                },
            },
        )
        cli_impl.session_contract_health_gate_impl(policy_profile="warn_only")
        lines = snapshot_path.read_text(encoding="utf-8").splitlines()
        assert lines, "health snapshot should be persisted"
        record = json.loads(lines[0])
        assert record["issue_types"] == ["missing_contract:provider"]

    def test_health_trend_invalid_payload_type_raises(self) -> None:
        # @trace FR-GOV-002
        with pytest.raises(typer.BadParameter):
            cli_impl.session_contract_health_trend_impl(payload_type="unknown")

    def test_health_trend_impl_single_snapshot_volatility_none_and_hash(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # @trace FR-GOV-002
        snapshot_path = tmp_path / "health-snapshots.jsonl"
        monkeypatch.setenv("THGENT_HEALTH_SNAPSHOT_PATH", str(snapshot_path))
        monkeypatch.setattr(
            cli_impl,
            "session_contract_audit_impl",
            lambda **_: _build_audit(total=10, healthy=10),
        )
        cli_impl.session_contract_health_gate_impl(policy_profile="warn_only")

        trend = cli_impl.session_contract_health_trend_impl(
            payload_type="session_contract_health_gate",
            policy_profile="warn_only",
            limit=10,
        )
        assert trend["snapshot_count"] == 1
        assert trend["snapshot_health_volatility"] is None
        assert trend["snapshot_health_volatility_hash"] == hashlib.sha256(str(None).encode("utf-8")).hexdigest()

    def test_health_trend_impl_normalizes_malformed_issue_types_in_snapshots(
        # @trace FR-GOV-002
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        snapshot_path = tmp_path / "health-snapshots.jsonl"
        monkeypatch.setenv("THGENT_HEALTH_SNAPSHOT_PATH", str(snapshot_path))

        payload = {
            "payload_type": "session_contract_health_report",
            "policy_profile": "custom",
            "generated_query": {
                "owner": None,
                "all": False,
                "strict": False,
                "top_blocked": 25,
            },
        }
        scope_key = cli_impl._health_scope_key(payload)
        oldest = {
            "record_type": "health_snapshot",
            "captured_at_utc": "2026-02-14T12:00:00Z",
            "scope_key": scope_key,
            "schema_version": "health-schema-v1",
            "payload_type": "session_contract_health_report",
            "status": "passed",
            "pass": True,
            "total": 10,
            "healthy_count": 10,
            "unhealthy_count": 0,
            "blocked_count": 0,
            "blocked_ratio": 0.0,
            "issue_types": "scalar-issue",
            "issue_counts": {"scalar-issue": 10},
        }
        latest = {
            "record_type": "health_snapshot",
            "captured_at_utc": "2026-02-14T12:10:00Z",
            "scope_key": scope_key,
            "schema_version": "health-schema-v1",
            "payload_type": "session_contract_health_report",
            "status": "blocked",
            "pass": False,
            "total": 10,
            "healthy_count": 9,
            "unhealthy_count": 1,
            "blocked_count": 1,
            "blocked_ratio": 0.1,
            "issue_types": {"left": 1, "right": 1},
            "issue_counts": {"left": 3, "right": 3},
        }
        snapshot_path.write_text(
            "\n".join([json.dumps(oldest).decode(), json.dumps(latest).decode()]) + "\n",
            encoding="utf-8",
        )

        trend = cli_impl.session_contract_health_trend_impl(
            payload_type="session_contract_health_report",
            policy_profile="custom",
            limit=10,
        )
        assert trend["snapshot_count"] == 2
        assert trend["latest_issue_types_count"] == 2
        assert trend["latest_issue_types_csv"] == "left, right"
        assert trend["latest_issue_types_json"] == json.dumps(["left", "right"]).decode()
        assert (
            trend["latest_issue_types_hash"]
            == hashlib.sha256(trend["latest_issue_types_json"].encode("utf-8")).hexdigest()
        )
        assert trend["snapshot_issue_churn_count"] == 3

    def test_health_report_impl_normalizes_contract_issues_for_issues_counts_and_rows(
        # @trace FR-GOV-002
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        audit_payload = {
            "rows": [
                {
                    "session_id": "s-good",
                    "owner": "alice",
                    "contract_state": "complete",
                    "contract_health": "healthy",
                    "contract_issues": [],
                    "started_at_utc": "2026-02-14T12:00:00Z",
                    "agent": "gemini",
                },
                {
                    "session_id": "s-bad",
                    "owner": "alice",
                    "contract_state": "partial",
                    "contract_health": "error",
                    "contract_issues": "missing_contract",
                    "started_at_utc": "2026-02-14T12:01:00Z",
                    "agent": "gemini",
                },
            ],
            "summary": {
                "total": 2,
                "complete": 1,
                "partial": 1,
                "request_only": 0,
                "contract_only": 0,
                "untracked": 0,
                "strict_checks_enabled": False,
                "health": {"healthy": 1, "warning": 0, "error": 1, "missing": 0},
            },
        }
        monkeypatch.setattr(
            cli_impl,
            "session_contract_audit_impl",
            lambda **_: audit_payload,
        )

        report = cli_impl.session_contract_health_report_impl(
            policy_profile="warn_only",
            top_blocked=25,
        )
        assert report["issue_counts"] == {"missing_contract": 1}
        assert report["top_blocked"][0]["issues"] == ["missing_contract"]
        assert report["blocked_count"] == 1

    def test_health_gate_impl_normalizes_previous_snapshot_issue_types_and_deltas(
        # @trace FR-GOV-002
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        snapshot_path = tmp_path / "health-snapshots.jsonl"
        monkeypatch.setenv("THGENT_HEALTH_SNAPSHOT_PATH", str(snapshot_path))
        # warn_only profile resolves min_healthy_ratio to 0.0, so scope_key must match
        scope_payload = {
            "payload_type": "session_contract_health_gate",
            "policy_profile": "warn_only",
            "generated_query": {
                "owner": None,
                "all": False,
                "strict": False,
                "min_healthy_ratio": 0.0,
            },
        }
        scope_key = cli_impl._health_scope_key(scope_payload)
        previous_snapshot = {
            "record_type": "health_snapshot",
            "captured_at_utc": "2026-02-14T12:00:00Z",
            "scope_key": scope_key,
            "schema_version": "health-schema-v1",
            "payload_type": "session_contract_health_gate",
            "status": "passed",
            "pass": True,
            "total": 3,
            "healthy_count": 3,
            "unhealthy_count": 0,
            "blocked_count": 0,
            "blocked_ratio": 0.0,
            "issue_types": "blocked-session-a",
            "issue_counts": {"blocked-session-a": 1},
            "blocked_sessions": [],
            "payload_signature": {},
        }
        latest_snapshot = {
            "record_type": "health_snapshot",
            "captured_at_utc": "2026-02-14T12:01:00Z",
            "scope_key": scope_key,
            "schema_version": "health-schema-v1",
            "payload_type": "session_contract_health_gate",
            "status": "blocked",
            "pass": False,
            "total": 3,
            "healthy_count": 2,
            "unhealthy_count": 1,
            "blocked_count": 1,
            "blocked_ratio": 1.0 / 3.0,
            "issue_types": {"x": 1},
            "issue_counts": {"x": 1},
            "blocked_sessions": [
                {
                    "session_id": "s1",
                    "state": "open",
                    "health": "error",
                    "issues": "ab",
                }
            ],
            "payload_signature": {},
        }
        snapshot_path.write_text(
            "\n".join(
                [
                    json.dumps(previous_snapshot).decode(),
                    json.dumps(latest_snapshot).decode(),
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(
            cli_impl,
            "session_contract_audit_impl",
            lambda **_: _build_audit(total=3, healthy=2),
        )

        trend = cli_impl.session_contract_health_trend_impl(
            payload_type="session_contract_health_gate",
            policy_profile="warn_only",
            limit=10,
        )
        assert trend["snapshot_count"] == 2
        assert trend["latest_issue_types_count"] == 1
        assert trend["snapshot_issue_churn_count"] == 2
        assert trend["delta_summary"]["blocked_count_delta"] == 1
        assert trend["delta_summary"]["blocked_ratio_delta"] == pytest.approx(1.0 / 3.0)
        assert trend["latest"]["issue_types"] == {"x": 1}


@pytest.mark.unit
class TestHealthSnapshotRetention:
    def test_snapshot_max_lines_default_and_min_floor(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # @trace FR-GOV-002
        monkeypatch.delenv("THGENT_HEALTH_SNAPSHOT_MAX_LINES", raising=False)
        assert cli_impl._health_snapshot_max_lines() == 5000

        monkeypatch.setenv("THGENT_HEALTH_SNAPSHOT_MAX_LINES", "12")
        assert cli_impl._health_snapshot_max_lines() == 100

        monkeypatch.setenv("THGENT_HEALTH_SNAPSHOT_MAX_LINES", "250")
        assert cli_impl._health_snapshot_max_lines() == 250

    def test_snapshot_compaction_trims_to_limit(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        # @trace FR-GOV-002
        snapshot_path = tmp_path / "health-snapshots.jsonl"
        monkeypatch.setenv("THGENT_HEALTH_SNAPSHOT_PATH", str(snapshot_path))
        monkeypatch.setenv("THGENT_HEALTH_SNAPSHOT_MAX_LINES", "100")

        lines = []
        for i in range(160):
            lines.append(json.dumps({"record_type": "health_snapshot", "i": i}).decode())
        snapshot_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        cli_impl._compact_health_snapshot_log()
        kept = snapshot_path.read_text(encoding="utf-8").splitlines()
        assert len(kept) == 100
        first = json.loads(kept[0])
        last = json.loads(kept[-1])
        assert first["i"] == 60
        assert last["i"] == 159
