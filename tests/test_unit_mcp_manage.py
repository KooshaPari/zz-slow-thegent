"""Unit tests for MCP configuration and service management."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import orjson as json
import pytest

from thegent.mcp.manage import (
    DEFAULT_MCP_URL,
    _ensure_mcp_servers,
    _get_mcp_url,
    _remote_config,
    install_to_claude_code,
    install_to_client,
    install_to_codex,
    install_to_cursor,
    install_to_droid,
    mcp_down,
    mcp_up,
    migrate_to_unimount,
    service_install,
    service_start,
    service_status,
    service_stop,
    service_uninstall,
)

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGetMcpUrl:
    """Tests for _get_mcp_url."""

    def test_default_url(self) -> None:
        # @trace FR-MCP-003
        """Default settings produce default MCP URL."""
        from thegent.config import ThegentSettings

        settings = ThegentSettings()
        url = _get_mcp_url(settings)
        assert url == "http://127.0.0.1:3847/mcp"

    def test_custom_host_and_port(self) -> None:
        # @trace FR-MCP-003
        """Custom host/port produce matching URL."""
        from thegent.config import ThegentSettings

        settings = ThegentSettings(mcp_host="0.0.0.0", mcp_port=9999)
        url = _get_mcp_url(settings)
        assert url == "http://0.0.0.0:9999/mcp"


@pytest.mark.unit
class TestRemoteConfig:
    """Tests for _remote_config."""

    def test_structure(self) -> None:
        # @trace FR-MCP-003
        """Remote config contains url, transport, and description."""
        cfg = _remote_config("http://localhost:3847/mcp")
        assert cfg["url"] == "http://localhost:3847/mcp"
        assert cfg["transport"] == "http"
        assert "description" in cfg
        assert isinstance(cfg["description"], str)

    def test_custom_url(self) -> None:
        # @trace FR-MCP-003
        """Custom URL is preserved in config."""
        cfg = _remote_config("http://10.0.0.1:8080/mcp")
        assert cfg["url"] == "http://10.0.0.1:8080/mcp"


@pytest.mark.unit
class TestEnsureMcpServers:
    """Tests for _ensure_mcp_servers."""

    def test_adds_missing_key(self) -> None:
        # @trace FR-MCP-003
        """Adds mcpServers key when missing."""
        config: dict = {"other": "data"}
        result = _ensure_mcp_servers(config)
        assert "mcpServers" in result
        assert result["mcpServers"] == {}

    def test_preserves_existing_key(self) -> None:
        # @trace FR-MCP-003
        """Does not overwrite existing mcpServers."""
        existing = {"existing": True}
        config: dict = {"mcpServers": existing}
        result = _ensure_mcp_servers(config)
        assert result["mcpServers"] is existing


# ---------------------------------------------------------------------------
# Install functions (file I/O with tmp_path)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestInstallToCursor:
    """Tests for install_to_cursor."""

    def test_creates_config_in_workspace(self, tmp_path: Path) -> None:
        # @trace FR-MCP-003
        """Creates .cursor/mcp.json in workspace directory."""
        result = install_to_cursor(url="http://test:1234/mcp", workspace=tmp_path)
        assert result is True
        config_path = tmp_path / ".cursor" / "mcp.json"
        assert config_path.exists()
        data = json.loads(config_path.read_text())
        assert data["mcpServers"]["thegent"]["url"] == "http://test:1234/mcp"
        assert data["mcpServers"]["codex_apps"]["url"] == "http://test:1234/mcp"

    def test_merges_with_existing_config(self, tmp_path: Path) -> None:
        # @trace FR-MCP-003
        """Merges thegent into existing config without clobbering other servers."""
        cursor_dir = tmp_path / ".cursor"
        cursor_dir.mkdir()
        existing = {"mcpServers": {"other-server": {"url": "http://other"}}}
        (cursor_dir / "mcp.json").write_text(json.dumps(existing).decode())

        install_to_cursor(url=DEFAULT_MCP_URL, workspace=tmp_path)

        data = json.loads((cursor_dir / "mcp.json").read_text())
        assert "other-server" in data["mcpServers"]
        assert "thegent" in data["mcpServers"]
        assert "codex_apps" in data["mcpServers"]

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        # @trace FR-MCP-003
        """Creates .cursor directory if it does not exist."""
        workspace = tmp_path / "nested" / "project"
        workspace.mkdir(parents=True)
        install_to_cursor(url=DEFAULT_MCP_URL, workspace=workspace)
        assert (workspace / ".cursor" / "mcp.json").exists()


@pytest.mark.unit
class TestInstallToCodex:
    """Tests for install_to_codex."""

    def test_creates_config(self, tmp_path: Path) -> None:
        # @trace FR-MCP-003
        """Creates codex MCP config at expected path."""
        codex_dir = tmp_path / ".codex"
        config_path = codex_dir / "mcp.json"
        with patch("thegent.mcp.manage.Path.home", return_value=tmp_path):
            install_to_codex(url="http://localhost:3847/mcp")
        assert config_path.exists()
        data = json.loads(config_path.read_text())
        assert "thegent" in data["mcpServers"]
        assert "codex_apps" in data["mcpServers"]


@pytest.mark.unit
class TestInstallToDroid:
    """Tests for install_to_droid."""

    def test_creates_factory_config(self, tmp_path: Path) -> None:
        # @trace FR-MCP-003
        """Creates .factory/mcp.json in workspace."""
        result = install_to_droid(url=DEFAULT_MCP_URL, workspace=tmp_path)
        assert result is True
        config_path = tmp_path / ".factory" / "mcp.json"
        assert config_path.exists()
        data = json.loads(config_path.read_text())
        assert data["mcpServers"]["thegent"]["url"] == DEFAULT_MCP_URL


@pytest.mark.unit
class TestInstallToClaudeCode:
    """Tests for install_to_claude_code."""

    def test_creates_config(self, tmp_path: Path) -> None:
        # @trace FR-MCP-003
        """Creates .claude.json at home directory."""
        with patch("thegent.mcp.manage.Path.home", return_value=tmp_path):
            result = install_to_claude_code(url="http://test:5555/mcp")
        assert result is True
        config_path = tmp_path / ".claude.json"
        assert config_path.exists()
        data = json.loads(config_path.read_text())
        assert data["mcpServers"]["thegent"]["url"] == "http://test:5555/mcp"

    def test_merges_existing(self, tmp_path: Path) -> None:
        # @trace FR-MCP-003
        """Merges into existing .claude.json config."""
        existing = {"mcpServers": {"existing": {"url": "http://x"}}, "other_key": 42}
        (tmp_path / ".claude.json").write_text(json.dumps(existing).decode())
        with patch("thegent.mcp.manage.Path.home", return_value=tmp_path):
            install_to_claude_code()
        data = json.loads((tmp_path / ".claude.json").read_text())
        assert "existing" in data["mcpServers"]
        assert "thegent" in data["mcpServers"]
        assert data["other_key"] == 42


# ---------------------------------------------------------------------------
# migrate_to_unimount
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestMigrateToUnimount:
    """Tests for migrate_to_unimount."""

    def test_preserves_other_servers(self, tmp_path: Path) -> None:
        """Migration updates only thegent aliases and preserves existing MCP entries."""
        existing = {
            "mcpServers": {
                "other-server": {"url": "http://old"},
                "legacy": {"url": "http://legacy"},
            },
            "other_key": 7,
        }
        codex_dir = tmp_path / ".codex"
        codex_dir.mkdir(parents=True, exist_ok=True)
        (codex_dir / "mcp.json").write_text(json.dumps(existing).decode())

        with patch("thegent.mcp.manage.Path.home", return_value=tmp_path):
            ok, msg = migrate_to_unimount(
                client="codex", mcp_url="http://127.0.0.1:3847/mcp"
            )

        assert ok is True
        assert "migrated" in msg.lower()

        data = json.loads((codex_dir / "mcp.json").read_text())
        assert "other-server" in data["mcpServers"]
        assert "legacy" in data["mcpServers"]
        assert data["mcpServers"]["thegent"]["url"] == "http://127.0.0.1:3847/mcp"
        assert data["mcpServers"]["codex_apps"]["url"] == "http://127.0.0.1:3847/mcp"
        assert data["other_key"] == 7


# ---------------------------------------------------------------------------
# install_to_client dispatcher
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestInstallToClient:
    """Tests for the install_to_client dispatcher."""

    def test_unknown_client(self) -> None:
        # @trace FR-MCP-003
        """Unknown client name returns failure."""
        ok, msg = install_to_client("nonexistent-client", DEFAULT_MCP_URL)
        assert ok is False
        assert "Unknown client" in msg

    def test_cursor_dispatch(self, tmp_path: Path) -> None:
        # @trace FR-MCP-003
        """Dispatches to cursor installer with workspace."""
        ok, msg = install_to_client("cursor", DEFAULT_MCP_URL, workspace=tmp_path)
        assert ok is True
        assert "cursor" in msg.lower()

    def test_droid_dispatch(self, tmp_path: Path) -> None:
        # @trace FR-MCP-003
        """Dispatches to droid installer with workspace."""
        ok, msg = install_to_client("droid", DEFAULT_MCP_URL, workspace=tmp_path)
        assert ok is True
        assert "droid" in msg.lower()

    def test_claude_code_dispatch(self, tmp_path: Path) -> None:
        # @trace FR-MCP-003
        """Dispatches to claude-code installer."""
        with patch("thegent.mcp.manage.Path.home", return_value=tmp_path):
            ok, msg = install_to_client("claude-code", DEFAULT_MCP_URL)
        assert ok is True
        assert "claude-code" in msg

    def test_handles_install_exception(self, tmp_path: Path) -> None:
        # @trace FR-MCP-003
        """Returns failure tuple when installer raises."""
        with patch(
            "thegent.mcp.manage.install_to_codex", side_effect=PermissionError("denied")
        ):
            ok, msg = install_to_client("codex", DEFAULT_MCP_URL)
        assert ok is False
        assert "denied" in msg


# ---------------------------------------------------------------------------
# Service management (launchd)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestServiceInstall:
    """Tests for service_install."""

    @patch("thegent.mcp.manage.platform.system", return_value="Linux")
    def test_non_macos_fails(self, mock_sys: MagicMock) -> None:
        # @trace FR-MCP-003
        """service_install fails on non-macOS."""
        ok, msg = service_install()
        assert ok is False
        assert "macOS" in msg

    @patch("thegent.mcp.manage.platform.system", return_value="Darwin")
    def test_macos_creates_plist(self, mock_sys: MagicMock, tmp_path: Path) -> None:
        # @trace FR-MCP-003
        """On macOS, creates plist and cache directory."""
        plist_path = tmp_path / "Library" / "LaunchAgents" / "com.thegent.mcp.plist"
        cache_dir = tmp_path / ".cache" / "thegent"
        with (
            patch("thegent.mcp.manage._launchd_plist_path", return_value=plist_path),
            patch("thegent.mcp.manage.Path.home", return_value=tmp_path),
        ):
            ok, _msg = service_install()
        assert ok is True
        assert plist_path.exists()
        assert "com.thegent.mcp" in plist_path.read_text()
        assert cache_dir.exists()


@pytest.mark.unit
class TestServiceStartStop:
    """Tests for service_start and service_stop."""

    @patch("thegent.mcp.manage.platform.system", return_value="Linux")
    def test_start_non_macos(self, mock_sys: MagicMock) -> None:
        # @trace FR-MCP-003
        """service_start fails on non-macOS."""
        ok, _msg = service_start()
        assert ok is False

    @patch("thegent.mcp.manage.platform.system", return_value="Linux")
    def test_stop_non_macos(self, mock_sys: MagicMock) -> None:
        # @trace FR-MCP-003
        """service_stop fails on non-macOS."""
        ok, _msg = service_stop()
        assert ok is False

    @patch("thegent.mcp.manage.platform.system", return_value="Darwin")
    def test_start_not_installed(self, mock_sys: MagicMock, tmp_path: Path) -> None:
        # @trace FR-MCP-003
        """service_start fails when plist does not exist."""
        plist = tmp_path / "nonexistent.plist"
        with patch("thegent.mcp.manage._launchd_plist_path", return_value=plist):
            ok, msg = service_start()
        assert ok is False
        assert "not installed" in msg.lower()

    @patch("thegent.mcp.manage.platform.system", return_value="Darwin")
    @patch("thegent.mcp.manage.subprocess.run")
    def test_stop_with_plist(
        self, mock_run: MagicMock, mock_sys: MagicMock, tmp_path: Path
    ) -> None:
        # @trace FR-MCP-003
        """service_stop calls launchctl unload when plist exists."""
        plist = tmp_path / "com.thegent.mcp.plist"
        plist.write_text("<plist/>")
        with patch("thegent.mcp.manage._launchd_plist_path", return_value=plist):
            ok, msg = service_stop()
        assert ok is True
        assert msg == "Stopped"
        mock_run.assert_called_once()


@pytest.mark.unit
class TestServiceUninstall:
    """Tests for service_uninstall."""

    @patch("thegent.mcp.manage.platform.system", return_value="Linux")
    def test_non_macos(self, mock_sys: MagicMock) -> None:
        # @trace FR-MCP-003
        """Fails on non-macOS."""
        ok, _msg = service_uninstall()
        assert ok is False

    @patch("thegent.mcp.manage.platform.system", return_value="Darwin")
    @patch("thegent.mcp.manage.subprocess.run")
    def test_removes_plist(
        self, mock_run: MagicMock, mock_sys: MagicMock, tmp_path: Path
    ) -> None:
        # @trace FR-MCP-003
        """Uninstall removes plist file."""
        plist = tmp_path / "com.thegent.mcp.plist"
        plist.write_text("<plist/>")
        with patch("thegent.mcp.manage._launchd_plist_path", return_value=plist):
            ok, _msg = service_uninstall()
        assert ok is True
        assert not plist.exists()


# ---------------------------------------------------------------------------
# Service status
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestServiceStatus:
    """Tests for service_status."""

    def test_healthy_service(self) -> None:
        # @trace FR-MCP-003
        """Returns running when HTTP health check succeeds."""
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            from thegent.config import ThegentSettings

            ok, msg = service_status(ThegentSettings())
        assert ok is True
        assert "Running" in msg

    @patch("thegent.mcp.manage.platform.system", return_value="Linux")
    def test_not_running_on_linux(self, mock_sys: MagicMock) -> None:
        # @trace FR-MCP-003
        """Non-macOS with failed HTTP returns not running."""
        with patch("urllib.request.urlopen", side_effect=Exception("refused")):
            from thegent.config import ThegentSettings

            ok, msg = service_status(ThegentSettings())
        assert ok is False
        assert "Not running" in msg


# ---------------------------------------------------------------------------
# Process-compose (mcp_up / mcp_down)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestMcpUp:
    """Tests for mcp_up."""

    @patch("thegent.mcp.manage._process_compose_path", return_value=None)
    def test_no_compose_file(self, mock_path: MagicMock) -> None:
        # @trace FR-MCP-003
        """Returns failure when process-compose.yaml not found."""
        ok, msg = mcp_up()
        assert ok is False
        assert "not found" in msg.lower()

    @patch("thegent.mcp.manage.shutil.which", return_value=None)
    @patch("thegent.mcp.manage._process_compose_path")
    def test_no_process_compose_binary(
        self, mock_path: MagicMock, mock_which: MagicMock, tmp_path: Path
    ) -> None:
        # @trace FR-MCP-003
        """Returns failure when process-compose binary not installed."""
        pc_file = tmp_path / "process-compose.yaml"
        pc_file.write_text("version: '0.5'")
        mock_path.return_value = pc_file
        ok, msg = mcp_up()
        assert ok is False
        assert "not installed" in msg.lower()


@pytest.mark.unit
class TestMcpDown:
    """Tests for mcp_down."""

    @patch("thegent.mcp.manage._process_compose_path", return_value=None)
    def test_no_compose_file(self, mock_path: MagicMock) -> None:
        # @trace FR-MCP-003
        """Returns failure when process-compose.yaml not found."""
        ok, msg = mcp_down()
        assert ok is False
        assert "not found" in msg.lower()

    @patch("thegent.mcp.manage.shutil.which", return_value=None)
    @patch("thegent.mcp.manage._process_compose_path")
    def test_no_process_compose_binary(
        self, mock_path: MagicMock, mock_which: MagicMock, tmp_path: Path
    ) -> None:
        # @trace FR-MCP-003
        """Returns failure when process-compose binary not installed."""
        pc_file = tmp_path / "process-compose.yaml"
        pc_file.write_text("version: '0.5'")
        mock_path.return_value = pc_file
        ok, msg = mcp_down()
        assert ok is False
        assert "not installed" in msg.lower()
