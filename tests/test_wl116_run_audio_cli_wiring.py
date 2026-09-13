"""WL-116 run app CLI wiring tests."""

from __future__ import annotations

from pathlib import Path

from thegent.cli.apps.run import run_agent


def test_run_agent_forwards_audio_and_grounding_flags(monkeypatch, tmp_path: Path) -> None:
    transcript = tmp_path / "sample.txt"
    transcript.write_text("speaker says hello", encoding="utf-8")

    captured: dict[str, object] = {}

    def fake_run_cmd(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr("thegent.cli.commands.cli.run_cmd", fake_run_cmd)

    run_agent(
        prompt="summarize this",
        agent="codex",
        bg=False,
        loop=False,
        cd=None,
        timeout=90,
        full=False,
        no_auto_agent=True,
        remote=None,
        audio=[str(transcript)],
        google_grounding=True,
    )

    assert captured["audio"] == [str(transcript)]
    assert captured["google_grounding"] is True
