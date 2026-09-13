"""E2E tests for health trend/policy CLI commands."""

from __future__ import annotations

import orjson as json
import pytest
from typer.testing import CliRunner

from thegent.main import app

runner = CliRunner()


@pytest.mark.e2e
class TestHealthTrendCLI:
    def test_health_trend_json_empty_scope(self, tmp_path) -> None:
        # @trace FR-CLI-001
        snapshot_path = tmp_path / "health-snapshots.jsonl"
        result = runner.invoke(
            app,
            [
                "session-contract-health-trend",
                "--format",
                "json",
                "--payload-type",
                "session_contract_health_report",
                "--limit",
                "5",
            ],
            env={
                "THGENT_HEALTH_SNAPSHOT_PATH": str(snapshot_path),
                "THGENT_SESSION_DIR": str(tmp_path / "sessions"),
            },
        )
        assert result.exit_code == 0
        payload = json.loads(result.stdout)
        assert payload["payload_type"] == "session_contract_health_trend"
        assert payload["trend_payload_type"] == "session_contract_health_report"
        assert payload["snapshot_count"] == 0
        assert payload["compat"]["mode"] == "compat"
        assert payload["compat"]["aliases"]["scope.owner"] == "scope_owner"

    def test_health_trend_rich_output_has_generated_timestamp(self, tmp_path) -> None:
        # @trace FR-CLI-001
        result = runner.invoke(
            app,
            [
                "session-contract-health-trend",
                "--payload-type",
                "session_contract_health_report",
            ],
            env={
                "THGENT_HEALTH_SNAPSHOT_PATH": str(tmp_path / "health-snapshots.jsonl"),
                "THGENT_SESSION_DIR": str(tmp_path / "sessions"),
            },
        )
        assert result.exit_code == 0
        assert "generated_at_utc=" in result.stdout
        assert "compat_mode=" in result.stdout
        assert "compat_aliases_count=" in result.stdout

    def test_health_trend_md_output(self, tmp_path) -> None:
        # @trace FR-CLI-001
        result = runner.invoke(
            app,
            [
                "session-contract-health-trend",
                "--format",
                "md",
                "--payload-type",
                "session_contract_health_gate",
            ],
            env={
                "THGENT_HEALTH_SNAPSHOT_PATH": str(tmp_path / "health-snapshots.jsonl"),
                "THGENT_SESSION_DIR": str(tmp_path / "sessions"),
            },
        )
        assert result.exit_code == 0
        assert "Session Contract Health Trend" in result.stdout
        assert "session_contract_health_gate" in result.stdout
        assert "compat_mode" in result.stdout
        assert "compat_aliases" in result.stdout
        assert "latest_status" in result.stdout
        assert "latest_pass" in result.stdout
        assert "latest_issue_types_count" in result.stdout
        assert "scope_owner" in result.stdout
        assert "scope_all" in result.stdout
        assert "scope_strict" in result.stdout
        assert "scope_policy_profile" in result.stdout

    def test_health_trend_export_json(self, tmp_path) -> None:
        # @trace FR-CLI-001
        out = tmp_path / "trend.json"
        result = runner.invoke(
            app,
            [
                "session-contract-health-trend",
                "--format",
                "json",
                "--output",
                str(out),
                "--export-format",
                "json",
                "--overwrite",
            ],
            env={
                "THGENT_HEALTH_SNAPSHOT_PATH": str(tmp_path / "health-snapshots.jsonl"),
                "THGENT_SESSION_DIR": str(tmp_path / "sessions"),
            },
        )
        assert result.exit_code == 0
        assert out.exists()
        payload = json.loads(out.read_text(encoding="utf-8"))
        assert payload["payload_type"] == "session_contract_health_trend"
        assert payload["compat"]["mode"] == "compat"
        assert payload["compat"]["aliases"]["scope.policy_profile"] == "scope_policy_profile"

    def test_health_trend_export_csv(self, tmp_path) -> None:
        # @trace FR-CLI-001
        out = tmp_path / "trend.csv"
        result = runner.invoke(
            app,
            [
                "session-contract-health-trend",
                "--output",
                str(out),
                "--export-format",
                "csv",
                "--overwrite",
            ],
            env={
                "THGENT_HEALTH_SNAPSHOT_PATH": str(tmp_path / "health-snapshots.jsonl"),
                "THGENT_SESSION_DIR": str(tmp_path / "sessions"),
            },
        )
        assert result.exit_code == 0
        assert out.exists()
        text = out.read_text(encoding="utf-8")
        assert "record_type" in text
        assert "compat_mode" in text
        assert "compat_aliases_json" in text
        assert "generated_at_utc" in text
        assert "summary" in text
        assert "latest_captured_at_utc" in text
        assert "latest_blocked_ratio" in text
        assert "latest_blocked_count" in text
        assert "latest_issue_types_count" in text

    def test_health_trend_export_md(self, tmp_path) -> None:
        # @trace FR-CLI-001
        out = tmp_path / "trend.md"
        result = runner.invoke(
            app,
            [
                "session-contract-health-trend",
                "--output",
                str(out),
                "--export-format",
                "md",
                "--overwrite",
            ],
            env={
                "THGENT_HEALTH_SNAPSHOT_PATH": str(tmp_path / "health-snapshots.jsonl"),
                "THGENT_SESSION_DIR": str(tmp_path / "sessions"),
            },
        )
        assert result.exit_code == 0
        assert out.exists()
        text = out.read_text(encoding="utf-8")
        assert "Session Contract Health Trend" in text
        assert "generated_at_utc" in text
        assert "compat_mode" in text
        assert "compat_aliases" in text
        assert "latest_status" in text
        assert "latest_captured_at_utc" in text
        assert "latest_blocked_ratio" in text
        assert "latest_blocked_count" in text
        assert "latest_issue_types_count" in text
        assert "scope_owner" in text
        assert "scope_all" in text
        assert "scope_strict" in text
        assert "scope_policy_profile" in text

    def test_health_trend_export_jsonl(self, tmp_path) -> None:
        # @trace FR-CLI-001
        out = tmp_path / "trend.jsonl"
        result = runner.invoke(
            app,
            [
                "session-contract-health-trend",
                "--output",
                str(out),
                "--export-format",
                "jsonl",
                "--overwrite",
            ],
            env={
                "THGENT_HEALTH_SNAPSHOT_PATH": str(tmp_path / "health-snapshots.jsonl"),
                "THGENT_SESSION_DIR": str(tmp_path / "sessions"),
            },
        )
        assert result.exit_code == 0
        assert out.exists()
        lines = [line for line in out.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert len(lines) >= 1
        first = json.loads(lines[0])
        assert first["record_type"] == "summary"
        assert first["payload_type"] == "session_contract_health_trend"
        assert first["compat"]["mode"] == "compat"
        assert "generated_at_utc" in first
        assert "latest_captured_at_utc" in first
        assert "latest_blocked_ratio" in first
        assert "latest_blocked_count" in first
        assert "latest_issue_types_count" in first
        assert "scope_owner" in first
        assert "scope_all" in first
        assert "scope_strict" in first
        assert "scope_policy_profile" in first
        if len(lines) > 1:
            second = json.loads(lines[1])
            assert second["record_type"] == "snapshot"
            assert second["compat_mode"] == "compat"
            assert "compat_aliases" in second

    def test_health_trend_export_refuses_overwrite_without_flag(self, tmp_path) -> None:
        # @trace FR-CLI-001
        out = tmp_path / "trend.json"
        out.write_text("{}", encoding="utf-8")
        result = runner.invoke(
            app,
            [
                "session-contract-health-trend",
                "--output",
                str(out),
                "--export-format",
                "json",
            ],
            env={
                "THGENT_HEALTH_SNAPSHOT_PATH": str(tmp_path / "health-snapshots.jsonl"),
                "THGENT_SESSION_DIR": str(tmp_path / "sessions"),
            },
        )
        assert result.exit_code != 0
        assert "already exists" in result.stdout

    def test_health_trend_export_invalid_format_fails(self, tmp_path) -> None:
        # @trace FR-CLI-001
        out = tmp_path / "trend.out"
        result = runner.invoke(
            app,
            [
                "session-contract-health-trend",
                "--output",
                str(out),
                "--export-format",
                "xml",
            ],
            env={
                "THGENT_HEALTH_SNAPSHOT_PATH": str(tmp_path / "health-snapshots.jsonl"),
                "THGENT_SESSION_DIR": str(tmp_path / "sessions"),
            },
        )
        assert result.exit_code != 0
        assert "Unsupported --export-format" in result.stdout


@pytest.mark.e2e
class TestHealthPolicyFlagsCLI:
    def test_health_gate_policy_flags_json(self, tmp_path) -> None:
        # @trace FR-CLI-001
        result = runner.invoke(
            app,
            [
                "session-contract-health-gate",
                "--format",
                "json",
                "--policy-profile",
                "strict_ci",
                "--no-worse-than-baseline",
                "--regression-tolerance",
                "0.05",
            ],
            env={"THGENT_SESSION_DIR": str(tmp_path / "sessions")},
        )
        payload = json.loads(result.stdout)
        assert payload["policy_profile"] == "strict_ci"
        assert "policy_evaluation" in payload
        assert payload["policy_evaluation"]["enforce_no_worse_than_baseline"] is True

    def test_health_report_policy_flags_json(self, tmp_path) -> None:
        # @trace FR-CLI-001
        result = runner.invoke(
            app,
            [
                "session-contract-health-report",
                "--format",
                "json",
                "--policy-profile",
                "prod_release",
                "--no-worse-than-baseline",
                "--regression-tolerance",
                "0.01",
            ],
            env={"THGENT_SESSION_DIR": str(tmp_path / "sessions")},
        )
        assert result.exit_code == 0
        payload = json.loads(result.stdout)
        assert payload["policy_profile"] == "prod_release"
        assert "trend_summary" in payload
        assert "compat" in payload
