"""Unit tests for infra OS user adapter."""

import subprocess
from pathlib import Path
from unittest.mock import patch

from thegent.infra.os_user_adapter import OSUserAdapter


def test_macos_uid_derivation_uses_next_available_id(tmp_path):
    """MacOS user creation should derive UID from the highest existing UID."""
    adapter = OSUserAdapter()
    adapter.system = "Darwin"
    home_dir = tmp_path / "agent-home"

    with patch.object(
        adapter,
        "_run_privileged",
        side_effect=[
            (True, "501 1001\n502 1002\n505 2000"),
            (True, ""),
            (True, ""),
            (True, ""),
            (True, ""),
            (True, ""),
            (True, ""),
            (True, ""),
            (True, ""),
            (True, ""),
        ],
    ):
        ok, message = adapter._create_macos_user("agent", home_dir)

    assert ok
    assert "UID 2001" in message


def test_windows_home_dir_config_included_in_power_shell_command():
    """Windows creation path should include explicit home-directory setup."""
    adapter = OSUserAdapter()
    adapter.system = "Windows"

    with patch("thegent.infra.os_user_adapter.subprocess.run") as run_mock:
        run_mock.return_value = subprocess.CompletedProcess(args=(), returncode=0, stdout="created")

        ok, message = adapter._create_windows_user("agent", Path("C:/agent/home"))

    assert ok
    assert run_mock.call_count == 1
    assert "New-Item" in run_mock.call_args.args[0][-1]
    assert "Set-LocalUser" in run_mock.call_args.args[0][-1]
    assert message == "created"


def test_create_os_user_returns_failure_for_unsupported_platform():
    """Unsupported platform returns a failure tuple."""
    adapter = OSUserAdapter()
    adapter.system = "Plan9"

    ok, reason = adapter.create_os_user("agent")

    assert ok is False
    assert "Unsupported OS: Plan9" in reason
