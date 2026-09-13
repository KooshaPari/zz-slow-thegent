"""Tests for WL-103 context compaction layer (pydantic models).

# @trace FR-CTX-103
"""

from __future__ import annotations

import pytest

from thegent.agents.compaction import (
    CompactionConfig,
    CompactionResult,
    CompactionTrigger,
    ContextCompactor,
    ContextWindow,
)

# ---------------------------------------------------------------------------
# CompactionTrigger
# ---------------------------------------------------------------------------


class TestCompactionTrigger:
    def test_never_value(self) -> None:
        assert CompactionTrigger.NEVER == "never"

    def test_token_threshold_value(self) -> None:
        assert CompactionTrigger.TOKEN_THRESHOLD == "token_threshold"

    def test_turn_count_value(self) -> None:
        assert CompactionTrigger.TURN_COUNT == "turn_count"


# ---------------------------------------------------------------------------
# CompactionConfig
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-CTX-103")
class TestCompactionConfig:
    def test_default_trigger_is_never(self) -> None:
        cfg = CompactionConfig()
        assert cfg.trigger == CompactionTrigger.NEVER

    def test_custom_token_threshold(self) -> None:
        cfg = CompactionConfig(token_threshold=50_000)
        assert cfg.token_threshold == 50_000

    def test_frozen_config(self) -> None:
        cfg = CompactionConfig()
        with pytest.raises(Exception):
            cfg.trigger = CompactionTrigger.TOKEN_THRESHOLD  # type: ignore[misc]

    def test_default_values(self) -> None:
        cfg = CompactionConfig()
        assert cfg.token_threshold == 100_000
        assert cfg.turn_threshold == 50
        assert cfg.max_summary_tokens == 2_000


# ---------------------------------------------------------------------------
# ContextWindow
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-CTX-103")
class TestContextWindow:
    def test_default_empty(self) -> None:
        w = ContextWindow()
        assert w.messages == []
        assert w.token_count == 0
        assert w.turn_count == 0
        assert w.compacted_at_turn is None

    def test_mutable_messages(self) -> None:
        w = ContextWindow()
        w.messages.append({"role": "user", "content": "hello"})
        assert len(w.messages) == 1

    def test_turn_count_starts_zero(self) -> None:
        w = ContextWindow()
        assert w.turn_count == 0


# ---------------------------------------------------------------------------
# ContextCompactor
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-CTX-103")
class TestContextCompactor:
    def test_should_compact_never_returns_false(self) -> None:
        compactor = ContextCompactor(
            config=CompactionConfig(trigger=CompactionTrigger.NEVER)
        )
        window = ContextWindow(token_count=999_999, turn_count=999)
        assert compactor.should_compact(window) is False

    def test_should_compact_token_threshold_below(self) -> None:
        cfg = CompactionConfig(
            trigger=CompactionTrigger.TOKEN_THRESHOLD, token_threshold=100_000
        )
        compactor = ContextCompactor(config=cfg)
        window = ContextWindow(token_count=50_000)
        assert compactor.should_compact(window) is False

    def test_should_compact_token_threshold_above(self) -> None:
        cfg = CompactionConfig(
            trigger=CompactionTrigger.TOKEN_THRESHOLD, token_threshold=100_000
        )
        compactor = ContextCompactor(config=cfg)
        window = ContextWindow(token_count=150_000)
        assert compactor.should_compact(window) is True

    def test_should_compact_turn_threshold_below(self) -> None:
        cfg = CompactionConfig(trigger=CompactionTrigger.TURN_COUNT, turn_threshold=50)
        compactor = ContextCompactor(config=cfg)
        window = ContextWindow(turn_count=30)
        assert compactor.should_compact(window) is False

    def test_should_compact_turn_threshold_above(self) -> None:
        cfg = CompactionConfig(trigger=CompactionTrigger.TURN_COUNT, turn_threshold=50)
        compactor = ContextCompactor(config=cfg)
        window = ContextWindow(turn_count=60)
        assert compactor.should_compact(window) is True

    def test_compact_replaces_messages_with_summary(self) -> None:
        cfg = CompactionConfig(
            trigger=CompactionTrigger.TOKEN_THRESHOLD, token_threshold=100
        )
        compactor = ContextCompactor(config=cfg)
        window = ContextWindow(
            messages=[
                {"role": "user", "content": "hello"},
                {"role": "assistant", "content": "hi there"},
                {"role": "user", "content": "how are you"},
            ],
            token_count=200,
            turn_count=3,
        )
        compactor.compact(window, summary="Key points: greeting exchange.")
        assert len(window.messages) == 1
        assert window.messages[0]["role"] == "system"
        assert window.messages[0]["content"] == "Key points: greeting exchange."

    def test_compact_returns_result_with_counts(self) -> None:
        cfg = CompactionConfig(
            trigger=CompactionTrigger.TOKEN_THRESHOLD, token_threshold=100
        )
        compactor = ContextCompactor(config=cfg)
        window = ContextWindow(
            messages=[
                {"role": "user", "content": "a" * 100},
                {"role": "assistant", "content": "b" * 100},
            ],
            token_count=200,
            turn_count=2,
        )
        result = compactor.compact(window, summary="summary")
        assert result.tokens_before == 200
        assert result.tokens_after == window.token_count
        assert result.turns_compacted == 2

    def test_compact_sets_compacted_at_turn(self) -> None:
        cfg = CompactionConfig(
            trigger=CompactionTrigger.TOKEN_THRESHOLD, token_threshold=100
        )
        compactor = ContextCompactor(config=cfg)
        window = ContextWindow(
            messages=[{"role": "user", "content": "x"}],
            token_count=200,
            turn_count=5,
        )
        compactor.compact(window, summary="s")
        assert window.compacted_at_turn == 5

    def test_estimate_tokens_proportional_to_length(self) -> None:
        compactor = ContextCompactor(config=CompactionConfig())
        short_msg = [{"role": "user", "content": "hi"}]
        long_msg = [{"role": "user", "content": "x" * 400}]
        short_est = compactor.estimate_tokens(short_msg)
        long_est = compactor.estimate_tokens(long_msg)
        assert long_est > short_est

    def test_build_compaction_prompt_includes_prompt(self) -> None:
        cfg = CompactionConfig(summary_prompt="Please summarize.")
        compactor = ContextCompactor(config=cfg)
        window = ContextWindow(
            messages=[{"role": "user", "content": "hello"}],
            turn_count=3,
            token_count=100,
        )
        prompt = compactor.build_compaction_prompt(window)
        assert "Please summarize." in prompt
        assert "3" in prompt  # turn count reference
        assert "100" in prompt  # token count reference

    def test_compact_resets_token_count(self) -> None:
        cfg = CompactionConfig(
            trigger=CompactionTrigger.TOKEN_THRESHOLD, token_threshold=100
        )
        compactor = ContextCompactor(config=cfg)
        window = ContextWindow(
            messages=[
                {"role": "user", "content": "a" * 400},
                {"role": "assistant", "content": "b" * 400},
            ],
            token_count=200,
            turn_count=2,
        )
        compactor.compact(window, summary="short summary")
        assert window.token_count < 200

    def test_compact_result_is_frozen(self) -> None:
        result = CompactionResult(
            summary="s",
            tokens_before=100,
            tokens_after=10,
            turns_compacted=5,
        )
        with pytest.raises(Exception):
            result.summary = "changed"  # type: ignore[misc]
