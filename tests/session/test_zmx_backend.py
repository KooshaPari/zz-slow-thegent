"""Unit tests for ZmxBackend and resolve_session_backend.

All subprocess calls are mocked — no zmx binary required.

# @trace FR-SES-001, FR-SES-002, FR-SES-003
"""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import orjson as json
import pytest

from thegent.session.zmx_backend import (
    ZmxBackend,
    ZmxSession,
    resolve_session_backend,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def backend() -> ZmxBackend:
    """A ZmxBackend with availability pre-set to True (zmx 'installed')."""
    b = ZmxBackend(zmx_bin="zmx")
    b._available = True  # bypass probe
    return b


@pytest.fixture
def unavailable_backend() -> ZmxBackend:
    """A ZmxBackend with availability pre-set to False (zmx not installed)."""
    b = ZmxBackend(zmx_bin="zmx")
    b._available = False
    return b


# ---------------------------------------------------------------------------
# ZmxBackend.available — probe logic
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestZmxBackendProbe:
    """Tests for the binary presence probe.  # @trace FR-SES-002"""

    @patch("shutil.which", return_value=None)
    def test_not_on_path_returns_false(self, _which: MagicMock) -> None:
        b = ZmxBackend()
        assert b.available is False

    @patch("shutil.which", return_value="/usr/local/bin/zmx")
    @patch(
        "subprocess.run",
        return_value=MagicMock(returncode=0, stdout="zmx 0.1.0\n", stderr=""),
    )
    def test_version_ok_returns_true(self, _run: MagicMock, _which: MagicMock) -> None:
        b = ZmxBackend()
        assert b.available is True

    @patch("shutil.which", return_value="/usr/local/bin/zmx")
    @patch(
        "subprocess.run",
        side_effect=[
            MagicMock(returncode=1, stdout="", stderr=""),  # --version fails
            MagicMock(returncode=0, stdout="", stderr=""),  # list succeeds
        ],
    )
    def test_version_fail_list_ok_returns_true(
        self, _run: MagicMock, _which: MagicMock
    ) -> None:
        b = ZmxBackend()
        assert b.available is True

    @patch("shutil.which", return_value="/usr/local/bin/zmx")
    @patch("subprocess.run", side_effect=OSError("exec failed"))
    def test_oserror_returns_false(self, _run: MagicMock, _which: MagicMock) -> None:
        b = ZmxBackend()
        assert b.available is False

    @patch("shutil.which", return_value="/usr/local/bin/zmx")
    @patch("subprocess.run", side_effect=subprocess.TimeoutExpired("zmx", 5))
    def test_timeout_returns_false(self, _run: MagicMock, _which: MagicMock) -> None:
        b = ZmxBackend()
        assert b.available is False

    def test_probe_result_cached(self) -> None:
        b = ZmxBackend()
        b._available = True
        with patch.object(b, "_probe") as mock_probe:
            _ = b.available
            _ = b.available
        mock_probe.assert_not_called()


# ---------------------------------------------------------------------------
# ZmxBackend.create
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestZmxBackendCreate:
    """# @trace FR-SES-001"""

    @patch(
        "subprocess.run",
        return_value=MagicMock(returncode=0, stdout="", stderr=""),
    )
    def test_create_success(self, mock_run: MagicMock, backend: ZmxBackend) -> None:
        result = backend.create("agent-session-1", ["claude", "--no-tty"])
        assert result is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[:3] == ["zmx", "new", "agent-session-1"]
        assert "claude" in call_args

    @patch(
        "subprocess.run",
        return_value=MagicMock(returncode=1, stdout="", stderr="error"),
    )
    def test_create_failure_returns_false(
        self, _run: MagicMock, backend: ZmxBackend
    ) -> None:
        result = backend.create("bad-session", ["fail"])
        assert result is False

    def test_create_unavailable_returns_false(
        self, unavailable_backend: ZmxBackend
    ) -> None:
        # @trace FR-SES-002
        result = unavailable_backend.create("session", ["cmd"])
        assert result is False

    @patch("subprocess.run", side_effect=OSError("no such file"))
    def test_create_oserror_returns_false(
        self, _run: MagicMock, backend: ZmxBackend
    ) -> None:
        result = backend.create("session", ["cmd"])
        assert result is False


# ---------------------------------------------------------------------------
# ZmxBackend.attach
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestZmxBackendAttach:
    """# @trace FR-SES-001"""

    @patch(
        "subprocess.run",
        return_value=MagicMock(returncode=0),
    )
    def test_attach_success(self, mock_run: MagicMock, backend: ZmxBackend) -> None:
        result = backend.attach("my-session")
        assert result is True
        call_args = mock_run.call_args[0][0]
        assert call_args == ["zmx", "attach", "my-session"]

    @patch("subprocess.run", return_value=MagicMock(returncode=1))
    def test_attach_failure_returns_false(
        self, _run: MagicMock, backend: ZmxBackend
    ) -> None:
        result = backend.attach("missing-session")
        assert result is False

    def test_attach_unavailable_returns_false(
        self, unavailable_backend: ZmxBackend
    ) -> None:
        result = unavailable_backend.attach("session")
        assert result is False


# ---------------------------------------------------------------------------
# ZmxBackend.list
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestZmxBackendList:
    """# @trace FR-SES-001"""

    def test_list_unavailable_returns_empty(
        self, unavailable_backend: ZmxBackend
    ) -> None:
        result = unavailable_backend.list()
        assert result == []

    @patch(
        "subprocess.run",
        return_value=MagicMock(
            returncode=0,
            stdout=json.dumps(
                [
                    {
                        "name": "agent-1",
                        "state": "running",
                        "pid": 1234,
                        "cmd": "claude",
                    },
                    {
                        "name": "agent-2",
                        "state": "detached",
                        "pid": 5678,
                        "cmd": "codex",
                    },
                ]
            ).decode(),
            stderr="",
        ),
    )
    def test_list_json_format(self, _run: MagicMock, backend: ZmxBackend) -> None:
        sessions = backend.list()
        assert len(sessions) == 2
        assert sessions[0].name == "agent-1"
        assert sessions[0].state == "running"
        assert sessions[0].pid == 1234
        assert sessions[0].cmd == "claude"
        assert sessions[1].name == "agent-2"

    @patch(
        "subprocess.run",
        side_effect=[
            # First call: list --format json → unknown flag
            MagicMock(returncode=1, stdout="", stderr="unknown flag --format"),
            # Second call: list (plain text)
            MagicMock(
                returncode=0,
                stdout="agent-1  running  1234  claude\nagent-2  detached  5678  codex\n",
                stderr="",
            ),
        ],
    )
    def test_list_plain_text_fallback(
        self, _run: MagicMock, backend: ZmxBackend
    ) -> None:
        sessions = backend.list()
        assert len(sessions) == 2
        assert sessions[0].name == "agent-1"
        assert sessions[0].state == "running"
        assert sessions[0].pid == 1234
        assert sessions[1].name == "agent-2"
        assert sessions[1].state == "detached"

    @patch(
        "subprocess.run",
        side_effect=[
            MagicMock(returncode=1, stdout="", stderr="unknown flag --format"),
            MagicMock(returncode=0, stdout="", stderr=""),
        ],
    )
    def test_list_empty_returns_empty(
        self, _run: MagicMock, backend: ZmxBackend
    ) -> None:
        sessions = backend.list()
        assert sessions == []

    @patch(
        "subprocess.run",
        side_effect=[
            MagicMock(returncode=1, stdout="", stderr="unknown flag --format"),
            MagicMock(returncode=0, stdout="# header\n\n  \n", stderr=""),
        ],
    )
    def test_list_skips_blank_and_comment_lines(
        self, _run: MagicMock, backend: ZmxBackend
    ) -> None:
        sessions = backend.list()
        assert sessions == []


# ---------------------------------------------------------------------------
# ZmxBackend.kill
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestZmxBackendKill:
    """# @trace FR-SES-001"""

    @patch("subprocess.run", return_value=MagicMock(returncode=0, stdout="", stderr=""))
    def test_kill_success(self, mock_run: MagicMock, backend: ZmxBackend) -> None:
        result = backend.kill("agent-1")
        assert result is True
        call_args = mock_run.call_args[0][0]
        assert call_args == ["zmx", "kill", "agent-1"]

    @patch(
        "subprocess.run",
        return_value=MagicMock(returncode=1, stdout="", stderr="not found"),
    )
    def test_kill_not_found_returns_false(
        self, _run: MagicMock, backend: ZmxBackend
    ) -> None:
        result = backend.kill("nonexistent")
        assert result is False

    def test_kill_unavailable_returns_false(
        self, unavailable_backend: ZmxBackend
    ) -> None:
        result = unavailable_backend.kill("session")
        assert result is False


# ---------------------------------------------------------------------------
# ZmxBackend.capture
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestZmxBackendCapture:
    """# @trace FR-SES-001, FR-SES-003"""

    @patch(
        "subprocess.run",
        return_value=MagicMock(returncode=0, stdout="line1\nline2\n", stderr=""),
    )
    def test_capture_success(self, mock_run: MagicMock, backend: ZmxBackend) -> None:
        content = backend.capture("agent-1", last_lines=50)
        assert content == "line1\nline2\n"
        call_args = mock_run.call_args[0][0]
        assert call_args == ["zmx", "capture", "agent-1", "--lines", "50"]

    @patch(
        "subprocess.run",
        return_value=MagicMock(returncode=1, stdout="", stderr="not found"),
    )
    def test_capture_failure_returns_empty(
        self, _run: MagicMock, backend: ZmxBackend
    ) -> None:
        content = backend.capture("missing", last_lines=50)
        assert content == ""

    def test_capture_unavailable_returns_empty(
        self, unavailable_backend: ZmxBackend
    ) -> None:
        # @trace FR-SES-002
        content = unavailable_backend.capture("session")
        assert content == ""

    @patch("subprocess.run", side_effect=OSError("pipe broken"))
    def test_capture_oserror_returns_empty(
        self, _run: MagicMock, backend: ZmxBackend
    ) -> None:
        content = backend.capture("session")
        assert content == ""

    @patch(
        "subprocess.run",
        return_value=MagicMock(returncode=0, stdout="output\n", stderr=""),
    )
    def test_capture_custom_line_count(
        self, mock_run: MagicMock, backend: ZmxBackend
    ) -> None:
        backend.capture("session", last_lines=100)
        call_args = mock_run.call_args[0][0]
        assert "--lines" in call_args
        assert "100" in call_args


# ---------------------------------------------------------------------------
# ZmxSession dataclass
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestZmxSession:
    def test_defaults(self) -> None:
        s = ZmxSession(name="test")
        assert s.name == "test"
        assert s.pid is None
        assert s.state == "unknown"
        assert s.cmd == ""
        assert s.extra == {}

    def test_with_all_fields(self) -> None:
        s = ZmxSession(
            name="a", pid=99, state="running", cmd="bash", extra={"tty": "/dev/pts/1"}
        )
        assert s.pid == 99
        assert s.extra["tty"] == "/dev/pts/1"


# ---------------------------------------------------------------------------
# resolve_session_backend
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestResolveSessionBackend:
    """# @trace FR-SES-001"""

    def test_backend_none_returns_none(self) -> None:
        result = resolve_session_backend("none")
        assert result is None

    def test_backend_tmux_returns_none(self) -> None:
        result = resolve_session_backend("tmux")
        assert result is None

    def test_backend_zmx_unavailable_returns_none(self) -> None:
        with patch(
            "thegent.session.zmx_backend.ZmxBackend.available",
            new_callable=lambda: property(lambda self: False),
        ):
            result = resolve_session_backend("zmx")
        assert result is None

    def test_backend_zmx_available_returns_backend(self) -> None:
        with patch(
            "thegent.session.zmx_backend.ZmxBackend.available",
            new_callable=lambda: property(lambda self: True),
        ):
            result = resolve_session_backend("zmx")
        assert isinstance(result, ZmxBackend)

    def test_backend_auto_zmx_available(self) -> None:
        with patch(
            "thegent.session.zmx_backend.ZmxBackend.available",
            new_callable=lambda: property(lambda self: True),
        ):
            result = resolve_session_backend("auto")
        assert isinstance(result, ZmxBackend)

    def test_backend_auto_zmx_unavailable_returns_none(self) -> None:
        with patch(
            "thegent.session.zmx_backend.ZmxBackend.available",
            new_callable=lambda: property(lambda self: False),
        ):
            result = resolve_session_backend("auto")
        assert result is None

    def test_unknown_backend_returns_none(self) -> None:
        result = resolve_session_backend("unknown-backend")
        assert result is None

    def test_env_var_respected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("THGENT_SESSION_BACKEND", "none")
        result = resolve_session_backend()
        assert result is None

    def test_override_takes_precedence_over_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("THGENT_SESSION_BACKEND", "zmx")
        # Override to "none" should win regardless of env
        result = resolve_session_backend("none")
        assert result is None

    def test_case_insensitive(self) -> None:
        result = resolve_session_backend("NONE")
        assert result is None

        result2 = resolve_session_backend("Tmux")
        assert result2 is None
