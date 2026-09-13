"""WL-116 audio transcript passthrough tests.

Tests cover:
- transcribe_audio_file: OpenAI Whisper API integration
- build_codex_audio_include: Codex Responses API include list
- inject_transcript_into_prompt: transcript injection into prompts
- load_transcripts: binary audio routing through Whisper
- RunResult.audio_transcript field presence

# @trace WL-116
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from thegent.agents.audio_inputs import (
    _BINARY_AUDIO_SUFFIXES,
    _TEXT_TRANSCRIPT_SUFFIXES,
    build_codex_audio_include,
    inject_transcript_into_prompt,
    load_transcripts,
    transcribe_audio_file,
)
from thegent.agents.base import RunResult

# ---------------------------------------------------------------------------
# build_codex_audio_include
# ---------------------------------------------------------------------------


def test_build_codex_audio_include_returns_list() -> None:
    """build_codex_audio_include must return a list."""
    # @trace WL-116
    result = build_codex_audio_include()
    assert isinstance(result, list)


def test_build_codex_audio_include_contains_expected_key() -> None:
    """The Codex include list must contain item.input_audio.transcript."""
    # @trace WL-116
    result = build_codex_audio_include()
    assert "item.input_audio.transcript" in result


def test_build_codex_audio_include_is_stable() -> None:
    """build_codex_audio_include must be deterministic across calls."""
    # @trace WL-116
    assert build_codex_audio_include() == build_codex_audio_include()


# ---------------------------------------------------------------------------
# inject_transcript_into_prompt
# ---------------------------------------------------------------------------


def test_inject_transcript_into_prompt_wraps_in_tags() -> None:
    """Injected transcript must be surrounded by [AUDIO TRANSCRIPT] tags."""
    # @trace WL-116
    result = inject_transcript_into_prompt("do the task", "speaker said hello")
    assert "[AUDIO TRANSCRIPT]" in result
    assert "[/AUDIO TRANSCRIPT]" in result


def test_inject_transcript_into_prompt_prepends_transcript() -> None:
    """Transcript block must come before the original prompt."""
    # @trace WL-116
    prompt = "analyse this"
    transcript = "hello world"
    result = inject_transcript_into_prompt(prompt, transcript)
    transcript_pos = result.index("[AUDIO TRANSCRIPT]")
    prompt_pos = result.index(prompt)
    assert transcript_pos < prompt_pos


def test_inject_transcript_into_prompt_contains_transcript_text() -> None:
    """The transcript text must appear verbatim in the result."""
    # @trace WL-116
    transcript = "the speaker said something important"
    result = inject_transcript_into_prompt("do something", transcript)
    assert transcript in result


def test_inject_transcript_into_prompt_contains_original_prompt() -> None:
    """The original prompt must appear verbatim in the result."""
    # @trace WL-116
    prompt = "summarize the content for me"
    result = inject_transcript_into_prompt(prompt, "words spoken")
    assert prompt in result


def test_inject_transcript_into_prompt_exact_format() -> None:
    """Verify the exact output format of inject_transcript_into_prompt."""
    # @trace WL-116
    result = inject_transcript_into_prompt("my prompt", "my transcript")
    expected = "[AUDIO TRANSCRIPT]\nmy transcript\n[/AUDIO TRANSCRIPT]\n\nmy prompt"
    assert result == expected


# ---------------------------------------------------------------------------
# transcribe_audio_file: error conditions
# ---------------------------------------------------------------------------


def test_transcribe_audio_file_raises_on_missing_file(tmp_path: Path) -> None:
    """transcribe_audio_file must raise FileNotFoundError if file is absent."""
    # @trace WL-116
    missing = tmp_path / "nonexistent.mp3"
    with pytest.raises(FileNotFoundError, match="Audio file not found"):
        transcribe_audio_file(missing)


def test_transcribe_audio_file_raises_on_unsupported_suffix(tmp_path: Path) -> None:
    """transcribe_audio_file must raise ValueError for non-binary-audio suffixes."""
    # @trace WL-116
    txt_file = tmp_path / "transcript.txt"
    txt_file.write_text("hello", encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported audio file format"):
        transcribe_audio_file(txt_file)


def test_transcribe_audio_file_raises_on_missing_api_key(tmp_path: Path, monkeypatch) -> None:
    """transcribe_audio_file must raise RuntimeError when OPENAI_API_KEY is absent."""
    # @trace WL-116
    audio = tmp_path / "clip.mp3"
    audio.write_bytes(b"\xff\xfb\x00\x00")  # minimal MP3-like bytes
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY is not set"):
        transcribe_audio_file(audio)


def test_transcribe_audio_file_calls_openai_client(tmp_path: Path, monkeypatch) -> None:
    """transcribe_audio_file must call client.audio.transcriptions.create with correct args."""
    # @trace WL-116
    audio = tmp_path / "speech.wav"
    audio.write_bytes(b"RIFF\x00\x00\x00\x00WAVEfmt ")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

    mock_response = MagicMock()
    mock_response.text = "transcribed speech content"
    mock_client = MagicMock()
    mock_client.audio.transcriptions.create.return_value = mock_response

    with patch("openai.OpenAI", return_value=mock_client):
        result = transcribe_audio_file(audio, model="whisper-1")

    assert result == "transcribed speech content"
    mock_client.audio.transcriptions.create.assert_called_once()
    call_kwargs = mock_client.audio.transcriptions.create.call_args[1]
    assert call_kwargs["model"] == "whisper-1"


def test_transcribe_audio_file_passes_model_parameter(tmp_path: Path, monkeypatch) -> None:
    """transcribe_audio_file must pass the model parameter to the API."""
    # @trace WL-116
    audio = tmp_path / "audio.m4a"
    audio.write_bytes(b"\x00\x00\x00 ftyp")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

    mock_response = MagicMock()
    mock_response.text = "spoken words"
    mock_client = MagicMock()
    mock_client.audio.transcriptions.create.return_value = mock_response

    with patch("openai.OpenAI", return_value=mock_client):
        transcribe_audio_file(audio, model="whisper-large")

    call_kwargs = mock_client.audio.transcriptions.create.call_args[1]
    assert call_kwargs["model"] == "whisper-large"


# ---------------------------------------------------------------------------
# load_transcripts with binary audio
# ---------------------------------------------------------------------------


def test_load_transcripts_routes_binary_audio_to_whisper(tmp_path: Path, monkeypatch) -> None:
    """load_transcripts must call transcribe_audio_file for binary audio inputs."""
    # @trace WL-116
    audio = tmp_path / "recording.mp3"
    audio.write_bytes(b"\xff\xfb\x90\x00")

    with patch(
        "thegent.agents.audio_inputs.transcribe_audio_file",
        return_value="the recording transcript",
    ):
        transcript, used = load_transcripts([str(audio)])

    assert transcript == "the recording transcript"
    assert used == [str(audio)]


def test_load_transcripts_rejects_truly_unknown_suffix(tmp_path: Path) -> None:
    """load_transcripts must raise ValueError for suffixes not in either allowed set."""
    # @trace WL-116
    bad_file = tmp_path / "data.xyz"
    bad_file.write_bytes(b"garbage")
    with pytest.raises(ValueError, match="Unsupported --audio input"):
        load_transcripts([str(bad_file)])


# ---------------------------------------------------------------------------
# RunResult has audio_transcript field
# ---------------------------------------------------------------------------


def test_run_result_has_audio_transcript_field() -> None:
    """RunResult must expose audio_transcript: str | None at the dataclass level."""
    # @trace WL-116
    result = RunResult(exit_code=0, stdout="ok", stderr="")
    assert hasattr(result, "audio_transcript")
    assert result.audio_transcript is None


def test_run_result_audio_transcript_stores_value() -> None:
    """RunResult.audio_transcript must store a provided string value."""
    # @trace WL-116
    result = RunResult(exit_code=0, stdout="ok", stderr="", audio_transcript="hello transcript")
    assert result.audio_transcript == "hello transcript"


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------


def test_binary_audio_suffixes_contains_common_formats() -> None:
    """The binary audio suffix set must include standard audio container formats."""
    # @trace WL-116
    for fmt in (".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm"):
        assert fmt in _BINARY_AUDIO_SUFFIXES, f"Missing format: {fmt}"


def test_binary_and_text_suffix_sets_are_disjoint() -> None:
    """Binary audio and text transcript suffix sets must not overlap."""
    # @trace WL-116
    overlap = _BINARY_AUDIO_SUFFIXES & _TEXT_TRANSCRIPT_SUFFIXES
    assert overlap == set(), f"Overlapping suffixes detected: {overlap}"
