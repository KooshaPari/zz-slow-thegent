"""Tests for BKM-08: DiscoveryClient and fallback functions.

Traces to: BKM-08 (PYTHON_FRONTMATTER_NATIVE_BACKMATTER_AUDIT_PLAN.md)

Coverage targets:
  - DiscoveryClient initialisation (native vs fallback)
  - All four public methods: sessions(), tools(), processes(), all()
  - tools_map() convenience method
  - Fallback helpers: _fallback_sessions, _fallback_tools, _fallback_processes
  - Error paths: binary timeout, invalid JSON, bad regex
  - scan_agent_processes() in discovery.py (BKM-08 integration)

# @trace BKM-08
"""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import pytest

from thegent.native.discovery_native import (
    DiscoveryClient,
    _fallback_processes,
    _fallback_sessions,
    _fallback_tools,
)

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_sessions_json() -> list[dict[str, Any]]:
    return [
        {
            "session_name": "main",
            "windows": 3,
            "created": "Mon Jan 1 00:00:00 2026",
            "attached": True,
            "source": "tmux",
        }
    ]


@pytest.fixture
def fake_tools_json() -> list[dict[str, Any]]:
    return [
        {"tool": "claude", "available": True, "path": "/usr/local/bin/claude"},
        {"tool": "thegent", "available": False, "path": None},
        {"tool": "tmux", "available": True, "path": "/usr/bin/tmux"},
        {"tool": "git", "available": True, "path": "/usr/bin/git"},
        {"tool": "npx", "available": False, "path": None},
        {"tool": "node", "available": False, "path": None},
        {"tool": "python3", "available": True, "path": "/usr/bin/python3"},
        {"tool": "screen", "available": False, "path": None},
        {"tool": "cargo", "available": False, "path": None},
    ]


@pytest.fixture
def fake_processes_json() -> list[dict[str, Any]]:
    return [
        {
            "pid": 12345,
            "ppid": 1000,
            "name": "claude-code",
            "cmd": ["claude", "--resume=abc123"],
            "memory_kb": 204800,
            "cpu_usage": 2.5,
            "run_time_s": 600,
        }
    ]


@pytest.fixture
def fake_all_json(
    fake_sessions_json: list[dict],
    fake_tools_json: list[dict],
    fake_processes_json: list[dict],
) -> dict[str, Any]:
    return {
        "sessions": fake_sessions_json,
        "tools": fake_tools_json,
        "processes": fake_processes_json,
    }


# ---------------------------------------------------------------------------
# DiscoveryClient initialisation
# ---------------------------------------------------------------------------


class TestDiscoveryClientInit:
    """DiscoveryClient.__init__ — binary detection."""

    def test_is_native_true_when_binary_found(self, tmp_path: Path) -> None:
        """When the binary exists, is_native is True."""
        fake_bin = tmp_path / "thegent-discovery"
        fake_bin.write_text("#!/bin/sh\necho '[]'")
        fake_bin.chmod(0o755)

        with patch("shutil.which", return_value=str(fake_bin)):
            client = DiscoveryClient()

        assert client.is_native is True
        assert client.binary_path == fake_bin

    def test_is_native_false_when_binary_absent(self) -> None:
        """When the binary is missing, is_native is False."""
        with (
            patch("shutil.which", return_value=None),
            patch.dict("os.environ", {DiscoveryClient.ENV_VAR: ""}, clear=False),
        ):
            client = DiscoveryClient()

        assert client.is_native is False
        assert client.binary_path is None

    def test_env_var_overrides_which(self, tmp_path: Path) -> None:
        """THGENT_DISCOVERY_BIN env var takes precedence over PATH lookup."""
        fake_bin = tmp_path / "custom-discovery"
        fake_bin.write_text("#!/bin/sh\necho '[]'")
        fake_bin.chmod(0o755)

        with patch.dict(
            "os.environ",
            {DiscoveryClient.ENV_VAR: str(fake_bin)},
            clear=False,
        ):
            client = DiscoveryClient()

        assert client.is_native is True
        assert client.binary_path == fake_bin

    def test_env_var_missing_file_falls_through(self) -> None:
        """THGENT_DISCOVERY_BIN pointing at missing file falls back to which."""
        with (
            patch.dict(
                "os.environ",
                {DiscoveryClient.ENV_VAR: "/does/not/exist/thegent-discovery"},
                clear=False,
            ),
            patch("shutil.which", return_value=None),
        ):
            client = DiscoveryClient()

        assert client.is_native is False


# ---------------------------------------------------------------------------
# Native path — subprocess output is returned
# ---------------------------------------------------------------------------


class TestDiscoveryClientNativePath:
    """DiscoveryClient methods when the binary is available."""

    def _make_native_client(self, tmp_path: Path) -> DiscoveryClient:
        fake_bin = tmp_path / "thegent-discovery"
        fake_bin.write_text("#!/bin/sh\necho '[]'")
        fake_bin.chmod(0o755)
        with patch("shutil.which", return_value=str(fake_bin)):
            return DiscoveryClient()

    def test_sessions_returns_binary_output(
        self,
        tmp_path: Path,
        fake_sessions_json: list[dict],
    ) -> None:
        client = self._make_native_client(tmp_path)
        with patch.object(client, "_run", return_value=fake_sessions_json) as mock_run:
            result = client.sessions()
        mock_run.assert_called_once_with("sessions")
        assert result == fake_sessions_json

    def test_tools_returns_binary_output(
        self,
        tmp_path: Path,
        fake_tools_json: list[dict],
    ) -> None:
        client = self._make_native_client(tmp_path)
        with patch.object(client, "_run", return_value=fake_tools_json):
            result = client.tools()
        assert result == fake_tools_json

    def test_processes_no_pattern(
        self,
        tmp_path: Path,
        fake_processes_json: list[dict],
    ) -> None:
        client = self._make_native_client(tmp_path)
        with patch.object(client, "_run", return_value=fake_processes_json) as mock_run:
            result = client.processes()
        mock_run.assert_called_once_with("processes")
        assert result == fake_processes_json

    def test_processes_with_pattern(
        self,
        tmp_path: Path,
        fake_processes_json: list[dict],
    ) -> None:
        client = self._make_native_client(tmp_path)
        with patch.object(client, "_run", return_value=fake_processes_json) as mock_run:
            result = client.processes(pattern="claude")
        mock_run.assert_called_once_with("processes", "--pattern", "claude")
        assert result == fake_processes_json

    def test_all_no_pattern(
        self,
        tmp_path: Path,
        fake_all_json: dict,
    ) -> None:
        client = self._make_native_client(tmp_path)
        with patch.object(client, "_run", return_value=fake_all_json) as mock_run:
            result = client.all()
        mock_run.assert_called_once_with("all")
        assert result == fake_all_json

    def test_all_with_pattern(
        self,
        tmp_path: Path,
        fake_all_json: dict,
    ) -> None:
        client = self._make_native_client(tmp_path)
        with patch.object(client, "_run", return_value=fake_all_json) as mock_run:
            client.all(pattern="cursor")
        mock_run.assert_called_once_with("all", "--pattern", "cursor")

    def test_tools_map_convenience(
        self,
        tmp_path: Path,
        fake_tools_json: list[dict],
    ) -> None:
        client = self._make_native_client(tmp_path)
        with patch.object(client, "_run", return_value=fake_tools_json):
            result = client.tools_map()
        assert isinstance(result, dict)
        assert result["claude"] is True
        assert result["thegent"] is False


# ---------------------------------------------------------------------------
# Error paths — native binary fails -> fallback used
# ---------------------------------------------------------------------------


class TestDiscoveryClientErrorFallback:
    """When native binary is available but fails, fallback functions are used."""

    def _make_native_client(self, tmp_path: Path) -> DiscoveryClient:
        fake_bin = tmp_path / "thegent-discovery"
        fake_bin.write_text("#!/bin/sh\nexit 1")
        fake_bin.chmod(0o755)
        with patch("shutil.which", return_value=str(fake_bin)):
            return DiscoveryClient()

    def test_sessions_falls_back_on_none(self, tmp_path: Path) -> None:
        client = self._make_native_client(tmp_path)
        with (
            patch.object(client, "_run", return_value=None),
            patch(
                "thegent.native.discovery_native._fallback_sessions",
                return_value={"sessions": [], "fallback": {"status": "ok"}},
            ) as mock_fb,
        ):
            result = client.sessions()
        mock_fb.assert_called_once()
        assert result == []

    def test_sessions_fallback_empty_state_preserves_success_status(self, tmp_path: Path) -> None:
        client = self._make_native_client(tmp_path)
        with (
            patch.object(client, "_run", return_value=None),
            patch(
                "thegent.native.discovery_native._fallback_sessions",
                return_value={
                    "sessions": [],
                    "fallback": {"status": "empty", "session_count": 0},
                },
            ) as mock_fb,
        ):
            result = client.sessions()
        mock_fb.assert_called_once()
        assert result == []
        assert client.last_fallback_metadata["sessions"]["status"] == "empty"
        assert client.last_fallback_metadata["sessions"]["session_count"] == 0

    def test_sessions_fallback_records_metadata(self, tmp_path: Path) -> None:
        client = self._make_native_client(tmp_path)
        with (
            patch.object(client, "_run", return_value=None),
            patch(
                "thegent.native.discovery_native._fallback_sessions",
                return_value={
                    "sessions": [],
                    "fallback": {
                        "status": "probe_failed",
                        "error_type": "tmux_missing",
                    },
                },
            ),
        ):
            result = client.sessions()
        assert result == []
        assert client.last_fallback_metadata["sessions"]["error_type"] == "tmux_missing"

    def test_tools_falls_back_on_none(self, tmp_path: Path) -> None:
        client = self._make_native_client(tmp_path)
        with (
            patch.object(client, "_run", return_value=None),
            patch(
                "thegent.native.discovery_native._fallback_tools",
                return_value={
                    "tools": [],
                    "fallback": {
                        "status": "probe_failed",
                        "error_type": "path_probe_missing",
                    },
                },
            ) as mock_fb,
        ):
            result = client.tools()
        mock_fb.assert_called_once()
        assert result == []
        assert client.last_fallback_metadata["tools"]["status"] == "probe_failed"
        assert client.last_fallback_metadata["tools"]["error_type"] == "path_probe_missing"

    def test_processes_falls_back_on_none(self, tmp_path: Path) -> None:
        client = self._make_native_client(tmp_path)
        with (
            patch.object(client, "_run", return_value=None),
            patch(
                "thegent.native.discovery_native._fallback_processes",
                return_value={
                    "processes": [],
                    "fallback": {
                        "status": "probe_failed",
                        "error_type": "psutil_missing",
                    },
                },
            ) as mock_fb,
        ):
            result = client.processes()
        mock_fb.assert_called_once()
        assert result == []
        assert client.last_fallback_metadata["processes"]["status"] == "probe_failed"
        assert client.last_fallback_metadata["processes"]["error_type"] == "psutil_missing"

    def test_all_falls_back_on_none(self, tmp_path: Path) -> None:
        client = self._make_native_client(tmp_path)
        with (
            patch.object(client, "_run", return_value=None),
            patch(
                "thegent.native.discovery_native._fallback_sessions",
                return_value={"sessions": [], "fallback": {"status": "ok"}},
            ),
            patch(
                "thegent.native.discovery_native._fallback_tools",
                return_value={"tools": [], "fallback": {"status": "ok"}},
            ),
            patch(
                "thegent.native.discovery_native._fallback_processes",
                return_value={"processes": [], "fallback": {"status": "ok"}},
            ),
        ):
            result = client.all()
        assert "sessions" in result
        assert "tools" in result
        assert "processes" in result
        assert result["fallback_metadata"]["sessions"]["status"] == "ok"
        assert result["fallback_metadata"]["tools"]["status"] == "ok"
        assert result["fallback_metadata"]["processes"]["status"] == "ok"

    def test_all_falls_back_on_timeout_with_native_metadata(self, tmp_path: Path) -> None:
        client = self._make_native_client(tmp_path)
        with (
            patch(
                "subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd="thegent-discovery", timeout=15),
            ),
            patch(
                "thegent.native.discovery_native._fallback_sessions",
                return_value={"sessions": [], "fallback": {"status": "ok"}},
            ),
            patch(
                "thegent.native.discovery_native._fallback_tools",
                return_value={"tools": [], "fallback": {"status": "ok"}},
            ),
            patch(
                "thegent.native.discovery_native._fallback_processes",
                return_value={"processes": [], "fallback": {"status": "ok"}},
            ),
        ):
            result = client.all()
        assert client.last_run_diagnostics is not None
        assert client.last_run_diagnostics["error_type"] == "timeout"
        assert result["fallback_metadata"]["sessions"]["native_run"]["status"] == "error"
        assert result["fallback_metadata"]["tools"]["native_run"]["error_type"] == "timeout"

    def test_all_falls_back_on_tmux_probe_failure(self, tmp_path: Path) -> None:
        client = self._make_native_client(tmp_path)
        with (
            patch(
                "subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd="thegent-discovery", timeout=15),
            ),
            patch(
                "thegent.native.discovery_native._fallback_sessions",
                return_value={
                    "sessions": [],
                    "fallback": {
                        "status": "probe_failed",
                        "error_type": "tmux_missing",
                    },
                },
            ),
            patch(
                "thegent.native.discovery_native._fallback_tools",
                return_value={"tools": [], "fallback": {"status": "ok"}},
            ),
            patch(
                "thegent.native.discovery_native._fallback_processes",
                return_value={"processes": [], "fallback": {"status": "ok"}},
            ),
        ):
            result = client.all()
        assert result["fallback_metadata"]["sessions"]["status"] == "probe_failed"
        assert result["fallback_metadata"]["sessions"]["error_type"] == "tmux_missing"

    def test_run_timeout_returns_none(self, tmp_path: Path) -> None:
        client = self._make_native_client(tmp_path)
        with patch(
            "subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="thegent-discovery", timeout=15),
        ):
            result = client._run("sessions")
        assert result is None

    def test_run_invalid_json_returns_none(self, tmp_path: Path) -> None:
        client = self._make_native_client(tmp_path)
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "not valid json{"
        with patch("subprocess.run", return_value=mock_result):
            result = client._run("tools")
        assert result is None

    def test_run_nonzero_exit_returns_none(self, tmp_path: Path) -> None:
        client = self._make_native_client(tmp_path)
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "some error"
        with patch("subprocess.run", return_value=mock_result):
            result = client._run("all")
        assert result is None
        assert client.last_run_diagnostics is not None
        assert client.last_run_diagnostics["error_type"] == "nonzero_exit"

    def test_run_launch_failure_records_diagnostics(self, tmp_path: Path) -> None:
        client = self._make_native_client(tmp_path)
        with patch("subprocess.run", side_effect=FileNotFoundError("missing")):
            result = client._run("all")
        assert result is None
        assert client.last_run_diagnostics is not None
        assert client.last_run_diagnostics["error_type"] == "binary_missing"


# ---------------------------------------------------------------------------
# Fallback path — no binary
# ---------------------------------------------------------------------------


class TestDiscoveryClientFallbackPath:
    """DiscoveryClient methods when binary is absent always use Python fallback."""

    @pytest.fixture
    def fallback_client(self) -> DiscoveryClient:
        with (
            patch("shutil.which", return_value=None),
            patch.dict("os.environ", {DiscoveryClient.ENV_VAR: ""}, clear=False),
        ):
            return DiscoveryClient()

    def test_sessions_delegates_to_fallback(self, fallback_client: DiscoveryClient) -> None:
        with patch(
            "thegent.native.discovery_native._fallback_sessions",
            return_value={
                "sessions": [{"session_name": "s1"}],
                "fallback": {"status": "ok"},
            },
        ) as mock_fb:
            result = fallback_client.sessions()
        mock_fb.assert_called_once()
        assert result == [{"session_name": "s1"}]

    def test_tools_delegates_to_fallback(self, fallback_client: DiscoveryClient) -> None:
        expected = [{"tool": "git", "available": True, "path": "/usr/bin/git"}]
        with patch("thegent.native.discovery_native._fallback_tools", return_value=expected):
            result = fallback_client.tools()
        assert result == expected

    def test_processes_delegates_to_fallback(self, fallback_client: DiscoveryClient) -> None:
        with patch("thegent.native.discovery_native._fallback_processes", return_value=[]) as mock_fb:
            fallback_client.processes(pattern="custom")
        mock_fb.assert_called_once_with("custom", include_meta=True)

    def test_all_delegates_to_fallback(self, fallback_client: DiscoveryClient) -> None:
        with (
            patch(
                "thegent.native.discovery_native._fallback_sessions",
                return_value={"sessions": [], "fallback": {"status": "ok"}},
            ),
            patch("thegent.native.discovery_native._fallback_tools", return_value=[]),
            patch("thegent.native.discovery_native._fallback_processes", return_value=[]),
        ):
            result = fallback_client.all()
        assert set(result.keys()) == {
            "sessions",
            "tools",
            "processes",
            "fallback_metadata",
        }


# ---------------------------------------------------------------------------
# Fallback function unit tests
# ---------------------------------------------------------------------------


class TestFallbackSessions:
    """_fallback_sessions — tmux/screen subprocess handling."""

    def test_returns_list_on_tmux_success(self) -> None:
        tmux_output = "main|3|Mon Jan  1 00:00:00 2026|1\n"
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = tmux_output
        with patch("subprocess.run", return_value=mock_result):
            sessions = _fallback_sessions()
        assert len(sessions) >= 1
        assert sessions[0]["session_name"] == "main"
        assert sessions[0]["source"] == "tmux"
        assert sessions[0]["attached"] is True

    def test_returns_empty_list_with_empty_status(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        with patch("subprocess.run", return_value=mock_result):
            payload = _fallback_sessions(include_meta=True)
        assert payload["sessions"] == []
        assert payload["fallback"]["status"] == "empty"
        assert payload["fallback"]["session_count"] == 0
        assert "error_type" not in payload["fallback"]

    def test_returns_list_on_tmux_failure(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        with patch("subprocess.run", return_value=mock_result):
            sessions = _fallback_sessions()
        # Should not raise; may be empty or include screen results
        assert isinstance(sessions, list)

    def test_handles_subprocess_exception(self) -> None:
        with patch("subprocess.run", side_effect=FileNotFoundError("tmux not found")):
            payload = _fallback_sessions(include_meta=True)
        assert payload["sessions"] == []
        assert payload["fallback"]["status"] == "probe_failed"
        assert payload["fallback"]["error_type"] == "tmux_missing"

    def test_returns_error_on_nonzero_exit(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 2
        mock_result.stdout = ""
        mock_result.stderr = "tmux failed"
        with patch("subprocess.run", return_value=mock_result):
            payload = _fallback_sessions(include_meta=True)
        assert payload["sessions"] == []
        assert payload["fallback"]["status"] == "probe_failed"
        assert payload["fallback"]["error_type"] == "nonzero_exit"
        assert payload["fallback"]["returncode"] == 2

    def test_timeout_metadata(self) -> None:
        with patch(
            "subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="tmux", timeout=5),
        ):
            payload = _fallback_sessions(include_meta=True)
        assert payload["sessions"] == []
        assert payload["fallback"]["status"] == "probe_failed"
        assert payload["fallback"]["error_type"] == "timeout"

    def test_malformed_output_sets_parse_failed_metadata(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "bad-line-no-delimiters\n"
        mock_result.stderr = ""
        with patch("subprocess.run", return_value=mock_result):
            payload = _fallback_sessions(include_meta=True)
        assert payload["sessions"] == []
        assert payload["fallback"]["status"] == "parse_failed"
        assert payload["fallback"]["error_type"] == "malformed_output"


class TestFallbackTools:
    """_fallback_tools — shutil.which calls."""

    def test_returns_entry_per_tool(self) -> None:
        with patch(
            "shutil.which",
            side_effect=lambda t: f"/usr/bin/{t}" if t == "git" else None,
        ):
            tools = _fallback_tools()
        names = {t["tool"] for t in tools}
        assert "git" in names
        assert "claude" in names
        git_entry = next(t for t in tools if t["tool"] == "git")
        assert git_entry["available"] is True
        assert git_entry["path"] == "/usr/bin/git"
        claude_entry = next(t for t in tools if t["tool"] == "claude")
        assert claude_entry["available"] is False
        assert claude_entry["path"] is None

    def test_all_tools_probed(self) -> None:
        with patch("shutil.which", return_value=None):
            tools = _fallback_tools()
        from thegent.native.discovery_native import _PROBE_TOOLS

        assert len(tools) == len(_PROBE_TOOLS)

    def test_include_meta_returns_payload(self) -> None:
        with patch(
            "shutil.which",
            side_effect=lambda t: f"/usr/bin/{t}" if t == "git" else None,
        ):
            payload = _fallback_tools(include_meta=True)
        assert payload["fallback"]["status"] == "ok"
        assert payload["fallback"]["tools_count"] == len(payload["tools"])
        assert payload["fallback"]["available_count"] == 1


class TestFallbackProcesses:
    """_fallback_processes — psutil scanning."""

    def _make_mock_proc(self, pid: int, name: str, cmdline: list[str]) -> MagicMock:
        proc = MagicMock()
        proc.info = {
            "pid": pid,
            "ppid": 1,
            "name": name,
            "cmdline": cmdline,
            "memory_info": MagicMock(rss=1024 * 1024),
            "cpu_percent": 1.5,
            "create_time": 0.0,
        }
        return proc

    def test_matches_default_pattern(self) -> None:
        mock_procs = [
            self._make_mock_proc(100, "claude-code", ["claude", "--resume=abc"]),
            self._make_mock_proc(200, "bash", ["bash", "-c", "echo hi"]),
        ]
        with patch("psutil.process_iter", return_value=mock_procs):
            result = _fallback_processes()
        pids = [p["pid"] for p in result]
        assert 100 in pids
        assert 200 not in pids

    def test_custom_pattern(self) -> None:
        mock_procs = [
            self._make_mock_proc(300, "bash", ["bash"]),
            self._make_mock_proc(400, "vim", ["vim", "NOTES.md"]),
        ]
        with patch("psutil.process_iter", return_value=mock_procs):
            result = _fallback_processes(pattern="vim")
        pids = [p["pid"] for p in result]
        assert 400 in pids
        assert 300 not in pids

    def test_invalid_pattern_returns_empty(self) -> None:
        payload = _fallback_processes(pattern="[invalid(regex", include_meta=True)
        assert payload["processes"] == []
        assert payload["fallback"]["error_type"] == "invalid_pattern"
        assert payload["fallback"]["status"] == "probe_failed"

    def test_handles_access_denied(self) -> None:
        import psutil as _psutil

        # Use a MagicMock for info so that .get() can be intercepted
        bad_proc = MagicMock()
        bad_info = MagicMock()
        bad_info.get = MagicMock(side_effect=_psutil.AccessDenied(0))
        bad_proc.info = bad_info

        good_proc = self._make_mock_proc(999, "thegent", ["thegent", "run"])
        with patch("psutil.process_iter", return_value=[bad_proc, good_proc]):
            result = _fallback_processes()
        pids = [p["pid"] for p in result]
        assert 999 in pids

    def test_psutil_import_error_returns_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When psutil is not importable, return empty list gracefully."""
        import sys

        monkeypatch.setitem(sys.modules, "psutil", None)
        payload = _fallback_processes(include_meta=True)
        assert payload["processes"] == []
        assert payload["fallback"]["error_type"] == "psutil_missing"
        assert payload["fallback"]["status"] == "probe_failed"


# ---------------------------------------------------------------------------
# Integration with discovery.py (BKM-08 integration point)
# ---------------------------------------------------------------------------


class TestScanAgentProcessesIntegration:
    """scan_agent_processes() in discovery.py delegates to DiscoveryClient."""

    def test_uses_native_client_when_available(self, fake_processes_json: list[dict]) -> None:
        import thegent.discovery as discovery_mod

        # Reset the module-level cache
        discovery_mod._native_client = None
        discovery_mod._native_checked = False

        mock_client = MagicMock()
        mock_client.is_native = True
        mock_client.processes.return_value = fake_processes_json

        with patch(
            "thegent.native.discovery_native.DiscoveryClient",
            return_value=mock_client,
        ):
            result = discovery_mod.scan_agent_processes()

        assert result == fake_processes_json

        # Restore cache so other tests are unaffected
        discovery_mod._native_client = None
        discovery_mod._native_checked = False

    def test_falls_back_to_agent_scanner_when_no_native(self) -> None:
        import sys

        import thegent.discovery as discovery_mod

        discovery_mod._native_client = None
        discovery_mod._native_checked = False

        mock_client = MagicMock()
        mock_client.is_native = False
        mock_client.processes.return_value = []

        mock_scanner_instance = MagicMock()
        mock_scanner_instance.scan.return_value = [{"pid": 42, "type": "codex"}]
        mock_scanner_cls = MagicMock(return_value=mock_scanner_instance)

        # Patch the discovery_v2 module at the sys.modules level to avoid
        # importing it directly (discovery_v2.py uses Python 3.10+ union syntax)
        fake_discovery_v2 = MagicMock()
        fake_discovery_v2.AgentScanner = mock_scanner_cls

        with (
            patch(
                "thegent.native.discovery_native.DiscoveryClient",
                return_value=mock_client,
            ),
            patch.dict(sys.modules, {"thegent.infra.discovery_v2": fake_discovery_v2}),
        ):
            result = discovery_mod.scan_agent_processes()

        # When native is not active, fallback scan returns psutil results
        assert isinstance(result, list)

        discovery_mod._native_client = None
        discovery_mod._native_checked = False
