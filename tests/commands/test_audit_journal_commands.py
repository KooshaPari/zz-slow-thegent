"""Tests for audit journal CLI commands.

WBS: wp-audit-journal-cli
FR Traceability: FR-VER-005 (audit log and diff CLI)
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from thegent.cli.apps import audit

if TYPE_CHECKING:
    pass

runner = CliRunner()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_git_journal():
    """Create a mock GitJournalEnhanced class."""
    with patch("thegent.cli.apps.audit.GitJournalEnhanced") as mock:
        # Mock list_sessions
        mock.list_sessions.return_value = [
            {
                "session_id": "test-session-1",
                "last_commit": "2024-01-15",
                "sha": "abc123def456",
            },
            {
                "session_id": "test-session-2",
                "last_commit": "2024-01-16",
                "sha": "789xyz123abc",
            },
        ]

        # Mock instance for journal operations
        mock_instance = MagicMock()
        mock_instance.get_audit_log.return_value = [
            {
                "sha": "abc123",
                "message": "Initial commit",
                "timestamp": "2024-01-15T10:00:00",
            },
            {
                "sha": "def456",
                "message": "Second entry",
                "timestamp": "2024-01-15T11:00:00",
            },
        ]
        mock_instance.get_attestations.return_value = [
            {
                "commit_sha": "abc123",
                "timestamp": "2024-01-15T10:00:00",
                "algorithm": "sha256",
            },
        ]
        mock_instance.get_performance_stats.return_value = {
            "native_scanner": True,
            "watcher": "watchman",
            "batch_size": 10,
            "total_commits": 2,
        }
        mock_instance.record_snapshot.return_value = "snapshot123abc"
        mock_instance.verify_attestation.return_value = True

        mock.return_value = mock_instance
        yield mock


# ---------------------------------------------------------------------------
# List command tests
# ---------------------------------------------------------------------------


class TestJournalList:
    def test_list_sessions_success(self, mock_git_journal) -> None:
        """Test listing all audit sessions."""
        result = runner.invoke(audit.app, ["journal", "list"])
        assert result.exit_code == 0
        assert "test-session-1" in result.output
        assert "test-session-2" in result.output
        assert "Git Journal Sessions" in result.output

    def test_list_sessions_empty(self, mock_git_journal) -> None:
        """Test listing with no sessions."""
        mock_git_journal.list_sessions.return_value = []
        result = runner.invoke(audit.app, ["journal", "list"])
        assert result.exit_code == 0
        assert "No audit sessions found" in result.output


# ---------------------------------------------------------------------------
# Status command tests
# ---------------------------------------------------------------------------


class TestJournalStatus:
    def test_status_with_session(self, mock_git_journal) -> None:
        """Test getting status for a specific session."""
        result = runner.invoke(
            audit.app, ["journal", "status", "--session", "test-session-1"]
        )
        assert result.exit_code == 0
        assert "Journal Status" in result.output or "test-session-1" in result.output

    def test_status_missing_session(self, mock_git_journal) -> None:
        """Test status requires --session flag."""
        result = runner.invoke(audit.app, ["journal", "status"])
        assert result.exit_code == 1
        assert (
            "--session required" in result.output.lower()
            or "error" in result.output.lower()
        )

    def test_status_no_entries(self, mock_git_journal) -> None:
        """Test status with session that has no entries."""
        mock_instance = mock_git_journal.return_value
        mock_instance.get_audit_log.return_value = []
        result = runner.invoke(
            audit.app, ["journal", "status", "--session", "empty-session"]
        )
        assert result.exit_code == 0
        assert "No entries" in result.output or "empty-session" in result.output


# ---------------------------------------------------------------------------
# Snapshot command tests
# ---------------------------------------------------------------------------


class TestJournalSnapshot:
    def test_snapshot_with_session(self, mock_git_journal) -> None:
        """Test creating snapshot with explicit session ID."""
        result = runner.invoke(
            audit.app,
            ["journal", "snapshot", "--session", "test-session-1", "--batch", "5"],
        )
        assert result.exit_code == 0
        assert "snapshot" in result.output.lower()
        assert "test-session-1" in result.output

    def test_snapshot_without_session(self, mock_git_journal) -> None:
        """Test snapshot creates session when not provided."""
        result = runner.invoke(audit.app, ["journal", "snapshot"])
        assert result.exit_code == 0
        assert "session" in result.output.lower() or "Created" in result.output

    def test_snapshot_with_flags(self, mock_git_journal) -> None:
        """Test snapshot with --watch and --attest flags."""
        result = runner.invoke(
            audit.app, ["journal", "snapshot", "--watch", "--attest", "--batch", "20"]
        )
        assert result.exit_code == 0
        assert "snapshot" in result.output.lower() or "Created" in result.output


# ---------------------------------------------------------------------------
# Prune command tests
# ---------------------------------------------------------------------------


class TestJournalPrune:
    def test_prune_with_max_age(self, mock_git_journal) -> None:
        """Test pruning old sessions with --max-age."""
        mock_git_journal.prune_old_sessions.return_value = 5
        result = runner.invoke(audit.app, ["journal", "prune", "--max-age", "30"])
        assert result.exit_code == 0
        assert "Pruned" in result.output or "5" in result.output

    def test_prune_default_max_age(self, mock_git_journal) -> None:
        """Test prune uses default max-age of 30 days."""
        result = runner.invoke(audit.app, ["journal", "prune"])
        assert result.exit_code == 0
        mock_git_journal.prune_old_sessions.assert_called_once()
        call_args = mock_git_journal.prune_old_sessions.call_args
        assert call_args[0][1] == 30 or call_args.kwargs.get("max_age_days") == 30


# ---------------------------------------------------------------------------
# Show command tests
# ---------------------------------------------------------------------------


class TestJournalShow:
    def test_show_with_session(self, mock_git_journal) -> None:
        """Test showing audit log for a session."""
        result = runner.invoke(
            audit.app, ["journal", "show", "--session", "test-session-1"]
        )
        assert result.exit_code == 0
        assert "Audit Log" in result.output or "test-session-1" in result.output
        assert "abc123" in result.output

    def test_show_missing_session(self, mock_git_journal) -> None:
        """Test show requires --session flag."""
        result = runner.invoke(audit.app, ["journal", "show"])
        assert result.exit_code == 1
        assert (
            "--session required" in result.output.lower()
            or "error" in result.output.lower()
        )


# ---------------------------------------------------------------------------
# Watch command tests
# ---------------------------------------------------------------------------


class TestJournalWatch:
    def test_watch_creates_session(self, mock_git_journal) -> None:
        """Test watch creates session when not provided."""
        result = runner.invoke(audit.app, ["journal", "watch"])
        assert result.exit_code == 0
        assert "watch" in result.output.lower() or "Session" in result.output

    def test_watch_with_session(self, mock_git_journal) -> None:
        """Test watch with explicit session ID."""
        result = runner.invoke(
            audit.app, ["journal", "watch", "--session", "watch-session"]
        )
        assert result.exit_code == 0
        assert "watch" in result.output.lower() or "watch-session" in result.output

    def test_watch_with_attest(self, mock_git_journal) -> None:
        """Test watch with attestation enabled."""
        result = runner.invoke(audit.app, ["journal", "watch", "--attest"])
        assert result.exit_code == 0
        assert "watch" in result.output.lower() or "attest" in result.output.lower()


# ---------------------------------------------------------------------------
# Attest command tests
# ---------------------------------------------------------------------------


class TestJournalAttest:
    def test_attest_with_session(self, mock_git_journal) -> None:
        """Test getting attestations for a session."""
        result = runner.invoke(
            audit.app, ["journal", "attest", "--session", "test-session-1"]
        )
        assert result.exit_code == 0
        assert "Attestations" in result.output or "test-session-1" in result.output

    def test_attest_missing_session(self, mock_git_journal) -> None:
        """Test attest requires --session flag."""
        result = runner.invoke(audit.app, ["journal", "attest"])
        assert result.exit_code == 1
        assert (
            "--session required" in result.output.lower()
            or "error" in result.output.lower()
        )

    def test_attest_no_entries(self, mock_git_journal) -> None:
        """Test attest with session that has no attestations."""
        mock_instance = mock_git_journal.return_value
        mock_instance.get_attestations.return_value = []
        result = runner.invoke(
            audit.app, ["journal", "attest", "--session", "no-attest-session"]
        )
        assert result.exit_code == 0
        assert "No attestations" in result.output


# ---------------------------------------------------------------------------
# Stats command tests
# ---------------------------------------------------------------------------


class TestJournalStats:
    def test_stats_with_session(self, mock_git_journal) -> None:
        """Test getting performance stats for a session."""
        result = runner.invoke(
            audit.app, ["journal", "stats", "--session", "test-session-1"]
        )
        assert result.exit_code == 0
        assert "Stats" in result.output or "test-session-1" in result.output
        assert "native_scanner" in result.output or "batch_size" in result.output

    def test_stats_missing_session(self, mock_git_journal) -> None:
        """Test stats requires --session flag."""
        result = runner.invoke(audit.app, ["journal", "stats"])
        assert result.exit_code == 1
        assert (
            "--session required" in result.output.lower()
            or "error" in result.output.lower()
        )


# ---------------------------------------------------------------------------
# Help and error handling tests
# ---------------------------------------------------------------------------


class TestJournalHelp:
    def test_journal_help_output(self) -> None:
        """Test journal help shows all available actions."""
        result = runner.invoke(audit.app, ["journal", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output
        assert "status" in result.output
        assert "snapshot" in result.output
        assert "prune" in result.output
        assert "show" in result.output
        assert "watch" in result.output
        assert "attest" in result.output
        assert "stats" in result.output

    def test_journal_invalid_action(self, mock_git_journal) -> None:
        """Test journal with invalid action returns error."""
        result = runner.invoke(audit.app, ["journal", "invalid-action"])
        assert result.exit_code == 1
        assert "Unknown action" in result.output or "invalid-action" in result.output


# ---------------------------------------------------------------------------
# Flag tests
# ---------------------------------------------------------------------------


class TestJournalFlags:
    def test_enhanced_flag(self, mock_git_journal) -> None:
        """Test --enhanced flag is accepted."""
        result = runner.invoke(audit.app, ["journal", "snapshot", "--enhanced"])
        assert result.exit_code == 0

    def test_basic_flag(self, mock_git_journal) -> None:
        """Test --basic flag is accepted."""
        result = runner.invoke(audit.app, ["journal", "snapshot", "--basic"])
        assert result.exit_code == 0

    def test_path_flag(self, mock_git_journal) -> None:
        """Test --path flag is accepted."""
        result = runner.invoke(
            audit.app, ["journal", "list", "--path", "/tmp/test-repo"]
        )
        assert result.exit_code == 0
        mock_git_journal.list_sessions.assert_called()
