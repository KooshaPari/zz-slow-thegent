"""Unit tests for ZmxSessionManager and ZmxSessionConfig.

All subprocess calls are mocked -- no zmx binary required.

# @trace FR-SES-001, FR-SES-002, FR-SES-003
"""

from __future__ import annotations

import importlib
import subprocess
import sys
from unittest.mock import MagicMock, patch

import orjson as json
import pytest

from thegent.muxless.zmx_session import (
    ZmxSessionConfig,
    ZmxSessionManager,
    make_zmx_session_manager,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def config() -> ZmxSessionConfig:
    """A ZmxSessionConfig using the default binary path."""
    return ZmxSessionConfig(binary_path="zmx", max_sessions=50, session_ttl_s=3600)


@pytest.fixture
def manager_available(config: ZmxSessionConfig) -> ZmxSessionManager:
    """ZmxSessionManager with zmx pre-set as available."""
    mgr = ZmxSessionManager(config=config)
    mgr._available = True
    return mgr


@pytest.fixture
def manager_unavailable(config: ZmxSessionConfig) -> ZmxSessionManager:
    """ZmxSessionManager with zmx pre-set as unavailable."""
    mgr = ZmxSessionManager(config=config)
    mgr._available = False
    return mgr


def _ok_run(stdout: str = "", returncode: int = 0) -> MagicMock:
    """Build a mock subprocess.CompletedProcess."""
    mock = MagicMock()
    mock.returncode = returncode
    mock.stdout = stdout
    mock.stderr = ""
    return mock


def _fail_run(stderr: str = "error", returncode: int = 1) -> MagicMock:
    """Build a failed mock subprocess.CompletedProcess."""
    mock = MagicMock()
    mock.returncode = returncode
    mock.stdout = ""
    mock.stderr = stderr
    return mock


# ---------------------------------------------------------------------------
# ZmxSessionConfig
# ---------------------------------------------------------------------------


class TestZmxSessionConfig:
    """Tests for ZmxSessionConfig dataclass and env-var reading."""

    def test_default_binary_path_is_zmx(self) -> None:
        cfg = ZmxSessionConfig()
        assert cfg.binary_path == "zmx"

    def test_default_max_sessions(self) -> None:
        cfg = ZmxSessionConfig()
        assert cfg.max_sessions == 50

    def test_default_session_ttl(self) -> None:
        cfg = ZmxSessionConfig()
        assert cfg.session_ttl_s == 3600

    def test_custom_binary_path(self) -> None:
        cfg = ZmxSessionConfig(binary_path="/usr/local/bin/zmx")
        assert cfg.binary_path == "/usr/local/bin/zmx"

    def test_custom_max_sessions(self) -> None:
        cfg = ZmxSessionConfig(max_sessions=10)
        assert cfg.max_sessions == 10

    def test_custom_session_ttl(self) -> None:
        cfg = ZmxSessionConfig(session_ttl_s=1800)
        assert cfg.session_ttl_s == 1800

    def test_from_env_reads_binary_env_var(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("THGENT_ZMX_BINARY", "/opt/zmx/bin/zmx")
        cfg = ZmxSessionConfig.from_env()
        assert cfg.binary_path == "/opt/zmx/bin/zmx"

    def test_from_env_reads_max_sessions_env_var(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("THGENT_ZMX_MAX_SESSIONS", "20")
        cfg = ZmxSessionConfig.from_env()
        assert cfg.max_sessions == 20

    def test_from_env_reads_ttl_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("THGENT_ZMX_SESSION_TTL", "7200")
        cfg = ZmxSessionConfig.from_env()
        assert cfg.session_ttl_s == 7200

    def test_from_env_defaults_when_env_not_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("THGENT_ZMX_BINARY", raising=False)
        monkeypatch.delenv("THGENT_ZMX_MAX_SESSIONS", raising=False)
        monkeypatch.delenv("THGENT_ZMX_SESSION_TTL", raising=False)
        cfg = ZmxSessionConfig.from_env()
        assert cfg.binary_path == "zmx"
        assert cfg.max_sessions == 50
        assert cfg.session_ttl_s == 3600

    def test_from_env_invalid_max_sessions_uses_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("THGENT_ZMX_MAX_SESSIONS", "not-a-number")
        cfg = ZmxSessionConfig.from_env()
        assert cfg.max_sessions == 50

    def test_from_env_invalid_ttl_uses_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("THGENT_ZMX_SESSION_TTL", "bad")
        cfg = ZmxSessionConfig.from_env()
        assert cfg.session_ttl_s == 3600

    def test_binary_path_uses_env_var_in_default_factory(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("THGENT_ZMX_BINARY", "/custom/zmx")
        cfg = ZmxSessionConfig()
        assert cfg.binary_path == "/custom/zmx"


# ---------------------------------------------------------------------------
# ZmxSessionManager.is_available
# ---------------------------------------------------------------------------


class TestIsAvailable:
    """Tests for is_available() probe logic.  # @trace FR-SES-002"""

    def test_returns_false_when_binary_not_on_path(self) -> None:
        mgr = ZmxSessionManager(ZmxSessionConfig(binary_path="zmx-not-real"))
        with patch("shutil.which", return_value=None):
            assert mgr.is_available() is False

    def test_returns_true_when_version_exits_zero(self) -> None:
        mgr = ZmxSessionManager(ZmxSessionConfig(binary_path="zmx"))
        with (
            patch("shutil.which", return_value="/usr/bin/zmx"),
            patch("subprocess.run", return_value=_ok_run("zmx 0.1.0")),
        ):
            assert mgr.is_available() is True

    def test_falls_back_to_list_probe_when_version_fails(self) -> None:
        mgr = ZmxSessionManager(ZmxSessionConfig(binary_path="zmx"))
        fail = _fail_run()
        ok = _ok_run()
        with (
            patch("shutil.which", return_value="/usr/bin/zmx"),
            patch("subprocess.run", side_effect=[fail, ok]),
        ):
            assert mgr.is_available() is True

    def test_returns_false_when_both_probes_fail(self) -> None:
        mgr = ZmxSessionManager(ZmxSessionConfig(binary_path="zmx"))
        with (
            patch("shutil.which", return_value="/usr/bin/zmx"),
            patch("subprocess.run", return_value=_fail_run()),
        ):
            assert mgr.is_available() is False

    def test_returns_false_on_os_error_during_probe(self) -> None:
        mgr = ZmxSessionManager(ZmxSessionConfig(binary_path="zmx"))
        with (
            patch("shutil.which", return_value="/usr/bin/zmx"),
            patch("subprocess.run", side_effect=OSError("no such file")),
        ):
            assert mgr.is_available() is False

    def test_availability_is_cached_after_first_call(self) -> None:
        mgr = ZmxSessionManager(ZmxSessionConfig(binary_path="zmx"))
        with (
            patch("shutil.which", return_value="/usr/bin/zmx"),
            patch("subprocess.run", return_value=_ok_run("zmx 0.1.0")) as mock_run,
        ):
            mgr.is_available()
            mgr.is_available()
            # subprocess.run called only once despite two is_available() calls
            assert mock_run.call_count == 1

    def test_returns_false_on_timeout_during_probe(self) -> None:
        mgr = ZmxSessionManager(ZmxSessionConfig(binary_path="zmx"))
        with (
            patch("shutil.which", return_value="/usr/bin/zmx"),
            patch("subprocess.run", side_effect=subprocess.TimeoutExpired("zmx", 5)),
        ):
            assert mgr.is_available() is False


# ---------------------------------------------------------------------------
# ZmxSessionManager.create_session
# ---------------------------------------------------------------------------


class TestCreateSession:
    """Tests for create_session().  # @trace FR-SES-001"""

    def test_returns_session_name_on_success(
        self, manager_available: ZmxSessionManager
    ) -> None:
        with patch("subprocess.run", return_value=_ok_run()) as mock_run:
            result = manager_available.create_session("agent-abc", ["/bin/sh"])
        assert result == "agent-abc"
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[:3] == ["zmx", "new", "agent-abc"]
        assert "/bin/sh" in call_args

    def test_returns_empty_string_when_zmx_unavailable(
        self, manager_unavailable: ZmxSessionManager
    ) -> None:
        result = manager_unavailable.create_session("sess", ["/bin/sh"])
        assert result == ""

    def test_returns_empty_string_when_zmx_new_fails(
        self, manager_available: ZmxSessionManager
    ) -> None:
        with patch("subprocess.run", return_value=_fail_run()):
            result = manager_available.create_session("fail-sess", ["/bin/sh"])
        assert result == ""

    def test_returns_empty_string_for_empty_session_id(
        self, manager_available: ZmxSessionManager
    ) -> None:
        result = manager_available.create_session("", ["/bin/sh"])
        assert result == ""

    def test_returns_empty_string_for_empty_command(
        self, manager_available: ZmxSessionManager
    ) -> None:
        result = manager_available.create_session("sess", [])
        assert result == ""

    def test_passes_command_args_after_separator(
        self, manager_available: ZmxSessionManager
    ) -> None:
        with patch("subprocess.run", return_value=_ok_run()) as mock_run:
            manager_available.create_session("myses", ["python", "-m", "http.server"])
        args = mock_run.call_args[0][0]
        sep_idx = args.index("--")
        assert args[sep_idx + 1 :] == ["python", "-m", "http.server"]

    def test_uses_subprocess_run_not_os_system(
        self, manager_available: ZmxSessionManager
    ) -> None:
        with patch("subprocess.run", return_value=_ok_run()) as mock_run:
            manager_available.create_session("sess", ["/bin/sh"])
        assert mock_run.called

    def test_returns_empty_on_os_error(
        self, manager_available: ZmxSessionManager
    ) -> None:
        with patch("subprocess.run", side_effect=OSError("spawn failed")):
            result = manager_available.create_session("sess", ["/bin/sh"])
        assert result == ""


# ---------------------------------------------------------------------------
# ZmxSessionManager.attach_session
# ---------------------------------------------------------------------------


class TestAttachSession:
    """Tests for attach_session().  # @trace FR-SES-001"""

    def test_returns_true_on_success(
        self, manager_available: ZmxSessionManager
    ) -> None:
        with patch("subprocess.run", return_value=_ok_run()):
            result = manager_available.attach_session("myses")
        assert result is True

    def test_returns_false_when_zmx_unavailable(
        self, manager_unavailable: ZmxSessionManager
    ) -> None:
        result = manager_unavailable.attach_session("myses")
        assert result is False

    def test_returns_false_when_attach_fails(
        self, manager_available: ZmxSessionManager
    ) -> None:
        with patch("subprocess.run", return_value=_fail_run()):
            result = manager_available.attach_session("myses")
        assert result is False

    def test_calls_zmx_attach_subcommand(
        self, manager_available: ZmxSessionManager
    ) -> None:
        with patch("subprocess.run", return_value=_ok_run()) as mock_run:
            manager_available.attach_session("target-sess")
        args = mock_run.call_args[0][0]
        assert args == ["zmx", "attach", "target-sess"]

    def test_interactive_run_has_no_capture(
        self, manager_available: ZmxSessionManager
    ) -> None:
        with patch("subprocess.run", return_value=_ok_run()) as mock_run:
            manager_available.attach_session("sess")
        call_kwargs = mock_run.call_args[1] or {}
        assert "capture_output" not in call_kwargs


# ---------------------------------------------------------------------------
# ZmxSessionManager.capture_output
# ---------------------------------------------------------------------------


class TestCaptureOutput:
    """Tests for capture_output().  # @trace FR-SES-001"""

    def test_returns_stdout_on_success(
        self, manager_available: ZmxSessionManager
    ) -> None:
        with patch("subprocess.run", return_value=_ok_run("line1\nline2\n")):
            result = manager_available.capture_output("sess", lines=50)
        assert result == "line1\nline2\n"

    def test_returns_empty_string_when_zmx_unavailable(
        self, manager_unavailable: ZmxSessionManager
    ) -> None:
        result = manager_unavailable.capture_output("sess")
        assert result == ""

    def test_returns_empty_string_on_capture_failure(
        self, manager_available: ZmxSessionManager
    ) -> None:
        with patch("subprocess.run", return_value=_fail_run()):
            result = manager_available.capture_output("sess")
        assert result == ""

    def test_default_lines_is_100(self, manager_available: ZmxSessionManager) -> None:
        with patch("subprocess.run", return_value=_ok_run("out")) as mock_run:
            manager_available.capture_output("sess")
        args = mock_run.call_args[0][0]
        assert "--lines" in args
        assert args[args.index("--lines") + 1] == "100"

    def test_custom_lines_passed_to_zmx(
        self, manager_available: ZmxSessionManager
    ) -> None:
        with patch("subprocess.run", return_value=_ok_run("out")) as mock_run:
            manager_available.capture_output("sess", lines=25)
        args = mock_run.call_args[0][0]
        assert args[args.index("--lines") + 1] == "25"

    def test_calls_zmx_capture_subcommand(
        self, manager_available: ZmxSessionManager
    ) -> None:
        with patch("subprocess.run", return_value=_ok_run("x")) as mock_run:
            manager_available.capture_output("my-session", lines=10)
        args = mock_run.call_args[0][0]
        assert args[:3] == ["zmx", "capture", "my-session"]

    def test_returns_empty_on_timeout(
        self, manager_available: ZmxSessionManager
    ) -> None:
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("zmx", 30)):
            result = manager_available.capture_output("sess")
        assert result == ""


# ---------------------------------------------------------------------------
# ZmxSessionManager.send_input
# ---------------------------------------------------------------------------


class TestSendInput:
    """Tests for send_input().  # @trace FR-SES-001"""

    def test_returns_true_on_success(
        self, manager_available: ZmxSessionManager
    ) -> None:
        with patch("subprocess.run", return_value=_ok_run()):
            result = manager_available.send_input("sess", "ls -la\n")
        assert result is True

    def test_returns_false_when_zmx_unavailable(
        self, manager_unavailable: ZmxSessionManager
    ) -> None:
        result = manager_unavailable.send_input("sess", "hello")
        assert result is False

    def test_returns_false_when_send_fails(
        self, manager_available: ZmxSessionManager
    ) -> None:
        with patch("subprocess.run", return_value=_fail_run()):
            result = manager_available.send_input("sess", "hello")
        assert result is False

    def test_calls_zmx_send_keys_subcommand(
        self, manager_available: ZmxSessionManager
    ) -> None:
        with patch("subprocess.run", return_value=_ok_run()) as mock_run:
            manager_available.send_input("target", "echo hi")
        args = mock_run.call_args[0][0]
        assert args == ["zmx", "send-keys", "target", "echo hi"]

    def test_returns_false_on_os_error(
        self, manager_available: ZmxSessionManager
    ) -> None:
        with patch("subprocess.run", side_effect=OSError("err")):
            result = manager_available.send_input("sess", "x")
        assert result is False


# ---------------------------------------------------------------------------
# ZmxSessionManager.list_sessions
# ---------------------------------------------------------------------------


class TestListSessions:
    """Tests for list_sessions().  # @trace FR-SES-001"""

    def test_returns_empty_list_when_zmx_unavailable(
        self, manager_unavailable: ZmxSessionManager
    ) -> None:
        result = manager_unavailable.list_sessions()
        assert result == []

    def test_returns_names_from_json_output(
        self, manager_available: ZmxSessionManager
    ) -> None:
        json_out = json.dumps([{"name": "sess-a"}, {"name": "sess-b"}]).decode()
        with patch("subprocess.run", return_value=_ok_run(json_out)):
            result = manager_available.list_sessions()
        assert "sess-a" in result
        assert "sess-b" in result

    def test_returns_sorted_names(self, manager_available: ZmxSessionManager) -> None:
        json_out = json.dumps(
            [{"name": "zzz"}, {"name": "aaa"}, {"name": "mmm"}]
        ).decode()
        with patch("subprocess.run", return_value=_ok_run(json_out)):
            result = manager_available.list_sessions()
        assert result == ["aaa", "mmm", "zzz"]

    def test_falls_back_to_text_when_json_flag_unsupported(
        self, manager_available: ZmxSessionManager
    ) -> None:
        json_fail = _fail_run(stderr="unknown flag --format")
        text_ok = _ok_run("sess-x  running  1234\nsess-y  detached  5678")
        with patch("subprocess.run", side_effect=[json_fail, text_ok]):
            result = manager_available.list_sessions()
        assert "sess-x" in result
        assert "sess-y" in result

    def test_returns_empty_list_on_zmx_list_failure(
        self, manager_available: ZmxSessionManager
    ) -> None:
        json_fail = _fail_run(stderr="unknown flag --format")
        list_fail = _fail_run()
        with patch("subprocess.run", side_effect=[json_fail, list_fail]):
            result = manager_available.list_sessions()
        assert result == []

    def test_handles_empty_json_array(
        self, manager_available: ZmxSessionManager
    ) -> None:
        with patch("subprocess.run", return_value=_ok_run("[]")):
            result = manager_available.list_sessions()
        assert result == []

    def test_handles_string_entries_in_json(
        self, manager_available: ZmxSessionManager
    ) -> None:
        json_out = json.dumps(["alpha", "beta"]).decode()
        with patch("subprocess.run", return_value=_ok_run(json_out)):
            result = manager_available.list_sessions()
        assert "alpha" in result
        assert "beta" in result

    def test_skips_comment_lines_in_text_output(
        self, manager_available: ZmxSessionManager
    ) -> None:
        json_fail = _fail_run(stderr="unrecognized")
        text_ok = _ok_run("# sessions\nsess-z  running  999\n")
        with patch("subprocess.run", side_effect=[json_fail, text_ok]):
            result = manager_available.list_sessions()
        assert result == ["sess-z"]

    def test_returns_empty_on_malformed_json(
        self, manager_available: ZmxSessionManager
    ) -> None:
        json_fail = _fail_run(stderr="unrecognized")
        text_fail = _fail_run()
        with patch("subprocess.run", side_effect=[json_fail, text_fail]):
            result = manager_available.list_sessions()
        assert result == []


# ---------------------------------------------------------------------------
# ZmxSessionManager.destroy_session
# ---------------------------------------------------------------------------


class TestDestroySession:
    """Tests for destroy_session().  # @trace FR-SES-001"""

    def test_returns_true_on_success(
        self, manager_available: ZmxSessionManager
    ) -> None:
        with patch("subprocess.run", return_value=_ok_run()):
            result = manager_available.destroy_session("sess")
        assert result is True

    def test_returns_false_when_zmx_unavailable(
        self, manager_unavailable: ZmxSessionManager
    ) -> None:
        result = manager_unavailable.destroy_session("sess")
        assert result is False

    def test_returns_false_when_kill_fails(
        self, manager_available: ZmxSessionManager
    ) -> None:
        with patch("subprocess.run", return_value=_fail_run()):
            result = manager_available.destroy_session("sess")
        assert result is False

    def test_calls_zmx_kill_subcommand(
        self, manager_available: ZmxSessionManager
    ) -> None:
        with patch("subprocess.run", return_value=_ok_run()) as mock_run:
            manager_available.destroy_session("to-kill")
        args = mock_run.call_args[0][0]
        assert args == ["zmx", "kill", "to-kill"]

    def test_returns_false_on_os_error(
        self, manager_available: ZmxSessionManager
    ) -> None:
        with patch("subprocess.run", side_effect=OSError("err")):
            result = manager_available.destroy_session("sess")
        assert result is False

    def test_returns_false_on_timeout(
        self, manager_available: ZmxSessionManager
    ) -> None:
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("zmx", 30)):
            result = manager_available.destroy_session("sess")
        assert result is False


# ---------------------------------------------------------------------------
# Graceful fallback when zmx not available
# ---------------------------------------------------------------------------


class TestGracefulFallback:
    """All public methods degrade gracefully when zmx is missing.  # @trace FR-SES-002"""

    def test_create_session_returns_empty_string_no_zmx(self) -> None:
        mgr = ZmxSessionManager()
        with patch("shutil.which", return_value=None):
            result = mgr.create_session("s", ["/bin/sh"])
        assert result == ""

    def test_attach_session_returns_false_no_zmx(self) -> None:
        mgr = ZmxSessionManager()
        with patch("shutil.which", return_value=None):
            result = mgr.attach_session("s")
        assert result is False

    def test_capture_output_returns_empty_string_no_zmx(self) -> None:
        mgr = ZmxSessionManager()
        with patch("shutil.which", return_value=None):
            result = mgr.capture_output("s")
        assert result == ""

    def test_send_input_returns_false_no_zmx(self) -> None:
        mgr = ZmxSessionManager()
        with patch("shutil.which", return_value=None):
            result = mgr.send_input("s", "text")
        assert result is False

    def test_list_sessions_returns_empty_list_no_zmx(self) -> None:
        mgr = ZmxSessionManager()
        with patch("shutil.which", return_value=None):
            result = mgr.list_sessions()
        assert result == []

    def test_destroy_session_returns_false_no_zmx(self) -> None:
        mgr = ZmxSessionManager()
        with patch("shutil.which", return_value=None):
            result = mgr.destroy_session("s")
        assert result is False

    def test_no_import_error_at_module_level(self) -> None:
        """Importing does not raise even without zmx installed.  # @trace FR-SES-002"""
        mod_name = "thegent.muxless.zmx_session"
        cached = sys.modules.pop(mod_name, None)
        try:
            import thegent.muxless.zmx_session as mod

            assert hasattr(mod, "ZmxSessionManager")
        finally:
            # Restore original module so later tests use the same class identity
            if cached is not None:
                sys.modules[mod_name] = cached
            elif mod_name in sys.modules:
                del sys.modules[mod_name]
            importlib.import_module(mod_name)


# ---------------------------------------------------------------------------
# make_zmx_session_manager factory
# ---------------------------------------------------------------------------


class TestMakeZmxSessionManager:
    """Tests for the make_zmx_session_manager factory function."""

    def test_returns_zmx_session_manager_instance(self) -> None:
        result = make_zmx_session_manager()
        assert isinstance(result, ZmxSessionManager)

    def test_uses_provided_config(self) -> None:
        cfg = ZmxSessionConfig(
            binary_path="/custom/zmx", max_sessions=5, session_ttl_s=600
        )
        mgr = make_zmx_session_manager(config=cfg)
        assert mgr._config.binary_path == "/custom/zmx"
        assert mgr._config.max_sessions == 5

    def test_reads_binary_from_env_when_config_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("THGENT_ZMX_BINARY", "/env/zmx")
        mgr = make_zmx_session_manager(config=None)
        assert mgr._config.binary_path == "/env/zmx"

    def test_returns_independent_instances(self) -> None:
        mgr1 = make_zmx_session_manager()
        mgr2 = make_zmx_session_manager()
        assert mgr1 is not mgr2

    def test_default_config_has_expected_defaults(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("THGENT_ZMX_BINARY", raising=False)
        monkeypatch.delenv("THGENT_ZMX_MAX_SESSIONS", raising=False)
        monkeypatch.delenv("THGENT_ZMX_SESSION_TTL", raising=False)
        mgr = make_zmx_session_manager()
        assert mgr._config.binary_path == "zmx"
        assert mgr._config.max_sessions == 50
        assert mgr._config.session_ttl_s == 3600


# ---------------------------------------------------------------------------
# Integration: create -> list -> capture -> destroy lifecycle
# ---------------------------------------------------------------------------


class TestSessionLifecycle:
    """Integration-style tests for the full session lifecycle.  # @trace FR-SES-001"""

    def test_full_lifecycle_with_mocked_subprocess(
        self, manager_available: ZmxSessionManager
    ) -> None:
        json_with_session = json.dumps([{"name": "lifecycle-sess"}]).decode()
        run_returns = [
            _ok_run(),  # create: zmx new
            _ok_run(json_with_session),  # list: zmx list --format json
            _ok_run("output line 1\noutput 2"),  # capture
            _ok_run(),  # destroy: zmx kill
        ]
        with patch("subprocess.run", side_effect=run_returns):
            created = manager_available.create_session("lifecycle-sess", ["/bin/sh"])
            assert created == "lifecycle-sess"

            sessions = manager_available.list_sessions()
            assert "lifecycle-sess" in sessions

            output = manager_available.capture_output("lifecycle-sess", lines=50)
            assert "output line 1" in output

            destroyed = manager_available.destroy_session("lifecycle-sess")
            assert destroyed is True

    def test_session_not_created_does_not_appear_in_list(
        self, manager_available: ZmxSessionManager
    ) -> None:
        create_fail = _fail_run()
        empty_list = _ok_run("[]")
        with patch("subprocess.run", side_effect=[create_fail, empty_list]):
            created = manager_available.create_session("fail-sess", ["/bin/sh"])
            assert created == ""
            sessions = manager_available.list_sessions()
            assert "fail-sess" not in sessions
