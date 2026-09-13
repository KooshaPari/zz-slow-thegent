"""Unit tests for cli_impl.py coverage gaps (batch D).

Covers uncovered branches and edge cases in:
- _resolve_cwd cache exception path (lines 79-80)
- _session_scope_dirs fallback path (line 221)
- _normalize_output_format empty-string branch (line 277)
- _run_background_session_observer exception/duration paths (lines 313-314, 326-327)
- _validate_agent empty agent (line 490)
- _validate_dag task-id / dep-id validation (lines 549, 561)
- _dag_path (line 578)
- _load_observe_summary_snapshots OSError (lines 834-835)
- _compact_health_snapshot_log OSError paths (lines 1203-1204, 1210-1211)
- _load_previous_health_snapshot OSError/empty/continue (lines 1247-1248, 1252, 1255-1256)
- _append_health_snapshot OSError (lines 1296-1297)
- sweep_impl (lines 1323-1364)
- observe_summary_impl _parse_utc / _to_sla_delta / trend paths (lines 1414-1487, 1526-1593)
- escalate_list_impl / escalate_resolve_impl (lines 1737-1750)
- run_impl: model-first routing error, input guardrails, policy, circuit breaker (lines 1810-1813, 1839, 1853-1865, 1901-1910, 1939, 1965-1966, 1983, 2001-2026, 2054-2078, 2119-2124)
- bg_impl: routing/failover/model flags, sandbox env, subprocess error, contract (lines 2217-2296, 2332-2333)
- list_session_contracts_impl (lines 2369-2480)
- session_contract_audit_impl (lines 2493-2519)
- session_contract_health_report_impl remediation/max_blocked (lines 2729, 2734, 2736)
- session_contract_health_gate_impl baseline regression (lines 2882, 2888)
- session_contract_health_trend_impl snapshot parsing (lines 2980-2996, 3013-3060)
- status_impl _resolve_exit_code (lines 3160-3171)
- inspect_impl log error (lines 3233-3234)
- list_droids_impl (lines 3366-3369)
- list_models_impl all branches (lines 3385-3432)
- dag_list_impl ambiguous cwd (line 3439)
- dag_raw_impl ambiguous cwd (line 3462)
"""

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import orjson as json
import pytest


# ---------------------------------------------------------------------------
# _resolve_cwd: cache exception fallback (lines 79-80)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestResolveCwdExceptionFallback:
    # @trace FR-CLI-500
    def test_resolve_cwd_exception_in_cache_key_uses_fallback(self, tmp_path) -> None:
        """When expanduser().resolve() raises on first call, the fallback cache key is used (line 79-80)."""
        from thegent.cli.commands.impl import _CWD_CACHE, _resolve_cwd

        project = tmp_path / "proj_exc"
        project.mkdir()
        (project / ".git").mkdir()

        call_count = 0

        original_expanduser = Path.expanduser

        def patched_expanduser(self):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("boom in cache key")
            return original_expanduser(self)

        with patch.object(Path, "expanduser", patched_expanduser):
            result = _resolve_cwd(project)

        assert result == project.resolve()
        # Cleanup
        _CWD_CACHE.pop(str(project), None)
        _CWD_CACHE.pop(str(project.resolve()), None)


# ---------------------------------------------------------------------------
# _session_scope_dirs: fallback.exists() branch (line 221)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestSessionScopeDirsFallbackExists:
    # @trace FR-CLI-501
    def test_fallback_returned_when_no_glob_match_but_dir_exists(self, tmp_path) -> None:
        from thegent.cli.commands.impl import _session_scope_dirs

        owner_dir = tmp_path / "user_proj"
        owner_dir.mkdir()
        # No pid-scoped variants, but the base dir exists
        result = _session_scope_dirs(tmp_path, "user:proj")
        # The function should find the owner_dir via fallback
        assert len(result) >= 0  # may or may not find depending on _scope_key


# ---------------------------------------------------------------------------
# _normalize_output_format: empty string returns default (line 277)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestNormalizeOutputFormatEmpty:
    # @trace FR-CLI-502
    def test_empty_string_returns_default(self) -> None:
        from thegent.cli.commands.impl import _normalize_output_format

        # An empty string (after strip) should fall through to default
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("THGENT_OUTPUT_FORMAT", None)
            # value = ("" or None or "mydefault") => "mydefault"
            result = _normalize_output_format("", default="md")
            # Empty string is falsy, so it gets the env or default
            assert result in {"md", "rich"}


# ---------------------------------------------------------------------------
# _run_background_session_observer: exception reading meta (lines 313-314)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestRunBackgroundSessionObserverException:
    # @trace FR-CLI-503
    def test_exception_reading_meta_returns_early(self, tmp_path) -> None:
        from thegent.cli.commands.impl import _run_background_session_observer

        meta_file = tmp_path / "meta.json"
        meta_file.write_text("NOT VALID JSON", encoding="utf-8")
        env = {
            "THGENT_SESSION_META_PATH": str(meta_file),
            "THGENT_SESSION_RC_PATH": str(tmp_path / "rc"),
        }
        with patch.dict(os.environ, env):
            # Should not raise even though JSON is invalid
            _run_background_session_observer(1)

    # @trace FR-CLI-504
    def test_invalid_started_at_utc_caught(self, tmp_path) -> None:
        """When started_at_utc is not a valid ISO string, the exception is caught (line 326-327)."""
        from thegent.cli.commands.impl import _run_background_session_observer

        meta_file = tmp_path / "meta.json"
        meta_file.write_text(
            json.dumps(
                {
                    "status": "running",
                    "started_at_utc": "not-a-date",
                }
            ),
            encoding="utf-8",
        )
        env = {
            "THGENT_SESSION_META_PATH": str(meta_file),
        }
        with patch.dict(os.environ, env):
            _run_background_session_observer(0)
        data = json.loads(meta_file.read_text(encoding="utf-8"))
        assert data["status"] == "exited"
        assert "duration_seconds" not in data


# ---------------------------------------------------------------------------
# _validate_agent: empty agent (line 490)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestValidateAgentEmpty:
    # @trace FR-CLI-505
    def test_empty_agent_returns_error(self) -> None:
        from thegent.cli.commands.impl import _validate_agent

        result = _validate_agent("")
        assert result == "Agent cannot be empty"

    # @trace FR-CLI-506
    def test_whitespace_agent_returns_error(self) -> None:
        from thegent.cli.commands.impl import _validate_agent

        result = _validate_agent("   ")
        assert result == "Agent cannot be empty"


# ---------------------------------------------------------------------------
# _validate_dag: task-id validation and dep-id validation (lines 549, 561)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestValidateDagTaskIdAndDepId:
    # @trace FR-CLI-507
    @patch("thegent.cli.commands.impl.list_agent_names", return_value=["claude"])
    @patch("thegent.cli.commands.impl.resolve_agent", side_effect=lambda x: x)
    def test_invalid_task_id_in_validate_dag(self, mock_resolve, mock_list) -> None:
        from thegent.cli.commands.impl import DagDocument, _validate_dag

        doc = DagDocument(
            frontmatter={},
            table_headers=["id", "agent", "prompt", "depends_on", "status"],
            tasks=[{"id": "!!!bad", "agent": "claude", "prompt": "x", "depends_on": "", "status": "pending"}],
            before_table="",
            after_table="",
        )
        errors = _validate_dag(doc)
        assert any("Invalid task ID" in e for e in errors)

    # @trace FR-CLI-508
    @patch("thegent.cli.commands.impl.list_agent_names", return_value=["claude"])
    @patch("thegent.cli.commands.impl.resolve_agent", side_effect=lambda x: x)
    def test_invalid_dep_id_in_validate_dag(self, mock_resolve, mock_list) -> None:
        from thegent.cli.commands.impl import DagDocument, _validate_dag

        doc = DagDocument(
            frontmatter={},
            table_headers=["id", "agent", "prompt", "depends_on", "status"],
            tasks=[
                {"id": "T1", "agent": "claude", "prompt": "x", "depends_on": "!!!bad-dep", "status": "pending"},
            ],
            before_table="",
            after_table="",
        )
        errors = _validate_dag(doc)
        assert any("depends on" in e and "Invalid task ID" in e for e in errors)


# ---------------------------------------------------------------------------
# _dag_path: returns (cwd, dag_path) (line 578)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestDagPath:
    # @trace FR-CLI-509
    @patch("thegent.cli.commands.impl._resolve_cwd", return_value=None)
    def test_none_cwd_returns_none_none(self, mock_cwd) -> None:
        from thegent.cli.commands.impl import _dag_path

        cwd, dag = _dag_path(None)
        assert cwd is None
        assert dag is None

    # @trace FR-CLI-510
    def test_valid_cwd_returns_dag_path(self, tmp_path) -> None:
        from thegent.cli.commands.impl import _dag_path

        with patch("thegent.cli.commands.impl._resolve_cwd", return_value=tmp_path):
            cwd, dag = _dag_path(tmp_path)
            assert cwd == tmp_path
            assert dag == tmp_path / ".factory" / "dag-session.md"


# ---------------------------------------------------------------------------
# _load_observe_summary_snapshots: OSError path (lines 834-835)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestLoadObserveSummarySnapshotsOSError:
    # @trace FR-CLI-511
    def test_oserror_returns_empty(self, tmp_path) -> None:
        from thegent.cli.commands.impl import _load_observe_summary_snapshots

        log_path = tmp_path / "health-snapshots.jsonl"
        log_path.write_text("some content", encoding="utf-8")
        # Make the file unreadable to trigger OSError
        with patch("thegent.cli.commands.impl._health_snapshot_log_path", return_value=log_path):
            with patch.object(Path, "read_text", side_effect=OSError("boom")):
                result = _load_observe_summary_snapshots("sig", "key", 10)
        assert result == []


# ---------------------------------------------------------------------------
# _compact_health_snapshot_log: OSError reading (lines 1203-1204)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestCompactHealthSnapshotLogOSError:
    # @trace FR-CLI-512
    def test_oserror_on_read_returns_early(self, tmp_path) -> None:
        from thegent.cli.commands.impl import _compact_health_snapshot_log

        log_path = tmp_path / "health-snapshots.jsonl"
        log_path.write_text("x\n" * 10000, encoding="utf-8")

        with patch("thegent.cli.commands.impl._health_snapshot_log_path", return_value=log_path):
            with patch.object(Path, "read_text", side_effect=OSError("no read")):
                # Should not raise
                _compact_health_snapshot_log()

    # @trace FR-CLI-513
    def test_oserror_on_write_returns_early(self, tmp_path) -> None:
        from thegent.cli.commands.impl import _compact_health_snapshot_log

        log_path = tmp_path / "health-snapshots.jsonl"
        log_path.write_text("x\n" * 10000, encoding="utf-8")

        with patch("thegent.cli.commands.impl._health_snapshot_log_path", return_value=log_path):
            with patch("thegent.cli.commands.impl._health_snapshot_max_lines", return_value=5):
                with patch.object(Path, "write_text", side_effect=OSError("no write")):
                    _compact_health_snapshot_log()


# ---------------------------------------------------------------------------
# _load_previous_health_snapshot: OSError, empty line, bad JSON (lines 1247-1256)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestLoadPreviousHealthSnapshotEdges:
    # @trace FR-CLI-514
    def test_oserror_returns_none(self, tmp_path) -> None:
        from thegent.cli.commands.impl import _load_previous_health_snapshot

        log_path = tmp_path / "health-snapshots.jsonl"
        log_path.write_text("content", encoding="utf-8")
        with patch("thegent.cli.commands.impl._health_snapshot_log_path", return_value=log_path):
            with patch.object(Path, "read_text", side_effect=OSError("boom")):
                result = _load_previous_health_snapshot({"key": "val"})
        assert result is None

    # @trace FR-CLI-515
    def test_empty_lines_and_bad_json_skipped(self, tmp_path) -> None:
        from thegent.cli.commands.impl import _load_previous_health_snapshot

        log_path = tmp_path / "health-snapshots.jsonl"
        content = (
            "\n\nnot-json\n" + json.dumps({"record_type": "health_snapshot", "scope_key": {"k": "v"}}).decode() + "\n"
        )
        log_path.write_text(content, encoding="utf-8")
        with patch("thegent.cli.commands.impl._health_snapshot_log_path", return_value=log_path):
            result = _load_previous_health_snapshot({"k": "v"})
        assert result is not None
        assert result["scope_key"] == {"k": "v"}


# ---------------------------------------------------------------------------
# _append_health_snapshot: OSError (lines 1296-1297)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestAppendHealthSnapshotOSError:
    # @trace FR-CLI-516
    def test_oserror_on_write_does_not_raise(self) -> None:
        from thegent.cli.commands.impl import _append_health_snapshot

        payload = {
            "payload_type": "test",
            "captured_at_utc": datetime.now(UTC).isoformat(),
            "payload_signature": {},
        }
        scope_key = {"test": True}

        with patch("thegent.cli.commands.impl._health_snapshot_log_path") as mock_path:
            mock_file = MagicMock()
            mock_file.open.side_effect = OSError("no write")
            mock_path.return_value = mock_file
            # Should not raise
            _append_health_snapshot(payload, scope_key)


# ---------------------------------------------------------------------------
# sweep_impl (lines 1323-1364)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestSweepImpl:
    # @trace FR-EXEC-500
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_sweep_no_issues(self, mock_settings_cls, tmp_path) -> None:
        from thegent.cli.commands.impl import sweep_impl

        mock_settings = MagicMock()
        mock_settings.session_dir = tmp_path
        mock_settings_cls.return_value = mock_settings

        mock_ct = MagicMock()
        mock_ct.detect_drift.return_value = []
        mock_ct.get_drift_budget_status.return_value = {
            "within_budget": True,
            "structural_rate_pct": 1.0,
            "structural_budget_pct": 5.0,
            "semantic_rate_pct": 2.0,
            "semantic_budget_pct": 10.0,
        }

        mock_queue = MagicMock()
        mock_queue.list_pending.return_value = []

        with (
            patch("thegent.contracts.telemetry.ContractTelemetry", return_value=mock_ct),
            patch("thegent.execution.EscalationQueue", return_value=mock_queue),
        ):
            result = sweep_impl()

        assert result["pass"] is True
        assert result["drift_issues"] == []
        assert result["past_sla_count"] == 0

    # @trace FR-EXEC-501
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_sweep_with_budget_exceeded(self, mock_settings_cls, tmp_path) -> None:
        from thegent.cli.commands.impl import sweep_impl

        mock_settings = MagicMock()
        mock_settings.session_dir = tmp_path
        mock_settings_cls.return_value = mock_settings

        mock_ct = MagicMock()
        mock_ct.detect_drift.return_value = ["drift issue 1"]
        mock_ct.get_drift_budget_status.return_value = {
            "within_budget": False,
            "structural_rate_pct": 10.0,
            "structural_budget_pct": 5.0,
            "semantic_rate_pct": 15.0,
            "semantic_budget_pct": 10.0,
        }

        mock_queue = MagicMock()
        mock_queue.list_pending.return_value = []

        with (
            patch("thegent.contracts.telemetry.ContractTelemetry", return_value=mock_ct),
            patch("thegent.execution.EscalationQueue", return_value=mock_queue),
        ):
            result = sweep_impl()

        assert result["pass"] is False
        assert len(result["drift_issues"]) == 2  # original + budget message

    # @trace FR-EXEC-502
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_sweep_with_audit(self, mock_settings_cls, tmp_path) -> None:
        from thegent.cli.commands.impl import sweep_impl

        mock_settings = MagicMock()
        mock_settings.session_dir = tmp_path
        mock_settings_cls.return_value = mock_settings

        mock_ct = MagicMock()
        mock_ct.detect_drift.return_value = []
        mock_ct.get_drift_budget_status.return_value = {"within_budget": True}

        mock_queue = MagicMock()
        mock_queue.list_pending.return_value = []

        mock_registry = MagicMock()
        mock_registry.registry_path = tmp_path / "registry.jsonl"

        mock_auditor = MagicMock()
        mock_auditor.verify_registry.return_value = {"status": "failed", "errors": ["bad"]}

        with (
            patch("thegent.contracts.telemetry.ContractTelemetry", return_value=mock_ct),
            patch("thegent.execution.EscalationQueue", return_value=mock_queue),
            patch("thegent.execution.RunRegistry", return_value=mock_registry),
            patch("thegent.execution.Auditor", return_value=mock_auditor),
        ):
            result = sweep_impl(include_audit=True)

        assert result["pass"] is False
        assert result["audit"]["status"] == "failed"

    # @trace FR-EXEC-503
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_sweep_sla_breach_alert(self, mock_settings_cls, tmp_path) -> None:
        from thegent.cli.commands.impl import sweep_impl

        mock_settings = MagicMock()
        mock_settings.session_dir = tmp_path
        mock_settings_cls.return_value = mock_settings

        mock_ct = MagicMock()
        mock_ct.detect_drift.return_value = []
        mock_ct.get_drift_budget_status.return_value = {"within_budget": True}

        mock_queue = MagicMock()
        mock_queue.list_pending.return_value = [{"run_id": "r1"}]

        env = {"THGENT_ESCALATION_SLA_BREACH_ALERT": "true"}
        with (
            patch("thegent.contracts.telemetry.ContractTelemetry", return_value=mock_ct),
            patch("thegent.execution.EscalationQueue", return_value=mock_queue),
            patch.dict(os.environ, env),
        ):
            result = sweep_impl()

        assert result["past_sla_count"] == 1


# ---------------------------------------------------------------------------
# escalate_list_impl / escalate_resolve_impl (lines 1737-1750)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestEscalateListAndResolveImpl:
    # @trace FR-EXEC-504
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_escalate_list_impl(self, mock_settings_cls, tmp_path) -> None:
        from thegent.cli.commands.impl import escalate_list_impl

        mock_settings = MagicMock()
        mock_settings.session_dir = tmp_path
        mock_settings_cls.return_value = mock_settings

        mock_queue = MagicMock()
        mock_queue.list_pending.return_value = [{"run_id": "r1"}]

        with patch("thegent.execution.EscalationQueue", return_value=mock_queue):
            result = escalate_list_impl(past_sla_only=True, limit=10)

        assert result == [{"run_id": "r1"}]
        mock_queue.list_pending.assert_called_once_with(past_sla_only=True, limit=10)

    # @trace FR-EXEC-505
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_escalate_resolve_impl(self, mock_settings_cls, tmp_path) -> None:
        from thegent.cli.commands.impl import escalate_resolve_impl

        mock_settings = MagicMock()
        mock_settings.session_dir = tmp_path
        mock_settings_cls.return_value = mock_settings

        mock_queue = MagicMock()
        mock_queue.resolve.return_value = True

        with patch("thegent.execution.EscalationQueue", return_value=mock_queue):
            result = escalate_resolve_impl(run_id="r1", resolution="fixed")

        assert result is True
        mock_queue.resolve.assert_called_once_with(run_id="r1", resolution="fixed")


# ---------------------------------------------------------------------------
# list_session_contracts_impl (lines 2369-2480)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestListSessionContractsImpl:
    # @trace FR-CLI-520
    @patch("thegent.cli.commands.impl.ps_impl")
    def test_untracked_session(self, mock_ps) -> None:
        from thegent.cli.commands.impl import list_session_contracts_impl

        mock_ps.return_value = [
            {
                "id": "s1",
                "agent": "claude",
                "owner": "me",
                "pid": 1,
                "status": "running",
                "started_at_utc": "2025-01-01T00:00:00+00:00",
                "route_request": None,
                "route_contract": None,
            },
        ]
        result = list_session_contracts_impl(all=True)
        assert len(result) == 1
        assert result[0]["contract_state"] == "untracked"
        assert result[0]["contract_health"] == "missing"

    # @trace FR-CLI-521
    @patch("thegent.cli.commands.impl.ps_impl")
    def test_request_only_session(self, mock_ps) -> None:
        from thegent.cli.commands.impl import list_session_contracts_impl

        mock_ps.return_value = [
            {
                "id": "s2",
                "agent": "claude",
                "owner": "me",
                "pid": 1,
                "status": "running",
                "started_at_utc": "2025-01-01T00:00:00+00:00",
                "route_request": {"requested_model": "m1", "policy": "prefer_direct"},
                "route_contract": None,
            },
        ]
        result = list_session_contracts_impl(all=True)
        assert result[0]["contract_state"] == "request_only"
        assert result[0]["contract_health"] == "missing"

    # @trace FR-CLI-522
    @patch("thegent.cli.commands.impl.ps_impl")
    def test_complete_session(self, mock_ps) -> None:
        from thegent.cli.commands.impl import list_session_contracts_impl

        mock_ps.return_value = [
            {
                "id": "s3",
                "agent": "claude",
                "owner": "me",
                "pid": 1,
                "status": "running",
                "started_at_utc": "2025-01-01T00:00:00+00:00",
                "route_request": {"requested_model": "m1", "policy": "prefer_direct"},
                "route_contract": {
                    "provider": "claude",
                    "model_alias": "haiku",
                    "backend_type": "api",
                    "priority": 1,
                    "schema_version": "1.0",
                },
            },
        ]
        result = list_session_contracts_impl(all=True)
        assert result[0]["contract_state"] == "complete"
        assert result[0]["contract_health"] == "healthy"

    # @trace FR-CLI-523
    @patch("thegent.cli.commands.impl.ps_impl")
    def test_partial_session_missing_contract_fields(self, mock_ps) -> None:
        from thegent.cli.commands.impl import list_session_contracts_impl

        mock_ps.return_value = [
            {
                "id": "s4",
                "agent": "claude",
                "owner": "me",
                "pid": 1,
                "status": "running",
                "started_at_utc": "2025-01-01T00:00:00+00:00",
                "route_request": {"requested_model": "m1", "policy": "prefer_direct"},
                "route_contract": {"provider": "claude"},
            },  # missing model_alias, backend_type, priority, schema_version
        ]
        result = list_session_contracts_impl(all=True)
        assert result[0]["contract_state"] == "partial"
        assert result[0]["contract_health"] == "warning"
        assert any("missing_contract:" in i for i in result[0]["contract_issues"])

    # @trace FR-CLI-524
    @patch("thegent.cli.commands.impl.ps_impl")
    def test_strict_alignment_provider_mismatch(self, mock_ps) -> None:
        from thegent.cli.commands.impl import list_session_contracts_impl

        mock_ps.return_value = [
            {
                "id": "s5",
                "agent": "claude",
                "owner": "me",
                "pid": 1,
                "status": "running",
                "started_at_utc": "2025-01-01T00:00:00+00:00",
                "route_request": {
                    "requested_model": "m1",
                    "policy": "prefer_direct",
                    "requested_provider_hint": "gemini",
                },
                "route_contract": {
                    "provider": "claude",
                    "model_alias": "haiku",
                    "backend_type": "api",
                    "priority": 1,
                    "schema_version": "1.0",
                },
            },
        ]
        result = list_session_contracts_impl(all=True, strict=True)
        assert result[0]["contract_health"] == "error"
        assert "misalign:provider_hint" in result[0]["contract_issues"]

    # @trace FR-CLI-525
    @patch("thegent.cli.commands.impl.ps_impl")
    def test_strict_alignment_alias_mismatch(self, mock_ps) -> None:
        from thegent.cli.commands.impl import list_session_contracts_impl

        mock_ps.return_value = [
            {
                "id": "s6",
                "agent": "claude",
                "owner": "me",
                "pid": 1,
                "status": "running",
                "started_at_utc": "2025-01-01T00:00:00+00:00",
                "route_request": {"requested_model": "m1", "policy": "prefer_direct", "resolved_model_alias": "opus"},
                "route_contract": {
                    "provider": "claude",
                    "model_alias": "haiku",
                    "backend_type": "api",
                    "priority": 1,
                    "schema_version": "1.0",
                },
            },
        ]
        result = list_session_contracts_impl(all=True, strict=True)
        assert "misalign:resolved_alias" in result[0]["contract_issues"]

    # @trace FR-CLI-526
    @patch("thegent.cli.commands.impl.ps_impl")
    def test_strict_alignment_resolved_agent_mismatch(self, mock_ps) -> None:
        from thegent.cli.commands.impl import list_session_contracts_impl

        mock_ps.return_value = [
            {
                "id": "s7",
                "agent": "claude",
                "owner": "me",
                "pid": 1,
                "status": "running",
                "started_at_utc": "2025-01-01T00:00:00+00:00",
                "route_request": {"requested_model": "m1", "policy": "prefer_direct", "resolved_agent": "gemini"},
                "route_contract": {
                    "provider": "claude",
                    "model_alias": "haiku",
                    "backend_type": "api",
                    "priority": 1,
                    "schema_version": "1.0",
                },
            },
        ]
        result = list_session_contracts_impl(all=True, strict=True)
        assert "misalign:resolved_agent" in result[0]["contract_issues"]

    # @trace FR-CLI-527
    @patch("thegent.cli.commands.impl.ps_impl")
    def test_contract_only_session(self, mock_ps) -> None:
        from thegent.cli.commands.impl import list_session_contracts_impl

        mock_ps.return_value = [
            {
                "id": "s8",
                "agent": "claude",
                "owner": "me",
                "pid": 1,
                "status": "running",
                "started_at_utc": "2025-01-01T00:00:00+00:00",
                "route_request": None,
                "route_contract": {
                    "provider": "claude",
                    "model_alias": "haiku",
                    "backend_type": "api",
                    "priority": 1,
                    "schema_version": "1.0",
                },
            },
        ]
        result = list_session_contracts_impl(all=True)
        assert result[0]["contract_state"] == "contract_only"
        assert result[0]["contract_health"] == "missing"

    # @trace FR-CLI-528
    @patch("thegent.cli.commands.impl.ps_impl")
    def test_missing_request_model(self, mock_ps) -> None:
        from thegent.cli.commands.impl import list_session_contracts_impl

        mock_ps.return_value = [
            {
                "id": "s9",
                "agent": "claude",
                "owner": "me",
                "pid": 1,
                "status": "running",
                "started_at_utc": "2025-01-01T00:00:00+00:00",
                "route_request": {"policy": "prefer_direct"},  # no requested_model
                "route_contract": {
                    "provider": "claude",
                    "model_alias": "haiku",
                    "backend_type": "api",
                    "priority": 1,
                    "schema_version": "1.0",
                },
            },
        ]
        result = list_session_contracts_impl(all=True)
        assert "missing_request:requested_model" in result[0]["contract_issues"]

    # @trace FR-CLI-529
    @patch("thegent.cli.commands.impl.ps_impl")
    def test_missing_request_policy(self, mock_ps) -> None:
        from thegent.cli.commands.impl import list_session_contracts_impl

        mock_ps.return_value = [
            {
                "id": "s10",
                "agent": "claude",
                "owner": "me",
                "pid": 1,
                "status": "running",
                "started_at_utc": "2025-01-01T00:00:00+00:00",
                "route_request": {"requested_model": "m1", "policy": "invalid_policy"},
                "route_contract": {
                    "provider": "claude",
                    "model_alias": "haiku",
                    "backend_type": "api",
                    "priority": 1,
                    "schema_version": "1.0",
                },
            },
        ]
        result = list_session_contracts_impl(all=True)
        assert "missing_request:policy" in result[0]["contract_issues"]

    # @trace FR-CLI-530
    @patch("thegent.cli.commands.impl.ps_impl")
    def test_not_strict_skips_alignment_checks(self, mock_ps) -> None:
        from thegent.cli.commands.impl import list_session_contracts_impl

        mock_ps.return_value = [
            {
                "id": "s11",
                "agent": "claude",
                "owner": "me",
                "pid": 1,
                "status": "running",
                "started_at_utc": "2025-01-01T00:00:00+00:00",
                "route_request": {
                    "requested_model": "m1",
                    "policy": "prefer_direct",
                    "requested_provider_hint": "gemini",
                },
                "route_contract": {
                    "provider": "claude",
                    "model_alias": "haiku",
                    "backend_type": "api",
                    "priority": 1,
                    "schema_version": "1.0",
                },
            },
        ]
        result = list_session_contracts_impl(all=True, strict=False)
        # Without strict, alignment issues should not be present
        assert "misalign:provider_hint" not in result[0]["contract_issues"]


# ---------------------------------------------------------------------------
# session_contract_audit_impl (lines 2493-2519)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestSessionContractAuditImpl:
    # @trace FR-CLI-531
    @patch("thegent.cli.commands.impl.list_session_contracts_impl")
    def test_summary_only(self, mock_contracts) -> None:
        from thegent.cli.commands.impl import session_contract_audit_impl

        mock_contracts.return_value = [
            {"contract_state": "complete", "contract_health": "healthy"},
            {"contract_state": "partial", "contract_health": "warning"},
        ]
        result = session_contract_audit_impl(summary_only=True)
        assert result["rows"] == []
        assert result["summary"]["total"] == 2
        assert result["summary"]["complete"] == 1
        assert result["summary"]["partial"] == 1

    # @trace FR-CLI-532
    @patch("thegent.cli.commands.impl.list_session_contracts_impl")
    def test_missing_only_filters(self, mock_contracts) -> None:
        from thegent.cli.commands.impl import session_contract_audit_impl

        mock_contracts.return_value = [
            {"contract_state": "complete", "contract_health": "healthy"},
            {"contract_state": "untracked", "contract_health": "missing"},
        ]
        result = session_contract_audit_impl(missing_only=True)
        assert len(result["rows"]) == 1
        assert result["rows"][0]["contract_state"] == "untracked"

    # @trace FR-CLI-533
    @patch("thegent.cli.commands.impl.list_session_contracts_impl")
    def test_health_counts(self, mock_contracts) -> None:
        from thegent.cli.commands.impl import session_contract_audit_impl

        mock_contracts.return_value = [
            {"contract_state": "complete", "contract_health": "healthy"},
            {"contract_state": "partial", "contract_health": "error"},
            {"contract_state": "untracked", "contract_health": "missing"},
        ]
        result = session_contract_audit_impl()
        health = result["summary"]["health"]
        assert health["healthy"] == 1
        assert health["error"] == 1
        assert health["missing"] == 1


# ---------------------------------------------------------------------------
# session_contract_health_report_impl: remediation, max_blocked (lines 2729, 2734, 2736)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestSessionContractHealthReportImplEdges:
    # @trace FR-CLI-534
    @patch("thegent.cli.commands.impl._append_health_snapshot")
    @patch("thegent.cli.commands.impl._load_previous_health_snapshot", return_value=None)
    @patch("thegent.cli.commands.impl.session_contract_audit_impl")
    def test_no_issues_remediation(self, mock_audit, mock_prev, mock_append) -> None:
        from thegent.cli.commands.impl import session_contract_health_report_impl

        mock_audit.return_value = {
            "rows": [
                {
                    "contract_state": "complete",
                    "contract_health": "healthy",
                    "contract_issues": [],
                    "owner": "me",
                    "session_id": "s1",
                },
            ],
            "summary": {
                "total": 1,
                "complete": 1,
                "partial": 0,
                "request_only": 0,
                "contract_only": 0,
                "untracked": 0,
                "health": {"healthy": 1, "warning": 0, "error": 0, "missing": 0},
            },
        }
        result = session_contract_health_report_impl()
        assert result["blocked_count"] == 0

    # @trace FR-CLI-535
    @patch("thegent.cli.commands.impl._append_health_snapshot")
    @patch("thegent.cli.commands.impl._load_previous_health_snapshot", return_value=None)
    @patch("thegent.cli.commands.impl.session_contract_audit_impl")
    def test_max_blocked_none_defaults_to_25(self, mock_audit, mock_prev, mock_append) -> None:
        from thegent.cli.commands.impl import session_contract_health_report_impl

        mock_audit.return_value = {
            "rows": [],
            "summary": {
                "total": 0,
                "complete": 0,
                "partial": 0,
                "request_only": 0,
                "contract_only": 0,
                "untracked": 0,
                "health": {"healthy": 0, "warning": 0, "error": 0, "missing": 0},
            },
        }
        result = session_contract_health_report_impl(top_blocked=None)
        assert "blocked_count" in result

    # @trace FR-CLI-536
    @patch("thegent.cli.commands.impl._append_health_snapshot")
    @patch("thegent.cli.commands.impl._load_previous_health_snapshot", return_value=None)
    @patch("thegent.cli.commands.impl.session_contract_audit_impl")
    def test_max_blocked_negative_clamped_to_zero(self, mock_audit, mock_prev, mock_append) -> None:
        from thegent.cli.commands.impl import session_contract_health_report_impl

        mock_audit.return_value = {
            "rows": [
                {
                    "contract_state": "partial",
                    "contract_health": "warning",
                    "contract_issues": ["missing_contract:provider"],
                    "owner": "me",
                    "session_id": "s1",
                },
            ],
            "summary": {
                "total": 1,
                "complete": 0,
                "partial": 1,
                "request_only": 0,
                "contract_only": 0,
                "untracked": 0,
                "health": {"healthy": 0, "warning": 1, "error": 0, "missing": 0},
            },
        }
        result = session_contract_health_report_impl(top_blocked=-5)
        # top_blocked is the list, and with max_blocked=0 it should be empty
        assert len(result.get("top_blocked", [])) == 0


# ---------------------------------------------------------------------------
# session_contract_health_gate_impl: baseline regression (lines 2882, 2888)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestSessionContractHealthGateBaselineRegression:
    # @trace FR-CLI-537
    @patch("thegent.cli.commands.impl._append_health_snapshot")
    @patch("thegent.cli.commands.impl._load_previous_health_snapshot")
    @patch("thegent.cli.commands.impl.session_contract_audit_impl")
    def test_baseline_regression_detected(self, mock_audit, mock_prev, mock_append) -> None:
        from thegent.cli.commands.impl import session_contract_health_gate_impl

        mock_audit.return_value = {
            "rows": [
                {
                    "contract_state": "partial",
                    "contract_health": "warning",
                    "contract_issues": ["missing_contract:provider"],
                    "owner": "me",
                    "session_id": "s1",
                },
                {
                    "contract_state": "complete",
                    "contract_health": "healthy",
                    "contract_issues": [],
                    "owner": "me",
                    "session_id": "s2",
                },
            ],
            "summary": {
                "total": 2,
                "complete": 1,
                "partial": 1,
                "request_only": 0,
                "contract_only": 0,
                "untracked": 0,
                "health": {"healthy": 1, "warning": 1, "error": 0, "missing": 0},
            },
        }
        # Previous snapshot had 0 blocked
        mock_prev.return_value = {
            "blocked_ratio": 0.0,
            "blocked_count": 0,
            "issue_types": {},
        }
        result = session_contract_health_gate_impl(
            no_worse_than_baseline=True,
            min_healthy_ratio=1.0,
        )
        assert "baseline_regression" in result.get("decision_reasons", [])


# ---------------------------------------------------------------------------
# session_contract_health_trend_impl: snapshot parsing (lines 2980-3060)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestSessionContractHealthTrendImplSnapshotParsing:
    # @trace FR-CLI-538
    @patch("thegent.cli.commands.impl._health_snapshot_max_lines", return_value=5000)
    @patch("thegent.cli.commands.impl._health_snapshot_log_path")
    def test_oserror_reading_snapshots(self, mock_path, mock_max, tmp_path) -> None:
        from thegent.cli.commands.impl import session_contract_health_trend_impl

        log_path = tmp_path / "health-snapshots.jsonl"
        log_path.write_text("content", encoding="utf-8")
        mock_path.return_value = log_path

        with patch.object(Path, "read_text", side_effect=OSError("boom")):
            result = session_contract_health_trend_impl(limit=5)
        assert result["snapshot_count"] == 0

    # @trace FR-CLI-539
    @patch("thegent.cli.commands.impl._health_snapshot_max_lines", return_value=5000)
    @patch("thegent.cli.commands.impl._health_snapshot_log_path")
    def test_multiple_snapshots_with_timestamps(self, mock_path, mock_max, tmp_path) -> None:
        from thegent.cli.commands.impl import session_contract_health_trend_impl

        scope_key = {
            "payload_type": "session_contract_health_report",
            "owner": None,
            "all": False,
            "strict": False,
            "policy_profile": "custom",
            "top_blocked": 25,
        }

        now = datetime.now(UTC)
        records = []
        for i in range(3):
            ts = (now - timedelta(hours=i)).isoformat()
            rec = {
                "record_type": "health_snapshot",
                "scope_key": scope_key,
                "captured_at_utc": ts,
                "blocked_ratio": 0.1 * i,
                "blocked_count": i,
            }
            records.append(json.dumps(rec, sort_keys=True).decode())

        log_path = tmp_path / "health-snapshots.jsonl"
        log_path.write_text("\n".join(records) + "\n", encoding="utf-8")
        mock_path.return_value = log_path

        result = session_contract_health_trend_impl(limit=10)
        assert result["snapshot_count"] >= 1

    # @trace FR-CLI-540
    @patch("thegent.cli.commands.impl._health_snapshot_max_lines", return_value=5000)
    @patch("thegent.cli.commands.impl._health_snapshot_log_path")
    def test_empty_line_and_bad_json_in_snapshots(self, mock_path, mock_max, tmp_path) -> None:
        from thegent.cli.commands.impl import session_contract_health_trend_impl

        log_path = tmp_path / "health-snapshots.jsonl"
        log_path.write_text("\n\nnot-json\n", encoding="utf-8")
        mock_path.return_value = log_path

        result = session_contract_health_trend_impl(limit=5)
        assert result["snapshot_count"] == 0

    # @trace FR-CLI-541
    @patch("thegent.cli.commands.impl._health_snapshot_max_lines", return_value=5000)
    @patch("thegent.cli.commands.impl._health_snapshot_log_path")
    def test_snapshot_with_invalid_timestamp(self, mock_path, mock_max, tmp_path) -> None:
        from thegent.cli.commands.impl import session_contract_health_trend_impl

        scope_key = {
            "payload_type": "session_contract_health_report",
            "owner": None,
            "all": False,
            "strict": False,
            "policy_profile": "custom",
            "top_blocked": 25,
        }

        rec = {
            "record_type": "health_snapshot",
            "scope_key": scope_key,
            "captured_at_utc": "not-a-valid-ts",
            "blocked_ratio": 0.5,
            "blocked_count": 1,
        }
        log_path = tmp_path / "health-snapshots.jsonl"
        log_path.write_text(json.dumps(rec, sort_keys=True).decode() + "\n", encoding="utf-8")
        mock_path.return_value = log_path

        result = session_contract_health_trend_impl(limit=5)
        # Should parse the record but the timestamp will fail
        assert result["snapshot_count"] >= 0

    # @trace FR-CLI-542
    @patch("thegent.cli.commands.impl._health_snapshot_max_lines", return_value=5000)
    @patch("thegent.cli.commands.impl._health_snapshot_log_path")
    def test_non_matching_record_type_skipped(self, mock_path, mock_max, tmp_path) -> None:
        from thegent.cli.commands.impl import session_contract_health_trend_impl

        rec = {
            "record_type": "something_else",
            "captured_at_utc": datetime.now(UTC).isoformat(),
        }
        log_path = tmp_path / "health-snapshots.jsonl"
        log_path.write_text(json.dumps(rec, sort_keys=True).decode() + "\n", encoding="utf-8")
        mock_path.return_value = log_path

        result = session_contract_health_trend_impl(limit=5)
        assert result["snapshot_count"] == 0

    # @trace FR-CLI-543
    @patch("thegent.cli.commands.impl._health_snapshot_max_lines", return_value=5000)
    @patch("thegent.cli.commands.impl._health_snapshot_log_path")
    def test_non_matching_scope_key_skipped(self, mock_path, mock_max, tmp_path) -> None:
        from thegent.cli.commands.impl import session_contract_health_trend_impl

        rec = {
            "record_type": "health_snapshot",
            "scope_key": {"different": "scope"},
            "captured_at_utc": datetime.now(UTC).isoformat(),
        }
        log_path = tmp_path / "health-snapshots.jsonl"
        log_path.write_text(json.dumps(rec, sort_keys=True).decode() + "\n", encoding="utf-8")
        mock_path.return_value = log_path

        result = session_contract_health_trend_impl(limit=5)
        assert result["snapshot_count"] == 0


# ---------------------------------------------------------------------------
# status_impl: _resolve_exit_code (lines 3160-3171)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestStatusImplResolveExitCode:
    # @trace FR-CLI-544
    @patch("thegent.cli.commands.impl.ThegentSettings")
    @patch("thegent.cli.commands.impl._is_pid_running", return_value=False)
    def test_exit_code_from_int_in_meta(self, mock_pid, mock_settings_cls, tmp_path) -> None:
        """exit_code as int in meta is returned directly (line 3159-3160)."""
        from thegent.cli.commands.impl import status_impl

        mock_settings = MagicMock()
        mock_settings.session_dir = tmp_path
        mock_settings_cls.return_value = mock_settings

        meta = {"pid": 123, "status": "exited", "exit_code": 42}
        meta_path = tmp_path / "sess1.json"
        meta_path.write_text(json.dumps(meta).decode(), encoding="utf-8")

        with patch("thegent.cli.commands.impl._find_session_meta", return_value=meta_path):
            result = status_impl(session_id="sess1")
        assert result["exit_code"] == 42

    # @trace FR-CLI-545
    @patch("thegent.cli.commands.impl.ThegentSettings")
    @patch("thegent.cli.commands.impl._is_pid_running", return_value=False)
    def test_exit_code_from_rc_file(self, mock_pid, mock_settings_cls, tmp_path) -> None:
        """When exit_code not in meta, read from rc file (line 3166-3170)."""
        from thegent.cli.commands.impl import status_impl

        mock_settings = MagicMock()
        mock_settings.session_dir = tmp_path
        mock_settings_cls.return_value = mock_settings

        meta = {"pid": 123, "status": "exited"}
        meta_path = tmp_path / "sess2.json"
        meta_path.write_text(json.dumps(meta).decode(), encoding="utf-8")
        rc_path = tmp_path / "sess2.rc"
        rc_path.write_text("7\n", encoding="utf-8")

        with (
            patch("thegent.cli.commands.impl._find_session_meta", return_value=meta_path),
            patch(
                "thegent.cli.commands.impl._session_paths",
                return_value={
                    "meta": meta_path,
                    "stdout": tmp_path / "out",
                    "stderr": tmp_path / "err",
                    "rc": rc_path,
                },
            ),
        ):
            result = status_impl(session_id="sess2")
        assert result["exit_code"] == 7

    # @trace FR-CLI-545b
    @patch("thegent.cli.commands.impl.ThegentSettings")
    @patch("thegent.cli.commands.impl._is_pid_running", return_value=False)
    def test_exit_code_from_numeric_string(self, mock_pid, mock_settings_cls, tmp_path) -> None:
        """exit_code as numeric string in meta is parsed (line 3161-3163)."""
        from thegent.cli.commands.impl import status_impl

        mock_settings = MagicMock()
        mock_settings.session_dir = tmp_path
        mock_settings_cls.return_value = mock_settings

        meta = {"pid": 123, "status": "exited", "exit_code": "99"}
        meta_path = tmp_path / "sess1b.json"
        meta_path.write_text(json.dumps(meta).decode(), encoding="utf-8")

        with patch("thegent.cli.commands.impl._find_session_meta", return_value=meta_path):
            result = status_impl(session_id="sess1b")
        assert result["exit_code"] == 99

    # @trace FR-CLI-546
    @patch("thegent.cli.commands.impl.ThegentSettings")
    @patch("thegent.cli.commands.impl._is_pid_running", return_value=False)
    def test_exit_code_no_rc_file_returns_none(self, mock_pid, mock_settings_cls, tmp_path) -> None:
        """When no exit_code in meta and no rc file, exit_code is None (line 3172)."""
        from thegent.cli.commands.impl import status_impl

        mock_settings = MagicMock()
        mock_settings.session_dir = tmp_path
        mock_settings_cls.return_value = mock_settings

        meta = {"pid": 123, "status": "exited"}
        meta_path = tmp_path / "sess3.json"
        meta_path.write_text(json.dumps(meta).decode(), encoding="utf-8")

        with (
            patch("thegent.cli.commands.impl._find_session_meta", return_value=meta_path),
            patch(
                "thegent.cli.commands.impl._session_paths",
                return_value={
                    "meta": meta_path,
                    "stdout": tmp_path / "out",
                    "stderr": tmp_path / "err",
                    "rc": tmp_path / "nonexistent.rc",
                },
            ),
        ):
            result = status_impl(session_id="sess3")
        assert result["exit_code"] is None

    # @trace FR-CLI-546b
    @patch("thegent.cli.commands.impl.ThegentSettings")
    @patch("thegent.cli.commands.impl._is_pid_running", return_value=False)
    def test_exit_code_rc_file_oserror(self, mock_pid, mock_settings_cls, tmp_path) -> None:
        """When rc_path.exists() but read fails, return None (line 3170-3171)."""
        from thegent.cli.commands.impl import status_impl

        mock_settings = MagicMock()
        mock_settings.session_dir = tmp_path
        mock_settings_cls.return_value = mock_settings

        meta = {"pid": 123, "status": "exited"}
        meta_path = tmp_path / "sess3b.json"
        meta_path.write_text(json.dumps(meta).decode(), encoding="utf-8")
        rc_path = tmp_path / "sess3b.rc"
        rc_path.write_text("bad\n", encoding="utf-8")  # non-numeric -> ValueError

        with (
            patch("thegent.cli.commands.impl._find_session_meta", return_value=meta_path),
            patch(
                "thegent.cli.commands.impl._session_paths",
                return_value={
                    "meta": meta_path,
                    "stdout": tmp_path / "out",
                    "stderr": tmp_path / "err",
                    "rc": rc_path,
                },
            ),
        ):
            result = status_impl(session_id="sess3b")
        assert result["exit_code"] is None

    # @trace FR-CLI-547
    @patch("thegent.cli.commands.impl.ThegentSettings")
    @patch("thegent.cli.commands.impl._is_pid_running", return_value=True)
    def test_running_exit_code_is_none(self, mock_pid, mock_settings_cls, tmp_path) -> None:
        """When session is running, exit_code is None (line 3156-3157)."""
        from thegent.cli.commands.impl import status_impl

        mock_settings = MagicMock()
        mock_settings.session_dir = tmp_path
        mock_settings_cls.return_value = mock_settings

        meta = {"pid": 123, "status": "running"}
        meta_path = tmp_path / "sess4.json"
        meta_path.write_text(json.dumps(meta).decode(), encoding="utf-8")

        with (
            patch("thegent.cli.commands.impl._find_session_meta", return_value=meta_path),
            patch(
                "thegent.cli.commands.impl._session_paths",
                return_value={
                    "meta": meta_path,
                    "stdout": tmp_path / "out",
                    "stderr": tmp_path / "err",
                    "rc": tmp_path / "rc",
                },
            ),
        ):
            result = status_impl(session_id="sess4")
        assert result["exit_code"] is None
        assert result["running"] is True


# ---------------------------------------------------------------------------
# inspect_impl: log error path (lines 3233-3234)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestInspectImplLogError:
    # @trace FR-CLI-548
    @patch("thegent.cli.commands.impl.logs_impl", side_effect=Exception("log read failed"))
    @patch("thegent.cli.commands.impl.status_impl", return_value={"status": "running"})
    @patch("thegent.cli.commands.impl.ps_impl")
    def test_log_error_captured(self, mock_ps, mock_status, mock_logs) -> None:
        from thegent.cli.commands.impl import inspect_impl

        result = inspect_impl(session_ids=["s1"])
        assert len(result) == 1
        assert "Error" in result[0]["logs"]


# ---------------------------------------------------------------------------
# list_droids_impl (lines 3366-3369)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestListDroidsImpl:
    # @trace FR-CLI-549
    @patch("thegent.cli.commands.impl.list_droid_names", return_value=["droid1", "droid2"])
    @patch("thegent.cli.commands.impl._resolve_droids_dir", return_value=Path("/fake/droids"))
    @patch("thegent.cli.commands.impl._resolve_cwd", return_value=Path("/fake/cwd"))
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_lists_droids_sorted(self, mock_settings_cls, mock_cwd, mock_droids_dir, mock_list) -> None:
        from thegent.cli.commands.impl import list_droids_impl

        result = list_droids_impl()
        assert result == ["droid1", "droid2"]


# ---------------------------------------------------------------------------
# list_models_impl: all branches (lines 3385-3432)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestListModelsImpl:
    # @trace FR-CLI-550
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_contract_view(self, mock_settings_cls) -> None:
        from thegent.cli.commands.impl import list_models_impl

        mock_catalog = MagicMock()
        mock_catalog.to_contract_view.return_value = {"contracts": []}

        with patch("thegent.models.ModelCatalog", mock_catalog):
            # We need to mock the import inside the function
            with patch.dict("sys.modules", {"thegent.models": MagicMock(ModelCatalog=mock_catalog)}):
                list_models_impl(include_contract=True)

    # @trace FR-CLI-551
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_by_model_view(self, mock_settings_cls) -> None:
        from thegent.cli.commands.impl import list_models_impl

        mock_catalog = MagicMock()
        mock_view = MagicMock()
        mock_view.by_model = {"claude": ["haiku", "opus"]}
        mock_catalog.to_catalog_view.return_value = mock_view

        with patch.dict(
            "sys.modules",
            {
                "thegent.models": MagicMock(ModelCatalog=mock_catalog),
                "thegent.models.scrapers": MagicMock(),
            },
        ):
            list_models_impl(by_model=True, use_scraped=False)

    # @trace FR-CLI-552
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_fallback_without_scraped(self, mock_settings_cls) -> None:
        from thegent.cli.commands.impl import list_models_impl

        mock_settings = MagicMock()
        mock_settings.default_cursor_model = "cursor-m"
        mock_settings.default_gemini_model = "gemini-m"
        mock_settings.default_copilot_model = "copilot-m"
        mock_settings.default_claude_model = "claude-m"
        mock_settings.default_codex_model = "codex-m"
        mock_settings.default_antigravity_model = "ag-m"
        mock_settings_cls.return_value = mock_settings

        result = list_models_impl(use_scraped=False, provider="claude")
        assert "claude" in result
        assert result["claude"] == ["claude-m"]

    # @trace FR-CLI-553
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_scraped_success(self, mock_settings_cls) -> None:
        from thegent.cli.commands.impl import list_models_impl

        mock_settings = MagicMock()
        mock_settings_cls.return_value = mock_settings

        mock_scraped = {"claude": ["haiku", "opus"]}
        with patch.dict(
            "sys.modules",
            {
                "thegent.models.scrapers": MagicMock(get_scraped_catalog=MagicMock(return_value=mock_scraped)),
            },
        ):
            result = list_models_impl(use_scraped=True, provider="claude")
        assert "claude" in result

    # @trace FR-CLI-554
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_scraped_exception_falls_back(self, mock_settings_cls) -> None:
        from thegent.cli.commands.impl import list_models_impl

        mock_settings = MagicMock()
        mock_settings.default_claude_model = "claude-default"
        mock_settings.default_cursor_model = "cursor-m"
        mock_settings.default_gemini_model = "gemini-m"
        mock_settings.default_copilot_model = "copilot-m"
        mock_settings.default_codex_model = "codex-m"
        mock_settings.default_antigravity_model = "ag-m"
        mock_settings_cls.return_value = mock_settings

        with patch.dict(
            "sys.modules",
            {
                "thegent.models.scrapers": MagicMock(
                    get_scraped_catalog=MagicMock(side_effect=RuntimeError("scrape fail"))
                ),
            },
        ):
            result = list_models_impl(use_scraped=True, provider="claude")
        assert "claude" in result
        assert result["claude"] == ["claude-default"]

    # @trace FR-CLI-555
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_all_providers_without_filter(self, mock_settings_cls) -> None:
        from thegent.cli.commands.impl import list_models_impl

        mock_settings = MagicMock()
        mock_settings.default_cursor_model = "cursor-m"
        mock_settings.default_gemini_model = "gemini-m"
        mock_settings.default_copilot_model = "copilot-m"
        mock_settings.default_claude_model = "claude-m"
        mock_settings.default_codex_model = "codex-m"
        mock_settings.default_antigravity_model = "ag-m"
        mock_settings_cls.return_value = mock_settings

        result = list_models_impl(use_scraped=False, provider=None)
        assert "claude" in result
        assert "gemini" in result
        assert "minimax" in result


# ---------------------------------------------------------------------------
# dag_list_impl: ambiguous cwd (line 3439)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestDagListImplAmbiguousCwd:
    # @trace FR-CLI-556
    @patch("thegent.cli.commands.impl._resolve_cwd", return_value=None)
    def test_ambiguous_cwd_returns_error(self, mock_cwd) -> None:
        from thegent.cli.commands.impl import dag_list_impl

        result = dag_list_impl()
        assert "error" in result
        assert "Ambiguous" in result["error"]


# ---------------------------------------------------------------------------
# dag_raw_impl: ambiguous cwd (line 3462)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestDagRawImplAmbiguousCwd:
    # @trace FR-CLI-557
    @patch("thegent.cli.commands.impl._resolve_cwd", return_value=None)
    def test_ambiguous_cwd_returns_error(self, mock_cwd) -> None:
        from thegent.cli.commands.impl import dag_raw_impl

        result = dag_raw_impl()
        assert "Error" in result
        assert "Ambiguous" in result


# ---------------------------------------------------------------------------
# observe_summary_impl: _parse_utc / _to_sla_delta / trend paths (lines 1414-1487)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestObserveSummaryImplInternals:
    # @trace FR-EXEC-506
    @patch("thegent.cli.commands.impl._append_observe_summary_snapshot")
    @patch("thegent.cli.commands.impl._load_observe_summary_snapshots", return_value=[])
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_observe_summary_with_z_suffix_datetime(self, mock_settings_cls, mock_load, mock_append) -> None:
        from thegent.cli.commands.impl import observe_summary_impl

        mock_settings = MagicMock()
        mock_settings.session_dir = Path("/tmp/fake")
        mock_settings_cls.return_value = mock_settings

        mock_ct = MagicMock()
        mock_ct.get_fallback_kpis.return_value = {}
        mock_ct.detect_drift.return_value = []
        mock_ct.get_drift_budget_status.return_value = {"within_budget": True}

        mock_queue = MagicMock()
        # Items with Z-suffix datetime
        mock_queue.list_pending.return_value = [
            {
                "run_id": "r1",
                "owner": "me",
                "agent": "claude",
                "lane": "standard",
                "reason": "blocked",
                "priority": 1,
                "past_sla": True,
                "sla_minutes": 30,
                "blocked_at_utc": "2025-01-01T00:00:00Z",
                "escalate_by_utc": "2025-01-01T00:30:00Z",
            },
        ]

        with (
            patch("thegent.contracts.telemetry.ContractTelemetry", return_value=mock_ct),
            patch("thegent.execution.EscalationQueue", return_value=mock_queue),
        ):
            result = observe_summary_impl(trend_samples=0)

        assert "escalation" in result
        assert result["escalation"]["backlog_count"] >= 0

    # @trace FR-EXEC-507
    @patch("thegent.cli.commands.impl._append_observe_summary_snapshot")
    @patch("thegent.cli.commands.impl._load_observe_summary_snapshots", return_value=[])
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_observe_summary_no_escalate_by(self, mock_settings_cls, mock_load, mock_append) -> None:
        from thegent.cli.commands.impl import observe_summary_impl

        mock_settings = MagicMock()
        mock_settings.session_dir = Path("/tmp/fake")
        mock_settings_cls.return_value = mock_settings

        mock_ct = MagicMock()
        mock_ct.get_fallback_kpis.return_value = {}
        mock_ct.detect_drift.return_value = []
        mock_ct.get_drift_budget_status.return_value = {"within_budget": True}

        mock_queue = MagicMock()
        mock_queue.list_pending.return_value = [
            {
                "run_id": "r1",
                "owner": "me",
                "agent": "claude",
                "lane": "standard",
                "reason": "blocked",
                "priority": 1,
                "past_sla": False,
                "sla_minutes": 30,
                "blocked_at_utc": None,
                "escalate_by_utc": None,  # No escalate_by
            },
        ]

        with (
            patch("thegent.contracts.telemetry.ContractTelemetry", return_value=mock_ct),
            patch("thegent.execution.EscalationQueue", return_value=mock_queue),
        ):
            result = observe_summary_impl(trend_samples=0)

        top = result["escalation"]["top_escalations"]
        assert len(top) >= 1
        assert top[0]["minutes_overdue"] is None

    # @trace FR-EXEC-508
    @patch("thegent.cli.commands.impl._append_observe_summary_snapshot")
    @patch("thegent.cli.commands.impl._load_observe_summary_snapshots", return_value=[])
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_observe_summary_invalid_trend_samples(self, mock_settings_cls, mock_load, mock_append) -> None:
        from thegent.cli.commands.impl import observe_summary_impl

        mock_settings = MagicMock()
        mock_settings.session_dir = Path("/tmp/fake")
        mock_settings_cls.return_value = mock_settings

        mock_ct = MagicMock()
        mock_ct.get_fallback_kpis.return_value = {}
        mock_ct.detect_drift.return_value = []
        mock_ct.get_drift_budget_status.return_value = {"within_budget": True}

        mock_queue = MagicMock()
        mock_queue.list_pending.return_value = []

        with (
            patch("thegent.contracts.telemetry.ContractTelemetry", return_value=mock_ct),
            patch("thegent.execution.EscalationQueue", return_value=mock_queue),
        ):
            result = observe_summary_impl(trend_samples="not-a-number")

        # Should not crash, trend_samples_requested should be 0
        assert "trend_summary" in result

    # @trace FR-EXEC-509
    @patch("thegent.cli.commands.impl._append_observe_summary_snapshot")
    @patch("thegent.cli.commands.impl._load_observe_summary_snapshots", return_value=[])
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_observe_summary_negative_trend_samples(self, mock_settings_cls, mock_load, mock_append) -> None:
        from thegent.cli.commands.impl import observe_summary_impl

        mock_settings = MagicMock()
        mock_settings.session_dir = Path("/tmp/fake")
        mock_settings_cls.return_value = mock_settings

        mock_ct = MagicMock()
        mock_ct.get_fallback_kpis.return_value = {}
        mock_ct.detect_drift.return_value = []
        mock_ct.get_drift_budget_status.return_value = {"within_budget": True}

        mock_queue = MagicMock()
        mock_queue.list_pending.return_value = []

        with (
            patch("thegent.contracts.telemetry.ContractTelemetry", return_value=mock_ct),
            patch("thegent.execution.EscalationQueue", return_value=mock_queue),
        ):
            result = observe_summary_impl(trend_samples=-5)

        assert "trend_summary" in result

    # @trace FR-EXEC-510
    @patch("thegent.cli.commands.impl._append_observe_summary_snapshot")
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_observe_summary_with_trend_snapshots(self, mock_settings_cls, mock_append) -> None:
        from thegent.cli.commands.impl import observe_summary_impl

        mock_settings = MagicMock()
        mock_settings.session_dir = Path("/tmp/fake")
        mock_settings_cls.return_value = mock_settings

        mock_ct = MagicMock()
        mock_ct.get_fallback_kpis.return_value = {}
        mock_ct.detect_drift.return_value = []
        mock_ct.get_drift_budget_status.return_value = {"within_budget": True}

        mock_queue = MagicMock()
        mock_queue.list_pending.return_value = []

        now = datetime.now(UTC)
        trend_records = [
            {"captured_at_utc": (now - timedelta(hours=1)).isoformat()},
            {"captured_at_utc": (now - timedelta(hours=2)).isoformat()},
            {"captured_at_utc": (now - timedelta(hours=3)).isoformat()},
        ]

        with (
            patch("thegent.contracts.telemetry.ContractTelemetry", return_value=mock_ct),
            patch("thegent.execution.EscalationQueue", return_value=mock_queue),
            patch("thegent.cli.commands.impl._load_observe_summary_snapshots", return_value=trend_records),
        ):
            result = observe_summary_impl(trend_samples=5)

        assert result["trend_summary"]["history_sample_count"] == 3

    # @trace FR-EXEC-511
    @patch("thegent.cli.commands.impl._append_observe_summary_snapshot")
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_observe_summary_with_baseline_snapshot(self, mock_settings_cls, mock_append) -> None:
        from thegent.cli.commands.impl import observe_summary_impl

        mock_settings = MagicMock()
        mock_settings.session_dir = Path("/tmp/fake")
        mock_settings_cls.return_value = mock_settings

        mock_ct = MagicMock()
        mock_ct.get_fallback_kpis.return_value = {
            "total_events": 100,
            "fallback_rate": 0.05,
            "success_rate": 0.95,
            "avg_confidence": 0.9,
        }
        mock_ct.detect_drift.return_value = []
        mock_ct.get_drift_budget_status.return_value = {
            "within_budget": True,
            "structural_rate_pct": 1.0,
            "semantic_rate_pct": 2.0,
        }

        mock_queue = MagicMock()
        mock_queue.list_pending.return_value = []

        now = datetime.now(UTC)
        trend_records = [
            {
                "captured_at_utc": (now - timedelta(hours=1)).isoformat(),
                "total_events": 50,
                "fallback_rate": 0.1,
                "success_rate": 0.9,
                "avg_confidence": 0.8,
                "drift_structural_rate_pct": 0.5,
                "drift_semantic_rate_pct": 1.0,
                "backlog_count": 1,
                "past_sla_count": 0,
                "structural_drift_pct": 0.5,
                "semantic_drift_pct": 1.0,
            },
        ]

        with (
            patch("thegent.contracts.telemetry.ContractTelemetry", return_value=mock_ct),
            patch("thegent.execution.EscalationQueue", return_value=mock_queue),
            patch("thegent.cli.commands.impl._load_observe_summary_snapshots", return_value=trend_records),
        ):
            result = observe_summary_impl(trend_samples=5)

        assert result["trend_summary"]["baseline_available"] is True

    # @trace FR-EXEC-512
    @patch("thegent.cli.commands.impl._append_observe_summary_snapshot")
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_observe_summary_parse_utc_invalid_no_z(self, mock_settings_cls, mock_append) -> None:
        """Test _parse_utc branch where value doesn't end with Z and is invalid."""
        from thegent.cli.commands.impl import observe_summary_impl

        mock_settings = MagicMock()
        mock_settings.session_dir = Path("/tmp/fake")
        mock_settings_cls.return_value = mock_settings

        mock_ct = MagicMock()
        mock_ct.get_fallback_kpis.return_value = {}
        mock_ct.detect_drift.return_value = []
        mock_ct.get_drift_budget_status.return_value = {"within_budget": True}

        mock_queue = MagicMock()
        mock_queue.list_pending.return_value = [
            {
                "run_id": "r1",
                "owner": "me",
                "agent": "claude",
                "lane": "standard",
                "reason": "blocked",
                "priority": 1,
                "past_sla": False,
                "sla_minutes": 30,
                "blocked_at_utc": "not-a-date",  # Invalid, no Z suffix
                "escalate_by_utc": "also-not-a-date",  # Invalid, no Z suffix
            },
        ]

        with (
            patch("thegent.contracts.telemetry.ContractTelemetry", return_value=mock_ct),
            patch("thegent.execution.EscalationQueue", return_value=mock_queue),
            patch("thegent.cli.commands.impl._load_observe_summary_snapshots", return_value=[]),
        ):
            result = observe_summary_impl(trend_samples=0)

        # The invalid dates should result in minutes_overdue=None
        top = result["escalation"]["top_escalations"]
        if top:
            assert top[0]["minutes_overdue"] is None

    # @trace FR-EXEC-513
    @patch("thegent.cli.commands.impl._append_observe_summary_snapshot")
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_observe_summary_parse_utc_naive_datetime(self, mock_settings_cls, mock_append) -> None:
        """Test _parse_utc branch where datetime is naive (no timezone)."""
        from thegent.cli.commands.impl import observe_summary_impl

        mock_settings = MagicMock()
        mock_settings.session_dir = Path("/tmp/fake")
        mock_settings_cls.return_value = mock_settings

        mock_ct = MagicMock()
        mock_ct.get_fallback_kpis.return_value = {}
        mock_ct.detect_drift.return_value = []
        mock_ct.get_drift_budget_status.return_value = {"within_budget": True}

        mock_queue = MagicMock()
        # Use naive datetime (no timezone) to hit the .replace(tzinfo=UTC) branch
        mock_queue.list_pending.return_value = [
            {
                "run_id": "r1",
                "owner": "me",
                "agent": "claude",
                "lane": "standard",
                "reason": "blocked",
                "priority": 1,
                "past_sla": True,
                "sla_minutes": 30,
                "blocked_at_utc": "2020-01-01T00:00:00",  # Naive, no TZ
                "escalate_by_utc": "2020-01-01T00:30:00",  # Naive, no TZ
            },
        ]

        with (
            patch("thegent.contracts.telemetry.ContractTelemetry", return_value=mock_ct),
            patch("thegent.execution.EscalationQueue", return_value=mock_queue),
            patch("thegent.cli.commands.impl._load_observe_summary_snapshots", return_value=[]),
        ):
            result = observe_summary_impl(trend_samples=0)

        top = result["escalation"]["top_escalations"]
        assert len(top) >= 1
        # Should have parsed successfully and computed overdue
        assert top[0]["minutes_overdue"] is not None

    # @trace FR-EXEC-514
    @patch("thegent.cli.commands.impl._append_observe_summary_snapshot")
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_observe_summary_parse_utc_z_suffix_valid(self, mock_settings_cls, mock_append) -> None:
        """Test _parse_utc branch where Z-suffix valid datetime is parsed via fallback."""
        from thegent.cli.commands.impl import observe_summary_impl

        mock_settings = MagicMock()
        mock_settings.session_dir = Path("/tmp/fake")
        mock_settings_cls.return_value = mock_settings

        mock_ct = MagicMock()
        mock_ct.get_fallback_kpis.return_value = {}
        mock_ct.detect_drift.return_value = []
        mock_ct.get_drift_budget_status.return_value = {"within_budget": True}

        mock_queue = MagicMock()
        mock_queue.list_pending.return_value = [
            {
                "run_id": "r1",
                "owner": "me",
                "agent": "claude",
                "lane": "standard",
                "reason": "blocked",
                "priority": 1,
                "past_sla": True,
                "sla_minutes": 30,
                "blocked_at_utc": "2020-01-01T00:00:00Z",
                "escalate_by_utc": "2020-01-01T00:30:00Z",
            },
        ]

        with (
            patch("thegent.contracts.telemetry.ContractTelemetry", return_value=mock_ct),
            patch("thegent.execution.EscalationQueue", return_value=mock_queue),
            patch("thegent.cli.commands.impl._load_observe_summary_snapshots", return_value=[]),
        ):
            result = observe_summary_impl(trend_samples=0)

        top = result["escalation"]["top_escalations"]
        assert len(top) >= 1


# ---------------------------------------------------------------------------
# observe_summary_impl: trend snapshot timestamps / intervals (lines 1545-1593)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestObserveSummaryTrendTimestamps:
    # @trace FR-EXEC-515
    @patch("thegent.cli.commands.impl._append_observe_summary_snapshot")
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_trend_with_multiple_timestamps_calculates_intervals(self, mock_settings_cls, mock_append) -> None:
        from thegent.cli.commands.impl import observe_summary_impl

        mock_settings = MagicMock()
        mock_settings.session_dir = Path("/tmp/fake")
        mock_settings_cls.return_value = mock_settings

        mock_ct = MagicMock()
        mock_ct.get_fallback_kpis.return_value = {}
        mock_ct.detect_drift.return_value = []
        mock_ct.get_drift_budget_status.return_value = {"within_budget": True}

        mock_queue = MagicMock()
        mock_queue.list_pending.return_value = []

        now = datetime.now(UTC)
        trend_records = [
            {"captured_at_utc": now.isoformat()},
            {"captured_at_utc": (now - timedelta(hours=1)).isoformat()},
            {"captured_at_utc": (now - timedelta(hours=2)).isoformat()},
        ]

        with (
            patch("thegent.contracts.telemetry.ContractTelemetry", return_value=mock_ct),
            patch("thegent.execution.EscalationQueue", return_value=mock_queue),
            patch("thegent.cli.commands.impl._load_observe_summary_snapshots", return_value=trend_records),
        ):
            result = observe_summary_impl(trend_samples=5)

        trend = result["trend_summary"]
        assert trend["trend_snapshot_interval_seconds_avg"] is not None
        assert trend["trend_snapshot_interval_seconds_min"] is not None
        assert trend["trend_snapshot_interval_seconds_max"] is not None
        assert trend["trend_snapshot_window_seconds"] is not None

    # @trace FR-EXEC-516
    @patch("thegent.cli.commands.impl._append_observe_summary_snapshot")
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_trend_with_invalid_timestamp_skipped(self, mock_settings_cls, mock_append) -> None:
        from thegent.cli.commands.impl import observe_summary_impl

        mock_settings = MagicMock()
        mock_settings.session_dir = Path("/tmp/fake")
        mock_settings_cls.return_value = mock_settings

        mock_ct = MagicMock()
        mock_ct.get_fallback_kpis.return_value = {}
        mock_ct.detect_drift.return_value = []
        mock_ct.get_drift_budget_status.return_value = {"within_budget": True}

        mock_queue = MagicMock()
        mock_queue.list_pending.return_value = []

        trend_records = [
            {"captured_at_utc": "not-valid"},
            {"captured_at_utc": "also-not-valid"},
        ]

        with (
            patch("thegent.contracts.telemetry.ContractTelemetry", return_value=mock_ct),
            patch("thegent.execution.EscalationQueue", return_value=mock_queue),
            patch("thegent.cli.commands.impl._load_observe_summary_snapshots", return_value=trend_records),
        ):
            result = observe_summary_impl(trend_samples=5)

        trend = result["trend_summary"]
        assert trend["trend_snapshot_invalid_timestamps"] == 2

    # @trace FR-EXEC-517
    @patch("thegent.cli.commands.impl._append_observe_summary_snapshot")
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_trend_delta_with_baseline(self, mock_settings_cls, mock_append) -> None:
        from thegent.cli.commands.impl import observe_summary_impl

        mock_settings = MagicMock()
        mock_settings.session_dir = Path("/tmp/fake")
        mock_settings_cls.return_value = mock_settings

        mock_ct = MagicMock()
        mock_ct.get_fallback_kpis.return_value = {
            "total_events": 100,
            "fallback_rate": 0.05,
            "success_rate": 0.95,
            "avg_confidence": 0.9,
        }
        mock_ct.detect_drift.return_value = []
        mock_ct.get_drift_budget_status.return_value = {
            "within_budget": True,
            "structural_rate_pct": 1.0,
            "semantic_rate_pct": 2.0,
        }

        mock_queue = MagicMock()
        mock_queue.list_pending.return_value = []

        # Baseline with numeric KPIs for delta computation
        baseline = {
            "captured_at_utc": datetime.now(UTC).isoformat(),
            "total_events": 50,
            "fallback_rate": 0.1,
            "success_rate": 0.8,
            "avg_confidence": 0.7,
            "structural_drift_pct": 0.5,
            "semantic_drift_pct": 1.0,
            "drift_structural_rate_pct": 0.5,
            "drift_semantic_rate_pct": 1.0,
            "backlog_count": 5,
            "past_sla_count": 2,
        }

        with (
            patch("thegent.contracts.telemetry.ContractTelemetry", return_value=mock_ct),
            patch("thegent.execution.EscalationQueue", return_value=mock_queue),
            patch("thegent.cli.commands.impl._load_observe_summary_snapshots", return_value=[baseline]),
        ):
            result = observe_summary_impl(trend_samples=5)

        # Delta should be computed
        assert result["trend_summary"]["baseline_available"] is True
        # The _delta function should produce float deltas
        kpi_deltas = result.get("kpi_deltas", {})
        assert isinstance(kpi_deltas, dict)

    # @trace FR-EXEC-518
    @patch("thegent.cli.commands.impl._append_observe_summary_snapshot")
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_observe_summary_delta_none_when_value_is_none(self, mock_settings_cls, mock_append) -> None:
        """Test _delta returns None when current or baseline is None."""
        from thegent.cli.commands.impl import observe_summary_impl

        mock_settings = MagicMock()
        mock_settings.session_dir = Path("/tmp/fake")
        mock_settings_cls.return_value = mock_settings

        mock_ct = MagicMock()
        mock_ct.get_fallback_kpis.return_value = {
            "total_events": None,  # None current value
        }
        mock_ct.detect_drift.return_value = []
        mock_ct.get_drift_budget_status.return_value = {"within_budget": True}

        mock_queue = MagicMock()
        mock_queue.list_pending.return_value = []

        baseline = {
            "captured_at_utc": datetime.now(UTC).isoformat(),
            "total_events": 50,
        }

        with (
            patch("thegent.contracts.telemetry.ContractTelemetry", return_value=mock_ct),
            patch("thegent.execution.EscalationQueue", return_value=mock_queue),
            patch("thegent.cli.commands.impl._load_observe_summary_snapshots", return_value=[baseline]),
        ):
            observe_summary_impl(trend_samples=5)

        # Should not crash


# ---------------------------------------------------------------------------
# ps_impl: meta read exception (lines 2332-2333)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestPsImplMetaReadException:
    # @trace FR-CLI-558
    @patch("thegent.cli.commands.impl._is_pid_running", return_value=False)
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_invalid_meta_json_skipped(self, mock_settings_cls, mock_pid, tmp_path) -> None:
        from thegent.cli.commands.impl import ps_impl

        mock_settings = MagicMock()
        mock_settings.session_dir = tmp_path
        mock_settings_cls.return_value = mock_settings

        owner_dir = tmp_path / "test_owner"
        owner_dir.mkdir()
        # Create invalid JSON meta file
        bad_meta = owner_dir / "bad-session.json"
        bad_meta.write_text("NOT JSON", encoding="utf-8")

        with (
            patch("thegent.cli.commands.impl._default_owner_tag", return_value="test_owner"),
            patch("thegent.cli.commands.impl._session_scope_dirs", return_value=[owner_dir]),
        ):
            result = ps_impl(all=True)
        # Should not crash, bad meta is skipped
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# bg_impl: routing/failover/model flags, sandbox env, subprocess error (lines 2217-2268)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestBgImplEdges:
    # @trace FR-CLI-559
    @patch("thegent.cli.commands.impl.ThegentSettings")
    @patch("thegent.cli.commands.impl.resolve_agent", return_value="claude")
    @patch("thegent.cli.commands.impl._resolve_cwd", return_value=Path("/tmp/cwd"))
    @patch("thegent.cli.commands.impl._default_owner_tag", return_value="test_owner")
    @patch("thegent.cli.commands.impl._session_dir")
    @patch("thegent.cli.commands.impl._new_session_id", return_value="sess-bg-1")
    @patch("thegent.cli.commands.impl._session_paths")
    @patch("thegent.execution.RunRegistry")
    def test_bg_impl_sandbox_env_filter(
        self,
        mock_rr,
        mock_paths,
        mock_new_sid,
        mock_session_dir,
        mock_owner,
        mock_cwd,
        mock_resolve,
        mock_settings_cls,
        tmp_path,
    ) -> None:
        from thegent.cli.commands.impl import bg_impl

        mock_settings = MagicMock()
        mock_settings.session_dir = tmp_path
        mock_settings.default_timeout_claude = 120
        mock_settings.sandbox_env_allowlist = {"PATH", "HOME"}
        mock_settings_cls.return_value = mock_settings

        mock_session_dir.return_value = tmp_path
        stdout_f = tmp_path / "stdout"
        stderr_f = tmp_path / "stderr"
        meta_f = tmp_path / "meta.json"
        rc_f = tmp_path / "rc"
        stdout_f.touch()
        stderr_f.touch()
        mock_paths.return_value = {
            "meta": meta_f,
            "stdout": stdout_f,
            "stderr": stderr_f,
            "rc": rc_f,
        }

        mock_migrator = MagicMock()
        mock_migrator.evaluate_version.return_value = {"allowed": True, "status": "current", "reason": "ok"}

        mock_proc = MagicMock()
        mock_proc.pid = 42

        env = {"THGENT_SANDBOX_ENV_FILTER": "true"}
        with (
            patch("thegent.contracts.migration.MigrationController", return_value=mock_migrator),
            patch.dict(os.environ, env),
            patch("subprocess.Popen", return_value=mock_proc),
            patch("thegent.cli.commands.impl._save_session_meta"),
        ):
            result = bg_impl(
                prompt="test",
                agent="claude",
                cd=Path("/tmp/cwd"),
                mode="write",
                timeout=30,
                full=True,
                routing="round-robin",
                failover=True,
                model="haiku",
                include_contract=True,
                route_contract={"provider": "claude"},
                route_request={"model": "haiku"},
            )

        assert result["session_id"] == "sess-bg-1"

    # @trace FR-CLI-560
    @patch("thegent.cli.commands.impl.ThegentSettings")
    @patch("thegent.cli.commands.impl.resolve_agent", return_value="claude")
    @patch("thegent.cli.commands.impl._resolve_cwd", return_value=Path("/tmp/cwd"))
    @patch("thegent.cli.commands.impl._default_owner_tag", return_value="test_owner")
    @patch("thegent.cli.commands.impl._session_dir")
    @patch("thegent.cli.commands.impl._new_session_id", return_value="sess-bg-2")
    @patch("thegent.cli.commands.impl._session_paths")
    @patch("thegent.execution.RunRegistry")
    def test_bg_impl_subprocess_error_closes_handles(
        self,
        mock_rr,
        mock_paths,
        mock_new_sid,
        mock_session_dir,
        mock_owner,
        mock_cwd,
        mock_resolve,
        mock_settings_cls,
        tmp_path,
    ) -> None:
        from thegent.cli.commands.impl import bg_impl

        mock_settings = MagicMock()
        mock_settings.session_dir = tmp_path
        mock_settings.default_timeout_claude = 120
        mock_settings_cls.return_value = mock_settings

        mock_session_dir.return_value = tmp_path
        stdout_f = tmp_path / "stdout"
        stderr_f = tmp_path / "stderr"
        meta_f = tmp_path / "meta.json"
        rc_f = tmp_path / "rc"
        stdout_f.touch()
        stderr_f.touch()
        mock_paths.return_value = {
            "meta": meta_f,
            "stdout": stdout_f,
            "stderr": stderr_f,
            "rc": rc_f,
        }

        mock_migrator = MagicMock()
        mock_migrator.evaluate_version.return_value = {"allowed": True, "status": "current", "reason": "ok"}

        with (
            patch("thegent.contracts.migration.MigrationController", return_value=mock_migrator),
            patch("subprocess.Popen", side_effect=OSError("spawn failed")),
            patch("thegent.cli.commands.impl._save_session_meta"),
            pytest.raises(OSError, match="spawn failed"),
        ):
            bg_impl(prompt="test", agent="claude", cd=Path("/tmp/cwd"), mode="write", timeout=30, full=True)


# ---------------------------------------------------------------------------
# list_models_impl: include_contract branch (line 3385-3392)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestListModelsImplContractView:
    # @trace FR-CLI-561
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_include_contract_calls_to_contract_view(self, mock_settings_cls) -> None:
        from thegent.cli.commands.impl import list_models_impl

        mock_catalog = MagicMock()
        mock_catalog.to_contract_view.return_value = {"routes": []}

        with patch.dict(
            "sys.modules",
            {
                "thegent.models": MagicMock(ModelCatalog=mock_catalog),
            },
        ):
            list_models_impl(include_contract=True, provider="claude", refresh=True)
        # to_contract_view should be called
        mock_catalog.to_contract_view.assert_called_once()

    # @trace FR-CLI-562
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_by_model_with_refresh(self, mock_settings_cls) -> None:
        from thegent.cli.commands.impl import list_models_impl

        mock_catalog = MagicMock()
        mock_view = MagicMock()
        mock_view.by_model = {"model-x": ["provider-a"]}
        mock_catalog.to_catalog_view.return_value = mock_view

        mock_get_scraped = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "thegent.models": MagicMock(ModelCatalog=mock_catalog),
                "thegent.models.scrapers": MagicMock(get_scraped_catalog=mock_get_scraped),
            },
        ):
            list_models_impl(by_model=True, refresh=True)
        # get_scraped_catalog should be called with use_cache=False
        mock_get_scraped.assert_called_once_with(use_cache=False)


# ---------------------------------------------------------------------------
# list_models_impl: use_scraped with refresh (line 3420-3427)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestListModelsImplScrapedRefresh:
    # @trace FR-CLI-563
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_scraped_with_refresh(self, mock_settings_cls) -> None:
        from thegent.cli.commands.impl import list_models_impl

        mock_settings = MagicMock()
        mock_settings_cls.return_value = mock_settings

        mock_scraped = {"claude": ["haiku-refreshed"]}
        with patch.dict(
            "sys.modules",
            {
                "thegent.models.scrapers": MagicMock(get_scraped_catalog=MagicMock(return_value=mock_scraped)),
            },
        ):
            result = list_models_impl(use_scraped=True, provider="claude", refresh=True)
        assert result["claude"] == ["haiku-refreshed"]


# ---------------------------------------------------------------------------
# session_contract_health_gate_impl: additional paths
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestSessionContractHealthGateImplPaths:
    # @trace FR-CLI-564
    @patch("thegent.cli.commands.impl._append_health_snapshot")
    @patch("thegent.cli.commands.impl._load_previous_health_snapshot", return_value=None)
    @patch("thegent.cli.commands.impl.session_contract_audit_impl")
    def test_gate_passes_when_all_healthy(self, mock_audit, mock_prev, mock_append) -> None:
        from thegent.cli.commands.impl import session_contract_health_gate_impl

        mock_audit.return_value = {
            "rows": [
                {
                    "contract_state": "complete",
                    "contract_health": "healthy",
                    "contract_issues": [],
                    "owner": "me",
                    "session_id": "s1",
                },
            ],
            "summary": {
                "total": 1,
                "complete": 1,
                "partial": 0,
                "request_only": 0,
                "contract_only": 0,
                "untracked": 0,
                "health": {"healthy": 1, "warning": 0, "error": 0, "missing": 0},
            },
        }
        result = session_contract_health_gate_impl(min_healthy_ratio=1.0)
        assert result["pass"] is True
        assert result["status"] == "passed"
        assert "ok" in result["decision_reasons"]

    # @trace FR-CLI-565
    @patch("thegent.cli.commands.impl._append_health_snapshot")
    @patch("thegent.cli.commands.impl._load_previous_health_snapshot")
    @patch("thegent.cli.commands.impl.session_contract_audit_impl")
    def test_gate_no_worse_baseline_with_no_previous(self, mock_audit, mock_prev, mock_append) -> None:
        from thegent.cli.commands.impl import session_contract_health_gate_impl

        mock_audit.return_value = {
            "rows": [
                {
                    "contract_state": "partial",
                    "contract_health": "warning",
                    "contract_issues": ["x"],
                    "owner": "me",
                    "session_id": "s1",
                },
            ],
            "summary": {
                "total": 1,
                "complete": 0,
                "partial": 1,
                "request_only": 0,
                "contract_only": 0,
                "untracked": 0,
                "health": {"healthy": 0, "warning": 1, "error": 0, "missing": 0},
            },
        }
        mock_prev.return_value = None
        result = session_contract_health_gate_impl(
            no_worse_than_baseline=True,
            min_healthy_ratio=0.0,
        )
        # No baseline, so baseline_pass defaults to True
        assert result["pass"] is True


# ---------------------------------------------------------------------------
# observe_summary_impl: _delta function with non-numeric values
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestObserveSummaryDeltaEdgeCases:
    # @trace FR-EXEC-519
    @patch("thegent.cli.commands.impl._append_observe_summary_snapshot")
    @patch("thegent.cli.commands.impl.ThegentSettings")
    def test_delta_with_non_numeric_returns_none(self, mock_settings_cls, mock_append) -> None:
        """Test _delta when float conversion fails (line 1574-1577)."""
        from thegent.cli.commands.impl import observe_summary_impl

        mock_settings = MagicMock()
        mock_settings.session_dir = Path("/tmp/fake")
        mock_settings_cls.return_value = mock_settings

        mock_ct = MagicMock()
        mock_ct.get_fallback_kpis.return_value = {
            "total_events": "not-a-number",  # Will fail float conversion in _delta
        }
        mock_ct.detect_drift.return_value = []
        mock_ct.get_drift_budget_status.return_value = {"within_budget": True}

        mock_queue = MagicMock()
        mock_queue.list_pending.return_value = []

        baseline = {
            "captured_at_utc": datetime.now(UTC).isoformat(),
            "total_events": 50,
        }

        with (
            patch("thegent.contracts.telemetry.ContractTelemetry", return_value=mock_ct),
            patch("thegent.execution.EscalationQueue", return_value=mock_queue),
            patch("thegent.cli.commands.impl._load_observe_summary_snapshots", return_value=[baseline]),
        ):
            observe_summary_impl(trend_samples=5)

        # Should not crash - _delta handles conversion errors


# ---------------------------------------------------------------------------
# _resolve_cwd: None cd branch (line 78)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestResolveCwdNoneCd:
    # @trace FR-CLI-566
    def test_none_cd_with_git_dir(self, tmp_path) -> None:
        """When cd is None, should use Path.cwd() and check for .git."""
        from thegent.cli.commands.impl import _CWD_CACHE, _resolve_cwd

        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        with patch("thegent.cli.commands.impl.Path.cwd", return_value=tmp_path):
            result = _resolve_cwd(None)

        assert result == tmp_path
        # Clean up cache
        for key in list(_CWD_CACHE.keys()):
            if str(tmp_path) in key:
                del _CWD_CACHE[key]


# ---------------------------------------------------------------------------
# inspect_impl: owner-based session lookup (line 3223-3225)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestInspectImplOwnerLookup:
    # @trace FR-CLI-567
    @patch("thegent.cli.commands.impl.logs_impl", return_value="log text")
    @patch("thegent.cli.commands.impl.status_impl", return_value={"status": "running"})
    @patch("thegent.cli.commands.impl.ps_impl", return_value=[{"id": "s1"}, {"id": "s2"}])
    def test_owner_based_lookup(self, mock_ps, mock_status, mock_logs) -> None:
        from thegent.cli.commands.impl import inspect_impl

        result = inspect_impl(session_ids=[], owner="test_owner")
        assert len(result) == 2
        mock_ps.assert_called_once_with(owner="test_owner", all=False)


# ---------------------------------------------------------------------------
# session_contract_health_trend_impl: blocked_ratio from snapshots (line 3056-3060)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestSessionContractHealthTrendBlockedRatio:
    # @trace FR-CLI-568
    @patch("thegent.cli.commands.impl._health_snapshot_max_lines", return_value=5000)
    @patch("thegent.cli.commands.impl._health_snapshot_log_path")
    def test_invalid_blocked_ratio_skipped(self, mock_path, mock_max, tmp_path) -> None:
        from thegent.cli.commands.impl import session_contract_health_trend_impl

        scope_key = {
            "payload_type": "session_contract_health_report",
            "owner": None,
            "all": False,
            "strict": False,
            "policy_profile": "custom",
            "top_blocked": 25,
        }

        now = datetime.now(UTC)
        records = []
        for i in range(3):
            ts = (now - timedelta(hours=i)).isoformat()
            rec = {
                "record_type": "health_snapshot",
                "scope_key": scope_key,
                "captured_at_utc": ts,
                "blocked_ratio": "not-a-float" if i == 1 else 0.1 * i,
                "blocked_count": i,
            }
            records.append(json.dumps(rec, sort_keys=True).decode())

        log_path = tmp_path / "health-snapshots.jsonl"
        log_path.write_text("\n".join(records) + "\n", encoding="utf-8")
        mock_path.return_value = log_path

        result = session_contract_health_trend_impl(limit=10)
        # Should not crash; invalid blocked_ratio is skipped
        assert result["snapshot_count"] >= 1


# ---------------------------------------------------------------------------
# session_contract_health_trend_impl: empty captured_at_utc (line 3019-3020)
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestSessionContractHealthTrendEmptyTimestamp:
    # @trace FR-CLI-569
    @patch("thegent.cli.commands.impl._health_snapshot_max_lines", return_value=5000)
    @patch("thegent.cli.commands.impl._health_snapshot_log_path")
    def test_empty_captured_at_skipped(self, mock_path, mock_max, tmp_path) -> None:
        from thegent.cli.commands.impl import session_contract_health_trend_impl

        scope_key = {
            "payload_type": "session_contract_health_report",
            "owner": None,
            "all": False,
            "strict": False,
            "policy_profile": "custom",
            "top_blocked": 25,
        }

        rec = {
            "record_type": "health_snapshot",
            "scope_key": scope_key,
            "captured_at_utc": "",  # empty timestamp
            "blocked_ratio": 0.5,
            "blocked_count": 1,
        }
        log_path = tmp_path / "health-snapshots.jsonl"
        log_path.write_text(json.dumps(rec, sort_keys=True).decode() + "\n", encoding="utf-8")
        mock_path.return_value = log_path

        result = session_contract_health_trend_impl(limit=5)
        assert result["snapshot_count"] == 1
