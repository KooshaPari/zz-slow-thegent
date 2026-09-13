from __future__ import annotations

from pathlib import Path

import pytest
from click.exceptions import Exit

from thegent.cli.apps.skills import skills_list, skills_select
from thegent.cli.commands.cli import _inject_skill_instructions
from thegent.cli.commands.impl import resume_impl
from thegent.skills.discovery import SkillInfo


def test_wl101_inject_skill_instructions_appends_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _fake_load_skill(name: str) -> dict[str, str] | None:
        return {"content": f"# {name} instructions"}

    monkeypatch.setattr("thegent.skills.discovery.load_skill", _fake_load_skill)
    prompt = _inject_skill_instructions("base prompt", ["alpha", "beta"])
    assert "base prompt" in prompt
    assert "## Skill: alpha" in prompt
    assert "## Skill: beta" in prompt


def test_wl101_inject_skill_instructions_errors_on_missing_skill(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("thegent.skills.discovery.load_skill", lambda _name: None)
    with pytest.raises(Exit):
        _inject_skill_instructions("base prompt", ["missing"])


def test_wl101_resume_impl_applies_skill_to_followup_prompt(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    session_root = tmp_path / "sessions"
    session_id = "sess-1"
    session_dir = session_root / session_id
    session_dir.mkdir(parents=True)
    state_path = session_dir / "state.json"
    state_path.write_text(
        '{"session_id":"sess-1","run_id":"run-1","status":"paused","updated_at_utc":"2026-02-21T00:00:00+00:00"}',
        encoding="utf-8",
    )

    class _FakeSettings:
        def __init__(self) -> None:
            self.session_dir = session_root

    sent: dict[str, str] = {}

    def _fake_send(
        session_id: str, message: str, msg_type: str = "reprompt"
    ) -> tuple[bool, str]:
        sent["session_id"] = session_id
        sent["message"] = message
        sent["msg_type"] = msg_type
        return True, "ok"

    class _FakeRegistry:
        def __init__(self, _session_dir):
            pass

        def register_resume(self, run_id: str) -> None:
            sent["run_id"] = run_id

    monkeypatch.setattr("thegent.cli.commands.impl.ThegentSettings", _FakeSettings)
    monkeypatch.setattr("thegent.cli.commands.impl.session_send_impl", _fake_send)
    monkeypatch.setattr("thegent.cli.commands.impl.RunRegistry", _FakeRegistry)
    monkeypatch.setattr(
        "thegent.skills.discovery.load_skill",
        lambda name: {"content": f"# {name} instructions"},
    )

    result = resume_impl(session_id=session_id, prompt="continue", skills=["alpha"])
    assert result["prompt_sent"] is True
    assert sent["run_id"] == "run-1"
    assert sent["session_id"] == session_id
    assert sent["msg_type"] == "reprompt"
    assert "continue" in sent["message"]
    assert "## Skill: alpha" in sent["message"]


def test_wl101_skills_select_errors_on_unknown_skill(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("thegent.skills.discovery.load_skill", lambda _name: None)

    with pytest.raises(Exit):
        skills_select("missing-skill")

    stderr = capsys.readouterr().out
    assert "Skill not found: missing-skill" in stderr


def test_wl101_skills_select_shell_quotes_name_with_spaces(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        "thegent.cli.apps.skills.load_skill", lambda _name: {"name": "x"}
    )
    skills_select("team alpha")
    stdout = capsys.readouterr().out
    assert "--skill 'team alpha'" in stdout


def test_wl101_skills_select_trims_input_name(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    loaded: dict[str, str] = {}

    def _fake_load_skill(name: str) -> dict[str, str]:
        loaded["name"] = name
        return {"name": "x"}

    monkeypatch.setattr("thegent.cli.apps.skills.load_skill", _fake_load_skill)
    skills_select("  alpha  ")
    stdout = capsys.readouterr().out
    assert loaded["name"] == "alpha"
    assert "Selected skill:" in stdout
    assert "--skill alpha" in stdout


def test_wl101_skills_select_rejects_control_characters(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(Exit):
        skills_select("alpha\nbeta")
    stderr = capsys.readouterr().out
    assert "must not contain control characters" in stderr


def test_wl101_skills_select_rejects_blank_name(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(Exit):
        skills_select("   ")
    stderr = capsys.readouterr().out
    assert "must be non-empty" in stderr


def test_wl101_skills_select_rejects_ascii_unit_separator(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(Exit):
        skills_select("alpha\x1fbeta")
    stderr = capsys.readouterr().out
    assert "must not contain control characters" in stderr


def test_wl101_skills_list_json_output(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        "thegent.cli.apps.skills.discover_skills",
        lambda: [
            SkillInfo(
                name="alpha",
                description="Alpha skill",
                version="1.2.3",
                entrypoint="SKILL.md",
                path=Path("/tmp/alpha"),
                skill_md_path=Path("/tmp/alpha/SKILL.md"),
                skill_json_path=Path("/tmp/alpha/skill.json"),
            )
        ],
    )
    skills_list(json_output=True)
    stdout = capsys.readouterr().out
    assert '"name": "alpha"' in stdout
    assert '"description": "Alpha skill"' in stdout


def test_wl101_skills_list_json_output_empty(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("thegent.cli.apps.skills.discover_skills", list)
    skills_list(json_output=True)
    stdout = capsys.readouterr().out
    assert stdout.strip() == "[]"


def test_wl101_skills_list_json_output_sorted_by_name(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        "thegent.cli.apps.skills.discover_skills",
        lambda: [
            SkillInfo(
                name="zeta",
                description="Zeta skill",
                version="1.0.0",
                entrypoint="SKILL.md",
                path=Path("/tmp/zeta"),
                skill_md_path=Path("/tmp/zeta/SKILL.md"),
                skill_json_path=Path("/tmp/zeta/skill.json"),
            ),
            SkillInfo(
                name="alpha",
                description="Alpha skill",
                version="1.0.0",
                entrypoint="SKILL.md",
                path=Path("/tmp/alpha"),
                skill_md_path=Path("/tmp/alpha/SKILL.md"),
                skill_json_path=Path("/tmp/alpha/skill.json"),
            ),
        ],
    )
    skills_list(json_output=True)
    stdout = capsys.readouterr().out
    assert stdout.index('"name": "alpha"') < stdout.index('"name": "zeta"')


def test_wl101_skills_list_json_output_stable_when_names_case_collide(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        "thegent.cli.apps.skills.discover_skills",
        lambda: [
            SkillInfo(
                name="alpha",
                description="lower",
                version="1.0.0",
                entrypoint="SKILL.md",
                path=Path("/tmp/alpha"),
                skill_md_path=Path("/tmp/alpha/SKILL.md"),
                skill_json_path=Path("/tmp/alpha/skill.json"),
            ),
            SkillInfo(
                name="Alpha",
                description="upper",
                version="1.0.0",
                entrypoint="SKILL.md",
                path=Path("/tmp/Alpha"),
                skill_md_path=Path("/tmp/Alpha/SKILL.md"),
                skill_json_path=Path("/tmp/Alpha/skill.json"),
            ),
        ],
    )
    skills_list(json_output=True)
    stdout = capsys.readouterr().out
    assert stdout.index('"name": "Alpha"') < stdout.index('"name": "alpha"')
