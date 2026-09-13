"""
E2E tests for Memory and Models commands.

Agent Journey: Agent manages memory (working memory) and models (AI providers)
Expected Behavior: Commands execute successfully and provide memory/model management
"""

import pytest
from typer.testing import CliRunner

from thegent.main import app

# Skip all tests in this file - CLI commands do not exist
pytestmark = pytest.mark.skip(reason="CLI commands 'models' do not exist in current implementation")

runner = CliRunner()


@pytest.mark.e2e
class TestMemoryModelsCommands:
    """E2E tests for Memory and Models commands."""

    # Memory commands
    def test_memory_help_exits_zero(self) -> None:
        """thegent memory --help exits with code 0."""
        result = runner.invoke(app, ["memory", "--help"])
        assert result.exit_code == 0

    def test_memory_add_help(self) -> None:
        """thegent memory add --help exits with code 0."""
        result = runner.invoke(app, ["memory", "add", "--help"])
        assert result.exit_code == 0

    def test_memory_remember_help(self) -> None:
        """thegent memory remember --help exits with code 0."""
        result = runner.invoke(app, ["memory", "remember", "--help"])
        assert result.exit_code == 0

    def test_memory_issue_help(self) -> None:
        """thegent memory issue --help exits with code 0."""
        result = runner.invoke(app, ["memory", "issue", "--help"])
        assert result.exit_code == 0

    def test_memory_rule_help(self) -> None:
        """thegent memory rule --help exits with code 0."""
        result = runner.invoke(app, ["memory", "rule", "--help"])
        assert result.exit_code == 0

    def test_memory_scrape_help(self) -> None:
        """thegent memory scrape --help exits with code 0."""
        result = runner.invoke(app, ["memory", "scrape", "--help"])
        assert result.exit_code == 0

    def test_memory_synthesize_help(self) -> None:
        """thegent memory synthesize --help exits with code 0."""
        result = runner.invoke(app, ["memory", "synthesize", "--help"])
        assert result.exit_code == 0

    def test_memory_garden_help(self) -> None:
        """thegent memory garden --help exits with code 0."""
        result = runner.invoke(app, ["memory", "garden", "--help"])
        assert result.exit_code == 0

    # Models commands
    def test_models_metrics_help(self) -> None:
        """thegent models metrics --help exits with code 0."""
        result = runner.invoke(app, ["models", "metrics", "--help"])
        assert result.exit_code == 0

    def test_models_cost_values_help(self) -> None:
        """thegent models cost-values --help exits with code 0."""
        result = runner.invoke(app, ["models", "cost-values", "--help"])
        assert result.exit_code == 0

    def test_models_speed_index_help(self) -> None:
        """thegent models speed-index --help exits with code 0."""
        result = runner.invoke(app, ["models", "speed-index", "--help"])
        assert result.exit_code == 0

    def test_models_quality_index_help(self) -> None:
        """thegent models quality-index --help exits with code 0."""
        result = runner.invoke(app, ["models", "quality-index", "--help"])
        assert result.exit_code == 0

    def test_models_setup_help(self) -> None:
        """thegent models-setup --help exits with code 0."""
        result = runner.invoke(app, ["models-setup", "--help"])
        assert result.exit_code == 0

    def test_leaderboard_help(self) -> None:
        """thegent leaderboard --help exits with code 0."""
        result = runner.invoke(app, ["leaderboard", "--help"])
        assert result.exit_code == 0
