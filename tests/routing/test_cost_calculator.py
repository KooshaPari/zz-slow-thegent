"""Tests for GW-33: per-request LLM cost calculator.

# @trace FR-COST-033
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from thegent.utils.routing_impl.cost_calculator import (
    ModelPricing,
    calculate_cost,
    calculate_cost_from_response,
    format_cost_header_value,
    get_model_pricing,
)

# ---------------------------------------------------------------------------
# calculate_cost — known model
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-COST-033")
def test_calculate_cost_known_model() -> None:
    """gpt-4o: 1000 prompt + 500 completion → exact USD."""
    # gpt-4o: $2.50/1M prompt, $10.00/1M completion
    expected = (1000 / 1_000_000) * 2.50 + (500 / 1_000_000) * 10.00
    result = calculate_cost("gpt-4o", 1000, 500)
    assert abs(result - expected) < 1e-10, f"Expected {expected}, got {result}"


# ---------------------------------------------------------------------------
# calculate_cost — unknown model
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-COST-033")
def test_calculate_cost_unknown_model() -> None:
    """Unknown model returns 0.0 without raising."""
    result = calculate_cost("totally-unknown-model-xyz-9999", 1000, 500)
    assert result == 0.0


# ---------------------------------------------------------------------------
# calculate_cost — zero tokens
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-COST-033")
def test_calculate_cost_zero_tokens() -> None:
    """0 prompt + 0 completion = 0.0 cost regardless of model."""
    result = calculate_cost("gpt-4o", 0, 0)
    assert result == 0.0


# ---------------------------------------------------------------------------
# calculate_cost — provider prefix stripped
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-COST-033")
def test_calculate_cost_provider_prefix() -> None:
    """'openai/gpt-4o' resolves to same pricing as bare 'gpt-4o'."""
    bare = calculate_cost("gpt-4o", 1000, 500)
    prefixed = calculate_cost("openai/gpt-4o", 1000, 500)
    assert bare == prefixed


# ---------------------------------------------------------------------------
# calculate_cost_from_response — dict format
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-COST-033")
def test_calculate_cost_from_response_dict_format() -> None:
    """Dict response with usage and model computes correct cost."""
    response = {
        "model": "gpt-4o",
        "usage": {
            "prompt_tokens": 1000,
            "completion_tokens": 500,
        },
    }
    expected = calculate_cost("gpt-4o", 1000, 500)
    result = calculate_cost_from_response(response)
    assert abs(result - expected) < 1e-10


@pytest.mark.requirement("FR-COST-033")
def test_calculate_cost_from_response_dict_no_usage() -> None:
    """Dict response without 'usage' key returns 0.0."""
    response = {"model": "gpt-4o"}
    result = calculate_cost_from_response(response)
    assert result == 0.0


# ---------------------------------------------------------------------------
# calculate_cost_from_response — object format (LiteLLM ModelResponse)
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-COST-033")
def test_calculate_cost_from_response_object_format() -> None:
    """Object response with .usage attrs computes correct cost."""
    usage = MagicMock()
    usage.prompt_tokens = 1000
    usage.completion_tokens = 500

    response = MagicMock()
    response.model = "gpt-4o"
    response.usage = usage

    expected = calculate_cost("gpt-4o", 1000, 500)
    result = calculate_cost_from_response(response)
    assert abs(result - expected) < 1e-10


@pytest.mark.requirement("FR-COST-033")
def test_calculate_cost_from_response_object_no_usage() -> None:
    """Object response where .usage is None returns 0.0."""
    response = MagicMock()
    response.usage = None

    result = calculate_cost_from_response(response)
    assert result == 0.0


# ---------------------------------------------------------------------------
# get_model_pricing — exact match
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-COST-033")
def test_get_model_pricing_exact_match() -> None:
    """Exact model name in FALLBACK_PRICING returns a ModelPricing instance."""
    pricing = get_model_pricing("gpt-4o")
    assert pricing is not None
    assert isinstance(pricing, ModelPricing)
    assert pricing.model == "gpt-4o"
    assert pricing.prompt_usd_per_1m == 2.50
    assert pricing.completion_usd_per_1m == 10.00
    assert pricing.currency == "USD"


@pytest.mark.requirement("FR-COST-033")
def test_get_model_pricing_missing() -> None:
    """Completely unknown model returns None."""
    result = get_model_pricing("no-such-model-99999")
    assert result is None


# ---------------------------------------------------------------------------
# get_model_pricing — provider prefix stripped
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-COST-033")
def test_get_model_pricing_prefix_stripped() -> None:
    """'openai/gpt-4o' resolves to same pricing as 'gpt-4o' via prefix stripping."""
    pricing_bare = get_model_pricing("gpt-4o")
    pricing_prefixed = get_model_pricing("openai/gpt-4o")
    assert pricing_bare is not None
    assert pricing_prefixed is not None
    assert pricing_bare.prompt_usd_per_1m == pricing_prefixed.prompt_usd_per_1m
    assert pricing_bare.completion_usd_per_1m == pricing_prefixed.completion_usd_per_1m


# ---------------------------------------------------------------------------
# format_cost_header_value
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-COST-033")
def test_format_cost_header_value_precision() -> None:
    """Six decimal places for a typical per-request cost."""
    result = format_cost_header_value(0.000125)
    assert result == "0.000125"


@pytest.mark.requirement("FR-COST-033")
def test_format_cost_header_value_zero() -> None:
    """Zero cost formats as '0.000000'."""
    result = format_cost_header_value(0.0)
    assert result == "0.000000"


@pytest.mark.requirement("FR-COST-033")
def test_format_cost_header_value_large() -> None:
    """Large cost (many tokens) is represented correctly."""
    # e.g. 1M prompt + 1M completion on gpt-4o = $2.50 + $10.00 = $12.50
    result = format_cost_header_value(12.50)
    assert result == "12.500000"
