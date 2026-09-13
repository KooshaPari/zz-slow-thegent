"""
E2E test for: thegent project init

Agent Journey: Agent executes thegent project init command
Expected Behavior: Command executes successfully and returns expected output
"""

import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from thegent.main import app

runner = CliRunner()


def run_project_register() -> str:
    """Run project init in an isolated temp directory."""
    with tempfile.TemporaryDirectory(prefix="thegent-project-register-") as project_path:
        project_name = f"thegent-test-project-{Path(project_path).name}"
        result = runner.invoke(
            app,
            [
                "project",
                "init",
                "--name",
                project_name,
                "--path",
                project_path,
            ],
        )
        assert result.exit_code == 0, f"Command failed: {result.stdout} {result.stderr}"
        return result.stdout


@pytest.mark.e2e
class TestProjectRegister:
    """E2E tests for thegent project init command."""

    def test_project_register_exits_zero(self) -> None:
        """thegent project init exits with code 0."""
        run_project_register()

    def test_project_register_produces_output(self) -> None:
        """thegent project init produces expected output."""
        output = run_project_register()
        assert output
        # TODO: Add specific output assertions based on command behavior
        assert output != ""

    def test_project_register_help_exits_zero(self) -> None:
        """thegent project init --help exits with code 0."""
        result = runner.invoke(app, ["project", "init", "--help"])
        assert result.exit_code == 0
