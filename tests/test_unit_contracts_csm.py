"""Unit tests for thegent.contracts.csm -- CanonicalStructuredMessage, CSMStatus, CSMPhase."""

import pytest

from tests.conftest_factories import make_csm
from thegent.contracts.csm import CanonicalStructuredMessage, CSMPhase, CSMStatus


@pytest.mark.unit
class TestCSMStatus:
    """Tests for CSMStatus enum."""

    def test_all_values_are_strings(self) -> None:
        # @trace FR-CTR-001
        for member in CSMStatus:
            assert isinstance(member.value, str)

    def test_expected_members_exist(self) -> None:
        # @trace FR-CTR-001
        expected = {
            "PENDING",
            "IN_PROGRESS",
            "COMPLETED",
            "FAILED",
            "BLOCKED",
            "CANCELLED",
        }
        actual = {m.name for m in CSMStatus}
        assert expected == actual

    def test_str_enum_equality(self) -> None:
        # @trace FR-CTR-001
        assert CSMStatus.COMPLETED == "completed"
        assert CSMStatus.PENDING == "pending"


@pytest.mark.unit
class TestCSMPhase:
    """Tests for CSMPhase enum."""

    def test_expected_members_exist(self) -> None:
        # @trace FR-CTR-001
        expected = {"PLANNER", "OPERATOR", "REVIEWER", "UNKNOWN"}
        actual = {m.name for m in CSMPhase}
        assert expected == actual

    def test_str_enum_equality(self) -> None:
        # @trace FR-CTR-001
        assert CSMPhase.UNKNOWN == "unknown"


@pytest.mark.unit
class TestCanonicalStructuredMessageConstruction:
    """Tests for CanonicalStructuredMessage construction and defaults."""

    def test_defaults(self) -> None:
        # @trace FR-CTR-001
        csm = CanonicalStructuredMessage()
        assert csm.task_id == ""
        assert csm.run_id == ""
        assert csm.status == CSMStatus.PENDING
        assert csm.phase == CSMPhase.UNKNOWN
        assert csm.progress == 0.0
        assert csm.actions_completed == []
        assert csm.issues == []
        assert csm.next_steps == []
        assert csm.schema_version == "csm-v1"

    def test_factory_defaults(self) -> None:
        # @trace FR-CTR-001
        csm = make_csm()
        assert csm.task_id == "test-task"
        assert csm.run_id == "test-run"
        assert csm.status == CSMStatus.PENDING

    def test_factory_custom_status(self) -> None:
        # @trace FR-CTR-001
        csm = make_csm(status="COMPLETED", progress=1.0, summary="done")
        assert csm.status == CSMStatus.COMPLETED
        assert csm.progress == 1.0
        assert csm.summary == "done"

    def test_list_fields_are_independent(self) -> None:
        # @trace FR-CTR-001
        csm1 = CanonicalStructuredMessage()
        csm2 = CanonicalStructuredMessage()
        csm1.actions_completed.append("x")
        assert csm2.actions_completed == []


@pytest.mark.unit
class TestCanonicalStructuredMessageToDict:
    """Tests for to_dict() serialization."""

    def test_to_dict_status_is_string_value(self) -> None:
        # @trace FR-CTR-001
        csm = make_csm(status="COMPLETED", progress=1.0, summary="ok")
        d = csm.to_dict()
        assert d["status"] == "completed"
        assert d["phase"] == "unknown"

    def test_to_dict_includes_all_core_fields(self) -> None:
        # @trace FR-CTR-001
        csm = make_csm()
        d = csm.to_dict()
        expected_keys = {
            "task_id",
            "run_id",
            "chunk_id",
            "status",
            "phase",
            "progress",
            "objective",
            "summary",
            "actions_completed",
            "issues",
            "next_steps",
            "evidence_set_hash",
            "policy_gate_id",
            "decision_reason_code",
            "schema_version",
            "source_contract",
        }
        assert expected_keys.issubset(set(d.keys()))

    def test_to_dict_lists_preserved(self) -> None:
        # @trace FR-CTR-001
        csm = make_csm(
            status="COMPLETED",
            progress=1.0,
            summary="ok",
            actions_completed=["a", "b"],
            issues=["i1"],
        )
        d = csm.to_dict()
        assert d["actions_completed"] == ["a", "b"]
        assert d["issues"] == ["i1"]


@pytest.mark.unit
class TestCanonicalStructuredMessageFromDict:
    """Tests for from_dict() deserialization."""

    def test_roundtrip(self) -> None:
        # @trace FR-CTR-001
        original = make_csm(
            task_id="t1",
            run_id="r1",
            status="COMPLETED",
            progress=1.0,
            summary="round trip",
            objective="test objective",
        )
        d = original.to_dict()
        restored = CanonicalStructuredMessage.from_dict(d)
        assert restored.task_id == "t1"
        assert restored.status == CSMStatus.COMPLETED
        assert restored.summary == "round trip"
        assert restored.progress == 1.0
        assert restored.objective == "test objective"

    def test_from_dict_unknown_status_defaults(self) -> None:
        # @trace FR-CTR-001
        d = {"status": "pending", "phase": "unknown"}
        csm = CanonicalStructuredMessage.from_dict(d)
        assert csm.status == CSMStatus.PENDING

    def test_from_dict_missing_fields_use_defaults(self) -> None:
        # @trace FR-CTR-001
        csm = CanonicalStructuredMessage.from_dict({})
        assert csm.task_id == ""
        assert csm.status == CSMStatus.PENDING
        assert csm.progress == 0.0

    def test_from_dict_extra_fields_go_to_raw_payload(self) -> None:
        # @trace FR-CTR-001
        d = {"task_id": "t1", "custom_field": "custom_value"}
        csm = CanonicalStructuredMessage.from_dict(d)
        assert csm.raw_payload.get("custom_field") == "custom_value"

    def test_from_dict_invalid_status_defaults_to_pending(self) -> None:
        # @trace FR-CTR-001
        d = {"status": 12345}
        csm = CanonicalStructuredMessage.from_dict(d)
        assert csm.status == CSMStatus.PENDING

    def test_from_dict_invalid_phase_defaults_to_unknown(self) -> None:
        # @trace FR-CTR-001
        d = {"phase": 99}
        csm = CanonicalStructuredMessage.from_dict(d)
        assert csm.phase == CSMPhase.UNKNOWN
