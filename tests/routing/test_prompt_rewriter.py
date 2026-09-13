"""Tests for GW-69: Auto prompt rewriting per model/provider.

All tests tagged with @pytest.mark.requirement("FR-PROMPT-069").

# @trace FR-PROMPT-069
"""

from __future__ import annotations

import pytest

from thegent.utils.routing_impl.prompt_rewriter import (
    RewriteConfig,
    RewriteResult,
    RewriteRule,
    rewrite_prompt,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _user(content: str) -> dict:
    return {"role": "user", "content": content}


def _assistant(content: str) -> dict:
    return {"role": "assistant", "content": content}


def _system(content: str) -> dict:
    return {"role": "system", "content": content}


def _rule(
    name: str = "test_rule",
    providers: list[str] | None = None,
    models: list[str] | None = None,
    transform: str = "remove_empty_turns",
    priority: int = 0,
) -> RewriteRule:
    return RewriteRule(
        name=name,
        providers=providers if providers is not None else [],
        models=models if models is not None else [],
        transform=transform,
        priority=priority,
    )


# ---------------------------------------------------------------------------
# Test 1: disabled config returns messages unchanged
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-PROMPT-069")
def test_rewrite_disabled_returns_original() -> None:
    """When config.enabled=False, messages are returned unchanged and no rules applied."""
    messages = [_user("hello world")]
    cfg = RewriteConfig(enabled=False)
    result = rewrite_prompt(messages, config=cfg)
    assert isinstance(result, RewriteResult)
    assert result.messages == messages
    assert result.applied_rules == []
    # Token estimates are equal when nothing changed
    assert result.original_token_estimate == result.rewritten_token_estimate


# ---------------------------------------------------------------------------
# Test 2: empty rules list returns original unchanged
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-PROMPT-069")
def test_no_rules_returns_original() -> None:
    """When config.rules=[], messages are returned unchanged and applied_rules is empty."""
    messages = [_user("hello"), _assistant("world")]
    cfg = RewriteConfig(rules=[])
    result = rewrite_prompt(messages, config=cfg)
    assert result.messages == messages
    assert result.applied_rules == []


# ---------------------------------------------------------------------------
# Test 3: add_cot_suffix appended to last user message
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-PROMPT-069")
def test_add_cot_suffix_appended_to_last_user_message() -> None:
    """The add_cot_suffix transform appends 'Think step by step.' to the last user message."""
    messages = [_system("You are helpful."), _user("What is 2+2?")]
    cfg = RewriteConfig(rules=[_rule(transform="add_cot_suffix")])
    result = rewrite_prompt(messages, config=cfg)
    last = result.messages[-1]
    assert last["role"] == "user"
    assert last["content"].endswith(" Think step by step.")
    assert "What is 2+2?" in last["content"]


# ---------------------------------------------------------------------------
# Test 4: add_cot_suffix not applied when last message is not user
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-PROMPT-069")
def test_add_cot_suffix_not_applied_when_last_not_user() -> None:
    """If the last message role is 'assistant', add_cot_suffix is a no-op."""
    messages = [_user("Question?"), _assistant("Answer.")]
    cfg = RewriteConfig(rules=[_rule(transform="add_cot_suffix")])
    result = rewrite_prompt(messages, config=cfg)
    last = result.messages[-1]
    assert last["role"] == "assistant"
    assert last["content"] == "Answer."


# ---------------------------------------------------------------------------
# Test 5: remove_empty_turns filters empty content messages
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-PROMPT-069")
def test_remove_empty_turns_filters_empty() -> None:
    """Messages with empty string content are removed by remove_empty_turns."""
    messages = [_user("hello"), {"role": "assistant", "content": ""}, _user("bye")]
    cfg = RewriteConfig(rules=[_rule(transform="remove_empty_turns")])
    result = rewrite_prompt(messages, config=cfg)
    contents = [m["content"] for m in result.messages]
    assert "" not in contents
    assert len(result.messages) == 2


# ---------------------------------------------------------------------------
# Test 6: remove_empty_turns keeps non-empty messages
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-PROMPT-069")
def test_remove_empty_turns_keeps_nonempty() -> None:
    """Non-empty messages are preserved by remove_empty_turns."""
    messages = [_user("hello"), _assistant("world"), _user("bye")]
    cfg = RewriteConfig(rules=[_rule(transform="remove_empty_turns")])
    result = rewrite_prompt(messages, config=cfg)
    assert len(result.messages) == 3
    assert result.messages[0]["content"] == "hello"
    assert result.messages[1]["content"] == "world"
    assert result.messages[2]["content"] == "bye"


# ---------------------------------------------------------------------------
# Test 7: rule matches by provider
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-PROMPT-069")
def test_rule_matches_provider() -> None:
    """A rule with providers=['anthropic'] matches anthropic but not openai."""
    anthropic_rule = _rule(name="anthr_rule", providers=["anthropic"], transform="remove_empty_turns")
    cfg = RewriteConfig(rules=[anthropic_rule])

    # Empty message + empty turn so we can see if the rule was applied
    messages = [_user("hi"), {"role": "assistant", "content": ""}]

    result_anthropic = rewrite_prompt(messages, provider="anthropic", config=cfg)
    assert "anthr_rule" in result_anthropic.applied_rules

    result_openai = rewrite_prompt(messages, provider="openai", config=cfg)
    assert "anthr_rule" not in result_openai.applied_rules


# ---------------------------------------------------------------------------
# Test 8: rule matches by model prefix
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-PROMPT-069")
def test_rule_matches_model_prefix() -> None:
    """A rule with models=['claude-opus'] matches 'claude-opus-4-6' (prefix match)."""
    rule = _rule(name="opus_rule", models=["claude-opus"], transform="remove_empty_turns")
    cfg = RewriteConfig(rules=[rule])

    messages = [_user("hi"), {"role": "assistant", "content": ""}]

    result_match = rewrite_prompt(messages, model="claude-opus-4-6", config=cfg)
    assert "opus_rule" in result_match.applied_rules

    result_no_match = rewrite_prompt(messages, model="gpt-4o", config=cfg)
    assert "opus_rule" not in result_no_match.applied_rules


# ---------------------------------------------------------------------------
# Test 9: empty providers list matches all providers
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-PROMPT-069")
def test_rule_empty_providers_matches_all() -> None:
    """A rule with providers=[] matches any provider."""
    rule = _rule(name="universal", providers=[], transform="remove_empty_turns")
    cfg = RewriteConfig(rules=[rule])
    messages = [_user("hi"), {"role": "assistant", "content": ""}]

    for prov in ["openai", "anthropic", "google", "mistral", ""]:
        result = rewrite_prompt(messages, provider=prov, config=cfg)
        assert "universal" in result.applied_rules, f"Expected match for provider={prov!r}"


# ---------------------------------------------------------------------------
# Test 10: empty models list matches all models
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-PROMPT-069")
def test_rule_empty_models_matches_all() -> None:
    """A rule with models=[] matches any model."""
    rule = _rule(name="any_model", models=[], transform="remove_empty_turns")
    cfg = RewriteConfig(rules=[rule])
    messages = [_user("hi"), {"role": "assistant", "content": ""}]

    for mdl in ["gpt-4o", "claude-opus-4-6", "gemini-pro", ""]:
        result = rewrite_prompt(messages, model=mdl, config=cfg)
        assert "any_model" in result.applied_rules, f"Expected match for model={mdl!r}"


# ---------------------------------------------------------------------------
# Test 11: applied_rules contains matched rule names
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-PROMPT-069")
def test_rewrite_result_applied_rules() -> None:
    """applied_rules in the result contains the names of all matched rules."""
    rule_a = _rule(name="rule_a", transform="remove_empty_turns", priority=10)
    rule_b = _rule(name="rule_b", transform="remove_empty_turns", priority=5)
    # rule_c should not match (wrong provider)
    rule_c = _rule(name="rule_c", providers=["anthropic"], transform="remove_empty_turns")
    cfg = RewriteConfig(rules=[rule_a, rule_b, rule_c])
    messages = [_user("hello")]
    result = rewrite_prompt(messages, provider="openai", config=cfg)
    assert "rule_a" in result.applied_rules
    assert "rule_b" in result.applied_rules
    assert "rule_c" not in result.applied_rules


# ---------------------------------------------------------------------------
# Test 12: token estimates are character counts of content
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-PROMPT-069")
def test_rewrite_result_token_estimates() -> None:
    """original_token_estimate and rewritten_token_estimate reflect character counts."""
    content = "A" * 100
    messages = [_user(content)]
    cfg = RewriteConfig(rules=[])  # no transforms
    result = rewrite_prompt(messages, config=cfg)
    assert result.original_token_estimate == 100
    assert result.rewritten_token_estimate == 100


# ---------------------------------------------------------------------------
# Test 13: truncate_long_system truncates long system prompt
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-PROMPT-069")
def test_truncate_long_system() -> None:
    """A system prompt exceeding max_system_length is truncated with '... [truncated]'."""
    long_content = "X" * 5000
    messages = [_system(long_content), _user("question")]
    cfg = RewriteConfig(rules=[], max_system_length=100)
    result = rewrite_prompt(messages, config=cfg)
    system_content = result.messages[0]["content"]
    assert len(system_content) < 5000
    assert system_content.endswith("... [truncated]")
    assert system_content.startswith("X" * 100)


# ---------------------------------------------------------------------------
# Test 14: truncate_short_system leaves short system prompt unchanged
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-PROMPT-069")
def test_truncate_short_system_unchanged() -> None:
    """A system prompt under max_system_length is not modified."""
    short_content = "Short system prompt."
    messages = [_system(short_content), _user("question")]
    cfg = RewriteConfig(rules=[], max_system_length=4096)
    result = rewrite_prompt(messages, config=cfg)
    assert result.messages[0]["content"] == short_content


# ---------------------------------------------------------------------------
# Test 15: priority ordering — higher priority applied before lower
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-PROMPT-069")
def test_priority_ordering() -> None:
    """Higher priority rules are applied before lower priority rules.

    We verify this by checking that applied_rules is ordered high→low priority.
    """
    rule_low = _rule(name="low_prio", transform="remove_empty_turns", priority=1)
    rule_high = _rule(name="high_prio", transform="remove_empty_turns", priority=20)
    rule_mid = _rule(name="mid_prio", transform="remove_empty_turns", priority=10)
    cfg = RewriteConfig(rules=[rule_low, rule_high, rule_mid])
    messages = [_user("hello")]
    result = rewrite_prompt(messages, config=cfg)
    assert result.applied_rules == ["high_prio", "mid_prio", "low_prio"]


# ---------------------------------------------------------------------------
# Test 16: default rules add CoT for reasoning models
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-PROMPT-069")
def test_default_rules_cot_for_matching_model() -> None:
    """With default rules, a matching model (e.g. 'claude-opus-4-6') gets CoT appended."""
    messages = [_user("Explain quantum entanglement.")]
    # No config = use DEFAULT_RULES
    result = rewrite_prompt(messages, model="claude-opus-4-6")
    last = result.messages[-1]
    assert last["role"] == "user"
    assert "Think step by step." in last["content"]
    assert "add_cot_reasoning" in result.applied_rules


# ---------------------------------------------------------------------------
# Test 17: original messages list is not mutated
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-PROMPT-069")
def test_messages_not_mutated() -> None:
    """rewrite_prompt must not modify the original messages list or its dicts."""
    original_content = "Original user message."
    messages = [_user(original_content)]
    original_id = id(messages)
    original_dict_id = id(messages[0])

    cfg = RewriteConfig(rules=[_rule(transform="add_cot_suffix")])
    result = rewrite_prompt(messages, config=cfg)

    # Original list not replaced
    assert id(messages) == original_id
    # Original dict not mutated
    assert id(messages[0]) == original_dict_id
    assert messages[0]["content"] == original_content
    # Result is different from original
    assert result.messages is not messages
    assert result.messages[0] is not messages[0]
