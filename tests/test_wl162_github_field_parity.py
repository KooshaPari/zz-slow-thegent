"""Tests for WL-162: GitHub Field Update Parity.

Verifies that FieldParityReport is created correctly,
GitHubFieldParityChecker checks individual and multiple fields,
and identifies out-of-parity fields.

# @trace WL-162
"""

from __future__ import annotations

import pytest

from thegent.integrations.github_field_parity import (
    FieldParityReport,
    GitHubFieldParityChecker,
)


class TestFieldParityReport:
    """WL-162: FieldParityReport dataclass."""

    @pytest.mark.requirement("WL-162")
    def test_report_creation_in_parity(self):
        """FieldParityReport with matching values has in_parity=True."""
        report = FieldParityReport(
            field_name="title", github_value="Foo", local_value="Foo", in_parity=True
        )

        assert report.field_name == "title"
        assert report.github_value == "Foo"
        assert report.local_value == "Foo"
        assert report.in_parity is True

    @pytest.mark.requirement("WL-162")
    def test_report_creation_out_of_parity(self):
        """FieldParityReport with mismatched values has in_parity=False."""
        report = FieldParityReport(
            field_name="status",
            github_value="open",
            local_value="closed",
            in_parity=False,
        )

        assert report.field_name == "status"
        assert report.github_value == "open"
        assert report.local_value == "closed"
        assert report.in_parity is False


class TestGitHubFieldParityChecker:
    """WL-162: GitHubFieldParityChecker operations."""

    @pytest.mark.requirement("WL-162")
    def test_check_matching_values(self):
        """check() returns in_parity=True when values match."""
        checker = GitHubFieldParityChecker()

        report = checker.check("title", "same", "same")

        assert report.field_name == "title"
        assert report.github_value == "same"
        assert report.local_value == "same"
        assert report.in_parity is True

    @pytest.mark.requirement("WL-162")
    def test_check_mismatched_values(self):
        """check() returns in_parity=False when values differ."""
        checker = GitHubFieldParityChecker()

        report = checker.check("status", "open", "closed")

        assert report.field_name == "status"
        assert report.github_value == "open"
        assert report.local_value == "closed"
        assert report.in_parity is False

    @pytest.mark.requirement("WL-162")
    def test_check_none_values_matching(self):
        """check() treats None == None as in parity."""
        checker = GitHubFieldParityChecker()

        report = checker.check("optional", None, None)

        assert report.in_parity is True

    @pytest.mark.requirement("WL-162")
    def test_check_none_vs_value_mismatch(self):
        """check() treats None vs value as out of parity."""
        checker = GitHubFieldParityChecker()

        report = checker.check("required", None, "value")

        assert report.in_parity is False

    @pytest.mark.requirement("WL-162")
    def test_check_all_single_field(self):
        """check_all() returns list with single report."""
        checker = GitHubFieldParityChecker()

        reports = checker.check_all({"title": ("match", "match")})

        assert len(reports) == 1
        assert reports[0].field_name == "title"
        assert reports[0].in_parity is True

    @pytest.mark.requirement("WL-162")
    def test_check_all_multiple_fields(self):
        """check_all() processes all fields in the dict."""
        checker = GitHubFieldParityChecker()

        reports = checker.check_all(
            {
                "title": ("Foo", "Foo"),
                "status": ("open", "closed"),
                "labels": (None, None),
            }
        )

        assert len(reports) == 3

        title_report = next(r for r in reports if r.field_name == "title")
        assert title_report.in_parity is True

        status_report = next(r for r in reports if r.field_name == "status")
        assert status_report.in_parity is False

        labels_report = next(r for r in reports if r.field_name == "labels")
        assert labels_report.in_parity is True

    @pytest.mark.requirement("WL-162")
    def test_out_of_parity_empty_list(self):
        """out_of_parity() returns empty list when all in parity."""
        checker = GitHubFieldParityChecker()
        reports = checker.check_all({"field1": ("val", "val"), "field2": ("x", "x")})

        out_of_sync = checker.out_of_parity(reports)

        assert len(out_of_sync) == 0

    @pytest.mark.requirement("WL-162")
    def test_out_of_parity_filters_correctly(self):
        """out_of_parity() returns only out-of-parity reports."""
        checker = GitHubFieldParityChecker()
        reports = checker.check_all(
            {
                "field1": ("match", "match"),
                "field2": ("gh-val", "local-val"),
                "field3": ("same", "same"),
                "field4": ("diff1", "diff2"),
            }
        )

        out_of_sync = checker.out_of_parity(reports)

        assert len(out_of_sync) == 2
        assert all(not r.in_parity for r in out_of_sync)
        field_names = {r.field_name for r in out_of_sync}
        assert field_names == {"field2", "field4"}

    @pytest.mark.requirement("WL-162")
    def test_out_of_parity_preserves_details(self):
        """out_of_parity() preserves field details in filtered reports."""
        checker = GitHubFieldParityChecker()
        reports = checker.check_all({"status": ("open", "closed")})

        out_of_sync = checker.out_of_parity(reports)

        assert len(out_of_sync) == 1
        report = out_of_sync[0]
        assert report.field_name == "status"
        assert report.github_value == "open"
        assert report.local_value == "closed"
