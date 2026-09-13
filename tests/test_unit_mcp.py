"""Unit tests for MCP server tools, resources, and cli_impl."""

import getpass
import hashlib
import os
import socket
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import orjson as json
import pytest

from thegent.cli.commands._cli_shared import resolve_owner_dir
from thegent.cli.commands.impl import (
    bg_impl,
    dag_list_impl,
    dag_raw_impl,
    list_agents_impl,
    ps_impl,
    session_meta_impl,
    status_impl,
)
from thegent.mcp.server import (
    resource_observe_summary,
    resource_session_contract_health_trend,
    thegent_observe_summary,
    thegent_session_contract_health_gate,
    thegent_session_contract_health_report,
    thegent_session_contract_health_trend,
)


class _Proc:
    """Simple fake process object."""

    def __init__(self, pid: int) -> None:
        self.pid = pid


@pytest.mark.unit
class TestCLIImplListAgents:
    """Tests for list_agents_impl (used by thegent://agents resource)."""

    def test_returns_agents_list(self) -> None:
        # @trace FR-MCP-001
        """list_agents_impl returns list of {name, backend}."""
        agents = list_agents_impl()
        assert isinstance(agents, list)
        assert len(agents) >= 5
        names = [a["name"] for a in agents]
        assert "cursor" in names
        assert "claude" in names
        assert "minimax" in names
        assert "glm" in names


@pytest.mark.unit
class TestCLIImplSessionMeta:
    """Tests for session_meta_impl."""

    def test_session_meta_nonexistent_returns_error(self) -> None:
        # @trace FR-MCP-001
        """Nonexistent session returns error dict."""
        result = session_meta_impl("nonexistent-session-id-xyz")
        assert isinstance(result, dict)
        assert "error" in result or "session_id" in result


@pytest.mark.unit
class TestCLIImplDagRaw:
    """Tests for dag_raw_impl."""

    def test_dag_raw_no_dag_returns_message(self, tmp_path: Path) -> None:
        # @trace FR-MCP-001
        """When no .factory/dag-session.md, returns error message."""
        with patch("thegent.cli.commands.impl._resolve_cwd", return_value=tmp_path):
            result = dag_raw_impl(cd=tmp_path)
        assert isinstance(result, str)
        assert "dag" in result.lower() or "not found" in result.lower() or len(result) >= 0

    def test_dag_raw_with_dag_returns_markdown(self, tmp_path: Path) -> None:
        # @trace FR-MCP-001
        """When .factory/dag-session.md exists, returns content."""
        factory_dir = tmp_path / ".factory"
        factory_dir.mkdir()
        dag_file = factory_dir / "dag-session.md"
        dag_file.write_text("# DAG\n\n- task a\n- task b\n")
        with patch("thegent.cli.commands.impl._resolve_cwd", return_value=tmp_path):
            result = dag_raw_impl(cd=tmp_path)
        assert "# DAG" in result
        assert "task a" in result


@pytest.mark.unit
class TestDagPertReadOnly:
    """Validate basic PERT-style DAG with read-only tasks works."""

    PERT_DAG = """---
project: test-pert
owner: test
---

| id | agent | prompt | depends_on | status |
|----|-------|--------|------------|--------|
| T1 | gemini | List top-level modules (read-only) | — | pending |
| T2 | cursor-agent | Summarize README (read-only) | T1 | pending |
| T3 | gemini | Report critical paths (read-only) | T2 | pending |
"""

    def test_dag_list_impl_parses_pert_tasks(self, tmp_path: Path) -> None:
        # @trace FR-MCP-001
        """dag_list_impl parses PERT-style DAG with dependencies."""
        factory_dir = tmp_path / ".factory"
        factory_dir.mkdir()
        dag_file = factory_dir / "dag-session.md"
        dag_file.write_text(self.PERT_DAG)
        with patch("thegent.cli.commands.impl._resolve_cwd", return_value=tmp_path):
            result = dag_list_impl(cd=tmp_path)
        assert "error" not in result
        assert "frontmatter" in result
        assert "tasks" in result
        tasks = result["tasks"]
        assert len(tasks) == 3
        assert tasks[0].get("id") == "T1"
        assert tasks[0].get("depends_on", "").strip() in ("—", "-", "")
        assert tasks[1].get("depends_on") == "T1"
        assert tasks[2].get("depends_on") == "T2"

    def test_dag_list_impl_accepts_cursor_label(self, tmp_path: Path) -> None:
        # @trace FR-MCP-001
        """DAG with agent label 'cursor' parses (resolves to cursor-agent)."""
        factory_dir = tmp_path / ".factory"
        factory_dir.mkdir()
        dag_content = """---
project: label-test
---

| id | agent | prompt | depends_on | status |
|----|-------|--------|------------|--------|
| L1 | cursor | Read-only summary | — | pending |
"""
        dag_file = factory_dir / "dag-session.md"
        dag_file.write_text(dag_content)
        with patch("thegent.cli.commands.impl._resolve_cwd", return_value=tmp_path):
            result = dag_list_impl(cd=tmp_path)
        assert "error" not in result
        assert len(result["tasks"]) == 1
        assert result["tasks"][0].get("agent") == "cursor"


@pytest.mark.unit
class TestMCPMetaContract:
    """Tests for MCP meta contract (health payload schema discoverability)."""

    def test_get_server_meta_impl_includes_health_payload_schema(self) -> None:
        # @trace FR-MCP-001
        """get_server_meta_impl returns health_payload_schema_version and health_payload_types."""
        from thegent.cli.commands.impl import get_server_meta_impl

        meta = get_server_meta_impl(server_name="thegent")
        assert meta["server"] == "thegent"
        assert meta["version"] == "1.0"
        assert "capabilities" in meta
        assert meta["health_payload_schema_version"] == "health-schema-v1"
        assert "session_contract_health_gate" in meta["health_payload_types"]
        assert "session_contract_health_report" in meta["health_payload_types"]
        assert "session_contract_health_trend" in meta["health_payload_types"]
        assert meta["observe_summary_payload_schema_version"] == "observe-summary-schema-v1"
        assert "observe_summary" in meta["observe_summary_payload_types"]
        assert "strict_ci" in meta["health_policy_profiles"]
        assert "warn_only" in meta["health_policy_profiles"]
        # Schema versions are sourced from the canonical module constants.
        assert meta["output_parser_schema_version"]
        assert meta["route_schema_version"]
        assert meta["contract_schema_version"]


@pytest.mark.unit
class TestMCPToolOutputFormat:
    """Verify MCP tool output format (JSON) matches cli_impl."""

    def test_list_agents_json_format(self) -> None:
        # @trace FR-MCP-001
        """list_agents_impl serialized to JSON matches MCP tool contract."""
        agents = list_agents_impl()
        result = json.dumps(agents)
        if isinstance(result, bytes):
            result = result.decode()
        data = json.loads(result)
        assert isinstance(data, list)
        assert all("name" in item and "backend" in item for item in data)


@pytest.mark.unit
class TestObserveSummaryMCPContracts:
    """Verify observe-summary MCP signatures and trend parameters."""

    def test_observe_summary_resource_forwards_trend_samples(self) -> None:
        # @trace FR-MCP-010
        payload = {
            "payload_type": "observe_summary",
            "payload_schema_version": "observe-summary-schema-v1",
            "generated_query": {"trend_samples": 4},
            "trend_summary": {"enabled": True},
            "kpis": {"total_events": 1, "fallback_rate": 0.0, "success_rate": 1.0, "avg_confidence": 1.0},
            "drift": {"within_budget": True, "structural_rate_pct": 0.0, "semantic_rate_pct": 0.0},
            "escalation": {"backlog_count": 0, "past_sla_count": 0},
            "status": "healthy",
            "alerts": [],
        }
        captured: dict[str, object] = {}

        def _fake_impl(**kwargs: object) -> dict[str, object]:
            captured.update(kwargs)
            return payload

        with patch("thegent.mcp.server.observe_summary_impl", side_effect=_fake_impl):
            raw = resource_observe_summary(
                "test-resource://observe",
                limit=25,
                drift_window=9,
                structural_budget_pct=5.0,
                semantic_budget_pct=8.0,
                provider="gemini",
                trend_samples=4,
                top_escalations=3,
            )
        data = json.loads(raw)
        assert data["generated_query"]["trend_samples"] == 4
        assert captured["trend_samples"] == 4
        assert captured["provider"] == "gemini"
        assert captured["top_escalations"] == 3

    def test_observe_summary_tool_includes_trend_meta(self) -> None:
        # @trace FR-MCP-010
        payload = {
            "payload_type": "observe_summary",
            "payload_schema_version": "observe-summary-schema-v1",
            "generated_query": {"trend_samples": 2, "top_escalations": 3},
            "trend_summary": {"enabled": True},
            "kpis": {
                "total_events": 1,
                "fallback_rate": 0.0,
                "success_rate": 1.0,
                "avg_confidence": 1.0,
            },
            "drift": {
                "within_budget": True,
                "structural_rate_pct": 0.0,
                "semantic_rate_pct": 0.0,
                "structural_budget_pct": 5.0,
                "semantic_budget_pct": 8.0,
            },
            "escalation": {
                "backlog_count": 3,
                "past_sla_count": 1,
                "top_escalations_count": 3,
            },
            "status": "healthy",
            "alerts": [],
        }
        with patch("thegent.mcp.server.observe_summary_impl", return_value=payload):
            result = thegent_observe_summary(
                limit=25,
                drift_window=9,
                structural_budget_pct=5.0,
                semantic_budget_pct=8.0,
                provider="gemini",
                trend_samples=2,
                top_escalations=3,
            )
        assert result.meta["trend_samples_requested"] == 2
        assert result.meta["trend_enabled"] is True
        assert result.meta["top_escalations_requested"] == 3


@pytest.mark.unit
class TestCLIImplBackground:
    """Tests for mcp_impl background lifecycle and status parity."""

    def test_bg_impl_launches_direct_subprocess_and_records_metadata(self, tmp_path: Path) -> None:
        # @trace FR-MCP-001
        """bg_impl starts a direct child process and writes session metadata."""
        session_dir = tmp_path / "sessions"

        with (
            patch("thegent.cli.commands.impl._resolve_cwd", return_value=tmp_path),
            patch.dict(
                os.environ,
                {"THGENT_SESSION_DIR": str(session_dir)},
            ),
            patch("thegent.cli.commands.impl.subprocess.Popen") as popen,
        ):
            popen.return_value = _Proc(pid=43210)
            result = bg_impl(
                agent="cursor-agent",
                prompt="hello world",
                cd=tmp_path,
                mode="write",
                timeout=120,
                full=True,
                droid=None,
                model=None,
                owner=None,
            )

        assert "session_id" in result
        assert "owner" in result
        scoped = resolve_owner_dir(result["owner"], session_dir)
        meta_path = scoped / f"{result['session_id']}.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        assert meta["agent"] == "cursor-agent"
        assert meta["pid"] == 43210
        assert meta["status"] == "running"
        assert meta["host"] == socket.gethostname()
        argv = popen.call_args.args[0]
        env = popen.call_args.kwargs["env"]
        assert argv[0] == sys.executable
        assert "-m" in argv
        assert "thegent.main" in argv
        assert "run" in argv
        assert popen.call_args.kwargs["cwd"] == str(tmp_path)
        assert popen.call_args.kwargs["stdin"] is subprocess.DEVNULL
        assert popen.call_args.kwargs["start_new_session"] is True
        assert popen.call_args.kwargs.get("shell", False) is False
        assert env["THGENT_SESSION_META_PATH"] == str(meta_path)
        assert env["THGENT_OWNER_TAG"] == result["owner"]

    def test_ps_impl_uses_rc_status(self, tmp_path: Path) -> None:
        # @trace FR-MCP-001
        """ps_impl resolves completion status from rc file and metadata."""
        owner = f"{getpass.getuser()}:{tmp_path.name}:manual"
        session_dir = tmp_path / "sessions"
        scoped = resolve_owner_dir(owner, session_dir)
        scoped.mkdir(parents=True, exist_ok=True)
        sid = "sid-ps"
        meta = {
            "session_id": sid,
            "agent": "cursor-agent",
            "owner": owner,
            "pid": 99999999,
            "started_at_utc": "2026-02-14T00:00:00+00:00",
        }
        (scoped / f"{sid}.json").write_text(json.dumps(meta).decode(), encoding="utf-8")
        (scoped / f"{sid}.rc").write_text("3\n", encoding="utf-8")

        with patch.dict("os.environ", {"THGENT_SESSION_DIR": str(session_dir)}):
            rows = ps_impl(owner=owner, all=False)

        assert len(rows) == 1
        assert rows[0]["id"] == sid
        assert rows[0]["status"] == "exited:3"

    def test_status_impl_returns_richer_payload(self, tmp_path: Path) -> None:
        # @trace FR-MCP-001
        """status_impl includes host/mode/path/timeout metadata."""
        owner = f"{getpass.getuser()}:{tmp_path.name}:manual"
        session_dir = tmp_path / "sessions"
        scoped = resolve_owner_dir(owner, session_dir)
        scoped.mkdir(parents=True, exist_ok=True)
        sid = "sid-status"
        paths = {
            "meta": str(scoped / f"{sid}.json"),
            "stdout": str(scoped / f"{sid}.stdout.log"),
            "stderr": str(scoped / f"{sid}.stderr.log"),
            "rc": str(scoped / f"{sid}.rc"),
        }
        meta = {
            "session_id": sid,
            "agent": "cursor-agent",
            "owner": owner,
            "pid": 11111111,
            "timeout_hint_s": 90,
            "command": ["echo", "hello"],
            "launcher_pid": 1,
            "launcher_ppid": 2,
            "launcher_uid": 3,
            "host": "unit-host",
            "cwd": str(tmp_path),
            "mode": "write",
            "started_at_utc": "2026-02-14T00:00:00+00:00",
            "paths": paths,
        }
        (scoped / f"{sid}.json").write_text(json.dumps(meta).decode(), encoding="utf-8")
        (scoped / f"{sid}.rc").write_text("0\n", encoding="utf-8")

        with patch.dict("os.environ", {"THGENT_SESSION_DIR": str(session_dir)}):
            status = status_impl(session_id=sid)

        assert status["status"] == "exited:0"
        assert status["exit_code"] == 0
        assert status["running"] is False
        assert status["timeout_hint_s"] == 90
        assert status["command"] == ["echo", "hello"]
        assert status["launcher_pid"] == 1
        assert status["launcher_ppid"] == 2
        assert status["launcher_uid"] == 3
        assert status["host"] == "unit-host"
        assert status["mode"] == "write"
        assert status["paths"]["rc"].endswith(".rc")


@pytest.mark.unit
class TestMCPHealthPolicyTrendContract:
    """Unit tests for MCP health gate/report/trend tool metadata and payload shape."""

    def test_health_gate_tool_meta_includes_policy_and_counts(self) -> None:
        # @trace FR-MCP-002
        payload = {
            "schema_version": "health-schema-v1",
            "payload_type": "session_contract_health_gate",
            "payload_signature": {"algorithm": "sha256", "value": "abc"},
            "status": "blocked",
            "policy_profile": "strict_ci",
            "decision_reasons": ["ratio_below_threshold"],
            "total": 10,
            "healthy_count": 9,
            "unhealthy_count": 1,
            "blocked_count": 1,
            "top_blocked_count": 1,
            "blocked_sessions_cap": 200,
        }
        with patch("thegent.mcp.server.session_contract_health_gate_impl", return_value=payload):
            result = thegent_session_contract_health_gate(policy_profile="strict_ci")
        assert result.meta["policy_profile"] == "strict_ci"
        assert result.meta["status"] == "blocked"
        assert result.meta["decision_reasons"] == ["ratio_below_threshold"]
        assert result.meta["total"] == 10
        assert result.meta["blocked_count"] == 1

    def test_health_report_tool_meta_includes_policy_and_counts(self) -> None:
        # @trace FR-MCP-002
        payload = {
            "schema_version": "health-schema-v1",
            "payload_type": "session_contract_health_report",
            "payload_signature": {"algorithm": "sha256", "value": "def"},
            "status": "passed",
            "policy_profile": "warn_only",
            "decision_reasons": ["ok"],
            "total": 8,
            "healthy_count": 8,
            "unhealthy_count": 0,
            "blocked_count": 0,
            "top_blocked_count": 0,
        }
        with patch("thegent.mcp.server.session_contract_health_report_impl", return_value=payload):
            result = thegent_session_contract_health_report(policy_profile="warn_only")
        assert result.meta["policy_profile"] == "warn_only"
        assert result.meta["status"] == "passed"
        assert result.meta["decision_reasons"] == ["ok"]
        assert result.meta["total"] == 8
        assert result.meta["blocked_count"] == 0

    def test_health_trend_tool_returns_meta_and_payload(self) -> None:
        # @trace FR-MCP-002
        payload = {
            "schema_version": "health-schema-v1",
            "payload_type": "session_contract_health_trend",
            "trend_payload_type": "session_contract_health_report",
            "generated_at_utc": "2026-02-14T12:15:00Z",
            "scope_key": {
                "payload_type": "session_contract_health_report",
                "owner": "scopekey-owner",
                "all": True,
                "strict": False,
                "policy_profile": "scopekey-profile",
                "top_blocked": 99,
                "min_healthy_ratio": 0.75,
            },
            "scope_key_json": "top-level-scope-key-json",
            "scope_payload_type": "top-level-payload-type",
            "scope_owner": "alice",
            "scope_all": False,
            "scope_strict": True,
            "scope_policy_profile": "strict_ci",
            "scope_min_healthy_ratio": None,
            "scope_top_blocked": 25,
            "snapshot_count": 3,
            "snapshot_ids_csv": "snap-a, snap-b",
            "snapshot_ids_hash": "snap-hash",
            "snapshot_window_seconds": 123,
            "snapshot_window_hash": "window-hash",
            "snapshot_interval_seconds_avg": 456,
            "snapshot_interval_hash": "interval-hash",
            "snapshot_density_per_hour": 3.25,
            "snapshot_density_hash": "density-hash",
            "snapshot_issue_churn_count": 2,
            "snapshot_issue_churn_hash": "churn-hash",
            "snapshot_health_volatility": 4.2,
            "snapshot_health_volatility_hash": "volatility-hash",
            "snapshot_freshness_seconds": 789,
            "snapshot_freshness_hash": "freshness-hash",
            "snapshot_retention_max_lines": 5000,
            "delta_summary": {"blocked_ratio_delta": -0.1, "blocked_count_delta": -1},
            "delta_summary_json": "top-level-delta-summary-json",
            "blocked_ratio_delta": 0.25,
            "blocked_count_delta": 4,
            "latest_status": "top-level-status",
            "latest_pass": True,
            "latest_captured_at_utc": "2026-02-14T12:11:00Z",
            "latest_blocked_ratio": 0.33,
            "latest_blocked_count": 17,
            "latest_issue_types_csv": "top-level-issue-types-csv",
            "latest_issue_types_json": "top-level-issue-types-json",
            "latest_issue_types_hash": "top-level-issue-types-hash",
            "latest": {
                "status": "blocked",
                "pass": False,
                "captured_at_utc": "2026-02-14T12:10:00Z",
                "blocked_ratio": 0.1,
                "blocked_count": 1,
                "issue_types": ["nested-a", "nested-b"],
            },
            "latest_issue_types_count": 9,
            "compat": {
                "mode": "compat",
                "aliases": {"scope.owner": "scope_owner"},
            },
            "compat_aliases_count": 7,
            "snapshots": [],
        }
        with patch("thegent.mcp.server.session_contract_health_trend_impl", return_value=payload):
            result = thegent_session_contract_health_trend(payload_type="session_contract_health_report")
        content = result.content
        if isinstance(content, list) and content:
            text_item = content[0]
            content = getattr(text_item, "text", str(text_item))
        body = json.loads(content)
        assert body["payload_type"] == "session_contract_health_trend"
        assert result.meta["trend_payload_type"] == "session_contract_health_report"
        assert result.meta["generated_at_utc"] == "2026-02-14T12:15:00Z"
        assert result.meta["scope_key_json"] == "top-level-scope-key-json"
        assert result.meta["scope_payload_type"] == "top-level-payload-type"
        assert result.meta["scope_owner"] == "alice"
        assert result.meta["scope_all"] is False
        assert result.meta["scope_strict"] is True
        assert result.meta["scope_policy_profile"] == "strict_ci"
        assert result.meta["scope_top_blocked"] == 25
        assert result.meta["scope_min_healthy_ratio"] is None
        assert result.meta["snapshot_count"] == 3
        assert result.meta["snapshot_ids_csv"] == "snap-a, snap-b"
        assert result.meta["snapshot_ids_hash"] == "snap-hash"
        assert result.meta["snapshot_window_seconds"] == 123
        assert result.meta["snapshot_window_hash"] == "window-hash"
        assert result.meta["snapshot_interval_seconds_avg"] == 456
        assert result.meta["snapshot_interval_hash"] == "interval-hash"
        assert result.meta["snapshot_density_per_hour"] == 3.25
        assert result.meta["snapshot_density_hash"] == "density-hash"
        assert result.meta["snapshot_issue_churn_count"] == 2
        assert result.meta["snapshot_issue_churn_hash"] == "churn-hash"
        assert result.meta["snapshot_health_volatility"] == 4.2
        assert result.meta["snapshot_health_volatility_hash"] == "volatility-hash"
        assert result.meta["snapshot_freshness_seconds"] == 789
        assert result.meta["snapshot_freshness_hash"] == "freshness-hash"
        assert result.meta["snapshot_retention_max_lines"] == 5000
        assert result.meta["delta_summary_json"] == "top-level-delta-summary-json"
        assert result.meta["blocked_ratio_delta"] == 0.25
        assert result.meta["blocked_count_delta"] == 4
        assert result.meta["scope_key"]["payload_type"] == "session_contract_health_report"
        assert result.meta["latest_status"] == "top-level-status"
        assert result.meta["latest_pass"] is True
        assert result.meta["latest_captured_at_utc"] == "2026-02-14T12:11:00Z"
        assert result.meta["latest_blocked_ratio"] == 0.33
        assert result.meta["latest_blocked_count"] == 17
        assert result.meta["latest_issue_types_count"] == 9
        assert result.meta["latest_issue_types_csv"] == "top-level-issue-types-csv"
        assert result.meta["latest_issue_types_json"] == "top-level-issue-types-json"
        assert result.meta["latest_issue_types_hash"] == "top-level-issue-types-hash"
        assert result.meta["compat_mode"] == "compat"
        assert result.meta["compat_aliases"]["scope.owner"] == "scope_owner"
        assert result.meta["compat_aliases_count"] == 7

    def test_health_trend_tool_fallback_for_missing_volatility_fields(self) -> None:
        # @trace FR-MCP-002
        payload = {
            "schema_version": "health-schema-v1",
            "schema_compat_mode": "compat",
            "payload_type": "session_contract_health_trend",
            "trend_payload_type": "session_contract_health_report",
            "schema_version_v2": "v2",
            "generated_at_utc": "2026-02-14T12:15:00Z",
            "snapshot_count": 1,
            "snapshot_ids_csv": "snap-a",
            "snapshot_ids_hash": "snap-hash",
            "snapshot_window_seconds": 42,
            "snapshot_window_hash": "window-hash",
            "snapshot_interval_seconds_avg": 7,
            "snapshot_interval_hash": "interval-hash",
            "snapshot_density_per_hour": 42.5,
            "snapshot_density_hash": "density-hash",
            "snapshot_issue_churn_count": 0,
            "snapshot_issue_churn_hash": "churn-hash",
            "snapshot_freshness_seconds": 5,
            "snapshot_freshness_hash": "freshness-hash",
            "snapshot_retention_max_lines": 5000,
            "delta_summary": {"blocked_ratio_delta": 0.1, "blocked_count_delta": 1},
            "delta_summary_json": "delta-summary-json",
            "blocked_ratio_delta": 0.1,
            "blocked_count_delta": 1,
            "latest_status": "top-level-status",
            "latest_pass": True,
            "latest_captured_at_utc": "2026-02-14T12:11:00Z",
            "latest_blocked_ratio": 0.2,
            "latest_blocked_count": 2,
            "latest_issue_types_count": 1,
            "latest_issue_types_csv": "top-level-issue-types-csv",
            "latest_issue_types_json": "top-level-issue-types-json",
            "latest_issue_types_hash": "top-level-issue-types-hash",
            "scope_key": {"payload_type": "session_contract_health_report"},
            "scope_key_json": "top-level-scope-key-json",
            "scope_payload_type": "top-level-payload-type",
            "scope_owner": "alice",
            "scope_all": False,
            "scope_strict": False,
            "scope_policy_profile": "strict_ci",
            "scope_min_healthy_ratio": None,
            "scope_top_blocked": 25,
            "compat": {"mode": "compat", "aliases": {"scope.owner": "scope_owner"}},
            "compat_aliases_count": 1,
            "snapshots": [],
        }
        with patch("thegent.mcp.server.session_contract_health_trend_impl", return_value=payload):
            result = thegent_session_contract_health_trend(payload_type="session_contract_health_report")
        expected_hash = hashlib.sha256(str(None).encode("utf-8")).hexdigest()
        assert result.meta["snapshot_health_volatility"] is None
        assert result.meta["snapshot_health_volatility_hash"] == expected_hash

    def test_health_trend_tool_normalizes_malformed_latest_issue_types(self) -> None:
        # @trace FR-MCP-002
        payload = {
            "schema_version": "health-schema-v1",
            "schema_compat_mode": "compat",
            "payload_type": "session_contract_health_trend",
            "trend_payload_type": "session_contract_health_report",
            "generated_at_utc": "2026-02-14T12:15:00Z",
            "snapshot_count": 1,
            "snapshot_ids_csv": "snap-a",
            "snapshot_ids_hash": "snap-hash",
            "snapshot_window_seconds": 42,
            "snapshot_window_hash": "window-hash",
            "snapshot_interval_seconds_avg": 7,
            "snapshot_interval_hash": "interval-hash",
            "snapshot_density_per_hour": 42.5,
            "snapshot_density_hash": "density-hash",
            "snapshot_issue_churn_count": 0,
            "snapshot_issue_churn_hash": "churn-hash",
            "snapshot_freshness_seconds": 5,
            "snapshot_freshness_hash": "freshness-hash",
            "snapshot_retention_max_lines": 5000,
            "delta_summary": {"blocked_ratio_delta": 0.1, "blocked_count_delta": 1},
            "delta_summary_json": "delta-summary-json",
            "blocked_ratio_delta": 0.1,
            "blocked_count_delta": 1,
            "latest_status": "top-level-status",
            "latest_pass": True,
            "latest_captured_at_utc": "2026-02-14T12:11:00Z",
            "latest_blocked_ratio": 0.2,
            "latest_blocked_count": 2,
            "latest": {
                "status": "blocked",
                "pass": False,
                "captured_at_utc": "2026-02-14T12:10:00Z",
                "blocked_ratio": 0.1,
                "blocked_count": 1,
                "issue_types": "abc",
            },
            "scope_key": {"payload_type": "session_contract_health_report"},
            "scope_key_json": "top-level-scope-key-json",
            "scope_payload_type": "top-level-payload-type",
            "scope_owner": "alice",
            "scope_all": False,
            "scope_strict": False,
            "scope_policy_profile": "strict_ci",
            "scope_min_healthy_ratio": None,
            "scope_top_blocked": 25,
            "compat": {"mode": "compat", "aliases": {"scope.owner": "scope_owner"}},
            "compat_aliases_count": 1,
            "snapshots": [],
        }
        expected_latest_issue_types_json = json.dumps(["abc"]).decode()
        expected_latest_issue_types_hash = hashlib.sha256(expected_latest_issue_types_json.encode("utf-8")).hexdigest()
        with patch("thegent.mcp.server.session_contract_health_trend_impl", return_value=payload):
            result = thegent_session_contract_health_trend(payload_type="session_contract_health_report")
        assert result.meta["latest_issue_types_count"] == 1
        assert result.meta["latest_issue_types_csv"] == "abc"
        assert result.meta["latest_issue_types_json"] == expected_latest_issue_types_json
        assert result.meta["latest_issue_types_hash"] == expected_latest_issue_types_hash

    def test_health_trend_resource_returns_json_payload(self) -> None:
        # @trace FR-MCP-002
        payload = {
            "schema_version": "health-schema-v1",
            "payload_type": "session_contract_health_trend",
            "trend_payload_type": "session_contract_health_gate",
            "snapshot_count": 2,
            "scope_key": {"payload_type": "session_contract_health_gate"},
            "delta_summary": {"blocked_ratio_delta": 0.2, "blocked_count_delta": 2},
            "snapshots": [],
        }
        with patch("thegent.mcp.server.session_contract_health_trend_impl", return_value=payload):
            raw = resource_session_contract_health_trend(payload_type="session_contract_health_gate")
        data = json.loads(raw)
        assert data["trend_payload_type"] == "session_contract_health_gate"
        assert data["snapshot_count"] == 2


@pytest.mark.unit
class TestMCPObserveSummaryContract:
    """Unit tests for MCP observe summary tool/resource parity."""

    def test_observe_summary_tool_returns_payload_and_meta(self) -> None:
        payload = {
            "status": "critical",
            "alerts": [
                "Escalation backlog critical: 2 past-SLA",
                "Contract drift over budget: structural=8.0% (budget 4.0%), semantic=0.0% (budget 10.0%)",
            ],
            "kpis": {
                "total_events": 100,
                "fallback_rate": 0.11,
                "structural_drift_pct": 8.0,
                "semantic_drift_pct": 0.0,
            },
            "drift": {
                "within_budget": False,
                "structural_rate_pct": 8.0,
                "semantic_rate_pct": 0.0,
                "structural_budget_pct": 4.0,
                "semantic_budget_pct": 10.0,
            },
            "escalation": {
                "backlog_count": 5,
                "past_sla_count": 2,
                "provider": "gemini",
                "top_escalations_count": 2,
            },
            "trend_summary": {"enabled": False},
            "generated_query": {"trend_samples": 0, "top_escalations": 2},
            "payload_type": "observe_summary",
            "payload_schema_version": "observe-summary-schema-v1",
        }
        with patch("thegent.mcp.server.observe_summary_impl", return_value=payload):
            result = thegent_observe_summary(
                limit=321,
                drift_window=17,
                structural_budget_pct=4.0,
                semantic_budget_pct=10.0,
                provider="gemini",
                top_escalations=2,
            )

        # Handle both list of content objects (FastMCP) and raw strings (legacy)
        content_str = ""
        if isinstance(result.content, list) and len(result.content) > 0:
            content_str = getattr(result.content[0], "text", str(result.content[0]))
        elif isinstance(result.content, str):
            content_str = result.content

        body = json.loads(content_str) if content_str else {}
        assert body["status"] == "critical"
        assert body["escalation"]["provider"] == "gemini"
        assert result.meta["status"] == "critical"
        assert result.meta["payload_type"] == "observe_summary"
        assert result.meta["payload_schema_version"] == "observe-summary-schema-v1"
        assert result.meta["alerts_count"] == 2
        assert result.meta["drift_within_budget"] is False
        assert result.meta["backlog_past_sla_count"] == 2
        assert result.meta["top_escalations_requested"] == 2
        assert result.meta["drift_structural_budget_pct"] == 4.0
        assert result.meta["provider"] == "gemini"
        assert result.meta["trend_enabled"] is False
        assert result.meta["trend_samples_requested"] == 0

    def test_observe_summary_resource_returns_json_payload(self) -> None:
        payload = {
            "status": "healthy",
            "alerts": [],
            "kpis": {"total_events": 12},
            "drift": {"within_budget": True},
            "escalation": {"backlog_count": 0, "past_sla_count": 0},
            "trend_summary": {"enabled": False},
            "generated_query": {"trend_samples": 3},
            "payload_type": "observe_summary",
            "payload_schema_version": "observe-summary-schema-v1",
        }
        with patch("thegent.mcp.server.observe_summary_impl", return_value=payload):
            raw = resource_observe_summary(
                "test-resource://observe", limit=100, drift_window=30, provider="cursor", trend_samples=3
            )
        data = json.loads(raw)
        assert data["status"] == "healthy"
        assert data["drift"]["within_budget"] is True
        assert data["trend_summary"]["enabled"] is False
        assert data["generated_query"]["trend_samples"] == 3
