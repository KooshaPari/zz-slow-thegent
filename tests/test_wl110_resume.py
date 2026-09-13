"""WL-110: Stable thegent resume <session_id> and thegent session list.

Tests for:
- resume_impl: state contract lookup, most-recent resolution, prompt injection
- session_list_impl: list all sessions from state contracts
- CLI wiring: thegent resume, thegent run resume, thegent session resume, thegent session list
"""

# @trace WL-110

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import orjson as json
import pytest
from typer.testing import CliRunner

from thegent.cli.apps.main import app
from thegent.cli.commands.impl import (
    _session_state_path,
    _write_session_state,
    resume_impl,
    session_list_impl,
)

runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_state(
    tmp_path: Path,
    session_id: str,
    run_id: str = "run-x",
    status: str = "running",
    updated_at: str = "2026-02-20T00:00:00+00:00",
    agent: str | None = "codex",
    model: str | None = "gpt-5",
    owner: str | None = None,
) -> Path:
    d = tmp_path / session_id
    d.mkdir(parents=True, exist_ok=True)
    payload: dict = {
        "session_id": session_id,
        "run_id": run_id,
        "status": status,
        "updated_at_utc": updated_at,
        "agent": agent,
        "model": model,
    }
    if owner is not None:
        payload["owner"] = owner
    sp = d / "state.json"
    sp.write_text(json.dumps(payload).decode(), encoding="utf-8")
    return sp


def _mock_settings(tmp_path: Path) -> MagicMock:
    s = MagicMock()
    s.session_dir = tmp_path
    return s


# ---------------------------------------------------------------------------
# _write_session_state
# ---------------------------------------------------------------------------


def test_write_session_state_creates_file(tmp_path: Path) -> None:
    # @trace WL-110
    settings = _mock_settings(tmp_path)
    sp = _write_session_state(
        settings=settings,
        session_id="s1",
        run_id="r1",
        agent="codex",
        model="gpt-5",
        cwd=tmp_path,
    )
    assert sp.exists()
    payload = json.loads(sp.read_text())
    assert payload["session_id"] == "s1"
    assert payload["run_id"] == "r1"
    assert payload["status"] == "running"


def test_write_session_state_creates_parent_directories(tmp_path: Path) -> None:
    # @trace WL-110
    settings = _mock_settings(tmp_path / "nested")
    sp = _write_session_state(
        settings=settings,
        session_id="s2",
        run_id="r2",
        agent=None,
        model=None,
        cwd=tmp_path,
    )
    assert sp.exists()


def test_write_session_state_stores_all_fields(tmp_path: Path) -> None:
    # @trace WL-110
    settings = _mock_settings(tmp_path)
    sp = _write_session_state(
        settings=settings,
        session_id="s3",
        run_id="r3",
        agent="cursor",
        model="gpt-4o",
        cwd=tmp_path,
    )
    payload = json.loads(sp.read_text())
    assert payload["agent"] == "cursor"
    assert payload["model"] == "gpt-4o"
    assert payload["cwd"] == str(tmp_path)
    assert "updated_at_utc" in payload


# ---------------------------------------------------------------------------
# _session_state_path
# ---------------------------------------------------------------------------


def test_session_state_path_correct_location(tmp_path: Path) -> None:
    # @trace WL-110
    settings = _mock_settings(tmp_path)
    p = _session_state_path(settings, "sess-abc")
    assert p == tmp_path.expanduser().resolve() / "sess-abc" / "state.json"


# ---------------------------------------------------------------------------
# resume_impl – error cases
# ---------------------------------------------------------------------------


def test_resume_impl_fails_when_state_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # @trace WL-110
    monkeypatch.setattr(
        "thegent.cli.commands.impl.ThegentSettings", lambda: _mock_settings(tmp_path)
    )
    result = resume_impl(session_id="nonexistent")
    assert result["exit_code"] == 1
    assert "State contract not found" in result["error"]
    assert "nonexistent" in result["error"]


def test_resume_impl_fails_when_no_sessions_exist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # @trace WL-110
    monkeypatch.setattr(
        "thegent.cli.commands.impl.ThegentSettings", lambda: _mock_settings(tmp_path)
    )
    result = resume_impl()
    assert result["exit_code"] == 1
    assert "No resumable sessions found" in result["error"]


def test_resume_impl_error_message_includes_start_hint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # @trace WL-110
    monkeypatch.setattr(
        "thegent.cli.commands.impl.ThegentSettings", lambda: _mock_settings(tmp_path)
    )
    result = resume_impl()
    assert "thegent run agent --bg" in result["error"]


def test_resume_impl_fails_when_run_id_missing_from_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # @trace WL-110
    monkeypatch.setattr(
        "thegent.cli.commands.impl.ThegentSettings", lambda: _mock_settings(tmp_path)
    )
    d = tmp_path / "sess-bad"
    d.mkdir()
    (d / "state.json").write_text(
        json.dumps({"session_id": "sess-bad", "status": "running"}).decode(),
        encoding="utf-8",
    )
    result = resume_impl(session_id="sess-bad")
    assert result["exit_code"] == 1
    assert "missing run_id" in result["error"]


# ---------------------------------------------------------------------------
# resume_impl – success cases
# ---------------------------------------------------------------------------


def test_resume_impl_succeeds_with_explicit_session_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # @trace WL-110
    _make_state(tmp_path, "s-explicit", run_id="r-explicit")
    monkeypatch.setattr(
        "thegent.cli.commands.impl.ThegentSettings", lambda: _mock_settings(tmp_path)
    )
    mock_registry = MagicMock()
    monkeypatch.setattr(
        "thegent.cli.commands.impl.RunRegistry", lambda *a, **kw: mock_registry
    )

    result = resume_impl(session_id="s-explicit")

    assert result["session_id"] == "s-explicit"
    assert result["run_id"] == "r-explicit"
    assert result["prompt_sent"] is False
    mock_registry.register_resume.assert_called_once_with("r-explicit")


def test_resume_impl_sends_prompt_when_provided(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # @trace WL-110
    _make_state(tmp_path, "s-prompt", run_id="r-prompt")
    monkeypatch.setattr(
        "thegent.cli.commands.impl.ThegentSettings", lambda: _mock_settings(tmp_path)
    )
    mock_registry = MagicMock()
    monkeypatch.setattr(
        "thegent.cli.commands.impl.RunRegistry", lambda *a, **kw: mock_registry
    )
    monkeypatch.setattr(
        "thegent.cli.commands.impl.session_send_impl", lambda *a, **kw: (True, "queued")
    )

    result = resume_impl(session_id="s-prompt", prompt="continue")

    assert result["prompt_sent"] is True


def test_resume_impl_selects_most_recent_by_updated_at(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # @trace WL-110
    _make_state(
        tmp_path, "s-old", run_id="r-old", updated_at="2026-02-19T00:00:00+00:00"
    )
    _make_state(
        tmp_path, "s-new", run_id="r-new", updated_at="2026-02-21T00:00:00+00:00"
    )
    monkeypatch.setattr(
        "thegent.cli.commands.impl.ThegentSettings", lambda: _mock_settings(tmp_path)
    )
    mock_registry = MagicMock()
    monkeypatch.setattr(
        "thegent.cli.commands.impl.RunRegistry", lambda *a, **kw: mock_registry
    )

    result = resume_impl()

    assert result["session_id"] == "s-new"
    assert result["run_id"] == "r-new"


def test_resume_impl_tie_breaks_deterministically_when_updated_at_matches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # @trace WL-110
    _make_state(tmp_path, "s-a", run_id="r-a", updated_at="2026-02-21T00:00:00+00:00")
    _make_state(tmp_path, "s-b", run_id="r-b", updated_at="2026-02-21T00:00:00+00:00")
    monkeypatch.setattr(
        "thegent.cli.commands.impl.ThegentSettings", lambda: _mock_settings(tmp_path)
    )
    mock_registry = MagicMock()
    monkeypatch.setattr(
        "thegent.cli.commands.impl.RunRegistry", lambda *a, **kw: mock_registry
    )

    result = resume_impl()

    assert result["session_id"] == "s-b"
    assert result["run_id"] == "r-b"


def test_resume_impl_updates_state_status_on_resume(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # @trace WL-110
    sp = _make_state(tmp_path, "s-status", run_id="r-status", status="paused")
    monkeypatch.setattr(
        "thegent.cli.commands.impl.ThegentSettings", lambda: _mock_settings(tmp_path)
    )
    mock_registry = MagicMock()
    monkeypatch.setattr(
        "thegent.cli.commands.impl.RunRegistry", lambda *a, **kw: mock_registry
    )

    resume_impl(session_id="s-status")

    updated = json.loads(sp.read_text())
    assert updated["status"] == "running"


# ---------------------------------------------------------------------------
# session_list_impl
# ---------------------------------------------------------------------------


def test_session_list_impl_returns_empty_when_no_sessions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # @trace WL-110
    monkeypatch.setattr(
        "thegent.cli.commands.session_ops_impl.ThegentSettings",
        lambda: _mock_settings(tmp_path),
    )
    result = session_list_impl()
    assert result == []


def test_session_list_impl_returns_sessions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # @trace WL-110
    _make_state(
        tmp_path, "s-list-1", run_id="r1", updated_at="2026-02-20T00:00:00+00:00"
    )
    _make_state(
        tmp_path, "s-list-2", run_id="r2", updated_at="2026-02-21T00:00:00+00:00"
    )
    monkeypatch.setattr(
        "thegent.cli.commands.session_ops_impl.ThegentSettings",
        lambda: _mock_settings(tmp_path),
    )
    monkeypatch.setattr(
        "thegent.cli.commands.impl._default_owner_tag", lambda: "testuser"
    )

    result = session_list_impl(all_sessions=True)
    ids = [r["session_id"] for r in result]
    assert "s-list-1" in ids
    assert "s-list-2" in ids


def test_session_list_impl_sorted_newest_first(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # @trace WL-110
    _make_state(
        tmp_path, "s-old2", run_id="r-o", updated_at="2026-02-19T00:00:00+00:00"
    )
    _make_state(
        tmp_path, "s-new2", run_id="r-n", updated_at="2026-02-21T00:00:00+00:00"
    )
    monkeypatch.setattr(
        "thegent.cli.commands.session_ops_impl.ThegentSettings",
        lambda: _mock_settings(tmp_path),
    )
    monkeypatch.setattr("thegent.cli.commands.impl._default_owner_tag", lambda: "u")

    result = session_list_impl(all_sessions=True)
    assert result[0]["session_id"] == "s-new2"
    assert result[1]["session_id"] == "s-old2"


def test_session_list_impl_respects_limit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # @trace WL-110
    for i in range(5):
        _make_state(
            tmp_path,
            f"s-lim-{i}",
            run_id=f"r-{i}",
            updated_at=f"2026-02-{10 + i:02d}T00:00:00+00:00",
        )
    monkeypatch.setattr(
        "thegent.cli.commands.session_ops_impl.ThegentSettings",
        lambda: _mock_settings(tmp_path),
    )
    monkeypatch.setattr("thegent.cli.commands.impl._default_owner_tag", lambda: "u")

    result = session_list_impl(all_sessions=True, limit=3)
    assert len(result) == 3


def test_session_list_impl_includes_required_fields(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # @trace WL-110
    _make_state(tmp_path, "s-fields", run_id="r-f", agent="cursor", model="gpt-4o")
    monkeypatch.setattr(
        "thegent.cli.commands.session_ops_impl.ThegentSettings",
        lambda: _mock_settings(tmp_path),
    )
    monkeypatch.setattr("thegent.cli.commands.impl._default_owner_tag", lambda: "u")

    result = session_list_impl(all_sessions=True)
    assert len(result) == 1
    row = result[0]
    assert "session_id" in row
    assert "status" in row
    assert "agent" in row
    assert "model" in row
    assert "updated_at_utc" in row
    assert "run_id" in row


def test_session_list_impl_skips_malformed_state_contracts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # @trace WL-110
    _make_state(
        tmp_path, "s-valid", run_id="r-valid", updated_at="2026-02-21T00:00:00+00:00"
    )
    bad_dir = tmp_path / "s-bad"
    bad_dir.mkdir(parents=True, exist_ok=True)
    (bad_dir / "state.json").write_text(
        json.dumps(
            {
                "session_id": "s-bad",
                "run_id": "   ",
                "status": "running",
                "updated_at_utc": "2026-02-22T00:00:00+00:00",
            }
        ).decode(),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "thegent.cli.commands.session_ops_impl.ThegentSettings",
        lambda: _mock_settings(tmp_path),
    )
    monkeypatch.setattr("thegent.cli.commands.impl._default_owner_tag", lambda: "u")

    result = session_list_impl(all_sessions=True)
    ids = [row["session_id"] for row in result]
    assert ids == ["s-valid"]


# ---------------------------------------------------------------------------
# CLI wiring – thegent session resume
# ---------------------------------------------------------------------------


def test_cli_session_resume_calls_resume_cmd(monkeypatch: pytest.MonkeyPatch) -> None:
    # @trace WL-110
    captured: dict = {}

    def _fake_resume_cmd(*, session_id=None, prompt=None, skills=None):
        captured["session_id"] = session_id
        captured["prompt"] = prompt

    monkeypatch.setattr("thegent.cli.commands.cli.resume_cmd", _fake_resume_cmd)

    result = runner.invoke(app, ["session", "resume", "s-cli", "--prompt", "go"])
    assert result.exit_code == 0
    assert captured["session_id"] == "s-cli"
    assert captured["prompt"] == "go"


def test_cli_session_resume_no_session_id(monkeypatch: pytest.MonkeyPatch) -> None:
    # @trace WL-110
    captured: dict = {}

    def _fake_resume_cmd(*, session_id=None, prompt=None, skills=None):
        captured["session_id"] = session_id

    monkeypatch.setattr("thegent.cli.commands.cli.resume_cmd", _fake_resume_cmd)

    result = runner.invoke(app, ["session", "resume"])
    assert result.exit_code == 0
    assert captured["session_id"] is None


# ---------------------------------------------------------------------------
# CLI wiring – thegent session list
# ---------------------------------------------------------------------------


def test_cli_session_list_json_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # @trace WL-110

    def _fake_session_list_impl(owner=None, all_sessions=False, limit=50):
        return [
            {
                "session_id": "s-cli-list",
                "status": "running",
                "agent": "codex",
                "model": "gpt-5",
                "updated_at_utc": "",
                "run_id": "r1",
                "cwd": None,
            }
        ]

    monkeypatch.setattr(
        "thegent.cli.commands.impl.session_list_impl", _fake_session_list_impl
    )

    result = runner.invoke(app, ["session", "list", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert data[0]["session_id"] == "s-cli-list"


def test_cli_session_list_rich_output(monkeypatch: pytest.MonkeyPatch) -> None:
    # @trace WL-110

    def _fake_session_list_impl(owner=None, all_sessions=False, limit=50):
        return [
            {
                "session_id": "s-rich",
                "status": "running",
                "agent": "codex",
                "model": "gpt-5",
                "updated_at_utc": "2026-02-20",
                "run_id": "r1",
                "cwd": None,
            }
        ]

    monkeypatch.setattr(
        "thegent.cli.commands.impl.session_list_impl", _fake_session_list_impl
    )

    result = runner.invoke(app, ["session", "list"])
    assert result.exit_code == 0
    assert "s-rich" in result.output


def test_cli_session_list_empty_shows_no_sessions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # @trace WL-110
    monkeypatch.setattr("thegent.cli.commands.impl.session_list_impl", lambda **kw: [])

    result = runner.invoke(app, ["session", "list"])
    assert result.exit_code == 0
    assert "No sessions found" in result.output


def test_cli_session_list_invalid_format_exits_2(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # @trace WL-110
    monkeypatch.setattr("thegent.cli.commands.impl.session_list_impl", lambda **kw: [])

    result = runner.invoke(app, ["session", "list", "--format", "xml"])
    assert result.exit_code == 2


# ---------------------------------------------------------------------------
# CLI wiring – top-level thegent resume shortcut
# ---------------------------------------------------------------------------


def test_top_level_resume_shortcut_wires_to_resume_cmd(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # @trace WL-110
    captured: dict = {}

    def _fake_resume_cmd(*, session_id=None, prompt=None, skills=None):
        captured["session_id"] = session_id
        captured["prompt"] = prompt

    monkeypatch.setattr("thegent.cli.commands.cli.resume_cmd", _fake_resume_cmd)

    result = runner.invoke(app, ["resume", "s-shortcut", "--prompt", "next step"])
    assert result.exit_code == 0
    assert captured["session_id"] == "s-shortcut"
    assert captured["prompt"] == "next step"


# ---------------------------------------------------------------------------
# CLI wiring – thegent run resume
# ---------------------------------------------------------------------------


def test_run_resume_subcommand_wires_to_resume_cmd(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # @trace WL-110
    captured: dict = {}

    def _fake_resume_cmd(*, session_id=None, prompt=None, skills=None):
        captured["session_id"] = session_id
        captured["prompt"] = prompt

    monkeypatch.setattr("thegent.cli.commands.cli.resume_cmd", _fake_resume_cmd)

    result = runner.invoke(app, ["run", "resume", "s-run-resume", "--prompt", "tick"])
    assert result.exit_code == 0
    assert captured["session_id"] == "s-run-resume"
    assert captured["prompt"] == "tick"
