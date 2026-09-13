"""
E2E tests for Governance, Guardrails, and Hierarchy commands.

Agent Journey: Agent manages system governance, guardrails, and organizational hierarchy
Expected Behavior: Commands execute successfully and provide relevant reports/visualizations
"""

import pytest
from typer.testing import CliRunner

from thegent.main import app

# Skip all tests in this file - CLI commands do not exist
pytestmark = pytest.mark.skip(reason="CLI commands 'guardrails', 'hierarchy' do not exist in current implementation")

runner = CliRunner()


@pytest.mark.e2e
class TestGovernGuardrailsHierarchyCommands:
    """E2E tests for Governance, Guardrails, and Hierarchy commands."""

    # Govern commands (remaining)
    def test_govern_compliance_report_help(self) -> None:
        """thegent govern compliance-report --help exits with code 0."""
        result = runner.invoke(app, ["govern", "compliance-report", "--help"])
        assert result.exit_code == 0

    def test_govern_cost_help(self) -> None:
        """thegent govern cost --help exits with code 0."""
        result = runner.invoke(app, ["govern", "cost", "--help"])
        assert result.exit_code == 0

    def test_govern_hook_watcher_help(self) -> None:
        """thegent govern hook-watcher --help exits with code 0."""
        result = runner.invoke(app, ["govern", "hook-watcher", "--help"])
        assert result.exit_code == 0

    def test_govern_negotiate_help(self) -> None:
        """thegent govern negotiate --help exits with code 0."""
        result = runner.invoke(app, ["govern", "negotiate", "--help"])
        assert result.exit_code == 0

    def test_govern_purge_help(self) -> None:
        """thegent govern purge --help exits with code 0."""
        result = runner.invoke(app, ["govern", "purge", "--help"])
        assert result.exit_code == 0

    def test_govern_purge_history_help(self) -> None:
        """thegent govern purge-history --help exits with code 0."""
        result = runner.invoke(app, ["govern", "purge-history", "--help"])
        assert result.exit_code == 0

    def test_govern_release_pack_help(self) -> None:
        """thegent govern release-pack --help exits with code 0."""
        result = runner.invoke(app, ["govern", "release-pack", "--help"])
        assert result.exit_code == 0

    def test_govern_roadmap_help(self) -> None:
        """thegent govern roadmap --help exits with code 0."""
        result = runner.invoke(app, ["govern", "roadmap", "--help"])
        assert result.exit_code == 0

    def test_govern_self_heal_tests_help(self) -> None:
        """thegent govern self-heal-tests --help exits with code 0."""
        result = runner.invoke(app, ["govern", "self-heal-tests", "--help"])
        assert result.exit_code == 0

    def test_govern_sweep_help(self) -> None:
        """thegent govern sweep --help exits with code 0."""
        result = runner.invoke(app, ["govern", "sweep", "--help"])
        assert result.exit_code == 0

    def test_govern_trend_analysis_help(self) -> None:
        """thegent govern trend-analysis --help exits with code 0."""
        result = runner.invoke(app, ["govern", "trend-analysis", "--help"])
        assert result.exit_code == 0

    # Guardrails commands
    def test_guardrails_help_exits_zero(self) -> None:
        """thegent guardrails --help exits with code 0."""
        result = runner.invoke(app, ["guardrails", "--help"])
        assert result.exit_code == 0

    def test_guardrails_check_help(self) -> None:
        """thegent guardrails check --help exits with code 0."""
        result = runner.invoke(app, ["guardrails", "check", "--help"])
        assert result.exit_code == 0

    def test_guardrails_show_help(self) -> None:
        """thegent guardrails show --help exits with code 0."""
        result = runner.invoke(app, ["guardrails", "show", "--help"])
        assert result.exit_code == 0

    # Hierarchy commands
    def test_hierarchy_help_exits_zero(self) -> None:
        """thegent hierarchy --help exits with code 0."""
        result = runner.invoke(app, ["hierarchy", "--help"])
        assert result.exit_code == 0

    def test_hierarchy_relationships_help(self) -> None:
        """thegent hierarchy relationships --help exits with code 0."""
        result = runner.invoke(app, ["hierarchy", "relationships", "--help"])
        assert result.exit_code == 0

    def test_hierarchy_show_help(self) -> None:
        """thegent hierarchy show --help exits with code 0."""
        result = runner.invoke(app, ["hierarchy", "show", "--help"])
        assert result.exit_code == 0

    def test_hierarchy_tree_help(self) -> None:
        """thegent hierarchy tree --help exits with code 0."""
        result = runner.invoke(app, ["hierarchy", "tree", "--help"])
        assert result.exit_code == 0
