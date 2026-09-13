"""WL-106 CLI wiring: run fork/rollback stubs call SessionManager APIs."""

from __future__ import annotations

from unittest.mock import patch

import pytest
import typer
from typer.testing import CliRunner

from thegent.cli.apps.run import app as run_app
from thegent.cli.commands import cli as cli_cmd
from thegent.session import SessionManagerError

runner = CliRunner()


def test_run_fork_routes_to_session_fork_cmd() -> None:
    with patch("thegent.cli.commands.cli.session_fork_cmd") as mock_cmd:
        result = runner.invoke(
            run_app,
            ["fork", "sess-1", "--from-turn", "2", "--new-session-id", "sess-2"],
        )
    assert result.exit_code == 0
    mock_cmd.assert_called_once_with(
        session_id="sess-1", from_turn=2, new_session_id="sess-2"
    )


def test_run_fork_rejects_non_positive_from_turn() -> None:
    with patch("thegent.cli.commands.cli.session_fork_cmd") as mock_cmd:
        result = runner.invoke(
            run_app,
            ["fork", "sess-1", "--from-turn", "0"],
        )
    assert result.exit_code == 2
    assert "Invalid value for '--from-turn'" in result.output
    mock_cmd.assert_not_called()


def test_run_rollback_routes_to_session_rollback_cmd() -> None:
    with patch("thegent.cli.commands.cli.session_rollback_cmd") as mock_cmd:
        result = runner.invoke(
            run_app,
            ["rollback", "sess-1", "--n-turns", "3"],
        )
    assert result.exit_code == 0
    mock_cmd.assert_called_once_with(session_id="sess-1", n_turns=3)


def test_run_rollback_rejects_non_positive_n_turns() -> None:
    with patch("thegent.cli.commands.cli.session_rollback_cmd") as mock_cmd:
        result = runner.invoke(
            run_app,
            ["rollback", "sess-1", "--n-turns", "0"],
        )
    assert result.exit_code == 2
    assert "Invalid value for '--n-turns'" in result.output
    mock_cmd.assert_not_called()


def test_session_fork_cmd_calls_session_manager_api() -> None:
    manager = _FakeManager(fork_id="forked-123")
    with patch("thegent.session.SessionManager", return_value=manager):
        cli_cmd.session_fork_cmd(
            session_id="source-1", from_turn=4, new_session_id="forked-123"
        )
    assert manager.fork_calls == [("source-1", 4, "forked-123")]


def test_session_fork_cmd_forwards_none_from_turn_by_default() -> None:
    manager = _FakeManager(fork_id="forked-123")
    with patch("thegent.session.SessionManager", return_value=manager):
        cli_cmd.session_fork_cmd(
            session_id="source-1", from_turn=None, new_session_id="forked-123"
        )
    assert manager.fork_calls == [("source-1", None, "forked-123")]


def test_session_fork_cmd_rejects_blank_explicit_new_session_id() -> None:
    manager = _FakeManager(fork_id="forked-123")
    with (
        patch("thegent.session.SessionManager", return_value=manager),
        pytest.raises(typer.Exit) as exc,
    ):
        cli_cmd.session_fork_cmd(
            session_id="source-1", from_turn=None, new_session_id="   "
        )
    assert exc.value.exit_code == 2
    assert manager.fork_calls == []


def test_session_fork_cmd_rejects_new_session_id_matching_source_id() -> None:
    manager = _FakeManager(fork_id="forked-123")
    with (
        patch("thegent.session.SessionManager", return_value=manager),
        pytest.raises(typer.Exit) as exc,
    ):
        cli_cmd.session_fork_cmd(
            session_id="source-1", from_turn=None, new_session_id="source-1"
        )
    assert exc.value.exit_code == 2
    assert manager.fork_calls == []


def test_session_fork_cmd_rejects_blank_session_id() -> None:
    manager = _FakeManager(fork_id="forked-123")
    with (
        patch("thegent.session.SessionManager", return_value=manager),
        pytest.raises(typer.Exit) as exc,
    ):
        cli_cmd.session_fork_cmd(
            session_id="   ", from_turn=1, new_session_id="forked-123"
        )
    assert exc.value.exit_code == 2
    assert manager.fork_calls == []


def test_session_fork_cmd_rejects_non_positive_from_turn() -> None:
    manager = _FakeManager(fork_id="forked-123")
    with (
        patch("thegent.session.SessionManager", return_value=manager),
        pytest.raises(typer.Exit) as exc,
    ):
        cli_cmd.session_fork_cmd(
            session_id="source-1", from_turn=0, new_session_id="forked-123"
        )
    assert exc.value.exit_code == 2
    assert manager.fork_calls == []


def test_session_fork_cmd_strips_new_session_id_before_manager_call() -> None:
    manager = _FakeManager(fork_id="forked-123")
    with patch("thegent.session.SessionManager", return_value=manager):
        cli_cmd.session_fork_cmd(
            session_id="source-1", from_turn=4, new_session_id="  forked-123  "
        )
    assert manager.fork_calls == [("source-1", 4, "forked-123")]


def test_session_rollback_cmd_calls_session_manager_api() -> None:
    manager = _FakeManager(remaining=2)
    with patch("thegent.session.SessionManager", return_value=manager):
        cli_cmd.session_rollback_cmd(session_id="sess-1", n_turns=1)
    assert manager.rollback_calls == [("sess-1", 1)]


def test_session_rollback_cmd_rejects_blank_session_id() -> None:
    manager = _FakeManager(remaining=2)
    with (
        patch("thegent.session.SessionManager", return_value=manager),
        pytest.raises(typer.Exit) as exc,
    ):
        cli_cmd.session_rollback_cmd(session_id="  ", n_turns=1)
    assert exc.value.exit_code == 2
    assert manager.rollback_calls == []


def test_session_rollback_cmd_rejects_non_positive_n_turns() -> None:
    manager = _FakeManager(remaining=2)
    with (
        patch("thegent.session.SessionManager", return_value=manager),
        pytest.raises(typer.Exit) as exc,
    ):
        cli_cmd.session_rollback_cmd(session_id="sess-1", n_turns=0)
    assert exc.value.exit_code == 2
    assert manager.rollback_calls == []


def test_session_fork_cmd_fails_loud_on_manager_error() -> None:
    manager = _FakeManager(fork_error=SessionManagerError("boom"))
    with (
        patch("thegent.session.SessionManager", return_value=manager),
        pytest.raises(typer.Exit) as exc,
    ):
        cli_cmd.session_fork_cmd(
            session_id="source-1", from_turn=None, new_session_id=None
        )
    assert exc.value.exit_code == 2


def test_session_rollback_cmd_fails_loud_on_manager_error() -> None:
    manager = _FakeManager(rollback_error=SessionManagerError("boom"))
    with (
        patch("thegent.session.SessionManager", return_value=manager),
        pytest.raises(typer.Exit) as exc,
    ):
        cli_cmd.session_rollback_cmd(session_id="sess-1", n_turns=1)
    assert exc.value.exit_code == 2


class _FakeManager:
    def __init__(
        self,
        *,
        fork_id: str = "forked",
        remaining: int = 0,
        fork_error: Exception | None = None,
        rollback_error: Exception | None = None,
    ) -> None:
        self._fork_id = fork_id
        self._remaining = remaining
        self._fork_error = fork_error
        self._rollback_error = rollback_error
        self.fork_calls: list[tuple[str, int | None, str | None]] = []
        self.rollback_calls: list[tuple[str, int]] = []

    def fork_session(
        self, session_id: str, *, from_turn: int | None, new_session_id: str | None
    ) -> str:
        self.fork_calls.append((session_id, from_turn, new_session_id))
        if self._fork_error is not None:
            raise self._fork_error
        return self._fork_id

    def rollback_session(self, session_id: str, *, n_turns: int) -> int:
        self.rollback_calls.append((session_id, n_turns))
        if self._rollback_error is not None:
            raise self._rollback_error
        return self._remaining
