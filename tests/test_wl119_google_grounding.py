"""WL-119 Google Search Grounding via Gemini API passthrough.

Tests for agents/grounding.py and impl.py grounding wire-in.

# @trace WL-119
"""

from __future__ import annotations

import inspect
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from thegent.agents.base import RunResult
from thegent.agents.grounding import (
    GEMINI_GROUNDING_AGENTS,
    GroundingSource,
    _resolve_gemini_api_key,
    _resolve_gemini_model,
    build_grounding_tools_arg,
    extract_grounding_metadata_sources,
    run_gemini_with_grounding,
)

# ---------------------------------------------------------------------------
# build_grounding_tools_arg
# ---------------------------------------------------------------------------


def test_build_grounding_tools_arg_returns_google_search_tool() -> None:
    # @trace WL-119
    tools = build_grounding_tools_arg()
    assert tools == [{"google_search": {}}]


def test_build_grounding_tools_arg_returns_list() -> None:
    # @trace WL-119
    tools = build_grounding_tools_arg()
    assert isinstance(tools, list)
    assert len(tools) == 1


def test_build_grounding_tools_arg_idempotent() -> None:
    # @trace WL-119 -- each call returns a fresh list (no shared mutation)
    tools1 = build_grounding_tools_arg()
    tools2 = build_grounding_tools_arg()
    assert tools1 == tools2
    assert tools1 is not tools2


# ---------------------------------------------------------------------------
# extract_grounding_metadata_sources
# ---------------------------------------------------------------------------


def test_extract_grounding_metadata_sources_standard_payload() -> None:
    # @trace WL-119
    payload: dict[str, Any] = {
        "groundingMetadata": {
            "groundingChunks": [
                {"web": {"uri": "https://a.example/page-1", "title": "A"}},
                {"web": {"uri": "https://b.example/page-2", "title": "B"}},
            ]
        }
    }
    result = extract_grounding_metadata_sources(payload)
    assert result == ["https://a.example/page-1", "https://b.example/page-2"]


def test_extract_grounding_metadata_sources_deduplicates() -> None:
    # @trace WL-119 -- duplicate URIs must appear only once
    payload: dict[str, Any] = {
        "groundingMetadata": {
            "groundingChunks": [
                {"web": {"uri": "https://a.example/x"}},
                {"web": {"uri": "https://a.example/x"}},
                {"web": {"uri": "https://b.example/y"}},
            ]
        }
    }
    result = extract_grounding_metadata_sources(payload)
    assert result == ["https://a.example/x", "https://b.example/y"]


def test_extract_grounding_metadata_sources_empty_payload() -> None:
    # @trace WL-119
    assert extract_grounding_metadata_sources({}) == []


def test_extract_grounding_metadata_sources_missing_grounding_metadata() -> None:
    # @trace WL-119
    payload: dict[str, Any] = {"someOtherKey": "value"}
    assert extract_grounding_metadata_sources(payload) == []


def test_extract_grounding_metadata_sources_empty_chunks() -> None:
    # @trace WL-119
    payload: dict[str, Any] = {"groundingMetadata": {"groundingChunks": []}}
    assert extract_grounding_metadata_sources(payload) == []


def test_extract_grounding_metadata_sources_skips_chunks_without_web_uri() -> None:
    # @trace WL-119 -- chunks with missing uri field must be silently skipped
    payload: dict[str, Any] = {
        "groundingMetadata": {
            "groundingChunks": [
                {"web": {}},  # no uri
                {"web": {"uri": "https://good.example/page"}},
                {"notWeb": {"uri": "https://ignored.example/page"}},
            ]
        }
    }
    result = extract_grounding_metadata_sources(payload)
    assert result == ["https://good.example/page"]


def test_extract_grounding_metadata_sources_preserves_order() -> None:
    # @trace WL-119
    payload: dict[str, Any] = {
        "groundingMetadata": {
            "groundingChunks": [
                {"web": {"uri": "https://first.example/"}},
                {"web": {"uri": "https://second.example/"}},
                {"web": {"uri": "https://third.example/"}},
            ]
        }
    }
    result = extract_grounding_metadata_sources(payload)
    assert result == ["https://first.example/", "https://second.example/", "https://third.example/"]


# ---------------------------------------------------------------------------
# _resolve_gemini_model
# ---------------------------------------------------------------------------


def test_resolve_gemini_model_returns_provided_model() -> None:
    # @trace WL-119
    assert _resolve_gemini_model("gemini/gemini-2.0-flash-exp") == "gemini/gemini-2.0-flash-exp"


def test_resolve_gemini_model_defaults_when_none() -> None:
    # @trace WL-119
    result = _resolve_gemini_model(None)
    assert result == "gemini/gemini-2.0-flash"


# ---------------------------------------------------------------------------
# _resolve_gemini_api_key
# ---------------------------------------------------------------------------


def test_resolve_gemini_api_key_from_gemini_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    # @trace WL-119
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-abc")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    assert _resolve_gemini_api_key() == "test-key-abc"


def test_resolve_gemini_api_key_from_google_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    # @trace WL-119
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key-xyz")
    assert _resolve_gemini_api_key() == "google-key-xyz"


def test_resolve_gemini_api_key_raises_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    # @trace WL-119 -- must fail loudly when API key is absent
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(ValueError, match="Gemini API key"):
        _resolve_gemini_api_key()


# ---------------------------------------------------------------------------
# GEMINI_GROUNDING_AGENTS membership
# ---------------------------------------------------------------------------


def test_gemini_grounding_agents_contains_gemini_and_antigravity() -> None:
    # @trace WL-119
    assert "gemini" in GEMINI_GROUNDING_AGENTS
    assert "antigravity" in GEMINI_GROUNDING_AGENTS


# ---------------------------------------------------------------------------
# run_gemini_with_grounding — non-Gemini model raises ValueError
# ---------------------------------------------------------------------------


def test_run_gemini_with_grounding_rejects_non_gemini_model(monkeypatch: pytest.MonkeyPatch) -> None:
    # @trace WL-119 -- must fail loudly for non-Gemini models
    monkeypatch.setenv("GEMINI_API_KEY", "dummy")
    with pytest.raises(ValueError, match="requires a Gemini model"):
        run_gemini_with_grounding("hello", model="claude-3-5-sonnet")


def test_run_gemini_with_grounding_rejects_openai_model(monkeypatch: pytest.MonkeyPatch) -> None:
    # @trace WL-119
    monkeypatch.setenv("GEMINI_API_KEY", "dummy")
    with pytest.raises(ValueError, match="requires a Gemini model"):
        run_gemini_with_grounding("hello", model="gpt-4o")


# ---------------------------------------------------------------------------
# run_gemini_with_grounding — happy path (mocked LiteLLM)
# ---------------------------------------------------------------------------


def _make_mock_completion_response(content: str, grounding_chunks: list[dict] | None = None) -> MagicMock:
    """Build a mock litellm completion response object."""
    choice = MagicMock()
    choice.message.content = content
    response = MagicMock()
    response.choices = [choice]

    grounding_meta: dict[str, Any] = {}
    if grounding_chunks is not None:
        grounding_meta = {"groundingChunks": grounding_chunks}

    response._hidden_params = {"groundingMetadata": grounding_meta} if grounding_chunks else {}
    response.model_extra = {}
    response.additional_kwargs = {}
    return response


def test_run_gemini_with_grounding_returns_run_result(monkeypatch: pytest.MonkeyPatch) -> None:
    # @trace WL-119
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    mock_response = _make_mock_completion_response("Test response text")

    with patch("litellm.completion", return_value=mock_response):
        result = run_gemini_with_grounding("What is 2+2?", model="gemini/gemini-2.0-flash")

    assert isinstance(result, RunResult)
    assert result.exit_code == 0
    assert result.stdout == "Test response text"
    assert result.stderr == ""


def test_run_gemini_with_grounding_extracts_grounding_sources(monkeypatch: pytest.MonkeyPatch) -> None:
    # @trace WL-119
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    chunks = [
        {"web": {"uri": "https://source1.example/", "title": "Source 1"}},
        {"web": {"uri": "https://source2.example/", "title": "Source 2"}},
    ]
    mock_response = _make_mock_completion_response("Grounded response", grounding_chunks=chunks)

    with patch("litellm.completion", return_value=mock_response):
        result = run_gemini_with_grounding("Search query", model="gemini/gemini-2.0-flash")

    assert result.grounding_sources == ["https://source1.example/", "https://source2.example/"]


def test_run_gemini_with_grounding_grounding_sources_none_when_no_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # @trace WL-119 -- no groundingMetadata -> grounding_sources is None
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    mock_response = _make_mock_completion_response("Response without grounding")

    with patch("litellm.completion", return_value=mock_response):
        result = run_gemini_with_grounding("Plain prompt", model="gemini/gemini-2.0-flash")

    assert result.grounding_sources is None


def test_run_gemini_with_grounding_passes_tools_to_litellm(monkeypatch: pytest.MonkeyPatch) -> None:
    # @trace WL-119 -- must pass tools=[{"google_search": {}}] to litellm
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    mock_response = _make_mock_completion_response("response")

    with patch("litellm.completion", return_value=mock_response) as mock_completion:
        run_gemini_with_grounding("prompt", model="gemini/gemini-2.0-flash")

    call_kwargs = mock_completion.call_args.kwargs
    assert call_kwargs["tools"] == [{"google_search": {}}]


def test_run_gemini_with_grounding_raises_runtime_error_on_api_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # @trace WL-119 -- must fail loudly (RuntimeError) on API failure
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    with patch("litellm.completion", side_effect=Exception("API quota exceeded")):
        with pytest.raises(RuntimeError, match="Gemini grounding API call failed"):
            run_gemini_with_grounding("prompt", model="gemini/gemini-2.0-flash")


# ---------------------------------------------------------------------------
# GroundingSource dataclass
# ---------------------------------------------------------------------------


def test_grounding_source_dataclass_has_url_and_optional_title() -> None:
    # @trace WL-119
    src = GroundingSource(url="https://example.com", title="Example")
    assert src.url == "https://example.com"
    assert src.title == "Example"


def test_grounding_source_title_defaults_to_none() -> None:
    # @trace WL-119
    src = GroundingSource(url="https://example.com")
    assert src.title is None


# ---------------------------------------------------------------------------
# impl.py wiring: run_impl accepts google_grounding parameter
# ---------------------------------------------------------------------------


def test_run_impl_accepts_google_grounding_parameter() -> None:
    # @trace WL-119
    from thegent.cli.commands.impl import run_impl

    sig = inspect.signature(run_impl)
    assert "google_grounding" in sig.parameters
    param = sig.parameters["google_grounding"]
    assert param.default is False


def test_run_impl_rejects_google_grounding_for_non_gemini_agent() -> None:
    # @trace WL-119 -- must fail loudly if used with non-Gemini agent
    from thegent.cli.commands.impl import run_impl

    result = run_impl(
        agent="claude",
        prompt="hello",
        cd=None,
        mode="read",
        timeout=10,
        google_grounding=True,
    )
    assert result.get("exit_code") == 1
    assert "Gemini" in result.get("error", "")
