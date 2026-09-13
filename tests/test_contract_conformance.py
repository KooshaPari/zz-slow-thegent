"""Conformance tests for provider adapters.

Ensures every registered provider adapter satisfies the contract requirements
and produces semantically valid CanonicalStructuredMessage (CSM) objects.
"""

import pytest

from thegent.contracts import (
    ADAPTER_REGISTRY,
    AdapterResult,
    CSMStatus,
    OutputAdapter,
    normalize_output,
)
from thegent.contracts.validation import validate_csm


@pytest.mark.parametrize("provider", list(ADAPTER_REGISTRY.keys()))
def test_adapter_registration(provider: str) -> None:
    # @trace FR-CTR-012
    """Every registered provider has an adapter."""
    adapter = ADAPTER_REGISTRY[provider]
    assert isinstance(adapter, OutputAdapter)
    assert adapter.provider == provider


@pytest.mark.parametrize("provider", list(ADAPTER_REGISTRY.keys()))
def test_adapter_normalize_plain_text(provider: str) -> None:
    # @trace FR-CTR-012
    """Adapters should handle plain text gracefully (even if they expect XML)."""
    raw = "Just some plain text without tags."
    res = normalize_output(provider, raw)
    assert isinstance(res, AdapterResult)
    assert res.csm.summary
    assert not validate_csm(res.csm)


@pytest.mark.parametrize(
    "provider",
    ["copilot", "gemini", "claude", "codex", "cursor", "cursor-agent", "antigravity"],
)
def test_xml_adapter_valid_tags(provider: str) -> None:
    # @trace FR-CTR-012
    """XML adapters should extract standard tags correctly."""
    raw = """
    <SUMMARY>Task completed successfully.</SUMMARY>
    <STATUS>completed</STATUS>
    <PROGRESS>100%</PROGRESS>
    <OBJECTIVE>Test XML extraction</OBJECTIVE>
    """
    res = normalize_output(provider, raw)
    assert res.csm.summary == "Task completed successfully."
    assert res.csm.status == CSMStatus.COMPLETED
    assert res.csm.progress == 1.0
    assert res.csm.objective == "Test XML extraction"
    assert res.confidence == 1.0
    assert not res.parse_errors


def test_xml_adapter_partial_tags() -> None:
    # @trace FR-CTR-012
    """XML adapters should handle partial/missing tags with lower confidence."""
    provider = "claude"
    raw = "<SUMMARY>Incomplete"
    res = normalize_output(provider, raw)
    # XMLOutputAdapter uses extract_tags which currently only handles balanced tags.
    # So SUMMARY will be missing in csm, and it will fall back to extract_condensed if allow_fallback=True.
    # Wait, normalize_output calls adapter.normalize.
    # XMLOutputAdapter.normalize calls extract_tags(text).
    # If no balanced tags, tags will be empty.
    # CSM status will be PENDING (default).
    assert res.csm.status == CSMStatus.PENDING
    assert res.confidence < 1.0


@pytest.mark.parametrize("provider", ["minimax", "cliproxy"])
def test_generic_adapter_conformance(provider: str) -> None:
    # @trace FR-CTR-012
    """Generic adapters should produce valid CSMs with limited metadata."""
    raw = "Detailed output from a generic provider."
    res = normalize_output(provider, raw)
    assert res.csm.summary == "Detailed output from a generic provider."
    assert res.csm.status == CSMStatus.COMPLETED
    assert res.csm.source_contract == "plain"
    assert res.confidence == 0.7


def test_task_tool_mismatch_conformance() -> None:
    # @trace FR-CTR-012
    """Test that XMLOutputAdapter handles both PascalCase (docs) and snake_case (impl) variants."""
    provider = "codex"

    # PascalCase (docs)
    raw_pascal = """
    <TaskUpdate>Implementing feature X</TaskUpdate>
    <TaskId>QA-123</TaskId>
    <Objective>Deliver feature X</Objective>
    <Status>completed</Status>
    """
    res_pascal = normalize_output(provider, raw_pascal)
    assert res_pascal.csm.task_id == "QA-123"
    assert res_pascal.csm.summary == "Implementing feature X"
    assert res_pascal.csm.status == CSMStatus.COMPLETED

    # snake_case (impl)
    raw_snake = """
    <task_id>QA-124</task_id>
    <task_objective>Deliver feature Y</task_objective>
    <task_status>in_progress</task_status>
    <task_summary>Working on feature Y</task_summary>
    """
    res_snake = normalize_output(provider, raw_snake)
    assert res_snake.csm.task_id == "QA-124"
    assert res_snake.csm.objective == "Deliver feature Y"
    assert res_snake.csm.status == CSMStatus.IN_PROGRESS
    assert res_snake.csm.summary == "Working on feature Y"
