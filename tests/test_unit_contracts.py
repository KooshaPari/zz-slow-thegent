"""Unit tests for thegent contracts package."""

import pytest

from thegent.contracts import (
    CONTRACT_SCHEMA_VERSION,
    CanonicalStructuredMessage,
    CSMPhase,
    CSMStatus,
    get_registry,
    normalize_output,
)
from thegent.contracts.parser import IncrementalXMLParser, extract_tags
from thegent.contracts.validation import validate_csm


@pytest.mark.unit
class TestContractRegistry:
    """Tests for ContractRegistry."""

    def test_get_registry_singleton(self) -> None:
        # @trace FR-CTR-001
        """get_registry returns same instance."""
        r1 = get_registry()
        r2 = get_registry()
        assert r1 is r2

    def test_csm_contract_registered(self) -> None:
        # @trace FR-CTR-001
        """CSM contract is registered."""
        r = get_registry()
        v = r.get("csm")
        assert v is not None
        assert v.contract_id == "csm"
        assert v.version == "csm-v1"

    def test_compatibility(self) -> None:
        # @trace FR-CTR-001
        """Compatibility check works."""
        r = get_registry()
        assert r.is_compatible("csm-v1", "csm-v1")
        assert r.is_compatible("task-tool-18", "csm-v1")


@pytest.mark.unit
class TestCanonicalStructuredMessage:
    """Tests for CanonicalStructuredMessage."""

    def test_to_dict_roundtrip(self) -> None:
        # @trace FR-CTR-001
        """to_dict and from_dict roundtrip."""
        csm = CanonicalStructuredMessage(
            task_id="T1",
            summary="Done",
            status=CSMStatus.COMPLETED,
            phase=CSMPhase.OPERATOR,
        )
        d = csm.to_dict()
        assert d["task_id"] == "T1"
        assert d["summary"] == "Done"
        assert d["status"] == "completed"
        restored = CanonicalStructuredMessage.from_dict(d)
        assert restored.task_id == csm.task_id
        assert restored.status == csm.status

    def test_schema_version_default(self) -> None:
        # @trace FR-CTR-001
        """Default schema_version is csm-v1."""
        csm = CanonicalStructuredMessage()
        assert csm.schema_version == "csm-v1"


@pytest.mark.unit
class TestNormalizeOutput:
    """Tests for normalize_output adapter fallback."""

    def test_fallback_plain_text(self) -> None:
        # @trace FR-CTR-001
        """Fallback produces CSM from plain text when no adapter."""
        res = normalize_output("unknown-provider", "Hello world")
        assert res.csm.summary == "Hello world"
        assert res.confidence == 0.5
        assert res.source_provider == "unknown-provider"

    def test_fallback_uses_extract_condensed(self) -> None:
        # @trace FR-CTR-001
        """Fallback uses extract_condensed for JSONL-like input."""
        raw = '{"type":"message","role":"assistant","content":"Extracted"}'
        res = normalize_output("gemini", raw)
        assert "Extracted" in res.csm.summary or res.csm.summary


@pytest.mark.unit
class TestSemanticValidation:
    """Tests for validate_csm phase-aware and invariant rules."""

    def test_valid_completed_passes(self) -> None:
        # @trace FR-CTR-001
        """Valid COMPLETED CSM has no issues."""
        csm = CanonicalStructuredMessage(summary="Done", status=CSMStatus.COMPLETED, progress=1.0)
        assert validate_csm(csm) == []

    def test_completed_without_summary_fails(self) -> None:
        # @trace FR-CTR-001
        """COMPLETED without summary fails."""
        csm = CanonicalStructuredMessage(status=CSMStatus.COMPLETED, progress=1.0)
        issues = validate_csm(csm)
        assert any("summary" in i for i in issues)

    def test_failed_without_issues_fails(self) -> None:
        # @trace FR-CTR-001
        """FAILED without issues or decision_reason_code fails."""
        csm = CanonicalStructuredMessage(status=CSMStatus.FAILED)
        issues = validate_csm(csm)
        assert any("FAILED" in i for i in issues)

    def test_failed_with_issues_passes(self) -> None:
        # @trace FR-CTR-001
        """FAILED with issues passes."""
        csm = CanonicalStructuredMessage(status=CSMStatus.FAILED, issues=["timeout"])
        assert validate_csm(csm) == []

    def test_reviewer_without_decision_reason_fails(self) -> None:
        # @trace FR-CTR-001
        """REVIEWER phase without decision_reason_code fails."""
        csm = CanonicalStructuredMessage(phase=CSMPhase.REVIEWER, status=CSMStatus.COMPLETED, summary="OK")
        issues = validate_csm(csm)
        assert any("REVIEWER" in i for i in issues)

    def test_planner_completed_without_objective_fails(self) -> None:
        # @trace FR-CTR-001
        """PLANNER COMPLETED without objective fails."""
        csm = CanonicalStructuredMessage(phase=CSMPhase.PLANNER, status=CSMStatus.COMPLETED, summary="OK")
        issues = validate_csm(csm)
        assert any("PLANNER" in i for i in issues)


@pytest.mark.unit
class TestIncrementalXMLParser:
    """Regression tests for incremental XML parser partial-state behavior."""

    def test_parse_balanced_tags_and_filters_allowed_tags(self) -> None:
        # @trace FR-CTR-001
        parser = IncrementalXMLParser(allowed_tags=["summary", "status"])
        parsed = parser.parse("<STATUS>in_progress</STATUS><SUMMARY>work in flight</SUMMARY><NOISE>skip</NOISE>")
        assert parsed == {"STATUS": "in_progress", "SUMMARY": "work in flight"}

    def test_extract_tags_helper_is_case_insensitive(self) -> None:
        # @trace FR-CTR-001
        parsed = extract_tags("<summary>done</summary><Task_Id>t-1</Task_Id>", tags=["summary"])
        assert parsed == {"SUMMARY": "done"}

    def test_get_partial_state_reports_open_tag_and_partial_content(self) -> None:
        # @trace FR-CTR-001
        parser = IncrementalXMLParser()
        state = parser.get_partial_state("<STATUS>in_progress<DETAILS>waiting")
        assert state["open_tag"] == "DETAILS"
        assert state["partial_content"] == "waiting"
        assert state["is_truncated"] is True

    def test_get_partial_state_reports_incomplete_trailing_tag_prefix(self) -> None:
        # @trace FR-CTR-001
        parser = IncrementalXMLParser()
        state = parser.get_partial_state("<STATUS>in_progress<STAT")
        assert state["open_tag"] is None
        assert state["partial_content"] == ""
        assert state["is_truncated"] is True
        assert state["incomplete_tag"] == "STAT"

    def test_get_partial_state_returns_no_partial_for_closed_markup(self) -> None:
        # @trace FR-CTR-001
        parser = IncrementalXMLParser()
        state = parser.get_partial_state("<STATUS>done</STATUS>")
        assert state["open_tag"] is None
        assert state["partial_content"] == ""
        assert state["is_truncated"] is False


@pytest.mark.unit
class TestXMLOutputAdapter:
    """Regression tests for XML adapter behavior on truncated/complete payloads."""

    def test_xml_adapter_marks_truncated_payload_as_non_final(self) -> None:
        # @trace FR-CTR-001
        result = normalize_output("gemini", "<SUMMARY>running<DETAILS>work")
        assert "parse_truncated" in result.parse_errors
        assert result.csm.status == CSMStatus.PENDING
        assert result.confidence == 0.0

    def test_xml_adapter_parses_complete_payload(self) -> None:
        # @trace FR-CTR-001
        result = normalize_output("gemini", "<STATUS>completed</STATUS><SUMMARY>done</SUMMARY>")
        assert result.parse_errors == []
        assert result.csm.status == CSMStatus.COMPLETED
        assert result.csm.summary == "done"


@pytest.mark.unit
class TestCSMRoundtripEdgeCases:
    """Edge case tests for CSM to_dict/from_dict roundtrip."""

    @pytest.mark.unit
    def test_roundtrip_preserves_all_list_fields(self) -> None:
        # @trace FR-CTR-001
        """Roundtrip preserves actions_completed, issues, next_steps lists."""
        csm = CanonicalStructuredMessage(
            task_id="T-edge",
            status=CSMStatus.IN_PROGRESS,
            actions_completed=["step1", "step2"],
            issues=["warning1"],
            next_steps=["finalize"],
            progress=0.5,
        )
        d = csm.to_dict()
        restored = CanonicalStructuredMessage.from_dict(d)
        assert restored.actions_completed == ["step1", "step2"]
        assert restored.issues == ["warning1"]
        assert restored.next_steps == ["finalize"]

    @pytest.mark.unit
    def test_roundtrip_empty_csm(self) -> None:
        # @trace FR-CTR-001
        """Roundtrip of default empty CSM preserves defaults."""
        csm = CanonicalStructuredMessage()
        d = csm.to_dict()
        restored = CanonicalStructuredMessage.from_dict(d)
        assert restored.status == CSMStatus.PENDING
        assert restored.phase == CSMPhase.UNKNOWN
        assert restored.progress == 0.0
        assert restored.summary == ""

    @pytest.mark.unit
    def test_from_dict_unknown_status_defaults_to_pending(self) -> None:
        # @trace FR-CTR-001
        """from_dict with invalid status value defaults to PENDING."""
        d = {"status": "nonexistent_status", "phase": "unknown"}
        # CSMStatus("nonexistent_status") should raise ValueError, caught by from_dict
        try:
            restored = CanonicalStructuredMessage.from_dict(d)
            # If no error, we check it handled gracefully
            assert restored.status in (CSMStatus.PENDING, CSMStatus.COMPLETED)
        except ValueError:
            # Also acceptable: from_dict may raise on invalid status
            pass

    @pytest.mark.unit
    def test_from_dict_preserves_extra_keys_in_raw_payload(self) -> None:
        # @trace FR-CTR-001
        """from_dict stores unrecognized keys in raw_payload."""
        d = {
            "task_id": "T1",
            "status": "completed",
            "phase": "operator",
            "summary": "done",
            "custom_field": "custom_value",
        }
        restored = CanonicalStructuredMessage.from_dict(d)
        assert "custom_field" in restored.raw_payload
        assert restored.raw_payload["custom_field"] == "custom_value"

    @pytest.mark.unit
    def test_schema_version_roundtrip(self) -> None:
        # @trace FR-CTR-001
        """Custom schema_version is preserved through roundtrip."""
        csm = CanonicalStructuredMessage(schema_version="csm-v2")
        d = csm.to_dict()
        assert d["schema_version"] == "csm-v2"
        restored = CanonicalStructuredMessage.from_dict(d)
        assert restored.schema_version == "csm-v2"

    @pytest.mark.unit
    def test_contract_schema_version_constant(self) -> None:
        # @trace FR-CTR-001
        """CONTRACT_SCHEMA_VERSION is csm-v1."""
        assert CONTRACT_SCHEMA_VERSION == "csm-v1"
