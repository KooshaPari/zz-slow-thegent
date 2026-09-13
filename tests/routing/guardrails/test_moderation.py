from __future__ import annotations

"""Tests for GW-54: Content moderation guardrail.

# @trace FR-GUARD-054
"""

import pytest

from thegent.utils.routing_impl.guardrails.moderation import (
    DEFAULT_CATEGORIES,
    ModerationConfig,
    check_moderation,
    should_block,
)

pytestmark = pytest.mark.requirement("FR-GUARD-054")


def test_check_moderation_clean_text():
    result = check_moderation("The weather today is lovely and sunny.")
    assert result.flagged is False
    assert result.categories == []
    assert result.severity == "none"
    assert result.score == 0.0


def test_check_moderation_violence_keyword():
    result = check_moderation("I want to kill the process running on port 8080.")
    assert result.flagged is True
    assert "violence" in result.categories
    assert result.severity == "high"


def test_check_moderation_explicit_keyword():
    result = check_moderation("This is explicit adult content marked nsfw.")
    assert result.flagged is True
    assert "explicit" in result.categories
    assert result.severity == "medium"


def test_check_moderation_multiple_categories():
    # Triggers violence (high) AND explicit (medium)
    text = "explicit murder scene was shown in this pornographic film."
    result = check_moderation(text)
    assert result.flagged is True
    assert len(result.categories) >= 2
    assert result.severity == "high"
    assert result.score > 0.0
    assert result.score <= 1.0


def test_should_block_high_severity():
    result = check_moderation("They plan to bomb the building and massacre everyone.")
    assert result.flagged is True
    assert result.severity == "high"
    assert should_block(result) is True


def test_should_block_medium_not_blocked_by_default():
    # Default block_on_severity is "high"; medium should NOT be blocked by default
    result = check_moderation("This video contains explicit content.")
    assert result.flagged is True
    assert result.severity == "medium"
    assert should_block(result) is False


def test_custom_config_lower_threshold():
    config = ModerationConfig(block_on_severity="medium")
    result = check_moderation("This video contains explicit content.", config=config)
    assert result.flagged is True
    assert should_block(result, config=config) is True


def test_moderation_score_fraction():
    # Score should be a fraction: matched / total categories
    total = len(DEFAULT_CATEGORIES)
    # Trigger exactly one category
    result = check_moderation("I want to murder the dragon in this video game.")
    assert result.flagged is True
    assert len(result.categories) >= 1
    expected_score = len(result.categories) / total
    assert abs(result.score - expected_score) < 1e-9


def test_empty_text_not_flagged():
    result = check_moderation("")
    assert result.flagged is False
    assert result.severity == "none"


def test_custom_blocklist():
    config = ModerationConfig(custom_blocklist=["forbidden_phrase", "another_bad_word"])
    result = check_moderation("This text contains forbidden_phrase somewhere.", config=config)
    assert result.flagged is True
    assert "custom_blocklist" in result.categories
    assert should_block(result, config=config) is True
