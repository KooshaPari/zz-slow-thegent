"""Tests for HarnessTUIMapper - unified harness TUI action mapper."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from thegent.agents.unified_session_index import (
    HarnessActionError,
    HarnessTUIMapper,
    HarnessType,
)


class TestHarnessTUIMapper:
    """Test HarnessTUIMapper functionality."""

    def test_list_actions(self):
        """List all available abstract actions."""
        mapper = HarnessTUIMapper()
        actions = mapper.list_actions()
        assert "send_message" in actions
        assert "attach_terminal" in actions
        assert "view_history" in actions
        assert "get_status" in actions
        assert "list_sessions" in actions

    def test_list_harnesses_for_action(self):
        """List harnesses that support a given action."""
        mapper = HarnessTUIMapper()
        harnesses = mapper.list_harnesses("send_message")
        assert "codex" in harnesses
        assert "claude" in harnesses
        assert "cursor" in harnesses

    def test_get_command_template(self):
        """Get the command template for a harness-action pair."""
        mapper = HarnessTUIMapper()
        cmd = mapper.get_command(HarnessType.CODEX, "send_message")
        assert cmd == "codex -p {prompt}"

        cmd = mapper.get_command(HarnessType.CLAUDE, "attach_terminal")
        assert "zmx attach" in cmd

    def test_get_command_unknown_harness(self):
        """Get command for unknown harness returns None."""
        mapper = HarnessTUIMapper()
        # Using invalid harness directly via enum
        cmd = mapper.get_command(HarnessType.UNKNOWN, "send_message")
        assert cmd is None

    def test_execute_unknown_action(self):
        """Execute unknown action raises HarnessActionError."""
        mapper = HarnessTUIMapper()
        with pytest.raises(HarnessActionError, match="Unknown action"):
            mapper.execute(HarnessType.CODEX, "nonexistent_action")

    def test_execute_missing_parameter(self):
        """Execute with missing template parameter raises HarnessActionError."""
        mapper = HarnessTUIMapper()
        with pytest.raises(HarnessActionError, match="Missing required parameter"):
            mapper.execute(HarnessType.CODEX, "send_message")  # missing prompt

    @patch("subprocess.run")
    def test_execute_success(self, mock_run):
        """Execute a command successfully."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        mapper = HarnessTUIMapper()
        result = mapper.execute(HarnessType.CODEX, "get_status")

        assert result["success"] is True
        assert result["returncode"] == 0

    @patch("subprocess.run")
    def test_execute_failure(self, mock_run):
        """Execute a command that fails."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error message"
        mock_run.return_value = mock_result

        mapper = HarnessTUIMapper()
        result = mapper.execute(HarnessType.CODEX, "get_status")

        assert result["success"] is False
        assert result["returncode"] == 1
        assert "error message" in result["stderr"]

    @patch("subprocess.run")
    def test_execute_timeout(self, mock_run):
        """Execute a command that times out."""
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 30)

        mapper = HarnessTUIMapper()
        result = mapper.execute(HarnessType.CODEX, "get_status")

        assert result["success"] is False
        assert "timed out" in result["stderr"]

    @patch("subprocess.run")
    def test_execute_command_not_found(self, mock_run):
        """Execute when harness CLI is not installed."""
        mock_run.side_effect = FileNotFoundError("codex")
        mapper = HarnessTUIMapper()
        with pytest.raises(HarnessActionError, match="not found"):
            mapper.execute(HarnessType.CODEX, "get_status")

    @patch("subprocess.run")
    def test_register_host_custom_actions(self, mock_run):
        """Register a new host with custom actions."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "ok"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        mapper = HarnessTUIMapper()

        mapper.register_host(
            host_id="remote-1",
            harness=HarnessType.CODEX,
            command_prefix="ssh user@remote",
            custom_actions={
                "send_message": "remote-codex -p {prompt}",
            },
        )

        # Check custom action is registered and executed
        result = mapper.execute(
            harness=HarnessType.CODEX,
            action="send_message",
            host_id="remote-1",
            prompt="test",
        )
        # The command should use custom_actions override
        assert "remote-codex" in result["command"]

    @patch("subprocess.run")
    def test_register_host_with_prefix(self, mock_run):
        """Register a host with command prefix for SSH."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "ok"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        mapper = HarnessTUIMapper()

        mapper.register_host(
            host_id="gpu-server",
            harness=HarnessType.CLAUDE,
            command_prefix="ssh -t user@gpu-server",
        )

        # Verify prefix is applied
        result = mapper.execute(
            harness=HarnessType.CLAUDE,
            action="get_status",
            host_id="gpu-server",
        )
        assert "ssh -t user@gpu-server" in result["command"]

    def test_custom_actions_override(self):
        """Custom actions override default mappings."""
        mapper = HarnessTUIMapper(
            custom_actions={
                "send_message": {
                    "codex": "custom-codex {prompt}",
                }
            }
        )

        cmd = mapper.get_command(HarnessType.CODEX, "send_message")
        assert cmd == "custom-codex {prompt}"

    def test_harness_type_enum_values(self):
        """Verify HarnessType enum values."""
        assert HarnessType.CURSOR.value == "cursor"
        assert HarnessType.CODEX.value == "codex"
        assert HarnessType.CLAUDE.value == "claude"
        assert HarnessType.ANTE.value == "ante"
        assert HarnessType.DROID.value == "droid"
