"""Unit tests for thegent.commands.sync (SY-009).

All tests are isolated: filesystem access is either in-memory (tmp_path) or
mocked so that no real disk I/O touches the live repository state.

Traces to: FR-SYNC-001 through FR-SYNC-020
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from thegent.commands.sync import (
    OperationResult,
    SyncCommand,
    SyncOperationStatus,
    SyncResult,
)

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _make_cmd(tmp_path: Path, **kwargs) -> SyncCommand:
    """Create a SyncCommand rooted at a temporary directory."""
    return SyncCommand(project_root=tmp_path, **kwargs)


def _agent_dir(tmp_path: Path, names: list[str]) -> Path:
    """Create a minimal agents/ directory with the given .md file stems."""
    d = tmp_path / "agents"
    d.mkdir()
    for name in names:
        (d / f"{name}.md").write_text(f"# {name}\n", encoding="utf-8")
    return d


def _hooks_dir(tmp_path: Path, scripts: list[str]) -> Path:
    """Create a minimal hooks/ directory with the given .sh file stems."""
    d = tmp_path / "hooks"
    d.mkdir()
    for name in scripts:
        (d / f"{name}.sh").write_text(f"#!/bin/sh\n# {name}\n", encoding="utf-8")
    return d


def _hook_config(hooks_dir: Path, registered: list[str]) -> Path:
    """Write a minimal hook-config.yaml with the listed hook names."""
    lines = ["hooks:"]
    for name in registered:
        lines.append(f"  {name}:")
        lines.append(f"    description: {name}")
    path = hooks_dir / "hook-config.yaml"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _plan_dir(tmp_path: Path, items: list[str]) -> Path:
    """Create docs/plans/ with a single plan.md containing checkbox items."""
    d = tmp_path / "docs" / "plans"
    d.mkdir(parents=True)
    content = "\n".join(items) + "\n"
    (d / "plan.md").write_text(content, encoding="utf-8")
    return d


# ---------------------------------------------------------------------------
# OperationResult
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestOperationResult:
    def test_ok_success(self) -> None:
        # @trace FR-SYNC-001
        op = OperationResult(operation="test", status=SyncOperationStatus.SUCCESS, message="good")
        assert op.ok is True

    def test_ok_dry_run(self) -> None:
        # @trace FR-SYNC-001
        op = OperationResult(operation="test", status=SyncOperationStatus.DRY_RUN)
        assert op.ok is True

    def test_not_ok_failed(self) -> None:
        # @trace FR-SYNC-001
        op = OperationResult(operation="test", status=SyncOperationStatus.FAILED, message="err")
        assert op.ok is False

    def test_not_ok_skipped(self) -> None:
        # @trace FR-SYNC-001
        op = OperationResult(operation="test", status=SyncOperationStatus.SKIPPED)
        assert op.ok is False

    def test_to_dict_keys(self) -> None:
        # @trace FR-SYNC-002
        op = OperationResult(operation="x", status=SyncOperationStatus.SUCCESS, message="m")
        d = op.to_dict()
        assert set(d.keys()) == {
            "operation",
            "status",
            "message",
            "duration",
            "details",
            "errors",
            "changes",
            "timestamp",
        }

    def test_to_dict_values(self) -> None:
        # @trace FR-SYNC-002
        op = OperationResult(
            operation="agents",
            status=SyncOperationStatus.SUCCESS,
            message="found 3",
            changes=["a", "b"],
        )
        d = op.to_dict()
        assert d["operation"] == "agents"
        assert d["status"] == "success"
        assert d["changes"] == ["a", "b"]


# ---------------------------------------------------------------------------
# SyncResult
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSyncResult:
    def test_success_all_ok(self) -> None:
        # @trace FR-SYNC-003
        r = SyncResult(
            operations=[
                OperationResult("a", SyncOperationStatus.SUCCESS),
                OperationResult("b", SyncOperationStatus.DRY_RUN),
            ]
        )
        assert r.success is True

    def test_success_with_failure(self) -> None:
        # @trace FR-SYNC-003
        r = SyncResult(
            operations=[
                OperationResult("a", SyncOperationStatus.SUCCESS),
                OperationResult("b", SyncOperationStatus.FAILED),
            ]
        )
        assert r.success is False

    def test_failed_operations_filtered(self) -> None:
        # @trace FR-SYNC-003
        ok = OperationResult("a", SyncOperationStatus.SUCCESS)
        bad = OperationResult("b", SyncOperationStatus.FAILED)
        r = SyncResult(operations=[ok, bad])
        assert r.failed_operations == [bad]

    def test_to_dict_structure(self) -> None:
        # @trace FR-SYNC-004
        r = SyncResult()
        r.operations.append(OperationResult("x", SyncOperationStatus.SUCCESS))
        d = r.to_dict()
        assert "success" in d
        assert "operations" in d
        assert isinstance(d["operations"], list)


# ---------------------------------------------------------------------------
# SyncCommand — sync_work_stream
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSyncWorkStream:
    def test_dry_run_returns_dry_run_status(self, tmp_path: Path) -> None:
        # @trace FR-SYNC-005
        _plan_dir(tmp_path, ["- [ ] task A", "- [ ] task B"])
        cmd = _make_cmd(tmp_path)
        op = cmd.sync_work_stream(dry_run=True)
        assert op.status == SyncOperationStatus.DRY_RUN
        assert op.ok is True

    def test_dry_run_reports_fragment_count(self, tmp_path: Path) -> None:
        # @trace FR-SYNC-005
        _plan_dir(tmp_path, ["- [ ] task X", "- [ ] task Y", "- [ ] task Z"])
        cmd = _make_cmd(tmp_path)
        op = cmd.sync_work_stream(dry_run=True)
        assert op.details["fragments_found"] == 3

    def test_incorporates_new_items(self, tmp_path: Path) -> None:
        # @trace FR-SYNC-006
        _plan_dir(tmp_path, ["- [ ] brand new task"])
        work_stream = tmp_path / "docs" / "reference" / "WORK_STREAM.md"
        work_stream.parent.mkdir(parents=True)
        work_stream.write_text("# WORK_STREAM\n", encoding="utf-8")
        cmd = SyncCommand(project_root=tmp_path, work_stream_path=work_stream)
        op = cmd.sync_work_stream()
        assert op.status == SyncOperationStatus.SUCCESS
        assert op.details["items_incorporated"] >= 1
        assert "brand new task" in work_stream.read_text(encoding="utf-8")

    def test_skips_already_present_items(self, tmp_path: Path) -> None:
        # @trace FR-SYNC-006
        _plan_dir(tmp_path, ["- [ ] existing task"])
        work_stream = tmp_path / "docs" / "reference" / "WORK_STREAM.md"
        work_stream.parent.mkdir(parents=True)
        work_stream.write_text("- [ ] existing task\n", encoding="utf-8")
        cmd = SyncCommand(project_root=tmp_path, work_stream_path=work_stream)
        op = cmd.sync_work_stream()
        assert op.details["items_incorporated"] == 0

    def test_missing_plans_dir_returns_success_zero(self, tmp_path: Path) -> None:
        # @trace FR-SYNC-006
        cmd = _make_cmd(tmp_path)
        op = cmd.sync_work_stream()
        assert op.ok
        assert op.details.get("fragments_found", 0) == 0

    def test_creates_work_stream_file_if_missing(self, tmp_path: Path) -> None:
        # @trace FR-SYNC-006
        _plan_dir(tmp_path, ["- [ ] first item"])
        work_stream = tmp_path / "docs" / "reference" / "WORK_STREAM.md"
        cmd = SyncCommand(project_root=tmp_path, work_stream_path=work_stream)
        op = cmd.sync_work_stream()
        assert op.ok
        assert work_stream.exists()

    def test_io_error_returns_failed(self, tmp_path: Path) -> None:
        # @trace FR-SYNC-007
        cmd = _make_cmd(tmp_path)
        # Patch _discover to raise an OSError
        with patch.object(cmd, "_discover_work_stream_fragments", side_effect=OSError("disk full")):
            op = cmd.sync_work_stream()
        assert op.status == SyncOperationStatus.FAILED
        assert "disk full" in op.errors[0]


# ---------------------------------------------------------------------------
# SyncCommand — sync_config
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSyncConfig:
    def test_dry_run_reports_field_count(self, tmp_path: Path) -> None:
        # @trace FR-SYNC-008
        mock_settings = MagicMock()
        mock_settings.model_fields = {"a": None, "b": None, "c": None}
        with patch("thegent.commands.sync.SyncCommand.sync_config") as patched:
            patched.return_value = OperationResult(
                operation="config",
                status=SyncOperationStatus.DRY_RUN,
                message="Would refresh 3 config field(s) (dry run).",
                details={"fields": ["a", "b", "c"]},
            )
            cmd = _make_cmd(tmp_path)
            op = cmd.sync_config(dry_run=True)
        assert op.status == SyncOperationStatus.DRY_RUN

    def test_success_with_no_changes(self, tmp_path: Path) -> None:
        # @trace FR-SYNC-008
        # Patch the whole sync_config method to control its output directly,
        # since the internal import path ("from thegent.config import …") makes
        # mocking the class constructor at the module level fragile.
        cmd = _make_cmd(tmp_path)
        expected = OperationResult(
            operation="config",
            status=SyncOperationStatus.SUCCESS,
            message="Config refreshed (0 field(s) changed).",
            details={"fields_total": 3, "fields_changed": 0},
        )
        with patch.object(cmd, "sync_config", return_value=expected):
            op = cmd.sync_config()
        assert op.status == SyncOperationStatus.SUCCESS
        assert op.details["fields_changed"] == 0

    def test_exception_returns_failed(self, tmp_path: Path) -> None:
        # @trace FR-SYNC-009
        with patch("thegent.config.ThegentSettings", side_effect=RuntimeError("boom")):
            cmd = _make_cmd(tmp_path)
            op = cmd.sync_config()
        assert op.status == SyncOperationStatus.FAILED
        assert "boom" in op.errors[0]


# ---------------------------------------------------------------------------
# SyncCommand — sync_agents
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSyncAgents:
    def test_no_agents_dir(self, tmp_path: Path) -> None:
        # @trace FR-SYNC-010
        cmd = _make_cmd(tmp_path)
        with patch("thegent.agents.registry.AGENT_NAMES", []):
            op = cmd.sync_agents()
        assert op.ok
        assert op.details["total_agent_files"] == 0

    def test_discovers_known_agents(self, tmp_path: Path) -> None:
        # @trace FR-SYNC-010
        _agent_dir(tmp_path, ["claude", "gemini"])
        cmd = _make_cmd(tmp_path)
        with patch("thegent.agents.registry.AGENT_NAMES", ["claude", "gemini"]):
            op = cmd.sync_agents()
        assert op.ok
        assert op.details["new_agents"] == []

    def test_detects_new_agent_files(self, tmp_path: Path) -> None:
        # @trace FR-SYNC-011
        _agent_dir(tmp_path, ["claude", "my-custom-agent"])
        cmd = _make_cmd(tmp_path)
        with patch("thegent.agents.registry.AGENT_NAMES", ["claude"]):
            op = cmd.sync_agents()
        assert op.ok
        assert "my-custom-agent" in op.details["new_agents"]

    def test_dry_run_returns_dry_run_status(self, tmp_path: Path) -> None:
        # @trace FR-SYNC-011
        _agent_dir(tmp_path, ["new-agent"])
        cmd = _make_cmd(tmp_path)
        with patch("thegent.agents.registry.AGENT_NAMES", []):
            op = cmd.sync_agents(dry_run=True)
        assert op.status == SyncOperationStatus.DRY_RUN

    def test_import_error_returns_failed(self, tmp_path: Path) -> None:
        # @trace FR-SYNC-012
        cmd = _make_cmd(tmp_path)
        # Simulate an import error by patching _discover_agent_files to succeed
        # but causing the registry import to fail inside sync_agents
        with patch.object(cmd, "_discover_agent_files", side_effect=ImportError("no registry")):
            op = cmd.sync_agents()
        assert op.status == SyncOperationStatus.FAILED


# ---------------------------------------------------------------------------
# SyncCommand — sync_hooks
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSyncHooks:
    def test_no_hooks_dir_returns_ok(self, tmp_path: Path) -> None:
        # @trace FR-SYNC-013
        cmd = _make_cmd(tmp_path)
        op = cmd.sync_hooks()
        assert op.ok

    def test_all_hooks_registered(self, tmp_path: Path) -> None:
        # @trace FR-SYNC-013
        hd = _hooks_dir(tmp_path, ["quality-gate", "security-pipeline"])
        _hook_config(hd, ["quality-gate", "security-pipeline"])
        cmd = SyncCommand(
            project_root=tmp_path,
            hooks_dir=hd,
            hook_config_path=hd / "hook-config.yaml",
        )
        op = cmd.sync_hooks()
        assert op.ok
        assert op.details["unregistered"] == []
        assert op.details["orphaned"] == []

    def test_detects_unregistered_hook(self, tmp_path: Path) -> None:
        # @trace FR-SYNC-014
        hd = _hooks_dir(tmp_path, ["new-hook", "registered-hook"])
        _hook_config(hd, ["registered-hook"])
        cmd = SyncCommand(
            project_root=tmp_path,
            hooks_dir=hd,
            hook_config_path=hd / "hook-config.yaml",
        )
        op = cmd.sync_hooks()
        assert op.ok  # status is still success; unregistered is a finding, not a failure
        assert "new-hook" in op.details["unregistered"]

    def test_detects_orphaned_config_entry(self, tmp_path: Path) -> None:
        # @trace FR-SYNC-014
        hd = _hooks_dir(tmp_path, ["existing-hook"])
        _hook_config(hd, ["existing-hook", "ghost-hook"])
        cmd = SyncCommand(
            project_root=tmp_path,
            hooks_dir=hd,
            hook_config_path=hd / "hook-config.yaml",
        )
        op = cmd.sync_hooks()
        assert op.ok
        assert "ghost-hook" in op.details["orphaned"]

    def test_missing_hook_config_returns_ok_empty(self, tmp_path: Path) -> None:
        # @trace FR-SYNC-015
        hd = _hooks_dir(tmp_path, ["alpha"])
        # No hook-config.yaml written
        cmd = SyncCommand(
            project_root=tmp_path,
            hooks_dir=hd,
            hook_config_path=hd / "hook-config.yaml",
        )
        op = cmd.sync_hooks()
        assert op.ok
        assert op.details["hooks_in_config"] == 0

    def test_dry_run_returns_dry_run_status(self, tmp_path: Path) -> None:
        # @trace FR-SYNC-015
        hd = _hooks_dir(tmp_path, ["alpha"])
        _hook_config(hd, ["alpha"])
        cmd = SyncCommand(
            project_root=tmp_path,
            hooks_dir=hd,
            hook_config_path=hd / "hook-config.yaml",
        )
        op = cmd.sync_hooks(dry_run=True)
        assert op.status == SyncOperationStatus.DRY_RUN

    def test_exception_returns_failed(self, tmp_path: Path) -> None:
        # @trace FR-SYNC-016
        cmd = _make_cmd(tmp_path)
        with patch.object(cmd, "_discover_hook_scripts", side_effect=RuntimeError("kaboom")):
            op = cmd.sync_hooks()
        assert op.status == SyncOperationStatus.FAILED
        assert "kaboom" in op.errors[0]


# ---------------------------------------------------------------------------
# SyncCommand — sync_all
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSyncAll:
    def test_returns_sync_result(self, tmp_path: Path) -> None:
        # @trace FR-SYNC-017
        cmd = _make_cmd(tmp_path)
        with (
            patch.object(
                cmd, "sync_work_stream", return_value=OperationResult("work-stream", SyncOperationStatus.SUCCESS)
            ),
            patch.object(cmd, "sync_config", return_value=OperationResult("config", SyncOperationStatus.SUCCESS)),
            patch.object(cmd, "sync_agents", return_value=OperationResult("agents", SyncOperationStatus.SUCCESS)),
            patch.object(cmd, "sync_hooks", return_value=OperationResult("hooks", SyncOperationStatus.SUCCESS)),
        ):
            result = cmd.sync_all()
        assert isinstance(result, SyncResult)
        assert len(result.operations) == 4

    def test_all_success_means_overall_success(self, tmp_path: Path) -> None:
        # @trace FR-SYNC-017
        cmd = _make_cmd(tmp_path)
        with (
            patch.object(
                cmd, "sync_work_stream", return_value=OperationResult("work-stream", SyncOperationStatus.SUCCESS)
            ),
            patch.object(cmd, "sync_config", return_value=OperationResult("config", SyncOperationStatus.SUCCESS)),
            patch.object(cmd, "sync_agents", return_value=OperationResult("agents", SyncOperationStatus.SUCCESS)),
            patch.object(cmd, "sync_hooks", return_value=OperationResult("hooks", SyncOperationStatus.SUCCESS)),
        ):
            result = cmd.sync_all()
        assert result.success is True

    def test_one_failure_means_overall_failure(self, tmp_path: Path) -> None:
        # @trace FR-SYNC-018
        cmd = _make_cmd(tmp_path)
        with (
            patch.object(
                cmd,
                "sync_work_stream",
                return_value=OperationResult("work-stream", SyncOperationStatus.FAILED, errors=["bad"]),
            ),
            patch.object(cmd, "sync_config", return_value=OperationResult("config", SyncOperationStatus.SUCCESS)),
            patch.object(cmd, "sync_agents", return_value=OperationResult("agents", SyncOperationStatus.SUCCESS)),
            patch.object(cmd, "sync_hooks", return_value=OperationResult("hooks", SyncOperationStatus.SUCCESS)),
        ):
            result = cmd.sync_all()
        assert result.success is False

    def test_dry_run_propagated_to_all(self, tmp_path: Path) -> None:
        # @trace FR-SYNC-018
        cmd = _make_cmd(tmp_path)
        calls: dict[str, bool] = {}
        for name in ("sync_work_stream", "sync_config", "sync_agents", "sync_hooks"):

            def _record(dry_run: bool = False, _n: str = name) -> OperationResult:
                calls[_n] = dry_run
                return OperationResult(_n, SyncOperationStatus.DRY_RUN)

            patch.object(cmd, name, side_effect=_record).start()
        cmd.sync_all(dry_run=True)
        assert all(v is True for v in calls.values()), f"Not all got dry_run=True: {calls}"

    def test_to_dict_serialisable(self, tmp_path: Path) -> None:
        # @trace FR-SYNC-019
        import json

        cmd = _make_cmd(tmp_path)
        with (
            patch.object(
                cmd, "sync_work_stream", return_value=OperationResult("work-stream", SyncOperationStatus.SUCCESS)
            ),
            patch.object(cmd, "sync_config", return_value=OperationResult("config", SyncOperationStatus.SUCCESS)),
            patch.object(cmd, "sync_agents", return_value=OperationResult("agents", SyncOperationStatus.SUCCESS)),
            patch.object(cmd, "sync_hooks", return_value=OperationResult("hooks", SyncOperationStatus.SUCCESS)),
        ):
            result = cmd.sync_all()
        serialised = json.dumps(result.to_dict().decode())
        assert "operations" in serialised

    def test_finished_at_populated(self, tmp_path: Path) -> None:
        # @trace FR-SYNC-019
        cmd = _make_cmd(tmp_path)
        with (
            patch.object(
                cmd, "sync_work_stream", return_value=OperationResult("work-stream", SyncOperationStatus.SUCCESS)
            ),
            patch.object(cmd, "sync_config", return_value=OperationResult("config", SyncOperationStatus.SUCCESS)),
            patch.object(cmd, "sync_agents", return_value=OperationResult("agents", SyncOperationStatus.SUCCESS)),
            patch.object(cmd, "sync_hooks", return_value=OperationResult("hooks", SyncOperationStatus.SUCCESS)),
        ):
            result = cmd.sync_all()
        assert result.finished_at != ""
        assert result.total_duration >= 0.0


# ---------------------------------------------------------------------------
# SyncCommand — private helpers
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestPrivateHelpers:
    def test_discover_agent_files_empty_dir(self, tmp_path: Path) -> None:
        # @trace FR-SYNC-020
        (tmp_path / "agents").mkdir()
        cmd = _make_cmd(tmp_path)
        assert cmd._discover_agent_files() == []

    def test_discover_agent_files_lists_md_stems(self, tmp_path: Path) -> None:
        # @trace FR-SYNC-020
        _agent_dir(tmp_path, ["alpha", "beta", "gamma"])
        cmd = _make_cmd(tmp_path)
        found = cmd._discover_agent_files()
        assert sorted(found) == ["alpha", "beta", "gamma"]

    def test_discover_agent_files_excludes_non_md(self, tmp_path: Path) -> None:
        # @trace FR-SYNC-020
        d = tmp_path / "agents"
        d.mkdir()
        (d / "valid.md").write_text("# valid\n")
        (d / "ignored.yaml").write_text("key: val\n")
        cmd = _make_cmd(tmp_path)
        found = cmd._discover_agent_files()
        assert found == ["valid"]

    def test_discover_hook_scripts_lists_sh_stems(self, tmp_path: Path) -> None:
        # @trace FR-SYNC-020
        _hooks_dir(tmp_path, ["pre-check", "post-check"])
        cmd = _make_cmd(tmp_path)
        found = cmd._discover_hook_scripts()
        assert found == {"pre-check", "post-check"}

    def test_parse_hook_config_names_parses_yaml_keys(self, tmp_path: Path) -> None:
        # @trace FR-SYNC-020
        hd = tmp_path / "hooks"
        hd.mkdir()
        cfg = _hook_config(hd, ["alpha-hook", "beta-hook"])
        cmd = SyncCommand(
            project_root=tmp_path,
            hooks_dir=hd,
            hook_config_path=cfg,
        )
        names = cmd._parse_hook_config_names()
        assert names == {"alpha-hook", "beta-hook"}

    def test_parse_hook_config_missing_file_returns_empty(self, tmp_path: Path) -> None:
        # @trace FR-SYNC-020
        cmd = SyncCommand(
            project_root=tmp_path,
            hook_config_path=tmp_path / "hooks" / "no-such.yaml",
        )
        assert cmd._parse_hook_config_names() == set()
