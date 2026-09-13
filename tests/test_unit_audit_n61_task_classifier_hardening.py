"""Hardening invariants for ``governance.task_classifier`` — AUDIT-N+61.

FR-GOV-TC-001 .. FR-GOV-TC-015
"""

from __future__ import annotations

from dataclasses import fields as dc_fields
from pathlib import Path

import pytest

from thegent.governance.task_classifier import (
    SchemaSpec,
    TaskClassification,
    TaskClassifierError,
    TaskMetadata,
    _coerce_int_range,
    _normalize_validation_depth,
    _parse_rule_condition,
    _require,
    validate_classification_payload,
)

# ---------------------------------------------------------------------------
# FR-GOV-TC-001
# ---------------------------------------------------------------------------


class TestFRGOVTC001TaskClassifierErrorSubclass:
    def test_is_valueerror_subclass(self) -> None:
        assert issubclass(TaskClassifierError, ValueError)


# ---------------------------------------------------------------------------
# FR-GOV-TC-002
# ---------------------------------------------------------------------------


class TestFRGOVTC002TaskMetadataFrozenDataclass:
    def test_frozen(self) -> None:
        tm = TaskMetadata(
            task_id="t1",
            title="title",
            domain="backend",
            scale="M",
            risk="low",
            coupling="none",
            runtime_profile="default",
            validation_depth=["unit"],
            overlap_risk=1,
        )
        with pytest.raises(AttributeError):
            tm.task_id = "changed"  # type: ignore[misc]

    def test_all_fields_set(self) -> None:
        expected = {
            "task_id",
            "title",
            "domain",
            "scale",
            "risk",
            "coupling",
            "runtime_profile",
            "validation_depth",
            "overlap_risk",
        }
        actual = {f.name for f in dc_fields(TaskMetadata)}
        assert actual == expected


# ---------------------------------------------------------------------------
# FR-GOV-TC-003
# ---------------------------------------------------------------------------


class TestFRGOVTC003TaskClassificationAsPayload:
    def test_payload_keys(self) -> None:
        tc = TaskClassification(
            delegation_tier="L2_managed",
            worker_count=4,
            worktree_mode="shared_lane",
            commit_mode="micro",
            required_gates=["lint", "unit"],
        )
        payload = tc.as_payload()
        assert set(payload.keys()) == {
            "delegation_tier",
            "worker_count",
            "worktree_mode",
            "commit_mode",
            "required_gates",
        }


# ---------------------------------------------------------------------------
# FR-GOV-TC-004
# ---------------------------------------------------------------------------


class TestFRGOVTC004SchemaSpecFields:
    def test_has_all_five_fields(self) -> None:
        expected = {
            "payload",
            "fields",
            "outputs",
            "policy_defaults",
            "escalation_rules",
        }
        actual = {f.name for f in dc_fields(SchemaSpec)}
        assert actual == expected


# ---------------------------------------------------------------------------
# FR-GOV-TC-005
# ---------------------------------------------------------------------------


class TestFRGOVTC005LoadSchemaNonexistentPath:
    def test_raises(self) -> None:
        from thegent.governance.task_classifier import load_schema

        with pytest.raises(TaskClassifierError):
            load_schema(schema_path=Path("/nonexistent/schema.yaml"))


# ---------------------------------------------------------------------------
# FR-GOV-TC-006
# ---------------------------------------------------------------------------


class TestFRGOVTC006RequireRaisesForNone:
    def test_none_raises(self) -> None:
        with pytest.raises(TaskClassifierError, match="missing required schema field"):
            _require(None, name="test_field")

    def test_non_none_passes(self) -> None:
        assert _require("ok", name="test_field") == "ok"


# ---------------------------------------------------------------------------
# FR-GOV-TC-007
# ---------------------------------------------------------------------------


class TestFRGOVTC007CoerceIntRangeRejectsNonList:
    def test_string_rejected(self) -> None:
        with pytest.raises(TaskClassifierError, match="two-value list"):
            _coerce_int_range("not a list")

    def test_int_rejected(self) -> None:
        with pytest.raises(TaskClassifierError, match="two-value list"):
            _coerce_int_range(42)

    def test_none_rejected(self) -> None:
        with pytest.raises(TaskClassifierError, match="two-value list"):
            _coerce_int_range(None)


# ---------------------------------------------------------------------------
# FR-GOV-TC-008
# ---------------------------------------------------------------------------


class TestFRGOVTC008CoerceIntRangeRejectsNon2ElementList:
    def test_one_element(self) -> None:
        with pytest.raises(TaskClassifierError, match="two-value list"):
            _coerce_int_range([1])

    def test_three_elements(self) -> None:
        with pytest.raises(TaskClassifierError, match="two-value list"):
            _coerce_int_range([1, 2, 3])

    def test_empty_list(self) -> None:
        with pytest.raises(TaskClassifierError, match="two-value list"):
            _coerce_int_range([])

    def test_valid_two_element(self) -> None:
        assert _coerce_int_range([1, 10]) == (1, 10)


# ---------------------------------------------------------------------------
# FR-GOV-TC-009
# ---------------------------------------------------------------------------


class TestFRGOVTC009NormalizeValidationDepthRejectsNonList:
    def test_string_rejected(self) -> None:
        with pytest.raises(TaskClassifierError, match="must be a list"):
            _normalize_validation_depth("not a list")

    def test_int_rejected(self) -> None:
        with pytest.raises(TaskClassifierError, match="must be a list"):
            _normalize_validation_depth(42)


# ---------------------------------------------------------------------------
# FR-GOV-TC-010
# ---------------------------------------------------------------------------


class TestFRGOVTC010NormalizeValidationDepthRejectsEmptyList:
    def test_empty_list(self) -> None:
        with pytest.raises(TaskClassifierError, match="at least one value"):
            _normalize_validation_depth([])


# ---------------------------------------------------------------------------
# FR-GOV-TC-011
# ---------------------------------------------------------------------------


class TestFRGOVTC011ValidateClassificationPayloadRejectsNonDict:
    def _schema(self) -> SchemaSpec:
        return SchemaSpec(
            payload={},
            fields={"task_id": {"type": "string", "required": True}},
            outputs={},
            policy_defaults={},
            escalation_rules=[],
        )

    def test_string_rejected(self) -> None:
        with pytest.raises(TaskClassifierError, match="payload must be a mapping"):
            validate_classification_payload("not a dict", self._schema())  # type: ignore[arg-type]

    def test_list_rejected(self) -> None:
        with pytest.raises(TaskClassifierError, match="payload must be a mapping"):
            validate_classification_payload([], self._schema())  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# FR-GOV-TC-012
# ---------------------------------------------------------------------------


class TestFRGOVTC012ValidateClassificationPayloadRejectsMissingRequired:
    def test_missing_required_field(self) -> None:
        schema = SchemaSpec(
            payload={},
            fields={"task_id": {"type": "string", "required": True}},
            outputs={},
            policy_defaults={},
            escalation_rules=[],
        )
        with pytest.raises(TaskClassifierError, match="missing required payload field"):
            validate_classification_payload({}, schema)


# ---------------------------------------------------------------------------
# FR-GOV-TC-013
# ---------------------------------------------------------------------------


class TestFRGOVTC013ParseRuleConditionInOperator:
    def test_in_operator(self) -> None:
        field, op, values = _parse_rule_condition("risk in [high, critical]")
        assert field == "risk"
        assert op == "in"
        assert values == ["high", "critical"]

    def test_in_operator_single_value(self) -> None:
        field, op, values = _parse_rule_condition("risk in [high]")
        assert field == "risk"
        assert op == "in"
        assert values == ["high"]


# ---------------------------------------------------------------------------
# FR-GOV-TC-014
# ---------------------------------------------------------------------------


class TestFRGOVTC014ParseRuleConditionComparisonOperators:
    def test_numeric_ge(self) -> None:
        field, op, rhs = _parse_rule_condition("overlap_risk >= 5")
        assert field == "overlap_risk"
        assert op == ">="
        assert rhs == 5

    def test_numeric_eq(self) -> None:
        field, op, rhs = _parse_rule_condition("overlap_risk == 3")
        assert field == "overlap_risk"
        assert op == "=="
        assert rhs == 3

    def test_string_eq(self) -> None:
        field, op, rhs = _parse_rule_condition('scale == "XL"')
        assert field == "scale"
        assert op == "=="
        assert rhs == "XL"

    def test_string_ne(self) -> None:
        field, op, rhs = _parse_rule_condition("coupling != none")
        assert field == "coupling"
        assert op == "!="
        assert rhs == "none"


# ---------------------------------------------------------------------------
# FR-GOV-TC-015
# ---------------------------------------------------------------------------


class TestFRGOVTC015AllExports:
    def test_all_exports(self) -> None:
        from thegent.governance import task_classifier as mod

        expected = [
            "_SCHEMA_PATH",
            "SchemaSpec",
            "TaskClassification",
            "TaskClassifierError",
            "TaskMetadata",
            "classify",
            "load_schema",
            "validate_classification_payload",
        ]
        assert list(mod.__all__) == expected
