"""Tests for WL-269: Conflict Triage Categories.

Verifies that conflicts can be triaged by field name into categories
(AUTO_RESOLVE, MANUAL_REVIEW, ESCALATE) for governance workflows.

# @trace WL-269
"""

from __future__ import annotations

import pytest

from thegent.integrations.conflict_triage import (
    ConflictTriageEngine,
    ConflictTriageRule,
    TriageCategory,
)


@pytest.mark.requirement("WL-269")
class TestConflictTriageEngine:
    """WL-269: Conflict triage categories and routing for governance."""

    def test_add_and_triage_auto_resolve(self):
        """# @trace WL-269 — add AUTO_RESOLVE rule and triage field."""
        engine = ConflictTriageEngine()

        rule = engine.add_rule("timestamp", TriageCategory.AUTO_RESOLVE)

        assert rule.field_name == "timestamp"
        assert rule.category == TriageCategory.AUTO_RESOLVE

        result = engine.triage("timestamp")
        assert result == TriageCategory.AUTO_RESOLVE

    def test_add_and_triage_manual_review(self):
        """# @trace WL-269 — add MANUAL_REVIEW rule and triage field."""
        engine = ConflictTriageEngine()

        engine.add_rule("description", TriageCategory.MANUAL_REVIEW)
        result = engine.triage("description")

        assert result == TriageCategory.MANUAL_REVIEW

    def test_add_and_triage_escalate(self):
        """# @trace WL-269 — add ESCALATE rule and triage field."""
        engine = ConflictTriageEngine()

        engine.add_rule("access_level", TriageCategory.ESCALATE)
        result = engine.triage("access_level")

        assert result == TriageCategory.ESCALATE

    def test_triage_missing_field_defaults_to_manual_review(self):
        """# @trace WL-269 — triaging field without rule defaults to MANUAL_REVIEW."""
        engine = ConflictTriageEngine()

        result = engine.triage("unknown_field")

        assert result == TriageCategory.MANUAL_REVIEW

    def test_triage_all_with_mixed_rules(self):
        """# @trace WL-269 — triage_all() returns category for each field."""
        engine = ConflictTriageEngine()
        engine.add_rule("timestamp", TriageCategory.AUTO_RESOLVE)
        engine.add_rule("description", TriageCategory.MANUAL_REVIEW)
        engine.add_rule("access_level", TriageCategory.ESCALATE)

        result = engine.triage_all(["timestamp", "description", "access_level"])

        assert result["timestamp"] == TriageCategory.AUTO_RESOLVE
        assert result["description"] == TriageCategory.MANUAL_REVIEW
        assert result["access_level"] == TriageCategory.ESCALATE

    def test_triage_all_with_missing_fields(self):
        """# @trace WL-269 — triage_all() defaults missing fields to MANUAL_REVIEW."""
        engine = ConflictTriageEngine()
        engine.add_rule("timestamp", TriageCategory.AUTO_RESOLVE)

        result = engine.triage_all(["timestamp", "unknown_field", "another_field"])

        assert result["timestamp"] == TriageCategory.AUTO_RESOLVE
        assert result["unknown_field"] == TriageCategory.MANUAL_REVIEW
        assert result["another_field"] == TriageCategory.MANUAL_REVIEW

    def test_triage_all_empty_list(self):
        """# @trace WL-269 — triage_all() with empty list returns empty dict."""
        engine = ConflictTriageEngine()

        result = engine.triage_all([])

        assert result == {}

    def test_overwriting_existing_rule(self):
        """# @trace WL-269 — adding rule with same field overwrites previous."""
        engine = ConflictTriageEngine()
        engine.add_rule("email", TriageCategory.AUTO_RESOLVE)
        engine.add_rule("email", TriageCategory.MANUAL_REVIEW)

        result = engine.triage("email")

        assert result == TriageCategory.MANUAL_REVIEW

    def test_multiple_independent_rules(self):
        """# @trace WL-269 — multiple rules are stored independently."""
        engine = ConflictTriageEngine()
        engine.add_rule("field1", TriageCategory.AUTO_RESOLVE)
        engine.add_rule("field2", TriageCategory.MANUAL_REVIEW)
        engine.add_rule("field3", TriageCategory.ESCALATE)

        assert engine.triage("field1") == TriageCategory.AUTO_RESOLVE
        assert engine.triage("field2") == TriageCategory.MANUAL_REVIEW
        assert engine.triage("field3") == TriageCategory.ESCALATE

    def test_triage_category_enum_values(self):
        """# @trace WL-269 — TriageCategory enum has correct string values."""
        assert TriageCategory.AUTO_RESOLVE.value == "auto_resolve"
        assert TriageCategory.MANUAL_REVIEW.value == "manual_review"
        assert TriageCategory.ESCALATE.value == "escalate"

    def test_conflict_triage_rule_dataclass(self):
        """# @trace WL-269 — ConflictTriageRule is properly structured."""
        rule = ConflictTriageRule(
            field_name="test_field", category=TriageCategory.AUTO_RESOLVE
        )

        assert rule.field_name == "test_field"
        assert rule.category == TriageCategory.AUTO_RESOLVE

    def test_triage_with_special_field_names(self):
        """# @trace WL-269 — triage handles special field names."""
        engine = ConflictTriageEngine()
        special_names = [
            "field-with-dash",
            "field_with_underscore",
            "field.with.dot",
            "field123",
            "UPPERCASE_FIELD",
        ]

        for name in special_names:
            engine.add_rule(name, TriageCategory.AUTO_RESOLVE)

        for name in special_names:
            assert engine.triage(name) == TriageCategory.AUTO_RESOLVE

    def test_triage_all_preserves_order(self):
        """# @trace WL-269 — triage_all() returns all requested fields."""
        engine = ConflictTriageEngine()
        fields = ["field1", "field2", "field3", "field4"]

        result = engine.triage_all(fields)

        assert set(result.keys()) == set(fields)

    def test_add_rule_returns_rule_object(self):
        """# @trace WL-269 — add_rule() returns ConflictTriageRule object."""
        engine = ConflictTriageEngine()

        rule = engine.add_rule("test_field", TriageCategory.ESCALATE)

        assert isinstance(rule, ConflictTriageRule)
        assert rule.field_name == "test_field"
        assert rule.category == TriageCategory.ESCALATE
