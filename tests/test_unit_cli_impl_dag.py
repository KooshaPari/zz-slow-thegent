"""Unit tests for cli_impl.py DAG and HEALTH functions.

Covers: _parse_dag_full, _validate_dag, _check_dag_cycles, _serialize_dag,
dag_run/sync/reconcile/checkpoint/rollback/recover/probe (cli.py cmd wrappers),
_build_continuation_prompt, session_contract_health_report/gate/trend_impl,
_load_previous_health_snapshot, _compact_health_snapshot_log, _resolve_health_policy,
observe_summary_impl, cockpit_cmd, feedback_cmd, _observe_summary_freshness_bucket,
and health serialization helpers.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import orjson as json
import pytest

from thegent.cli.commands.impl import (
    HEALTH_PAYLOAD_SCHEMA_VERSION,
    DagDocument,
    _atomic_write,
    _build_continuation_prompt,
    _check_dag_cycles,
    _dag_path,
    _dag_update_task,
    _ensure_contract_version_header,
    _ensure_dag_file,
    _ensure_evidence_header,
    _escape_cell,
    _get_ready_task_ids,
    _hash_health_payload,
    _parse_dag_full,
    _parse_depends_on,
    _serialize_dag,
    _validate_dag,
    _validate_task_id,
    dag_list_impl,
    dag_raw_impl,
)

# AUDIT-N+19 Phase 4: helpers with a new contract live in
# ``session_health_impl`` (canonical home). Import them from there so the
# AUDIT-N+9 legacy contract on ``impl`` (re-exported from
# ``observability_impl``) stays untouched and the AUDIT-N+9 parity
# surface holds.
from thegent.cli.commands.session_health_impl import (  # noqa: E402
    _coerce_issue_types,
    _compact_health_snapshot_log,
    _health_scope_key,
    _load_previous_health_snapshot,
    _observe_summary_freshness_bucket,
    _resolve_health_policy,
)

# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

DAG_CONTENT = """\
---
version: 1
project: test-proj
owner: alice
---
## Tasks

| ID | Agent | Prompt | Depends_on | Status |
|----|-------|--------|------------|--------|
| T1 | claude | do thing 1 | - | pending |
| T2 | claude | do thing 2 | T1 | pending |
| T3 | claude | do thing 3 | T1,T2 | pending |
"""

DAG_CONTENT_DONE = """\
---
version: 1
project: test-proj
owner: alice
---
## Tasks

| ID | Agent | Prompt | Depends_on | Status |
|----|-------|--------|------------|--------|
| T1 | claude | do thing 1 | - | done |
| T2 | claude | do thing 2 | T1 | pending |
"""

DAG_CONTENT_CYCLE = """\
## Tasks

| ID | Agent | Prompt | Depends_on | Status |
|----|-------|--------|------------|--------|
| T1 | claude | do thing 1 | T2 | pending |
| T2 | claude | do thing 2 | T1 | pending |
"""

DAG_CONTENT_SELF_REF = """\
## Tasks

| ID | Agent | Prompt | Depends_on | Status |
|----|-------|--------|------------|--------|
| T1 | claude | do thing 1 | T1 | pending |
"""

DAG_CONTENT_EMPTY = """\
## Tasks

| ID | Agent | Prompt | Depends_on | Status |
|----|-------|--------|------------|--------|
"""


def _write_dag(tmp_path: Path, content: str) -> Path:
    dag_dir = tmp_path / ".factory"
    dag_dir.mkdir(parents=True, exist_ok=True)
    dag_file = dag_dir / "dag-session.md"
    dag_file.write_text(content, encoding="utf-8")
    return dag_file


# =========================================================================
# 1. _parse_dag_full
# =========================================================================


@pytest.mark.unit
class TestParseDagFull:
    """Tests for _parse_dag_full parsing."""

    def test_parse_valid_dag(self, tmp_path) -> None:
        # @trace FR-CLI-151
        dag_file = _write_dag(tmp_path, DAG_CONTENT)
        doc = _parse_dag_full(dag_file)
        assert isinstance(doc, DagDocument)
        assert doc.frontmatter["version"] == "1"
        assert doc.frontmatter["project"] == "test-proj"
        assert doc.frontmatter["owner"] == "alice"
        assert len(doc.tasks) == 3
        assert doc.tasks[0]["id"] == "T1"
        assert doc.tasks[1]["depends_on"] == "T1"

    def test_parse_empty_dag(self, tmp_path) -> None:
        # @trace FR-CLI-152
        dag_file = _write_dag(tmp_path, DAG_CONTENT_EMPTY)
        doc = _parse_dag_full(dag_file)
        assert doc.tasks == []
        assert len(doc.table_headers) > 0

    def test_parse_no_frontmatter(self, tmp_path) -> None:
        # @trace FR-CLI-153
        content = """\
## Tasks

| ID | Agent | Prompt | Depends_on | Status |
|----|-------|--------|------------|--------|
| T1 | claude | do thing 1 | - | pending |
"""
        dag_file = _write_dag(tmp_path, content)
        doc = _parse_dag_full(dag_file)
        assert doc.frontmatter == {}
        assert len(doc.tasks) == 1

    def test_parse_preserves_headers(self, tmp_path) -> None:
        # @trace FR-CLI-154
        dag_file = _write_dag(tmp_path, DAG_CONTENT)
        doc = _parse_dag_full(dag_file)
        assert "id" in doc.table_headers
        assert "agent" in doc.table_headers
        assert "status" in doc.table_headers


# =========================================================================
# 2. _validate_dag
# =========================================================================


@pytest.mark.unit
class TestValidateDag:
    """Tests for _validate_dag validation."""

    @patch("thegent.cli.commands.dag_impl.resolve_agent", side_effect=lambda x: x)
    @patch(
        "thegent.cli.commands.dag_impl.list_agent_names",
        return_value=["claude", "gemini", "codex"],
    )
    def test_valid_dag_no_errors(self, mock_list, mock_resolve, tmp_path) -> None:
        # @trace FR-CLI-155
        dag_file = _write_dag(tmp_path, DAG_CONTENT)
        doc = _parse_dag_full(dag_file)
        errors = _validate_dag(doc)
        assert errors == []

    @patch("thegent.cli.commands.dag_impl.resolve_agent", side_effect=lambda x: x)
    @patch("thegent.cli.commands.dag_impl.list_agent_names", return_value=["claude"])
    def test_invalid_agent(self, mock_list, mock_resolve, tmp_path) -> None:
        # @trace FR-CLI-156
        content = """\
## Tasks

| ID | Agent | Prompt | Depends_on | Status |
|----|-------|--------|------------|--------|
| T1 | fakeagent | do thing | - | pending |
"""
        dag_file = _write_dag(tmp_path, content)
        doc = _parse_dag_full(dag_file)
        errors = _validate_dag(doc)
        assert any("Unknown agent" in e for e in errors)

    @patch("thegent.cli.commands.dag_impl.resolve_agent", side_effect=lambda x: x)
    @patch("thegent.cli.commands.dag_impl.list_agent_names", return_value=["claude"])
    def test_duplicate_task_ids(self, mock_list, mock_resolve, tmp_path) -> None:
        # @trace FR-CLI-157
        content = """\
## Tasks

| ID | Agent | Prompt | Depends_on | Status |
|----|-------|--------|------------|--------|
| T1 | claude | thing 1 | - | pending |
| T1 | claude | thing 2 | - | pending |
"""
        dag_file = _write_dag(tmp_path, content)
        doc = _parse_dag_full(dag_file)
        errors = _validate_dag(doc)
        assert any("Duplicate task ID" in e for e in errors)

    @patch("thegent.cli.commands.dag_impl.resolve_agent", side_effect=lambda x: x)
    @patch("thegent.cli.commands.dag_impl.list_agent_names", return_value=["claude"])
    def test_done_task_missing_evidence(self, mock_list, mock_resolve, tmp_path) -> None:
        # @trace FR-CLI-158
        content = """\
## Tasks

| ID | Agent | Prompt | Depends_on | Status |
|----|-------|--------|------------|--------|
| T1 | claude | do thing | - | done |
"""
        dag_file = _write_dag(tmp_path, content)
        doc = _parse_dag_full(dag_file)
        errors = _validate_dag(doc)
        assert any("evidence" in e.lower() for e in errors)


# =========================================================================
# 3. _check_dag_cycles
# =========================================================================


@pytest.mark.unit
class TestCheckDagCycles:
    """Tests for _check_dag_cycles cycle detection."""

    def test_acyclic_graph(self, tmp_path) -> None:
        # @trace FR-CLI-159
        dag_file = _write_dag(tmp_path, DAG_CONTENT)
        doc = _parse_dag_full(dag_file)
        errors = _check_dag_cycles(doc.tasks)
        cycle_errors = [e for e in errors if "cycle" in e.lower()]
        assert cycle_errors == []

    def test_cyclic_graph(self, tmp_path) -> None:
        # @trace FR-CLI-160
        dag_file = _write_dag(tmp_path, DAG_CONTENT_CYCLE)
        doc = _parse_dag_full(dag_file)
        errors = _check_dag_cycles(doc.tasks)
        assert any("cycle" in e.lower() for e in errors)

    def test_self_referencing_task(self, tmp_path) -> None:
        # @trace FR-CLI-161
        dag_file = _write_dag(tmp_path, DAG_CONTENT_SELF_REF)
        doc = _parse_dag_full(dag_file)
        errors = _check_dag_cycles(doc.tasks)
        assert any("cycle" in e.lower() for e in errors)

    def test_unknown_dependency(self) -> None:
        # @trace FR-CLI-162
        tasks = [
            {"id": "T1", "depends_on": "T99", "status": "pending"},
        ]
        errors = _check_dag_cycles(tasks)
        assert any("unknown task" in e.lower() for e in errors)


# =========================================================================
# 4. _serialize_dag
# =========================================================================


@pytest.mark.unit
class TestSerializeDag:
    """Tests for _serialize_dag serialization."""

    def test_roundtrip_serialization(self, tmp_path) -> None:
        # @trace FR-CLI-163
        dag_file = _write_dag(tmp_path, DAG_CONTENT)
        doc = _parse_dag_full(dag_file)
        output = _serialize_dag(doc)
        assert "| T1 |" in output
        assert "| T2 |" in output
        assert "| T3 |" in output

    def test_empty_tasks_serialization(self) -> None:
        # @trace FR-CLI-164
        doc = DagDocument(
            frontmatter={},
            tasks=[],
            before_table="# DAG\n",
            after_table="",
            table_headers=["id", "agent", "prompt", "depends_on", "status"],
        )
        output = _serialize_dag(doc)
        assert "| id |" in output
        assert "---" in output

    def test_escape_pipe_in_cells(self) -> None:
        # @trace FR-CLI-165
        result = _escape_cell("foo|bar")
        assert "|" not in result or "\\|" in result


# =========================================================================
# 5. dag_run_cmd (cli.py) - tested via mocking
# =========================================================================


@pytest.mark.unit
class TestDagRunCmd:
    """Tests for dag_run_cmd via mocking."""

    @patch("thegent.cli.commands.impl._resolve_cwd")
    @patch("thegent.cli.services.run_dag_helpers.parse_dag_full")
    @patch("thegent.cli.commands.dag_impl._get_ready_task_ids", return_value=["T2"])
    @patch("thegent.cli.commands.impl.bg_impl", return_value={"session_id": "session-abc"})
    @patch("thegent.cli.commands.dag_impl._serialize_dag", return_value="serialized")
    @patch("thegent.cli.commands.dag_impl._atomic_write")
    @patch("thegent.cli.commands.dag_impl._dag_update_task", return_value=True)
    @patch("thegent.cli.commands.dag_impl._resolve_prompt", return_value="do thing 2")
    def test_spawns_ready_tasks(
        self,
        mock_resolve_prompt,
        mock_dag_update,
        mock_write,
        mock_serialize,
        mock_bg,
        mock_ready,
        mock_parse,
        mock_cwd,
        tmp_path,
    ) -> None:
        # @trace FR-CLI-166
        mock_cwd.return_value = tmp_path
        _write_dag(tmp_path, DAG_CONTENT_DONE)
        mock_parse.return_value = DagDocument(
            frontmatter={"version": "1", "project": "test-proj", "owner": "alice"},
            tasks=[
                {
                    "id": "T1",
                    "agent": "claude",
                    "prompt": "do thing 1",
                    "depends_on": "-",
                    "status": "done",
                },
                {
                    "id": "T2",
                    "agent": "claude",
                    "prompt": "do thing 2",
                    "depends_on": "T1",
                    "status": "pending",
                },
            ],
            before_table="## Tasks\n\n",
            after_table="",
            table_headers=["id", "agent", "prompt", "depends_on", "status"],
        )

        from thegent.cli import dag_run_cmd

        dag_run_cmd(cd=tmp_path, dry_run=False)
        mock_bg.assert_called()

    @patch("thegent.cli.commands.impl._resolve_cwd")
    @patch("thegent.cli.services.run_dag_helpers.parse_dag_full")
    @patch("thegent.cli.commands.dag_impl._get_ready_task_ids", return_value=["T2"])
    @patch("thegent.cli.commands.dag_impl._resolve_prompt", return_value="do thing 2")
    def test_dry_run_no_spawn(
        self,
        mock_resolve_prompt,
        mock_ready,
        mock_parse,
        mock_cwd,
        tmp_path,
    ) -> None:
        # @trace FR-CLI-167
        mock_cwd.return_value = tmp_path
        dag_file = _write_dag(tmp_path, DAG_CONTENT_DONE)
        mock_parse.return_value = _parse_dag_full(dag_file)

        from thegent.cli import dag_run_cmd

        with patch("thegent.cli.commands.impl.bg_impl") as mock_bg:
            dag_run_cmd(cd=tmp_path, dry_run=True)
            mock_bg.assert_not_called()

    @patch("thegent.cli.commands.impl._resolve_cwd")
    @patch("thegent.cli.services.run_dag_helpers.parse_dag_full")
    @patch("thegent.cli.commands.dag_impl._get_ready_task_ids", return_value=[])
    def test_no_ready_tasks(self, mock_ready, mock_parse, mock_cwd, tmp_path) -> None:
        # @trace FR-CLI-168
        mock_cwd.return_value = tmp_path
        dag_file = _write_dag(tmp_path, DAG_CONTENT)
        mock_parse.return_value = _parse_dag_full(dag_file)

        from thegent.cli import dag_run_cmd

        dag_run_cmd(cd=tmp_path, dry_run=False)


# =========================================================================
# 6. dag_sync_cmd (cli.py)
# =========================================================================


@pytest.mark.unit
class TestDagSyncCmd:
    """Tests for dag_sync_cmd status updates."""

    @patch("thegent.cli.commands.impl._resolve_cwd")
    @patch("thegent.cli.commands.dag_impl._parse_dag_full")
    @patch("thegent.cli.commands.dag_impl.ThegentSettings")
    @patch("thegent.cli.commands.impl._find_session_meta")
    @patch("thegent.cli.commands.impl._read_session_meta", return_value={"pid": "99999"})
    @patch("thegent.cli.commands.impl._is_pid_running", return_value=False)
    @patch("thegent.cli.commands.impl._session_paths")
    @patch("thegent.cli.commands.dag_impl._serialize_dag", return_value="serialized")
    @patch("thegent.cli.commands.dag_impl._atomic_write")
    @patch("thegent.cli.commands.impl._default_owner_tag", return_value="test:owner")
    def test_sync_marks_done(
        self,
        mock_owner,
        mock_write,
        mock_serialize,
        mock_paths,
        mock_running,
        mock_meta,
        mock_find,
        mock_settings,
        mock_parse,
        mock_cwd,
        tmp_path,
    ) -> None:
        # @trace FR-CLI-169
        mock_cwd.return_value = tmp_path
        _write_dag(tmp_path, DAG_CONTENT)

        doc = DagDocument(
            frontmatter={},
            tasks=[
                {
                    "id": "T1",
                    "agent": "claude",
                    "prompt": "x",
                    "depends_on": "-",
                    "status": "running",
                    "session_id": "sess-1",
                },
            ],
            before_table="",
            after_table="",
            table_headers=["id", "agent", "prompt", "depends_on", "status"],
        )
        mock_parse.return_value = doc

        rc_mock = MagicMock()
        rc_mock.exists.return_value = True
        rc_mock.read_text.return_value = "0"
        mock_paths.return_value = {
            "rc": rc_mock,
            "stdout": MagicMock(),
            "stderr": MagicMock(),
        }

        with patch("thegent.execution.CheckpointRegistry") as mock_ckpt_cls:
            mock_ckpt_inst = MagicMock()
            mock_ckpt_cls.return_value = mock_ckpt_inst
            from thegent.cli import dag_sync_cmd

            dag_sync_cmd(cd=tmp_path)

        assert doc.tasks[0]["status"] == "done"


# =========================================================================
# 7. dag_reconcile_cmd (cli.py)
# =========================================================================


@pytest.mark.unit
class TestDagReconcileCmd:
    """Tests for dag_reconcile_cmd stuck task cleanup."""

    @patch("thegent.cli.commands.plan_cmds._resolve_cwd")
    @patch("thegent.cli.commands.plan_cmds._parse_dag_full")
    @patch("thegent.cli.commands.plan_cmds.ThegentSettings")
    @patch("thegent.cli.commands.plan_cmds._session_status_for", return_value="exited:0")
    @patch("thegent.cli.commands.plan_cmds._serialize_dag", return_value="serialized")
    @patch("thegent.cli.commands.plan_cmds._atomic_write")
    def test_reconcile_stuck_running_to_pending(
        self,
        mock_write,
        mock_serialize,
        mock_status,
        mock_settings,
        mock_parse,
        mock_cwd,
        tmp_path,
    ) -> None:
        # @trace FR-CLI-170
        mock_cwd.return_value = tmp_path
        _write_dag(tmp_path, DAG_CONTENT)

        doc = DagDocument(
            frontmatter={},
            tasks=[
                {
                    "id": "T1",
                    "agent": "claude",
                    "prompt": "x",
                    "depends_on": "-",
                    "status": "running",
                    "session_id": "sess-dead",
                },
            ],
            before_table="",
            after_table="",
            table_headers=["id", "agent", "prompt", "depends_on", "status"],
        )
        mock_parse.return_value = doc

        from thegent.cli import dag_reconcile_cmd

        dag_reconcile_cmd(cd=tmp_path)

        assert doc.tasks[0]["status"] == "pending"

    @patch("thegent.cli.commands.plan_cmds._resolve_cwd")
    @patch("thegent.cli.commands.plan_cmds._parse_dag_full")
    @patch("thegent.cli.commands.plan_cmds.ThegentSettings")
    def test_reconcile_no_running_no_change(self, mock_settings, mock_parse, mock_cwd, tmp_path) -> None:
        # @trace FR-CLI-171
        mock_cwd.return_value = tmp_path
        _write_dag(tmp_path, DAG_CONTENT)

        doc = DagDocument(
            frontmatter={},
            tasks=[
                {
                    "id": "T1",
                    "agent": "claude",
                    "prompt": "x",
                    "depends_on": "-",
                    "status": "pending",
                },
            ],
            before_table="",
            after_table="",
            table_headers=["id", "agent", "prompt", "depends_on", "status"],
        )
        mock_parse.return_value = doc

        from thegent.cli import dag_reconcile_cmd

        dag_reconcile_cmd(cd=tmp_path)

        assert doc.tasks[0]["status"] == "pending"


# =========================================================================
# 8. dag_checkpoint_cmd (cli.py)
# =========================================================================


@pytest.mark.unit
class TestDagCheckpointCmd:
    """Tests for dag_checkpoint_cmd."""

    @patch("thegent.cli.commands.plan_cmds._resolve_cwd")
    @patch("thegent.cli.commands.plan_cmds.ThegentSettings")
    @patch("thegent.execution.CheckpointRegistry")
    @patch("thegent.cli.commands.plan_cmds._default_owner_tag", return_value="test:owner")
    def test_checkpoint_creation(self, mock_owner, mock_registry_cls, mock_settings, mock_cwd, tmp_path) -> None:
        # @trace FR-CLI-172
        mock_cwd.return_value = tmp_path
        _write_dag(tmp_path, DAG_CONTENT)

        mock_registry = MagicMock()
        mock_ckpt = MagicMock()
        mock_ckpt.checkpoint_id = "ckpt-123"
        mock_registry.create_checkpoint.return_value = mock_ckpt
        mock_registry_cls.return_value = mock_registry

        from thegent.cli import dag_checkpoint_cmd

        dag_checkpoint_cmd(cd=tmp_path, reason="test checkpoint")

        mock_registry.create_checkpoint.assert_called_once()
        call_kwargs = mock_registry.create_checkpoint.call_args
        assert "test checkpoint" in str(call_kwargs)


# =========================================================================
# 9. dag_rollback_cmd (cli.py)
# =========================================================================


@pytest.mark.unit
class TestDagRollbackCmd:
    """Tests for dag_rollback_cmd."""

    @patch("thegent.cli.commands.plan_cmds._resolve_cwd")
    @patch("thegent.cli.commands.plan_cmds.ThegentSettings")
    @patch("thegent.execution.CheckpointRegistry")
    @patch("thegent.cli.commands.plan_cmds._atomic_write")
    def test_rollback_to_checkpoint(self, mock_write, mock_registry_cls, mock_settings, mock_cwd, tmp_path) -> None:
        # @trace FR-CLI-173
        mock_cwd.return_value = tmp_path
        _write_dag(tmp_path, DAG_CONTENT)

        mock_registry = MagicMock()
        mock_registry.get_checkpoint.return_value = {
            "checkpoint_id": "ckpt-abc",
            "dag_content": "## Restored DAG content",
            "reason": "before experiment",
        }
        mock_registry_cls.return_value = mock_registry

        from thegent.cli import dag_rollback_cmd

        dag_rollback_cmd(checkpoint_id="ckpt-abc", cd=tmp_path)

        mock_write.assert_called_once()
        written_content = mock_write.call_args[0][1]
        assert written_content == "## Restored DAG content"

    @patch("thegent.cli.commands.plan_cmds._resolve_cwd")
    @patch("thegent.cli.commands.plan_cmds.ThegentSettings")
    @patch("thegent.execution.CheckpointRegistry")
    def test_rollback_missing_checkpoint(self, mock_registry_cls, mock_settings, mock_cwd, tmp_path) -> None:
        # @trace FR-CLI-174
        mock_cwd.return_value = tmp_path
        _write_dag(tmp_path, DAG_CONTENT)

        mock_registry = MagicMock()
        mock_registry.get_checkpoint.return_value = None
        mock_registry_cls.return_value = mock_registry

        import click

        from thegent.cli import dag_rollback_cmd

        with pytest.raises(click.exceptions.Exit):
            dag_rollback_cmd(checkpoint_id="nonexistent", cd=tmp_path)


# =========================================================================
# 10. dag_recover_cmd (cli.py)
# =========================================================================


@pytest.mark.unit
class TestDagRecoverCmd:
    """Tests for dag_recover_cmd recovery actions."""

    def _make_doc(self, tasks):
        return DagDocument(
            frontmatter={},
            tasks=tasks,
            before_table="",
            after_table="",
            table_headers=[
                "id",
                "agent",
                "prompt",
                "depends_on",
                "status",
                "retry_count",
            ],
        )

    @patch("thegent.cli.commands.impl._resolve_cwd")
    @patch("thegent.cli.commands.dag_impl._parse_dag_full")
    @patch("thegent.cli.commands.dag_impl._serialize_dag", return_value="serialized")
    @patch("thegent.cli.commands.dag_impl._atomic_write")
    def test_retry_failed(self, mock_write, mock_serialize, mock_parse, mock_cwd, tmp_path) -> None:
        # @trace FR-CLI-175
        mock_cwd.return_value = tmp_path
        _write_dag(tmp_path, DAG_CONTENT)

        doc = self._make_doc(
            [
                {
                    "id": "T1",
                    "agent": "claude",
                    "prompt": "x",
                    "depends_on": "-",
                    "status": "failed",
                },
                {
                    "id": "T2",
                    "agent": "claude",
                    "prompt": "y",
                    "depends_on": "-",
                    "status": "done",
                },
            ]
        )
        mock_parse.return_value = doc

        from thegent.cli import dag_recover_cmd

        dag_recover_cmd(cd=tmp_path, action="retry-failed")

        assert doc.tasks[0]["status"] == "pending"
        assert doc.tasks[1]["status"] == "done"

    @patch("thegent.cli.commands.impl._resolve_cwd")
    @patch("thegent.cli.commands.dag_impl._parse_dag_full")
    @patch("thegent.cli.commands.dag_impl._serialize_dag", return_value="serialized")
    @patch("thegent.cli.commands.dag_impl._atomic_write")
    def test_clear_stuck(self, mock_write, mock_serialize, mock_parse, mock_cwd, tmp_path) -> None:
        # @trace FR-CLI-176
        mock_cwd.return_value = tmp_path
        _write_dag(tmp_path, DAG_CONTENT)

        doc = self._make_doc(
            [
                {
                    "id": "T1",
                    "agent": "claude",
                    "prompt": "x",
                    "depends_on": "-",
                    "status": "running",
                },
            ]
        )
        mock_parse.return_value = doc

        from thegent.cli import dag_recover_cmd

        dag_recover_cmd(cd=tmp_path, action="clear-stuck")

        assert doc.tasks[0]["status"] == "pending"

    @patch("thegent.cli.commands.impl._resolve_cwd")
    @patch("thegent.cli.commands.dag_impl._parse_dag_full")
    @patch("thegent.cli.commands.dag_impl._serialize_dag", return_value="serialized")
    @patch("thegent.cli.commands.dag_impl._atomic_write")
    def test_reset_retries(self, mock_write, mock_serialize, mock_parse, mock_cwd, tmp_path) -> None:
        # @trace FR-CLI-177
        mock_cwd.return_value = tmp_path
        _write_dag(tmp_path, DAG_CONTENT)

        doc = self._make_doc(
            [
                {
                    "id": "T1",
                    "agent": "claude",
                    "prompt": "x",
                    "depends_on": "-",
                    "status": "failed",
                    "retry_count": "3",
                },
            ]
        )
        mock_parse.return_value = doc

        from thegent.cli import dag_recover_cmd

        dag_recover_cmd(cd=tmp_path, action="reset-retries")

        assert doc.tasks[0]["retry_count"] == "0"


# =========================================================================
# 11. dag_probe_cmd (cli.py)
# =========================================================================


@pytest.mark.unit
class TestDagProbeCmd:
    """Tests for dag_probe_cmd regression detection."""

    @patch("thegent.cli.commands.plan_cmds._dag_path")
    @patch("thegent.cli.commands.plan_cmds.ThegentSettings")
    @patch("thegent.execution.CheckpointRegistry")
    def test_probe_no_drift(self, mock_registry_cls, mock_settings, mock_dag_path, tmp_path) -> None:
        # @trace FR-CLI-178
        dag_file = _write_dag(tmp_path, DAG_CONTENT)
        mock_dag_path.return_value = (tmp_path, dag_file)

        mock_registry = MagicMock()
        mock_registry.list_checkpoints.return_value = [{"checkpoint_id": "ckpt-base"}]
        mock_registry.get_checkpoint.return_value = {
            "checkpoint_id": "ckpt-base",
            "dag_content": DAG_CONTENT,
        }
        mock_registry_cls.return_value = mock_registry

        from thegent.cli import dag_probe_cmd

        dag_probe_cmd(cd=tmp_path)

    @patch("thegent.cli.commands.plan_cmds._dag_path")
    @patch("thegent.cli.commands.plan_cmds.ThegentSettings")
    @patch("thegent.execution.CheckpointRegistry")
    def test_probe_drift_detected(self, mock_registry_cls, mock_settings, mock_dag_path, tmp_path) -> None:
        # @trace FR-CLI-179
        dag_file = _write_dag(tmp_path, DAG_CONTENT)
        mock_dag_path.return_value = (tmp_path, dag_file)

        mock_registry = MagicMock()
        mock_registry.list_checkpoints.return_value = [{"checkpoint_id": "ckpt-old"}]
        mock_registry.get_checkpoint.return_value = {
            "checkpoint_id": "ckpt-old",
            "dag_content": "## different content",
        }
        mock_registry_cls.return_value = mock_registry

        from thegent.cli import dag_probe_cmd

        dag_probe_cmd(cd=tmp_path)


# =========================================================================
# 12. _build_continuation_prompt
# =========================================================================


@pytest.mark.unit
class TestBuildContinuationPrompt:
    """Tests for _build_continuation_prompt."""

    @patch(
        "thegent.cli.commands.session_impl._load_prior_session_output",
        return_value="prior output text",
    )
    def test_prompt_includes_prior_context(self, mock_load) -> None:
        # @trace FR-CLI-180
        settings = MagicMock()
        result = _build_continuation_prompt(settings, "sess-1", "do next thing")
        assert "prior output text" in result
        assert "do next thing" in result
        assert "Continuing from prior session" in result

    @patch("thegent.cli.commands.session_impl._load_prior_session_output", return_value="")
    def test_prompt_no_prior_output(self, mock_load) -> None:
        # @trace FR-CLI-181
        settings = MagicMock()
        result = _build_continuation_prompt(settings, "sess-1", "do next thing")
        assert result == "do next thing"

    def test_prompt_empty_session_ids(self) -> None:
        # @trace FR-CLI-182
        settings = MagicMock()
        result = _build_continuation_prompt(settings, "", "do next thing")
        assert result == "do next thing"

    @patch(
        "thegent.cli.commands.session_impl._load_prior_session_output",
        side_effect=["output A", "output B"],
    )
    def test_prompt_multiple_sessions(self, mock_load) -> None:
        # @trace FR-CLI-183
        settings = MagicMock()
        result = _build_continuation_prompt(settings, "sess-1,sess-2", "combine results")
        assert "sess-1" in result
        assert "sess-2" in result
        assert "combine results" in result


# =========================================================================
# 13. session_contract_health_report_impl
# =========================================================================


@pytest.mark.unit
class TestHealthReportImpl:
    """Tests for session_contract_health_report_impl."""

    @patch("thegent.cli.commands.session_health_report_impl.session_contract_audit_impl")
    @patch(
        "thegent.cli.commands.session_health_report_impl._load_previous_health_snapshot",
        return_value=None,
    )
    @patch("thegent.cli.commands.session_health_report_impl._append_health_snapshot")
    def test_report_all_healthy(self, mock_append, mock_prev, mock_audit) -> None:
        # @trace FR-CLI-184
        mock_audit.return_value = {
            "summary": {
                "total": 5,
                "health": {"healthy": 5, "warning": 0, "error": 0, "missing": 0},
            },
            "rows": [
                {
                    "session_id": f"s{i}",
                    "owner": "alice",
                    "contract_health": "healthy",
                    "contract_state": "active",
                    "contract_issues": [],
                }
                for i in range(5)
            ],
        }

        from thegent.cli.commands.impl import session_contract_health_report_impl

        result = session_contract_health_report_impl(owner="alice")
        assert result["status"] == "passed"
        assert result["healthy_count"] == 5
        assert result["blocked_count"] == 0
        assert result["payload_type"] == "session_contract_health_report"

    @patch("thegent.cli.commands.session_health_report_impl.session_contract_audit_impl")
    @patch(
        "thegent.cli.commands.session_health_report_impl._load_previous_health_snapshot",
        return_value=None,
    )
    @patch("thegent.cli.commands.session_health_report_impl._append_health_snapshot")
    def test_report_with_blockers(self, mock_append, mock_prev, mock_audit) -> None:
        # @trace FR-CLI-185
        mock_audit.return_value = {
            "summary": {
                "total": 2,
                "health": {"healthy": 1, "warning": 0, "error": 1, "missing": 0},
            },
            "rows": [
                {
                    "session_id": "s1",
                    "owner": "alice",
                    "contract_health": "healthy",
                    "contract_state": "active",
                    "contract_issues": [],
                },
                {
                    "session_id": "s2",
                    "owner": "alice",
                    "contract_health": "error",
                    "contract_state": "done",
                    "contract_issues": ["missing_contract:provider"],
                },
            ],
        }

        from thegent.cli.commands.impl import session_contract_health_report_impl

        result = session_contract_health_report_impl(owner="alice")
        assert result["blocked_count"] == 1
        assert result["schema_version"] == HEALTH_PAYLOAD_SCHEMA_VERSION
        assert "payload_signature" in result


# =========================================================================
# 14. session_contract_health_gate_impl
# =========================================================================


@pytest.mark.unit
class TestHealthGateImpl:
    """Tests for session_contract_health_gate_impl."""

    @patch("thegent.cli.commands.session_health_impl.session_contract_audit_impl")
    @patch(
        "thegent.cli.commands.session_health_impl._load_previous_health_snapshot",
        return_value=None,
    )
    @patch("thegent.cli.commands.session_health_impl._append_health_snapshot")
    def test_gate_pass(self, mock_append, mock_prev, mock_audit) -> None:
        # @trace FR-CLI-186
        mock_audit.return_value = {
            "summary": {
                "total": 3,
                "health": {"healthy": 3, "warning": 0, "error": 0, "missing": 0},
            },
            "rows": [
                {
                    "session_id": f"s{i}",
                    "owner": "alice",
                    "contract_health": "healthy",
                    "contract_state": "active",
                    "contract_issues": [],
                }
                for i in range(3)
            ],
        }

        from thegent.cli.commands.impl import session_contract_health_gate_impl

        result = session_contract_health_gate_impl(owner="alice", min_healthy_ratio=1.0)
        assert result["pass"] is True
        assert result["status"] == "passed"

    @patch("thegent.cli.commands.session_health_impl.session_contract_audit_impl")
    @patch(
        "thegent.cli.commands.session_health_impl._load_previous_health_snapshot",
        return_value=None,
    )
    @patch("thegent.cli.commands.session_health_impl._append_health_snapshot")
    def test_gate_fail(self, mock_append, _mock_prev, mock_audit) -> None:
        # @trace FR-CLI-187
        mock_audit.return_value = {
            "summary": {
                "total": 4,
                "health": {"healthy": 2, "warning": 0, "error": 2, "missing": 0},
            },
            "rows": [
                {
                    "session_id": "s1",
                    "owner": "alice",
                    "contract_health": "healthy",
                    "contract_state": "active",
                    "contract_issues": [],
                },
                {
                    "session_id": "s2",
                    "owner": "alice",
                    "contract_health": "healthy",
                    "contract_state": "active",
                    "contract_issues": [],
                },
                {
                    "session_id": "s3",
                    "owner": "alice",
                    "contract_health": "error",
                    "contract_state": "done",
                    "contract_issues": ["missing_contract:provider"],
                },
                {
                    "session_id": "s4",
                    "owner": "alice",
                    "contract_health": "error",
                    "contract_state": "done",
                    "contract_issues": ["missing_contract:model_alias"],
                },
            ],
        }

        from thegent.cli.commands.impl import session_contract_health_gate_impl

        result = session_contract_health_gate_impl(owner="alice", min_healthy_ratio=1.0)
        assert result["pass"] is False
        assert result["status"] == "blocked"
        assert result["blocked_count"] == 2


# =========================================================================
# 15. session_contract_health_trend_impl
# =========================================================================


@pytest.mark.unit
class TestHealthTrendImpl:
    """Tests for session_contract_health_trend_impl."""

    @patch("thegent.cli.commands.session_health_report_impl._health_snapshot_log_path")
    @patch(
        "thegent.cli.commands.session_health_report_impl._health_snapshot_max_lines",
        return_value=5000,
    )
    def test_trend_empty_snapshots(self, _mock_max, mock_path, tmp_path) -> None:
        # @trace FR-CLI-188
        snap_path = tmp_path / "snapshots.jsonl"
        mock_path.return_value = snap_path

        from thegent.cli.commands.impl import session_contract_health_trend_impl

        result = session_contract_health_trend_impl(
            payload_type="session_contract_health_report",
            owner="alice",
        )
        assert result["snapshot_count"] == 0
        assert result["latest"] is None

    @patch("thegent.cli.commands.session_health_report_impl._health_snapshot_log_path")
    @patch(
        "thegent.cli.commands.session_health_report_impl._health_snapshot_max_lines",
        return_value=5000,
    )
    def test_trend_reads_existing_snapshots(self, _mock_max, mock_path, tmp_path) -> None:
        # @trace FR-CLI-189
        snap_path = tmp_path / "snapshots.jsonl"
        scope_key = {
            "payload_type": "session_contract_health_report",
            "owner": "alice",
            "all": False,
            "strict": False,
            "policy_profile": "custom",
            "top_blocked": 25,
        }
        snapshot = {
            "record_type": "health_snapshot",
            "scope_key": scope_key,
            "captured_at_utc": "2026-02-14T10:00:00+00:00",
            "status": "passed",
            "pass": True,
            "blocked_ratio": 0.0,
            "blocked_count": 0,
            "issue_types": [],
        }
        snap_path.write_text(
            json.dumps(snapshot, option=json.OPT_SORT_KEYS).decode() + "\n",
            encoding="utf-8",
        )
        mock_path.return_value = snap_path

        from thegent.cli.commands.impl import session_contract_health_trend_impl

        result = session_contract_health_trend_impl(
            payload_type="session_contract_health_report",
            owner="alice",
        )
        assert result["snapshot_count"] == 1

    def test_trend_invalid_payload_type(self) -> None:
        # @trace FR-CLI-190
        import typer

        from thegent.cli.commands.impl import session_contract_health_trend_impl

        with pytest.raises(typer.BadParameter):
            session_contract_health_trend_impl(payload_type="bogus_type")


# =========================================================================
# 16. _load_previous_health_snapshot
# =========================================================================


@pytest.mark.unit
class TestLoadPreviousHealthSnapshot:
    """Tests for _load_previous_health_snapshot."""

    @patch("thegent.cli.commands.session_health_impl._health_snapshot_log_path")
    def test_load_from_file(self, mock_path, tmp_path) -> None:
        # @trace FR-CLI-191
        snap_path = tmp_path / "snapshots.jsonl"
        scope_key = {"payload_type": "gate", "owner": "bob"}
        record = {
            "record_type": "health_snapshot",
            "scope_key": scope_key,
            "blocked_ratio": 0.1,
        }
        snap_path.write_text(
            json.dumps(record, option=json.OPT_SORT_KEYS).decode() + "\n",
            encoding="utf-8",
        )
        mock_path.return_value = snap_path

        result = _load_previous_health_snapshot(scope_key)
        assert result is not None
        assert result["blocked_ratio"] == 0.1

    @patch("thegent.cli.commands.session_health_impl._health_snapshot_log_path")
    def test_load_no_matching_scope(self, mock_path, tmp_path) -> None:
        # @trace FR-CLI-192
        snap_path = tmp_path / "snapshots.jsonl"
        record = {
            "record_type": "health_snapshot",
            "scope_key": {"payload_type": "gate", "owner": "alice"},
            "blocked_ratio": 0.5,
        }
        snap_path.write_text(
            json.dumps(record, option=json.OPT_SORT_KEYS).decode() + "\n",
            encoding="utf-8",
        )
        mock_path.return_value = snap_path

        result = _load_previous_health_snapshot({"payload_type": "gate", "owner": "bob"})
        assert result is None

    @patch("thegent.cli.commands.session_health_impl._health_snapshot_log_path")
    def test_load_no_file(self, mock_path, tmp_path) -> None:
        # @trace FR-CLI-193
        mock_path.return_value = tmp_path / "nonexistent.jsonl"
        result = _load_previous_health_snapshot({"payload_type": "gate", "owner": "x"})
        assert result is None


# =========================================================================
# 17. _compact_health_snapshot_log
# =========================================================================


@pytest.mark.unit
class TestCompactHealthSnapshotLog:
    """Tests for _compact_health_snapshot_log."""

    @patch("thegent.cli.commands.session_health_impl._health_snapshot_log_path")
    @patch(
        "thegent.cli.commands.session_health_impl._health_snapshot_max_lines",
        return_value=3,
    )
    def test_compacts_when_over_limit(self, _mock_max, mock_path, tmp_path) -> None:
        # @trace FR-CLI-194
        snap_path = tmp_path / "snapshots.jsonl"
        lines = [f'{{"line": {i}}}' for i in range(10)]
        snap_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        mock_path.return_value = snap_path

        _compact_health_snapshot_log()

        remaining_lines = [l for l in snap_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        assert len(remaining_lines) == 3

    @patch("thegent.cli.commands.session_health_impl._health_snapshot_log_path")
    @patch(
        "thegent.cli.commands.session_health_impl._health_snapshot_max_lines",
        return_value=100,
    )
    def test_no_compact_when_under_limit(self, _mock_max, mock_path, tmp_path) -> None:
        # @trace FR-CLI-195
        snap_path = tmp_path / "snapshots.jsonl"
        lines = [f'{{"line": {i}}}' for i in range(5)]
        snap_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        mock_path.return_value = snap_path

        _compact_health_snapshot_log()

        remaining_lines = [l for l in snap_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        assert len(remaining_lines) == 5


# =========================================================================
# 18. _resolve_health_policy
# =========================================================================


@pytest.mark.unit
class TestResolveHealthPolicy:
    """Tests for _resolve_health_policy."""

    def test_strict_ci_profile(self) -> None:
        # @trace FR-CLI-196
        result = _resolve_health_policy("strict_ci", strict=False, min_healthy_ratio=0.5)
        assert result["profile"] == "strict_ci"
        assert result["strict"] is True
        assert result["min_healthy_ratio"] == 1.0
        assert result["profile_exists"] is True

    def test_warn_only_profile(self) -> None:
        # @trace FR-CLI-197
        result = _resolve_health_policy("warn_only", strict=True, min_healthy_ratio=0.9)
        assert result["profile"] == "warn_only"
        assert result["strict"] is False
        assert result["min_healthy_ratio"] == 0.0

    def test_custom_profile_no_match(self) -> None:
        # @trace FR-CLI-198
        result = _resolve_health_policy("nonexistent_profile", strict=True, min_healthy_ratio=0.8)
        assert result["profile_exists"] is False
        assert result["strict"] is True
        assert result["min_healthy_ratio"] == 0.8

    def test_none_profile_uses_params(self) -> None:
        # @trace FR-CLI-199
        result = _resolve_health_policy(None, strict=True, min_healthy_ratio=0.75)
        assert result["profile"] == "custom"
        assert result["strict"] is True
        assert result["min_healthy_ratio"] == 0.75

    def test_clamped_ratio(self) -> None:
        # @trace FR-CLI-200
        result = _resolve_health_policy(None, strict=False, min_healthy_ratio=5.0)
        assert result["min_healthy_ratio"] == 1.0
        result_neg = _resolve_health_policy(None, strict=False, min_healthy_ratio=-0.5)
        assert result_neg["min_healthy_ratio"] == 0.0


# =========================================================================
# 19. observe_summary_impl (smoke test with heavy mocking)
# =========================================================================


@pytest.mark.unit
class TestObserveSummaryImpl:
    """Tests for observe_summary_impl."""

    @patch("thegent.cli.commands.impl.ThegentSettings")
    @patch("thegent.cli.commands.impl.ContractTelemetry", create=True)
    @patch("thegent.cli.commands.impl.EscalationQueue", create=True)
    def test_observe_summary_basic(self, mock_queue_cls, mock_ct_cls, mock_settings) -> None:
        # @trace FR-CLI-151
        mock_settings.return_value = MagicMock(session_dir="/tmp/sessions")

        mock_ct = MagicMock()
        mock_ct.get_fallback_kpis.return_value = {
            "total_events": 10,
            "fallback_rate": 0.1,
            "success_rate": 0.9,
            "avg_confidence": 0.95,
            "structural_drift_pct": 1.0,
            "semantic_drift_pct": 2.0,
        }
        mock_ct.detect_drift.return_value = []
        mock_ct.get_drift_budget_status.return_value = {
            "within_budget": True,
            "structural_rate_pct": 1.0,
            "semantic_rate_pct": 2.0,
            "structural_budget_pct": 5.0,
            "semantic_budget_pct": 10.0,
        }
        mock_ct_cls.return_value = mock_ct

        mock_queue = MagicMock()
        mock_queue.list_pending.return_value = []
        mock_queue_cls.return_value = mock_queue

        with (
            patch("thegent.cli.commands.impl._health_snapshot_log_path") as mock_snap_path,
            patch("thegent.cli.commands.impl._compact_health_snapshot_log"),
        ):
            mock_snap_path.return_value = Path("/tmp/fake-snapshots.jsonl")

            from thegent.cli.commands.impl import observe_summary_impl

            result = observe_summary_impl(limit=100, trend_samples=0)
            assert "status" in result
            assert "kpis" in result


# =========================================================================
# 20. cockpit_cmd (cli.py)
# =========================================================================


@pytest.mark.unit
class TestCockpitCmd:
    """Tests for cockpit_cmd."""

    @patch("thegent.cli.commands.infra_cmds.ThegentSettings")
    @patch("thegent.cli.commands.infra_cmds.RunRegistry")
    @patch("thegent.execution.CircuitBreakerRegistry")
    @patch("thegent.execution.CheckpointRegistry")
    @patch("thegent.cli.commands.impl.ps_impl")
    def test_cockpit_output(self, mock_ps, mock_ckpt_cls, mock_cb_cls, mock_rr_cls, _mock_settings) -> None:
        # @trace FR-CLI-152
        mock_ps.return_value = [
            {"session_id": "s1", "status": "running"},
            {"session_id": "s2", "status": "exited:1"},
        ]
        mock_rr = MagicMock()
        mock_rr.list_runs.return_value = []
        mock_rr_cls.return_value = mock_rr

        mock_cb = MagicMock()
        mock_cb.is_open.return_value = False
        mock_cb_cls.return_value = mock_cb

        mock_ckpt = MagicMock()
        mock_ckpt.list_checkpoints.return_value = [{"checkpoint_id": "ckpt-1"}]
        mock_ckpt_cls.return_value = mock_ckpt

        from thegent.cli import cockpit_cmd

        cockpit_cmd()


# =========================================================================
# 21. feedback_cmd (cli.py)
# =========================================================================


@pytest.mark.unit
class TestFeedbackCmd:
    """Tests for feedback_cmd."""

    @patch("thegent.cli.commands.session_cmds.ThegentSettings")
    @patch("thegent.cli.commands.session_cmds.RunRegistry")
    def test_feedback_recording(self, mock_rr_cls, _mock_settings) -> None:
        # @trace FR-CLI-153
        mock_rr = MagicMock()
        mock_rr_cls.return_value = mock_rr

        from thegent.cli import feedback_cmd

        feedback_cmd(run_id="run-123", score=0.9, note="good run")

        mock_rr.register_feedback.assert_called_once_with("run-123", 0.9, "good run")

    @patch("thegent.cli.commands.session_cmds.ThegentSettings")
    @patch("thegent.cli.commands.session_cmds.RunRegistry")
    def test_feedback_no_note(self, mock_rr_cls, _mock_settings) -> None:
        # @trace FR-CLI-154
        mock_rr = MagicMock()
        mock_rr_cls.return_value = mock_rr

        from thegent.cli import feedback_cmd

        feedback_cmd(run_id="run-456", score=0.5)

        mock_rr.register_feedback.assert_called_once_with("run-456", 0.5, None)


# =========================================================================
# 22. _observe_summary_freshness_bucket
# =========================================================================


@pytest.mark.unit
class TestObserveSummaryFreshnessBucket:
    """Tests for _observe_summary_freshness_bucket bucket classification."""

    def test_fresh_bucket(self) -> None:
        # @trace FR-CLI-155
        result = _observe_summary_freshness_bucket(30, fresh_seconds=60, warm_seconds=300, stale_seconds=600)
        assert result == "fresh"

    def test_warm_bucket(self) -> None:
        # @trace FR-CLI-156
        result = _observe_summary_freshness_bucket(120, fresh_seconds=60, warm_seconds=300, stale_seconds=600)
        assert result == "warm"

    def test_stale_bucket(self) -> None:
        # @trace FR-CLI-157
        result = _observe_summary_freshness_bucket(400, fresh_seconds=60, warm_seconds=300, stale_seconds=600)
        assert result == "stale"

    def test_critical_bucket(self) -> None:
        # @trace FR-CLI-158
        result = _observe_summary_freshness_bucket(900, fresh_seconds=60, warm_seconds=300, stale_seconds=600)
        assert result == "critical"

    def test_unknown_bucket(self) -> None:
        # @trace FR-CLI-159
        result = _observe_summary_freshness_bucket(None, fresh_seconds=60, warm_seconds=300, stale_seconds=600)
        assert result == "unknown"

    def test_future_bucket(self) -> None:
        # @trace FR-CLI-160
        result = _observe_summary_freshness_bucket(-10, fresh_seconds=60, warm_seconds=300, stale_seconds=600)
        assert result == "future"


# =========================================================================
# 23. Health report serialization helpers (cli.py)
# =========================================================================


@pytest.mark.unit
class TestSerializeHealthReport:
    """Tests for _serialize_health_report_md/csv/jsonl."""

    def _report_fixture(self):
        return {
            "schema_version": HEALTH_PAYLOAD_SCHEMA_VERSION,
            "schema_compat_mode": "compat",
            "payload_type": "session_contract_health_report",
            "payload_signature": {"algorithm": "sha256", "value": "abc123"},
            "status": "blocked",
            "pass": False,
            "total": 5,
            "total_sessions": 5,
            "healthy_count": 4,
            "healthy_sessions": 4,
            "unhealthy_count": 1,
            "unhealthy_sessions": 1,
            "blocked_count": 1,
            "blocked_sessions": 1,
            "blocked_sessions_count": 1,
            "blocked_ratio": 0.2,
            "top_blocked_count": 1,
            "strict_checks_enabled": True,
            "health": {"healthy": 4, "warning": 0, "error": 1, "missing": 0},
            "issue_counts": {"missing_contract:provider": 1},
            "issue_breakdown": [{"issue": "missing_contract:provider", "count": 1}],
            "owner_breakdown": {
                "alice": {
                    "total": 5,
                    "healthy": 4,
                    "warning": 0,
                    "error": 1,
                    "missing": 0,
                },
            },
            "top_blocked": [
                {
                    "session_id": "s5",
                    "owner": "alice",
                    "state": "done",
                    "health": "error",
                    "issues": ["missing_contract:provider"],
                    "remediation": ["Ensure route_contract includes provider metadata at session creation."],
                    "started_at_utc": "2026-02-14T10:00:00Z",
                    "agent": "claude",
                },
            ],
            "generated_at_utc": "2026-02-14T12:00:00Z",
            "generated_query": {
                "owner": "alice",
                "all": False,
                "strict": True,
                "top_blocked": 25,
            },
            "compat": {"mode": "compat", "aliases": {}},
        }

    def test_md_serialization(self) -> None:
        # @trace FR-CLI-161
        from thegent.cli import _serialize_health_report_md

        result = _serialize_health_report_md(self._report_fixture())
        assert "## Session Contract Health Report" in result
        assert "blocked" in result.lower()
        assert "s5" in result

    def test_csv_serialization(self) -> None:
        # @trace FR-CLI-162
        from thegent.cli import _serialize_health_report_csv

        result = _serialize_health_report_csv(self._report_fixture())
        assert "schema_version" in result
        assert "s5" in result

    def test_jsonl_serialization(self) -> None:
        # @trace FR-CLI-163
        from thegent.cli import _serialize_health_report_jsonl

        result = _serialize_health_report_jsonl(self._report_fixture())
        lines = [l for l in result.strip().splitlines() if l.strip()]
        assert len(lines) >= 1
        parsed = json.loads(lines[0])
        assert parsed["record_type"] == "summary"


# =========================================================================
# 24. Health trend serialization helpers (cli.py)
# =========================================================================


@pytest.mark.unit
class TestSerializeHealthTrend:
    """Tests for _serialize_health_trend_md/csv/jsonl."""

    def _trend_fixture(self):
        return {
            "schema_version": HEALTH_PAYLOAD_SCHEMA_VERSION,
            "schema_compat_mode": "compat",
            "payload_type": "session_contract_health_trend",
            "payload_signature": {"algorithm": "sha256", "value": "def456"},
            "trend_payload_type": "session_contract_health_report",
            "scope_key": {
                "payload_type": "session_contract_health_report",
                "owner": "alice",
                "all": False,
                "strict": False,
                "policy_profile": "custom",
                "top_blocked": 25,
            },
            "scope_key_json": '{"all":false,"owner":"alice","payload_type":"session_contract_health_report","policy_profile":"custom","strict":false,"top_blocked":25}',
            "scope_payload_type": "session_contract_health_report",
            "scope_owner": "alice",
            "scope_all": False,
            "scope_strict": False,
            "scope_policy_profile": "custom",
            "scope_min_healthy_ratio": None,
            "scope_top_blocked": 25,
            "snapshot_count": 2,
            "snapshot_ids_csv": "2026-02-14T10:00:00+00:00, 2026-02-14T09:00:00+00:00",
            "snapshot_ids_hash": "abc",
            "snapshot_window_seconds": 3600,
            "snapshot_window_hash": "def",
            "snapshot_interval_seconds_avg": 3600,
            "snapshot_interval_hash": "ghi",
            "snapshot_freshness_seconds": 100,
            "snapshot_freshness_hash": "jkl",
            "snapshot_density_per_hour": 2.0,
            "snapshot_density_hash": "mno",
            "snapshot_issue_churn_count": 0,
            "snapshot_issue_churn_hash": "pqr",
            "snapshot_health_volatility": 0.01,
            "snapshot_health_volatility_hash": "stu",
            "limit": 20,
            "latest": {
                "captured_at_utc": "2026-02-14T10:00:00+00:00",
                "status": "passed",
                "pass": True,
                "blocked_ratio": 0.0,
                "blocked_count": 0,
                "issue_types": [],
            },
            "latest_status": "passed",
            "latest_pass": True,
            "latest_captured_at_utc": "2026-02-14T10:00:00+00:00",
            "latest_blocked_ratio": 0.0,
            "latest_blocked_count": 0,
            "latest_issue_types_count": 0,
            "latest_issue_types_csv": "",
            "latest_issue_types_json": "[]",
            "latest_issue_types_hash": "empty",
            "oldest": {
                "captured_at_utc": "2026-02-14T09:00:00+00:00",
                "status": "passed",
                "pass": True,
                "blocked_ratio": 0.0,
                "blocked_count": 0,
                "issue_types": [],
            },
            "delta_summary": {"blocked_ratio_delta": 0.0, "blocked_count_delta": 0},
            "delta_summary_json": '{"blocked_count_delta":0,"blocked_ratio_delta":0.0}',
            "blocked_ratio_delta": 0.0,
            "blocked_count_delta": 0,
            "snapshot_retention_max_lines": 5000,
            "snapshots": [],
            "generated_at_utc": "2026-02-14T12:00:00Z",
            "compat": {"mode": "compat", "aliases": {}},
            "compat_aliases_count": 0,
        }

    def test_trend_md_serialization(self) -> None:
        # @trace FR-CLI-164
        from thegent.cli import _serialize_health_trend_md

        result = _serialize_health_trend_md(self._trend_fixture())
        assert "## Session Contract Health Trend" in result
        assert "snapshot_count: 2" in result

    def test_trend_csv_serialization(self) -> None:
        # @trace FR-CLI-165
        from thegent.cli import _serialize_health_trend_csv

        result = _serialize_health_trend_csv(self._trend_fixture())
        assert "schema_version" in result
        assert "snapshot_count" in result

    def test_trend_jsonl_serialization(self) -> None:
        # @trace FR-CLI-166
        from thegent.cli import _serialize_health_trend_jsonl

        result = _serialize_health_trend_jsonl(self._trend_fixture())
        lines = [l for l in result.strip().splitlines() if l.strip()]
        assert len(lines) >= 1
        parsed = json.loads(lines[0])
        assert parsed["record_type"] == "summary"


# =========================================================================
# Additional helper coverage
# =========================================================================


@pytest.mark.unit
class TestDagHelpers:
    """Tests for small DAG helper functions."""

    def test_parse_depends_on_empty(self) -> None:
        # @trace FR-CLI-167
        assert _parse_depends_on("") == []
        assert _parse_depends_on("-") == []
        assert _parse_depends_on("\u2014") == []

    def test_parse_depends_on_single(self) -> None:
        # @trace FR-CLI-168
        assert _parse_depends_on("T1") == ["T1"]

    def test_parse_depends_on_multiple(self) -> None:
        # @trace FR-CLI-169
        result = _parse_depends_on("T1, T2, T3")
        assert result == ["T1", "T2", "T3"]

    def test_get_ready_task_ids_all_pending_no_deps(self) -> None:
        # @trace FR-CLI-170
        tasks = [
            {"id": "T1", "depends_on": "-", "status": "pending"},
            {"id": "T2", "depends_on": "-", "status": "pending"},
        ]
        ready = _get_ready_task_ids(tasks)
        assert set(ready) == {"T1", "T2"}

    def test_get_ready_task_ids_blocked_by_pending_dep(self) -> None:
        # @trace FR-CLI-171
        tasks = [
            {"id": "T1", "depends_on": "-", "status": "pending"},
            {"id": "T2", "depends_on": "T1", "status": "pending"},
        ]
        ready = _get_ready_task_ids(tasks)
        assert ready == ["T1"]

    def test_get_ready_task_ids_dep_done(self) -> None:
        # @trace FR-CLI-172
        tasks = [
            {"id": "T1", "depends_on": "-", "status": "done"},
            {"id": "T2", "depends_on": "T1", "status": "pending"},
        ]
        ready = _get_ready_task_ids(tasks)
        assert ready == ["T2"]

    def test_validate_task_id_valid(self) -> None:
        # @trace FR-CLI-173
        assert _validate_task_id("T1") is None
        assert _validate_task_id("task-01") is None
        assert _validate_task_id("A_B_C") is None

    def test_validate_task_id_invalid(self) -> None:
        # @trace FR-CLI-174
        assert _validate_task_id("") is not None
        assert _validate_task_id("  ") is not None
        assert _validate_task_id("@invalid") is not None

    def test_dag_update_task(self) -> None:
        # @trace FR-CLI-175
        doc = DagDocument(
            frontmatter={},
            tasks=[
                {
                    "id": "T1",
                    "agent": "claude",
                    "prompt": "x",
                    "depends_on": "-",
                    "status": "pending",
                },
            ],
            before_table="",
            after_table="",
            table_headers=["id", "agent", "prompt", "depends_on", "status"],
        )
        updated = _dag_update_task(doc, "T1", status="running", session_id="sess-1")
        assert updated is True
        assert doc.tasks[0]["status"] == "running"
        assert doc.tasks[0]["evidence"] == "sess-1"

    def test_dag_update_task_not_found(self) -> None:
        # @trace FR-CLI-176
        doc = DagDocument(
            frontmatter={},
            tasks=[
                {
                    "id": "T1",
                    "agent": "claude",
                    "prompt": "x",
                    "depends_on": "-",
                    "status": "pending",
                },
            ],
            before_table="",
            after_table="",
            table_headers=["id", "agent", "prompt", "depends_on", "status"],
        )
        updated = _dag_update_task(doc, "NONEXISTENT", status="running")
        assert updated is False

    def test_coerce_issue_types_list(self) -> None:
        # @trace FR-CLI-177
        assert _coerce_issue_types(["a", "b"]) == ["a", "b"]

    def test_coerce_issue_types_dict(self) -> None:
        # @trace FR-CLI-178
        assert _coerce_issue_types({"a": 1, "b": 2}) == ["a", "b"]

    def test_coerce_issue_types_none(self) -> None:
        # @trace FR-CLI-179
        assert _coerce_issue_types(None) == []

    def test_hash_health_payload_deterministic(self) -> None:
        # @trace FR-CLI-180
        payload = {
            "key": "value",
            "generated_at_utc": "varies",
            "payload_signature": "varies",
        }
        h1 = _hash_health_payload(payload)
        h2 = _hash_health_payload(payload)
        assert h1 == h2
        assert h1["algorithm"] == "sha256"

    def test_ensure_dag_file_creates_empty(self, tmp_path) -> None:
        # @trace FR-CLI-181
        fake_path = tmp_path / ".factory" / "dag-session.md"
        doc = _ensure_dag_file(fake_path)
        assert isinstance(doc, DagDocument)
        assert doc.tasks == []

    def test_ensure_dag_file_loads_existing(self, tmp_path) -> None:
        # @trace FR-CLI-182
        dag_file = _write_dag(tmp_path, DAG_CONTENT)
        doc = _ensure_dag_file(dag_file)
        assert len(doc.tasks) == 3

    def test_atomic_write(self, tmp_path) -> None:
        # @trace FR-CLI-183
        target = tmp_path / "test_output.md"
        _atomic_write(target, "hello world")
        assert target.read_text(encoding="utf-8") == "hello world"

    def test_atomic_write_with_backup(self, tmp_path) -> None:
        # @trace FR-CLI-184
        target = tmp_path / "test_output.md"
        target.write_text("original", encoding="utf-8")
        _atomic_write(target, "updated", backup=True)
        assert target.read_text(encoding="utf-8") == "updated"
        assert (tmp_path / "test_output.md.bak").exists()

    def test_health_scope_key(self) -> None:
        # @trace FR-CLI-185
        payload = {
            "payload_type": "session_contract_health_gate",
            "generated_query": {
                "owner": "alice",
                "all": False,
                "strict": True,
                "min_healthy_ratio": 0.95,
            },
            "policy_profile": "strict_ci",
        }
        scope = _health_scope_key(payload)
        assert scope["payload_type"] == "session_contract_health_gate"
        assert scope["owner"] == "alice"
        assert scope["min_healthy_ratio"] == 0.95

    def test_ensure_evidence_header_adds_column(self) -> None:
        # @trace FR-CLI-186
        doc = DagDocument(
            frontmatter={},
            tasks=[{"id": "T1", "status": "done", "evidence": "sess-1"}],
            before_table="",
            after_table="",
            table_headers=["id", "agent", "prompt", "depends_on", "status"],
        )
        _ensure_evidence_header(doc)
        assert "evidence" in doc.table_headers

    def test_ensure_contract_version_header(self) -> None:
        # @trace FR-CLI-187
        doc = DagDocument(
            frontmatter={},
            tasks=[{"id": "T1", "status": "done", "contract_version": "v2"}],
            before_table="",
            after_table="",
            table_headers=["id", "agent", "prompt", "depends_on", "status"],
        )
        _ensure_contract_version_header(doc)
        assert "contract_version" in doc.table_headers

    @patch("thegent.cli.commands.impl._resolve_cwd", return_value=None)
    def test_dag_path_returns_none_for_ambiguous_cwd(self, _mock_cwd) -> None:
        # @trace FR-CLI-188
        cwd, dp = _dag_path(None)
        assert cwd is None
        assert dp is None

    @patch("thegent.cli.commands.impl._resolve_cwd")
    def test_dag_list_impl_no_file(self, mock_cwd, tmp_path) -> None:
        # @trace FR-CLI-189
        mock_cwd.return_value = tmp_path
        result = dag_list_impl(cd=tmp_path)
        assert "error" in result

    @patch("thegent.cli.commands.impl._resolve_cwd")
    def test_dag_list_impl_with_file(self, mock_cwd, tmp_path) -> None:
        # @trace FR-CLI-190
        mock_cwd.return_value = tmp_path
        _write_dag(tmp_path, DAG_CONTENT)
        result = dag_list_impl(cd=tmp_path)
        assert "tasks" in result
        assert len(result["tasks"]) == 3

    @patch("thegent.cli.commands.impl._resolve_cwd")
    def test_dag_raw_impl_no_file(self, mock_cwd, tmp_path) -> None:
        # @trace FR-CLI-191
        mock_cwd.return_value = tmp_path
        result = dag_raw_impl(cd=tmp_path)
        assert "Error" in result

    @patch("thegent.cli.commands.impl._resolve_cwd")
    def test_dag_raw_impl_with_file(self, mock_cwd, tmp_path) -> None:
        # @trace FR-CLI-192
        mock_cwd.return_value = tmp_path
        _write_dag(tmp_path, DAG_CONTENT)
        result = dag_raw_impl(cd=tmp_path)
        assert "T1" in result
        assert "T2" in result
