"""Tests for WL-103 ContextCompactor.

Covers:
- Token counter (char-based and tiktoken modes)
- Compaction trigger at configurable threshold (default 80%)
- should_compact() logic
- compact() turn-reduction logic
- context_usage_ratio surfaced in RunResult
- Edge cases and error paths

# @trace WL-103
"""

from __future__ import annotations

import pytest

from thegent.agents.base import RunResult
from thegent.agents.context_compactor import (
    ContextCompactionResult,
    ContextCompactor,
    _encoding_for_model,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _turn(role: str, content: str) -> dict[str, str]:
    return {"role": role, "content": content}


def _many_turns(n: int, chars_each: int = 10) -> list[dict[str, str]]:
    turns = []
    for i in range(n):
        role = "user" if i % 2 == 0 else "assistant"
        turns.append(_turn(role, "x" * chars_each))
    return turns


# ---------------------------------------------------------------------------
# 1. Constructor validation
# ---------------------------------------------------------------------------


@pytest.mark.requirement("WL-103")
def test_constructor_rejects_invalid_parameters() -> None:  # @trace WL-103
    with pytest.raises(ValueError, match="threshold_ratio"):
        ContextCompactor(threshold_ratio=0)
    with pytest.raises(ValueError, match="chars_per_token"):
        ContextCompactor(chars_per_token=0)


@pytest.mark.requirement("WL-103")
def test_constructor_rejects_negative_threshold_ratio() -> None:  # @trace WL-103
    with pytest.raises(ValueError, match="threshold_ratio"):
        ContextCompactor(threshold_ratio=-0.1)


@pytest.mark.requirement("WL-103")
def test_constructor_rejects_negative_chars_per_token() -> None:  # @trace WL-103
    with pytest.raises(ValueError, match="chars_per_token"):
        ContextCompactor(chars_per_token=-1.0)


@pytest.mark.requirement("WL-103")
def test_constructor_accepts_valid_parameters() -> None:  # @trace WL-103
    compactor = ContextCompactor(threshold_ratio=0.9, chars_per_token=3.5)
    assert compactor is not None


# ---------------------------------------------------------------------------
# 2. Token counter — char-based mode
# ---------------------------------------------------------------------------


@pytest.mark.requirement("WL-103")
def test_count_tokens_empty_string_returns_zero() -> None:  # @trace WL-103
    compactor = ContextCompactor()
    assert compactor.count_tokens("") == 0


@pytest.mark.requirement("WL-103")
def test_count_tokens_char_based_uses_chars_per_token() -> None:  # @trace WL-103
    compactor = ContextCompactor(chars_per_token=4.0)
    # 8 chars / 4.0 = 2 tokens
    assert compactor.count_tokens("abcdefgh") == 2


@pytest.mark.requirement("WL-103")
def test_count_tokens_char_based_ceiling_rounding() -> None:  # @trace WL-103
    compactor = ContextCompactor(chars_per_token=4.0)
    # 5 chars / 4.0 = 1.25 → ceil = 2
    assert compactor.count_tokens("abcde") == 2


@pytest.mark.requirement("WL-103")
def test_estimate_tokens_alias_matches_count_tokens() -> None:  # @trace WL-103
    compactor = ContextCompactor(chars_per_token=4.0)
    text = "hello world"
    assert compactor.estimate_tokens(text) == compactor.count_tokens(text)


# ---------------------------------------------------------------------------
# 3. Token counter — tiktoken mode
# ---------------------------------------------------------------------------


@pytest.mark.requirement("WL-103")
def test_count_tokens_tiktoken_mode_returns_positive_for_nonempty() -> None:  # @trace WL-103
    compactor = ContextCompactor(model="gpt-4")
    assert compactor.count_tokens("hello world") > 0


@pytest.mark.requirement("WL-103")
def test_count_tokens_tiktoken_mode_empty_string_returns_zero() -> None:  # @trace WL-103
    compactor = ContextCompactor(model="gpt-4")
    assert compactor.count_tokens("") == 0


@pytest.mark.requirement("WL-103")
def test_count_tokens_tiktoken_longer_text_has_more_tokens() -> None:  # @trace WL-103
    compactor = ContextCompactor(model="gpt-4")
    short = compactor.count_tokens("hi")
    long = compactor.count_tokens("hello world this is a much longer text string")
    assert long > short


@pytest.mark.requirement("WL-103")
def test_encoding_for_model_unknown_model_uses_fallback() -> None:  # @trace WL-103
    # Should not raise — unknown model uses cl100k_base fallback
    enc = _encoding_for_model("unknown-model-xyz")
    assert enc is not None
    tokens = enc.encode("test")
    assert len(tokens) > 0


@pytest.mark.requirement("WL-103")
def test_encoding_for_model_claude_prefix_resolves() -> None:  # @trace WL-103
    enc = _encoding_for_model("claude-haiku-4-5")
    assert enc is not None


# ---------------------------------------------------------------------------
# 4. should_compact()
# ---------------------------------------------------------------------------


@pytest.mark.requirement("WL-103")
def test_should_compact_returns_false_when_below_threshold() -> None:  # @trace WL-103
    compactor = ContextCompactor(threshold_ratio=0.8)
    assert compactor.should_compact(79, 100) is False


@pytest.mark.requirement("WL-103")
def test_should_compact_returns_false_when_exactly_at_threshold() -> None:  # @trace WL-103
    compactor = ContextCompactor(threshold_ratio=0.8)
    # 80 / 100 == 0.80, which is NOT > 0.80
    assert compactor.should_compact(80, 100) is False


@pytest.mark.requirement("WL-103")
def test_should_compact_returns_true_when_above_threshold() -> None:  # @trace WL-103
    compactor = ContextCompactor(threshold_ratio=0.8)
    assert compactor.should_compact(81, 100) is True


@pytest.mark.requirement("WL-103")
def test_should_compact_raises_on_zero_context_max() -> None:  # @trace WL-103
    compactor = ContextCompactor()
    with pytest.raises(ValueError, match="must be > 0"):
        compactor.should_compact(10, 0)


# ---------------------------------------------------------------------------
# 5. usage_ratio()
# ---------------------------------------------------------------------------


@pytest.mark.requirement("WL-103")
def test_usage_ratio_is_deterministic() -> None:  # @trace WL-103
    compactor = ContextCompactor(chars_per_token=4.0)
    ratio = compactor.usage_ratio([_turn("user", "abcd"), _turn("assistant", "efgh")], 100)
    assert ratio > 0.0
    assert ratio < 1.0


@pytest.mark.requirement("WL-103")
def test_usage_ratio_requires_positive_context_window() -> None:  # @trace WL-103
    compactor = ContextCompactor()
    with pytest.raises(ValueError, match="must be > 0"):
        compactor.usage_ratio([], 0)


@pytest.mark.requirement("WL-103")
def test_usage_ratio_empty_turns_is_zero() -> None:  # @trace WL-103
    compactor = ContextCompactor()
    assert compactor.usage_ratio([], 1000) == 0.0


@pytest.mark.requirement("WL-103")
def test_usage_ratio_increases_with_more_turns() -> None:  # @trace WL-103
    compactor = ContextCompactor(chars_per_token=1.0)
    few = compactor.usage_ratio([_turn("user", "a")], 100)
    many = compactor.usage_ratio([_turn("user", "a" * 50), _turn("assistant", "b" * 50)], 100)
    assert many > few


# ---------------------------------------------------------------------------
# 6. compact() — no-op cases
# ---------------------------------------------------------------------------


@pytest.mark.requirement("WL-103")
def test_compact_returns_unchanged_when_under_threshold() -> None:  # @trace WL-103
    compactor = ContextCompactor(threshold_ratio=0.9)
    turns = _many_turns(4, chars_each=1)
    result = compactor.compact(turns, 1000)
    assert result.compacted is False
    assert result.turns is turns


@pytest.mark.requirement("WL-103")
def test_compact_requires_minimum_turn_count_of_four() -> None:  # @trace WL-103
    compactor = ContextCompactor(threshold_ratio=0.1)
    turns = [_turn("user", "a"), _turn("assistant", "b"), _turn("user", "c")]
    result = compactor.compact(turns, 1)
    assert result.compacted is False


@pytest.mark.requirement("WL-103")
def test_compact_returns_correct_ratio_when_not_compacted() -> None:  # @trace WL-103
    compactor = ContextCompactor(threshold_ratio=0.9, chars_per_token=4.0)
    turns = [_turn("user", "abcd")]  # 1 token + 1 token = 2 tokens
    result = compactor.compact(turns, 10_000)
    assert result.usage_ratio == compactor.usage_ratio(turns, 10_000)


# ---------------------------------------------------------------------------
# 7. compact() — active compaction
# ---------------------------------------------------------------------------


@pytest.mark.requirement("WL-103")
def test_compact_summarizes_older_turns_and_keeps_recent_two() -> None:  # @trace WL-103
    compactor = ContextCompactor(threshold_ratio=0.2, chars_per_token=1.0)
    turns = [
        _turn("system", "rule"),
        _turn("user", "first question"),
        _turn("assistant", "first answer"),
        _turn("user", "second question"),
        _turn("assistant", "second answer"),
    ]
    result = compactor.compact(turns, 20)
    assert result.compacted is True
    assert len(result.turns) == 3
    assert result.turns[0]["role"] == "system"
    assert "Summary of prior context" in result.turns[0]["content"]
    assert result.turns[-2:] == turns[-2:]


@pytest.mark.requirement("WL-103")
def test_compact_reduces_usage_ratio() -> None:  # @trace WL-103
    compactor = ContextCompactor(threshold_ratio=0.2, chars_per_token=1.0)
    turns = [_turn("user", "x" * 40), _turn("assistant", "y" * 40), _turn("user", "z" * 40), _turn("assistant", "w")]
    before = compactor.usage_ratio(turns, 50)
    after = compactor.compact(turns, 50).usage_ratio
    assert before > after


@pytest.mark.requirement("WL-103")
def test_compact_result_usage_ratio_is_post_compaction_ratio() -> None:  # @trace WL-103
    compactor = ContextCompactor(threshold_ratio=0.2, chars_per_token=1.0)
    turns = _many_turns(6, chars_each=20)
    result = compactor.compact(turns, 10)
    assert result.compacted is True
    # Post-compaction ratio should reflect the new, shorter turn list
    expected_ratio = compactor.usage_ratio(result.turns, 10)
    assert abs(result.usage_ratio - expected_ratio) < 1e-9


@pytest.mark.requirement("WL-103")
def test_compact_summary_turn_mentions_each_compacted_turn_role() -> None:  # @trace WL-103
    compactor = ContextCompactor(threshold_ratio=0.1, chars_per_token=1.0)
    turns = [
        _turn("system", "sys content"),
        _turn("user", "user content"),
        _turn("assistant", "assistant content"),
        _turn("user", "second user turn"),
    ]
    result = compactor.compact(turns, 5)
    assert result.compacted is True
    summary_content = result.turns[0]["content"]
    # Compacted turns are all except last two: system + user
    assert "system" in summary_content
    assert "user" in summary_content


# ---------------------------------------------------------------------------
# 8. estimate_turn_tokens()
# ---------------------------------------------------------------------------


@pytest.mark.requirement("WL-103")
def test_estimate_turn_tokens_counts_role_and_content() -> None:  # @trace WL-103
    compactor = ContextCompactor(chars_per_token=1.0)
    turn = _turn("user", "hello")
    # "user" (4 chars) + "hello" (5 chars) = 9 tokens at chars_per_token=1
    assert compactor.estimate_turn_tokens(turn) == 9


@pytest.mark.requirement("WL-103")
def test_estimate_turn_tokens_missing_keys_returns_zero() -> None:  # @trace WL-103
    compactor = ContextCompactor()
    assert compactor.estimate_turn_tokens({}) == 0


# ---------------------------------------------------------------------------
# 9. RunResult.context_usage_ratio field
# ---------------------------------------------------------------------------


@pytest.mark.requirement("WL-103")
def test_run_result_has_context_usage_ratio_field() -> None:  # @trace WL-103
    result = RunResult(exit_code=0, stdout="", stderr="")
    assert hasattr(result, "context_usage_ratio")
    assert result.context_usage_ratio is None


@pytest.mark.requirement("WL-103")
def test_run_result_context_usage_ratio_can_be_set() -> None:  # @trace WL-103
    result = RunResult(exit_code=0, stdout="", stderr="", context_usage_ratio=0.75)
    assert result.context_usage_ratio == 0.75


@pytest.mark.requirement("WL-103")
def test_run_result_context_usage_ratio_accepts_float_values() -> None:  # @trace WL-103
    for ratio in [0.0, 0.5, 0.8, 1.0, 1.5]:
        result = RunResult(exit_code=0, stdout="", stderr="", context_usage_ratio=ratio)
        assert result.context_usage_ratio == ratio


# ---------------------------------------------------------------------------
# 10. ContextCompactionResult dataclass
# ---------------------------------------------------------------------------


@pytest.mark.requirement("WL-103")
def test_context_compaction_result_is_frozen() -> None:  # @trace WL-103
    result = ContextCompactionResult(turns=[], usage_ratio=0.5, compacted=False)
    with pytest.raises(Exception):
        result.compacted = True  # type: ignore[misc]


@pytest.mark.requirement("WL-103")
def test_context_compaction_result_fields_accessible() -> None:  # @trace WL-103
    turns = [_turn("user", "hi")]
    result = ContextCompactionResult(turns=turns, usage_ratio=0.42, compacted=False)
    assert result.turns is turns
    assert result.usage_ratio == 0.42
    assert result.compacted is False


# ---------------------------------------------------------------------------
# 11. count_turns_tokens()
# ---------------------------------------------------------------------------


@pytest.mark.requirement("WL-103")
def test_count_turns_tokens_empty_list_is_zero() -> None:  # @trace WL-103
    compactor = ContextCompactor()
    assert compactor.count_turns_tokens([]) == 0


@pytest.mark.requirement("WL-103")
def test_count_turns_tokens_is_sum_of_individual_turns() -> None:  # @trace WL-103
    compactor = ContextCompactor(chars_per_token=1.0)
    turns = [_turn("user", "abc"), _turn("assistant", "de")]
    total = compactor.count_turns_tokens(turns)
    expected = sum(compactor.estimate_turn_tokens(t) for t in turns)
    assert total == expected


# ---------------------------------------------------------------------------
# 12. Tiktoken wired into compact() when model is specified
# ---------------------------------------------------------------------------


@pytest.mark.requirement("WL-103")
def test_compact_with_tiktoken_model_triggers_on_accurate_token_count() -> None:  # @trace WL-103
    # 6 turns of 50 chars ≈ 48 tiktoken tokens; use context_window_max=50 so ratio > 0.80 default
    compactor = ContextCompactor(threshold_ratio=0.8, model="gpt-4")
    turns = _many_turns(6, chars_each=50)
    result = compactor.compact(turns, 50)
    # 48 tokens / 50 max = 0.96 > 0.80 → should compact
    assert result.compacted is True


@pytest.mark.requirement("WL-103")
def test_compact_with_tiktoken_model_preserves_last_two_turns() -> None:  # @trace WL-103
    compactor = ContextCompactor(threshold_ratio=0.8, model="gpt-4")
    turns = _many_turns(6, chars_each=50)
    result = compactor.compact(turns, 50)
    assert result.compacted is True
    assert result.turns[-2:] == turns[-2:]
