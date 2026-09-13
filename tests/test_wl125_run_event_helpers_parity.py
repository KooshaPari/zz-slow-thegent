from __future__ import annotations

from thegent.cli.commands import impl


def test_wl125_resolve_audio_transcript_wrapper_delegates(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake(*, injected_audio_transcript, result_audio_transcript):
        captured["injected"] = injected_audio_transcript
        captured["result"] = result_audio_transcript
        return "resolved"

    monkeypatch.setattr(
        "thegent.cli.commands.impl.run_event_helpers.resolve_audio_transcript_for_output",
        _fake,
    )

    output = impl._resolve_audio_transcript_for_output(
        injected_audio_transcript="from-flag",
        result_audio_transcript="from-result",
    )

    assert output == "resolved"
    assert captured["injected"] == "from-flag"
    assert captured["result"] == "from-result"


def test_wl125_build_run_event_details_wrapper_delegates(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake(
        *, grounding_sources, audio_transcript, audio_sources, context_usage_ratio
    ):
        captured["grounding_sources"] = grounding_sources
        captured["audio_transcript"] = audio_transcript
        captured["audio_sources"] = audio_sources
        captured["context_usage_ratio"] = context_usage_ratio
        return {"ok": True}

    monkeypatch.setattr(
        "thegent.cli.commands.impl.run_event_helpers.build_run_event_details", _fake
    )

    output = impl._build_run_event_details(
        grounding_sources=["https://example.com"],
        audio_transcript="transcript",
        audio_sources=["mic"],
        context_usage_ratio=0.9,
    )

    assert output == {"ok": True}
    assert captured["grounding_sources"] == ["https://example.com"]
    assert captured["audio_transcript"] == "transcript"
    assert captured["audio_sources"] == ["mic"]
    assert captured["context_usage_ratio"] == 0.9
