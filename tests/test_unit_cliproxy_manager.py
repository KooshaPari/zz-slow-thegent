"""Unit tests for cliproxy_manager (CLIProxyAPIPlus lifecycle, login flows)."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from thegent.agents.cliproxy_manager import (
    _LOGIN_FLAGS,
    _binary_available,
    _load_json,
    ensure_proxy_running,
    run_login,
    run_login_unified,
    start_proxy_managed,
)
from thegent.config import ThegentSettings


@pytest.mark.unit
class TestLoginFlags:
    """Tests for login flag coverage."""

    def test_cliproxy_providers_have_flags(self) -> None:
        # @trace FR-AGT-006
        """All providers (including roo, kilo) use CLIProxy -login flags."""
        assert "claude" in _LOGIN_FLAGS
        assert _LOGIN_FLAGS["claude"] == "-claude-login"
        assert "gemini" in _LOGIN_FLAGS
        assert _LOGIN_FLAGS["gemini"] == "-login"
        assert "roo" in _LOGIN_FLAGS
        assert _LOGIN_FLAGS["roo"] == "-roo-login"
        assert "kilo" in _LOGIN_FLAGS
        assert _LOGIN_FLAGS["kilo"] == "-kilo-login"

    def test_all_providers_covered(self) -> None:
        # @trace FR-AGT-006
        """Full provider set includes roo, kilo, claude, glm, minimax, kiro variants."""
        assert "roo" in _LOGIN_FLAGS
        assert "kilo" in _LOGIN_FLAGS
        assert "claude" in _LOGIN_FLAGS
        assert "glm" in _LOGIN_FLAGS
        assert _LOGIN_FLAGS["glm"] == "-iflow-login"
        assert "minimax" in _LOGIN_FLAGS
        assert _LOGIN_FLAGS["minimax"] == "-minimax-login"
        assert "kiro-aws" in _LOGIN_FLAGS


@pytest.mark.unit
class TestBinaryAvailable:
    """Tests for _binary_available."""

    def test_returns_true_when_path_exists(self, tmp_path: Path) -> None:
        # @trace FR-AGT-006
        """Returns True when binary path exists."""
        (tmp_path / "bin").touch()
        assert _binary_available(str(tmp_path / "bin")) is True

    @patch("thegent.agents.cliproxy_manager.shutil.which")
    def test_returns_true_when_on_path(self, mock_which: MagicMock) -> None:
        # @trace FR-AGT-006
        """Returns True when binary on PATH."""
        mock_which.return_value = "/usr/bin/foo"
        assert _binary_available("foo") is True

    def test_returns_false_when_missing(self) -> None:
        # @trace FR-AGT-006
        """Returns False when path does not exist and not on PATH."""
        with patch("thegent.agents.cliproxy_manager.shutil.which", return_value=None):
            assert _binary_available("/nonexistent/path/xyz") is False


@pytest.mark.unit
class TestRunLogin:
    """Tests for run_login."""

    def test_unknown_provider_raises(self) -> None:
        # @trace FR-AGT-006
        """Unknown provider raises ValueError."""
        settings = ThegentSettings()
        with pytest.raises(ValueError, match="Unknown provider"):
            run_login(settings, "unknown-xyz")

    @patch("thegent.agents.cliproxy_manager._resolve_binary")
    @patch("thegent.agents.cliproxy_manager._ensure_config")
    @patch("thegent.agents.cliproxy_manager.subprocess.run")
    def test_roo_login_invokes_cliproxy(
        self,
        mock_run: MagicMock,
        mock_ensure: MagicMock,
        mock_resolve: MagicMock,
        tmp_path: Path,
    ) -> None:
        # @trace FR-AGT-006
        """run_login roo passes -roo-login to CLIProxy binary."""
        fake_binary = tmp_path / "cli-proxy-api-plus"
        fake_binary.touch()
        mock_resolve.return_value = str(fake_binary)
        mock_ensure.return_value = tmp_path / "config.yaml"
        mock_run.return_value = MagicMock(returncode=0)

        settings = ThegentSettings()
        rc = run_login(settings, "roo")

        assert rc == 0
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert str(fake_binary) in cmd or "cli-proxy-api-plus" in str(cmd)
        assert "-config" in cmd
        assert "-roo-login" in cmd

    @patch("thegent.agents.cliproxy_manager._resolve_binary")
    @patch("thegent.agents.cliproxy_manager._ensure_config")
    @patch("thegent.agents.cliproxy_manager.subprocess.run")
    def test_kilo_login_invokes_cliproxy(
        self,
        mock_run: MagicMock,
        mock_ensure: MagicMock,
        mock_resolve: MagicMock,
        tmp_path: Path,
    ) -> None:
        # @trace FR-AGT-006
        """run_login kilo passes -kilo-login to CLIProxy binary."""
        fake_binary = tmp_path / "cli-proxy-api-plus"
        fake_binary.touch()
        mock_resolve.return_value = str(fake_binary)
        mock_ensure.return_value = tmp_path / "config.yaml"
        mock_run.return_value = MagicMock(returncode=0)

        settings = ThegentSettings()
        rc = run_login(settings, "kilo")

        assert rc == 0
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "-kilo-login" in cmd

    @patch("thegent.agents.cliproxy_manager._resolve_binary")
    @patch("thegent.agents.cliproxy_manager._ensure_config")
    @patch("thegent.agents.cliproxy_manager.subprocess.run")
    def test_claude_login_invokes_cliproxy(
        self,
        mock_run: MagicMock,
        mock_ensure: MagicMock,
        mock_resolve: MagicMock,
        tmp_path: Path,
    ) -> None:
        # @trace FR-AGT-006
        """run_login claude passes -claude-login to CLIProxy binary."""
        fake_binary = tmp_path / "cli-proxy-api-plus"
        fake_binary.touch()
        mock_resolve.return_value = str(fake_binary)
        mock_ensure.return_value = tmp_path / "config.yaml"
        mock_run.return_value = MagicMock(returncode=0)

        settings = ThegentSettings()
        rc = run_login(settings, "claude")

        assert rc == 0
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert str(fake_binary) in cmd or "cli-proxy-api-plus" in str(cmd)
        assert "-config" in cmd
        assert "-claude-login" in cmd


@pytest.mark.unit
class TestRunLoginUnified:
    """Tests for run_login_unified behavior."""

    @patch("thegent.agents.cliproxy_manager.kill_proxy", return_value=False)
    @patch("thegent.agents.cliproxy_manager._inject_api_key_into_cliproxy")
    @patch("thegent.agents.cliproxy_manager._get_factory_api_key")
    @patch("thegent.agents.cliproxy_manager._has_provider_credentials", return_value=False)
    @patch("thegent.agents.cliproxy_manager._ensure_config")
    def test_run_login_unified_uses_factory_key_when_configured(
        self,
        mock_ensure: MagicMock,
        mock_has_credentials: MagicMock,
        mock_factory: MagicMock,
        mock_inject: MagicMock,
        mock_kill: MagicMock,
        tmp_path: Path,
    ) -> None:
        # @trace FR-AGT-006
        """run_login_unified reuses factory API key when skip_if_configured is true."""
        config_path = tmp_path / "cliproxy-config.yaml"
        config_path.write_text("port: 8317")
        mock_ensure.return_value = config_path
        mock_factory.return_value = ("abc", "/tmp/factory.json")

        rc = run_login_unified(ThegentSettings(), "roo")

        assert rc == 0
        mock_inject.assert_called_once()
        mock_kill.assert_called_once()

    @patch("thegent.agents.cliproxy_manager.webbrowser.open", return_value=True)
    @patch("thegent.agents.cliproxy_manager._inject_api_key_into_cliproxy")
    @patch("thegent.agents.cliproxy_manager._get_factory_api_key")
    @patch("thegent.agents.cliproxy_manager._has_provider_credentials", return_value=False)
    @patch("thegent.agents.cliproxy_manager._ensure_config")
    def test_run_login_unified_returns_skip_when_no_key(
        self,
        mock_ensure: MagicMock,
        mock_has_credentials: MagicMock,
        mock_factory: MagicMock,
        mock_inject: MagicMock,
        mock_web_open: MagicMock,
        tmp_path: Path,
    ) -> None:
        # @trace FR-AGT-006
        """run_login_unified returns 1 when user skips API key entry."""
        config_path = tmp_path / "cliproxy-config.yaml"
        config_path.write_text("port: 8317")
        mock_ensure.return_value = config_path
        mock_factory.return_value = (None, None)

        rc = run_login_unified(ThegentSettings(), "roo", prompt_func=lambda prompt: "")

        assert rc == 1
        mock_inject.assert_not_called()
        mock_web_open.assert_called_once()


@pytest.mark.unit
class TestEnsureProxyRunning:
    """Tests for ensure_proxy_running."""

    @patch("thegent.agents.cliproxy_manager._is_proxy_reachable")
    def test_returns_base_url_when_already_reachable(self, mock_reachable: MagicMock) -> None:
        # @trace FR-AGT-006
        """Skips start when proxy already running."""
        mock_reachable.return_value = True
        settings = ThegentSettings()
        base_url = ensure_proxy_running(settings)
        assert base_url == f"http://127.0.0.1:{settings.cliproxy_port}/v1"
        mock_reachable.assert_called()

    @patch("thegent.agents.cliproxy_manager._is_proxy_reachable")
    @patch("thegent.agents.cliproxy_manager._resolve_binary")
    @patch("thegent.agents.cliproxy_manager._ensure_config")
    @patch("thegent.agents.cliproxy_manager.subprocess.Popen")
    def test_starts_proxy_when_not_reachable(
        self,
        mock_popen: MagicMock,
        mock_ensure: MagicMock,
        mock_resolve: MagicMock,
        mock_reachable: MagicMock,
        tmp_path: Path,
    ) -> None:
        # @trace FR-AGT-006
        """Starts proxy when not reachable."""
        fake_binary = tmp_path / "cli-proxy-api-plus"
        fake_binary.touch()
        mock_reachable.side_effect = [False, True]  # first check fails, second succeeds
        mock_resolve.return_value = str(fake_binary)
        mock_ensure.return_value = tmp_path / "config.yaml"
        mock_popen.return_value = MagicMock(poll=MagicMock(return_value=None))

        settings = ThegentSettings()
        base_url = ensure_proxy_running(settings)

        assert base_url == f"http://127.0.0.1:{settings.cliproxy_port}/v1"
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args[0][0]
        assert "-config" in call_args
        assert str(tmp_path / "config.yaml") in call_args


@pytest.mark.unit
class TestStartProxyManaged:
    """Tests for start_proxy_managed."""

    @patch("thegent.agents.cliproxy_manager._is_proxy_reachable")
    def test_returns_none_proc_when_already_reachable(self, mock_reachable: MagicMock) -> None:
        # @trace FR-AGT-006
        """Returns (None, base_url) when proxy already running."""
        mock_reachable.return_value = True
        settings = ThegentSettings()
        proc, base_url = start_proxy_managed(settings)
        assert proc is None
        assert base_url == f"http://127.0.0.1:{settings.cliproxy_port}/v1"

    @patch("thegent.agents.cliproxy_manager._is_proxy_reachable")
    @patch("thegent.agents.cliproxy_manager._resolve_binary")
    @patch("thegent.agents.cliproxy_manager._ensure_config")
    @patch("thegent.agents.cliproxy_manager.subprocess.Popen")
    def test_returns_proc_when_started(
        self,
        mock_popen: MagicMock,
        mock_ensure: MagicMock,
        mock_resolve: MagicMock,
        mock_reachable: MagicMock,
        tmp_path: Path,
    ) -> None:
        # @trace FR-AGT-006
        """Returns (proc, base_url) when proxy is started."""
        fake_binary = tmp_path / "cli-proxy-api-plus"
        fake_binary.touch()
        mock_reachable.side_effect = [False, True]
        mock_resolve.return_value = str(fake_binary)
        mock_ensure.return_value = tmp_path / "config.yaml"
        mock_proc = MagicMock(poll=MagicMock(return_value=None))
        mock_popen.return_value = mock_proc

        settings = ThegentSettings()
        proc, base_url = start_proxy_managed(settings)

        assert proc is mock_proc
        assert base_url == f"http://127.0.0.1:{settings.cliproxy_port}/v1"


@pytest.mark.unit
class TestStartProxyAndWait:
    """Tests for _start_proxy_and_wait startup flow and timeout handling."""

    @patch("thegent.agents.cliproxy_manager._is_proxy_reachable")
    @patch("thegent.agents.cliproxy_manager.subprocess.Popen")
    @patch("thegent.agents.cliproxy_manager.time.sleep")
    def test_start_proxy_and_wait_success(
        self,
        mock_sleep: MagicMock,
        mock_popen: MagicMock,
        mock_reachable: MagicMock,
        tmp_path: Path,
    ) -> None:
        # @trace FR-AGT-006
        """Returns proc when proxy becomes reachable after startup."""
        from thegent.agents.cliproxy_manager import _start_proxy_and_wait

        mock_proc = MagicMock(poll=MagicMock(return_value=None))
        mock_popen.return_value = mock_proc
        mock_reachable.return_value = True  # reachable on first check

        settings = ThegentSettings()
        config_path = tmp_path / "config.yaml"
        binary = str(tmp_path / "bin")

        proc = _start_proxy_and_wait(binary, config_path, "http://127.0.0.1:8317/v1", settings)
        assert proc is mock_proc

    @patch("thegent.agents.cliproxy_manager._is_proxy_reachable")
    @patch("thegent.agents.cliproxy_manager.subprocess.Popen")
    @patch("thegent.agents.cliproxy_manager.time.sleep")
    def test_start_proxy_and_wait_process_exits_immediately(
        self,
        mock_sleep: MagicMock,
        mock_popen: MagicMock,
        mock_reachable: MagicMock,
        tmp_path: Path,
    ) -> None:
        # @trace FR-AGT-006
        """Raises RuntimeError when proxy process exits immediately."""
        from thegent.agents.cliproxy_manager import _start_proxy_and_wait

        mock_proc = MagicMock(poll=MagicMock(return_value=1), returncode=1)
        mock_popen.return_value = mock_proc
        mock_reachable.return_value = False

        settings = ThegentSettings()
        config_path = tmp_path / "config.yaml"
        binary = str(tmp_path / "bin")

        with pytest.raises(RuntimeError, match="exited with code"):
            _start_proxy_and_wait(binary, config_path, "http://127.0.0.1:8317/v1", settings)

    @patch("thegent.agents.cliproxy_manager._is_proxy_reachable")
    @patch("thegent.agents.cliproxy_manager.subprocess.Popen")
    @patch("thegent.agents.cliproxy_manager.time.sleep")
    def test_start_proxy_and_wait_timeout(
        self,
        mock_sleep: MagicMock,
        mock_popen: MagicMock,
        mock_reachable: MagicMock,
        tmp_path: Path,
    ) -> None:
        # @trace FR-AGT-006
        """Raises RuntimeError and kills proc when proxy never becomes reachable."""
        from thegent.agents.cliproxy_manager import _start_proxy_and_wait

        mock_proc = MagicMock(poll=MagicMock(return_value=None))
        mock_popen.return_value = mock_proc
        mock_reachable.return_value = False  # never reachable

        settings = ThegentSettings()
        config_path = tmp_path / "config.yaml"
        binary = str(tmp_path / "bin")

        with pytest.raises(RuntimeError, match="did not become ready"):
            _start_proxy_and_wait(binary, config_path, "http://127.0.0.1:8317/v1", settings)
        mock_proc.kill.assert_called_once()


@pytest.mark.unit
class TestIsProxyReachable:
    """Tests for _is_proxy_reachable health check."""

    @patch("urllib.request.urlopen")
    def test_reachable_on_v1_models(self, mock_urlopen: MagicMock) -> None:
        # @trace FR-AGT-006
        """Returns True when /v1/models responds successfully."""
        from thegent.agents.cliproxy_manager import _is_proxy_reachable

        mock_urlopen.return_value.__enter__ = MagicMock(return_value=MagicMock())
        mock_urlopen.return_value.__exit__ = MagicMock(return_value=False)
        assert _is_proxy_reachable("http://127.0.0.1:8317") is True

    @patch("urllib.request.urlopen", side_effect=OSError("refused"))
    def test_unreachable_returns_false(self, mock_urlopen: MagicMock) -> None:
        # @trace FR-AGT-006
        """Returns False when both endpoints fail."""
        from thegent.agents.cliproxy_manager import _is_proxy_reachable

        assert _is_proxy_reachable("http://127.0.0.1:99999") is False


@pytest.mark.unit
class TestRunLoginAdditionalProviders:
    """Additional tests for run_login covering more providers."""

    @patch("thegent.agents.cliproxy_manager._resolve_binary")
    @patch("thegent.agents.cliproxy_manager._binary_available")
    @patch("thegent.agents.cliproxy_manager._ensure_config")
    @patch("thegent.agents.cliproxy_manager.subprocess.run")
    def test_gemini_login(
        self,
        mock_run: MagicMock,
        mock_ensure: MagicMock,
        mock_avail: MagicMock,
        mock_resolve: MagicMock,
        tmp_path: Path,
    ) -> None:
        # @trace FR-AGT-006
        """run_login gemini passes -login flag."""
        mock_resolve.return_value = "/usr/bin/cli-proxy-api-plus"
        mock_avail.return_value = True
        mock_ensure.return_value = tmp_path / "config.yaml"
        mock_run.return_value = MagicMock(returncode=0)

        rc = run_login(ThegentSettings(), "gemini")
        assert rc == 0
        cmd = mock_run.call_args[0][0]
        assert "-login" in cmd

    @patch("thegent.agents.cliproxy_manager._resolve_binary")
    @patch("thegent.agents.cliproxy_manager._binary_available")
    @patch("thegent.agents.cliproxy_manager._ensure_config")
    @patch("thegent.agents.cliproxy_manager.subprocess.run")
    @patch("thegent.agents.cliproxy_manager.sys.stdin.isatty")
    def test_minimax_login_requires_tty(
        self,
        mock_isatty: MagicMock,
        mock_run: MagicMock,
        mock_ensure: MagicMock,
        mock_avail: MagicMock,
        mock_resolve: MagicMock,
        tmp_path: Path,
    ) -> None:
        """minimax login exits with code 2 when stdin is non-interactive."""
        mock_resolve.return_value = "/usr/bin/cli-proxy-api-plus"
        mock_avail.return_value = True
        mock_ensure.return_value = tmp_path / "config.yaml"
        mock_isatty.return_value = False

        rc = run_login(ThegentSettings(), "minimax")
        assert rc == 2
        mock_run.assert_not_called()

    @patch("thegent.agents.cliproxy_manager._resolve_binary")
    @patch("thegent.agents.cliproxy_manager._binary_available")
    @patch("thegent.agents.cliproxy_manager._ensure_config")
    @patch("thegent.agents.cliproxy_manager.subprocess.run")
    @patch("thegent.agents.cliproxy_manager.sys.stdin.isatty")
    def test_minimax_login_uses_interactive_stdio(
        self,
        mock_isatty: MagicMock,
        mock_run: MagicMock,
        mock_ensure: MagicMock,
        mock_avail: MagicMock,
        mock_resolve: MagicMock,
        tmp_path: Path,
    ) -> None:
        """minimax login streams stdio and honors timeout override."""
        mock_resolve.return_value = "/usr/bin/cli-proxy-api-plus"
        mock_avail.return_value = True
        mock_ensure.return_value = tmp_path / "config.yaml"
        mock_isatty.return_value = True
        mock_run.return_value = MagicMock(returncode=0)

        rc = run_login(ThegentSettings(), "minimax", login_timeout=7)
        assert rc == 0
        kwargs = mock_run.call_args.kwargs
        assert kwargs["timeout"] == 7
        assert "capture_output" not in kwargs
        assert kwargs["stdin"] is not None
        assert kwargs["stdout"] is not None
        assert kwargs["stderr"] is not None

    @patch("thegent.agents.cliproxy_manager.run_login_unified")
    def test_qwen_login_uses_api_key_flow(self, mock_unified: MagicMock) -> None:
        """CLIP-BUG-08: qwen login should use unified API-key flow, not OAuth flag."""
        mock_unified.return_value = 0

        rc = run_login(ThegentSettings(), "qwen")

        assert rc == 0
        mock_unified.assert_called_once()

    @patch("thegent.agents.cliproxy_manager._resolve_binary")
    @patch("thegent.agents.cliproxy_manager._binary_available")
    def test_login_binary_not_found_raises(
        self,
        mock_avail: MagicMock,
        mock_resolve: MagicMock,
    ) -> None:
        # @trace FR-AGT-006
        """run_login raises FileNotFoundError when binary not available."""
        mock_resolve.return_value = "/nonexistent/cli-proxy-api-plus"
        mock_avail.return_value = False

        with pytest.raises(FileNotFoundError, match="cli-proxy-api-plus not found"):
            run_login(ThegentSettings(), "claude")

    @patch("thegent.agents.cliproxy_manager._resolve_binary")
    @patch("thegent.agents.cliproxy_manager._binary_available")
    @patch("thegent.agents.cliproxy_manager._ensure_config")
    @patch("thegent.agents.cliproxy_manager.subprocess.run")
    def test_login_returns_nonzero_exit_code(
        self,
        mock_run: MagicMock,
        mock_ensure: MagicMock,
        mock_avail: MagicMock,
        mock_resolve: MagicMock,
        tmp_path: Path,
    ) -> None:
        # @trace FR-AGT-006
        """run_login returns nonzero exit code on failure."""
        mock_resolve.return_value = "/usr/bin/cli-proxy-api-plus"
        mock_avail.return_value = True
        mock_ensure.return_value = tmp_path / "config.yaml"
        mock_run.return_value = MagicMock(returncode=1)

        rc = run_login(ThegentSettings(), "copilot")
        assert rc == 1


@pytest.mark.unit
class TestStartProxyManagedBinaryNotFound:
    """Tests for start_proxy_managed when binary is not available."""

    @patch("thegent.agents.cliproxy_manager._is_proxy_reachable")
    @patch("thegent.agents.cliproxy_manager._resolve_binary")
    @patch("thegent.agents.cliproxy_manager._binary_available")
    def test_raises_file_not_found(
        self,
        mock_avail: MagicMock,
        mock_resolve: MagicMock,
        mock_reachable: MagicMock,
    ) -> None:
        # @trace FR-AGT-006
        """start_proxy_managed raises FileNotFoundError when binary missing."""
        mock_reachable.return_value = False
        mock_resolve.return_value = "/nonexistent/bin"
        mock_avail.return_value = False

        with pytest.raises(FileNotFoundError, match="cli-proxy-api-plus not found"):
            start_proxy_managed(ThegentSettings())


@pytest.mark.unit
class TestEnsureConfig:
    """Tests for _ensure_config - config file creation and reading."""

    def test_creates_config_when_missing(self, tmp_path: Path) -> None:
        # @trace FR-AGT-006
        """Creates minimal YAML config when no config file exists."""
        from thegent.agents.cliproxy_manager import _ensure_config

        config_dir = tmp_path / "config"
        config_file = config_dir / "cliproxy-config.yaml"
        auth_dir = tmp_path / "auth"

        settings = ThegentSettings(
            cliproxy_config_path=config_file,
            cliproxy_auth_dir=auth_dir,
            cliproxy_port=9999,
        )
        result = _ensure_config(settings)

        assert result == config_file.resolve()
        assert config_file.exists()
        import yaml

        data = yaml.safe_load(config_file.read_text())
        assert data["port"] == 9999
        assert data["auth-dir"] == str(auth_dir.resolve())

    def test_reads_existing_config_and_preserves_values(self, tmp_path: Path) -> None:
        # @trace FR-AGT-006
        """Reads existing config and preserves user-defined keys."""
        import yaml

        from thegent.agents.cliproxy_manager import _ensure_config

        config_file = tmp_path / "cliproxy-config.yaml"
        auth_dir = tmp_path / "auth"
        auth_dir.mkdir()
        existing = {"port": 7777, "custom-key": "user-value"}
        config_file.write_text(yaml.dump(existing))

        settings = ThegentSettings(
            cliproxy_config_path=config_file,
            cliproxy_auth_dir=auth_dir,
            cliproxy_port=9999,
        )
        _ensure_config(settings)

        data = yaml.safe_load(config_file.read_text())
        assert data["port"] == 7777  # setdefault preserves existing
        assert data["custom-key"] == "user-value"

    def test_handles_corrupt_yaml(self, tmp_path: Path) -> None:
        # @trace FR-AGT-006
        """Handles corrupt YAML by starting with empty config."""
        from thegent.agents.cliproxy_manager import _ensure_config

        config_file = tmp_path / "cliproxy-config.yaml"
        auth_dir = tmp_path / "auth"
        config_file.write_text(": : invalid yaml [[[")

        settings = ThegentSettings(
            cliproxy_config_path=config_file,
            cliproxy_auth_dir=auth_dir,
            cliproxy_port=8317,
        )
        result = _ensure_config(settings)
        assert result.exists()

        import yaml

        data = yaml.safe_load(config_file.read_text())
        assert data["port"] == 8317

    def test_creates_auth_dir(self, tmp_path: Path) -> None:
        # @trace FR-AGT-006
        """Creates auth directory if it does not exist."""
        from thegent.agents.cliproxy_manager import _ensure_config

        config_file = tmp_path / "cfg" / "config.yaml"
        auth_dir = tmp_path / "new-auth-dir"

        settings = ThegentSettings(
            cliproxy_config_path=config_file,
            cliproxy_auth_dir=auth_dir,
        )
        _ensure_config(settings)
        assert auth_dir.resolve().exists()

    def test_empty_yaml_file_treated_as_empty_dict(self, tmp_path: Path) -> None:
        # @trace FR-AGT-006
        """Empty YAML file (loads as None) treated as empty config."""
        from thegent.agents.cliproxy_manager import _ensure_config

        config_file = tmp_path / "config.yaml"
        auth_dir = tmp_path / "auth"
        config_file.write_text("")  # yaml.safe_load returns None

        settings = ThegentSettings(
            cliproxy_config_path=config_file,
            cliproxy_auth_dir=auth_dir,
            cliproxy_port=8317,
        )
        _ensure_config(settings)

        import yaml

        data = yaml.safe_load(config_file.read_text())
        assert data["port"] == 8317


@pytest.mark.unit
class TestResolveBinary:
    """Tests for _resolve_binary - binary path resolution logic."""

    def test_env_override_existing_file(self, tmp_path: Path) -> None:
        # @trace FR-AGT-006
        """THGENT_CLIPROXY_BINARY env var with existing file returns expanded path."""
        from thegent.agents.cliproxy_manager import _resolve_binary

        fake_bin = tmp_path / "cli-proxy-api-plus"
        fake_bin.touch()

        with patch.dict("os.environ", {"THGENT_CLIPROXY_BINARY": str(fake_bin)}):
            result = _resolve_binary(ThegentSettings())
        assert result == str(fake_bin)

    def test_env_override_nonexistent_returns_value(self) -> None:
        # @trace FR-AGT-006
        """THGENT_CLIPROXY_BINARY env with non-existent path returns the raw value."""
        from thegent.agents.cliproxy_manager import _resolve_binary

        with patch.dict("os.environ", {"THGENT_CLIPROXY_BINARY": "/no/such/binary"}):
            result = _resolve_binary(ThegentSettings())
        assert result == "/no/such/binary"

    def test_absolute_path_in_settings_existing(self, tmp_path: Path) -> None:
        # @trace FR-AGT-006
        """Absolute path in settings that exists returns expanded path."""
        from thegent.agents.cliproxy_manager import _resolve_binary

        fake_bin = tmp_path / "proxy"
        fake_bin.touch()
        settings = ThegentSettings(cliproxy_binary=str(fake_bin))

        with patch.dict("os.environ", {}, clear=False):
            # Ensure no env override
            import os

            os.environ.pop("THGENT_CLIPROXY_BINARY", None)
            result = _resolve_binary(settings)
        assert result == str(fake_bin)

    @patch("thegent.agents.cliproxy_manager.shutil.which")
    def test_which_finds_on_path(self, mock_which: MagicMock) -> None:
        # @trace FR-AGT-006
        """Falls back to shutil.which when cmd is a simple name."""
        from thegent.agents.cliproxy_manager import _resolve_binary

        mock_which.return_value = "/usr/local/bin/cli-proxy-api-plus"
        with patch.dict("os.environ", {}, clear=False):
            import os

            os.environ.pop("THGENT_CLIPROXY_BINARY", None)
            result = _resolve_binary(ThegentSettings())
        assert result == "/usr/local/bin/cli-proxy-api-plus"

    @patch("thegent.agents.cliproxy_manager.shutil.which", return_value=None)
    def test_local_bin_fallback(self, mock_which: MagicMock, tmp_path: Path) -> None:
        # @trace FR-AGT-006
        """Falls back to ~/.local/bin/<cmd> when which fails."""
        from thegent.agents.cliproxy_manager import _resolve_binary

        local_bin = tmp_path / ".local" / "bin" / "cli-proxy-api-plus"
        local_bin.parent.mkdir(parents=True)
        local_bin.touch()

        with (
            patch.dict("os.environ", {}, clear=False),
            patch("thegent.agents.cliproxy_manager.Path.home", return_value=tmp_path),
        ):
            import os

            os.environ.pop("THGENT_CLIPROXY_BINARY", None)
            result = _resolve_binary(ThegentSettings())
        assert result == str(local_bin)

    @patch("thegent.agents.cliproxy_manager.shutil.which", return_value=None)
    def test_returns_cmd_name_when_nothing_found(self, mock_which: MagicMock, tmp_path: Path) -> None:
        # @trace FR-AGT-006
        """Returns bare command name when no resolution succeeds."""
        from thegent.agents.cliproxy_manager import _resolve_binary

        with (
            patch.dict("os.environ", {}, clear=False),
            patch("thegent.agents.cliproxy_manager.Path.home", return_value=tmp_path),
        ):
            import os

            os.environ.pop("THGENT_CLIPROXY_BINARY", None)
            result = _resolve_binary(ThegentSettings())
        assert result == "cli-proxy-api-plus"


@pytest.mark.unit
class TestEnsureProxyRunningBinaryNotFound:
    """Tests for ensure_proxy_running when binary is not available."""

    @patch("thegent.agents.cliproxy_manager._is_proxy_reachable")
    @patch("thegent.agents.cliproxy_manager._resolve_binary")
    @patch("thegent.agents.cliproxy_manager._binary_available")
    def test_raises_file_not_found_error(
        self,
        mock_avail: MagicMock,
        mock_resolve: MagicMock,
        mock_reachable: MagicMock,
    ) -> None:
        # @trace FR-AGT-006
        """ensure_proxy_running raises FileNotFoundError when binary not available."""
        mock_reachable.return_value = False
        mock_resolve.return_value = "/nonexistent"
        mock_avail.return_value = False

        with pytest.raises(FileNotFoundError, match="cli-proxy-api-plus not found"):
            ensure_proxy_running(ThegentSettings())


@pytest.mark.unit
class TestStartProxyAndWaitPortInUse:
    """Tests for _start_proxy_and_wait timeout indicating port in use."""

    @patch("thegent.agents.cliproxy_manager._is_proxy_reachable")
    @patch("thegent.agents.cliproxy_manager.subprocess.Popen")
    @patch("thegent.agents.cliproxy_manager.time.sleep")
    def test_timeout_message_mentions_port(
        self,
        mock_sleep: MagicMock,
        mock_popen: MagicMock,
        mock_reachable: MagicMock,
        tmp_path: Path,
    ) -> None:
        # @trace FR-AGT-006
        """Timeout RuntimeError message mentions port may be in use."""
        from thegent.agents.cliproxy_manager import _start_proxy_and_wait

        mock_proc = MagicMock(poll=MagicMock(return_value=None))
        mock_popen.return_value = mock_proc
        mock_reachable.return_value = False

        settings = ThegentSettings(cliproxy_port=9876)
        config_path = tmp_path / "config.yaml"

        with pytest.raises(RuntimeError, match="9876"):
            _start_proxy_and_wait(str(tmp_path / "bin"), config_path, "http://127.0.0.1:9876/v1", settings)


@pytest.mark.unit
class TestStartProxyManagedFullLifecycle:
    """Tests for start_proxy_managed full lifecycle with health check polling."""

    @patch("thegent.agents.cliproxy_manager._is_proxy_reachable")
    @patch("thegent.agents.cliproxy_manager._resolve_binary")
    @patch("thegent.agents.cliproxy_manager._binary_available")
    @patch("thegent.agents.cliproxy_manager._ensure_config")
    @patch("thegent.agents.cliproxy_manager.subprocess.Popen")
    @patch("thegent.agents.cliproxy_manager.time.sleep")
    def test_full_lifecycle_delayed_ready(
        self,
        mock_sleep: MagicMock,
        mock_popen: MagicMock,
        mock_ensure: MagicMock,
        mock_avail: MagicMock,
        mock_resolve: MagicMock,
        mock_reachable: MagicMock,
        tmp_path: Path,
    ) -> None:
        # @trace FR-AGT-006
        """start_proxy_managed polls until proxy becomes reachable."""
        fake_binary = tmp_path / "cli-proxy-api-plus"
        fake_binary.touch()
        # First call from start_proxy_managed check, then 2 fails in wait loop, then success
        mock_reachable.side_effect = [False, False, False, True]
        mock_resolve.return_value = str(fake_binary)
        mock_avail.return_value = True
        mock_ensure.return_value = tmp_path / "config.yaml"
        mock_proc = MagicMock(poll=MagicMock(return_value=None))
        mock_popen.return_value = mock_proc

        settings = ThegentSettings()
        proc, base_url = start_proxy_managed(settings)

        assert proc is mock_proc
        assert base_url == f"http://127.0.0.1:{settings.cliproxy_port}/v1"
        assert mock_sleep.call_count >= 2


@pytest.mark.unit
class TestProviderDefinitionJsonLoading:
    """Validation coverage for cliproxy provider definition JSON loading."""

    def test_load_json_returns_mapping_for_valid_object(self, tmp_path: Path) -> None:
        data_dir = tmp_path / "cliproxy_data"
        data_dir.mkdir(parents=True)
        f = data_dir / "provider_definitions.json"
        f.write_text('{"roo": {"model": "roo-1"}}')

        with patch("thegent.agents.cliproxy_manager._CLIPROXY_DATA_DIR", data_dir):
            parsed = _load_json("provider_definitions.json")

        assert parsed["roo"]["model"] == "roo-1"

    def test_load_json_raises_on_missing_file(self, tmp_path: Path) -> None:
        data_dir = tmp_path / "cliproxy_data"
        data_dir.mkdir(parents=True)

        with patch("thegent.agents.cliproxy_manager._CLIPROXY_DATA_DIR", data_dir):
            with pytest.raises(ValueError, match="missing_file"):
                _load_json("provider_definitions.json")

    def test_load_json_raises_on_invalid_json(self, tmp_path: Path) -> None:
        data_dir = tmp_path / "cliproxy_data"
        data_dir.mkdir(parents=True)
        f = data_dir / "provider_definitions.json"
        f.write_text("{not json")

        with patch("thegent.agents.cliproxy_manager._CLIPROXY_DATA_DIR", data_dir):
            with pytest.raises(ValueError, match="invalid_json"):
                _load_json("provider_definitions.json")

    def test_load_json_raises_on_non_object_json(self, tmp_path: Path) -> None:
        data_dir = tmp_path / "cliproxy_data"
        data_dir.mkdir(parents=True)
        f = data_dir / "provider_definitions.json"
        f.write_text('["roo", "kilo"]')

        with patch("thegent.agents.cliproxy_manager._CLIPROXY_DATA_DIR", data_dir):
            with pytest.raises(ValueError, match="invalid_shape"):
                _load_json("provider_definitions.json")
