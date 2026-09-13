"""WL-110 focused tests for stable resume state contract behavior."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import orjson as json
import pytest
from typer.testing import CliRunner

from thegent.cli.apps.main import app
from thegent.cli.commands.impl import (
    _write_session_state,
    resume_impl,
    session_list_impl,
)

runner = CliRunner()


def test_write_session_state_persists_contract(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    settings = MagicMock()
    settings.session_dir = tmp_path

    state_path = _write_session_state(
        settings=settings,
        session_id="sess-1",
        run_id="run-1",
        agent="codex",
        model="gpt-5-codex",
        cwd=tmp_path,
    )

    payload = json.loads(state_path.read_text(encoding="utf-8"))
    assert payload["session_id"] == "sess-1"
    assert payload["run_id"] == "run-1"
    assert payload["status"] == "running"


def test_resume_impl_requires_existing_state_contract(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mock_settings = MagicMock()
    mock_settings.session_dir = tmp_path
    monkeypatch.setattr("thegent.cli.commands.impl.ThegentSettings", lambda: mock_settings)

    result = resume_impl(session_id="missing")
    assert result["exit_code"] == 1
    assert "State contract not found" in result["error"]


def test_resume_impl_rejects_non_json_state_contract(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    session_id = "sess-bad-json"
    state_dir = tmp_path / session_id
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "state.json").write_text("{bad", encoding="utf-8")

    mock_settings = MagicMock()
    mock_settings.session_dir = tmp_path
    monkeypatch.setattr("thegent.cli.commands.impl.ThegentSettings", lambda: mock_settings)

    result = resume_impl(session_id=session_id)
    assert result["exit_code"] == 1
    assert "not valid JSON" in result["error"]


def test_resume_impl_rejects_session_id_mismatch_in_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    session_id = "sess-mismatch"
    state_dir = tmp_path / session_id
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "state.json").write_text(
        json.dumps(
            {
                "session_id": "different-session",
                "run_id": "run-2",
                "status": "running",
                "updated_at_utc": "2026-02-21T00:00:00+00:00",
            }
        ).decode(),
        encoding="utf-8",
    )

    mock_settings = MagicMock()
    mock_settings.session_dir = tmp_path
    monkeypatch.setattr("thegent.cli.commands.impl.ThegentSettings", lambda: mock_settings)

    result = resume_impl(session_id=session_id)
    assert result["exit_code"] == 1
    assert "session_id mismatch" in result["error"]


def test_resume_impl_reports_actionable_message_when_no_sessions_exist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mock_settings = MagicMock()
    mock_settings.session_dir = tmp_path
    monkeypatch.setattr("thegent.cli.commands.impl.ThegentSettings", lambda: mock_settings)

    result = resume_impl()

    assert result["exit_code"] == 1
    assert "No resumable sessions found" in result["error"]
    assert "thegent run agent --bg" in result["error"]


def test_resume_impl_registers_resume_and_sends_prompt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    session_id = "sess-2"
    state_dir = tmp_path / session_id
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / "state.json"
    state_path.write_text(
        json.dumps(
            {
                "session_id": session_id,
                "run_id": "run-2",
                "agent": "codex",
                "model": "gpt-5-codex",
                "cwd": str(tmp_path).decode(),
                "status": "running",
                "updated_at_utc": "2026-02-21T00:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )

    mock_settings = MagicMock()
    mock_settings.session_dir = tmp_path
    monkeypatch.setattr("thegent.cli.commands.impl.ThegentSettings", lambda: mock_settings)

    mock_registry = MagicMock()
    monkeypatch.setattr("thegent.cli.commands.impl.RunRegistry", lambda *_args, **_kwargs: mock_registry)
    monkeypatch.setattr("thegent.cli.commands.impl.session_send_impl", lambda *_args, **_kwargs: (True, "queued"))

    result = resume_impl(session_id=session_id, prompt="continue")

    assert result["session_id"] == session_id
    assert result["run_id"] == "run-2"
    assert result["prompt_sent"] is True
    mock_registry.register_resume.assert_called_once_with("run-2")


def test_resume_impl_rejects_whitespace_prompt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    session_id = "sess-space"
    state_dir = tmp_path / session_id
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "state.json").write_text(
        json.dumps(
            {
                "session_id": session_id,
                "run_id": "run-space",
                "status": "running",
                "updated_at_utc": "2026-02-21T00:00:00+00:00",
            }
        ).decode(),
        encoding="utf-8",
    )

    mock_settings = MagicMock()
    mock_settings.session_dir = tmp_path
    monkeypatch.setattr("thegent.cli.commands.impl.ThegentSettings", lambda: mock_settings)
    mock_registry = MagicMock()
    monkeypatch.setattr("thegent.cli.commands.impl.RunRegistry", lambda *_args, **_kwargs: mock_registry)

    result = resume_impl(session_id=session_id, prompt="   ")

    assert result["exit_code"] == 1
    assert "whitespace-only" in result["error"]
    mock_registry.register_resume.assert_not_called()


def test_resume_impl_does_not_register_when_prompt_delivery_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    session_id = "sess-send-fail"
    state_dir = tmp_path / session_id
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "state.json").write_text(
        json.dumps(
            {
                "session_id": session_id,
                "run_id": "run-send-fail",
                "status": "running",
                "updated_at_utc": "2026-02-21T00:00:00+00:00",
            }
        ).decode(),
        encoding="utf-8",
    )

    mock_settings = MagicMock()
    mock_settings.session_dir = tmp_path
    monkeypatch.setattr("thegent.cli.commands.impl.ThegentSettings", lambda: mock_settings)
    mock_registry = MagicMock()
    monkeypatch.setattr("thegent.cli.commands.impl.RunRegistry", lambda *_args, **_kwargs: mock_registry)
    monkeypatch.setattr(
        "thegent.cli.commands.impl.session_send_impl",
        lambda *_args, **_kwargs: (False, "failed to queue prompt"),
    )

    result = resume_impl(session_id=session_id, prompt="continue")

    assert result["exit_code"] == 1
    assert "failed to queue prompt" in result["error"]
    mock_registry.register_resume.assert_not_called()


def test_resume_impl_without_session_id_uses_most_recent_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    older_dir = tmp_path / "sess-older"
    older_dir.mkdir(parents=True, exist_ok=True)
    (older_dir / "state.json").write_text(
        json.dumps(
            {
                "session_id": "sess-older",
                "run_id": "run-older",
                "status": "running",
                "updated_at_utc": "2026-02-20T00:00:00+00:00",
            }
        ).decode(),
        encoding="utf-8",
    )

    newer_dir = tmp_path / "sess-newer"
    newer_dir.mkdir(parents=True, exist_ok=True)
    (newer_dir / "state.json").write_text(
        json.dumps(
            {
                "session_id": "sess-newer",
                "run_id": "run-newer",
                "status": "running",
                "updated_at_utc": "2026-02-21T00:00:00+00:00",
            }
        ).decode(),
        encoding="utf-8",
    )

    mock_settings = MagicMock()
    mock_settings.session_dir = tmp_path
    monkeypatch.setattr("thegent.cli.commands.impl.ThegentSettings", lambda: mock_settings)

    mock_registry = MagicMock()
    monkeypatch.setattr("thegent.cli.commands.impl.RunRegistry", lambda *_args, **_kwargs: mock_registry)

    result = resume_impl()

    assert result["session_id"] == "sess-newer"
    assert result["run_id"] == "run-newer"
    mock_registry.register_resume.assert_called_once_with("run-newer")


def test_resume_impl_without_session_id_skips_latest_invalid_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    valid_dir = tmp_path / "sess-valid"
    valid_dir.mkdir(parents=True, exist_ok=True)
    (valid_dir / "state.json").write_text(
        json.dumps(
            {
                "session_id": "sess-valid",
                "run_id": "run-valid",
                "status": "running",
                "updated_at_utc": "2026-02-20T00:00:00+00:00",
            }
        ).decode(),
        encoding="utf-8",
    )

    invalid_newer_dir = tmp_path / "sess-invalid-newer"
    invalid_newer_dir.mkdir(parents=True, exist_ok=True)
    (invalid_newer_dir / "state.json").write_text(
        json.dumps(
            {
                "session_id": "sess-invalid-newer",
                "run_id": "   ",
                "status": "running",
                "updated_at_utc": "2026-02-21T00:00:00+00:00",
            }
        ).decode(),
        encoding="utf-8",
    )

    mock_settings = MagicMock()
    mock_settings.session_dir = tmp_path
    monkeypatch.setattr("thegent.cli.commands.impl.ThegentSettings", lambda: mock_settings)
    mock_registry = MagicMock()
    monkeypatch.setattr("thegent.cli.commands.impl.RunRegistry", lambda *_args, **_kwargs: mock_registry)

    result = resume_impl()

    assert result["session_id"] == "sess-valid"
    assert result["run_id"] == "run-valid"
    mock_registry.register_resume.assert_called_once_with("run-valid")


def test_resume_impl_without_session_id_handles_mixed_timezone_timestamps(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    naive_dir = tmp_path / "sess-naive"
    naive_dir.mkdir(parents=True, exist_ok=True)
    (naive_dir / "state.json").write_text(
        json.dumps(
            {
                "session_id": "sess-naive",
                "run_id": "run-naive",
                "status": "running",
                "updated_at_utc": "2026-02-21T00:00:00",
            }
        ).decode(),
        encoding="utf-8",
    )

    aware_newer_dir = tmp_path / "sess-aware-newer"
    aware_newer_dir.mkdir(parents=True, exist_ok=True)
    (aware_newer_dir / "state.json").write_text(
        json.dumps(
            {
                "session_id": "sess-aware-newer",
                "run_id": "run-aware-newer",
                "status": "running",
                "updated_at_utc": "2026-02-21T00:00:01+00:00",
            }
        ).decode(),
        encoding="utf-8",
    )

    mock_settings = MagicMock()
    mock_settings.session_dir = tmp_path
    monkeypatch.setattr("thegent.cli.commands.impl.ThegentSettings", lambda: mock_settings)
    mock_registry = MagicMock()
    monkeypatch.setattr("thegent.cli.commands.impl.RunRegistry", lambda *_args, **_kwargs: mock_registry)

    result = resume_impl()

    assert result["session_id"] == "sess-aware-newer"
    assert result["run_id"] == "run-aware-newer"
    mock_registry.register_resume.assert_called_once_with("run-aware-newer")


def test_resume_impl_without_session_id_normalizes_whitespace_contract_strings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    session_dir = tmp_path / "sess-normalized"
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / "state.json").write_text(
        json.dumps(
            {
                "session_id": "  sess-normalized  ",
                "run_id": "  run-normalized  ",
                "status": "running",
                "updated_at_utc": "2026-02-21T00:00:00+00:00",
            }
        ).decode(),
        encoding="utf-8",
    )

    mock_settings = MagicMock()
    mock_settings.session_dir = tmp_path
    monkeypatch.setattr("thegent.cli.commands.impl.ThegentSettings", lambda: mock_settings)
    mock_registry = MagicMock()
    monkeypatch.setattr("thegent.cli.commands.impl.RunRegistry", lambda *_args, **_kwargs: mock_registry)

    result = resume_impl()

    assert result["session_id"] == "sess-normalized"
    assert result["run_id"] == "run-normalized"
    mock_registry.register_resume.assert_called_once_with("run-normalized")


def test_top_level_resume_passthrough(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, str | None] = {}

    def _fake_resume_cmd(*, session_id: str | None = None, prompt: str | None = None) -> None:
        captured["session_id"] = session_id
        captured["prompt"] = prompt

    monkeypatch.setattr("thegent.cli.commands.cli.resume_cmd", _fake_resume_cmd)

    result = runner.invoke(app, ["resume", "sess-top", "--prompt", "continue"])

    assert result.exit_code == 0
    assert captured["session_id"] == "sess-top"
    assert captured["prompt"] == "continue"


def test_session_list_impl_normalizes_contract_strings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    session_dir = tmp_path / "sess-contract"
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / "state.json").write_text(
        json.dumps(
            {
                "session_id": "  sess-contract  ",
                "run_id": "  run-contract  ",
                "status": "running",
                "updated_at_utc": "2026-02-21T00:00:00+00:00",
            }
        ).decode(),
        encoding="utf-8",
    )

    mock_settings = MagicMock()
    mock_settings.session_dir = tmp_path
    monkeypatch.setattr("thegent.cli.commands.session_ops_impl.ThegentSettings", lambda: mock_settings)
    monkeypatch.setattr(
        "thegent.cli.commands.session_ops_impl.RunRegistry",
        lambda *_args, **_kwargs: MagicMock(list_runs=lambda **_kw: []),
    )

    rows = session_list_impl(all_sessions=True)

    assert rows[0]["session_id"] == "sess-contract"
    assert rows[0]["run_id"] == "run-contract"


def test_run_resume_prompt_passthrough(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, str | None | list[str] | None] = {}

    def _fake_resume_cmd(
        *,
        session_id: str | None = None,
        prompt: str | None = None,
        skills: list[str] | None = None,
    ) -> None:
        captured["session_id"] = session_id
        captured["prompt"] = prompt
        captured["skills"] = skills

    monkeypatch.setattr("thegent.cli.commands.cli.resume_cmd", _fake_resume_cmd)

    result = runner.invoke(app, ["run", "resume", "sess-run", "--prompt", "continue from this state"])

    assert result.exit_code == 0
    assert captured["session_id"] == "sess-run"
    assert captured["prompt"] == "continue from this state"
    assert captured["skills"] is None
