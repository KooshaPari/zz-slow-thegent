"""Tests for WL-224: Workstream Schema Linter.

Verifies schema validation, field checking, and violation reporting.

# @trace WL-224
"""

from __future__ import annotations

import pytest


@pytest.mark.requirement("WL-224")
class TestWorkstreamSchemaLinter:
    """WL-224: Workstream schema linter for validation."""

    def test_lint_valid_record_returns_empty(self):
        """# @trace WL-224 — lint() returns empty list for valid record."""
        from thegent.integrations.workstream_schema_linter import WorkstreamSchemaLinter

        linter = WorkstreamSchemaLinter()
        record = {"id": "WL-001", "title": "Test", "status": "IN_PROGRESS"}
        violations = linter.lint(record)

        assert violations == []

    def test_lint_missing_id_field(self):
        """# @trace WL-224 — lint() detects missing 'id' field."""
        from thegent.integrations.workstream_schema_linter import WorkstreamSchemaLinter

        linter = WorkstreamSchemaLinter()
        record = {"title": "Test", "status": "IN_PROGRESS"}
        violations = linter.lint(record)

        assert len(violations) == 1
        assert violations[0].field == "id"
        assert "missing" in violations[0].message.lower()

    def test_lint_missing_title_field(self):
        """# @trace WL-224 — lint() detects missing 'title' field."""
        from thegent.integrations.workstream_schema_linter import WorkstreamSchemaLinter

        linter = WorkstreamSchemaLinter()
        record = {"id": "WL-001", "status": "IN_PROGRESS"}
        violations = linter.lint(record)

        assert len(violations) == 1
        assert violations[0].field == "title"

    def test_lint_missing_status_field(self):
        """# @trace WL-224 — lint() detects missing 'status' field."""
        from thegent.integrations.workstream_schema_linter import WorkstreamSchemaLinter

        linter = WorkstreamSchemaLinter()
        record = {"id": "WL-001", "title": "Test"}
        violations = linter.lint(record)

        assert len(violations) == 1
        assert violations[0].field == "status"

    def test_lint_multiple_missing_fields(self):
        """# @trace WL-224 — lint() reports all missing fields."""
        from thegent.integrations.workstream_schema_linter import WorkstreamSchemaLinter

        linter = WorkstreamSchemaLinter()
        record = {}
        violations = linter.lint(record)

        assert len(violations) == 3
        fields = {v.field for v in violations}
        assert fields == {"id", "title", "status"}

    def test_lint_empty_id_field(self):
        """# @trace WL-224 — lint() detects empty 'id' field."""
        from thegent.integrations.workstream_schema_linter import WorkstreamSchemaLinter

        linter = WorkstreamSchemaLinter()
        record = {"id": "", "title": "Test", "status": "IN_PROGRESS"}
        violations = linter.lint(record)

        assert len(violations) == 1
        assert violations[0].field == "id"
        assert "empty" in violations[0].message.lower()

    def test_lint_empty_title_field(self):
        """# @trace WL-224 — lint() detects empty 'title' field."""
        from thegent.integrations.workstream_schema_linter import WorkstreamSchemaLinter

        linter = WorkstreamSchemaLinter()
        record = {"id": "WL-001", "title": "", "status": "IN_PROGRESS"}
        violations = linter.lint(record)

        assert len(violations) == 1
        assert violations[0].field == "title"

    def test_lint_empty_status_field(self):
        """# @trace WL-224 — lint() detects empty 'status' field."""
        from thegent.integrations.workstream_schema_linter import WorkstreamSchemaLinter

        linter = WorkstreamSchemaLinter()
        record = {"id": "WL-001", "title": "Test", "status": ""}
        violations = linter.lint(record)

        assert len(violations) == 1
        assert violations[0].field == "status"

    def test_lint_multiple_empty_fields(self):
        """# @trace WL-224 — lint() reports all empty fields."""
        from thegent.integrations.workstream_schema_linter import WorkstreamSchemaLinter

        linter = WorkstreamSchemaLinter()
        record = {"id": "", "title": "", "status": ""}
        violations = linter.lint(record)

        assert len(violations) == 3

    def test_schema_violation_dataclass_structure(self):
        """# @trace WL-224 — SchemaViolation dataclass has required fields."""
        from thegent.integrations.workstream_schema_linter import SchemaViolation

        violation = SchemaViolation(field="id", message="Missing id")
        assert violation.field == "id"
        assert violation.message == "Missing id"
        assert violation.severity == "error"

    def test_schema_violation_custom_severity(self):
        """# @trace WL-224 — SchemaViolation supports custom severity."""
        from thegent.integrations.workstream_schema_linter import SchemaViolation

        violation = SchemaViolation(field="id", message="Missing id", severity="warning")
        assert violation.severity == "warning"

    def test_is_valid_returns_true_for_valid_record(self):
        """# @trace WL-224 — is_valid() returns True for valid record."""
        from thegent.integrations.workstream_schema_linter import WorkstreamSchemaLinter

        linter = WorkstreamSchemaLinter()
        record = {"id": "WL-001", "title": "Test", "status": "DONE"}
        assert linter.is_valid(record) is True

    def test_is_valid_returns_false_for_invalid_record(self):
        """# @trace WL-224 — is_valid() returns False for invalid record."""
        from thegent.integrations.workstream_schema_linter import WorkstreamSchemaLinter

        linter = WorkstreamSchemaLinter()
        record = {"id": "WL-001", "title": "Test"}
        assert linter.is_valid(record) is False

    def test_lint_many_returns_empty_for_all_valid(self):
        """# @trace WL-224 — lint_many() returns empty dict for all valid records."""
        from thegent.integrations.workstream_schema_linter import WorkstreamSchemaLinter

        linter = WorkstreamSchemaLinter()
        records = [
            {"id": "WL-001", "title": "Test1", "status": "PENDING"},
            {"id": "WL-002", "title": "Test2", "status": "IN_PROGRESS"},
        ]
        violations = linter.lint_many(records)

        assert violations == {}

    def test_lint_many_maps_violations_to_indices(self):
        """# @trace WL-224 — lint_many() maps violations to record indices."""
        from thegent.integrations.workstream_schema_linter import WorkstreamSchemaLinter

        linter = WorkstreamSchemaLinter()
        records = [
            {"id": "WL-001", "title": "Test1", "status": "PENDING"},
            {"id": "WL-002", "title": "Test2"},
            {"id": "", "title": "Test3", "status": "DONE"},
        ]
        violations = linter.lint_many(records)

        assert 1 in violations
        assert 2 in violations
        assert len(violations[1]) == 1
        assert violations[1][0].field == "status"

    def test_lint_many_empty_list(self):
        """# @trace WL-224 — lint_many() returns empty dict for empty list."""
        from thegent.integrations.workstream_schema_linter import WorkstreamSchemaLinter

        linter = WorkstreamSchemaLinter()
        violations = linter.lint_many([])

        assert violations == {}

    def test_lint_many_only_invalid_records(self):
        """# @trace WL-224 — lint_many() only includes invalid records."""
        from thegent.integrations.workstream_schema_linter import WorkstreamSchemaLinter

        linter = WorkstreamSchemaLinter()
        records = [
            {"title": "Test1"},
            {"id": "WL-002"},
            {},
        ]
        violations = linter.lint_many(records)

        assert len(violations) == 3
        assert 0 in violations
        assert 1 in violations
        assert 2 in violations

    def test_lint_with_extra_fields_is_valid(self):
        """# @trace WL-224 — lint() ignores extra fields not in schema."""
        from thegent.integrations.workstream_schema_linter import WorkstreamSchemaLinter

        linter = WorkstreamSchemaLinter()
        record = {
            "id": "WL-001",
            "title": "Test",
            "status": "DONE",
            "priority": "HIGH",
            "owner": "john",
        }
        violations = linter.lint(record)

        assert violations == []

    def test_violation_severity_defaults_to_error(self):
        """# @trace WL-224 — violations default severity to 'error'."""
        from thegent.integrations.workstream_schema_linter import WorkstreamSchemaLinter

        linter = WorkstreamSchemaLinter()
        record = {"title": "Test", "status": "DONE"}
        violations = linter.lint(record)

        assert all(v.severity == "error" for v in violations)
