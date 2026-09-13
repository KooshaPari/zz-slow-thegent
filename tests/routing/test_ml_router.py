"""Tests for GW-68: ML meta-model routing.

# @trace FR-AROUTE-068
"""

from __future__ import annotations

import pytest

from thegent.utils.routing_impl.ml_router import (
    TaskClassification,
    classify_task,
    ml_route,
    select_model,
)


@pytest.mark.requirement("FR-AROUTE-068")
class TestClassifyTask:
    def test_classify_coding_prompt(self) -> None:
        """'implement a function' classifies as coding."""
        result = classify_task("implement a function to sort a list")
        assert result.task_type == "coding"

    def test_classify_reasoning_prompt(self) -> None:
        """'reason through this logic' classifies as reasoning."""
        result = classify_task("reason through this logic step by step")
        assert result.task_type == "reasoning"

    def test_classify_summarization_prompt(self) -> None:
        """'summarize this article' classifies as summarization."""
        result = classify_task("summarize this article into key points")
        assert result.task_type == "summarization"

    def test_classify_creative_prompt(self) -> None:
        """'write a short story' classifies as creative."""
        result = classify_task("write a short story about a robot")
        assert result.task_type == "creative"

    def test_classify_retrieval_prompt(self) -> None:
        """'what is the capital of France' classifies as retrieval."""
        result = classify_task("what is the capital of France")
        assert result.task_type == "retrieval"

    def test_classify_general_fallback(self) -> None:
        """Gibberish with no keyword hits falls back to 'general' with confidence=0.5."""
        result = classify_task("zxqwerty asdf foobar baz qux quux")
        assert result.task_type == "general"
        assert result.confidence == 0.5

    def test_classification_confidence(self) -> None:
        """A coding prompt produces confidence > 0."""
        result = classify_task("implement a sorting algorithm and refactor the class")
        assert result.task_type == "coding"
        assert result.confidence > 0


@pytest.mark.requirement("FR-AROUTE-068")
class TestSelectModel:
    def test_select_model_for_coding(self) -> None:
        """Coding task selects claude-opus-4-6 as priority-1 model."""
        classification = TaskClassification(task_type="coding", confidence=0.9, signals=["implement"])
        result = select_model(classification)
        assert result is not None
        assert result.model == "claude-opus-4-6"
        assert result.priority == 1

    def test_select_model_available_filter(self) -> None:
        """available_models filter restricts returned model."""
        classification = TaskClassification(task_type="coding", confidence=0.8, signals=["code"])
        # Exclude claude-opus-4-6 (priority 1), gpt-4o should be next for coding
        result = select_model(classification, available_models=["gpt-4o", "gpt-4o-mini"])
        assert result is not None
        assert result.model == "gpt-4o"

    def test_select_model_no_match_returns_none(self) -> None:
        """Empty preferences list -> None."""
        classification = TaskClassification(task_type="coding", confidence=0.8, signals=[])
        result = select_model(classification, preferences=[])
        assert result is None

    def test_select_model_no_available_match_returns_none(self) -> None:
        """available_models with no overlap -> None."""
        classification = TaskClassification(task_type="coding", confidence=0.8, signals=[])
        result = select_model(classification, available_models=["some-unknown-model"])
        assert result is None

    def test_select_model_general_task(self) -> None:
        """General task selects a model that covers 'general' task type."""
        classification = TaskClassification(task_type="general", confidence=0.5, signals=[])
        result = select_model(classification)
        assert result is not None
        assert "general" in result.task_types


@pytest.mark.requirement("FR-AROUTE-068")
class TestMlRoute:
    def test_ml_route_convenience(self) -> None:
        """ml_route: one-shot classify+select returns a model preference."""
        result = ml_route("implement a binary search algorithm")
        assert result is not None
        assert result.model  # non-empty model name

    def test_ml_route_with_available_models(self) -> None:
        """ml_route respects available_models filter."""
        result = ml_route(
            "summarize this document into a brief overview",
            available_models=["gpt-4o-mini"],
        )
        assert result is not None
        assert result.model == "gpt-4o-mini"

    def test_ml_route_empty_available_returns_none(self) -> None:
        """ml_route with no matching available models returns None."""
        result = ml_route("write a poem", available_models=["nonexistent-model"])
        assert result is None
