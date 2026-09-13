"""WL-119 human-facing run output formatting tests."""

from __future__ import annotations

from thegent.cli.commands.cli import (
    _format_grounding_sources_lines,
    _format_transcript_summary_line,
)


def test_format_transcript_summary_line_from_audio_metadata() -> None:
    line = _format_transcript_summary_line({"transcript_length_chars": 42, "source_count": 2})
    assert line == "Transcript input: 42 chars from 2 files (~21 chars/file)"


def test_format_transcript_summary_line_uses_singular_file_label() -> None:
    line = _format_transcript_summary_line({"transcript_length_chars": 9, "source_count": 1})
    assert line == "Transcript input: 9 chars from 1 file"


def test_format_transcript_summary_line_uses_singular_char_label() -> None:
    line = _format_transcript_summary_line({"transcript_length_chars": 1, "source_count": 1})
    assert line == "Transcript input: 1 char from 1 file"


def test_format_transcript_summary_line_applies_thousands_separator() -> None:
    line = _format_transcript_summary_line({"transcript_length_chars": 12345, "source_count": 2})
    assert line == "Transcript input: 12,345 chars from 2 files (~6,172 chars/file)"


def test_format_transcript_summary_line_rejects_negative_metadata() -> None:
    line = _format_transcript_summary_line({"transcript_length_chars": -1, "source_count": 1})
    assert line is None


def test_format_transcript_summary_line_rejects_zero_source_count_metadata() -> None:
    line = _format_transcript_summary_line({"transcript_length_chars": 10, "source_count": 0})
    assert line is None


def test_format_transcript_summary_line_uses_empty_transcript_label() -> None:
    line = _format_transcript_summary_line({"transcript_length_chars": 0, "source_count": 2})
    assert line == "Transcript input: empty transcript from 2 files"


def test_format_grounding_sources_lines_includes_count_and_truncation() -> None:
    lines = _format_grounding_sources_lines(
        [
            "https://a.example/1",
            "https://b.example/2",
            "https://c.example/3",
            "https://d.example/4",
        ]
    )
    assert lines[0] == "Grounding sources: showing 3/4"
    assert "  - https://a.example/1" in lines
    assert "  - ... and 1 more" in lines
    assert "  - domains: a.example, b.example, c.example (+1 more)" in lines


def test_format_grounding_sources_lines_deduplicates_repeated_urls() -> None:
    lines = _format_grounding_sources_lines(
        ["https://a.example/1", "https://a.example/1", " https://b.example/2 ", "https://b.example/2"]
    )
    assert lines[0] == "Grounding sources: showing 2/2"
    assert lines.count("  - https://a.example/1") == 1
    assert lines.count("  - https://b.example/2") == 1


def test_format_grounding_sources_lines_deduplicates_case_and_trailing_punctuation() -> None:
    lines = _format_grounding_sources_lines(
        [
            "HTTPS://A.EXAMPLE/1",
            "https://a.example/1.",
            "https://b.example/2;",
            "https://B.example/2",
        ]
    )
    assert lines[0] == "Grounding sources: showing 2/2"
    assert lines.count("  - https://a.example/1") == 1
    assert lines.count("  - https://b.example/2") == 1


def test_format_grounding_sources_lines_domain_rollup_normalizes_www_prefix() -> None:
    lines = _format_grounding_sources_lines(
        [
            "https://www.docs.example/path",
            "https://docs.example/another",
            "https://WWW.blog.example/post",
        ]
    )
    assert "  - domains: docs.example, blog.example" in lines


def test_format_grounding_sources_lines_deduplicates_root_trailing_slash_variants() -> None:
    lines = _format_grounding_sources_lines(["https://a.example/", "https://a.example"])
    assert lines[0] == "Grounding sources: showing 1/1"
    assert lines.count("  - https://a.example") == 1
