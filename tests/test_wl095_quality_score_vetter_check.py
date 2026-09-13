"""Unit tests for WL-095: QualityScoreVetterCheck — LLM-as-judge via configurable model.

All tests use mocked litellm.acompletion calls. No real LLM calls made.
Judge model called with structured rubric prompt; returns 1-5 Likert scores.
pass_threshold applies to mean(scores)/5.0 (normalised ratio).
min_criterion_score is an integer floor per criterion (1-5 scale).
judge_model="auto" resolves via CapabilityIndex.recommend("quality scoring").

Every test carries # @trace WL-095
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import orjson as json
import pytest

from thegent.govern.vetter.checks import QualityScoreVetterCheck
from thegent.govern.vetter.models import (
    VetterCheck,
    VetterCheckResult,
    VetterConfigError,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_litellm_response(scores: dict[str, int], pass_verdict: bool, critique: str = "") -> MagicMock:
    """Build a minimal litellm ModelResponse mock with the given judge payload."""
    payload = json.dumps({"scores": scores, "pass_verdict": pass_verdict, "critique": critique}).decode()
    msg = MagicMock()
    msg.content = payload
    choice = MagicMock()
    choice.message = msg
    response = MagicMock()
    response.choices = [choice]
    return response


def _run(coro: Any) -> Any:
    return asyncio.get_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# 1. Construction and defaults
# ---------------------------------------------------------------------------


def test_default_name():
    # @trace WL-095
    check = QualityScoreVetterCheck(judge_model="gpt-4o-mini", rubric=["correctness"])
    assert check.name == "quality_score"


def test_default_judge_model_is_auto():
    # @trace WL-095
    check = QualityScoreVetterCheck(rubric=["correctness"])
    assert check.judge_model == "auto"


def test_default_pass_threshold():
    # @trace WL-095
    check = QualityScoreVetterCheck(judge_model="gpt-4o-mini", rubric=["correctness"])
    assert check.pass_threshold == 0.75


def test_default_min_criterion_score():
    # @trace WL-095
    check = QualityScoreVetterCheck(judge_model="gpt-4o-mini", rubric=["correctness"])
    assert check.min_criterion_score == 3


def test_default_always_run_is_false():
    # @trace WL-095
    check = QualityScoreVetterCheck(judge_model="gpt-4o-mini", rubric=["correctness"])
    assert check.always_run is False


def test_implements_vetter_check_protocol():
    # @trace WL-095
    check = QualityScoreVetterCheck(judge_model="gpt-4o-mini", rubric=["correctness"])
    assert isinstance(check, VetterCheck)


# ---------------------------------------------------------------------------
# 2. Configuration validation
# ---------------------------------------------------------------------------


def test_pass_threshold_below_zero_raises():
    # @trace WL-095
    with pytest.raises(VetterConfigError, match="pass_threshold must be in range"):
        QualityScoreVetterCheck(judge_model="gpt-4o-mini", rubric=["correctness"], pass_threshold=-0.1)


def test_pass_threshold_above_one_raises():
    # @trace WL-095
    with pytest.raises(VetterConfigError, match="pass_threshold must be in range"):
        QualityScoreVetterCheck(judge_model="gpt-4o-mini", rubric=["correctness"], pass_threshold=1.1)


def test_min_criterion_score_zero_raises():
    # @trace WL-095
    with pytest.raises(VetterConfigError, match="min_criterion_score must be in range"):
        QualityScoreVetterCheck(judge_model="gpt-4o-mini", rubric=["correctness"], min_criterion_score=0)


def test_min_criterion_score_six_raises():
    # @trace WL-095
    with pytest.raises(VetterConfigError, match="min_criterion_score must be in range"):
        QualityScoreVetterCheck(judge_model="gpt-4o-mini", rubric=["correctness"], min_criterion_score=6)


def test_empty_rubric_list_raises():
    # @trace WL-095
    with pytest.raises(VetterConfigError, match="rubric list must contain at least one criterion"):
        QualityScoreVetterCheck(judge_model="gpt-4o-mini", rubric=[])


def test_empty_rubric_dict_raises():
    # @trace WL-095
    with pytest.raises(VetterConfigError, match="rubric dict must contain at least one criterion"):
        QualityScoreVetterCheck(judge_model="gpt-4o-mini", rubric={})


def test_rubric_whitespace_only_entries_filtered_list():
    # @trace WL-095
    with pytest.raises(VetterConfigError, match="rubric list must contain at least one criterion"):
        QualityScoreVetterCheck(judge_model="gpt-4o-mini", rubric=["  ", ""])


def test_rubric_whitespace_only_keys_filtered_dict():
    # @trace WL-095
    with pytest.raises(VetterConfigError, match="rubric dict must contain at least one criterion"):
        QualityScoreVetterCheck(judge_model="gpt-4o-mini", rubric={"  ": "desc"})


# ---------------------------------------------------------------------------
# 3. Rubric normalisation
# ---------------------------------------------------------------------------


def test_rubric_list_normalised_to_dict():
    # @trace WL-095
    check = QualityScoreVetterCheck(judge_model="gpt-4o-mini", rubric=["correctness", "safety"])
    assert check._rubric_map == {"correctness": "correctness", "safety": "safety"}


def test_rubric_list_strips_whitespace_around_keys():
    # @trace WL-095
    check = QualityScoreVetterCheck(judge_model="gpt-4o-mini", rubric=[" correctness ", " safety "])
    assert check._rubric_map == {"correctness": "correctness", "safety": "safety"}


def test_rubric_dict_preserved():
    # @trace WL-095
    check = QualityScoreVetterCheck(
        judge_model="gpt-4o-mini",
        rubric={"correctness": "Is the answer correct?", "safety": "Is the answer safe?"},
    )
    assert check._rubric_map["correctness"] == "Is the answer correct?"
    assert check._rubric_map["safety"] == "Is the answer safe?"


def test_rubric_dict_empty_description_falls_back_to_key():
    # @trace WL-095
    check = QualityScoreVetterCheck(
        judge_model="gpt-4o-mini",
        rubric={"correctness": "   "},
    )
    assert check._rubric_map["correctness"] == "correctness"


def test_rubric_dict_strips_keys_and_descriptions():
    # @trace WL-095
    check = QualityScoreVetterCheck(
        judge_model="gpt-4o-mini",
        rubric={" correctness ": "  Uses facts only  "},
    )
    assert check._rubric_map == {"correctness": "Uses facts only"}


def test_rubric_dict_duplicate_keys_after_strip_raises():
    # @trace WL-095
    with pytest.raises(VetterConfigError, match="duplicate rubric criterion after normalization: correctness"):
        QualityScoreVetterCheck(
            judge_model="gpt-4o-mini",
            rubric={"correctness": "A", " correctness ": "B"},
        )


def test_rubric_list_duplicate_entries_after_strip_raises():
    # @trace WL-095
    with pytest.raises(VetterConfigError, match="duplicate rubric criterion after normalization: correctness"):
        QualityScoreVetterCheck(
            judge_model="gpt-4o-mini",
            rubric=["correctness", " correctness "],
        )


# ---------------------------------------------------------------------------
# 4. Passing judge response
# ---------------------------------------------------------------------------


def test_all_scores_high_passes():
    # @trace WL-095
    check = QualityScoreVetterCheck(
        judge_model="gpt-4o-mini",
        rubric=["correctness", "completeness"],
        pass_threshold=0.75,
        min_criterion_score=3,
    )
    mock_resp = _make_litellm_response(
        scores={"correctness": 5, "completeness": 4},
        pass_verdict=True,
        critique="",
    )
    with patch("litellm.acompletion", new=AsyncMock(return_value=mock_resp)):
        result: VetterCheckResult = _run(check.check("run-1", "agent output", {"task": "some task"}))

    assert result.passed is True
    assert result.message == ""
    # mean = (5+4)/2 = 4.5; aggregate_score = 4.5/5 = 0.9
    assert abs(result.score - 0.9) < 1e-4


def test_passed_result_has_correct_metadata_keys():
    # @trace WL-095
    check = QualityScoreVetterCheck(
        judge_model="gpt-4o-mini",
        rubric=["correctness"],
        pass_threshold=0.5,
        min_criterion_score=2,
    )
    mock_resp = _make_litellm_response(scores={"correctness": 4}, pass_verdict=True)
    with patch("litellm.acompletion", new=AsyncMock(return_value=mock_resp)):
        result = _run(check.check("run-2", "output", {}))

    assert "scores" in result.metadata
    assert "judge_model" in result.metadata
    assert "thresholds" in result.metadata
    assert "rubric" in result.metadata
    assert "pass_verdict" in result.metadata


def test_judge_model_recorded_in_metadata():
    # @trace WL-095
    check = QualityScoreVetterCheck(judge_model="claude-3-5-haiku", rubric=["correctness"])
    mock_resp = _make_litellm_response(scores={"correctness": 5}, pass_verdict=True)
    with patch("litellm.acompletion", new=AsyncMock(return_value=mock_resp)):
        result = _run(check.check("run-3", "output", {}))

    assert result.metadata["judge_model"] == "claude-3-5-haiku"


# ---------------------------------------------------------------------------
# 5. Failing paths
# ---------------------------------------------------------------------------


def test_low_aggregate_score_fails():
    # @trace WL-095
    check = QualityScoreVetterCheck(
        judge_model="gpt-4o-mini",
        rubric=["correctness", "completeness"],
        pass_threshold=0.75,
        min_criterion_score=1,
    )
    # mean = (2+2)/2 = 2.0; aggregate_score = 2.0/5 = 0.4 < 0.75
    mock_resp = _make_litellm_response(
        scores={"correctness": 2, "completeness": 2},
        pass_verdict=True,
        critique="Output was incomplete.",
    )
    with patch("litellm.acompletion", new=AsyncMock(return_value=mock_resp)):
        result = _run(check.check("run-4", "bad output", {"task": "test"}))

    assert result.passed is False
    assert "incomplete" in result.message.lower()


def test_per_criterion_floor_fails():
    # @trace WL-095
    check = QualityScoreVetterCheck(
        judge_model="gpt-4o-mini",
        rubric=["correctness", "safety"],
        pass_threshold=0.5,
        min_criterion_score=4,
    )
    # correctness=5 passes floor, safety=2 fails floor (< 4)
    mock_resp = _make_litellm_response(
        scores={"correctness": 5, "safety": 2},
        pass_verdict=True,
        critique="Safety criterion too low.",
    )
    with patch("litellm.acompletion", new=AsyncMock(return_value=mock_resp)):
        result = _run(check.check("run-5", "risky output", {"task": "task"}))

    assert result.passed is False
    assert "safety" in result.message.lower() or "criterion" in result.message.lower()


def test_pass_verdict_false_overrides_good_scores():
    # @trace WL-095
    check = QualityScoreVetterCheck(
        judge_model="gpt-4o-mini",
        rubric=["correctness"],
        pass_threshold=0.5,
        min_criterion_score=2,
    )
    # Good scores, but judge explicitly says pass_verdict=False
    mock_resp = _make_litellm_response(
        scores={"correctness": 5},
        pass_verdict=False,
        critique="Hallucination detected.",
    )
    with patch("litellm.acompletion", new=AsyncMock(return_value=mock_resp)):
        result = _run(check.check("run-6", "output", {}))

    assert result.passed is False
    assert "hallucination" in result.message.lower()


def test_failed_result_message_from_critique():
    # @trace WL-095
    check = QualityScoreVetterCheck(
        judge_model="gpt-4o-mini",
        rubric=["correctness"],
        pass_threshold=0.9,
        min_criterion_score=1,
    )
    # aggregate_score = 3/5 = 0.6 < 0.9
    mock_resp = _make_litellm_response(
        scores={"correctness": 3},
        pass_verdict=True,
        critique="Not detailed enough.",
    )
    with patch("litellm.acompletion", new=AsyncMock(return_value=mock_resp)):
        result = _run(check.check("run-7", "output", {}))

    assert result.passed is False
    assert result.message == "Not detailed enough."


def test_failed_result_fallback_message_when_no_critique():
    # @trace WL-095
    check = QualityScoreVetterCheck(
        judge_model="gpt-4o-mini",
        rubric=["correctness"],
        pass_threshold=0.9,
        min_criterion_score=1,
    )
    # aggregate_score = 3/5 = 0.6 < 0.9; no critique
    mock_resp = _make_litellm_response(scores={"correctness": 3}, pass_verdict=True, critique="")
    with patch("litellm.acompletion", new=AsyncMock(return_value=mock_resp)):
        result = _run(check.check("run-8", "output", {}))

    assert result.passed is False
    assert len(result.message) > 0
    assert "aggregate_score" in result.message


# ---------------------------------------------------------------------------
# 6. Score range validation
# ---------------------------------------------------------------------------


def test_score_above_5_raises_config_error():
    # @trace WL-095
    check = QualityScoreVetterCheck(judge_model="gpt-4o-mini", rubric=["correctness"])
    mock_resp = _make_litellm_response(scores={"correctness": 6}, pass_verdict=True)
    with patch("litellm.acompletion", new=AsyncMock(return_value=mock_resp)):
        with pytest.raises(VetterConfigError, match="scores must be integers in range"):
            _run(check.check("run-9", "output", {}))


def test_score_below_1_raises_config_error():
    # @trace WL-095
    check = QualityScoreVetterCheck(judge_model="gpt-4o-mini", rubric=["correctness"])
    mock_resp = _make_litellm_response(scores={"correctness": 0}, pass_verdict=True)
    with patch("litellm.acompletion", new=AsyncMock(return_value=mock_resp)):
        with pytest.raises(VetterConfigError, match="scores must be integers in range"):
            _run(check.check("run-10", "output", {}))


def test_missing_criterion_score_raises_config_error():
    # @trace WL-095
    check = QualityScoreVetterCheck(judge_model="gpt-4o-mini", rubric=["correctness", "completeness"])
    # Only "correctness" returned, "completeness" missing
    mock_resp = _make_litellm_response(scores={"correctness": 4}, pass_verdict=True)
    with patch("litellm.acompletion", new=AsyncMock(return_value=mock_resp)):
        with pytest.raises(VetterConfigError, match=r"missing score.*completeness"):
            _run(check.check("run-11", "output", {}))


def test_unexpected_criterion_score_raises_config_error():
    # @trace WL-095
    check = QualityScoreVetterCheck(judge_model="gpt-4o-mini", rubric=["correctness"])
    mock_resp = _make_litellm_response(scores={"correctness": 4, "novelty": 5}, pass_verdict=True)
    with patch("litellm.acompletion", new=AsyncMock(return_value=mock_resp)):
        with pytest.raises(VetterConfigError, match=r"unexpected score.*novelty"):
            _run(check.check("run-11b", "output", {}))


def test_float_score_raises_config_error():
    # @trace WL-095
    check = QualityScoreVetterCheck(judge_model="gpt-4o-mini", rubric=["correctness"])
    mock_resp = _make_litellm_response(scores={"correctness": 3.5}, pass_verdict=True)
    with patch("litellm.acompletion", new=AsyncMock(return_value=mock_resp)):
        with pytest.raises(VetterConfigError, match="schema validation"):
            _run(check.check("run-11c", "output", {}))


def test_bool_score_raises_config_error():
    # @trace WL-095
    check = QualityScoreVetterCheck(judge_model="gpt-4o-mini", rubric=["correctness"])
    mock_resp = _make_litellm_response(scores={"correctness": True}, pass_verdict=True)
    with patch("litellm.acompletion", new=AsyncMock(return_value=mock_resp)):
        with pytest.raises(VetterConfigError, match="schema validation"):
            _run(check.check("run-11d", "output", {}))


# ---------------------------------------------------------------------------
# 7. Aggregate score computation
# ---------------------------------------------------------------------------


def test_aggregate_score_is_mean_divided_by_five():
    # @trace WL-095
    check = QualityScoreVetterCheck(
        judge_model="gpt-4o-mini",
        rubric=["a", "b", "c"],
        pass_threshold=0.0,
        min_criterion_score=1,
    )
    # mean(3,4,5) = 4.0; 4.0/5 = 0.8
    mock_resp = _make_litellm_response(scores={"a": 3, "b": 4, "c": 5}, pass_verdict=True)
    with patch("litellm.acompletion", new=AsyncMock(return_value=mock_resp)):
        result = _run(check.check("run-12", "output", {}))

    assert abs(result.score - 0.8) < 1e-4


def test_aggregate_score_boundary_exact_pass_threshold():
    # @trace WL-095
    # mean(4,4)/2 = 4.0; 4.0/5 = 0.8 == pass_threshold=0.8 -> passes (>=)
    check = QualityScoreVetterCheck(
        judge_model="gpt-4o-mini",
        rubric=["a", "b"],
        pass_threshold=0.8,
        min_criterion_score=1,
    )
    mock_resp = _make_litellm_response(scores={"a": 4, "b": 4}, pass_verdict=True)
    with patch("litellm.acompletion", new=AsyncMock(return_value=mock_resp)):
        result = _run(check.check("run-13", "output", {}))

    assert result.passed is True
    assert abs(result.score - 0.8) < 1e-4


def test_scores_stored_as_integers_in_metadata():
    # @trace WL-095
    check = QualityScoreVetterCheck(
        judge_model="gpt-4o-mini",
        rubric=["correctness"],
        pass_threshold=0.0,
        min_criterion_score=1,
    )
    mock_resp = _make_litellm_response(scores={"correctness": 4}, pass_verdict=True)
    with patch("litellm.acompletion", new=AsyncMock(return_value=mock_resp)):
        result = _run(check.check("run-14", "output", {}))

    assert isinstance(result.metadata["scores"]["correctness"], int)
    assert result.metadata["scores"]["correctness"] == 4


# ---------------------------------------------------------------------------
# 8. model_resolver overrides auto
# ---------------------------------------------------------------------------


def test_model_resolver_used_when_judge_model_auto():
    # @trace WL-095
    captured_args: list[str] = []

    def resolver(task: str, ctx: dict[str, Any]) -> str:
        captured_args.append(task)
        return "gpt-4o"

    check = QualityScoreVetterCheck(judge_model="auto", rubric=["correctness"], model_resolver=resolver)
    mock_resp = _make_litellm_response(scores={"correctness": 5}, pass_verdict=True)
    with patch("litellm.acompletion", new=AsyncMock(return_value=mock_resp)) as mock_call:
        _run(check.check("run-15", "output", {}))
        assert mock_call.call_args[1]["model"] == "gpt-4o"

    assert captured_args[0] == "quality scoring"


def test_model_resolver_returning_empty_raises():
    # @trace WL-095
    def bad_resolver(task: str, ctx: dict[str, Any]) -> str:
        return "   "

    check = QualityScoreVetterCheck(judge_model="auto", rubric=["correctness"], model_resolver=bad_resolver)
    with pytest.raises(VetterConfigError, match="model_resolver returned empty model name"):
        _run(check.check("run-16", "output", {}))


def test_model_resolver_returning_non_string_raises():
    # @trace WL-095
    def bad_resolver(task: str, ctx: dict[str, Any]) -> Any:
        return 123

    check = QualityScoreVetterCheck(judge_model="auto", rubric=["correctness"], model_resolver=bad_resolver)
    with pytest.raises(VetterConfigError, match="model_resolver must return a non-empty string model name"):
        _run(check.check("run-16b", "output", {}))


def test_explicit_judge_model_bypasses_resolver():
    # @trace WL-095
    called: list[bool] = []

    def resolver(task: str, ctx: dict[str, Any]) -> str:
        called.append(True)
        return "should-not-use"

    check = QualityScoreVetterCheck(
        judge_model="claude-3-opus",
        rubric=["correctness"],
        model_resolver=resolver,
    )
    mock_resp = _make_litellm_response(scores={"correctness": 5}, pass_verdict=True)
    with patch("litellm.acompletion", new=AsyncMock(return_value=mock_resp)) as mock_call:
        _run(check.check("run-17", "output", {}))
        assert mock_call.call_args[1]["model"] == "claude-3-opus"

    assert not called


# ---------------------------------------------------------------------------
# 9. judge_model="auto" with CapabilityIndex
# ---------------------------------------------------------------------------


def test_auto_model_uses_capability_index_recommend():
    # @trace WL-095
    from thegent.agents.capability_index import (
        AgentRecommendation,
        AgentRecord,
        CapabilityIndex,
    )

    agent_path = Path("/fake/agents/judge.md")
    fake_agent = AgentRecord(
        name="quality-judge",
        path=agent_path,
        description="quality scoring judge",
        capabilities=["quality scoring"],
        model="gpt-4o-quality",
        runner=None,
        raw_frontmatter={},
        body="",
    )
    fake_rec = AgentRecommendation(
        name="quality-judge",
        path=agent_path,
        score=0.9,
        description="quality scoring judge",
        capabilities=["quality scoring"],
    )
    mock_index = MagicMock(spec=CapabilityIndex)
    mock_index.recommend.return_value = [fake_rec]
    mock_index.all_agents.return_value = [fake_agent]

    check = QualityScoreVetterCheck(judge_model="auto", rubric=["correctness"])
    mock_resp = _make_litellm_response(scores={"correctness": 5}, pass_verdict=True)

    with (
        patch(
            "thegent.govern.vetter.checks.QualityScoreVetterCheck._resolve_auto_model", return_value="gpt-4o-quality"
        ),
        patch("litellm.acompletion", new=AsyncMock(return_value=mock_resp)) as mock_call,
    ):
        result = _run(check.check("run-18", "output", {}))
        assert mock_call.call_args[1]["model"] == "gpt-4o-quality"
        assert result.metadata["judge_model"] == "gpt-4o-quality"


def test_auto_model_no_recommendations_raises():
    # @trace WL-095
    from thegent.agents.capability_index import CapabilityIndex

    mock_index = MagicMock(spec=CapabilityIndex)
    mock_index.recommend.return_value = []
    mock_index.all_agents.return_value = []

    check = QualityScoreVetterCheck(judge_model="auto", rubric=["correctness"])
    with patch("thegent.govern.vetter.checks.QualityScoreVetterCheck._resolve_auto_model") as mock_auto:
        mock_auto.side_effect = VetterConfigError(
            "QualityScoreVetterCheck judge_model='auto' found no CapabilityIndex recommendations for quality scoring"
        )
        with pytest.raises(VetterConfigError, match="no CapabilityIndex recommendations"):
            _run(check.check("run-19", "output", {}))


def test_auto_model_context_index_empty_recommendations_raise_without_fallback():
    # @trace WL-095
    from thegent.agents.capability_index import CapabilityIndex

    mock_index = MagicMock(spec=CapabilityIndex)
    mock_index.recommend.return_value = []
    mock_index.all_agents.return_value = []
    check = QualityScoreVetterCheck(judge_model="auto", rubric=["correctness"])

    with patch("litellm.acompletion", new=AsyncMock()) as mock_call:
        with pytest.raises(VetterConfigError, match="no CapabilityIndex recommendations"):
            _run(check.check("run-19b", "output", {"capability_index": mock_index}))
    mock_call.assert_not_called()


def test_auto_model_context_index_none_recommendations_raise_without_fallback():
    # @trace WL-095
    from thegent.agents.capability_index import CapabilityIndex

    mock_index = MagicMock(spec=CapabilityIndex)
    mock_index.recommend.return_value = None
    mock_index.all_agents.return_value = []
    check = QualityScoreVetterCheck(judge_model="auto", rubric=["correctness"])

    with patch("litellm.acompletion", new=AsyncMock()) as mock_call:
        with pytest.raises(VetterConfigError, match="no CapabilityIndex recommendations"):
            _run(check.check("run-19c", "output", {"capability_index": mock_index}))
    mock_call.assert_not_called()


def test_auto_model_via_context_capability_index():
    # @trace WL-095
    # When capability_index is passed in context, _resolve_auto_model should use it
    from thegent.agents.capability_index import (
        AgentRecommendation,
        AgentRecord,
        CapabilityIndex,
    )

    agent_path = Path("/ctx/agents/judge.md")
    fake_agent = AgentRecord(
        name="ctx-judge",
        path=agent_path,
        description="quality scoring",
        capabilities=["quality scoring"],
        model="ctx-model",
        runner=None,
        raw_frontmatter={},
        body="",
    )
    fake_rec = AgentRecommendation(
        name="ctx-judge",
        path=agent_path,
        score=0.95,
        description="quality scoring",
        capabilities=["quality scoring"],
    )
    mock_index = MagicMock(spec=CapabilityIndex)
    mock_index.recommend.return_value = [fake_rec]
    mock_index.all_agents.return_value = [fake_agent]

    check = QualityScoreVetterCheck(judge_model="auto", rubric=["correctness"])
    mock_resp = _make_litellm_response(scores={"correctness": 5}, pass_verdict=True)

    with patch("litellm.acompletion", new=AsyncMock(return_value=mock_resp)):
        result = _run(check.check("run-20", "output", {"capability_index": mock_index}))
        mock_index.recommend.assert_called_once_with("quality scoring", top_n=5)
        assert result.metadata["judge_model"] == "ctx-model"


# ---------------------------------------------------------------------------
# 10. Prompt construction
# ---------------------------------------------------------------------------


def test_prompt_includes_run_id():
    # @trace WL-095
    check = QualityScoreVetterCheck(judge_model="gpt-4o-mini", rubric=["correctness"])
    mock_resp = _make_litellm_response(scores={"correctness": 4}, pass_verdict=True)
    captured_msgs: list[Any] = []

    async def fake_acompletion(**kwargs: Any) -> Any:
        captured_msgs.extend(kwargs["messages"])
        return mock_resp

    with patch("litellm.acompletion", new=fake_acompletion):
        _run(check.check("MY-RUN-ID", "output", {}))

    user_msg_content = next(m["content"] for m in captured_msgs if m["role"] == "user")
    assert "MY-RUN-ID" in user_msg_content


def test_prompt_includes_rubric_criterion_description():
    # @trace WL-095
    check = QualityScoreVetterCheck(
        judge_model="gpt-4o-mini",
        rubric={"correctness": "Is the output factually correct?"},
    )
    mock_resp = _make_litellm_response(scores={"correctness": 4}, pass_verdict=True)
    captured_msgs: list[Any] = []

    async def fake_acompletion(**kwargs: Any) -> Any:
        captured_msgs.extend(kwargs["messages"])
        return mock_resp

    with patch("litellm.acompletion", new=fake_acompletion):
        _run(check.check("run-21", "output", {"task": "test"}))

    user_msg_content = next(m["content"] for m in captured_msgs if m["role"] == "user")
    assert "Is the output factually correct?" in user_msg_content


def test_prompt_requests_1_to_5_scale():
    # @trace WL-095
    check = QualityScoreVetterCheck(judge_model="gpt-4o-mini", rubric=["correctness"])
    mock_resp = _make_litellm_response(scores={"correctness": 4}, pass_verdict=True)
    captured_msgs: list[Any] = []

    async def fake_acompletion(**kwargs: Any) -> Any:
        captured_msgs.extend(kwargs["messages"])
        return mock_resp

    with patch("litellm.acompletion", new=fake_acompletion):
        _run(check.check("run-22", "output", {}))

    user_msg_content = next(m["content"] for m in captured_msgs if m["role"] == "user")
    assert "1 to 5" in user_msg_content or "1-5" in user_msg_content


def test_temperature_is_zero():
    # @trace WL-095
    check = QualityScoreVetterCheck(judge_model="gpt-4o-mini", rubric=["correctness"])
    mock_resp = _make_litellm_response(scores={"correctness": 4}, pass_verdict=True)

    with patch("litellm.acompletion", new=AsyncMock(return_value=mock_resp)) as mock_call:
        _run(check.check("run-23", "output", {}))
        assert mock_call.call_args[1]["temperature"] == 0.0


# ---------------------------------------------------------------------------
# 11. Export from __init__
# ---------------------------------------------------------------------------


def test_exported_from_vetter_init():
    # @trace WL-095
    from thegent.govern import vetter as vetter_module

    assert hasattr(vetter_module, "QualityScoreVetterCheck")
    assert vetter_module.QualityScoreVetterCheck is QualityScoreVetterCheck


def test_exported_in_all():
    # @trace WL-095
    from thegent.govern import vetter as vetter_module

    assert "QualityScoreVetterCheck" in vetter_module.__all__


# ---------------------------------------------------------------------------
# 12. Multi-criterion rubric
# ---------------------------------------------------------------------------


def test_five_criteria_rubric_all_pass():
    # @trace WL-095
    rubric = {
        "correctness": "Factual accuracy",
        "completeness": "Covers all requirements",
        "safety": "No harmful content",
        "clarity": "Easy to understand",
        "conciseness": "No unnecessary verbosity",
    }
    check = QualityScoreVetterCheck(
        judge_model="gpt-4o-mini",
        rubric=rubric,
        pass_threshold=0.6,
        min_criterion_score=3,
    )
    scores = dict.fromkeys(rubric, 5)
    mock_resp = _make_litellm_response(scores=scores, pass_verdict=True)
    with patch("litellm.acompletion", new=AsyncMock(return_value=mock_resp)):
        result = _run(check.check("run-24", "great output", {"task": "complex task"}))

    assert result.passed is True
    assert abs(result.score - 1.0) < 1e-4


def test_single_criterion_rubric_at_floor_passes():
    # @trace WL-095
    check = QualityScoreVetterCheck(
        judge_model="gpt-4o-mini",
        rubric=["correctness"],
        pass_threshold=0.6,
        min_criterion_score=3,
    )
    # score=3 (floor exact), aggregate=3/5=0.6 == threshold -> passes
    mock_resp = _make_litellm_response(scores={"correctness": 3}, pass_verdict=True)
    with patch("litellm.acompletion", new=AsyncMock(return_value=mock_resp)):
        result = _run(check.check("run-25", "output", {}))

    assert result.passed is True
    assert abs(result.score - 0.6) < 1e-4


def test_single_criterion_just_below_floor_fails():
    # @trace WL-095
    check = QualityScoreVetterCheck(
        judge_model="gpt-4o-mini",
        rubric=["correctness"],
        pass_threshold=0.0,  # aggregate threshold irrelevant
        min_criterion_score=4,
    )
    # score=3 < floor=4 -> fails per-criterion check
    mock_resp = _make_litellm_response(scores={"correctness": 3}, pass_verdict=True)
    with patch("litellm.acompletion", new=AsyncMock(return_value=mock_resp)):
        result = _run(check.check("run-26", "output", {}))

    assert result.passed is False


def test_judge_timeout_error_propagates_without_fallback():
    # @trace WL-095
    check = QualityScoreVetterCheck(judge_model="gpt-4o-mini", rubric=["correctness"])
    with patch("litellm.acompletion", new=AsyncMock(side_effect=TimeoutError("judge timeout"))):
        with pytest.raises(asyncio.TimeoutError, match="judge timeout"):
            _run(check.check("run-timeout", "output", {}))


def test_judge_runtime_error_propagates_without_wrapping():
    # @trace WL-095
    check = QualityScoreVetterCheck(judge_model="gpt-4o-mini", rubric=["correctness"])
    with patch("litellm.acompletion", new=AsyncMock(side_effect=RuntimeError("judge transport failed"))):
        with pytest.raises(RuntimeError, match="judge transport failed"):
            _run(check.check("run-judge-error", "output", {}))


def test_metadata_scores_keys_are_sorted_for_deterministic_audit_contract():
    # @trace WL-095
    check = QualityScoreVetterCheck(
        judge_model="gpt-4o-mini",
        rubric={"zeta": "zeta quality", "alpha": "alpha quality"},
        pass_threshold=0.1,
        min_criterion_score=1,
    )
    mock_resp = _make_litellm_response(scores={"zeta": 4, "alpha": 5}, pass_verdict=True)

    with patch("litellm.acompletion", new=AsyncMock(return_value=mock_resp)):
        result = _run(check.check("run-metadata-order", "output", {}))

    assert list(result.metadata["scores"].keys()) == ["alpha", "zeta"]
