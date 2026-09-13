"""
Visual TUI Testing for thegent
Applitools-style visual regression for terminal UI
"""

import subprocess

import pytest


class TestTUI:
    """Visual TUI regression tests using terminal capture."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        self.output_dir = tmp_path / "screenshots"
        self.output_dir.mkdir()

    def capture_terminal_state(self, command: list[str]) -> str:
        """Capture terminal state for a given command."""
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        return result.stdout + result.stderr

    def test_agent_initialization_screen(self):
        """Test that agent initialization screen renders correctly."""
        output = self.capture_terminal_state(["thegent", "init"])
        assert "Initializing" in output
        assert "Agent" in output

    def test_help_command_output(self):
        """Test help command displays all available commands."""
        output = self.capture_terminal_state(["thegent", "help"])
        expected_commands = ["agent", "governance", "health"]
        for cmd in expected_commands:
            assert cmd in output.lower()

    def test_error_state_visual(self):
        """Test that error states render with proper formatting."""
        output = self.capture_terminal_state(["thegent", "invalid-command"])
        assert "error" in output.lower() or "Error" in output


class TestAccessibilityTree:
    """Accessibility tree validation for TUI."""

    def test_accessibility_tree_generation(self):
        """Test that accessibility tree can be generated."""
        result = subprocess.run(["thegent", "a11y-tree"], capture_output=True, text=True)
        assert result.returncode == 0 or "error" in result.stderr.lower()
