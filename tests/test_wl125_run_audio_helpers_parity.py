from __future__ import annotations

from thegent.cli.commands import impl


def test_wl125_build_audio_summary_metadata_wrapper_delegates(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake(*, audio_transcript, audio_sources):
        captured["audio_transcript"] = audio_transcript
        captured["audio_sources"] = audio_sources
        return {"ok": True}

    monkeypatch.setattr(
        "thegent.cli.commands.impl.run_audio_helpers.build_audio_summary_metadata",
        _fake,
    )

    output = impl._build_audio_summary_metadata(
        audio_transcript="transcript",
        audio_sources=["/tmp/a.txt"],
    )

    assert output == {"ok": True}
    assert captured["audio_transcript"] == "transcript"
    assert captured["audio_sources"] == ["/tmp/a.txt"]
