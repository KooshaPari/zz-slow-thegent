"""Integration tests for the full normalization pipeline.

Tests adapter -> parser -> validation -> policy chain end-to-end,
verifying that raw agent output is properly normalized to CSM and
that policy enforcement operates on normalized results.
"""

from __future__ import annotations

import pytest

from tests.conftest_factories import make_csm, make_fallback_policy
from thegent.contracts.adapters import (
    XMLOutputAdapter,
    normalize_output,
)
from thegent.contracts.csm import CSMStatus
from thegent.contracts.policy import evaluate_fallback
from thegent.contracts.validation import (
    InvariantViolation,
    SemanticValidationError,
    ensure_valid_csm,
    validate_csm,
)


@pytest.mark.integration
class TestAdapterParserChain:
    """Tests that XMLOutputAdapter correctly delegates to IncrementalXMLParser."""

    def test_xml_adapter_parses_complete_output(self) -> None:
        # @trace FR-CTR-002
        """A well-formed XML output should yield a COMPLETED CSM with high confidence."""
        adapter = XMLOutputAdapter("test-provider")
        raw = (
            "<TASK_ID>task-001</TASK_ID>"
            "<STATUS>completed</STATUS>"
            "<SUMMARY>All files updated successfully</SUMMARY>"
            "<PROGRESS>100%</PROGRESS>"
        )
        result = adapter.normalize(raw, context={"run_id": "run-001"})

        assert result.csm.status == CSMStatus.COMPLETED
        assert result.csm.task_id == "task-001"
        assert result.csm.summary == "All files updated successfully"
        assert result.csm.progress == 1.0
        assert result.confidence >= 0.7
        assert result.source_provider == "test-provider"

    def test_xml_adapter_handles_in_progress(self) -> None:
        # @trace FR-CTR-002
        """IN_PROGRESS status should parse with fractional progress."""
        adapter = XMLOutputAdapter("test-provider")
        raw = "<STATUS>in_progress</STATUS><PROGRESS>50</PROGRESS>"
        result = adapter.normalize(raw)

        assert result.csm.status == CSMStatus.IN_PROGRESS
        assert result.csm.progress == 0.5

    def test_xml_adapter_returns_parse_errors_on_empty_tags(self) -> None:
        # @trace FR-CTR-003
        """When no XML tags are found, adapter returns low confidence with errors."""
        adapter = XMLOutputAdapter("test-provider")
        raw = "Just some plain text with no XML at all."
        result = adapter.normalize(raw)

        assert result.confidence == 0.0
        assert "no_xml_tags_detected" in result.parse_errors
        assert result.csm.status == CSMStatus.PENDING

    def test_parser_feeds_adapter_with_multiple_tags(self) -> None:
        # @trace FR-CTR-002
        """Multiple XML tags are all extracted and mapped to CSM fields."""
        raw = (
            "<TASK_ID>t-1</TASK_ID>"
            "<STATUS>completed</STATUS>"
            "<SUMMARY>Refactored module</SUMMARY>"
            "<OBJECTIVE>Clean up code</OBJECTIVE>"
            "<PROGRESS>100</PROGRESS>"
            "<ACTIONS_COMPLETED>Removed dead code\nFixed imports</ACTIONS_COMPLETED>"
            "<NEXT_STEPS>Run tests\nDeploy</NEXT_STEPS>"
        )
        adapter = XMLOutputAdapter("claude")
        result = adapter.normalize(raw, context={"run_id": "r-1"})

        assert result.csm.task_id == "t-1"
        assert result.csm.objective == "Clean up code"
        assert len(result.csm.actions_completed) == 2
        assert "Removed dead code" in result.csm.actions_completed
        assert len(result.csm.next_steps) == 2


@pytest.mark.integration
class TestAdapterValidationChain:
    """Tests that adapter output is properly validated by the validation layer."""

    def test_completed_without_summary_triggers_validation_issue(self) -> None:
        # @trace FR-CTR-003
        """An adapter result with COMPLETED but no summary should have validation issues."""
        adapter = XMLOutputAdapter("test-provider")
        raw = "<STATUS>completed</STATUS><PROGRESS>100</PROGRESS>"
        result = adapter.normalize(raw)

        issues = validate_csm(result.csm)
        assert any("summary is empty" in i for i in issues)

    def test_valid_completed_output_passes_validation(self) -> None:
        # @trace FR-CTR-003
        """A properly formed COMPLETED output should pass validation cleanly."""
        adapter = XMLOutputAdapter("test-provider")
        raw = "<STATUS>completed</STATUS><SUMMARY>Done</SUMMARY><PROGRESS>100%</PROGRESS>"
        result = adapter.normalize(raw)
        issues = validate_csm(result.csm)

        assert issues == []

    def test_ensure_valid_csm_raises_on_invariant_violation(self) -> None:
        # @trace FR-CTR-003
        """ensure_valid_csm should raise InvariantViolation for bad CSM."""
        csm = make_csm(status="COMPLETED", progress=0.0)

        with pytest.raises(InvariantViolation, match="COMPLETED but progress"):
            ensure_valid_csm(csm)


@pytest.mark.integration
class TestNormalizationPolicyChain:
    """Tests the full normalize_output -> evaluate_fallback policy chain."""

    def test_structured_output_passes_default_policy(self) -> None:
        # @trace FR-CTR-008
        """Well-structured XML output should pass default fallback policy."""
        raw = "<STATUS>completed</STATUS><SUMMARY>Task done</SUMMARY><PROGRESS>100%</PROGRESS>"
        result = normalize_output("claude", raw, context={"run_id": "run-1"})

        policy = make_fallback_policy()
        is_fallback = result.csm.source_contract == "fallback-plain"
        violations = evaluate_fallback(
            provider="claude",
            confidence=result.confidence,
            is_fallback=is_fallback,
            policy=policy,
        )
        assert violations == []

    def test_plain_text_triggers_fallback_detection(self) -> None:
        # @trace FR-CTR-008
        """Plain text that falls back should be detected by the policy layer."""
        raw = "Everything is fine, the work is done."
        result = normalize_output("claude", raw, context={"run_id": "run-2"})

        # The result uses fallback-plain when XML parsing fails
        is_fallback = result.csm.source_contract == "fallback-plain"
        policy = make_fallback_policy(allow_plain_fallback=False)
        violations = evaluate_fallback(
            provider="claude",
            confidence=result.confidence,
            is_fallback=is_fallback,
            policy=policy,
        )
        if is_fallback:
            assert any("disabled" in v for v in violations)

    def test_strict_provider_blocks_fallback(self) -> None:
        # @trace FR-CTR-008
        """A strict provider falling back should generate a policy violation."""
        policy = make_fallback_policy(strict_providers=["gemini"])

        violations = evaluate_fallback(
            provider="gemini",
            confidence=0.5,
            is_fallback=True,
            policy=policy,
        )
        assert any("strict" in v.lower() for v in violations)

    def test_low_confidence_below_threshold_violates_policy(self) -> None:
        # @trace FR-CTR-008
        """Confidence below the min threshold should produce a violation."""
        policy = make_fallback_policy(min_confidence_threshold=0.8)

        violations = evaluate_fallback(
            provider="claude",
            confidence=0.3,
            is_fallback=False,
            policy=policy,
        )
        assert any("below threshold" in v for v in violations)

    def test_high_fallback_rate_violates_policy(self) -> None:
        # @trace FR-CTR-008
        """When global fallback rate exceeds budget, policy should flag it."""
        policy = make_fallback_policy(max_fallback_rate=0.2)
        stats = {"fallback_rate": 0.5}

        violations = evaluate_fallback(
            provider="claude",
            confidence=0.8,
            is_fallback=False,
            policy=policy,
            stats=stats,
        )
        assert any("exceeds budget" in v for v in violations)

    def test_normalize_output_no_fallback_raises_on_failure(self) -> None:
        # @trace FR-CTR-008
        """When allow_fallback=False and normalization fails, should raise."""
        raw = "No XML here"
        with pytest.raises(SemanticValidationError, match="fallback is disabled"):
            normalize_output("nonexistent-provider-xyz", raw, allow_fallback=False)
