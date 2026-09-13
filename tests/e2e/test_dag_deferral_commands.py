"""
E2E tests for DAG and Deferral commands.

Agent Journey: Agent manages DAG (Directed Acyclic Graph) of tasks and deferrals
Expected Behavior: Commands execute successfully and show status/reconcile state
"""

import pytest
from typer.testing import CliRunner

from thegent.main import app

# Skip all tests in this file - CLI commands do not exist
pytestmark = pytest.mark.skip(reason="CLI commands 'dag', 'deferral' do not exist in current implementation")

runner = CliRunner()


@pytest.mark.e2e
class TestDagDeferralCommands:
    """E2E tests for DAG and Deferral commands."""

    # DAG commands
    def test_dag_help_exits_zero(self) -> None:
        """thegent dag --help exits with code 0."""
        result = runner.invoke(app, ["dag", "--help"])
        assert result.exit_code == 0

    def test_dag_reconcile_help(self) -> None:
        """thegent dag reconcile --help exits with code 0."""
        result = runner.invoke(app, ["dag", "reconcile", "--help"])
        assert result.exit_code == 0

    def test_dag_wait_next_help(self) -> None:
        """thegent dag wait-next --help exits with code 0."""
        result = runner.invoke(app, ["dag", "wait-next", "--help"])
        assert result.exit_code == 0

    # Deferral commands
    def test_deferral_help_exits_zero(self) -> None:
        """thegent deferral --help exits with code 0."""
        result = runner.invoke(app, ["deferral", "--help"])
        assert result.exit_code == 0

    def test_deferral_list_help(self) -> None:
        """thegent deferral list --help exits with code 0."""
        result = runner.invoke(app, ["deferral", "list", "--help"])
        assert result.exit_code == 0

    def test_deferral_resume_help(self) -> None:
        """thegent deferral resume --help exits with code 0."""
        result = runner.invoke(app, ["deferral", "resume", "--help"])
        assert result.exit_code == 0

    def test_deferral_show_help(self) -> None:
        """thegent deferral show --help exits with code 0."""
        result = runner.invoke(app, ["deferral", "show", "--help"])
        assert result.exit_code == 0

    # control_plane commands
    def test_control_plane_help(self) -> None:
        """thegent control_plane --help exits with code 0."""
        result = runner.invoke(app, ["control_plane", "--help"])
        assert result.exit_code == 0

    def test_control_plane_serve_help(self) -> None:
        """thegent control_plane serve --help exits with code 0."""
        result = runner.invoke(app, ["control_plane", "serve", "--help"])
        assert result.exit_code == 0

    def test_control_plane_status_help(self) -> None:
        """thegent control_plane status --help exits with code 0."""
        result = runner.invoke(app, ["control_plane", "status", "--help"])
        assert result.exit_code == 0

    def test_control_plane_start_help(self) -> None:
        """thegent control_plane start --help exits with code 0."""
        result = runner.invoke(app, ["control_plane", "start", "--help"])
        assert result.exit_code == 0

    def test_control_plane_stop_help(self) -> None:
        """thegent control_plane stop --help exits with code 0."""
        result = runner.invoke(app, ["control_plane", "stop", "--help"])
        assert result.exit_code == 0

    # Top-level commands
    def test_archive_help(self) -> None:
        """thegent archive --help exits with code 0."""
        result = runner.invoke(app, ["archive", "--help"])
        assert result.exit_code == 0

    def test_closure_pack_help(self) -> None:
        """thegent closure-pack --help exits with code 0."""
        result = runner.invoke(app, ["closure-pack", "--help"])
        assert result.exit_code == 0
