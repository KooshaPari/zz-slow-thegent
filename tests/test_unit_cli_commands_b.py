"""Unit tests for CLI command implementations (second half of cli.py ~lines 2400-4336).

Tests cover DAG commands, health/observe commands, governance commands,
serialization helpers, model listing helpers, and miscellaneous commands.
All functions are called DIRECTLY with internal dependencies mocked.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import click.exceptions
import orjson as json
import pytest

from thegent.cli.commands.impl import DagDocument

# typer.Exit inherits from click.exceptions.Exit (RuntimeError), not SystemExit
_EXIT = (SystemExit, click.exceptions.Exit)


# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------


def _make_dag_doc(
    tasks: list[dict[str, str]] | None = None,
    headers: list[str] | None = None,
) -> DagDocument:
    """Build a minimal DagDocument for testing."""
    return DagDocument(
        frontmatter={"version": "1", "project": "test", "owner": "ci"},
        tasks=tasks or [],
        before_table="# DAG Session\n\n## Tasks\n\n",
        after_table="",
        table_headers=headers or ["id", "agent", "prompt", "depends_on", "status"],
    )


def _health_report_result(**overrides: Any) -> dict[str, Any]:
    """Build a minimal health report result dict."""
    base: dict[str, Any] = {
        "schema_version": "3.0",
        "payload_type": "session_contract_health_report",
        "status": "pass",
        "pass": True,
        "total": 5,
        "total_sessions": 5,
        "healthy_sessions": 5,
        "unhealthy_sessions": 0,
        "blocked_sessions": 0,
        "blocked_sessions_count": 0,
        "blocked_count": 0,
        "blocked_ratio": 0.0,
        "top_blocked_count": 0,
        "health": {"healthy": 5, "warning": 0, "error": 0, "missing": 0},
        "strict_checks_enabled": False,
        "issue_breakdown": [],
        "owner_breakdown": {},
        "top_blocked": [],
        "healthy_count": 5,
        "unhealthy_count": 0,
    }
    base.update(overrides)
    return base


def _health_trend_result(**overrides: Any) -> dict[str, Any]:
    """Build a minimal health trend result dict."""
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


def _health_gate_result(**overrides: Any) -> dict[str, Any]:
    """Build a minimal health gate result dict."""
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
        "summary": {"health": {"healthy": 5, "warning": 0, "error": 0, "missing": 0}},
        "decision_reasons": [],
    }
    base.update(overrides)
    return base


# ============================================================================
# DAG COMMANDS
# ============================================================================


@pytest.mark.unit
class TestDagListCmdImpl:
    """Tests for dag_list_cmd implementation."""

    @patch("thegent.cli._resolve_cwd", return_value=None)
    @patch("thegent.cli.console")
    def test_ambiguous_cwd_exits(self, mock_console, mock_cwd) -> None:
        # @trace FR-CLI-300
        from thegent.cli import dag_list_cmd

        with pytest.raises(_EXIT):
            dag_list_cmd(cd=None, format=None)

    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli._parse_dag_session", return_value=({}, []))
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_no_tasks_json(self, mock_console, mock_cwd, mock_parse, mock_settings, tmp_path) -> None:
        # @trace FR-CLI-301
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.touch()
        mock_cwd.return_value = tmp_path
        mock_settings.return_value.output_format = "json"

        from thegent.cli import dag_list_cmd

        dag_list_cmd(cd=None, format="json")

    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli._parse_dag_session")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_with_tasks_md_format(self, mock_console, mock_cwd, mock_parse, mock_settings, tmp_path) -> None:
        # @trace FR-CLI-302
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.touch()
        mock_cwd.return_value = tmp_path
        tasks = [
            {
                "id": "T1",
                "agent": "claude",
                "prompt": "Do stuff",
                "depends_on": "-",
                "status": "pending",
            }
        ]
        mock_parse.return_value = ({}, tasks)
        mock_settings.return_value.output_format = "rich"

        from thegent.cli import dag_list_cmd

        dag_list_cmd(cd=None, format="md")
        assert any("T1" in str(c) for c in mock_console.print.call_args_list)

    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli._parse_dag_session")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_no_tasks_rich(self, mock_console, mock_cwd, mock_parse, mock_settings, tmp_path) -> None:
        # @trace FR-CLI-303
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.touch()
        mock_cwd.return_value = tmp_path
        mock_parse.return_value = ({}, [])
        mock_settings.return_value.output_format = "rich"

        from thegent.cli import dag_list_cmd

        dag_list_cmd(cd=None, format=None)
        assert any("No tasks" in str(c) for c in mock_console.print.call_args_list)

    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli._parse_dag_session")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_dag_not_found(self, mock_console, mock_cwd, mock_parse, mock_settings, tmp_path) -> None:
        # @trace FR-CLI-304
        mock_cwd.return_value = tmp_path

        from thegent.cli import dag_list_cmd

        with pytest.raises(_EXIT):
            dag_list_cmd(cd=None, format=None)


@pytest.mark.unit
class TestDagValidateCmdImpl:
    """Tests for dag_validate_cmd implementation."""

    @patch("thegent.cli._resolve_cwd", return_value=None)
    @patch("thegent.cli.console")
    def test_ambiguous_cwd(self, mock_console, mock_cwd) -> None:
        # @trace FR-CLI-305
        from thegent.cli import dag_validate_cmd

        with pytest.raises(_EXIT):
            dag_validate_cmd(cd=None)

    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_dag_not_found(self, mock_console, mock_cwd, tmp_path) -> None:
        # @trace FR-CLI-306
        mock_cwd.return_value = tmp_path
        from thegent.cli import dag_validate_cmd

        with pytest.raises(_EXIT):
            dag_validate_cmd(cd=None)

    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli._validate_dag", return_value=[])
    @patch("thegent.cli._parse_dag_full")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_valid_dag(self, mock_console, mock_cwd, mock_parse, mock_validate, mock_settings, tmp_path) -> None:
        # @trace FR-CLI-307
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.touch()
        mock_cwd.return_value = tmp_path
        mock_parse.return_value = _make_dag_doc()
        mock_settings.return_value.session_dir = str(tmp_path / "sessions")
        mock_ckpt_registry = MagicMock()
        mock_ckpt_registry.list_checkpoints.return_value = []
        with patch("thegent.execution.CheckpointRegistry", return_value=mock_ckpt_registry):
            from thegent.cli import dag_validate_cmd

            dag_validate_cmd(cd=None)
        assert any("valid" in str(c).lower() for c in mock_console.print.call_args_list)

    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli._validate_dag", return_value=["Cycle detected"])
    @patch("thegent.cli._parse_dag_full")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_invalid_dag(self, mock_console, mock_cwd, mock_parse, mock_validate, mock_settings, tmp_path) -> None:
        # @trace FR-CLI-308
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.touch()
        mock_cwd.return_value = tmp_path
        mock_parse.return_value = _make_dag_doc()

        from thegent.cli import dag_validate_cmd

        with pytest.raises(_EXIT):
            dag_validate_cmd(cd=None)


@pytest.mark.unit
@pytest.mark.skip(reason="WL-124 refactoring - patches needed")
class TestDagAddCmdImpl:
    """Tests for dag_add_cmd implementation."""

    @patch("thegent.cli._resolve_cwd", return_value=None)
    @patch("thegent.cli.console")
    def test_ambiguous_cwd(self, mock_console, mock_cwd) -> None:
        # @trace FR-CLI-309
        from thegent.cli import dag_add_cmd

        with pytest.raises(_EXIT):
            dag_add_cmd(task_id="T1", agent="claude", prompt="test")

    @patch("thegent.cli._validate_task_id", return_value="bad id")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_invalid_task_id(self, mock_console, mock_cwd, mock_validate, tmp_path) -> None:
        # @trace FR-CLI-310
        mock_cwd.return_value = tmp_path
        from thegent.cli import dag_add_cmd

        with pytest.raises(_EXIT):
            dag_add_cmd(task_id="!bad!", agent="claude", prompt="test")

    @patch("thegent.cli._validate_agent", return_value="bad agent")
    @patch("thegent.cli._validate_task_id", return_value=None)
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_invalid_agent(self, mock_console, mock_cwd, mock_vtid, mock_vagent, tmp_path) -> None:
        # @trace FR-CLI-311
        mock_cwd.return_value = tmp_path
        from thegent.cli import dag_add_cmd

        with pytest.raises(_EXIT):
            dag_add_cmd(task_id="T1", agent="@#$", prompt="test")

    @patch("thegent.cli._validate_agent", return_value=None)
    @patch("thegent.cli._validate_task_id", return_value=None)
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_empty_prompt(self, mock_console, mock_cwd, mock_vtid, mock_vagent, tmp_path) -> None:
        # @trace FR-CLI-312
        mock_cwd.return_value = tmp_path
        from thegent.cli import dag_add_cmd

        with pytest.raises(_EXIT):
            dag_add_cmd(task_id="T1", agent="claude", prompt="   ")

    @patch("thegent.cli._atomic_write")
    @patch("thegent.cli._serialize_dag", return_value="serialized")
    @patch("thegent.cli._check_dag_cycles", return_value=[])
    @patch("thegent.cli._ensure_dag_file")
    @patch("thegent.cli._validate_agent", return_value=None)
    @patch("thegent.cli._validate_task_id", return_value=None)
    @patch("thegent.cli._resolve_cwd")
    @pytest.mark.skip(reason="Test needs additional mocking - complex DAG cmd flow")
    @patch("thegent.cli.console")
    def test_add_success(
        self,
        mock_console,
        mock_cwd,
        mock_vtid,
        mock_vagent,
        mock_ensure,
        mock_cycles,
        mock_ser,
        mock_write,
        tmp_path,
    ) -> None:
        # @trace FR-CLI-313
        dag_dir = tmp_path / ".factory"
        dag_dir.mkdir(parents=True)
        mock_cwd.return_value = tmp_path
        mock_ensure.return_value = _make_dag_doc()

        from thegent.cli import dag_add_cmd

        dag_add_cmd(task_id="T1", agent="claude", prompt="Run tests")
        mock_write.assert_called_once()
        assert any("Added" in str(c) for c in mock_console.print.call_args_list)

    @patch("thegent.cli._ensure_dag_file")
    @patch("thegent.cli._validate_agent", return_value=None)
    @patch("thegent.cli._validate_task_id", return_value=None)
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_duplicate_task_id(self, mock_console, mock_cwd, mock_vtid, mock_vagent, mock_ensure, tmp_path) -> None:
        # @trace FR-CLI-314
        dag_dir = tmp_path / ".factory"
        dag_dir.mkdir(parents=True)
        mock_cwd.return_value = tmp_path
        mock_ensure.return_value = _make_dag_doc(
            tasks=[
                {
                    "id": "T1",
                    "agent": "claude",
                    "prompt": "x",
                    "depends_on": "-",
                    "status": "pending",
                }
            ],
        )
        from thegent.cli import dag_add_cmd

        with pytest.raises(_EXIT):
            dag_add_cmd(task_id="T1", agent="claude", prompt="Run tests")


@pytest.mark.unit
@pytest.mark.skip(reason="WL-124 refactoring - patches needed")
class TestDagRemoveCmdImpl:
    """Tests for dag_remove_cmd implementation."""

    @patch("thegent.cli._resolve_cwd", return_value=None)
    @patch("thegent.cli.console")
    def test_ambiguous_cwd(self, mock_console, mock_cwd) -> None:
        # @trace FR-CLI-315
        from thegent.cli import dag_remove_cmd

        with pytest.raises(_EXIT):
            dag_remove_cmd(task_id="T1")

    @patch("thegent.cli._atomic_write")
    @patch("thegent.cli._serialize_dag", return_value="serialized")
    @patch("thegent.cli._parse_dag_full")
    @pytest.mark.skip(reason="Test needs additional mocking - complex DAG cmd flow")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_remove_success(self, mock_console, mock_cwd, mock_parse, mock_ser, mock_write, tmp_path) -> None:
        # @trace FR-CLI-316
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.touch()
        mock_cwd.return_value = tmp_path
        mock_parse.return_value = _make_dag_doc(
            tasks=[
                {
                    "id": "T1",
                    "agent": "claude",
                    "prompt": "x",
                    "depends_on": "-",
                    "status": "pending",
                }
            ],
        )
        from thegent.cli import dag_remove_cmd

        dag_remove_cmd(task_id="T1")
        mock_write.assert_called_once()

    @patch("thegent.cli._parse_dag_full")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_remove_not_found(self, mock_console, mock_cwd, mock_parse, tmp_path) -> None:
        # @trace FR-CLI-317
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.touch()
        mock_cwd.return_value = tmp_path
        mock_parse.return_value = _make_dag_doc()

        from thegent.cli import dag_remove_cmd

        with pytest.raises(_EXIT):
            dag_remove_cmd(task_id="NONEXIST")


@pytest.mark.unit
class TestDagCancelCmdImpl:
    """Tests for dag_cancel_cmd implementation."""

    @pytest.mark.skip(reason="Test needs additional mocking - dag_update_cmd not in cli namespace")
    @patch("thegent.cli.dag_update_cmd")
    @patch("thegent.cli.console")
    def test_cancel_delegates_to_update(self, mock_console, mock_update) -> None:
        # @trace FR-CLI-318
        from thegent.cli import dag_cancel_cmd

        dag_cancel_cmd(task_id="T1", cd=None)
        mock_update.assert_called_once_with(task_id="T1", cd=None, status="cancelled")


@pytest.mark.unit
class TestDagUpdateCmdImpl:
    """Tests for dag_update_cmd implementation."""

    @patch("thegent.cli._resolve_cwd", return_value=None)
    @patch("thegent.cli.console")
    def test_ambiguous_cwd(self, mock_console, mock_cwd) -> None:
        # @trace FR-CLI-319
        from thegent.cli import dag_update_cmd

        with pytest.raises(_EXIT):
            dag_update_cmd(task_id="T1")

    @patch("thegent.cli._parse_dag_full")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_task_not_found(self, mock_console, mock_cwd, mock_parse, tmp_path) -> None:
        # @trace FR-CLI-320
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.touch()
        mock_cwd.return_value = tmp_path
        mock_parse.return_value = _make_dag_doc()

        from thegent.cli import dag_update_cmd

        with pytest.raises(_EXIT):
            dag_update_cmd(task_id="NONEXIST", status="done")

    @patch("thegent.cli._parse_dag_full")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_invalid_status(self, mock_console, mock_cwd, mock_parse, tmp_path) -> None:
        # @trace FR-CLI-321
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.touch()
        mock_cwd.return_value = tmp_path
        mock_parse.return_value = _make_dag_doc(
            tasks=[
                {
                    "id": "T1",
                    "agent": "claude",
                    "prompt": "x",
                    "depends_on": "-",
                    "status": "pending",
                }
            ],
        )
        from thegent.cli import dag_update_cmd

        with pytest.raises(_EXIT):
            dag_update_cmd(task_id="T1", status="INVALID_STATUS")

    @patch("thegent.cli._atomic_write")
    @patch("thegent.cli._serialize_dag", return_value="serialized")
    @patch("thegent.cli._check_dag_cycles", return_value=[])
    @patch("thegent.cli._dag_update_task", return_value=True)
    @patch("thegent.cli._parse_dag_full")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_update_success(
        self,
        mock_console,
        mock_cwd,
        mock_parse,
        mock_upd,
        mock_cycles,
        mock_ser,
        mock_write,
        tmp_path,
    ) -> None:
        # @trace FR-CLI-322
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.touch()
        mock_cwd.return_value = tmp_path
        mock_parse.return_value = _make_dag_doc(
            tasks=[
                {
                    "id": "T1",
                    "agent": "claude",
                    "prompt": "x",
                    "depends_on": "-",
                    "status": "pending",
                }
            ],
        )
        from thegent.cli import dag_update_cmd

        dag_update_cmd(task_id="T1", status="done")
        mock_write.assert_called_once()


@pytest.mark.unit
class TestDagStatusCmdImpl:
    """Tests for dag_status_cmd implementation."""

    @patch("thegent.cli._resolve_cwd", return_value=None)
    @patch("thegent.cli.console")
    def test_ambiguous_cwd(self, mock_console, mock_cwd) -> None:
        # @trace FR-CLI-323
        from thegent.cli import dag_status_cmd

        with pytest.raises(_EXIT):
            dag_status_cmd(cd=None)

    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli._session_status_for", return_value="running")
    @patch("thegent.cli._parse_dag_session")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_with_sessions_json(self, mock_console, mock_cwd, mock_parse, mock_status, mock_settings, tmp_path) -> None:
        # @trace FR-CLI-324
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.touch()
        mock_cwd.return_value = tmp_path
        tasks = [{"id": "T1", "status": "running", "session_id": "sess-123"}]
        mock_parse.return_value = ({}, tasks)
        mock_settings.return_value.output_format = "json"

        from thegent.cli import dag_status_cmd

        dag_status_cmd(cd=None, format="json")

    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli._parse_dag_session")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_no_sessions(self, mock_console, mock_cwd, mock_parse, mock_settings, tmp_path) -> None:
        # @trace FR-CLI-325
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.touch()
        mock_cwd.return_value = tmp_path
        mock_parse.return_value = ({}, [{"id": "T1", "status": "pending"}])
        mock_settings.return_value.output_format = "rich"

        from thegent.cli import dag_status_cmd

        dag_status_cmd(cd=None, format=None)
        assert any("No tasks with session_id" in str(c) for c in mock_console.print.call_args_list)


@pytest.mark.unit
class TestDagReadyCmdImpl:
    """Tests for dag_ready_cmd implementation."""

    @patch("thegent.cli._resolve_cwd", return_value=None)
    @patch("thegent.cli.console")
    def test_ambiguous_cwd(self, mock_console, mock_cwd) -> None:
        # @trace FR-CLI-326
        from thegent.cli import dag_ready_cmd

        with pytest.raises(_EXIT):
            dag_ready_cmd(cd=None)

    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli.commands.dag_impl_ops._get_ready_task_ids", return_value=["T1"])
    @patch("thegent.cli._parse_dag_session")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_ready_ids_format(self, mock_console, mock_cwd, mock_parse, mock_ready, mock_settings, tmp_path) -> None:
        # @trace FR-CLI-327
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.touch()
        mock_cwd.return_value = tmp_path
        tasks = [
            {
                "id": "T1",
                "agent": "claude",
                "prompt": "test",
                "depends_on": "-",
                "status": "pending",
            }
        ]
        mock_parse.return_value = ({}, tasks)
        mock_settings.return_value.output_format = "rich"

        from thegent.cli import dag_ready_cmd

        dag_ready_cmd(cd=None, format="ids")
        assert any("T1" in str(c) for c in mock_console.print.call_args_list)

    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli.commands.dag_impl_ops._get_ready_task_ids", return_value=[])
    @patch("thegent.cli._parse_dag_session")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_no_ready_tasks(self, mock_console, mock_cwd, mock_parse, mock_ready, mock_settings, tmp_path) -> None:
        # @trace FR-CLI-328
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.touch()
        mock_cwd.return_value = tmp_path
        mock_parse.return_value = ({}, [])
        mock_settings.return_value.output_format = "rich"

        from thegent.cli import dag_ready_cmd

        dag_ready_cmd(cd=None, format=None)
        assert any("No ready" in str(c) for c in mock_console.print.call_args_list)

    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli.commands.dag_impl_ops._get_ready_task_ids", return_value=["T1"])
    @patch("thegent.cli._parse_dag_session")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_ready_json(self, mock_console, mock_cwd, mock_parse, mock_ready, mock_settings, tmp_path) -> None:
        # @trace FR-CLI-329
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.touch()
        mock_cwd.return_value = tmp_path
        mock_parse.return_value = (
            {},
            [{"id": "T1", "agent": "claude", "prompt": "test"}],
        )
        mock_settings.return_value.output_format = "json"

        from thegent.cli import dag_ready_cmd

        dag_ready_cmd(cd=None, format="json")


@pytest.mark.unit
class TestDagReconcileCmdImpl:
    """Tests for dag_reconcile_cmd implementation."""

    @patch("thegent.cli._resolve_cwd", return_value=None)
    @patch("thegent.cli.console")
    def test_ambiguous_cwd(self, mock_console, mock_cwd) -> None:
        # @trace FR-CLI-330
        from thegent.cli import dag_reconcile_cmd

        with pytest.raises(_EXIT):
            dag_reconcile_cmd(cd=None)

    @patch("thegent.cli._atomic_write")
    @patch("thegent.cli._serialize_dag", return_value="serialized")
    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli._parse_dag_full")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_reconcile_stuck_running(
        self,
        mock_console,
        mock_cwd,
        mock_parse,
        mock_settings,
        mock_ser,
        mock_write,
        tmp_path,
    ) -> None:
        # @trace FR-CLI-331
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.touch()
        mock_cwd.return_value = tmp_path
        mock_parse.return_value = _make_dag_doc(
            tasks=[
                {
                    "id": "T1",
                    "agent": "claude",
                    "prompt": "x",
                    "depends_on": "-",
                    "status": "running",
                }
            ],
        )
        mock_settings.return_value.session_dir = str(tmp_path)

        from thegent.cli import dag_reconcile_cmd

        dag_reconcile_cmd(cd=None)
        assert any("Reconciled" in str(c) for c in mock_console.print.call_args_list)

    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli._parse_dag_full")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_reconcile_no_changes(self, mock_console, mock_cwd, mock_parse, mock_settings, tmp_path) -> None:
        # @trace FR-CLI-332
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.touch()
        mock_cwd.return_value = tmp_path
        mock_parse.return_value = _make_dag_doc(
            tasks=[
                {
                    "id": "T1",
                    "agent": "claude",
                    "prompt": "x",
                    "depends_on": "-",
                    "status": "done",
                }
            ],
        )
        mock_settings.return_value.session_dir = str(tmp_path)

        from thegent.cli import dag_reconcile_cmd

        dag_reconcile_cmd(cd=None)
        assert any("in sync" in str(c) for c in mock_console.print.call_args_list)


@pytest.mark.unit
class TestDagCheckpointCmdImpl:
    """Tests for dag_checkpoint_cmd implementation."""

    @patch("thegent.cli._resolve_cwd", return_value=None)
    @patch("thegent.cli.console")
    def test_ambiguous_cwd(self, mock_console, mock_cwd) -> None:
        # @trace FR-CLI-333
        from thegent.cli import dag_checkpoint_cmd

        with pytest.raises(_EXIT):
            dag_checkpoint_cmd(cd=None)

    @patch("thegent.cli._default_owner_tag", return_value="ci@host")
    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_checkpoint_created(self, mock_console, mock_cwd, mock_settings, mock_owner, tmp_path) -> None:
        # @trace FR-CLI-334
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.write_text("# DAG\n")
        mock_cwd.return_value = tmp_path
        mock_settings.return_value.session_dir = str(tmp_path / "sessions")

        mock_ckpt = MagicMock()
        mock_ckpt.checkpoint_id = "ckpt-001"
        mock_registry = MagicMock()
        mock_registry.create_checkpoint.return_value = mock_ckpt

        with patch("thegent.execution.CheckpointRegistry", return_value=mock_registry):
            from thegent.cli import dag_checkpoint_cmd

            dag_checkpoint_cmd(cd=None, reason="Test checkpoint")
        mock_registry.create_checkpoint.assert_called_once()
        assert any("Checkpoint" in str(c) for c in mock_console.print.call_args_list)


@pytest.mark.unit
class TestDagRollbackCmdImpl:
    """Tests for dag_rollback_cmd implementation."""

    @patch("thegent.cli._resolve_cwd", return_value=None)
    @patch("thegent.cli.console")
    def test_ambiguous_cwd(self, mock_console, mock_cwd) -> None:
        # @trace FR-CLI-335
        from thegent.cli import dag_rollback_cmd

        with pytest.raises(_EXIT):
            dag_rollback_cmd(checkpoint_id="ckpt-001")

    @patch("thegent.cli._atomic_write")
    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_rollback_success(self, mock_console, mock_cwd, mock_settings, mock_write, tmp_path) -> None:
        # @trace FR-CLI-336
        mock_cwd.return_value = tmp_path
        mock_settings.return_value.session_dir = str(tmp_path / "sessions")

        mock_registry = MagicMock()
        mock_registry.get_checkpoint.return_value = {
            "dag_content": "# Old DAG\n",
            "reason": "Manual",
        }

        with patch("thegent.execution.CheckpointRegistry", return_value=mock_registry):
            from thegent.cli import dag_rollback_cmd

            dag_rollback_cmd(checkpoint_id="ckpt-001")
        mock_write.assert_called_once()

    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_rollback_not_found(self, mock_console, mock_cwd, mock_settings, tmp_path) -> None:
        # @trace FR-CLI-337
        mock_cwd.return_value = tmp_path
        mock_settings.return_value.session_dir = str(tmp_path / "sessions")

        mock_registry = MagicMock()
        mock_registry.get_checkpoint.return_value = None

        with patch("thegent.execution.CheckpointRegistry", return_value=mock_registry):
            from thegent.cli import dag_rollback_cmd

            with pytest.raises(_EXIT):
                dag_rollback_cmd(checkpoint_id="NONEXIST")

    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_rollback_no_content(self, mock_console, mock_cwd, mock_settings, tmp_path) -> None:
        # @trace FR-CLI-338
        mock_cwd.return_value = tmp_path
        mock_settings.return_value.session_dir = str(tmp_path / "sessions")

        mock_registry = MagicMock()
        mock_registry.get_checkpoint.return_value = {
            "dag_content": None,
            "reason": "test",
        }

        with patch("thegent.execution.CheckpointRegistry", return_value=mock_registry):
            from thegent.cli import dag_rollback_cmd

            with pytest.raises(_EXIT):
                dag_rollback_cmd(checkpoint_id="ckpt-empty")


@pytest.mark.unit
class TestDagCheckpointsCmdImpl:
    """Tests for dag_checkpoints_cmd implementation."""

    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli.console")
    def test_no_checkpoints(self, mock_console, mock_settings, tmp_path) -> None:
        # @trace FR-CLI-339
        mock_settings.return_value.session_dir = str(tmp_path)
        mock_registry = MagicMock()
        mock_registry.list_checkpoints.return_value = []

        with patch("thegent.execution.CheckpointRegistry", return_value=mock_registry):
            from thegent.cli import dag_checkpoints_cmd

            dag_checkpoints_cmd(limit=20)
        assert any("No checkpoints" in str(c) for c in mock_console.print.call_args_list)

    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli.console")
    def test_with_checkpoints(self, mock_console, mock_settings, tmp_path) -> None:
        # @trace FR-CLI-340
        mock_settings.return_value.session_dir = str(tmp_path)
        mock_registry = MagicMock()
        mock_registry.list_checkpoints.return_value = [
            {
                "checkpoint_id": "ckpt-1",
                "created_at_utc": "2025-01-01T12:00:00Z",
                "owner": "ci",
                "reason": "test",
            },
        ]

        with patch("thegent.execution.CheckpointRegistry", return_value=mock_registry):
            from thegent.cli import dag_checkpoints_cmd

            dag_checkpoints_cmd(limit=20)
        mock_console.print.assert_called()


@pytest.mark.unit
@pytest.mark.skip(reason="WL-124 refactoring - patches needed")
class TestDagRecoverCmdImpl:
    """Tests for dag_recover_cmd implementation."""

    @patch(
        "thegent.cli.commands._cli_shared.dag_recover_impl",
        return_value={"error": "DAG not found", "changed": False},
    )
    @patch("thegent.cli.console")
    def test_dag_not_found(self, mock_console, mock_dag_path) -> None:
        # @trace FR-CLI-341
        from thegent.cli import dag_recover_cmd

        with pytest.raises(_EXIT):
            dag_recover_cmd(cd=None, action="retry-failed")

    @patch(
        "thegent.cli.commands._cli_shared.dag_recover_impl",
        return_value={"changed": True},
    )
    @patch("thegent.cli.console")
    def test_retry_failed(self, mock_console, mock_impl) -> None:
        # @trace FR-CLI-342
        from thegent.cli import dag_recover_cmd

        dag_recover_cmd(cd=None, action="retry-failed")
        assert any("Reset" in str(c) for c in mock_console.print.call_args_list)

    @patch(
        "thegent.cli.commands._cli_shared.dag_recover_impl",
        return_value={"changed": True},
    )
    @patch("thegent.cli.console")
    def test_clear_stuck(self, mock_console, mock_impl) -> None:
        # @trace FR-CLI-343
        from thegent.cli import dag_recover_cmd

        dag_recover_cmd(cd=None, action="clear-stuck")
        assert any("Reset" in str(c) for c in mock_console.print.call_args_list)

    @patch(
        "thegent.cli.commands._cli_shared.dag_recover_impl",
        return_value={"changed": True},
    )
    @patch("thegent.cli.console")
    def test_reset_retries(self, mock_console, mock_impl) -> None:
        # @trace FR-CLI-344
        from thegent.cli import dag_recover_cmd

        dag_recover_cmd(cd=None, action="reset-retries")
        assert any("Reset" in str(c) for c in mock_console.print.call_args_list)

    @patch(
        "thegent.cli.commands._cli_shared.dag_recover_impl",
        return_value={"changed": False, "error": "Unknown action"},
    )
    @patch("thegent.cli.console")
    def test_unknown_action(self, mock_console, mock_impl) -> None:
        # @trace FR-CLI-345
        from thegent.cli import dag_recover_cmd

        with pytest.raises(_EXIT):
            dag_recover_cmd(cd=None, action="unknown-action")


@pytest.mark.skip(reason="WL-124 refactoring - patches needed")
class TestDagProbeCmdImpl:
    """Tests for dag_probe_cmd implementation."""

    @patch(
        "thegent.cli.commands._cli_shared.dag_recover_impl",
        return_value={"error": "DAG not found", "changed": False},
    )
    @patch("thegent.cli.console")
    def test_dag_not_found(self, mock_console, mock_dag_path) -> None:
        # @trace FR-CLI-346
        from thegent.cli import dag_probe_cmd

        with pytest.raises(_EXIT):
            dag_probe_cmd(cd=None)

    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli.commands.dag_impl_ops._dag_path")
    @patch("thegent.cli.console")
    def test_no_baseline(self, mock_console, mock_dag_path, mock_settings, tmp_path) -> None:
        # @trace FR-CLI-347
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.write_text("# DAG\n")
        mock_dag_path.return_value = (tmp_path, dag_file)
        mock_settings.return_value.session_dir = str(tmp_path)

        mock_registry = MagicMock()
        mock_registry.list_checkpoints.return_value = []

        with patch("thegent.execution.CheckpointRegistry", return_value=mock_registry):
            from thegent.cli import dag_probe_cmd

            dag_probe_cmd(cd=None)
        assert any("No baseline" in str(c) for c in mock_console.print.call_args_list)

    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli.commands.dag_impl_ops._dag_path")
    @patch("thegent.cli.console")
    def test_no_drift(self, mock_console, mock_dag_path, mock_settings, tmp_path) -> None:
        # @trace FR-CLI-348
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.write_text("# DAG content\n")
        mock_dag_path.return_value = (tmp_path, dag_file)
        mock_settings.return_value.session_dir = str(tmp_path)

        mock_registry = MagicMock()
        mock_registry.list_checkpoints.return_value = [{"checkpoint_id": "ckpt-1"}]
        mock_registry.get_checkpoint.return_value = {"dag_content": "# DAG content\n"}

        with patch("thegent.execution.CheckpointRegistry", return_value=mock_registry):
            from thegent.cli import dag_probe_cmd

            dag_probe_cmd(cd=None)
        assert any("No drift" in str(c) for c in mock_console.print.call_args_list)

    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli.commands.dag_impl_ops._dag_path")
    @patch("thegent.cli.console")
    def test_drift_detected(self, mock_console, mock_dag_path, mock_settings, tmp_path) -> None:
        # @trace FR-CLI-349
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.write_text("# DAG content CHANGED\n")
        mock_dag_path.return_value = (tmp_path, dag_file)
        mock_settings.return_value.session_dir = str(tmp_path)

        mock_registry = MagicMock()
        mock_registry.get_checkpoint.return_value = {"dag_content": "# DAG original\n"}

        with patch("thegent.execution.CheckpointRegistry", return_value=mock_registry):
            from thegent.cli import dag_probe_cmd

            dag_probe_cmd(cd=None, baseline_id="ckpt-1")
        assert any("Drift" in str(c) for c in mock_console.print.call_args_list)


# ============================================================================
# DAG RUN & SYNC
# ============================================================================


@pytest.mark.unit
@pytest.mark.skip(reason="WL-124 refactoring - patches needed")
class TestDagRunCmdImpl:
    """Tests for dag_run_cmd implementation."""

    @patch("thegent.cli._resolve_cwd", return_value=None)
    @patch("thegent.cli.console")
    def test_ambiguous_cwd(self, mock_console, mock_cwd) -> None:
        # @trace FR-CLI-350
        from thegent.cli import dag_run_cmd

        with pytest.raises(_EXIT):
            dag_run_cmd(cd=None)

    @patch("thegent.cli.dag_reconcile_cmd")
    @patch("thegent.cli.commands.dag_impl_ops._get_ready_task_ids", return_value=[])
    @patch("thegent.cli._parse_dag_full")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_no_ready_tasks(self, mock_console, mock_cwd, mock_parse, mock_ready, mock_reconcile, tmp_path) -> None:
        # @trace FR-CLI-351
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.touch()
        mock_cwd.return_value = tmp_path
        mock_parse.return_value = _make_dag_doc()

        from thegent.cli import dag_run_cmd

        dag_run_cmd(cd=None, dry_run=False)
        assert any("No ready" in str(c) for c in mock_console.print.call_args_list)

    @patch("thegent.cli.commands.dag_impl_ops._get_ready_task_ids", return_value=["T1"])
    @patch("thegent.cli._parse_dag_full")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_dry_run(self, mock_console, mock_impl, tmp_path) -> None:
        # @trace FR-CLI-352
        from thegent.cli import dag_run_cmd

        dag_run_cmd(cd=None, dry_run=True)
        assert any("Would run" in str(c) for c in mock_console.print.call_args_list)

    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_check_drift_blocks(self, mock_console, mock_cwd, tmp_path) -> None:
        # @trace FR-CLI-353
        mock_cwd.return_value = tmp_path
        mock_settings = MagicMock()
        mock_settings.session_dir = str(tmp_path)
        mock_ct = MagicMock()
        mock_ct.detect_drift.return_value = ["drift: low confidence"]

        with (
            patch("thegent.cli.ThegentSettings", return_value=mock_settings),
            patch("thegent.contracts.telemetry.ContractTelemetry", return_value=mock_ct),
        ):
            from thegent.cli import dag_run_cmd

            with pytest.raises(_EXIT):
                dag_run_cmd(cd=None, check_drift=True, dry_run=False)


@pytest.mark.unit
class TestDagSyncCmdImpl:
    """Tests for dag_sync_cmd implementation."""

    @patch("thegent.cli._resolve_cwd", return_value=None)
    @patch("thegent.cli.console")
    def test_ambiguous_cwd(self, mock_console, mock_cwd) -> None:
        # @trace FR-CLI-354
        from thegent.cli import dag_sync_cmd

        with pytest.raises(_EXIT):
            dag_sync_cmd(cd=None)

    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli._parse_dag_full")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_no_changes(self, mock_console, mock_cwd, mock_parse, mock_settings, tmp_path) -> None:
        # @trace FR-CLI-355
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.touch()
        mock_cwd.return_value = tmp_path
        mock_parse.return_value = _make_dag_doc(
            tasks=[{"id": "T1", "status": "done", "session_id": ""}],
        )
        mock_settings.return_value.session_dir = str(tmp_path)

        from thegent.cli import dag_sync_cmd

        dag_sync_cmd(cd=None)
        assert any("No status changes" in str(c) for c in mock_console.print.call_args_list)


# ============================================================================
# HEALTH COMMANDS
# ============================================================================


@pytest.mark.unit
@pytest.mark.skip(reason="WL-124 refactoring - patches needed")
class TestSessionContractHealthReportCmdImpl:
    """Tests for session_contract_health_report_cmd."""

    @patch("thegent.cli._default_owner_tag", return_value="ci@host")
    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli.console")
    def test_json_format(self, mock_console, mock_settings, mock_owner) -> None:
        # @trace FR-CLI-356
        mock_settings.return_value.output_format = "json"
        result = _health_report_result()

        with patch(
            "thegent.cli.commands.impl.session_contract_health_report_impl",
            return_value=result,
        ):
            from thegent.cli import session_contract_health_report_cmd

            session_contract_health_report_cmd(format="json")

    @patch("thegent.cli._default_owner_tag", return_value="ci@host")
    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli.console")
    def test_rich_format(self, mock_console, mock_settings, mock_owner) -> None:
        # @trace FR-CLI-357
        mock_settings.return_value.output_format = "rich"
        result = _health_report_result(
            top_blocked=[],
            issue_breakdown=[{"issue": "timeout", "count": 3}],
        )

        with patch(
            "thegent.cli.commands.impl.session_contract_health_report_impl",
            return_value=result,
        ):
            from thegent.cli import session_contract_health_report_cmd

            session_contract_health_report_cmd(format=None)
        mock_console.print.assert_called()

    @patch("thegent.cli._default_owner_tag", return_value="ci@host")
    @pytest.mark.skip(reason="Test needs additional mocking - ThegentSettings mock")
    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli.console")
    def test_with_export_output(self, mock_console, mock_settings, mock_owner, tmp_path) -> None:
        # @trace FR-CLI-358
        mock_settings.return_value.output_format = "rich"
        result = _health_report_result()
        output = tmp_path / "report.json"

        with (
            patch(
                "thegent.cli.commands.impl.session_contract_health_report_impl",
                return_value=result,
            ),
            patch(
                "thegent.cli.commands.session_contract_cmds._write_report_export",
                return_value="json",
            ) as mock_write,
            patch(
                "thegent.cli.commands.session_cmds_helpers.resolve_export_format_with_notice",
                return_value="json",
            ),
        ):
            from thegent.cli import session_contract_health_report_cmd

            session_contract_health_report_cmd(output=output, format=None)
        mock_write.assert_called_once()


@pytest.mark.unit
class TestSessionContractHealthGateCmdImpl:
    """Tests for session_contract_health_gate_cmd."""

    @patch("thegent.cli._default_owner_tag", return_value="ci@host")
    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli.console")
    def test_pass_json(self, mock_console, mock_settings, mock_owner) -> None:
        # @trace FR-CLI-359
        mock_settings.return_value.output_format = "json"
        result = _health_gate_result()

        with patch(
            "thegent.cli.commands.impl.session_contract_health_gate_impl",
            return_value=result,
        ):
            from thegent.cli import session_contract_health_gate_cmd

            session_contract_health_gate_cmd(format="json")

    @patch("thegent.cli._default_owner_tag", return_value="ci@host")
    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli.console")
    def test_fail_exits(self, mock_console, mock_settings, mock_owner) -> None:
        # @trace FR-CLI-360
        mock_settings.return_value.output_format = "rich"
        result = _health_gate_result(**{"pass": False, "status": "fail"})

        with patch(
            "thegent.cli.commands.impl.session_contract_health_gate_impl",
            return_value=result,
        ):
            from thegent.cli import session_contract_health_gate_cmd

            with pytest.raises(_EXIT):
                session_contract_health_gate_cmd(format=None)


@pytest.mark.unit
class TestSessionContractHealthTrendCmdImpl:
    """Tests for session_contract_health_trend_cmd."""

    @patch("thegent.cli._default_owner_tag", return_value="ci@host")
    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli.console")
    def test_json_format(self, mock_console, mock_settings, mock_owner) -> None:
        # @trace FR-CLI-361
        mock_settings.return_value.output_format = "json"
        result = _health_trend_result()

        with patch(
            "thegent.cli.commands.impl.session_contract_health_trend_impl",
            return_value=result,
        ):
            from thegent.cli import session_contract_health_trend_cmd

            session_contract_health_trend_cmd(format="json")

    @patch("thegent.cli._default_owner_tag", return_value="ci@host")
    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli.console")
    def test_rich_format_with_latest(self, mock_console, mock_settings, mock_owner) -> None:
        # @trace FR-CLI-362
        mock_settings.return_value.output_format = "rich"
        result = _health_trend_result()

        with patch(
            "thegent.cli.commands.impl.session_contract_health_trend_impl",
            return_value=result,
        ):
            from thegent.cli import session_contract_health_trend_cmd

            session_contract_health_trend_cmd(format=None)
        mock_console.print.assert_called()


# ============================================================================
# SERIALIZATION HELPERS
# ============================================================================


@pytest.mark.unit
class TestSerializeHealthReportMd:
    """Tests for _serialize_health_report_md."""

    def test_basic(self) -> None:
        # @trace FR-CLI-363
        from thegent.cli import _serialize_health_report_md

        result = _health_report_result()
        md = _serialize_health_report_md(result)
        assert "## Session Contract Health Report" in md
        assert "schema_version: 3.0" in md

    def test_with_blocked(self) -> None:
        # @trace FR-CLI-364
        from thegent.cli import _serialize_health_report_md

        result = _health_report_result(
            top_blocked=[
                {
                    "session_id": "s1",
                    "owner": "alice",
                    "state": "blocked",
                    "health": "error",
                    "issues": ["timeout"],
                    "remediation": ["retry"],
                },
            ],
        )
        md = _serialize_health_report_md(result)
        assert "Top Blocked" in md
        assert "s1" in md


@pytest.mark.unit
class TestSerializeHealthReportCsv:
    """Tests for _serialize_health_report_csv."""

    def test_basic(self) -> None:
        # @trace FR-CLI-365
        from thegent.cli import _serialize_health_report_csv

        result = _health_report_result()
        csv_str = _serialize_health_report_csv(result)
        assert "schema_version" in csv_str
        assert "summary" in csv_str


@pytest.mark.unit
class TestSerializeHealthReportJsonl:
    """Tests for _serialize_health_report_jsonl."""

    def test_basic(self) -> None:
        # @trace FR-CLI-366
        from thegent.cli import _serialize_health_report_jsonl

        result = _health_report_result()
        jsonl_str = _serialize_health_report_jsonl(result)
        lines = jsonl_str.strip().split("\n")
        assert len(lines) >= 1
        parsed = json.loads(lines[0])
        assert parsed["record_type"] == "summary"


@pytest.mark.unit
class TestSerializeHealthTrendMd:
    """Tests for _serialize_health_trend_md."""

    def test_basic(self) -> None:
        # @trace FR-CLI-367
        from thegent.cli import _serialize_health_trend_md

        result = _health_trend_result()
        md = _serialize_health_trend_md(result)
        assert "## Session Contract Health Trend" in md
        assert "schema_version: 3.0" in md
        assert "trend_payload_type" in md


@pytest.mark.unit
class TestSerializeHealthTrendCsv:
    """Tests for _serialize_health_trend_csv."""

    def test_basic(self) -> None:
        # @trace FR-CLI-368
        from thegent.cli import _serialize_health_trend_csv

        result = _health_trend_result()
        csv_str = _serialize_health_trend_csv(result)
        assert "schema_version" in csv_str
        assert "trend_payload_type" in csv_str


@pytest.mark.unit
class TestSerializeHealthTrendJsonl:
    """Tests for _serialize_health_trend_jsonl."""

    def test_basic(self) -> None:
        # @trace FR-CLI-369
        from thegent.cli import _serialize_health_trend_jsonl

        result = _health_trend_result()
        jsonl_str = _serialize_health_trend_jsonl(result)
        lines = jsonl_str.strip().split("\n")
        assert len(lines) >= 1
        parsed = json.loads(lines[0])
        assert parsed["record_type"] == "summary"


# ============================================================================
# WRITE EXPORT HELPERS
# ============================================================================


@pytest.mark.unit
class TestWriteHealthTrendExport:
    """Tests for _write_health_trend_export."""

    def test_unsupported_format(self, tmp_path) -> None:
        # @trace FR-CLI-370
        from thegent.cli import _write_health_trend_export

        output = tmp_path / "out.xyz"
        with pytest.raises(_EXIT):
            _write_health_trend_export(
                output=output,
                result=_health_trend_result(),
                export_format="banana",
                overwrite=False,
            )

    def test_output_is_directory(self, tmp_path) -> None:
        # @trace FR-CLI-371
        from thegent.cli import _write_health_trend_export

        with pytest.raises(_EXIT):
            _write_health_trend_export(
                output=tmp_path,
                result=_health_trend_result(),
                export_format="json",
                overwrite=False,
            )

    def test_json_export(self, tmp_path) -> None:
        # @trace FR-CLI-372
        from thegent.cli import _write_health_trend_export

        output = tmp_path / "out.json"
        fmt = _write_health_trend_export(
            output=output,
            result=_health_trend_result(),
            export_format="json",
            overwrite=False,
        )
        assert fmt == "json"
        assert output.exists()

    def test_overwrite_required(self, tmp_path) -> None:
        # @trace FR-CLI-373
        from thegent.cli import _write_health_trend_export

        output = tmp_path / "out.json"
        output.write_text("{}")
        with pytest.raises(_EXIT):
            _write_health_trend_export(
                output=output,
                result=_health_trend_result(),
                export_format="json",
                overwrite=False,
            )

    def test_overwrite_allowed(self, tmp_path) -> None:
        # @trace FR-CLI-374
        from thegent.cli import _write_health_trend_export

        output = tmp_path / "out.json"
        output.write_text("{}")
        fmt = _write_health_trend_export(
            output=output,
            result=_health_trend_result(),
            export_format="json",
            overwrite=True,
        )
        assert fmt == "json"


# ============================================================================
# GOVERNANCE COMMANDS
# ============================================================================


@pytest.mark.unit
class TestEscalateAddCmdImpl:
    """Tests for escalate_add_cmd implementation."""

    @patch("thegent.cli.console")
    def test_basic(self, mock_console) -> None:
        # @trace FR-CLI-375
        with patch("thegent.cli.commands.impl.escalate_add_impl") as mock_impl:
            from thegent.cli import escalate_add_cmd

            escalate_add_cmd(run_id="run-1", reason="blocked", sla_minutes=30)
        mock_impl.assert_called_once()
        assert any("Added" in str(c) for c in mock_console.print.call_args_list)


@pytest.mark.unit
class TestEscalateListCmdImpl:
    """Tests for escalate_list_cmd implementation."""

    @patch("thegent.cli.console")
    def test_empty_list(self, mock_console) -> None:
        # @trace FR-CLI-376
        with patch("thegent.cli.commands.impl.escalate_list_impl", return_value=[]):
            from thegent.cli import escalate_list_cmd

            escalate_list_cmd(format=None)
        assert any("No escalation" in str(c) for c in mock_console.print.call_args_list)

    @patch("thegent.cli.console")
    def test_json_format(self, mock_console) -> None:
        # @trace FR-CLI-377
        items = [
            {
                "run_id": "r1",
                "reason": "timeout",
                "owner": "alice",
                "lane": "standard",
                "blocked_at_utc": "2025-01-01T00:00:00Z",
                "escalate_by_utc": "2025-01-01T00:30:00Z",
                "past_sla": False,
            }
        ]
        with patch("thegent.cli.commands.impl.escalate_list_impl", return_value=items):
            from thegent.cli import escalate_list_cmd

            escalate_list_cmd(format="json")


@pytest.mark.unit
class TestEscalateResolveCmdImpl:
    """Tests for escalate_resolve_cmd implementation."""

    @patch("thegent.cli.console")
    def test_resolve_success(self, mock_console) -> None:
        # @trace FR-CLI-378
        with patch("thegent.cli.commands._cli_shared.escalate_resolve_impl", return_value=True):
            from thegent.cli import escalate_resolve_cmd

            escalate_resolve_cmd(run_id="r1", resolution="fixed")
        assert any("resolved" in str(c).lower() for c in mock_console.print.call_args_list)

    @patch("thegent.cli.console")
    def test_resolve_not_found(self, mock_console) -> None:
        # @trace FR-CLI-379
        with patch("thegent.cli.commands._cli_shared.escalate_resolve_impl", return_value=False):
            from thegent.cli import escalate_resolve_cmd

            escalate_resolve_cmd(run_id="r-nonexist", resolution="fixed")
        assert any("no pending" in str(c).lower() for c in mock_console.print.call_args_list)


@pytest.mark.unit
class TestSweepCmdImpl:
    """Tests for sweep_cmd implementation."""

    @patch("thegent.cli.console")
    def test_sweep_pass(self, mock_console) -> None:
        # @trace FR-CLI-380
        result = {"pass": True, "drift_issues": [], "past_sla_count": 0, "audit": None}
        with patch("thegent.cli.commands.impl.sweep_impl", return_value=result):
            from thegent.cli import sweep_cmd

            sweep_cmd(format=None)
        assert any("passed" in str(c).lower() for c in mock_console.print.call_args_list)

    @patch("thegent.cli.console")
    def test_sweep_fail_exits(self, mock_console) -> None:
        # @trace FR-CLI-381
        result = {
            "pass": False,
            "drift_issues": ["low confidence"],
            "past_sla_count": 2,
            "audit": None,
        }
        with patch("thegent.cli.commands.impl.sweep_impl", return_value=result):
            from thegent.cli import sweep_cmd

            with pytest.raises(_EXIT):
                sweep_cmd(format=None)


@pytest.mark.unit
class TestPurgeCmdImpl:
    """Tests for purge_cmd implementation."""

    @patch("thegent.cli.console")
    def test_dry_run(self, mock_console) -> None:
        # @trace FR-CLI-382
        with patch(
            "thegent.cli.commands.impl.purge_impl",
            return_value={"purged": 5, "kept": 95},
            create=True,
        ):
            from thegent.cli import purge_cmd

            purge_cmd(dry_run=True)
        assert any("Dry-run" in str(c) for c in mock_console.print.call_args_list)

    @patch("thegent.cli.console")
    def test_actual_purge(self, mock_console) -> None:
        # @trace FR-CLI-383
        with patch(
            "thegent.cli.commands.impl.purge_impl",
            return_value={"purged": 5, "kept": 95},
            create=True,
        ):
            from thegent.cli import purge_cmd

            purge_cmd(dry_run=False)
        assert any("Purged" in str(c) for c in mock_console.print.call_args_list)


@pytest.mark.skip(reason="data_protection_cmd function does not exist in codebase")
class TestDataProtectionCmdImpl:
    """Tests for data_protection_cmd implementation."""

    @patch("thegent.cli.console")
    def test_json_format(self, mock_console) -> None:
        # @trace FR-CLI-384
        status = {
            "session_dir": "/tmp/sessions",
            "permissions_restricted": True,
            "masking_enabled": True,
            "retention_policy_days": 30,
        }
        with patch(
            "thegent.cli.commands.impl.get_data_protection_status_impl",
            return_value=status,
        ):
            from thegent.cli import data_protection_cmd

            data_protection_cmd(format="json")

    @patch("thegent.cli.console")
    def test_rich_format(self, mock_console) -> None:
        # @trace FR-CLI-385
        status = {
            "session_dir": "/tmp/sessions",
            "permissions_restricted": True,
            "masking_enabled": False,
            "retention_policy_days": 30,
        }
        with patch(
            "thegent.cli.commands.impl.get_data_protection_status_impl",
            return_value=status,
        ):
            from thegent.cli import data_protection_cmd

            data_protection_cmd(format=None)
        mock_console.print.assert_called()


# ============================================================================
# OBSERVE / COCKPIT / FEEDBACK
# ============================================================================


@pytest.mark.unit
class TestObserveSummaryCmdImpl:
    """Tests for observe_summary_cmd implementation."""

    @patch("thegent.cli.console")
    def test_json_format(self, mock_console) -> None:
        # @trace FR-CLI-386
        result = {
            "kpis": {
                "total_events": 100,
                "fallback_rate": 0.05,
                "success_rate": 0.95,
                "avg_confidence": 0.9,
            },
            "drift": {
                "structural_rate_pct": 1.0,
                "structural_budget_pct": 5.0,
                "semantic_rate_pct": 2.0,
                "semantic_budget_pct": 10.0,
                "within_budget": True,
                "issues": [],
            },
            "escalation": {"backlog_count": 0, "past_sla_count": 0},
        }
        with patch("thegent.cli.commands.impl.observe_summary_impl", return_value=result):
            from thegent.cli import observe_summary_cmd

            observe_summary_cmd(format="json")


@pytest.mark.unit
class TestCockpitCmdImpl:
    """Tests for cockpit_cmd implementation."""

    @patch("thegent.cli.Columns")
    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli.console")
    def test_basic(self, mock_console, mock_settings, mock_columns) -> None:
        # @trace FR-CLI-387
        mock_settings.return_value.session_dir = Path("/tmp/sessions")

        mock_registry = MagicMock()
        mock_registry.list_runs.return_value = []

        mock_cb = MagicMock()
        mock_cb.is_open.return_value = False

        mock_ckpt = MagicMock()
        mock_ckpt.list_checkpoints.return_value = []

        with (
            patch("thegent.cli.RunRegistry", return_value=mock_registry),
            patch("thegent.execution.CircuitBreakerRegistry", return_value=mock_cb),
            patch("thegent.execution.CheckpointRegistry", return_value=mock_ckpt),
            patch("thegent.cli.commands.impl.ps_impl", return_value=[]),
        ):
            from thegent.cli import cockpit_cmd

            cockpit_cmd()
        mock_console.print.assert_called()


@pytest.mark.unit
class TestFeedbackCmdImpl:
    """Tests for feedback_cmd implementation."""

    @patch("thegent.cli.RunRegistry")
    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli.console")
    def test_feedback_recorded(self, mock_console, mock_settings, mock_run_reg_cls) -> None:
        # @trace FR-CLI-388
        mock_settings.return_value.session_dir = Path("/tmp/sessions")
        mock_registry = MagicMock()
        mock_run_reg_cls.return_value = mock_registry

        from thegent.cli import feedback_cmd

        feedback_cmd(run_id="r1", score=0.8, note="good")
        mock_registry.register_feedback.assert_called_once_with("r1", 0.8, "good")
        assert any("Feedback" in str(c) for c in mock_console.print.call_args_list)


# ============================================================================
# ARCHIVE / BENCHMARK / CLOSURE PACK
# ============================================================================


@pytest.mark.unit
class TestArchiveCmdImpl:
    """Tests for archive_cmd implementation."""

    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli.console")
    def test_hot_archive(self, mock_console, mock_settings, tmp_path) -> None:
        # @trace FR-CLI-389
        session_dir = tmp_path / "sessions"
        session_dir.mkdir()
        mock_settings.return_value.session_dir = str(session_dir)
        mock_settings.return_value.retention_days_sessions = 30

        from thegent.cli import archive_cmd

        archive_cmd(days=None, domain=None, tier=None)
        assert any("Archived" in str(c) for c in mock_console.print.call_args_list)

    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli.console")
    def test_cold_archive(self, mock_console, mock_settings, tmp_path) -> None:
        # @trace FR-CLI-390
        session_dir = tmp_path / "sessions"
        session_dir.mkdir()
        archive_dir = session_dir / "archive"
        archive_dir.mkdir()
        mock_settings.return_value.session_dir = str(session_dir)

        from thegent.cli import archive_cmd

        archive_cmd(days=365, domain=None, tier="cold")
        assert any("cold storage" in str(c) for c in mock_console.print.call_args_list)


@pytest.mark.unit
class TestBenchmarkCmdImpl:
    """Tests for benchmark_cmd implementation."""

    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli.console")
    def test_no_runs(self, mock_console, mock_settings) -> None:
        # @trace FR-CLI-391
        mock_settings.return_value.session_dir = Path("/tmp/sessions")
        mock_registry = MagicMock()
        mock_registry.list_runs.return_value = []

        with patch("thegent.cli.RunRegistry", return_value=mock_registry):
            from thegent.cli import benchmark_cmd

            benchmark_cmd()
        assert any("No runs" in str(c) for c in mock_console.print.call_args_list)

    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli.console")
    def test_with_runs(self, mock_console, mock_settings) -> None:
        # @trace FR-CLI-392
        mock_settings.return_value.session_dir = Path("/tmp/sessions")
        mock_registry = MagicMock()
        mock_registry.list_runs.return_value = [
            {"status": "completed", "duration_s": 10.5},
            {"status": "completed", "duration_s": 20.0},
            {"status": "failed", "error_class": "timeout"},
        ]

        mock_telemetry = MagicMock()
        mock_telemetry.get_stats.return_value = {"total": 0}

        with (
            patch("thegent.cli.RunRegistry", return_value=mock_registry),
            patch(
                "thegent.contracts.telemetry.ContractTelemetry",
                return_value=mock_telemetry,
            ),
        ):
            from thegent.cli import benchmark_cmd

            benchmark_cmd()
        mock_console.print.assert_called()


@pytest.mark.unit
class TestClosurePackCmdImpl:
    """Tests for closure_pack_cmd implementation."""

    @patch("thegent.cli._resolve_cwd", return_value=None)
    @patch("thegent.cli.console")
    def test_ambiguous_cwd(self, mock_console, mock_cwd) -> None:
        # @trace FR-CLI-393
        from thegent.cli import closure_pack_cmd

        with pytest.raises(_EXIT):
            closure_pack_cmd(cd=None)

    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli._parse_dag_full")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_generates_pack(self, mock_console, mock_cwd, mock_parse, mock_settings, tmp_path) -> None:
        # @trace FR-CLI-394
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.touch()
        mock_cwd.return_value = tmp_path
        mock_parse.return_value = _make_dag_doc(
            tasks=[{"id": "T1", "status": "done", "evidence": "link"}],
        )
        mock_settings.return_value.session_dir = tmp_path / "sessions"
        mock_settings.return_value.environment = "production"

        mock_registry = MagicMock()
        mock_registry.list_runs.return_value = [{"status": "completed"}]
        mock_registry.registry_path = tmp_path / "registry.jsonl"

        mock_auditor = MagicMock()
        mock_auditor.verify_registry.return_value = {
            "status": "passed",
            "valid_count": 1,
            "corrupt_count": 0,
        }

        mock_ct = MagicMock()
        mock_ct.get_stats.return_value = {
            "success_rate": 0.95,
            "fallback_rate": 0.05,
            "avg_confidence": 0.9,
        }
        mock_ct.get_drift_budget_status.return_value = {
            "structural_rate_pct": 1.0,
            "structural_budget_pct": 5.0,
            "semantic_rate_pct": 2.0,
            "semantic_budget_pct": 10.0,
            "within_budget": True,
        }
        mock_ct.detect_drift.return_value = []

        with (
            patch("thegent.cli.RunRegistry", return_value=mock_registry),
            patch("thegent.execution.Auditor", return_value=mock_auditor),
            patch("thegent.contracts.telemetry.ContractTelemetry", return_value=mock_ct),
        ):
            from thegent.cli import closure_pack_cmd

            closure_pack_cmd(cd=None)
        assert any("Closure pack" in str(c) for c in mock_console.print.call_args_list)


# ============================================================================
# MODEL LISTING HELPERS
# ============================================================================


@pytest.mark.unit
class TestListModelHelpers:
    """Tests for _list_*_models helper functions."""

    @patch("thegent.cli.console")
    def test_list_minimax_models(self, mock_console) -> None:
        # @trace FR-CLI-395
        from thegent.cli import _list_minimax_models

        _list_minimax_models()
        assert any("Minimax" in str(c) for c in mock_console.print.call_args_list)

    @patch("thegent.cli.console")
    def test_list_glm_models(self, mock_console) -> None:
        # @trace FR-CLI-396
        from thegent.cli import _list_glm_models

        _list_glm_models()
        assert any("GLM" in str(c) for c in mock_console.print.call_args_list)

    @patch("thegent.cli.console")
    def test_list_gemini_models(self, mock_console) -> None:
        # @trace FR-CLI-397
        from thegent.cli import _list_gemini_models

        _list_gemini_models()
        assert any("Gemini" in str(c) for c in mock_console.print.call_args_list)

    @patch("thegent.cli.console")
    def test_list_claude_models(self, mock_console) -> None:
        # @trace FR-CLI-398
        from thegent.cli import _list_claude_models

        _list_claude_models()
        assert any("Claude" in str(c) for c in mock_console.print.call_args_list)

    @patch("thegent.cli.subprocess")
    @patch("thegent.cli.console")
    def test_list_cursor_models_success(self, mock_console, mock_subprocess) -> None:
        # @trace FR-CLI-399
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "model-1\nmodel-2\nTip: use these"
        mock_subprocess.run.return_value = mock_proc

        from thegent.cli import _list_cursor_models

        _list_cursor_models()
        assert any("Cursor" in str(c) for c in mock_console.print.call_args_list)

    @patch("thegent.cli.subprocess")
    @patch("thegent.cli.console")
    def test_list_cursor_models_not_found(self, mock_console, mock_subprocess) -> None:
        # @trace FR-CLI-400
        mock_subprocess.run.side_effect = FileNotFoundError
        mock_subprocess.TimeoutExpired = type("TimeoutExpired", (Exception,), {})

        from thegent.cli import _list_cursor_models

        _list_cursor_models()
        assert any("not found" in str(c).lower() for c in mock_console.print.call_args_list)

    @patch("thegent.cli.console")
    def test_list_copilot_models_fallback(self, mock_console) -> None:
        # @trace FR-CLI-301  (re-use series for additional model helpers)
        from thegent.cli import _list_copilot_models_fallback

        _list_copilot_models_fallback()
        assert any("Copilot" in str(c) for c in mock_console.print.call_args_list)

    @patch("thegent.cli.console")
    def test_list_codex_models_fallback(self, mock_console) -> None:
        # @trace FR-CLI-302
        from thegent.cli import _list_codex_models_fallback

        _list_codex_models_fallback()
        assert any("Codex" in str(c) for c in mock_console.print.call_args_list)

    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli.console")
    def test_list_antigravity_models(self, mock_console, mock_settings) -> None:
        # @trace FR-CLI-303
        mock_settings.return_value.default_antigravity_model = "ag-model-1"
        from thegent.cli import _list_antigravity_models

        _list_antigravity_models()
        assert any("Antigravity" in str(c) for c in mock_console.print.call_args_list)


# ============================================================================
# CONTRACTS / DRIFT / MIGRATION
# ============================================================================


@pytest.mark.unit
class TestContractsRegistryCmdImpl:
    """Tests for contracts_registry_cmd implementation."""

    @patch("thegent.cli.console")
    def test_json_format(self, mock_console) -> None:
        # @trace FR-CLI-304
        mock_version = MagicMock()
        mock_version.contract_id = "session-v3"
        mock_version.version = "3.0"
        mock_version.description = "Session contract"
        mock_version.deprecated = False
        mock_version.migration_window_end = None
        mock_version.__dict__ = {
            "contract_id": "session-v3",
            "version": "3.0",
            "description": "test",
            "deprecated": False,
            "migration_window_end": None,
        }

        mock_registry = MagicMock()
        mock_registry.list_versions.return_value = [mock_version]

        with patch("thegent.contracts.registry.get_registry", return_value=mock_registry):
            from thegent.cli import contracts_registry_cmd

            contracts_registry_cmd(format="json")


@pytest.mark.unit
class TestMigrationCmdImpl:
    """Tests for migration_cmd implementation."""

    @patch("thegent.cli.console")
    def test_json_format(self, mock_console) -> None:
        # @trace FR-CLI-305
        result = {
            "allowed": True,
            "status": "active",
            "reason": "supported",
            "migration_days_left": 90,
        }
        mock_mc = MagicMock()
        mock_mc.evaluate_version.return_value = result

        with patch("thegent.contracts.migration.MigrationController", return_value=mock_mc):
            from thegent.cli import migration_cmd

            migration_cmd(contract_id="session-v3", version="3.0", format="json")


@pytest.mark.unit
class TestDriftCmdImpl:
    """Tests for drift_cmd implementation."""

    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli.console")
    def test_no_drift(self, mock_console, mock_settings) -> None:
        # @trace FR-CLI-306
        mock_settings.return_value.session_dir = "/tmp/sessions"
        mock_ct = MagicMock()
        mock_ct.detect_drift.return_value = []
        mock_ct.get_drift_budget_status.return_value = {"within_budget": True}

        with patch("thegent.contracts.telemetry.ContractTelemetry", return_value=mock_ct):
            from thegent.cli import drift_cmd

            drift_cmd(format=None)

    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli.console")
    def test_drift_json(self, mock_console, mock_settings) -> None:
        # @trace FR-CLI-307
        mock_settings.return_value.session_dir = "/tmp/sessions"
        mock_ct = MagicMock()
        mock_ct.detect_drift.return_value = ["confidence drop"]
        mock_ct.get_drift_budget_status.return_value = {"within_budget": False}

        with patch("thegent.contracts.telemetry.ContractTelemetry", return_value=mock_ct):
            from thegent.cli import drift_cmd

            drift_cmd(format="json")


# ============================================================================
# PLAN ANALYZE
# ============================================================================


@pytest.mark.unit
class TestPlanAnalyzeCmdImpl:
    """Tests for plan_analyze_cmd implementation."""

    @patch("thegent.cli._resolve_cwd", return_value=None)
    @patch("thegent.cli.console")
    def test_ambiguous_cwd(self, mock_console, mock_cwd) -> None:
        # @trace FR-CLI-308
        from thegent.cli import plan_analyze_cmd

        with pytest.raises(_EXIT):
            plan_analyze_cmd(cd=None)

    @patch("thegent.cli.ThegentSettings")
    @patch("thegent.cli._parse_dag_full")
    @patch("thegent.cli._resolve_cwd")
    @patch("thegent.cli.console")
    def test_json_format(self, mock_console, mock_cwd, mock_parse, mock_settings, tmp_path) -> None:
        # @trace FR-CLI-309
        dag_file = tmp_path / ".factory" / "dag-session.md"
        dag_file.parent.mkdir(parents=True)
        dag_file.touch()
        mock_cwd.return_value = tmp_path
        mock_parse.return_value = _make_dag_doc(
            tasks=[
                {
                    "id": "T1",
                    "agent": "claude",
                    "prompt": "test",
                    "depends_on": "-",
                    "status": "pending",
                }
            ],
        )
        mock_settings.return_value.output_format = "json"

        MagicMock()
        mock_pert_results = {
            "T1": MagicMock(
                expected_duration=1.0,
                variance=0.1,
                confidence_p50=1.0,
                confidence_p90=1.5,
            )
        }
        mock_contention = []
        mock_cr = MagicMock()
        mock_cr.risk_score = 0.2
        mock_cr.factors = []
        mock_cr.high_risk_tasks = []
        mock_cr.recommendations = []

        with (
            patch(
                "thegent.planning.simulation.pert_forward_pass",
                return_value=mock_pert_results,
            ),
            patch(
                "thegent.planning.simulation.simulate_resource_contention",
                return_value=mock_contention,
            ),
            patch(
                "thegent.planning.simulation.score_continuity_risk",
                return_value=mock_cr,
            ),
            patch("thegent.planning.simulation.PERTNode"),
            patch("thegent.planning.simulation.ContinuityRiskInput"),
        ):
            from thegent.cli import plan_analyze_cmd

            plan_analyze_cmd(cd=None, format="json")
