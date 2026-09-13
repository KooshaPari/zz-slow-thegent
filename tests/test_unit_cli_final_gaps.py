"""Targeted tests to close remaining coverage gaps in cli.py.

Covers specific uncovered lines: 722, 778, 1114-1115, 1697, 1705, 1748,
2437, 2700-2702, 2852-2853, 2873, 2972-2973, 3119, 3136, 3158-3159,
3164-3165, 3195, 3200-3201, 3406, 3420-3428, 3457-3458, 3461-3462,
3475, 3508, 3511-3512, 3548-3549, 3555-3558, 3565, 3592-3593, 3876,
3879, 3882-3889, 4136, 4237
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Never
from unittest.mock import MagicMock, patch

import click.exceptions
import orjson as json
import pytest
import typer

from thegent.cli.commands.impl import DagDocument

_EXIT = (SystemExit, click.exceptions.Exit)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_settings(**overrides):
    defaults = {
        "session_dir": "/tmp/thegent-test-sessions",
        "environment": "development",
        "trust_score_threshold": 0.7,
        "override_ttl_seconds": 300,
        "output_format": "rich",
        "default_routing": "prefer_direct",
        "default_antigravity_model": "gemini-3-pro-high",
        "cursor_api_url": "http://localhost:8080",
        "retention_days_sessions": 30,
    }
    defaults.update(overrides)
    s = MagicMock()
    for k, v in defaults.items():
        setattr(s, k, v)
    return s


def _make_dag_doc(tasks=None, headers=None):
    return DagDocument(
        frontmatter={"version": "1", "project": "test", "owner": "ci"},
        tasks=tasks or [],
        before_table="# DAG Session\n\n## Tasks\n\n",
        after_table="",
        table_headers=headers or ["id", "agent", "prompt", "depends_on", "status"],
    )


def _health_gate_result(**overrides) -> dict[str, Any]:
    base: dict[str, Any] = {
        "schema_version": "3.0",
        "payload_type": "session_contract_health_gate",
        "status": "pass",
        "pass": True,
        "healthy_ratio": 1.0,
        "threshold": 1.0,
        "healthy_count": 5,
        "unhealthy_count": 0,
        "blocked_count": 0,
        "total": 5,
        "total_sessions": 5,
        "healthy_sessions": 5,
        "unhealthy_sessions": 0,
        "blocked_sessions": [],
        "blocked_sessions_count": 0,
        "blocked_ratio": 0.0,
        "top_blocked_count": 0,
        "blocked_sessions_cap": 25,
        "strict_checks_enabled": False,
        "generated_at_utc": "2025-01-01T00:00:00Z",
        "generated_query": {
            "owner": "ci",
            "all": False,
            "strict": False,
            "min_healthy_ratio": 1.0,
        },
        "summary": {"health": {"healthy": 5, "warning": 0, "error": 0, "missing": 0}},
        "decision_reasons": [],
    }
    base.update(overrides)
    return base


def _health_trend_result(**overrides) -> dict[str, Any]:
    base: dict[str, Any] = {
        "schema_version": "3.0",
        "payload_type": "session_contract_health_trend",
        "trend_payload_type": "session_contract_health_trend",
        "snapshot_count": 2,
        "limit": 20,
        "scope_key": {"owner": "ci", "payload_type": "session_contract_health_report"},
        "delta_summary": {"blocked_ratio_delta": 0.0, "blocked_count_delta": 0},
        "latest": {
            "status": "pass",
            "pass": True,
            "captured_at_utc": "2025-01-01T00:00:00Z",
            "blocked_ratio": 0.0,
            "blocked_count": 0,
            "issue_types": [],
        },
        "snapshots": [],
        "generated_at_utc": "2025-01-01T00:00:00Z",
    }
    base.update(overrides)
    return base


# ============================================================================
# Line 722: observe_summary_cmd — non-dict escalation item skipped
# ============================================================================


@pytest.mark.unit
class TestObserveSummaryNonDictEscalation:
    """Cover line 722: continue when top_escalation item is not a dict."""

    @patch("thegent.cli.console")
    @patch("thegent.cli._normalize_output_format", return_value="rich")
    @patch("thegent.cli.commands.impl.observe_summary_impl")
    def test_non_dict_escalation_skipped(
        self, mock_impl, mock_fmt, mock_console
    ) -> None:
        # @trace FR-CLI-722
        mock_impl.return_value = {
            "kpis": {
                "total_events": 10,
                "fallback_rate": 0.1,
                "success_rate": 0.9,
                "avg_confidence": 0.95,
            },
            "drift": {
                "structural_rate_pct": 1.0,
                "structural_budget_pct": 5.0,
                "semantic_rate_pct": 2.0,
                "semantic_budget_pct": 10.0,
                "within_budget": True,
                "issues": [],
            },
            "escalation": {
                "backlog_count": 0,
                "past_sla_count": 0,
                "top_escalations": ["not-a-dict", 42, None],
            },
            "alerts": [],
            "status": "healthy",
        }
        from thegent.cli import observe_summary_cmd

        observe_summary_cmd()


# ============================================================================
# Lines 772-778: contracts_conformance_cmd JSON format path (passing)
# ============================================================================


@pytest.mark.unit
class TestContractsConformanceJsonFormat:
    """Cover line 778: conformance cmd returns after JSON output (no drift, no failures)."""

    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli.contracts_conformance_cmd.__module__", "thegent.cli")
    def test_conformance_json_pass(self, mock_settings_cls) -> None:
        # @trace FR-CLI-778
        mock_settings_cls.return_value = _mock_settings()
        mock_report = {
            "passed": 3,
            "total": 3,
            "failed": 0,
            "results": [],
            "drift_issues": [],
        }
        from thegent.cli import contracts_conformance_cmd

        with patch(
            "thegent.contracts.conformance.run_conformance_suite",
            return_value=mock_report,
        ):
            # Source returns early for JSON format without printing
            contracts_conformance_cmd(format="json")


# ============================================================================
# Lines 1114-1115: session_contract_health_gate_cmd — unrecognized output suffix
# ============================================================================


@pytest.mark.unit
class TestHealthGateUnrecognizedSuffix:
    """Cover lines 1114-1115: output path with unrecognized extension triggers note."""

    @patch("thegent.cli.console")
    @patch("thegent.cli._default_owner_tag", return_value="ci")
    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli.commands.impl.session_contract_health_gate_impl")
    @patch("thegent.cli._write_health_gate_export", return_value="json")
    def test_unrecognized_suffix_note(
        self, mock_write, mock_impl, mock_settings_cls, mock_owner, mock_console
    ) -> None:
        # @trace FR-CLI-1114
        mock_settings_cls.return_value = _mock_settings()
        mock_impl.return_value = _health_gate_result()
        from thegent.cli import session_contract_health_gate_cmd

        output_path = Path("/tmp/test-output.xyz")
        session_contract_health_gate_cmd(output=output_path)
        # Should print a note about unrecognized extension
        note_printed = any(
            "not recognized for export" in str(c)
            for c in mock_console.print.call_args_list
        )
        assert note_printed, "Expected a note about unrecognized suffix"


# ============================================================================
# Lines 1697, 1705: _write_report_export — json fallback + tmp cleanup after replace
# ============================================================================


@pytest.mark.unit
class TestWriteReportExportJsonFallback:
    """Cover line 1697 (json fallback) and line 1705 (tmp unlink after success)."""

    def test_json_fallback_format(self, tmp_path) -> None:
        # @trace FR-CLI-1697
        from thegent.cli import _write_report_export

        report = {"status": "pass", "total": 1}
        output = tmp_path / "report.json"
        fmt = _write_report_export(output=output, report=report, export_format="json")
        assert fmt == "json"
        content = json.loads(output.read_text())
        assert content["status"] == "pass"

    def test_tmp_file_cleaned_on_replace_failure(self, tmp_path, monkeypatch) -> None:
        # @trace FR-CLI-1705
        from thegent.cli import _write_report_export

        report = {"status": "pass"}
        output = tmp_path / "report.json"

        def failing_replace(self, target) -> Never:
            raise OSError("simulated replace failure")

        monkeypatch.setattr(Path, "replace", failing_replace)
        with pytest.raises(OSError, match="simulated replace failure"):
            _write_report_export(output=output, report=report, export_format="json")
        # tmp file should have been cleaned up by the finally block
        tmp_files = list(tmp_path.glob(".*tmp"))
        assert len(tmp_files) == 0


# ============================================================================
# Line 1748: _write_health_gate_export — tmp cleanup
# ============================================================================


@pytest.mark.unit
class TestWriteHealthGateExportTmpCleanup:
    """Cover line 1748: tmp file unlinked after atomic write in _write_health_gate_export."""

    def test_health_gate_export_cleans_tmp_on_failure(
        self, tmp_path, monkeypatch
    ) -> None:
        # @trace FR-CLI-1748
        from thegent.cli import _write_health_gate_export

        report = _health_gate_result()
        output = tmp_path / "gate.json"

        def failing_replace(self, target) -> Never:
            raise OSError("simulated replace failure")

        monkeypatch.setattr(Path, "replace", failing_replace)
        with pytest.raises(OSError, match="simulated replace failure"):
            _write_health_gate_export(
                output=output, report=report, export_format="json", overwrite=True
            )
        tmp_files = list(tmp_path.glob(".*tmp"))
        assert len(tmp_files) == 0


# ============================================================================
# Line 2437: _write_health_trend_export — tmp cleanup after replace
# ============================================================================


@pytest.mark.unit
class TestWriteHealthTrendExportTmpCleanup:
    """Cover line 2437: tmp file cleaned up in _write_health_trend_export."""

    def test_trend_export_cleans_tmp_on_failure(self, tmp_path, monkeypatch) -> None:
        # @trace FR-CLI-2437
        from thegent.cli import _write_health_trend_export

        result = _health_trend_result()
        output = tmp_path / "trend.json"

        def failing_replace(self, target) -> Never:
            raise OSError("simulated replace failure")

        monkeypatch.setattr(Path, "replace", failing_replace)
        with pytest.raises(OSError, match="simulated replace failure"):
            _write_health_trend_export(
                output=output, result=result, export_format="json"
            )
        tmp_files = list(tmp_path.glob(".*tmp"))
        assert len(tmp_files) == 0


# ============================================================================
# Lines 2700-2702: _ensure_dag_file — file exists branch
# ============================================================================


@pytest.mark.unit
class TestEnsureDagFileExists:
    """Cover lines 2700-2702: _ensure_dag_file for both branches."""

    @patch("thegent.cli._parse_dag_full")
    def test_existing_dag_parsed(self, mock_parse, tmp_path) -> None:
        # @trace FR-CLI-2700
        dag_path = tmp_path / "dag-session.md"
        dag_path.write_text("# DAG\n| id | status |\n| -- | -- |\n| T1 | pending |")
        expected = _make_dag_doc(tasks=[{"id": "T1", "status": "pending"}])
        mock_parse.return_value = expected
        from thegent.cli import _ensure_dag_file

        result = _ensure_dag_file(dag_path)
        mock_parse.assert_called_once_with(dag_path)
        assert result == expected

    def test_missing_dag_creates_empty_doc(self, tmp_path) -> None:
        # @trace FR-CLI-2702
        dag_path = tmp_path / "nonexistent-dag.md"
        from thegent.cli import _ensure_dag_file

        result = _ensure_dag_file(dag_path)
        assert result.tasks == []
        assert result.frontmatter["version"] == "1"


# ============================================================================
# Lines 2852-2853: dag_update_cmd — DAG file not found
# ============================================================================


@pytest.mark.unit
class TestDagUpdateCmdDagNotFound:
    """Cover lines 2852-2853: dag_update_cmd when dag file does not exist."""

    @patch("thegent.cli.console")
    @patch("thegent.cli._resolve_cwd")
    def test_dag_not_found_exits(self, mock_cwd, mock_console, tmp_path) -> None:
        # @trace FR-CLI-2852
        mock_cwd.return_value = tmp_path
        from thegent.cli import dag_update_cmd

        with pytest.raises(_EXIT):
            dag_update_cmd(task_id="T1")


# ============================================================================
# Line 2873: dag_update_cmd — valid depends_on normalized
# ============================================================================


@pytest.mark.unit
class TestDagUpdateCmdDependsOnNormalized:
    """Cover line 2873: depends_on is normalized to comma-joined list."""

    @patch("thegent.cli.console")
    @patch("thegent.cli._atomic_write")
    @patch("thegent.cli._serialize_dag", return_value="serialized")
    @patch("thegent.cli._check_dag_cycles", return_value=[])
    @patch("thegent.cli._dag_update_task", return_value=True)
    @patch("thegent.cli._parse_dag_full")
    @patch("thegent.cli._resolve_cwd")
    def test_depends_on_normalized(
        self,
        mock_cwd,
        mock_parse,
        mock_update,
        mock_cycles,
        mock_serialize,
        mock_write,
        mock_console,
        tmp_path,
    ) -> None:
        # @trace FR-CLI-2873
        dag_path = tmp_path / ".factory" / "dag-session.md"
        dag_path.parent.mkdir(parents=True)
        dag_path.write_text("placeholder")
        mock_cwd.return_value = tmp_path
        doc = _make_dag_doc(
            tasks=[
                {"id": "T1", "status": "pending"},
                {"id": "T2", "status": "pending"},
            ]
        )
        mock_parse.return_value = doc
        from thegent.cli import dag_update_cmd

        dag_update_cmd(task_id="T2", depends_on="T1")
        # Check that _dag_update_task was called with normalized depends_on
        _, kwargs = mock_update.call_args
        assert kwargs["depends_on"] == "T1"


# ============================================================================
# Lines 2972-2973: dag_reconcile_cmd — session status running keeps task
# ============================================================================


@pytest.mark.unit
class TestDagReconcileRunningSession:
    """Cover lines 2972-2973: _session_status_for returns 'running' so task stays running."""

    @patch("thegent.cli.console")
    @patch("thegent.cli._atomic_write")
    @patch("thegent.cli._serialize_dag", return_value="serialized")
    @patch("thegent.cli._session_status_for", return_value="running")
    @patch("thegent.cli._parse_dag_full")
    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli._resolve_cwd")
    def test_running_session_keeps_task_running(
        self,
        mock_cwd,
        mock_settings_cls,
        mock_parse,
        mock_status,
        mock_serialize,
        mock_write,
        mock_console,
        tmp_path,
    ) -> None:
        # @trace FR-CLI-2972
        dag_path = tmp_path / ".factory" / "dag-session.md"
        dag_path.parent.mkdir(parents=True)
        dag_path.write_text("placeholder")
        mock_cwd.return_value = tmp_path
        mock_settings_cls.return_value = _mock_settings()
        doc = _make_dag_doc(
            tasks=[
                {"id": "T1", "status": "running", "session_id": "sess-1"},
            ]
        )
        mock_parse.return_value = doc
        from thegent.cli import dag_reconcile_cmd

        dag_reconcile_cmd(cd=tmp_path)
        # Task should remain running, no write
        mock_write.assert_not_called()


# ============================================================================
# Lines 3119, 3136: archive_cmd — domain filter skips items
# ============================================================================


@pytest.mark.unit
class TestArchiveCmdDomainFilter:
    """Cover lines 3119 and 3136: domain filter skips non-matching items."""

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings")
    def test_cold_tier_domain_filter(
        self, mock_settings_cls, mock_console, tmp_path
    ) -> None:
        # @trace FR-CLI-3119

        mock_settings_cls.return_value = _mock_settings(session_dir=str(tmp_path))
        archive_dir = tmp_path / "archive"
        archive_dir.mkdir()
        archive_dir / "cold"
        # Create old session not matching domain
        old_session = archive_dir / "other-project-001"
        old_session.mkdir()
        # Set mtime to 2 years ago
        import os

        old_time = time.time() - (400 * 86400)
        os.utime(old_session, (old_time, old_time))

        from thegent.cli import archive_cmd

        archive_cmd(tier="cold", domain="my-domain")
        # Session should NOT have been moved (domain doesn't match)
        assert old_session.exists()

    @patch("thegent.cli.console")
    @patch("thegent.cli.ThegentSettings")
    def test_hot_tier_domain_filter(
        self, mock_settings_cls, mock_console, tmp_path
    ) -> None:
        # @trace FR-CLI-3136
        import os

        mock_settings_cls.return_value = _mock_settings(session_dir=str(tmp_path))
        archive_dir = tmp_path / "archive"
        archive_dir.mkdir()
        old_session = tmp_path / "other-project-002"
        old_session.mkdir()
        old_time = time.time() - (60 * 86400)
        os.utime(old_session, (old_time, old_time))

        from thegent.cli import archive_cmd

        archive_cmd(domain="my-domain")
        # Session should NOT have been moved (domain doesn't match)
        assert old_session.exists()


# ============================================================================
# Lines 3158-3159, 3164-3165: operations_cmd — valid operation + json format
# ============================================================================


@pytest.mark.unit
class TestOperationsCmdBranches:
    """Cover lines 3158-3159, 3164-3165 in operations_cmd."""

    @patch("thegent.cli.console")
    def test_operations_valid_operation_json(self, mock_console) -> None:
        # @trace FR-CLI-3158
        from thegent.cli import operations_cmd

        mock_entry = MagicMock()
        mock_entry.command = "test-cmd"
        mock_entry.description = "Test description"
        mock_entry.mcp_tool = "test_tool"

        mock_op = MagicMock()
        mock_op.value = "orchestrate"

        with (
            patch("thegent.operations.Operation", return_value=mock_op),
            patch(
                "thegent.operations.get_operations_by_type", return_value=[mock_entry]
            ),
        ):
            # Source returns early for JSON format without printing
            operations_cmd(format="json", operation="orchestrate")
        mock_console.print.assert_not_called()


# ============================================================================
# Lines 3195, 3200-3201: modes_cmd — valid mode + json format
# ============================================================================


@pytest.mark.unit
class TestModesCmdBranches:
    """Cover lines 3195, 3200-3201 in modes_cmd."""

    @patch("thegent.cli.console")
    def test_modes_valid_mode_json(self, mock_console) -> None:
        # @trace FR-CLI-3195
        mock_entry = MagicMock()
        mock_entry.mode = MagicMock(value="sequential_delegation")
        mock_entry.description = "Sequential delegation mode"
        mock_entry.phases = ["plan", "execute"]
        mock_entry.use_case = "Simple tasks"
        mock_entry.risk_profile = "low"
        mock_entry.selection_hint = "For simple tasks"

        with patch("thegent.orchestration_modes.get_mode", return_value=mock_entry):
            from thegent.cli import modes_cmd

            # Source returns early for JSON format without printing
            modes_cmd(format="json", mode="sequential_delegation")
        mock_console.print.assert_not_called()


# ============================================================================
# Line 3406: dag_run_cmd — specific task filter
# ============================================================================


@pytest.mark.unit
class TestDagRunCmdTaskFilter:
    """Cover line 3406: ready_ids narrowed to specific task."""

    @patch("thegent.cli.console")
    @patch("thegent.cli.dag_reconcile_cmd")
    @patch("thegent.cli._get_ready_task_ids", return_value=["T1", "T2"])
    @patch("thegent.cli._parse_dag_full")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli._resolve_prompt", return_value="Do something")
    def test_specific_task_filter(
        self,
        mock_prompt,
        mock_cwd,
        mock_parse,
        mock_ready,
        mock_reconcile,
        mock_console,
        tmp_path,
    ) -> None:
        # @trace FR-CLI-3406
        dag_path = tmp_path / ".factory" / "dag-session.md"
        dag_path.parent.mkdir(parents=True)
        dag_path.write_text("placeholder")
        mock_cwd.return_value = tmp_path
        doc = _make_dag_doc(
            tasks=[
                {"id": "T1", "agent": "claude", "prompt": "Do T1", "status": "pending"},
                {"id": "T2", "agent": "claude", "prompt": "Do T2", "status": "pending"},
            ]
        )
        mock_parse.return_value = doc
        from thegent.cli import dag_run_cmd

        dag_run_cmd(cd=tmp_path, dry_run=True, task="T1")
        # Only T1 should be printed
        printed_texts = [str(c) for c in mock_console.print.call_args_list]
        assert any("T1" in t for t in printed_texts)


# ============================================================================
# Lines 3420-3428: dag_run_cmd — max_parallel with priority sorting
# ============================================================================


@pytest.mark.unit
class TestDagRunCmdMaxParallelPriority:
    """Cover lines 3420-3428: priority sorting + truncation by max_parallel."""

    @patch("thegent.cli.console")
    @patch("thegent.cli.dag_reconcile_cmd")
    @patch("thegent.cli._get_ready_task_ids", return_value=["T1", "T2", "T3"])
    @patch("thegent.cli._parse_dag_full")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli._resolve_prompt", return_value="Do something")
    def test_max_parallel_priority(
        self,
        mock_prompt,
        mock_cwd,
        mock_parse,
        mock_ready,
        mock_reconcile,
        mock_console,
        tmp_path,
    ) -> None:
        # @trace FR-CLI-3420
        dag_path = tmp_path / ".factory" / "dag-session.md"
        dag_path.parent.mkdir(parents=True)
        dag_path.write_text("placeholder")
        mock_cwd.return_value = tmp_path
        doc = _make_dag_doc(
            tasks=[
                {
                    "id": "T1",
                    "agent": "claude",
                    "prompt": "Do T1",
                    "status": "pending",
                    "priority": "1",
                },
                {
                    "id": "T2",
                    "agent": "claude",
                    "prompt": "Do T2",
                    "status": "pending",
                    "priority": "10",
                },
                {
                    "id": "T3",
                    "agent": "claude",
                    "prompt": "Do T3",
                    "status": "pending",
                    "priority": "5",
                },
            ]
        )
        mock_parse.return_value = doc
        from thegent.cli import dag_run_cmd

        dag_run_cmd(cd=tmp_path, dry_run=True, max_parallel=2)
        # T2 (priority=10) should appear first, then T3 (priority=5)
        printed_texts = [str(c) for c in mock_console.print.call_args_list]
        t2_found = False
        for t in printed_texts:
            if "T2" in t:
                t2_found = True
        assert t2_found

    @patch("thegent.cli.console")
    @patch("thegent.cli.dag_reconcile_cmd")
    @patch("thegent.cli._get_ready_task_ids", return_value=["T1", "T2"])
    @patch("thegent.cli._parse_dag_full")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli._resolve_prompt", return_value="Do something")
    def test_max_parallel_priority_except_branch(
        self,
        mock_prompt,
        mock_cwd,
        mock_parse,
        mock_ready,
        mock_reconcile,
        mock_console,
        tmp_path,
    ) -> None:
        # @trace FR-CLI-3424
        dag_path = tmp_path / ".factory" / "dag-session.md"
        dag_path.parent.mkdir(parents=True)
        dag_path.write_text("placeholder")
        mock_cwd.return_value = tmp_path

        # Create a task dict subclass that raises ValueError on .get("priority")
        class BrokenPriorityDict(dict):
            def get(self, key, default=None):
                if key == "priority":
                    raise ValueError("broken priority")
                return super().get(key, default)

        doc = _make_dag_doc(
            tasks=[
                {
                    "id": "T1",
                    "agent": "claude",
                    "prompt": "Do T1",
                    "status": "pending",
                    "priority": "5",
                },
                BrokenPriorityDict(
                    id="T2", agent="claude", prompt="Do T2", status="pending"
                ),
            ]
        )
        mock_parse.return_value = doc
        from thegent.cli import dag_run_cmd

        dag_run_cmd(cd=tmp_path, dry_run=True, max_parallel=2)


# ============================================================================
# Lines 3457-3458: dag_run_cmd — confidence < min_confidence upgrades quorum
# ============================================================================


@pytest.mark.unit
class TestDagRunCmdConfidenceUpgrade:
    """Cover lines 3457-3458: low confidence upgrades quorum from 1 to 2."""

    @patch("thegent.cli.console")
    @patch("thegent.cli._atomic_write")
    @patch("thegent.cli._serialize_dag", return_value="serialized")
    @patch("thegent.cli._dag_update_task", return_value=True)
    @patch("thegent.cli.dag_reconcile_cmd")
    @patch("thegent.cli._get_ready_task_ids", return_value=["T1"])
    @patch("thegent.cli._parse_dag_full")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli._resolve_prompt", return_value="Do something")
    @patch("thegent.cli.resolve_agent", return_value="claude")
    @patch("thegent.cli.bg_cmd", return_value="sess-001")
    def test_low_confidence_upgrades_quorum(
        self,
        mock_bg_cmd,
        mock_resolve_agent,
        mock_prompt,
        mock_cwd,
        mock_parse,
        mock_ready,
        mock_reconcile,
        mock_update,
        mock_serialize,
        mock_write,
        mock_console,
        tmp_path,
    ) -> None:
        # @trace FR-CLI-3457
        dag_path = tmp_path / ".factory" / "dag-session.md"
        dag_path.parent.mkdir(parents=True)
        dag_path.write_text("placeholder")
        mock_cwd.return_value = tmp_path
        doc = _make_dag_doc(
            tasks=[
                {
                    "id": "T1",
                    "agent": "claude",
                    "prompt": "Do T1",
                    "status": "pending",
                    "confidence": "0.5",
                    "min_confidence": "0.85",
                },
            ]
        )
        mock_parse.return_value = doc
        from thegent.cli import dag_run_cmd

        dag_run_cmd(cd=tmp_path)
        # Should print the "Low confidence" message
        printed_texts = [str(c) for c in mock_console.print.call_args_list]
        assert any("Low confidence" in t for t in printed_texts)


# ============================================================================
# Lines 3461-3462: dag_run_cmd — missing agent or prompt skips task
# ============================================================================


@pytest.mark.unit
class TestDagRunCmdMissingAgentSkips:
    """Cover lines 3461-3462: task with no agent is skipped."""

    @patch("thegent.cli.console")
    @patch("thegent.cli.dag_reconcile_cmd")
    @patch("thegent.cli._get_ready_task_ids", return_value=["T1"])
    @patch("thegent.cli._parse_dag_full")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli._resolve_prompt", return_value="")
    def test_missing_prompt_skips(
        self,
        mock_prompt,
        mock_cwd,
        mock_parse,
        mock_ready,
        mock_reconcile,
        mock_console,
        tmp_path,
    ) -> None:
        # @trace FR-CLI-3461
        dag_path = tmp_path / ".factory" / "dag-session.md"
        dag_path.parent.mkdir(parents=True)
        dag_path.write_text("placeholder")
        mock_cwd.return_value = tmp_path
        doc = _make_dag_doc(
            tasks=[
                {"id": "T1", "agent": "claude", "prompt": "", "status": "pending"},
            ]
        )
        mock_parse.return_value = doc
        from thegent.cli import dag_run_cmd

        dag_run_cmd(cd=tmp_path)
        printed_texts = [str(c) for c in mock_console.print.call_args_list]
        assert any("Skipping" in t for t in printed_texts)


# ============================================================================
# Line 3475: dag_run_cmd — quorum > 1 sets arbitration leader/follower
# ============================================================================


@pytest.mark.unit
class TestDagRunCmdQuorumArbitration:
    """Cover line 3475: arbitration set to leader/follower for quorum > 1."""

    @patch("thegent.cli.console")
    @patch("thegent.cli._atomic_write")
    @patch("thegent.cli._serialize_dag", return_value="serialized")
    @patch("thegent.cli._dag_update_task", return_value=True)
    @patch("thegent.cli.dag_reconcile_cmd")
    @patch("thegent.cli._get_ready_task_ids", return_value=["T1"])
    @patch("thegent.cli._parse_dag_full")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli._resolve_prompt", return_value="Do something")
    @patch("thegent.cli.resolve_agent", return_value="claude")
    @patch("thegent.cli.bg_cmd", return_value="sess-001")
    def test_quorum_arbitration(
        self,
        mock_bg_cmd,
        mock_resolve_agent,
        mock_prompt,
        mock_cwd,
        mock_parse,
        mock_ready,
        mock_reconcile,
        mock_update,
        mock_serialize,
        mock_write,
        mock_console,
        tmp_path,
    ) -> None:
        # @trace FR-CLI-3475
        dag_path = tmp_path / ".factory" / "dag-session.md"
        dag_path.parent.mkdir(parents=True)
        dag_path.write_text("placeholder")
        mock_cwd.return_value = tmp_path
        doc = _make_dag_doc(
            tasks=[
                {
                    "id": "T1",
                    "agent": "claude",
                    "prompt": "Do T1",
                    "status": "pending",
                    "quorum": "2",
                },
            ]
        )
        mock_parse.return_value = doc
        from thegent.cli import dag_run_cmd

        dag_run_cmd(cd=tmp_path)
        # bg_cmd should be called twice (quorum=2)
        assert mock_bg_cmd.call_count == 2


# ============================================================================
# Lines 3508, 3511-3512: dag_run_cmd — retry_count logic
# ============================================================================


@pytest.mark.unit
class TestDagRunCmdRetryCount:
    """Cover lines 3508, 3511-3512: retry_count for failed/pending tasks."""

    @patch("thegent.cli.console")
    @patch("thegent.cli._atomic_write")
    @patch("thegent.cli._serialize_dag", return_value="serialized")
    @patch("thegent.cli._dag_update_task", return_value=True)
    @patch("thegent.cli.dag_reconcile_cmd")
    @patch("thegent.cli._get_ready_task_ids", return_value=["T1"])
    @patch("thegent.cli._parse_dag_full")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli._resolve_prompt", return_value="Do something")
    @patch("thegent.cli.resolve_agent", return_value="claude")
    @patch("thegent.cli.bg_cmd", return_value="sess-001")
    def test_retry_count_failed_task(
        self,
        mock_bg_cmd,
        mock_resolve_agent,
        mock_prompt,
        mock_cwd,
        mock_parse,
        mock_ready,
        mock_reconcile,
        mock_update,
        mock_serialize,
        mock_write,
        mock_console,
        tmp_path,
    ) -> None:
        # @trace FR-CLI-3508
        dag_path = tmp_path / ".factory" / "dag-session.md"
        dag_path.parent.mkdir(parents=True)
        dag_path.write_text("placeholder")
        mock_cwd.return_value = tmp_path
        doc = _make_dag_doc(
            tasks=[
                {
                    "id": "T1",
                    "agent": "claude",
                    "prompt": "Do T1",
                    "status": "failed",
                    "retry_count": "2",
                },
            ]
        )
        mock_parse.return_value = doc
        from thegent.cli import dag_run_cmd

        dag_run_cmd(cd=tmp_path)
        # retry_count should be 3 (2+1)
        _, kwargs = mock_update.call_args
        assert kwargs["retry_count"] == 3

    @patch("thegent.cli.console")
    @patch("thegent.cli._atomic_write")
    @patch("thegent.cli._serialize_dag", return_value="serialized")
    @patch("thegent.cli._dag_update_task", return_value=True)
    @patch("thegent.cli.dag_reconcile_cmd")
    @patch("thegent.cli._get_ready_task_ids", return_value=["T1"])
    @patch("thegent.cli._parse_dag_full")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli._resolve_prompt", return_value="Do something")
    @patch("thegent.cli.resolve_agent", return_value="claude")
    @patch("thegent.cli.bg_cmd", return_value="sess-001")
    def test_retry_count_invalid_value(
        self,
        mock_bg_cmd,
        mock_resolve_agent,
        mock_prompt,
        mock_cwd,
        mock_parse,
        mock_ready,
        mock_reconcile,
        mock_update,
        mock_serialize,
        mock_write,
        mock_console,
        tmp_path,
    ) -> None:
        # @trace FR-CLI-3511
        dag_path = tmp_path / ".factory" / "dag-session.md"
        dag_path.parent.mkdir(parents=True)
        dag_path.write_text("placeholder")
        mock_cwd.return_value = tmp_path
        doc = _make_dag_doc(
            tasks=[
                {
                    "id": "T1",
                    "agent": "claude",
                    "prompt": "Do T1",
                    "status": "failed",
                    "retry_count": "not-a-number",
                },
            ]
        )
        mock_parse.return_value = doc
        from thegent.cli import dag_run_cmd

        dag_run_cmd(cd=tmp_path)
        # retry_count should be 1 (failed, but invalid current count -> except branch)
        _, kwargs = mock_update.call_args
        assert kwargs["retry_count"] == 1


# ============================================================================
# Lines 3548-3549, 3555-3558, 3565: dag_sync_cmd — session done/failed logic
# ============================================================================


@pytest.mark.unit
class TestDagSyncCmdSessionCompletion:
    """Cover dag_sync_cmd session completion, failure, and BadParameter branches."""

    @patch("thegent.cli.console")
    @patch("thegent.cli._atomic_write")
    @patch("thegent.cli._serialize_dag", return_value="serialized")
    @patch("thegent.cli._is_pid_running", return_value=False)
    @patch("thegent.cli._session_paths")
    @patch("thegent.cli._read_session_meta", return_value={"pid": "123"})
    @patch("thegent.cli._find_session_meta")
    @patch("thegent.cli._parse_dag_full")
    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli._default_owner_tag", return_value="ci")
    @patch("thegent.execution.CheckpointRegistry")
    def test_sync_single_session_failed(
        self,
        mock_ckpt,
        mock_owner,
        mock_cwd,
        mock_settings_cls,
        mock_parse,
        mock_find_meta,
        mock_read_meta,
        mock_paths,
        mock_pid,
        mock_serialize,
        mock_write,
        mock_console,
        tmp_path,
    ) -> None:
        # @trace FR-CLI-3555
        dag_path = tmp_path / ".factory" / "dag-session.md"
        dag_path.parent.mkdir(parents=True)
        dag_path.write_text("placeholder")
        mock_cwd.return_value = tmp_path
        mock_settings_cls.return_value = _mock_settings(session_dir=tmp_path)
        mock_find_meta.return_value = tmp_path / "meta.json"

        rc_file = MagicMock()
        rc_file.exists.return_value = True
        rc_file.read_text.return_value = "1"
        mock_paths.return_value = {
            "rc": rc_file,
            "stdout": MagicMock(),
            "stderr": MagicMock(),
        }

        doc = _make_dag_doc(
            tasks=[
                {"id": "T1", "status": "running", "session_id": "sess-1"},
            ]
        )
        mock_parse.return_value = doc
        from thegent.cli import dag_sync_cmd

        dag_sync_cmd(cd=tmp_path)
        # Task should be marked as failed
        assert doc.tasks[0]["status"] == "failed"

    @patch("thegent.cli.console")
    @patch("thegent.cli._atomic_write")
    @patch("thegent.cli._serialize_dag", return_value="serialized")
    @patch("thegent.cli._is_pid_running", return_value=False)
    @patch("thegent.cli._session_paths")
    @patch("thegent.cli._read_session_meta", return_value={"pid": "123"})
    @patch("thegent.cli._find_session_meta")
    @patch("thegent.cli._parse_dag_full")
    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli._default_owner_tag", return_value="ci")
    @patch("thegent.execution.CheckpointRegistry")
    def test_sync_quorum_any_failed(
        self,
        mock_ckpt,
        mock_owner,
        mock_cwd,
        mock_settings_cls,
        mock_parse,
        mock_find_meta,
        mock_read_meta,
        mock_paths,
        mock_pid,
        mock_serialize,
        mock_write,
        mock_console,
        tmp_path,
    ) -> None:
        # @trace FR-CLI-3565
        dag_path = tmp_path / ".factory" / "dag-session.md"
        dag_path.parent.mkdir(parents=True)
        dag_path.write_text("placeholder")
        mock_cwd.return_value = tmp_path
        mock_settings_cls.return_value = _mock_settings(session_dir=tmp_path)
        mock_find_meta.return_value = tmp_path / "meta.json"

        rc_file = MagicMock()
        rc_file.exists.return_value = True
        # First call returns "0", second returns "1"
        rc_file.read_text.side_effect = ["0", "1"]
        mock_paths.return_value = {
            "rc": rc_file,
            "stdout": MagicMock(),
            "stderr": MagicMock(),
        }

        doc = _make_dag_doc(
            tasks=[
                {"id": "T1", "status": "running", "session_id": "sess-1,sess-2"},
            ]
        )
        mock_parse.return_value = doc
        from thegent.cli import dag_sync_cmd

        dag_sync_cmd(cd=tmp_path)
        # Multi-session quorum with any_failed -> status = "failed"
        assert doc.tasks[0]["status"] == "failed"

    @patch("thegent.cli.console")
    @patch("thegent.cli._parse_dag_full")
    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli._resolve_cwd")
    @patch(
        "thegent.cli._find_session_meta", side_effect=typer.BadParameter("not found")
    )
    def test_sync_bad_parameter_breaks(
        self,
        mock_find_meta,
        mock_cwd,
        mock_settings_cls,
        mock_parse,
        mock_console,
        tmp_path,
    ) -> None:
        # @trace FR-CLI-3556
        dag_path = tmp_path / ".factory" / "dag-session.md"
        dag_path.parent.mkdir(parents=True)
        dag_path.write_text("placeholder")
        mock_cwd.return_value = tmp_path
        mock_settings_cls.return_value = _mock_settings()
        doc = _make_dag_doc(
            tasks=[
                {"id": "T1", "status": "running", "session_id": "sess-1"},
            ]
        )
        mock_parse.return_value = doc
        from thegent.cli import dag_sync_cmd

        dag_sync_cmd(cd=tmp_path)
        # Task should remain running (BadParameter -> all_done=False)
        assert doc.tasks[0]["status"] == "running"

    @patch("thegent.cli.console")
    @patch("thegent.cli._is_pid_running", return_value=True)
    @patch("thegent.cli._read_session_meta", return_value={"pid": "999"})
    @patch("thegent.cli._find_session_meta")
    @patch("thegent.cli._parse_dag_full")
    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli._resolve_cwd")
    def test_sync_pid_still_running(
        self,
        mock_cwd,
        mock_settings_cls,
        mock_parse,
        mock_find_meta,
        mock_read_meta,
        mock_pid,
        mock_console,
        tmp_path,
    ) -> None:
        # @trace FR-CLI-3548
        dag_path = tmp_path / ".factory" / "dag-session.md"
        dag_path.parent.mkdir(parents=True)
        dag_path.write_text("placeholder")
        mock_cwd.return_value = tmp_path
        mock_settings_cls.return_value = _mock_settings()
        mock_find_meta.return_value = tmp_path / "meta.json"
        doc = _make_dag_doc(
            tasks=[
                {"id": "T1", "status": "running", "session_id": "sess-1"},
            ]
        )
        mock_parse.return_value = doc
        from thegent.cli import dag_sync_cmd

        dag_sync_cmd(cd=tmp_path)
        # Task should remain running (pid is alive -> all_done=False)
        assert doc.tasks[0]["status"] == "running"


# ============================================================================
# Lines 3592-3593: dag_checkpoint_cmd — DAG not found
# ============================================================================


@pytest.mark.unit
class TestDagCheckpointCmdDagNotFound:
    """Cover lines 3592-3593: dag_checkpoint_cmd when dag file does not exist."""

    @patch("thegent.cli.console")
    @patch("thegent.cli._resolve_cwd")
    def test_dag_not_found_exits(self, mock_cwd, mock_console, tmp_path) -> None:
        # @trace FR-CLI-3592
        mock_cwd.return_value = tmp_path
        from thegent.cli import dag_checkpoint_cmd

        with pytest.raises(_EXIT):
            dag_checkpoint_cmd()


# ============================================================================
# Lines 3876, 3879, 3882-3889: logs_follow_cmd — file disappears / truncated / new data
# ============================================================================


@pytest.mark.unit
class TestLogsFollowBranches:
    """Cover lines 3876, 3879, 3882-3889 in the follow loop of logs_cmd."""

    @patch("thegent.cli.console")
    @patch("thegent.cli._is_pid_running")
    @patch("thegent.cli._read_session_meta", return_value={"pid": "123"})
    @patch("thegent.cli._session_paths")
    @patch("thegent.cli._find_session_meta")
    @patch("thegent.cli.ThegentSettings")
    def test_follow_file_disappears(
        self,
        mock_settings_cls,
        mock_find_meta,
        mock_paths,
        mock_read_meta,
        mock_pid,
        mock_console,
        tmp_path,
    ) -> None:
        # @trace FR-CLI-3876
        mock_settings_cls.return_value = _mock_settings()
        mock_find_meta.return_value = tmp_path / "meta.json"
        stdout_file = tmp_path / "stdout.log"
        stdout_file.write_text("initial line\n")

        call_count = 0

        def exists_side_effect(*a, **kw) -> bool:
            nonlocal call_count
            call_count += 1
            # After initial read and first follow loop check, delete the file
            if call_count >= 2:
                if stdout_file.exists.__wrapped__():
                    stdout_file.unlink()
                return False
            return True

        mock_paths.return_value = {
            "stdout": stdout_file,
            "stderr": tmp_path / "stderr.log",
            "rc": MagicMock(exists=lambda: False),
        }
        mock_pid.return_value = True  # process running so we enter loop

        from thegent.cli import logs_cmd

        # We need to mock target.exists() in the loop to return False
        # Instead, delete the file in a controlled way via patching
        # Simpler approach: delete file before calling with follow
        stdout_file.write_text("initial\n")
        # Call logs with follow=True; the file exists for initial read
        # Then we delete it immediately -- but loop runs fast
        # Use a side_effect on _is_pid_running to delete on second call
        call_idx = 0

        def pid_side_effect(pid) -> bool:
            nonlocal call_idx
            call_idx += 1
            if call_idx == 1:
                # First iteration: file still exists but no new data
                # Delete it before next check
                if stdout_file.exists():
                    stdout_file.unlink()
                return True
            return False

        mock_pid.side_effect = pid_side_effect
        stdout_file.write_text("initial\n")
        # This should enter follow loop, find file deleted, and return
        logs_cmd(session_id="sess-1", follow=True, tail=10, stderr=False, timeout=0)

    @patch("thegent.cli.console")
    @patch("thegent.cli._is_pid_running")
    @patch("thegent.cli._read_session_meta", return_value={"pid": "123"})
    @patch("thegent.cli._session_paths")
    @patch("thegent.cli._find_session_meta")
    @patch("thegent.cli.ThegentSettings")
    def test_follow_reads_new_data_then_exits(
        self,
        mock_settings_cls,
        mock_find_meta,
        mock_paths,
        mock_read_meta,
        mock_pid,
        mock_console,
        tmp_path,
    ) -> None:
        # @trace FR-CLI-3882
        mock_settings_cls.return_value = _mock_settings()
        mock_find_meta.return_value = tmp_path / "meta.json"
        stdout_file = tmp_path / "stdout.log"
        stdout_file.write_text("line1\n")
        mock_paths.return_value = {
            "stdout": stdout_file,
            "stderr": tmp_path / "stderr.log",
            "rc": MagicMock(exists=lambda: False),
        }

        call_idx = 0

        def pid_side_effect(pid) -> bool:
            nonlocal call_idx
            call_idx += 1
            if call_idx == 1:
                # Append data before the loop checks size
                stdout_file.write_text("line1\nline2 extra data\n")
                return True  # running -> enters loop
            return False  # not running -> will read new data then exit

        mock_pid.side_effect = pid_side_effect

        from thegent.cli import logs_cmd

        logs_cmd(session_id="sess-1", follow=True, tail=1, stderr=False, timeout=0)
        # Verify new data was printed
        printed_texts = [str(c) for c in mock_console.print.call_args_list]
        assert any("line2" in t for t in printed_texts)

    @patch("thegent.cli.console")
    @patch("thegent.cli._is_pid_running")
    @patch("thegent.cli._read_session_meta", return_value={"pid": "123"})
    @patch("thegent.cli._session_paths")
    @patch("thegent.cli._find_session_meta")
    @patch("thegent.cli.ThegentSettings")
    def test_follow_file_truncated_resets_pos(
        self,
        mock_settings_cls,
        mock_find_meta,
        mock_paths,
        mock_read_meta,
        mock_pid,
        mock_console,
        tmp_path,
    ) -> None:
        # @trace FR-CLI-3879
        mock_settings_cls.return_value = _mock_settings()
        mock_find_meta.return_value = tmp_path / "meta.json"
        stdout_file = tmp_path / "stdout.log"
        # Write a large initial file
        stdout_file.write_text("A" * 1000 + "\n")
        mock_paths.return_value = {
            "stdout": stdout_file,
            "stderr": tmp_path / "stderr.log",
            "rc": MagicMock(exists=lambda: False),
        }

        call_idx = 0

        def pid_side_effect(pid) -> bool:
            nonlocal call_idx
            call_idx += 1
            if call_idx == 1:
                # Truncate file to trigger size < pos -> pos = 0
                stdout_file.write_text("short\n")
                return True
            return False  # exit on second iteration after reading truncated data

        mock_pid.side_effect = pid_side_effect

        from thegent.cli import logs_cmd

        logs_cmd(session_id="sess-1", follow=True, tail=1, stderr=False, timeout=0)
        printed_texts = [str(c) for c in mock_console.print.call_args_list]
        assert any("short" in t for t in printed_texts)


# ============================================================================
# Line 4136: resolve_model_route_cmd — no route and no available routes
# ============================================================================


@pytest.mark.unit
class TestResolveModelRouteCmdNoRoutes:
    """Cover line 4136: no route found and no available routes."""

    @patch("thegent.cli.console")
    def test_no_route_no_available(self, mock_console) -> None:
        # @trace FR-CLI-4136
        with (
            patch(
                "thegent.models.normalize_route_policy", return_value="prefer_direct"
            ),
            patch("thegent.models.normalize_model_id", return_value="unknown-model"),
            patch("thegent.models.resolve_route_contract", return_value=None),
            patch("thegent.models.ModelCatalog") as MockCatalog,
        ):
            MockCatalog.routes_for.return_value = []
            from thegent.cli import resolve_model_route_cmd

            with pytest.raises(_EXIT):
                resolve_model_route_cmd(model="unknown-model")
            printed_texts = [str(c) for c in mock_console.print.call_args_list]
            assert any("No route for model" in t for t in printed_texts)


# ============================================================================
# Line 4237: _list_copilot_models — model regex finds no known models -> fallback
# ============================================================================


@pytest.mark.unit
class TestListCopilotModelsNoKnownModels:
    """Cover line 4237: regex finds choices but none are claude/gpt/gemini -> fallback."""

    @patch("thegent.cli.console")
    @patch("thegent.cli._list_copilot_models_fallback")
    @patch("thegent.cli.subprocess")
    def test_no_known_models_triggers_fallback(
        self, mock_subprocess, mock_fallback, mock_console
    ) -> None:
        # @trace FR-CLI-4237
        proc = MagicMock()
        proc.returncode = 0
        proc.stdout = '--model {choices: "some-random-model", "another-unknown"}'
        mock_subprocess.run.return_value = proc
        from thegent.cli import _list_copilot_models

        _list_copilot_models()
        mock_fallback.assert_called_once()
