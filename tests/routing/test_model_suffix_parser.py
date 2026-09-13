"""Tests for GW-14: model suffix routing (ParsedModel API).

Covers parse_model_suffixes, apply_suffix_to_request, and resolve_suffix_model.

# @trace FR-ROUTE-014
"""

from __future__ import annotations

import pytest

from thegent.utils.routing_impl.model_suffix_parser import (
    ModelSuffix,
    apply_suffix_to_request,
    parse_model_suffixes,
    resolve_suffix_model,
)

# ---------------------------------------------------------------------------
# parse_model_suffixes
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-ROUTE-014")
def test_parse_model_no_suffix() -> None:
    """A bare model name yields empty suffixes and unchanged base_model."""
    result = parse_model_suffixes("gpt-4o")
    assert result.base_model == "gpt-4o"
    assert result.suffixes == []
    assert result.raw == "gpt-4o"


@pytest.mark.requirement("FR-ROUTE-014")
def test_parse_model_single_suffix_nitro() -> None:
    result = parse_model_suffixes("gpt-4o:nitro")
    assert result.base_model == "gpt-4o"
    assert result.suffixes == [ModelSuffix.NITRO]


@pytest.mark.requirement("FR-ROUTE-014")
def test_parse_model_single_suffix_floor() -> None:
    result = parse_model_suffixes("gpt-4o:floor")
    assert result.base_model == "gpt-4o"
    assert result.suffixes == [ModelSuffix.FLOOR]


@pytest.mark.requirement("FR-ROUTE-014")
def test_parse_model_thinking_suffix() -> None:
    result = parse_model_suffixes("claude-sonnet-4-5:thinking")
    assert result.base_model == "claude-sonnet-4-5"
    assert ModelSuffix.THINKING in result.suffixes


@pytest.mark.requirement("FR-ROUTE-014")
def test_parse_model_online_suffix() -> None:
    result = parse_model_suffixes("gpt-4o:online")
    assert result.base_model == "gpt-4o"
    assert ModelSuffix.ONLINE in result.suffixes


@pytest.mark.requirement("FR-ROUTE-014")
def test_parse_model_multiple_suffixes() -> None:
    """Multiple suffixes in order are all parsed."""
    result = parse_model_suffixes("anthropic/claude-sonnet-4-5:thinking:online")
    assert result.base_model == "anthropic/claude-sonnet-4-5"
    assert ModelSuffix.THINKING in result.suffixes
    assert ModelSuffix.ONLINE in result.suffixes
    assert len(result.suffixes) == 2


@pytest.mark.requirement("FR-ROUTE-014")
def test_parse_model_unknown_suffix_ignored() -> None:
    """Unknown suffix tokens are silently ignored; base_model is set correctly."""
    result = parse_model_suffixes("model:unknownsuffix")
    assert result.base_model == "model"
    assert result.suffixes == []


@pytest.mark.requirement("FR-ROUTE-014")
def test_parse_model_raw_preserved() -> None:
    """The raw attribute always reflects the original input string."""
    raw = "gpt-4o:nitro"
    result = parse_model_suffixes(raw)
    assert result.raw == raw


# ---------------------------------------------------------------------------
# ParsedModel properties
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-ROUTE-014")
def test_has_suffix_true() -> None:
    result = parse_model_suffixes("gpt-4o:nitro")
    assert result.has_suffix is True


@pytest.mark.requirement("FR-ROUTE-014")
def test_has_suffix_false() -> None:
    result = parse_model_suffixes("gpt-4o")
    assert result.has_suffix is False


@pytest.mark.requirement("FR-ROUTE-014")
def test_is_thinking() -> None:
    result = parse_model_suffixes("model:thinking")
    assert result.is_thinking is True
    assert parse_model_suffixes("model:nitro").is_thinking is False


@pytest.mark.requirement("FR-ROUTE-014")
def test_is_free_tier() -> None:
    result = parse_model_suffixes("model:free")
    assert result.is_free_tier is True
    assert parse_model_suffixes("model:nitro").is_free_tier is False


@pytest.mark.requirement("FR-ROUTE-014")
def test_is_performance_tier() -> None:
    result = parse_model_suffixes("model:nitro")
    assert result.is_performance_tier is True
    assert parse_model_suffixes("model:floor").is_performance_tier is False


@pytest.mark.requirement("FR-ROUTE-014")
def test_needs_web_search() -> None:
    result = parse_model_suffixes("model:online")
    assert result.needs_web_search is True
    assert parse_model_suffixes("model:nitro").needs_web_search is False


# ---------------------------------------------------------------------------
# apply_suffix_to_request
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-ROUTE-014")
def test_apply_suffix_thinking_adds_reasoning() -> None:
    parsed = parse_model_suffixes("model:thinking")
    result = apply_suffix_to_request({}, parsed)
    assert result.get("reasoning") == {"effort": "high"}


@pytest.mark.requirement("FR-ROUTE-014")
def test_apply_suffix_thinking_does_not_overwrite_existing_reasoning() -> None:
    """Existing reasoning config is not overwritten by THINKING suffix."""
    parsed = parse_model_suffixes("model:thinking")
    body = {"reasoning": {"effort": "low", "custom": True}}
    result = apply_suffix_to_request(body, parsed)
    # Should not overwrite existing reasoning
    assert result["reasoning"]["effort"] == "low"
    assert result["reasoning"]["custom"] is True


@pytest.mark.requirement("FR-ROUTE-014")
def test_apply_suffix_online_adds_plugins() -> None:
    parsed = parse_model_suffixes("model:online")
    result = apply_suffix_to_request({}, parsed)
    plugins = result.get("plugins", [])
    assert any(p.get("id") == "web" for p in plugins)
    web_plugin = next(p for p in plugins if p.get("id") == "web")
    assert web_plugin.get("max_results") == 5


@pytest.mark.requirement("FR-ROUTE-014")
def test_apply_suffix_does_not_mutate() -> None:
    """apply_suffix_to_request must not mutate the original body."""
    parsed = parse_model_suffixes("model:thinking:online")
    original: dict = {"model": "base"}
    original_copy = dict(original)
    apply_suffix_to_request(original, parsed)
    assert original == original_copy


@pytest.mark.requirement("FR-ROUTE-014")
def test_apply_suffix_no_suffix_unchanged() -> None:
    """A ParsedModel with no suffixes returns a copy identical to the input."""
    parsed = parse_model_suffixes("model")
    body = {"model": "base", "temperature": 0.7}
    result = apply_suffix_to_request(body, parsed)
    assert result == body
    assert result is not body  # deep copy, not same object


@pytest.mark.requirement("FR-ROUTE-014")
def test_apply_suffix_nitro_sets_tg_tier_performance() -> None:
    parsed = parse_model_suffixes("model:nitro")
    result = apply_suffix_to_request({}, parsed)
    assert result.get("tg_tier") == "performance"


@pytest.mark.requirement("FR-ROUTE-014")
def test_apply_suffix_floor_sets_tg_tier_economy() -> None:
    parsed = parse_model_suffixes("model:floor")
    result = apply_suffix_to_request({}, parsed)
    assert result.get("tg_tier") == "economy"


@pytest.mark.requirement("FR-ROUTE-014")
def test_apply_suffix_free_sets_tg_tier_free() -> None:
    parsed = parse_model_suffixes("model:free")
    result = apply_suffix_to_request({}, parsed)
    assert result.get("tg_tier") == "free"


# ---------------------------------------------------------------------------
# resolve_suffix_model
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-ROUTE-014")
def test_resolve_suffix_model_with_map() -> None:
    """When model_map has a matching key, the mapped value is returned."""
    parsed = parse_model_suffixes("gpt-4o:nitro")
    model_map = {"gpt-4o:nitro": "gpt-4o-turbo"}
    assert resolve_suffix_model(parsed, model_map) == "gpt-4o-turbo"


@pytest.mark.requirement("FR-ROUTE-014")
def test_resolve_suffix_model_no_map_returns_base() -> None:
    """When model_map is None or has no matching key, base_model is returned."""
    parsed = parse_model_suffixes("gpt-4o:nitro")
    assert resolve_suffix_model(parsed, None) == "gpt-4o"
    assert resolve_suffix_model(parsed, {}) == "gpt-4o"


@pytest.mark.requirement("FR-ROUTE-014")
def test_resolve_suffix_model_floor_with_map() -> None:
    parsed = parse_model_suffixes("gpt-4o:floor")
    model_map = {"gpt-4o:floor": "gpt-4o-mini"}
    assert resolve_suffix_model(parsed, model_map) == "gpt-4o-mini"


@pytest.mark.requirement("FR-ROUTE-014")
def test_resolve_suffix_model_free_with_map() -> None:
    parsed = parse_model_suffixes("llama:free")
    model_map = {"llama:free": "llama-3-8b-free"}
    assert resolve_suffix_model(parsed, model_map) == "llama-3-8b-free"


@pytest.mark.requirement("FR-ROUTE-014")
def test_resolve_suffix_model_non_tier_suffix_returns_base() -> None:
    """THINKING/ONLINE/EXTENDED suffixes are not tier-mapped; base_model returned."""
    parsed = parse_model_suffixes("model:thinking")
    model_map = {"model:thinking": "thinking-model"}
    # THINKING is not a tier suffix, so model_map is not consulted
    assert resolve_suffix_model(parsed, model_map) == "model"
