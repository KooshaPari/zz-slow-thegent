"""Tests for WL-315: Governance Sign-Off Template."""

from __future__ import annotations

from pathlib import Path

import pytest

from thegent.integrations.signoff_template import get_template_path, render_template


class TestGetTemplatePath:
    """Tests for get_template_path function."""

    @pytest.mark.requirement("WL-315")
    def test_returns_path(self) -> None:
        """Test get_template_path returns a Path object."""
        path = get_template_path()
        assert isinstance(path, Path)

    @pytest.mark.requirement("WL-315")
    def test_path_ends_with_template_name(self) -> None:
        """Test returned path ends with AUTOSYNC_SIGNOFF_TEMPLATE.md."""
        path = get_template_path()
        assert path.name == "AUTOSYNC_SIGNOFF_TEMPLATE.md"

    @pytest.mark.requirement("WL-315")
    def test_path_in_governance_directory(self) -> None:
        """Test returned path is in docs/governance directory."""
        path = get_template_path()
        assert "governance" in path.parts
        assert "docs" in path.parts

    @pytest.mark.requirement("WL-315")
    def test_template_file_exists(self) -> None:
        """Test the template file exists at the returned path."""
        path = get_template_path()
        assert path.exists(), f"Template not found at {path}"

    @pytest.mark.requirement("WL-315")
    def test_template_is_file(self) -> None:
        """Test the template path is a file, not a directory."""
        path = get_template_path()
        assert path.is_file()


class TestRenderTemplate:
    """Tests for render_template function."""

    @pytest.mark.requirement("WL-315")
    def test_render_basic(self) -> None:
        """Test rendering with basic inputs."""
        result = render_template(
            date="2026-02-22",
            reviewer="agent-alice",
            environment="staging",
            connectors=["jira", "linear"],
        )
        assert isinstance(result, str)
        assert "2026-02-22" in result
        assert "agent-alice" in result
        assert "staging" in result
        assert "jira" in result
        assert "linear" in result

    @pytest.mark.requirement("WL-315")
    def test_render_preserves_template_structure(self) -> None:
        """Test render preserves markdown structure."""
        result = render_template(
            date="2026-02-22",
            reviewer="test-reviewer",
            environment="production",
            connectors=["test"],
        )
        assert "# Autosync Production Enablement Sign-Off" in result
        assert "## Summary" in result
        assert "## Pre-Enablement Checklist" in result
        assert "## Validation Evidence" in result
        assert "## Approval" in result
        assert "## Rollback Plan" in result

    @pytest.mark.requirement("WL-315")
    def test_render_date_substitution(self) -> None:
        """Test date is substituted in Summary."""
        date = "2026-02-22"
        result = render_template(
            date=date, reviewer="reviewer", environment="staging", connectors=[]
        )
        assert date in result
        # Check it appears in Summary section context
        assert "| Date | 2026-02-22 |" in result

    @pytest.mark.requirement("WL-315")
    def test_render_reviewer_substitution(self) -> None:
        """Test reviewer is substituted in Summary."""
        reviewer = "human-bob"
        result = render_template(
            date="2026-02-22", reviewer=reviewer, environment="staging", connectors=[]
        )
        assert reviewer in result
        assert f"| Reviewer | {reviewer} |" in result

    @pytest.mark.requirement("WL-315")
    def test_render_environment_substitution(self) -> None:
        """Test environment is substituted in Summary."""
        result = render_template(
            date="2026-02-22",
            reviewer="reviewer",
            environment="production",
            connectors=[],
        )
        assert "| Environment | production |" in result

    @pytest.mark.requirement("WL-315")
    def test_render_single_connector(self) -> None:
        """Test rendering with single connector."""
        result = render_template(
            date="2026-02-22",
            reviewer="reviewer",
            environment="staging",
            connectors=["jira"],
        )
        assert "| Connector(s) | jira |" in result

    @pytest.mark.requirement("WL-315")
    def test_render_multiple_connectors(self) -> None:
        """Test rendering with multiple connectors."""
        result = render_template(
            date="2026-02-22",
            reviewer="reviewer",
            environment="production",
            connectors=["jira", "linear", "asana"],
        )
        assert "jira, linear, asana" in result

    @pytest.mark.requirement("WL-315")
    def test_render_empty_connectors_list(self) -> None:
        """Test rendering with empty connector list."""
        result = render_template(
            date="2026-02-22",
            reviewer="reviewer",
            environment="staging",
            connectors=[],
        )
        assert "| Connector(s) |" in result

    @pytest.mark.requirement("WL-315")
    def test_render_contains_checkboxes(self) -> None:
        """Test rendered template contains checklist checkboxes."""
        result = render_template(
            date="2026-02-22", reviewer="reviewer", environment="staging", connectors=[]
        )
        # Count occurrences of checklist items
        checkbox_count = result.count("- [ ]")
        assert checkbox_count >= 8, (
            f"Expected at least 8 checkboxes, found {checkbox_count}"
        )

    @pytest.mark.requirement("WL-315")
    def test_render_contains_validation_table(self) -> None:
        """Test rendered template contains validation evidence table."""
        result = render_template(
            date="2026-02-22", reviewer="reviewer", environment="staging", connectors=[]
        )
        assert "Validation Evidence" in result
        assert "PASS/FAIL" in result
        assert "Auth scope verification" in result

    @pytest.mark.requirement("WL-315")
    def test_render_contains_rollback_section(self) -> None:
        """Test rendered template contains rollback plan."""
        result = render_template(
            date="2026-02-22", reviewer="reviewer", environment="staging", connectors=[]
        )
        assert "Rollback Plan" in result
        assert "thegent autosync disable" in result
        assert "thegent autosync rollback" in result
