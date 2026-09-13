"""Unit tests for VetterPolicy, VetterCheck Protocol, VetterResult, and all 6 concrete checks.

Every test function carries:
  # @trace WL-090

Covers:
- VetterVerdict enum values
- VetterCheckResult model creation and frozen immutability
- VetterResult model creation and frozen immutability
- VetterPolicy model creation and frozen immutability
- Protocol conformance for all 6 check classes
- Each concrete check pass/fail path (mocked dependencies)
- VetterConfigError for missing firewall in SafetyCheck
- VetterConfigError for empty schema in SchemaCheck
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import orjson as json
import pytest

from thegent.govern.vetter.checks import (
    DiffSizeCheck,
    LLMJudgeCheck,
    QualityScoreVetterCheck,
    RuffCheck,
    SafetyCheck,
    SchemaCheck,
    TestPassCheck,
    _extract_changed_py_files,
)
from thegent.govern.vetter.models import (
    VetterCheck,
    VetterCheckResult,
    VetterConfigError,
    VetterPolicy,
    VetterResult,
    VetterVerdict,
)

# ---------------------------------------------------------------------------
# VetterVerdict enum
# ---------------------------------------------------------------------------


def test_verdict_approved():
    # @trace WL-090
    assert VetterVerdict.APPROVED == "approved"


def test_verdict_rejected():
    # @trace WL-090
    assert VetterVerdict.REJECTED == "rejected"


def test_verdict_escalated():
    # @trace WL-090
    assert VetterVerdict.ESCALATED == "escalated"


def test_verdict_revision_requested():
    # @trace WL-090
    assert VetterVerdict.REVISION_REQUESTED == "revision_requested"


def test_verdict_is_str_enum():
    # @trace WL-090
    assert isinstance(VetterVerdict.APPROVED, str)


# ---------------------------------------------------------------------------
# VetterCheckResult
# ---------------------------------------------------------------------------


def test_check_result_basic_creation():
    # @trace WL-090
    r = VetterCheckResult(check_name="test", passed=True)
    assert r.check_name == "test"
    assert r.passed is True
    assert r.score is None
    assert r.message == ""
    assert r.metadata == {}


def test_check_result_is_frozen():
    # @trace WL-090
    r = VetterCheckResult(check_name="test", passed=True)
    with pytest.raises(Exception):
        r.passed = False  # type: ignore[misc]


def test_check_result_with_score():
    # @trace WL-090
    r = VetterCheckResult(check_name="llm_judge", passed=False, score=0.45, message="too low")
    assert r.score == 0.45
    assert r.message == "too low"


# ---------------------------------------------------------------------------
# VetterResult
# ---------------------------------------------------------------------------


def test_vetter_result_basic():
    # @trace WL-090
    cr = VetterCheckResult(check_name="schema", passed=True)
    result = VetterResult(run_id="run-1", verdict=VetterVerdict.APPROVED, check_results=[cr])
    assert result.run_id == "run-1"
    assert result.verdict == VetterVerdict.APPROVED
    assert len(result.check_results) == 1
    assert result.revision_prompt is None
    assert result.escalation_reason is None
    assert result.timestamp > 0


def test_vetter_result_is_frozen():
    # @trace WL-090
    result = VetterResult(run_id="r", verdict=VetterVerdict.REJECTED, check_results=[])
    with pytest.raises(Exception):
        result.verdict = VetterVerdict.APPROVED  # type: ignore[misc]


def test_vetter_result_revision_fields():
    # @trace WL-090
    result = VetterResult(
        run_id="r2",
        verdict=VetterVerdict.REVISION_REQUESTED,
        check_results=[],
        revision_prompt="Please fix the imports",
    )
    assert result.revision_prompt == "Please fix the imports"


# ---------------------------------------------------------------------------
# VetterPolicy
# ---------------------------------------------------------------------------


def test_policy_basic_creation():
    # @trace WL-090
    p = VetterPolicy(checks=["schema", "safety"])
    assert p.checks == ["schema", "safety"]
    assert p.max_revision_rounds == 3
    assert p.bypass_checks == []
    assert p.escalate_on == []
    assert p.thresholds == {}
    assert p.on_fail == "reject"
    assert p.escalation_lane == "standard"


def test_policy_is_frozen():
    # @trace WL-090
    p = VetterPolicy(checks=["schema"])
    with pytest.raises(Exception):
        p.checks = ["other"]  # type: ignore[misc]


def test_policy_with_all_fields():
    # @trace WL-090
    p = VetterPolicy(
        checks=["schema", "llm_judge"],
        escalate_on=["safety"],
        on_fail="escalate",
        escalation_lane="critical",
        thresholds={"llm_judge": 0.8},
        max_revision_rounds=5,
        bypass_checks=["ruff"],
    )
    assert p.max_revision_rounds == 5
    assert p.thresholds["llm_judge"] == 0.8
    assert "ruff" in p.bypass_checks
    assert p.on_fail == "escalate"
    assert p.escalation_lane == "critical"


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------


def test_schema_check_implements_protocol():
    # @trace WL-090
    check = SchemaCheck(schema={"type": "object"})
    assert isinstance(check, VetterCheck)


def test_diff_size_check_implements_protocol():
    # @trace WL-090
    check = DiffSizeCheck()
    assert isinstance(check, VetterCheck)


def test_safety_check_implements_protocol():
    # @trace WL-090
    mock_fw = MagicMock()
    mock_fw.inspect_output.return_value = ("output", [])
    check = SafetyCheck(firewall=mock_fw)
    assert isinstance(check, VetterCheck)


def test_llm_judge_check_implements_protocol():
    # @trace WL-090
    check = LLMJudgeCheck()
    assert isinstance(check, VetterCheck)


def test_quality_score_check_implements_protocol():
    # @trace WL-095
    check = QualityScoreVetterCheck()
    assert isinstance(check, VetterCheck)


def test_test_pass_check_implements_protocol():
    # @trace WL-090
    check = TestPassCheck()
    assert isinstance(check, VetterCheck)


def test_ruff_check_implements_protocol():
    # @trace WL-090
    check = RuffCheck()
    assert isinstance(check, VetterCheck)


# ---------------------------------------------------------------------------
# SchemaCheck
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_schema_check_passes_valid_json():
    # @trace WL-090
    check = SchemaCheck(schema={"type": "object", "properties": {"key": {"type": "string"}}})
    result = await check.check("run-1", json.dumps({"key": "value"}).decode(), {})
    assert result.passed is True
    assert result.check_name == "schema"


@pytest.mark.asyncio
async def test_schema_check_fails_invalid_json():
    # @trace WL-090
    check = SchemaCheck(schema={"type": "object"})
    result = await check.check("run-1", "not valid json {{", {})
    assert result.passed is False
    assert "JSON parse error" in result.message


@pytest.mark.asyncio
async def test_schema_check_fails_schema_violation():
    # @trace WL-090
    check = SchemaCheck(schema={"type": "object", "required": ["name"]})
    result = await check.check("run-1", json.dumps({"other": 1}).decode(), {})
    assert result.passed is False
    assert "Schema validation failed" in result.message


@pytest.mark.asyncio
async def test_schema_check_raises_on_empty_schema():
    # @trace WL-090
    check = SchemaCheck(schema={})
    with pytest.raises(VetterConfigError, match="schema must not be empty"):
        await check.check("run-1", "{}", {})


# ---------------------------------------------------------------------------
# DiffSizeCheck
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_diff_size_check_passes_small_diff():
    # @trace WL-090
    diff = "\n".join([f"+line{i}" for i in range(10)])
    check = DiffSizeCheck(max_lines=100)
    result = await check.check("run-1", diff, {})
    assert result.passed is True
    assert result.metadata["diff_lines"] == 10


@pytest.mark.asyncio
async def test_diff_size_check_fails_large_diff():
    # @trace WL-090
    diff = "\n".join([f"+line{i}" for i in range(600)])
    check = DiffSizeCheck(max_lines=500)
    result = await check.check("run-1", diff, {})
    assert result.passed is False
    assert "exceeds max" in result.message


@pytest.mark.asyncio
async def test_diff_size_check_excludes_headers():
    # @trace WL-090
    diff = "--- a/file.py\n+++ b/file.py\n" + "\n".join([f"+line{i}" for i in range(5)])
    check = DiffSizeCheck(max_lines=100)
    result = await check.check("run-1", diff, {})
    assert result.passed is True
    assert result.metadata["diff_lines"] == 5


# ---------------------------------------------------------------------------
# SafetyCheck
# ---------------------------------------------------------------------------


def test_safety_check_raises_without_firewall():
    # @trace WL-090
    with pytest.raises(VetterConfigError, match="SemanticFirewall"):
        SafetyCheck(firewall=None)


@pytest.mark.asyncio
async def test_safety_check_passes_clean_output():
    # @trace WL-090
    mock_fw = MagicMock()
    mock_fw.inspect_output.return_value = ("clean output", [])
    check = SafetyCheck(firewall=mock_fw)
    result = await check.check("run-1", "clean output", {})
    assert result.passed is True


@pytest.mark.asyncio
async def test_safety_check_fails_on_violations():
    # @trace WL-090
    mock_fw = MagicMock()
    mock_fw.inspect_output.return_value = ("output", ["CRITICAL: rm -rf / detected"])
    check = SafetyCheck(firewall=mock_fw)
    result = await check.check("run-1", "output", {})
    assert result.passed is False
    assert "Safety violations" in result.message
    assert result.metadata["blocked"] is True


# ---------------------------------------------------------------------------
# LLMJudgeCheck
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_llm_judge_check_passes_good_output():
    # @trace WL-090
    mock_response = MagicMock()
    mock_response.choices[0].message.content = json.dumps(
        {
            "scores": {"correctness": 5, "completeness": 4, "safety": 5},
            "pass_verdict": True,
            "critique": "",
        }
    )
    with patch("litellm.acompletion", new_callable=AsyncMock, return_value=mock_response):
        check = LLMJudgeCheck(pass_threshold=0.75)
        result = await check.check("run-1", "good output", {"task": "write a function"})
    assert result.passed is True
    assert result.score is not None
    assert result.score > 0.75


@pytest.mark.asyncio
async def test_llm_judge_check_fails_low_score():
    # @trace WL-090
    mock_response = MagicMock()
    mock_response.choices[0].message.content = json.dumps(
        {
            "scores": {"correctness": 1, "completeness": 2, "safety": 1},
            "pass_verdict": False,
            "critique": "Output is incomplete and incorrect",
        }
    )
    with patch("litellm.acompletion", new_callable=AsyncMock, return_value=mock_response):
        check = LLMJudgeCheck(pass_threshold=0.75)
        result = await check.check("run-1", "bad output", {"task": "write a function"})
    assert result.passed is False
    assert "incomplete" in result.message


# ---------------------------------------------------------------------------
# QualityScoreVetterCheck
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_quality_score_check_passes_when_all_thresholds_met():
    # @trace WL-095
    mock_response = MagicMock()
    mock_response.choices[0].message.content = json.dumps(
        {
            "scores": {"correctness": 0.95, "completeness": 0.85, "safety": 0.9},
            "pass_verdict": True,
            "critique": "",
        }
    )
    with patch("litellm.acompletion", new_callable=AsyncMock, return_value=mock_response):
        check = QualityScoreVetterCheck(
            pass_threshold=0.8,
            min_criterion_score=0.7,
            rubric=["correctness", "completeness", "safety"],
        )
        result = await check.check("run-qs-1", "good output", {"task": "write safe code"})
    assert result.passed is True
    assert result.score is not None
    assert result.metadata["judge_model"] == "gpt-4o-mini"


@pytest.mark.asyncio
async def test_quality_score_check_fails_on_aggregate_threshold():
    # @trace WL-095
    mock_response = MagicMock()
    mock_response.choices[0].message.content = json.dumps(
        {
            "scores": {"correctness": 0.6, "completeness": 0.6, "safety": 0.6},
            "pass_verdict": True,
            "critique": "Average quality is too low",
        }
    )
    with patch("litellm.acompletion", new_callable=AsyncMock, return_value=mock_response):
        check = QualityScoreVetterCheck(pass_threshold=0.75, min_criterion_score=0.5)
        result = await check.check("run-qs-2", "mediocre output", {"task": "write code"})
    assert result.passed is False
    assert "too low" in result.message


@pytest.mark.asyncio
async def test_quality_score_check_fails_on_min_criterion_threshold():
    # @trace WL-095
    mock_response = MagicMock()
    mock_response.choices[0].message.content = json.dumps(
        {
            "scores": {"correctness": 0.9, "completeness": 0.85, "safety": 0.2},
            "pass_verdict": True,
            "critique": "Safety score is unacceptable",
        }
    )
    with patch("litellm.acompletion", new_callable=AsyncMock, return_value=mock_response):
        check = QualityScoreVetterCheck(pass_threshold=0.7, min_criterion_score=0.5)
        result = await check.check("run-qs-3", "unsafe output", {"task": "write code"})
    assert result.passed is False
    assert "unacceptable" in result.message


@pytest.mark.asyncio
async def test_quality_score_check_raises_on_malformed_json():
    # @trace WL-095
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "not-json"
    with patch("litellm.acompletion", new_callable=AsyncMock, return_value=mock_response):
        check = QualityScoreVetterCheck()
        with pytest.raises(VetterConfigError, match="judge response was not valid JSON"):
            await check.check("run-qs-4", "output", {"task": "task"})


@pytest.mark.asyncio
async def test_quality_score_check_raises_on_invalid_payload_shape():
    # @trace WL-095
    mock_response = MagicMock()
    mock_response.choices[0].message.content = json.dumps({"scores": {"correctness": 0.8}}).decode()
    with patch("litellm.acompletion", new_callable=AsyncMock, return_value=mock_response):
        check = QualityScoreVetterCheck()
        with pytest.raises(VetterConfigError, match="judge response failed schema validation"):
            await check.check("run-qs-4b", "output", {"task": "task"})


@pytest.mark.asyncio
async def test_quality_score_check_auto_model_uses_capability_index_recommendation():
    # @trace WL-095
    mock_response = MagicMock()
    mock_response.choices[0].message.content = json.dumps(
        {
            "scores": {"correctness": 0.8, "completeness": 0.8, "safety": 0.8},
            "pass_verdict": True,
            "critique": "",
        }
    ).decode()

    fake_agent = MagicMock()
    fake_agent.path = Path("/tmp/quality-agent.md")
    fake_agent.model = "gpt-4o-mini"
    fake_rec = MagicMock()
    fake_rec.path = fake_agent.path
    fake_index = MagicMock()
    fake_index.recommend.return_value = [fake_rec]
    fake_index.all_agents.return_value = [fake_agent]

    with (
        patch("thegent.agents.capability_index.CapabilityIndex.get", return_value=fake_index),
        patch("litellm.acompletion", new_callable=AsyncMock, return_value=mock_response),
    ):
        check = QualityScoreVetterCheck(judge_model="auto")
        result = await check.check("run-qs-5", "output", {"task": "task"})

    assert result.passed is True
    assert result.metadata["judge_model"] == "gpt-4o-mini"
    fake_index.recommend.assert_called_once_with("quality scoring", top_n=5)


@pytest.mark.asyncio
async def test_quality_score_check_raises_when_auto_model_has_no_recommendations():
    # @trace WL-095
    fake_index = MagicMock()
    fake_index.recommend.return_value = []
    fake_index.all_agents.return_value = []
    with patch("thegent.agents.capability_index.CapabilityIndex.get", return_value=fake_index):
        check = QualityScoreVetterCheck(judge_model="auto")
        with pytest.raises(VetterConfigError, match="found no CapabilityIndex recommendations"):
            await check.check("run-qs-6", "output", {"task": "task"})


@pytest.mark.asyncio
async def test_quality_score_check_raises_when_auto_model_has_no_configured_model():
    # @trace WL-095
    fake_agent = MagicMock()
    fake_agent.path = Path("/tmp/quality-agent.md")
    fake_agent.model = None
    fake_rec = MagicMock()
    fake_rec.path = fake_agent.path
    fake_index = MagicMock()
    fake_index.recommend.return_value = [fake_rec]
    fake_index.all_agents.return_value = [fake_agent]
    with patch("thegent.agents.capability_index.CapabilityIndex.get", return_value=fake_index):
        check = QualityScoreVetterCheck(judge_model="auto")
        with pytest.raises(VetterConfigError, match="did not include a configured model"):
            await check.check("run-qs-7", "output", {"task": "task"})


@pytest.mark.asyncio
async def test_quality_score_check_prefers_explicit_model_resolver_when_provided():
    # @trace WL-095
    mock_response = MagicMock()
    mock_response.choices[0].message.content = json.dumps(
        {
            "scores": {"correctness": 0.8, "completeness": 0.8, "safety": 0.8},
            "pass_verdict": True,
            "critique": "",
        }
    ).decode()
    resolver = MagicMock(return_value="gpt-4.1-mini")
    with patch("litellm.acompletion", new_callable=AsyncMock, return_value=mock_response):
        check = QualityScoreVetterCheck(judge_model="auto", model_resolver=resolver)
        result = await check.check("run-qs-8", "output", {"task": "task"})

    assert result.passed is True
    assert result.metadata["judge_model"] == "gpt-4.1-mini"
    resolver.assert_called_once_with("quality scoring", {"task": "task"})


@pytest.mark.asyncio
async def test_quality_score_check_raises_when_auto_model_resolver_returns_empty():
    # @trace WL-095
    check = QualityScoreVetterCheck(judge_model="auto")
    check.model_resolver = MagicMock(return_value=" ")
    with pytest.raises(VetterConfigError, match="model_resolver returned empty model name"):
        await check.check("run-qs-9", "output", {"task": "task"})


@pytest.mark.asyncio
async def test_quality_score_check_builds_deterministic_failure_message_without_critique():
    # @trace WL-095
    mock_response = MagicMock()
    mock_response.choices[0].message.content = json.dumps(
        {
            "scores": {"correctness": 5, "completeness": 4, "safety": 2},
            "pass_verdict": True,
            "critique": "   ",
        }
    ).decode()
    with patch("litellm.acompletion", new_callable=AsyncMock, return_value=mock_response):
        check = QualityScoreVetterCheck(pass_threshold=0.8, min_criterion_score=3)
        result = await check.check("run-qs-10", "output", {"task": "task"})

    assert result.passed is False
    assert "failing_criteria=safety=2" in result.message
    assert "aggregate_score=" in result.message


# ---------------------------------------------------------------------------
# TestPassCheck
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_test_pass_check_passes_on_zero_exit():
    # @trace WL-090
    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (b"2 passed", None)
    mock_proc.returncode = 0
    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        check = TestPassCheck()
        result = await check.check("run-1", "", {})
    assert result.passed is True


@pytest.mark.asyncio
async def test_test_pass_check_fails_on_nonzero_exit():
    # @trace WL-090
    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (b"FAILED 1 error", None)
    mock_proc.returncode = 1
    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        check = TestPassCheck()
        result = await check.check("run-1", "", {})
    assert result.passed is False
    assert "FAILED" in result.message


@pytest.mark.asyncio
async def test_test_pass_check_handles_timeout():
    # @trace WL-090
    mock_proc = AsyncMock()
    mock_proc.communicate.side_effect = asyncio.TimeoutError
    # kill() on asyncio.subprocess.Process is synchronous; patch to MagicMock to avoid
    # coroutine-never-awaited RuntimeWarning when using AsyncMock.
    mock_proc.kill = MagicMock(return_value=None)
    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        check = TestPassCheck(timeout_seconds=1)
        result = await check.check("run-1", "", {})
    assert result.passed is False
    assert "timed out" in result.message
    assert result.metadata["timeout"] is True


# ---------------------------------------------------------------------------
# RuffCheck
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ruff_check_skips_when_no_py_files():
    # @trace WL-090
    check = RuffCheck()
    result = await check.check("run-1", "no python files here", {})
    assert result.passed is True
    assert "skipped" in result.message


@pytest.mark.asyncio
async def test_ruff_check_passes_clean_files():
    # @trace WL-090
    diff = "--- a/src/foo.py\n+++ b/src/foo.py\n+x = 1\n"
    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (b"", None)
    mock_proc.returncode = 0
    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        check = RuffCheck()
        result = await check.check("run-1", diff, {})
    assert result.passed is True


@pytest.mark.asyncio
async def test_ruff_check_fails_on_violations():
    # @trace WL-090
    diff = "--- a/src/foo.py\n+++ b/src/foo.py\n+import os\n"
    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (b"src/foo.py:1:1: F401 'os' imported but unused", None)
    mock_proc.returncode = 1
    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        check = RuffCheck()
        result = await check.check("run-1", diff, {})
    assert result.passed is False
    assert "F401" in result.message


# ---------------------------------------------------------------------------
# Helper: _extract_changed_py_files
# ---------------------------------------------------------------------------


def test_extract_changed_py_files_parses_unified_diff():
    # @trace WL-090
    diff = (
        "--- a/src/thegent/foo.py\n"
        "+++ b/src/thegent/foo.py\n"
        "@@ -1,3 +1,4 @@\n"
        "+import sys\n"
        "--- a/tests/test_bar.py\n"
        "+++ b/tests/test_bar.py\n"
    )
    files = _extract_changed_py_files(diff)
    assert "src/thegent/foo.py" in files
    assert "tests/test_bar.py" in files


def test_extract_changed_py_files_deduplicates():
    # @trace WL-090
    diff = "--- a/foo.py\n+++ b/foo.py\n--- a/foo.py\n+++ b/foo.py\n"
    files = _extract_changed_py_files(diff)
    assert files.count("foo.py") == 1
