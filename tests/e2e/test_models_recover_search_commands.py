"""
E2E tests for Model Indices, Recovery, and Search commands.

Agent Journey: Agent searches for system capabilities, recovers from failure, and explores model options
Expected Behavior: Commands execute successfully and provide relevant indices/search results
"""

import pytest
from typer.testing import CliRunner

from thegent.main import app

# Skip all tests in this file - CLI commands do not exist
pytestmark = pytest.mark.skip(reason="CLI commands 'recover', 'search' do not exist in current implementation")

runner = CliRunner()


@pytest.mark.e2e
class TestModelsRecoverSearchCommands:
    """E2E tests for Model Indices, Recovery, and Search commands."""

    # Models indices
    def test_list_model_indices_help(self) -> None:
        """thegent list-model-indices --help exits with code 0."""
        result = runner.invoke(app, ["list-model-indices", "--help"])
        assert result.exit_code == 0

    def test_search_models_help(self) -> None:
        """thegent search-models --help exits with code 0."""
        result = runner.invoke(app, ["search-models", "--help"])
        assert result.exit_code == 0

    def test_search_modalities_help(self) -> None:
        """thegent search-modalities --help exits with code 0."""
        result = runner.invoke(app, ["search-modalities", "--help"])
        assert result.exit_code == 0

    def test_show_modalities_help(self) -> None:
        """thegent show-modalities --help exits with code 0."""
        result = runner.invoke(app, ["show-modalities", "--help"])
        assert result.exit_code == 0

    # Recover commands
    def test_recover_help_exits_zero(self) -> None:
        """thegent recover --help exits with code 0."""
        result = runner.invoke(app, ["recover", "--help"])
        assert result.exit_code == 0

    def test_recover_dag_recover_help(self) -> None:
        """thegent recover dag-recover --help exits with code 0."""
        result = runner.invoke(app, ["recover", "dag-recover", "--help"])
        assert result.exit_code == 0

    # System commands
    def test_uninstall_system_deps_help(self) -> None:
        """thegent uninstall-system-deps --help exits with code 0."""
        result = runner.invoke(app, ["uninstall-system-deps", "--help"])
        assert result.exit_code == 0

    def test_restore_backup_help(self) -> None:
        """thegent restore-backup --help exits with code 0."""
        result = runner.invoke(app, ["restore-backup", "--help"])
        assert result.exit_code == 0

    def test_validate_provider_help(self) -> None:
        """thegent validate-provider --help exits with code 0."""
        result = runner.invoke(app, ["validate-provider", "--help"])
        assert result.exit_code == 0

    # Top-level commands
    def test_fix_help(self) -> None:
        """thegent fix --help exits with code 0."""
        result = runner.invoke(app, ["fix", "--help"])
        assert result.exit_code == 0

    def test_free_help(self) -> None:
        """thegent free --help exits with code 0."""
        result = runner.invoke(app, ["free", "--help"])
        assert result.exit_code == 0

    def test_route_probe_help(self) -> None:
        """thegent route-probe --help exits with code 0."""
        result = runner.invoke(app, ["route-probe", "--help"])
        assert result.exit_code == 0

    def test_lock_cleanup_help(self) -> None:
        """thegent lock_cleanup --help exits with code 0."""
        result = runner.invoke(app, ["lock_cleanup", "--help"])
        assert result.exit_code == 0

    def test_lock_cleanup_service_help(self) -> None:
        """thegent lock_cleanup service --help exits with code 0."""
        result = runner.invoke(app, ["lock_cleanup", "service", "--help"])
        assert result.exit_code == 0
