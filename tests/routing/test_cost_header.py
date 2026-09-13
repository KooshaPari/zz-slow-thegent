"""Tests for GW-32: tg-response-cost header builder.

# @trace FR-COST-032
"""

from __future__ import annotations

import pytest

from thegent.cliproxy_adapter import build_cost_response_header

# ---------------------------------------------------------------------------
# build_cost_response_header — with usage
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-COST-032")
def test_build_cost_response_header_with_usage() -> None:
    """Response body with known model + usage produces tg-response-cost header."""
    response_body = {
        "model": "gpt-4o",
        "usage": {
            "prompt_tokens": 1000,
            "completion_tokens": 500,
        },
    }
    result = build_cost_response_header(response_body)
    assert "tg-response-cost" in result
    cost_str = result["tg-response-cost"]
    # gpt-4o: (1000/1M)*2.50 + (500/1M)*10.00 = 0.0025 + 0.005 = 0.0075
    assert cost_str == "0.007500"


# ---------------------------------------------------------------------------
# build_cost_response_header — empty response
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-COST-032")
def test_build_cost_response_header_empty_response() -> None:
    """Empty dict response body returns empty dict (no header)."""
    result = build_cost_response_header({})
    assert result == {}


# ---------------------------------------------------------------------------
# build_cost_response_header — unknown model
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-COST-032")
def test_build_cost_response_header_unknown_model() -> None:
    """Unknown model causes cost=0.0, so no header is emitted."""
    response_body = {
        "model": "totally-unknown-model-xyz-9999",
        "usage": {
            "prompt_tokens": 1000,
            "completion_tokens": 500,
        },
    }
    result = build_cost_response_header(response_body)
    assert result == {}


# ---------------------------------------------------------------------------
# build_cost_response_header — no usage key
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-COST-032")
def test_build_cost_response_header_no_usage_key() -> None:
    """Response body missing the 'usage' key returns empty dict (no header)."""
    response_body = {
        "model": "gpt-4o",
        # no 'usage' key
    }
    result = build_cost_response_header(response_body)
    assert result == {}
