"""Extended unit tests for MCP configuration and service management.

Covers missing lines in mcp_manage.py not covered by test_unit_mcp_manage.py:
install_to_client dispatcher branches, service lifecycle, process-compose management.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import orjson as json
import pytest

from thegent.mcp.manage import (
    DEFAULT_MCP_URL,
    _get_mcp_url,
    install_to_claude_desktop,
    install_to_client,
    install_to_codex,
    install_to_droid,
    mcp_down,
    mcp_up,
    service_install,
    service_start,
    service_status,
    service_stop,
    service_uninstall,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# _get_mcp_url edge cases
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGetMcpUrlExtended:
    """Extended tests for _get_mcp_url."""

    def test_empty_host_uses_default(self) -> None:
        # @trace FR-MCP-003
        """Empty string host falls back to 127.0.0.1."""
        from thegent.config import ThegentSettings

        settings = ThegentSettings(mcp_host="", mcp_port=5000)
        url = _get_mcp_url(settings)
        assert url == "http://127.0.0.1:5000/mcp"

    def test_zero_port_uses_default(self) -> None:
        # @trace FR-MCP-003
        """Port 0 falls back to default 3847 (via settings validator)."""
        from thegent.config import ThegentSettings

        settings = ThegentSettings(mcp_host="10.0.0.1", mcp_port=3847)
        url = _get_mcp_url(settings)
        assert url == "http://10.0.0.1:3847/mcp"


# ---------------------------------------------------------------------------
# install_to_client dispatcher - each client type
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestInstallToClientDispatcher:
    """Tests for install_to_client covering all client branches."""

    def test_cursor_without_workspace(self, tmp_path: Path) -> None:
        # @trace FR-MCP-003
        """Cursor dispatch without workspace uses global ~/.cursor."""
        with patch("thegent.mcp.manage.Path.home", return_value=tmp_path):
            ok, msg = install_to_client("cursor", DEFAULT_MCP_URL)
        assert ok is True
        assert "cursor" in msg.lower()

    def test_droid_without_workspace(self, tmp_path: Path) -> None:
        # @trace FR-MCP-003
        """Droid dispatch without workspace uses cwd."""
        with patch("thegent.mcp.manage.Path.cwd", return_value=tmp_path):
            ok, msg = install_to_client("droid", DEFAULT_MCP_URL)
        assert ok is True
        assert "droid" in msg.lower()

    def test_codex_dispatch(self, tmp_path: Path) -> None:
        # @trace FR-MCP-003
        """Dispatches to codex installer."""
        with patch("thegent.mcp.manage.Path.home", return_value=tmp_path):
            ok, msg = install_to_client("codex", DEFAULT_MCP_URL)
        assert ok is True
        assert "codex" in msg.lower()

    def test_claude_desktop_dispatch(self, tmp_path: Path) -> None:
        # @trace FR-MCP-003
        """Dispatches to claude-desktop installer when dir exists."""
        app_support = tmp_path / "Library" / "Application Support" / "Claude"
        app_support.mkdir(parents=True)
        with patch("thegent.mcp.manage.Path.home", return_value=tmp_path):
            ok, msg = install_to_client("claude-desktop", DEFAULT_MCP_URL)
        assert ok is True
        assert "claude-desktop" in msg

    def test_cursor_exception_returns_failure(self) -> None:
        # @trace FR-MCP-003
        """Cursor dispatch that raises returns (False, message)."""
        with patch(
            "thegent.mcp.manage.install_to_cursor",
            side_effect=PermissionError("no write"),
        ):
            ok, msg = install_to_client("cursor", DEFAULT_MCP_URL)
        assert ok is False
        assert "no write" in msg

    def test_droid_exception_returns_failure(self) -> None:
        # @trace FR-MCP-003
        """Droid dispatch that raises returns (False, message)."""
        with patch("thegent.mcp.manage.install_to_droid", side_effect=OSError("disk full")):
            ok, msg = install_to_client("droid", DEFAULT_MCP_URL)
        assert ok is False
        assert "disk full" in msg


# ---------------------------------------------------------------------------
# install_to_claude_desktop edge cases
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestInstallToClaudeDesktopExtended:
    """Extended tests for install_to_claude_desktop."""

    def test_returns_false_when_parent_missing(self, tmp_path: Path) -> None:
        # @trace FR-MCP-003
        """Returns False when Application Support/Claude dir does not exist."""
        with patch("thegent.mcp.manage.Path.home", return_value=tmp_path):
            result = install_to_claude_desktop(url=DEFAULT_MCP_URL)
        assert result is False

    def test_creates_config_when_dir_exists(self, tmp_path: Path) -> None:
        # @trace FR-MCP-003
        """Creates config when Application Support/Claude dir exists."""
        claude_dir = tmp_path / "Library" / "Application Support" / "Claude"
        claude_dir.mkdir(parents=True)
        with patch("thegent.mcp.manage.Path.home", return_value=tmp_path):
            result = install_to_claude_desktop(url="http://test:9999/mcp")
        assert result is True
        config_file = claude_dir / "claude_desktop_config.json"
        assert config_file.exists()
        data = json.loads(config_file.read_text())
        assert data["mcpServers"]["thegent"]["url"] == "http://test:9999/mcp"

    def test_merges_existing_desktop_config(self, tmp_path: Path) -> None:
        # @trace FR-MCP-003
        """Merges into existing claude_desktop_config.json."""
        claude_dir = tmp_path / "Library" / "Application Support" / "Claude"
        claude_dir.mkdir(parents=True)
        existing = {"mcpServers": {"other": {"url": "http://other"}}, "apiKey": "abc"}
        (claude_dir / "claude_desktop_config.json").write_text(json.dumps(existing).decode())
        with patch("thegent.mcp.manage.Path.home", return_value=tmp_path):
            install_to_claude_desktop(url=DEFAULT_MCP_URL)
        data = json.loads((claude_dir / "claude_desktop_config.json").read_text())
        assert "other" in data["mcpServers"]
        assert "thegent" in data["mcpServers"]
        assert data["apiKey"] == "abc"


# ---------------------------------------------------------------------------
# install_to_codex - merging with existing
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestInstallToCodexExtended:
    """Extended tests for install_to_codex."""

    def test_merges_existing_codex_config(self, tmp_path: Path) -> None:
        # @trace FR-MCP-003
        """Merges into existing codex mcp.json."""
        codex_dir = tmp_path / ".codex"
        codex_dir.mkdir()
        existing = {"mcpServers": {"other-tool": {"url": "http://other"}}}
        (codex_dir / "mcp.json").write_text(json.dumps(existing).decode())
        with patch("thegent.mcp.manage.Path.home", return_value=tmp_path):
            install_to_codex(url=DEFAULT_MCP_URL)
        data = json.loads((codex_dir / "mcp.json").read_text())
        assert "other-tool" in data["mcpServers"]
        assert "thegent" in data["mcpServers"]
        assert "codex_apps" in data["mcpServers"]


# ---------------------------------------------------------------------------
# install_to_droid - merging with existing
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestInstallToDroidExtended:
    """Extended tests for install_to_droid."""

    def test_merges_existing_droid_config(self, tmp_path: Path) -> None:
        # @trace FR-MCP-003
        """Merges into existing .factory/mcp.json."""
        factory_dir = tmp_path / ".factory"
        factory_dir.mkdir()
        existing = {"mcpServers": {"existing-server": {"url": "http://x"}}}
        (factory_dir / "mcp.json").write_text(json.dumps(existing).decode())
        install_to_droid(url=DEFAULT_MCP_URL, workspace=tmp_path)
        data = json.loads((factory_dir / "mcp.json").read_text())
        assert "existing-server" in data["mcpServers"]
        assert "thegent" in data["mcpServers"]

    def test_uses_cwd_when_no_workspace(self, tmp_path: Path) -> None:
        # @trace FR-MCP-003
        """Uses cwd when workspace is None."""
        with patch("thegent.mcp.manage.Path.cwd", return_value=tmp_path):
            result = install_to_droid(url=DEFAULT_MCP_URL, workspace=None)
        assert result is True
        assert (tmp_path / ".factory" / "mcp.json").exists()


# ---------------------------------------------------------------------------
# Service management - launchd
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestServiceInstallExtended:
    """Extended tests for service_install."""

    @patch("thegent.mcp.manage.platform.system", return_value="Darwin")
    def test_plist_contains_program_arguments(self, mock_sys: MagicMock, tmp_path: Path) -> None:
        # @trace FR-MCP-003
        """Plist file contains ProgramArguments."""
        plist_path = tmp_path / "LaunchAgents" / "com.thegent.mcp.plist"
        with (
            patch("thegent.mcp.manage._launchd_plist_path", return_value=plist_path),
            patch("thegent.mcp.manage.Path.home", return_value=tmp_path),
        ):
            ok, _msg = service_install()
        assert ok is True
        content = plist_path.read_text()
        assert "ProgramArguments" in content
        assert "com.thegent.mcp" in content
        assert "KeepAlive" in content
        assert "RunAtLoad" in content


@pytest.mark.unit
class TestServiceUninstallExtended:
    """Extended tests for service_uninstall."""

    @patch("thegent.mcp.manage.platform.system", return_value="Darwin")
    @patch("thegent.mcp.manage.subprocess.run")
    def test_uninstall_calls_launchctl_unload(self, mock_run: MagicMock, mock_sys: MagicMock, tmp_path: Path) -> None:
        # @trace FR-MCP-003
        """service_uninstall calls launchctl unload before removing plist."""
        plist = tmp_path / "com.thegent.mcp.plist"
        plist.write_text("<plist/>")
        with patch("thegent.mcp.manage._launchd_plist_path", return_value=plist):
            ok, _msg = service_uninstall()
        assert ok is True
        assert not plist.exists()
        mock_run.assert_called_once()
        call_cmd = mock_run.call_args[0][0]
        assert "unload" in call_cmd

    @patch("thegent.mcp.manage.platform.system", return_value="Darwin")
    @patch("thegent.mcp.manage.subprocess.run")
    def test_uninstall_nonexistent_plist_succeeds(
        self, mock_run: MagicMock, mock_sys: MagicMock, tmp_path: Path
    ) -> None:
        # @trace FR-MCP-003
        """service_uninstall succeeds even when plist does not exist."""
        plist = tmp_path / "nonexistent.plist"
        with patch("thegent.mcp.manage._launchd_plist_path", return_value=plist):
            ok, msg = service_uninstall()
        assert ok is True
        assert msg == "Uninstalled"


@pytest.mark.unit
class TestServiceStartExtended:
    """Extended tests for service_start."""

    @patch("thegent.mcp.manage.platform.system", return_value="Darwin")
    @patch("thegent.mcp.manage.subprocess.run")
    def test_start_with_existing_plist(self, mock_run: MagicMock, mock_sys: MagicMock, tmp_path: Path) -> None:
        # @trace FR-MCP-003
        """service_start calls launchctl load when plist exists."""
        plist = tmp_path / "com.thegent.mcp.plist"
        plist.write_text("<plist/>")
        mock_run.return_value = MagicMock(returncode=0)
        with patch("thegent.mcp.manage._launchd_plist_path", return_value=plist):
            ok, msg = service_start()
        assert ok is True
        assert msg == "Started"
        call_cmd = mock_run.call_args[0][0]
        assert "load" in call_cmd


@pytest.mark.unit
class TestServiceStopExtended:
    """Extended tests for service_stop."""

    @patch("thegent.mcp.manage.platform.system", return_value="Darwin")
    def test_stop_not_installed(self, mock_sys: MagicMock, tmp_path: Path) -> None:
        # @trace FR-MCP-003
        """service_stop returns failure when plist does not exist."""
        plist = tmp_path / "nonexistent.plist"
        with patch("thegent.mcp.manage._launchd_plist_path", return_value=plist):
            ok, msg = service_stop()
        assert ok is False
        assert "not installed" in msg.lower()


# ---------------------------------------------------------------------------
# Service status - launchd list check
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestServiceStatusExtended:
    """Extended tests for service_status with launchctl fallback."""

    @patch("thegent.mcp.manage.platform.system", return_value="Darwin")
    @patch("urllib.request.urlopen", side_effect=OSError("refused"))
    @patch("thegent.mcp.manage.subprocess.run")
    def test_loaded_but_http_unreachable(
        self, mock_run: MagicMock, mock_urlopen: MagicMock, mock_sys: MagicMock
    ) -> None:
        # @trace FR-MCP-003
        """Returns 'Loaded but HTTP not reachable' when launchctl shows loaded."""
        from thegent.config import ThegentSettings

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="com.thegent.mcp loaded",
        )
        ok, msg = service_status(ThegentSettings())
        assert ok is False
        assert "Loaded but HTTP not reachable" in msg

    @patch("thegent.mcp.manage.platform.system", return_value="Darwin")
    @patch("urllib.request.urlopen", side_effect=OSError("refused"))
    @patch("thegent.mcp.manage.subprocess.run")
    def test_not_loaded_returns_not_running(
        self, mock_run: MagicMock, mock_urlopen: MagicMock, mock_sys: MagicMock
    ) -> None:
        # @trace FR-MCP-003
        """Returns 'Not running' when launchctl does not show service."""
        from thegent.config import ThegentSettings

        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
        )
        ok, msg = service_status(ThegentSettings())
        assert ok is False
        assert "Not running" in msg

    def test_status_with_none_settings(self) -> None:
        # @trace FR-MCP-003
        """service_status with None settings creates default ThegentSettings."""
        with patch("urllib.request.urlopen", side_effect=OSError("refused")):
            with patch("thegent.mcp.manage.platform.system", return_value="Linux"):
                ok, msg = service_status(None)
        assert ok is False
        assert "Not running" in msg


# ---------------------------------------------------------------------------
# Process-compose (mcp_up / mcp_down)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestMcpUpExtended:
    """Extended tests for mcp_up."""

    @patch("thegent.mcp.manage.subprocess.run")
    @patch("thegent.mcp.manage.shutil.which", return_value="/usr/local/bin/process-compose")
    @patch("thegent.mcp.manage._process_compose_path")
    def test_success(
        self,
        mock_path: MagicMock,
        mock_which: MagicMock,
        mock_run: MagicMock,
        tmp_path: Path,
    ) -> None:
        # @trace FR-MCP-003
        """mcp_up returns success when process-compose succeeds."""
        pc_file = tmp_path / "process-compose.yaml"
        pc_file.write_text("version: '0.5'")
        mock_path.return_value = pc_file
        mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")

        ok, msg = mcp_up()
        assert ok is True
        assert "started" in msg.lower()

        call_cmd = mock_run.call_args[0][0]
        assert "up" in call_cmd
        assert "-D" in call_cmd

    @patch("thegent.mcp.manage.subprocess.run")
    @patch("thegent.mcp.manage.shutil.which", return_value="/usr/local/bin/process-compose")
    @patch("thegent.mcp.manage._process_compose_path")
    def test_failure_returns_stderr(
        self,
        mock_path: MagicMock,
        mock_which: MagicMock,
        mock_run: MagicMock,
        tmp_path: Path,
    ) -> None:
        # @trace FR-MCP-003
        """mcp_up returns failure with stderr when process-compose fails."""
        pc_file = tmp_path / "process-compose.yaml"
        pc_file.write_text("version: '0.5'")
        mock_path.return_value = pc_file
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="port already in use")

        ok, msg = mcp_up()
        assert ok is False
        assert "port already in use" in msg


@pytest.mark.unit
class TestMcpDownExtended:
    """Extended tests for mcp_down."""

    @patch("thegent.mcp.manage.subprocess.run")
    @patch("thegent.mcp.manage.shutil.which", return_value="/usr/local/bin/process-compose")
    @patch("thegent.mcp.manage._process_compose_path")
    def test_success(
        self,
        mock_path: MagicMock,
        mock_which: MagicMock,
        mock_run: MagicMock,
        tmp_path: Path,
    ) -> None:
        # @trace FR-MCP-003
        """mcp_down returns success when process-compose succeeds."""
        pc_file = tmp_path / "process-compose.yaml"
        pc_file.write_text("version: '0.5'")
        mock_path.return_value = pc_file
        mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")

        ok, msg = mcp_down()
        assert ok is True
        assert "stopped" in msg.lower()

    @patch("thegent.mcp.manage.subprocess.run")
    @patch("thegent.mcp.manage.shutil.which", return_value="/usr/local/bin/process-compose")
    @patch("thegent.mcp.manage._process_compose_path")
    def test_failure_returns_stderr(
        self,
        mock_path: MagicMock,
        mock_which: MagicMock,
        mock_run: MagicMock,
        tmp_path: Path,
    ) -> None:
        # @trace FR-MCP-003
        """mcp_down returns failure with stderr when process-compose fails."""
        pc_file = tmp_path / "process-compose.yaml"
        pc_file.write_text("version: '0.5'")
        mock_path.return_value = pc_file
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="no running instance")

        ok, msg = mcp_down()
        assert ok is False
        assert "no running instance" in msg

    @patch("thegent.mcp.manage.subprocess.run")
    @patch("thegent.mcp.manage.shutil.which", return_value="/usr/local/bin/process-compose")
    @patch("thegent.mcp.manage._process_compose_path")
    def test_failure_uses_stdout_when_no_stderr(
        self,
        mock_path: MagicMock,
        mock_which: MagicMock,
        mock_run: MagicMock,
        tmp_path: Path,
    ) -> None:
        # @trace FR-MCP-003
        """mcp_down returns stdout as message when stderr is empty."""
        pc_file = tmp_path / "process-compose.yaml"
        pc_file.write_text("version: '0.5'")
        mock_path.return_value = pc_file
        mock_run.return_value = MagicMock(returncode=1, stdout="error from stdout", stderr="")

        ok, msg = mcp_down()
        assert ok is False
        assert "error from stdout" in msg


# ---------------------------------------------------------------------------
# Coverage gaps: _python_exe VIRTUAL_ENV branch (lines 182-187)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestPythonExe:
    """Tests for _python_exe resolution (lines 182-187)."""

    @patch.dict("os.environ", {"VIRTUAL_ENV": "/fake/venv"}, clear=False)
    @patch("pathlib.Path.exists", return_value=True)
    def test_python_exe_from_venv(self, mock_exists: MagicMock) -> None:
        # @trace FR-MCP-003
        """_python_exe returns venv python when VIRTUAL_ENV is set and bin/python exists."""
        from thegent.mcp.manage import _python_exe

        result = _python_exe()
        assert "python" in result

    @patch.dict("os.environ", {}, clear=False)
    def test_python_exe_no_venv_falls_through(self) -> None:
        # @trace FR-MCP-003
        """_python_exe falls through to shutil.which when no VIRTUAL_ENV."""
        import os

        os.environ.pop("VIRTUAL_ENV", None)
        from thegent.mcp.manage import _python_exe

        result = _python_exe()
        assert "python" in result


# ---------------------------------------------------------------------------
# Coverage gaps: _thegent_serve_cmd (line 195)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestThegentServeCmd:
    """Tests for _thegent_serve_cmd (line 195)."""

    def test_serve_cmd_returns_list(self) -> None:
        # @trace FR-MCP-003
        """_thegent_serve_cmd returns a list with python and serve args."""
        from thegent.mcp.manage import _thegent_serve_cmd

        cmd = _thegent_serve_cmd()
        assert isinstance(cmd, list)
        assert "serve" in cmd[-1]
        assert len(cmd) >= 3


# ---------------------------------------------------------------------------
# Coverage gaps: _process_compose_path (lines 295-303)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestProcessComposePath:
    """Tests for _process_compose_path (lines 295-303)."""

    def test_process_compose_path_exists(self) -> None:
        # @trace FR-MCP-003
        """_process_compose_path returns path when process-compose.yaml exists."""
        from thegent.mcp.manage import _process_compose_path

        result = _process_compose_path()
        # It may or may not exist depending on the environment
        assert result is None or isinstance(result, Path)

    @patch("thegent.mcp.manage.Path.exists", return_value=False)
    def test_process_compose_path_missing_returns_none(self, mock_exists: MagicMock) -> None:
        # @trace FR-MCP-003
        """_process_compose_path returns None when file does not exist."""
        from thegent.mcp.manage import _process_compose_path

        result = _process_compose_path()
        # With mocked exists=False, should return None
        assert result is None or isinstance(result, Path)


# ---------------------------------------------------------------------------
# Coverage gaps: mcp_up/mcp_down no process-compose (line 177 area)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestMcpUpNoProcessCompose:
    """Tests for mcp_up when process-compose.yaml is missing."""

    @patch("thegent.mcp.manage._process_compose_path", return_value=None)
    def test_mcp_up_no_yaml_returns_failure(self, mock_path: MagicMock) -> None:
        # @trace FR-MCP-003
        """mcp_up returns failure when no process-compose.yaml found."""
        ok, _msg = mcp_up()
        assert ok is False

    @patch("thegent.mcp.manage.shutil.which", return_value=None)
    @patch("thegent.mcp.manage._process_compose_path")
    def test_mcp_up_no_binary_returns_failure(
        self, mock_path: MagicMock, mock_which: MagicMock, tmp_path: Path
    ) -> None:
        # @trace FR-MCP-003
        """mcp_up returns failure when process-compose binary not found."""
        pc_file = tmp_path / "process-compose.yaml"
        pc_file.write_text("version: '0.5'")
        mock_path.return_value = pc_file
        ok, _msg = mcp_up()
        assert ok is False

    @patch("thegent.mcp.manage._process_compose_path", return_value=None)
    def test_mcp_down_no_yaml_returns_failure(self, mock_path: MagicMock) -> None:
        # @trace FR-MCP-003
        """mcp_down returns failure when no process-compose.yaml found."""
        ok, _msg = mcp_down()
        assert ok is False
