"""WL-119 low-risk slice tests."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from thegent.cli.commands.impl import (
    _build_run_event_details,
    _resolve_grounding_sources_for_output,
)
from thegent.execution import RunRegistry
from thegent.utils.routing_impl.grounding import (
    extract_grounding_sources,
    extract_grounding_sources_from_payload,
    normalize_grounding_source_url,
)


def test_extract_grounding_sources_dedupes_and_preserves_order() -> None:
    text = "See https://a.example/x and https://b.example/y then https://a.example/x"
    assert extract_grounding_sources(text) == ["https://a.example/x", "https://b.example/y"]


def test_extract_grounding_sources_normalizes_and_dedupes_urls() -> None:
    text = "Refs: HTTPS://A.EXAMPLE/x, https://a.example/x. https://b.example/y?"
    assert extract_grounding_sources(text) == ["https://a.example/x", "https://b.example/y"]


def test_extract_grounding_sources_empty() -> None:
    assert extract_grounding_sources("") == []


def test_normalize_grounding_source_url_trims_and_lowercases_host() -> None:
    normalized = normalize_grounding_source_url("  HTTPS://Docs.Example.com/Ref?id=1.  ")
    assert normalized == "https://docs.example.com/Ref?id=1"


def test_normalize_grounding_source_url_removes_default_ports() -> None:
    assert normalize_grounding_source_url("https://docs.example.com:443/ref") == "https://docs.example.com/ref"
    assert normalize_grounding_source_url("http://docs.example.com:80/ref") == "http://docs.example.com/ref"


def test_normalize_grounding_source_url_removes_default_root_trailing_slash() -> None:
    assert normalize_grounding_source_url("https://docs.example.com/") == "https://docs.example.com"
    assert normalize_grounding_source_url("http://docs.example.com/") == "http://docs.example.com"
    assert normalize_grounding_source_url("https://docs.example.com/path/") == "https://docs.example.com/path/"


def test_normalize_grounding_source_url_unwraps_wrapped_literals() -> None:
    assert normalize_grounding_source_url("<https://docs.example.com/ref>") == "https://docs.example.com/ref"
    assert normalize_grounding_source_url("(https://docs.example.com/ref)") == "https://docs.example.com/ref"
    assert normalize_grounding_source_url("[https://docs.example.com/ref]") == "https://docs.example.com/ref"


def test_extract_grounding_sources_from_payload_grounding_metadata() -> None:
    payload = {
        "groundingMetadata": {
            "groundingChunks": [
                {"web": {"uri": "https://a.example/source-1", "title": "A"}},
                {"web": {"uri": "https://b.example/source-2", "title": "B"}},
                {"web": {"uri": "https://a.example/source-1", "title": "A duplicate"}},
            ]
        }
    }
    assert extract_grounding_sources_from_payload(payload) == [
        "https://a.example/source-1",
        "https://b.example/source-2",
    ]


def test_extract_grounding_sources_from_payload_supports_source_url_keys() -> None:
    payload = {
        "groundingMetadata": {
            "groundingChunks": [
                {"web": {"sourceUrl": "https://a.example/source-1"}},
                {"web": {"sourceUrl": "https://b.example/source-2"}},
                {"web": {"sourceUrl": "https://a.example/source-1"}},
            ]
        }
    }
    assert extract_grounding_sources_from_payload(payload) == [
        "https://a.example/source-1",
        "https://b.example/source-2",
    ]


def test_resolve_grounding_sources_prefers_structured_result_list() -> None:
    resolved = _resolve_grounding_sources_for_output(
        stdout="plain text without urls",
        result_grounding_sources=["https://a.example/x", "https://a.example/x", "https://b.example/y"],
    )
    assert resolved == ["https://a.example/x", "https://b.example/y"]


def test_run_registry_finish_event_can_persist_grounding_sources(tmp_path: Path) -> None:
    registry = RunRegistry(tmp_path)
    event_details = _build_run_event_details(
        grounding_sources=["https://a.example/1", "https://b.example/2"],
        audio_transcript=None,
        audio_sources=[],
        context_usage_ratio=0.55,
    )
    assert event_details == {
        "grounding_sources": ["https://a.example/1", "https://b.example/2"],
        "context_usage_ratio": 0.55,
    }
    registry.register_end(
        run_id="run-grounding",
        exit_code=0,
        status="completed",
        ended_at_utc=datetime.now(UTC).isoformat(),
        duration_s=0.1,
        event_details=event_details,
    )

    rows = registry.registry_path.read_text(encoding="utf-8").splitlines()
    assert rows
    assert '"grounding_sources": ["https://a.example/1", "https://b.example/2"]' in rows[-1]
    assert '"context_usage_ratio": 0.55' in rows[-1]
