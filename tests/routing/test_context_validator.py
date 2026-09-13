"""Tests for GW-62: Pre-call context window validation.

# @trace FR-AROUTE-062
"""

from __future__ import annotations

import pytest

from thegent.utils.routing_impl.context_validator import (
    CONTEXT_WINDOW_LIMITS,
    ContextWindowCheckResult,
    check_context_window,
    estimate_token_count,
    select_fallback_model,
)


@pytest.mark.requirement("FR-AROUTE-062")
class TestEstimateTokenCount:
    def test_estimate_token_count_basic(self) -> None:
        messages = [{"role": "user", "content": "Hello world"}]
        count = estimate_token_count(messages)
        assert isinstance(count, int)
        assert count > 0

    def test_estimate_token_count_empty(self) -> None:
        count = estimate_token_count([])
        assert count == 0

    def test_estimate_token_count_multiple_messages(self) -> None:
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is 2+2?"},
        ]
        single = estimate_token_count([messages[0]])
        combined = estimate_token_count(messages)
        assert combined > single

    def test_estimate_token_count_scales_with_length(self) -> None:
        short_msg = [{"role": "user", "content": "Hi"}]
        long_msg = [{"role": "user", "content": "Hi " * 1000}]
        assert estimate_token_count(long_msg) > estimate_token_count(short_msg)

    def test_estimate_token_count_formula(self) -> None:
        # Verify the formula: sum of len(str(msg)) // 4
        messages = [{"role": "user", "content": "test"}]
        expected = len(str(messages[0])) // 4
        assert estimate_token_count(messages) == expected


@pytest.mark.requirement("FR-AROUTE-062")
class TestCheckContextWindow:
    def test_check_context_window_fits(self) -> None:
        # Small messages should fit gpt-4o's 128k limit
        messages = [{"role": "user", "content": "Hello"}]
        result = check_context_window("gpt-4o", messages)
        assert isinstance(result, ContextWindowCheckResult)
        assert result.fits is True
        assert result.overflow == 0
        assert result.model_limit == 128_000

    def test_check_context_window_overflow(self) -> None:
        # Craft a message that exceeds gpt-4o-mini's 128k limit
        # 128k tokens * 4 chars/token = ~512k chars
        huge_content = "x" * (128_000 * 4 + 10_000)
        messages = [{"role": "user", "content": huge_content}]
        result = check_context_window("gpt-4o-mini", messages)
        assert result.fits is False
        assert result.overflow > 0
        assert result.estimated_tokens > result.model_limit

    def test_check_context_window_unknown_model_allows(self) -> None:
        messages = [{"role": "user", "content": "Hello"}]
        result = check_context_window("unknown-future-model", messages)
        assert result.fits is True
        assert result.model_limit is None
        assert result.overflow == 0

    def test_check_context_window_result_fields(self) -> None:
        messages = [{"role": "user", "content": "Hello"}]
        result = check_context_window("gpt-4o", messages)
        assert hasattr(result, "fits")
        assert hasattr(result, "estimated_tokens")
        assert hasattr(result, "model_limit")
        assert hasattr(result, "overflow")

    def test_check_context_window_claude_large_limit(self) -> None:
        # claude-opus-4-5 has 200k limit — small messages should fit
        messages = [{"role": "user", "content": "What is AI?"}]
        result = check_context_window("claude-opus-4-5", messages)
        assert result.fits is True
        assert result.model_limit == 200_000

    def test_check_context_window_gemini_huge_limit(self) -> None:
        messages = [{"role": "user", "content": "Hello"}]
        result = check_context_window("gemini-1.5-pro", messages)
        assert result.fits is True
        assert result.model_limit == 1_000_000


@pytest.mark.requirement("FR-AROUTE-062")
class TestSelectFallbackModel:
    def test_select_fallback_model_first_fits(self) -> None:
        messages = [{"role": "user", "content": "Hello"}]
        fallbacks = ["gpt-4o-mini", "gemini-1.5-flash"]
        result = select_fallback_model("gpt-4o", fallbacks, messages)
        assert result == "gpt-4o-mini"

    def test_select_fallback_empty_list(self) -> None:
        messages = [{"role": "user", "content": "Hello"}]
        result = select_fallback_model("gpt-4o", [], messages)
        assert result == "gpt-4o"

    def test_select_fallback_unknown_model_allowed(self) -> None:
        messages = [{"role": "user", "content": "Hello"}]
        fallbacks = ["unknown-model-a", "unknown-model-b"]
        # Unknown models pass through (no limit)
        result = select_fallback_model("gpt-4o", fallbacks, messages)
        assert result == "unknown-model-a"

    def test_select_fallback_last_when_none_fit(self) -> None:
        # Build messages that exceed all known limits
        huge_content = "x" * (1_000_000 * 4 + 100_000)
        messages = [{"role": "user", "content": huge_content}]
        fallbacks = ["gpt-4o-mini", "claude-haiku-4-5"]
        result = select_fallback_model("gpt-4o", fallbacks, messages)
        # None fit, so return last fallback
        assert result == "claude-haiku-4-5"

    def test_select_fallback_prefers_fitting_over_later(self) -> None:
        messages = [{"role": "user", "content": "Hello"}]
        fallbacks = ["gpt-4o-mini", "gemini-1.5-pro"]
        result = select_fallback_model("gpt-4o", fallbacks, messages)
        # First fallback fits, return it
        assert result == "gpt-4o-mini"


@pytest.mark.requirement("FR-AROUTE-062")
class TestContextWindowLimits:
    def test_known_models_in_limits(self) -> None:
        expected_models = [
            "gpt-4o",
            "gpt-4o-mini",
            "claude-opus-4-5",
            "claude-sonnet-4-5",
            "claude-haiku-4-5",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
        ]
        for model in expected_models:
            assert model in CONTEXT_WINDOW_LIMITS, f"Model {model!r} missing from CONTEXT_WINDOW_LIMITS"

    def test_limits_are_positive_ints(self) -> None:
        for model, limit in CONTEXT_WINDOW_LIMITS.items():
            assert isinstance(limit, int), f"{model}: limit must be int"
            assert limit > 0, f"{model}: limit must be positive"
