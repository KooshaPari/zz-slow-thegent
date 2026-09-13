"""Unit tests for smart_prune Triple-Lock and protected-process logic.

Covers:
- _is_protected_process guard (all protected names, edge cases)
- SmartPruner.detect_completion (Triple-Lock 2)
- SmartPruner.check_docs_written (Triple-Lock 3)
- SmartPruner.check_triple_lock (all three locks together)
- SmartPruner.run_cycle dry_run / yes / confirmation logic
- mcp_prune protected-process final guard
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import pytest

from thegent.orchestration.pruning.smart_prune import (
    IDLE_COUNT_THRESHOLD,
    PROTECTED_PROCESS_NAMES,
    SessionSnapshot,
    SmartPruner,
    _is_protected_process,
    smart_prune_main,
)

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# _is_protected_process
# ---------------------------------------------------------------------------


class TestIsProtectedProcess:
    """Tests for _is_protected_process guard."""

    @pytest.mark.parametrize(
        "name",
        [
            "cursor-agent",
            "cursor-agent --resume=abc123",
            "/usr/local/bin/cursor-agent",
            "thegent",
            "thegent run --bg",
            "claude",
            "/opt/claude-code/bin/claude",
            "codex",
            "/usr/local/bin/codex run",
            "droid",
            "bash",
            "/bin/bash",
            "zsh",
            "/usr/bin/zsh",
            "ghostty",
            "terminal",
            "iterm",
            "CURSOR-AGENT",  # case insensitive
            "BASH",
            "ZSH",
        ],
    )
    def test_protected_names_are_blocked(self, name: str) -> None:
        assert _is_protected_process(name) is True, f"Expected {name!r} to be protected"

    @pytest.mark.parametrize(
        "name",
        [
            "node",
            "npm",
            "bun",
            "deno",
            "pyright-langserver",
            "typescript-language-server",
            "tsserver.js",
            "@playwright/mcp",
            "context7-mcp",
            "cc-status",
            "",
            "python3",
            "uvicorn",
        ],
    )
    def test_non_protected_names_are_allowed(self, name: str) -> None:
        assert _is_protected_process(name) is False, (
            f"Expected {name!r} to NOT be protected"
        )

    def test_empty_string_not_protected(self) -> None:
        assert _is_protected_process("") is False

    def test_all_protected_constants_covered(self) -> None:
        """Every entry in PROTECTED_PROCESS_NAMES must be caught."""
        for protected in PROTECTED_PROCESS_NAMES:
            assert _is_protected_process(protected) is True, f"{protected!r} not caught"

    def test_partial_path_with_protected_name(self) -> None:
        assert _is_protected_process("/usr/bin/zsh") is True
        assert (
            _is_protected_process("/Applications/Ghostty.app/Contents/MacOS/ghostty")
            is True
        )


# ---------------------------------------------------------------------------
# SmartPruner.detect_completion (Triple-Lock 2)
# ---------------------------------------------------------------------------


class TestDetectCompletion:
    """Tests for completion marker detection."""

    def setup_method(self) -> None:
        with patch("thegent.orchestration.pruning.smart_prune.ThegentSettings"):
            self.pruner = SmartPruner.__new__(SmartPruner)
            self.pruner.settings = MagicMock()
            self.pruner.snapshots = {}

    @pytest.mark.parametrize(
        "output",
        [
            "... some work ...\nTask finished\n",
            "... Summary: all done\n",
            "completed successfully\n",
            "Cursor turned off\n",
            "All good (done)\n",
            "[done]\n",
            "Task complete.\n",
            "Implementation finished.\n",
            "Migration successful.\n",
        ],
    )
    def test_completion_markers_detected(self, output: str) -> None:
        assert self.pruner.detect_completion(output) is True

    def test_no_completion_marker(self) -> None:
        assert self.pruner.detect_completion("Still working...") is False

    def test_marker_in_last_1000_chars(self) -> None:
        # Marker beyond 1000 chars from end should NOT match
        long_prefix = "A" * 2000
        assert self.pruner.detect_completion(long_prefix + " nothing here") is False

    def test_marker_within_last_1000_chars(self) -> None:
        long_prefix = "A" * 2000
        assert self.pruner.detect_completion(long_prefix + " Task finished") is True


# ---------------------------------------------------------------------------
# SmartPruner.check_docs_written (Triple-Lock 3)
# ---------------------------------------------------------------------------


class TestCheckDocsWritten:
    """Tests for docs-written check."""

    def test_doc_modified_after_start(self, tmp_path: Path) -> None:
        research_dir = tmp_path / "docs" / "research"
        research_dir.mkdir(parents=True)
        doc = research_dir / "CONVERSATION_DUMP_2026-01-01.md"
        doc.write_text("# Dump\n")

        # Use a start time in the past so the file is "newer"
        start_time = time.time() - 10
        with patch("thegent.orchestration.pruning.smart_prune.ThegentSettings"):
            pruner = SmartPruner.__new__(SmartPruner)
            pruner.settings = MagicMock()
            pruner.snapshots = {}
            pruner.project_root = tmp_path

        assert pruner.check_docs_written(start_time) is True

    def test_doc_modified_before_start(self, tmp_path: Path) -> None:
        research_dir = tmp_path / "docs" / "research"
        research_dir.mkdir(parents=True)
        doc = research_dir / "OLD.md"
        doc.write_text("# Old\n")

        # Start time is well in the future relative to the file's mtime
        start_time = time.time() + 9999
        with patch("thegent.orchestration.pruning.smart_prune.ThegentSettings"):
            pruner = SmartPruner.__new__(SmartPruner)
            pruner.settings = MagicMock()
            pruner.snapshots = {}
            pruner.project_root = tmp_path

        assert pruner.check_docs_written(start_time) is False

    def test_no_docs_dirs(self, tmp_path: Path) -> None:
        with patch("thegent.orchestration.pruning.smart_prune.ThegentSettings"):
            pruner = SmartPruner.__new__(SmartPruner)
            pruner.settings = MagicMock()
            pruner.snapshots = {}
            pruner.project_root = tmp_path

        assert pruner.check_docs_written(time.time() - 10) is False


# ---------------------------------------------------------------------------
# SmartPruner.check_triple_lock
# ---------------------------------------------------------------------------


class TestCheckTripleLock:
    """Tests for the combined Triple-Lock evaluation."""

    def _make_pruner(self, tmp_path: Path) -> SmartPruner:
        with patch("thegent.orchestration.pruning.smart_prune.ThegentSettings"):
            pruner = SmartPruner.__new__(SmartPruner)
            pruner.settings = MagicMock()
            pruner.snapshots = {}
            pruner.project_root = tmp_path
        return pruner

    def _make_snap(self, idle_count: int = 0) -> SessionSnapshot:
        return SessionSnapshot(
            session_id="test-123",
            last_output="old output",
            last_check_time=time.time(),
            idle_count=idle_count,
        )

    def test_all_locks_pass(self, tmp_path: Path) -> None:
        pruner = self._make_pruner(tmp_path)
        # Set up a doc modified after session start
        research = tmp_path / "docs" / "research"
        research.mkdir(parents=True)
        (research / "dump.md").write_text("done")

        snap = self._make_snap(idle_count=IDLE_COUNT_THRESHOLD)
        output = "Task finished\n"
        st = time.time() - 10
        now = time.time()

        is_idle, is_complete, docs = pruner.check_triple_lock(snap, output, st, now)
        assert is_idle is True
        assert is_complete is True
        assert docs is True

    def test_idle_lock_fails_when_too_few_cycles(self, tmp_path: Path) -> None:
        pruner = self._make_pruner(tmp_path)
        snap = self._make_snap(idle_count=IDLE_COUNT_THRESHOLD - 1)
        output = "Task finished\n"
        is_idle, _is_complete, _ = pruner.check_triple_lock(
            snap, output, time.time() - 10, time.time()
        )
        assert is_idle is False

    def test_completion_lock_fails_when_no_marker(self, tmp_path: Path) -> None:
        pruner = self._make_pruner(tmp_path)
        snap = self._make_snap(idle_count=IDLE_COUNT_THRESHOLD)
        output = "Still working..."
        _, is_complete, _ = pruner.check_triple_lock(
            snap, output, time.time() - 10, time.time()
        )
        assert is_complete is False

    def test_docs_lock_fails_when_no_docs(self, tmp_path: Path) -> None:
        pruner = self._make_pruner(tmp_path)
        snap = self._make_snap(idle_count=IDLE_COUNT_THRESHOLD)
        output = "Task finished\n"
        _, _, docs = pruner.check_triple_lock(
            snap, output, time.time() + 9999, time.time()
        )
        assert docs is False


# ---------------------------------------------------------------------------
# SmartPruner.run_cycle — dry_run / yes / confirmation
# ---------------------------------------------------------------------------


class TestRunCycleDryRun:
    """Tests that run_cycle never kills without explicit confirmation."""

    def _make_pruner_with_eligible_session(
        self, tmp_path: Path
    ) -> tuple[SmartPruner, dict[str, Any]]:
        """Return a pruner and a fake session that passes all Triple-Lock criteria."""
        research = tmp_path / "docs" / "research"
        research.mkdir(parents=True)
        (research / "dump.md").write_text("done")

        with (
            patch("thegent.orchestration.pruning.smart_prune.ThegentSettings"),
            patch("thegent.orchestration.pruning.smart_prune.ps_impl") as mock_ps,
            patch(
                "thegent.orchestration.pruning.smart_prune.list_tmux_panes"
            ) as mock_panes,
            patch(
                "thegent.orchestration.pruning.smart_prune.capture_tmux_pane"
            ) as mock_cap,
        ):
            pruner = SmartPruner.__new__(SmartPruner)
            pruner.settings = MagicMock(platform="linux")
            pruner.project_root = tmp_path
            pruner.state_file = tmp_path / "state.json"
            pruner.snapshots = {}

            session: dict[str, Any] = {
                "id": "sess-eligible",
                "pid": 9999,
                "agent": "some-lsp-worker",
                "status": "running",
                "started_at_utc": None,
                "tty": "",
                "source": "other",
            }

            # Pre-load a snapshot that is already idle enough
            pruner.snapshots["sess-eligible"] = SessionSnapshot(
                session_id="sess-eligible",
                last_output="Task finished\n",
                last_check_time=time.time() - 90,
                idle_count=IDLE_COUNT_THRESHOLD + 1,
            )

            mock_ps.return_value = [session]
            mock_panes.return_value = []
            mock_cap.return_value = "Task finished\n"

        return pruner, session

    def test_dry_run_does_not_kill(self, tmp_path: Path) -> None:
        """dry_run=True must never trigger _prune_session."""
        pruner, session = self._make_eligible_pruner(tmp_path)

        with (
            patch.object(pruner, "_prune_session") as mock_prune,
            patch(
                "thegent.orchestration.pruning.smart_prune.ps_impl",
                return_value=[session],
            ),
            patch(
                "thegent.orchestration.pruning.smart_prune.list_tmux_panes",
                return_value=[],
            ),
            patch(
                "thegent.orchestration.pruning.smart_prune.capture_tmux_pane",
                return_value="Task finished\n",
            ),
        ):
            results = pruner.run_cycle(force_prune=True, dry_run=True, yes=True)

        mock_prune.assert_not_called()
        assert results["dry_run"] is True

    def test_no_yes_does_not_kill(self, tmp_path: Path) -> None:
        """Without yes=True, run_cycle must not kill even when all locks pass."""
        pruner, session = self._make_eligible_pruner(tmp_path)

        with (
            patch.object(pruner, "_prune_session") as mock_prune,
            patch(
                "thegent.orchestration.pruning.smart_prune.ps_impl",
                return_value=[session],
            ),
            patch(
                "thegent.orchestration.pruning.smart_prune.list_tmux_panes",
                return_value=[],
            ),
            patch(
                "thegent.orchestration.pruning.smart_prune.capture_tmux_pane",
                return_value="Task finished\n",
            ),
        ):
            results = pruner.run_cycle(force_prune=True, dry_run=False, yes=False)

        mock_prune.assert_not_called()
        assert results["pruned"] == 0

    def test_force_and_yes_kills(self, tmp_path: Path) -> None:
        """force=True + yes=True must call _prune_session for eligible sessions."""
        pruner, session = self._make_eligible_pruner(tmp_path)

        with (
            patch.object(pruner, "_prune_session") as mock_prune,
            patch(
                "thegent.orchestration.pruning.smart_prune.ps_impl",
                return_value=[session],
            ),
            patch(
                "thegent.orchestration.pruning.smart_prune.list_tmux_panes",
                return_value=[],
            ),
            patch(
                "thegent.orchestration.pruning.smart_prune.capture_tmux_pane",
                return_value="Task finished\n",
            ),
        ):
            results = pruner.run_cycle(force_prune=True, dry_run=False, yes=True)

        mock_prune.assert_called_once()
        assert results["pruned"] == 1

    def _make_eligible_pruner(
        self, tmp_path: Path
    ) -> tuple[SmartPruner, dict[str, Any]]:
        research = tmp_path / "docs" / "research"
        research.mkdir(parents=True)
        (research / "dump.md").write_text("done")

        pruner = SmartPruner.__new__(SmartPruner)
        pruner.settings = MagicMock(platform="linux")
        pruner.project_root = tmp_path
        pruner.state_file = tmp_path / "state.json"
        pruner.snapshots = {}

        session: dict[str, Any] = {
            "id": "sess-eligible",
            "pid": 9999,
            "agent": "some-lsp-worker",
            "status": "running",
            "started_at_utc": None,
            "tty": "",
            "source": "other",
        }

        # Pre-load snapshot that is idle enough and has completion signal
        pruner.snapshots["sess-eligible"] = SessionSnapshot(
            session_id="sess-eligible",
            last_output="Task finished\n",
            last_check_time=time.time() - 90,
            idle_count=IDLE_COUNT_THRESHOLD + 1,
        )

        return pruner, session


# ---------------------------------------------------------------------------
# Protected sessions are skipped in run_cycle
# ---------------------------------------------------------------------------


class TestRunCycleProtectedSessions:
    """run_cycle must skip sessions whose agent name is protected."""

    @pytest.mark.parametrize(
        "agent_name",
        [
            "cursor-agent",
            "claude",
            "codex",
            "droid",
            "bash",
            "thegent",
        ],
    )
    def test_protected_agent_is_skipped(self, agent_name: str, tmp_path: Path) -> None:
        pruner = SmartPruner.__new__(SmartPruner)
        pruner.settings = MagicMock(platform="linux")
        pruner.project_root = tmp_path
        pruner.state_file = tmp_path / "state.json"
        pruner.snapshots = {}

        session: dict[str, Any] = {
            "id": "sess-protected",
            "pid": 1234,
            "agent": agent_name,
            "status": "running",
            "started_at_utc": None,
            "tty": "",
        }

        with (
            patch.object(pruner, "_prune_session") as mock_prune,
            patch(
                "thegent.orchestration.pruning.smart_prune.ps_impl",
                return_value=[session],
            ),
            patch(
                "thegent.orchestration.pruning.smart_prune.list_tmux_panes",
                return_value=[],
            ),
        ):
            results = pruner.run_cycle(force_prune=True, dry_run=False, yes=True)

        mock_prune.assert_not_called()
        assert results["pruned"] == 0
        assert results["kept"] == 1


# ---------------------------------------------------------------------------
# _prune_session protected-process final guard
# ---------------------------------------------------------------------------


class TestPruneSessionProtectedGuard:
    """_prune_session must abort when agent is protected (belt-and-suspenders)."""

    def test_prune_session_aborts_for_protected_agent(self, tmp_path: Path) -> None:
        pruner = SmartPruner.__new__(SmartPruner)
        pruner.settings = MagicMock(platform="linux")
        pruner.project_root = tmp_path
        pruner.state_file = tmp_path / "state.json"
        pruner.snapshots = {}

        session: dict[str, Any] = {
            "id": "sess-claude",
            "pid": 5555,
            "agent": "claude",
            "status": "running",
            "tty": "",
            "source": "other",
        }

        with patch("thegent.orchestration.pruning.prune.mcp_prune") as mock_mcp_prune:
            # Import here to avoid circular import issues at module level
            from thegent.orchestration.pruning.prune import mcp_prune  # noqa: F401

            pruner._prune_session(session, pane=None)

        # mcp_prune should NOT have been called because the agent is protected
        mock_mcp_prune.assert_not_called()


# ---------------------------------------------------------------------------
# smart_prune_main entry point
# ---------------------------------------------------------------------------


class TestSmartPruneMain:
    """Tests for the smart_prune_main convenience entry point."""

    def test_dry_run_returns_results(self, tmp_path: Path) -> None:
        with (
            patch("thegent.orchestration.pruning.smart_prune.ThegentSettings"),
            patch("thegent.orchestration.pruning.smart_prune.ps_impl", return_value=[]),
            patch(
                "thegent.orchestration.pruning.smart_prune.list_tmux_panes",
                return_value=[],
            ),
        ):
            results = smart_prune_main(
                force=False, reprompt=False, dry_run=True, yes=False
            )

        assert "pruned" in results
        assert "kept" in results
        assert results["dry_run"] is True

    def test_no_sessions_no_kills(self, tmp_path: Path) -> None:
        with (
            patch("thegent.orchestration.pruning.smart_prune.ThegentSettings"),
            patch("thegent.orchestration.pruning.smart_prune.ps_impl", return_value=[]),
            patch(
                "thegent.orchestration.pruning.smart_prune.list_tmux_panes",
                return_value=[],
            ),
        ):
            results = smart_prune_main(
                force=True, reprompt=False, dry_run=False, yes=True
            )

        assert results["pruned"] == 0
