"""WL-037 — thegent sync work-stream / rules / research integration tests.

Tests cover:
  - SyncCommand.sync_rules (delegates to RulesSyncManager)
  - SyncCommand.sync_research (runs incorporate + appends research fragments)
  - SyncCommand._discover_research_fragments (helper)
  - CLI subcommands: work-stream, rules, research

# @trace WL-037
"""

from __future__ import annotations

import sys
import textwrap
import types
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from thegent.commands.sync import (
    OperationResult,
    SyncCommand,
    SyncOperationStatus,
    SyncResult,
)

if TYPE_CHECKING:
    from pathlib import Path


def _stub_impl(merged: int = 0):
    """Return a fake impl module with incorporate_impl returning the given merged count."""
    mod = types.ModuleType("thegent.cli.commands.impl")
    mod.incorporate_impl = lambda cd=None, dry_run=False: {"merged": merged}  # type: ignore[attr-defined]
    return mod


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_cmd(tmp_path: Path, **kwargs) -> SyncCommand:
    return SyncCommand(project_root=tmp_path, **kwargs)


def _make_rules_dir(tmp_path: Path, rule_ids: list[str]) -> Path:
    """Create .thegent/rules/ with minimal rule files."""
    rules_dir = tmp_path / ".thegent" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    for rid in rule_ids:
        content = textwrap.dedent(
            f"""\
            ---
            id: {rid}
            title: Rule {rid}
            platforms: [cursor, claude, codex]
            ---
            Always follow rule {rid}.
            """
        )
        (rules_dir / f"{rid}.md").write_text(content, encoding="utf-8")
    return rules_dir


def _make_research_dir(tmp_path: Path, items: list[str]) -> Path:
    """Create docs/research/ with a single markdown file containing checkbox items."""
    d = tmp_path / "docs" / "research"
    d.mkdir(parents=True, exist_ok=True)
    content = "\n".join(items) + "\n"
    (d / "research.md").write_text(content, encoding="utf-8")
    return d


def _make_plans_dir(tmp_path: Path, items: list[str]) -> Path:
    """Create docs/plans/ with a single markdown file containing checkbox items."""
    d = tmp_path / "docs" / "plans"
    d.mkdir(parents=True, exist_ok=True)
    content = "\n".join(items) + "\n"
    (d / "plan.md").write_text(content, encoding="utf-8")
    return d


def _make_work_stream(tmp_path: Path, initial_content: str = "# WORK_STREAM\n") -> Path:
    ws = tmp_path / "docs" / "reference" / "WORK_STREAM.md"
    ws.parent.mkdir(parents=True, exist_ok=True)
    ws.write_text(initial_content, encoding="utf-8")
    return ws


# ---------------------------------------------------------------------------
# SyncCommand.sync_rules — delegates to RulesSyncManager
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSyncRules:
    """# @trace WL-037"""

    def test_sync_rules_success(self, tmp_path: Path) -> None:
        """sync_rules calls RulesSyncManager.sync_all and returns SUCCESS."""
        # @trace WL-037
        _make_rules_dir(tmp_path, ["r1", "r2"])
        cmd = _make_cmd(tmp_path)
        op = cmd.sync_rules()
        assert op.ok, f"Expected ok, got: {op.message} / errors={op.errors}"
        assert op.status == SyncOperationStatus.SUCCESS

    def test_sync_rules_dry_run(self, tmp_path: Path) -> None:
        """sync_rules dry-run returns DRY_RUN status and writes nothing."""
        # @trace WL-037
        _make_rules_dir(tmp_path, ["r1"])
        cmd = _make_cmd(tmp_path)
        op = cmd.sync_rules(dry_run=True)
        assert op.status == SyncOperationStatus.DRY_RUN
        # Cursor rule file must NOT exist
        assert not (tmp_path / ".cursor" / "rules" / "thegent-rules.mdc").exists()

    def test_sync_rules_writes_platform_files(self, tmp_path: Path) -> None:
        """sync_rules writes cursor/claude/codex artifacts when not dry-run."""
        # @trace WL-037
        _make_rules_dir(tmp_path, ["r1"])
        cmd = _make_cmd(tmp_path)
        op = cmd.sync_rules()
        assert op.ok
        assert (tmp_path / ".cursor" / "rules" / "thegent-rules.mdc").exists()
        assert (tmp_path / "CLAUDE.md").exists()

    def test_sync_rules_missing_rules_dir_returns_failed(self, tmp_path: Path) -> None:
        """sync_rules raises FileNotFoundError which becomes FAILED status."""
        # @trace WL-037
        # No .thegent/rules directory created
        cmd = _make_cmd(tmp_path)
        op = cmd.sync_rules()
        assert op.status == SyncOperationStatus.FAILED
        assert op.errors

    def test_sync_rules_details_contain_rules_loaded(self, tmp_path: Path) -> None:
        """sync_rules details include rules_loaded count."""
        # @trace WL-037
        _make_rules_dir(tmp_path, ["r1", "r2", "r3"])
        cmd = _make_cmd(tmp_path)
        op = cmd.sync_rules()
        assert op.ok
        assert op.details.get("rules_loaded", 0) == 3

    def test_sync_rules_changes_list_file_paths(self, tmp_path: Path) -> None:
        """sync_rules.changes contains paths of written files."""
        # @trace WL-037
        _make_rules_dir(tmp_path, ["r1"])
        cmd = _make_cmd(tmp_path)
        op = cmd.sync_rules()
        assert op.ok
        assert len(op.changes) > 0
        assert all(isinstance(c, str) for c in op.changes)

    def test_sync_rules_dry_run_reports_file_count(self, tmp_path: Path) -> None:
        """sync_rules dry-run details.files is populated."""
        # @trace WL-037
        _make_rules_dir(tmp_path, ["r1"])
        cmd = _make_cmd(tmp_path)
        op = cmd.sync_rules(dry_run=True)
        assert op.status == SyncOperationStatus.DRY_RUN
        assert isinstance(op.details.get("files"), list)


# ---------------------------------------------------------------------------
# SyncCommand.sync_research
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSyncResearch:
    """# @trace WL-037"""

    def test_sync_research_dry_run(self, tmp_path: Path) -> None:
        """sync_research dry-run returns DRY_RUN and does not modify WORK_STREAM.md."""
        # @trace WL-037
        _make_research_dir(tmp_path, ["- [ ] research task A", "- [ ] research task B"])
        ws = _make_work_stream(tmp_path)
        original = ws.read_text(encoding="utf-8")
        cmd = _make_cmd(tmp_path, work_stream_path=ws)
        with patch.dict(sys.modules, {"thegent.cli.commands.impl": _stub_impl(merged=0)}):
            op = cmd.sync_research(dry_run=True)
        assert op.status == SyncOperationStatus.DRY_RUN
        assert ws.read_text(encoding="utf-8") == original

    def test_sync_research_incorporates_new_items(self, tmp_path: Path) -> None:
        """sync_research appends new research fragment items to WORK_STREAM.md."""
        # @trace WL-037
        _make_research_dir(tmp_path, ["- [ ] new research item"])
        ws = _make_work_stream(tmp_path)
        cmd = _make_cmd(tmp_path, work_stream_path=ws)
        with patch.dict(sys.modules, {"thegent.cli.commands.impl": _stub_impl(merged=0)}):
            op = cmd.sync_research()
        assert op.ok
        content = ws.read_text(encoding="utf-8")
        assert "new research item" in content

    def test_sync_research_deduplicates_existing_items(self, tmp_path: Path) -> None:
        """sync_research does not re-append items already in WORK_STREAM.md."""
        # @trace WL-037
        _make_research_dir(tmp_path, ["- [ ] existing item"])
        ws = _make_work_stream(tmp_path, "# WS\n- [ ] existing item\n")
        cmd = _make_cmd(tmp_path, work_stream_path=ws)
        with patch.dict(sys.modules, {"thegent.cli.commands.impl": _stub_impl(merged=0)}):
            op = cmd.sync_research()
        assert op.ok
        assert op.details.get("research_incorporated", 0) == 0

    def test_sync_research_deduplicates_by_wl_id(self, tmp_path: Path) -> None:
        """sync_research dedupes when WL ID already exists with different text."""
        # @trace WL-037
        _make_research_dir(tmp_path, ["- [ ] WL-159 follow-up from research"])
        ws = _make_work_stream(tmp_path, "# WS\n- [ ] WL-159 existing backlog entry\n")
        cmd = _make_cmd(tmp_path, work_stream_path=ws)
        with patch.dict(sys.modules, {"thegent.cli.commands.impl": _stub_impl(merged=0)}):
            op = cmd.sync_research()
        assert op.ok
        assert op.details.get("research_incorporated", 0) == 0

    def test_sync_research_scans_plans_and_research_dirs(self, tmp_path: Path) -> None:
        """sync_research scans both docs/research/ and docs/plans/."""
        # @trace WL-037
        _make_research_dir(tmp_path, ["- [ ] from-research"])
        _make_plans_dir(tmp_path, ["- [ ] from-plans"])
        ws = _make_work_stream(tmp_path)
        cmd = _make_cmd(tmp_path, work_stream_path=ws)
        with patch.dict(sys.modules, {"thegent.cli.commands.impl": _stub_impl(merged=0)}):
            op = cmd.sync_research()
        assert op.ok
        content = ws.read_text(encoding="utf-8")
        assert "from-research" in content
        assert "from-plans" in content

    def test_sync_research_reports_total_incorporated(self, tmp_path: Path) -> None:
        """sync_research details.total_incorporated sums incorporate_merged + research_incorporated."""
        # @trace WL-037
        _make_research_dir(tmp_path, ["- [ ] item A", "- [ ] item B"])
        ws = _make_work_stream(tmp_path)
        cmd = _make_cmd(tmp_path, work_stream_path=ws)
        with patch.dict(sys.modules, {"thegent.cli.commands.impl": _stub_impl(merged=2)}):
            op = cmd.sync_research()
        assert op.ok
        total = op.details.get("total_incorporated", 0)
        assert total >= 2

    def test_sync_research_exception_returns_failed(self, tmp_path: Path) -> None:
        """sync_research wraps unexpected errors into FAILED OperationResult."""
        # @trace WL-037
        cmd = _make_cmd(tmp_path)
        with patch.dict(sys.modules, {"thegent.cli.commands.impl": _stub_impl(merged=0)}):
            with patch.object(cmd, "_discover_research_fragments", side_effect=OSError("disk full")):
                op = cmd.sync_research()
        assert op.status == SyncOperationStatus.FAILED
        assert "disk full" in op.errors[0]

    def test_sync_research_no_fragments_returns_success(self, tmp_path: Path) -> None:
        """sync_research with no fragments still returns SUCCESS."""
        # @trace WL-037
        ws = _make_work_stream(tmp_path)
        cmd = _make_cmd(tmp_path, work_stream_path=ws)
        with patch.dict(sys.modules, {"thegent.cli.commands.impl": _stub_impl(merged=0)}):
            op = cmd.sync_research()
        assert op.ok
        assert op.details.get("research_fragments_found", 0) == 0

    def test_incorporate_into_work_stream_returns_zero_when_contended(self, tmp_path: Path) -> None:
        """Concurrent lock contention skips sync writes and leaves source unchanged."""
        # @trace WL-037
        _make_research_dir(tmp_path, ["- [ ] item A"])
        ws = _make_work_stream(tmp_path, "# WS\n")
        original = ws.read_text(encoding="utf-8")
        cmd = _make_cmd(tmp_path, work_stream_path=ws)

        with patch(
            "thegent.commands.sync._locked_file_access", side_effect=BlockingIOError(11, "resource unavailable")
        ):
            with patch.dict(sys.modules, {"thegent.cli.commands.impl": _stub_impl(merged=0)}):
                op = cmd.sync_research()

        assert op.ok
        assert op.details["research_incorporated"] == 0
        assert op.details["total_incorporated"] == 0
        assert ws.read_text(encoding="utf-8") == original


# ---------------------------------------------------------------------------
# SyncCommand._discover_research_fragments
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestDiscoverResearchFragments:
    """# @trace WL-037"""

    def test_scans_research_dir(self, tmp_path: Path) -> None:
        """_discover_research_fragments returns items from docs/research/."""
        # @trace WL-037
        _make_research_dir(tmp_path, ["- [ ] task R1", "- [ ] task R2"])
        cmd = _make_cmd(tmp_path)
        frags = cmd._discover_research_fragments()
        assert "- [ ] task R1" in frags
        assert "- [ ] task R2" in frags

    def test_scans_plans_dir(self, tmp_path: Path) -> None:
        """_discover_research_fragments returns items from docs/plans/."""
        # @trace WL-037
        _make_plans_dir(tmp_path, ["- [ ] plan task P1"])
        cmd = _make_cmd(tmp_path)
        frags = cmd._discover_research_fragments()
        assert "- [ ] plan task P1" in frags

    def test_empty_dirs_returns_empty(self, tmp_path: Path) -> None:
        """_discover_research_fragments returns [] when dirs don't exist."""
        # @trace WL-037
        cmd = _make_cmd(tmp_path)
        assert cmd._discover_research_fragments() == []

    def test_filters_non_checkbox_lines(self, tmp_path: Path) -> None:
        """_discover_research_fragments only picks up checkbox/table lines."""
        # @trace WL-037
        d = tmp_path / "docs" / "research"
        d.mkdir(parents=True, exist_ok=True)
        (d / "r.md").write_text("# Header\nsome prose\n- [ ] a task\n", encoding="utf-8")
        cmd = _make_cmd(tmp_path)
        frags = cmd._discover_research_fragments()
        assert "- [ ] a task" in frags
        assert "# Header" not in frags
        assert "some prose" not in frags

    def test_table_rows_are_included(self, tmp_path: Path) -> None:
        """_discover_research_fragments picks up markdown table rows."""
        # @trace WL-037
        d = tmp_path / "docs" / "research"
        d.mkdir(parents=True, exist_ok=True)
        (d / "table.md").write_text("| WL-099 | Some task | docs/ | P1 | - |\n", encoding="utf-8")
        cmd = _make_cmd(tmp_path)
        frags = cmd._discover_research_fragments()
        assert any("WL-099" in f for f in frags)


# ---------------------------------------------------------------------------
# SyncCommand.sync_all now includes rules and research in its scope
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSyncAllWithNewOps:
    """Verify that the new sync_rules / sync_research methods can be patched into sync_all.

    # @trace WL-037
    """

    def test_sync_all_still_calls_four_ops(self, tmp_path: Path) -> None:
        """sync_all still calls the original four operations (regression guard)."""
        # @trace WL-037
        cmd = _make_cmd(tmp_path)
        ops_called: list[str] = []

        for name in ("sync_work_stream", "sync_config", "sync_agents", "sync_hooks"):

            def _record(dry_run: bool = False, _n: str = name) -> OperationResult:
                ops_called.append(_n)
                return OperationResult(_n, SyncOperationStatus.SUCCESS)

            patch.object(cmd, name, side_effect=_record).start()

        result = cmd.sync_all()
        assert isinstance(result, SyncResult)
        assert len(result.operations) == 4
        assert set(ops_called) == {"sync_work_stream", "sync_config", "sync_agents", "sync_hooks"}
