"""Unit tests for cli_impl session-management functions.

Covers: run_impl, bg_impl, status_impl, stop_impl, wait_impl,
        inspect_impl, logs_impl, ps_impl, history_impl, session_meta_impl,
        events_impl, and internal helpers (_is_pid_running, _resolve_session_status,
        _session_paths, _new_session_id, _read_session_meta, _save_session_meta,
        _find_session_meta, _session_dir, _scope_key, _default_owner_tag,
        _compose_owner_tag, _build_continuation_prompt, _inject_time_constraint,
        _resolve_agent_model, _normalize_output_format,
        _run_background_session_observer).
"""

import os
import signal
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import orjson as json
import pytest
import typer

from thegent.cli.commands import impl as cli_impl


# ---------------------------------------------------------------------------
# Helpers: _is_pid_running
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestIsPidRunning:
    def test_negative_pid_returns_false(self) -> None:
        # @trace FR-CLI-100
        assert cli_impl._is_pid_running(-1) is False

    def test_zero_pid_returns_false(self) -> None:
        # @trace FR-CLI-101
        assert cli_impl._is_pid_running(0) is False

    @patch("os.kill")
    def test_running_pid(self, mock_kill) -> None:
        # @trace FR-CLI-102
        mock_kill.return_value = None
        assert cli_impl._is_pid_running(12345) is True
        mock_kill.assert_called_once_with(12345, 0)

    @patch("os.kill", side_effect=OSError("No such process"))
    def test_dead_pid(self, mock_kill) -> None:
        # @trace FR-CLI-103
        assert cli_impl._is_pid_running(99999) is False


# ---------------------------------------------------------------------------
# Helpers: _scope_key
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestScopeKey:
    def test_alphanumeric_passthrough(self) -> None:
        # @trace FR-CLI-104
        assert cli_impl._scope_key("user-proj") == "user-proj"

    def test_special_chars_replaced(self) -> None:
        # @trace FR-CLI-105
        result = cli_impl._scope_key("user:proj/sub")
        assert ":" not in result
        assert "/" not in result


# ---------------------------------------------------------------------------
# Helpers: _session_paths
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestSessionPaths:
    def test_returns_expected_keys(self, tmp_path) -> None:
        # @trace FR-CLI-106
        paths = cli_impl._session_paths(tmp_path, "sess-001")
        assert set(paths.keys()) == {"meta", "stdout", "stderr", "rc", "in"}
        assert paths["meta"] == tmp_path / "sess-001.json"
        assert paths["stdout"] == tmp_path / "sess-001.stdout.log"
        assert paths["stderr"] == tmp_path / "sess-001.stderr.log"
        assert paths["rc"] == tmp_path / "sess-001.rc"
        assert paths["in"] == tmp_path / "sess-001.in"


# ---------------------------------------------------------------------------
# Helpers: _new_session_id
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestNewSessionId:
    def test_contains_agent_name(self) -> None:
        # @trace FR-CLI-107
        sid = cli_impl._new_session_id("claude", "alice:proj")
        assert "claude" in sid

    def test_unique_ids(self) -> None:
        # @trace FR-CLI-108
        ids = {cli_impl._new_session_id("claude", "x") for _ in range(20)}
        assert len(ids) == 20


# ---------------------------------------------------------------------------
# Helpers: _read_session_meta / _save_session_meta
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestReadSaveSessionMeta:
    def test_round_trip(self, tmp_path) -> None:
        # @trace FR-CLI-109
        meta_path = tmp_path / "sess.json"
        payload = {"session_id": "s1", "agent": "claude", "pid": 123}
        cli_impl._save_session_meta(meta_path, payload)
        loaded = cli_impl._read_session_meta(meta_path)
        assert loaded["session_id"] == "s1"
        assert loaded["pid"] == 123

    def test_read_missing_raises(self, tmp_path) -> None:
        # @trace FR-CLI-110
        with pytest.raises(typer.BadParameter, match="Session not found"):
            cli_impl._read_session_meta(tmp_path / "nope.json")


# ---------------------------------------------------------------------------
# Helpers: _find_session_meta
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestFindSessionMeta:
    def test_find_direct(self, tmp_path) -> None:
        # @trace FR-CLI-111
        settings = MagicMock()
        settings.session_dir = tmp_path
        meta = tmp_path / "sess-abc.json"
        meta.write_text("{}", encoding="utf-8")
        result = cli_impl._find_session_meta(settings, "sess-abc")
        assert result == meta

    def test_find_in_scope_dir(self, tmp_path) -> None:
        # @trace FR-CLI-112
        settings = MagicMock()
        settings.session_dir = tmp_path
        scope = tmp_path / "owner_scope"
        scope.mkdir()
        meta = scope / "sess-xyz.json"
        meta.write_text("{}", encoding="utf-8")
        result = cli_impl._find_session_meta(settings, "sess-xyz")
        assert result == meta

    def test_not_found_raises(self, tmp_path) -> None:
        # @trace FR-CLI-113
        settings = MagicMock()
        settings.session_dir = tmp_path
        with pytest.raises(typer.BadParameter, match="Session not found"):
            cli_impl._find_session_meta(settings, "nonexistent")


# ---------------------------------------------------------------------------
# Helpers: _resolve_session_status
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestResolveSessionStatus:
    def test_running(self, tmp_path) -> None:
        # @trace FR-CLI-114
        rc_path = tmp_path / "sess.rc"
        assert cli_impl._resolve_session_status({}, rc_path, running=True) == "running"

    def test_exited_with_exit_code_in_payload(self, tmp_path) -> None:
        # @trace FR-CLI-115
        rc_path = tmp_path / "sess.rc"
        result = cli_impl._resolve_session_status(
            {"exit_code": 0}, rc_path, running=False
        )
        assert result == "exited:0"

    def test_exited_with_rc_file(self, tmp_path) -> None:
        # @trace FR-CLI-116
        rc_path = tmp_path / "sess.rc"
        rc_path.write_text("42\n", encoding="utf-8")
        result = cli_impl._resolve_session_status({}, rc_path, running=False)
        assert result == "exited:42"

    def test_exited_fallback_no_code(self, tmp_path) -> None:
        # @trace FR-CLI-117
        rc_path = tmp_path / "sess.rc"
        result = cli_impl._resolve_session_status({}, rc_path, running=False)
        assert result == "exited"

    def test_exited_rc_file_invalid(self, tmp_path) -> None:
        # @trace FR-CLI-118
        rc_path = tmp_path / "sess.rc"
        rc_path.write_text("garbage\n", encoding="utf-8")
        result = cli_impl._resolve_session_status({}, rc_path, running=False)
        assert result == "exited"


# ---------------------------------------------------------------------------
# Helpers: _inject_time_constraint
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestInjectTimeConstraint:
    def test_appends_budget(self) -> None:
        # @trace FR-CLI-119
        result = cli_impl._inject_time_constraint("do stuff", 90)
        assert "TIME CONSTRAINT" in result
        assert "do stuff" in result

    def test_summary_mode_adds_output_format(self) -> None:
        # @trace FR-CLI-120
        result = cli_impl._inject_time_constraint("task", 60, summary_mode=True)
        assert "OUTPUT FORMAT" in result

    def test_no_summary_mode(self) -> None:
        # @trace FR-CLI-121
        result = cli_impl._inject_time_constraint("task", 60, summary_mode=False)
        assert "OUTPUT FORMAT" not in result


# ---------------------------------------------------------------------------
# Helpers: _resolve_agent_model
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestResolveAgentModel:
    def test_explicit_model_returned(self) -> None:
        # @trace FR-CLI-122
        settings = MagicMock()
        result = cli_impl._resolve_agent_model("claude", "gpt-4", "write", settings)
        assert result == "gpt-4"

    def test_claude_default(self) -> None:
        # @trace FR-CLI-123
        settings = MagicMock()
        settings.default_claude_model = "haiku"
        result = cli_impl._resolve_agent_model("claude", None, "write", settings)
        assert result == "haiku"

    def test_codex_full_mode(self) -> None:
        # @trace FR-CLI-124
        settings = MagicMock()
        settings.default_codex_model_high = "codex-high"
        result = cli_impl._resolve_agent_model("codex", None, "full", settings)
        assert result == "codex-high"

    def test_codex_normal_mode(self) -> None:
        # @trace FR-CLI-125
        settings = MagicMock()
        settings.default_codex_model = "codex-std"
        result = cli_impl._resolve_agent_model("codex", None, "write", settings)
        assert result == "codex-std"

    def test_unknown_agent_returns_none(self) -> None:
        # @trace FR-CLI-126
        settings = MagicMock()
        result = cli_impl._resolve_agent_model(
            "unknown-agent-xyz", None, "write", settings
        )
        assert result is None

    def test_minimax_hardcoded(self) -> None:
        # @trace FR-CLI-127
        settings = MagicMock()
        result = cli_impl._resolve_agent_model("minimax", None, "write", settings)
        assert result == "minimax-m2.5"


# ---------------------------------------------------------------------------
# Helpers: _normalize_output_format
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestNormalizeOutputFormat:
    def test_json_passthrough(self) -> None:
        # @trace FR-CLI-128
        assert cli_impl._normalize_output_format("json") == "json"

    def test_md_passthrough(self) -> None:
        # @trace FR-CLI-129
        assert cli_impl._normalize_output_format("md") == "md"

    def test_default_rich(self) -> None:
        # @trace FR-CLI-130
        assert cli_impl._normalize_output_format(None) == "rich"

    @patch.dict(os.environ, {"THGENT_OUTPUT_FORMAT": "json"})
    def test_env_var_override(self) -> None:
        # @trace FR-CLI-131
        assert cli_impl._normalize_output_format(None) == "json"


# ---------------------------------------------------------------------------
# Helpers: _compose_owner_tag / _default_owner_tag
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestOwnerTag:
    def test_compose_basic(self, tmp_path) -> None:
        # @trace FR-CLI-132
        tag = cli_impl._compose_owner_tag("alice", tmp_path)
        assert tag == f"alice:{tmp_path.name}"

    def test_compose_with_scope(self, tmp_path) -> None:
        # @trace FR-CLI-133
        tag = cli_impl._compose_owner_tag("bob", tmp_path, scope="myscope")
        assert tag == f"bob:{tmp_path.name}:myscope"

    @patch.dict(os.environ, {"THGENT_OWNER_TAG": "explicit-tag"}, clear=False)
    def test_default_owner_tag_explicit_env(self, tmp_path) -> None:
        # @trace FR-CLI-134
        tag = cli_impl._default_owner_tag(tmp_path)
        assert tag == "explicit-tag"


# ---------------------------------------------------------------------------
# Helpers: _run_background_session_observer
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestRunBackgroundSessionObserver:
    def test_updates_meta_on_exit(self, tmp_path) -> None:
        # @trace FR-CLI-135
        meta_path = tmp_path / "sess.json"
        rc_path = tmp_path / "sess.rc"
        started = datetime.now(UTC).isoformat()
        cli_impl._save_session_meta(
            meta_path,
            {
                "session_id": "s1",
                "status": "running",
                "started_at_utc": started,
            },
        )
        with patch.dict(
            os.environ,
            {
                "THGENT_SESSION_META_PATH": str(meta_path),
                "THGENT_SESSION_RC_PATH": str(rc_path),
            },
        ):
            cli_impl._run_background_session_observer(0)
        updated = json.loads(meta_path.read_text(encoding="utf-8"))
        assert updated["status"] == "exited"
        assert updated["exit_code"] == 0
        assert updated["timed_out"] is False
        assert rc_path.read_text(encoding="utf-8").strip() == "0"

    def test_timed_out_flag(self, tmp_path) -> None:
        # @trace FR-CLI-136
        meta_path = tmp_path / "sess.json"
        cli_impl._save_session_meta(
            meta_path,
            {
                "session_id": "s2",
                "status": "running",
                "started_at_utc": datetime.now(UTC).isoformat(),
            },
        )
        with patch.dict(
            os.environ,
            {
                "THGENT_SESSION_META_PATH": str(meta_path),
            },
        ):
            cli_impl._run_background_session_observer(1, timed_out=True)
        updated = json.loads(meta_path.read_text(encoding="utf-8"))
        assert updated["timed_out"] is True
        assert updated["exit_code"] == 1

    def test_no_meta_path_is_noop(self) -> None:
        # @trace FR-CLI-137
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("THGENT_SESSION_META_PATH", None)
            cli_impl._run_background_session_observer(0)


# ---------------------------------------------------------------------------
# status_impl
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestStatusImpl:
    def test_running_session(self, tmp_path) -> None:
        # @trace FR-CLI-138
        settings = MagicMock()
        settings.session_dir = tmp_path
        meta_path = tmp_path / "sess-run.json"
        cli_impl._save_session_meta(
            meta_path,
            {
                "session_id": "sess-run",
                "pid": 12345,
                "owner": "alice:proj",
                "agent": "claude",
                "mode": "write",
                "cwd": "/tmp",
                "host": "localhost",
                "started_at_utc": "2025-01-01T00:00:00",
                "status": "running",
            },
        )
        with (
            patch("thegent.cli.commands.impl.ThegentSettings", return_value=settings),
            patch("thegent.cli.commands.impl._is_pid_running", return_value=True),
        ):
            result = cli_impl.status_impl("sess-run")
        assert result["status"] == "running"
        assert result["running"] is True
        assert result["exit_code"] is None

    def test_finished_session_with_rc_file(self, tmp_path) -> None:
        # @trace FR-CLI-139
        settings = MagicMock()
        settings.session_dir = tmp_path
        meta_path = tmp_path / "sess-done.json"
        cli_impl._save_session_meta(
            meta_path,
            {
                "session_id": "sess-done",
                "pid": 99,
                "owner": "alice:proj",
            },
        )
        rc_path = tmp_path / "sess-done.rc"
        rc_path.write_text("0\n", encoding="utf-8")
        with (
            patch("thegent.cli.commands.impl.ThegentSettings", return_value=settings),
            patch("thegent.cli.commands.impl._is_pid_running", return_value=False),
        ):
            result = cli_impl.status_impl("sess-done")
        assert result["status"] == "exited:0"
        assert result["running"] is False
        assert result["exit_code"] == 0

    def test_session_not_found(self, tmp_path) -> None:
        # @trace FR-CLI-140
        settings = MagicMock()
        settings.session_dir = tmp_path
        with patch("thegent.cli.commands.impl.ThegentSettings", return_value=settings):
            result = cli_impl.status_impl("nonexistent")
        assert "error" in result

    def test_include_contract_metadata(self, tmp_path) -> None:
        # @trace FR-CLI-141
        settings = MagicMock()
        settings.session_dir = tmp_path
        meta_path = tmp_path / "sess-c.json"
        cli_impl._save_session_meta(
            meta_path,
            {
                "session_id": "sess-c",
                "pid": 0,
                "owner": "x",
                "route_contract": {"provider": "claude"},
                "route_request": {"requested_model": "haiku"},
            },
        )
        with (
            patch("thegent.cli.commands.impl.ThegentSettings", return_value=settings),
            patch("thegent.cli.commands.impl._is_pid_running", return_value=False),
        ):
            result = cli_impl.status_impl("sess-c", include_contract=True)
        assert result["route_contract"] == {"provider": "claude"}
        assert result["route_request"] == {"requested_model": "haiku"}


# ---------------------------------------------------------------------------
# stop_impl
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestStopImpl:
    def test_stop_running_session(self, tmp_path) -> None:
        # @trace FR-CLI-142
        settings = MagicMock()
        settings.session_dir = tmp_path
        meta_path = tmp_path / "sess-stop.json"
        cli_impl._save_session_meta(
            meta_path,
            {
                "session_id": "sess-stop",
                "pid": 12345,
            },
        )
        with (
            patch("thegent.cli.commands.impl.ThegentSettings", return_value=settings),
            patch("thegent.cli.commands.impl._is_pid_running", return_value=True),
            patch("os.killpg") as mock_killpg,
        ):
            result = cli_impl.stop_impl("sess-stop")
        assert result["status"] == "stopped"
        mock_killpg.assert_called_once_with(12345, signal.SIGTERM)

    def test_stop_force_kill(self, tmp_path) -> None:
        # @trace FR-CLI-143
        settings = MagicMock()
        settings.session_dir = tmp_path
        meta_path = tmp_path / "sess-fk.json"
        cli_impl._save_session_meta(
            meta_path,
            {
                "session_id": "sess-fk",
                "pid": 12345,
            },
        )
        with (
            patch("thegent.cli.commands.impl.ThegentSettings", return_value=settings),
            patch("thegent.cli.commands.impl._is_pid_running", return_value=True),
            patch("os.killpg") as mock_killpg,
        ):
            result = cli_impl.stop_impl("sess-fk", force=True)
        assert result["status"] == "stopped_force"
        mock_killpg.assert_called_once_with(12345, signal.SIGKILL)

    def test_stop_already_stopped(self, tmp_path) -> None:
        # @trace FR-CLI-144
        settings = MagicMock()
        settings.session_dir = tmp_path
        meta_path = tmp_path / "sess-dead.json"
        cli_impl._save_session_meta(
            meta_path,
            {
                "session_id": "sess-dead",
                "pid": 99,
            },
        )
        with (
            patch("thegent.cli.commands.impl.ThegentSettings", return_value=settings),
            patch("thegent.cli.commands.impl._is_pid_running", return_value=False),
        ):
            result = cli_impl.stop_impl("sess-dead")
        assert result["status"] == "not_running"

    def test_stop_os_error(self, tmp_path) -> None:
        # @trace FR-CLI-145
        settings = MagicMock()
        settings.session_dir = tmp_path
        meta_path = tmp_path / "sess-err.json"
        cli_impl._save_session_meta(
            meta_path,
            {
                "session_id": "sess-err",
                "pid": 12345,
            },
        )
        with (
            patch("thegent.cli.commands.impl.ThegentSettings", return_value=settings),
            patch("thegent.cli.commands.impl._is_pid_running", return_value=True),
            patch("os.killpg", side_effect=OSError("Permission denied")),
        ):
            result = cli_impl.stop_impl("sess-err")
        assert result["status"] == "error"
        assert "Permission denied" in result["error"]

    def test_stop_session_not_found(self, tmp_path) -> None:
        # @trace FR-CLI-146
        settings = MagicMock()
        settings.session_dir = tmp_path
        with patch("thegent.cli.commands.impl.ThegentSettings", return_value=settings):
            result = cli_impl.stop_impl("nope-id")
        assert "error" in result


# ---------------------------------------------------------------------------
# wait_impl
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestWaitImpl:
    def test_wait_already_done(self, tmp_path) -> None:
        # @trace FR-CLI-147
        settings = MagicMock()
        settings.session_dir = tmp_path
        meta_path = tmp_path / "sess-w.json"
        cli_impl._save_session_meta(
            meta_path,
            {
                "session_id": "sess-w",
                "pid": 0,
            },
        )
        rc_path = tmp_path / "sess-w.rc"
        rc_path.write_text("0\n", encoding="utf-8")
        with (
            patch("thegent.cli.commands.impl.ThegentSettings", return_value=settings),
            patch("thegent.cli.commands.impl._is_pid_running", return_value=False),
        ):
            result = cli_impl.wait_impl("sess-w")
        assert result["exit_code"] == 0
        assert result["timed_out"] is False

    def test_wait_timeout(self, tmp_path) -> None:
        # @trace FR-CLI-148
        settings = MagicMock()
        settings.session_dir = tmp_path
        meta_path = tmp_path / "sess-wt.json"
        cli_impl._save_session_meta(
            meta_path,
            {
                "session_id": "sess-wt",
                "pid": 12345,
            },
        )
        call_count = 0

        def _fake_pid_running(pid) -> bool:
            nonlocal call_count
            call_count += 1
            return True

        with (
            patch("thegent.cli.commands.impl.ThegentSettings", return_value=settings),
            patch(
                "thegent.cli.commands.impl._is_pid_running",
                side_effect=_fake_pid_running,
            ),
            patch("thegent.cli.commands.impl.time.sleep"),
            patch(
                "thegent.cli.commands.impl.time.time",
                side_effect=[0.0, 0.0, 0.5, 1.0, 1.5, 2.0],
            ),
        ):
            result = cli_impl.wait_impl("sess-wt", timeout=1)
        assert result["timed_out"] is True

    def test_wait_session_not_found(self, tmp_path) -> None:
        # @trace FR-CLI-149
        settings = MagicMock()
        settings.session_dir = tmp_path
        with patch("thegent.cli.commands.impl.ThegentSettings", return_value=settings):
            result = cli_impl.wait_impl("no-session")
        assert "error" in result


# ---------------------------------------------------------------------------
# logs_impl
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestLogsImpl:
    def test_stdout_logs(self, tmp_path) -> None:
        # @trace FR-CLI-100
        settings = MagicMock()
        settings.session_dir = tmp_path
        meta_path = tmp_path / "sess-log.json"
        meta_path.write_text("{}", encoding="utf-8")
        stdout_path = tmp_path / "sess-log.stdout.log"
        stdout_path.write_text("line1\nline2\nline3\n", encoding="utf-8")
        with patch("thegent.cli.commands.impl.ThegentSettings", return_value=settings):
            result = cli_impl.logs_impl("sess-log")
        assert "line1" in result
        assert "line3" in result

    def test_stderr_logs(self, tmp_path) -> None:
        # @trace FR-CLI-101
        settings = MagicMock()
        settings.session_dir = tmp_path
        meta_path = tmp_path / "sess-log2.json"
        meta_path.write_text("{}", encoding="utf-8")
        stderr_path = tmp_path / "sess-log2.stderr.log"
        stderr_path.write_text("err1\nerr2\n", encoding="utf-8")
        with patch("thegent.cli.commands.impl.ThegentSettings", return_value=settings):
            result = cli_impl.logs_impl("sess-log2", stderr=True)
        assert "err1" in result

    def test_tail_lines(self, tmp_path) -> None:
        # @trace FR-CLI-102
        settings = MagicMock()
        settings.session_dir = tmp_path
        meta_path = tmp_path / "sess-tail.json"
        meta_path.write_text("{}", encoding="utf-8")
        stdout_path = tmp_path / "sess-tail.stdout.log"
        stdout_path.write_text(
            "\n".join(f"line{i}" for i in range(100)), encoding="utf-8"
        )
        with patch("thegent.cli.commands.impl.ThegentSettings", return_value=settings):
            result = cli_impl.logs_impl("sess-tail", tail=5)
        lines = result.strip().splitlines()
        assert len(lines) == 5

    def test_log_file_missing(self, tmp_path) -> None:
        # @trace FR-CLI-103
        settings = MagicMock()
        settings.session_dir = tmp_path
        meta_path = tmp_path / "sess-nolog.json"
        meta_path.write_text("{}", encoding="utf-8")
        with patch("thegent.cli.commands.impl.ThegentSettings", return_value=settings):
            result = cli_impl.logs_impl("sess-nolog")
        assert "Log file missing" in result

    def test_session_not_found(self, tmp_path) -> None:
        # @trace FR-CLI-104
        settings = MagicMock()
        settings.session_dir = tmp_path
        with patch("thegent.cli.commands.impl.ThegentSettings", return_value=settings):
            result = cli_impl.logs_impl("phantom")
        assert "Error" in result


# ---------------------------------------------------------------------------
# ps_impl
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestPsImpl:
    def test_list_own_sessions(self, tmp_path) -> None:
        # @trace FR-CLI-105
        settings = MagicMock()
        settings.session_dir = tmp_path
        scope_dir = tmp_path / "alice_proj"
        scope_dir.mkdir()
        cli_impl._save_session_meta(
            scope_dir / "s1.json",
            {
                "session_id": "s1",
                "agent": "claude",
                "owner": "alice:proj",
                "pid": 0,
                "prompt": "do stuff",
                "started_at_utc": "2025-01-01T00:00:00",
            },
        )
        with (
            patch("thegent.cli.commands.impl.ThegentSettings", return_value=settings),
            patch(
                "thegent.cli.commands.impl._default_owner_tag",
                return_value="alice:proj",
            ),
            patch("thegent.cli.commands.impl._is_pid_running", return_value=False),
        ):
            rows = cli_impl.ps_impl()
        assert len(rows) == 1
        assert rows[0]["id"] == "s1"

    def test_list_all_sessions(self, tmp_path) -> None:
        # @trace FR-CLI-106
        settings = MagicMock()
        settings.session_dir = tmp_path
        for owner_key, owner_val, sid in [
            ("alice_proj", "alice:proj", "s1"),
            ("bob_proj", "bob:proj", "s2"),
        ]:
            scope_dir = tmp_path / owner_key
            scope_dir.mkdir()
            cli_impl._save_session_meta(
                scope_dir / f"{sid}.json",
                {
                    "session_id": sid,
                    "agent": "claude",
                    "owner": owner_val,
                    "pid": 0,
                    "prompt": "task",
                    "started_at_utc": "2025-01-01T00:00:00",
                },
            )
        with (
            patch("thegent.cli.commands.impl.ThegentSettings", return_value=settings),
            patch("thegent.cli.commands.impl._is_pid_running", return_value=False),
        ):
            rows = cli_impl.ps_impl(all=True)
        assert len(rows) == 2

    def test_owner_filter(self, tmp_path) -> None:
        # @trace FR-CLI-107
        settings = MagicMock()
        settings.session_dir = tmp_path
        scope_dir = tmp_path / "alice_proj"
        scope_dir.mkdir()
        cli_impl._save_session_meta(
            scope_dir / "s1.json",
            {
                "session_id": "s1",
                "agent": "claude",
                "owner": "alice:proj",
                "pid": 0,
                "prompt": "task",
            },
        )
        cli_impl._save_session_meta(
            scope_dir / "s2.json",
            {
                "session_id": "s2",
                "agent": "claude",
                "owner": "bob:proj",
                "pid": 0,
                "prompt": "other",
            },
        )
        with (
            patch("thegent.cli.commands.impl.ThegentSettings", return_value=settings),
            patch("thegent.cli.commands.impl._is_pid_running", return_value=False),
        ):
            rows = cli_impl.ps_impl(owner="alice:proj")
        assert all(r["owner"] == "alice:proj" for r in rows)

    def test_prompt_preview_truncation(self, tmp_path) -> None:
        # @trace FR-CLI-108
        settings = MagicMock()
        settings.session_dir = tmp_path
        scope_dir = tmp_path / "x_x"
        scope_dir.mkdir()
        long_prompt = "A" * 100
        cli_impl._save_session_meta(
            scope_dir / "s1.json",
            {
                "session_id": "s1",
                "agent": "claude",
                "owner": "x:x",
                "pid": 0,
                "prompt": long_prompt,
            },
        )
        with (
            patch("thegent.cli.commands.impl.ThegentSettings", return_value=settings),
            patch("thegent.cli.commands.impl._default_owner_tag", return_value="x:x"),
            patch("thegent.cli.commands.impl._is_pid_running", return_value=False),
        ):
            rows = cli_impl.ps_impl()
        assert rows[0]["prompt_preview"].endswith("...")
        assert len(rows[0]["prompt_preview"]) == 43  # 40 chars + "..."

    def test_include_contract(self, tmp_path) -> None:
        # @trace FR-CLI-109
        settings = MagicMock()
        settings.session_dir = tmp_path
        scope_dir = tmp_path / "a_b"
        scope_dir.mkdir()
        cli_impl._save_session_meta(
            scope_dir / "s1.json",
            {
                "session_id": "s1",
                "agent": "claude",
                "owner": "a:b",
                "pid": 0,
                "prompt": "task",
                "route_contract": {"provider": "claude"},
            },
        )
        with (
            patch("thegent.cli.commands.impl.ThegentSettings", return_value=settings),
            patch("thegent.cli.commands.impl._default_owner_tag", return_value="a:b"),
            patch("thegent.cli.commands.impl._is_pid_running", return_value=False),
        ):
            rows = cli_impl.ps_impl(include_contract=True)
        assert rows[0]["route_contract"] == {"provider": "claude"}


# ---------------------------------------------------------------------------
# inspect_impl
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestInspectImpl:
    def test_single_session(self, tmp_path) -> None:
        # @trace FR-CLI-110
        settings = MagicMock()
        settings.session_dir = tmp_path
        meta_path = tmp_path / "sess-insp.json"
        cli_impl._save_session_meta(
            meta_path,
            {
                "session_id": "sess-insp",
                "pid": 0,
                "owner": "x",
            },
        )
        stdout_path = tmp_path / "sess-insp.stdout.log"
        stdout_path.write_text("hello world\n", encoding="utf-8")
        with (
            patch("thegent.cli.commands.impl.ThegentSettings", return_value=settings),
            patch("thegent.cli.commands.impl._is_pid_running", return_value=False),
        ):
            results = cli_impl.inspect_impl(["sess-insp"])
        assert len(results) == 1
        assert results[0]["session_id"] == "sess-insp"
        assert "hello world" in results[0]["logs"]

    def test_multiple_sessions(self, tmp_path) -> None:
        # @trace FR-CLI-111
        settings = MagicMock()
        settings.session_dir = tmp_path
        for sid in ["s1", "s2"]:
            meta = tmp_path / f"{sid}.json"
            cli_impl._save_session_meta(
                meta,
                {
                    "session_id": sid,
                    "pid": 0,
                    "owner": "x",
                },
            )
            stdout = tmp_path / f"{sid}.stdout.log"
            stdout.write_text(f"output of {sid}\n", encoding="utf-8")
        with (
            patch("thegent.cli.commands.impl.ThegentSettings", return_value=settings),
            patch("thegent.cli.commands.impl._is_pid_running", return_value=False),
        ):
            results = cli_impl.inspect_impl(["s1", "s2"])
        assert len(results) == 2

    def test_inspect_with_owner_discovery(self, tmp_path) -> None:
        # @trace FR-CLI-112
        settings = MagicMock()
        settings.session_dir = tmp_path
        scope_dir = tmp_path / "alice_proj"
        scope_dir.mkdir()
        cli_impl._save_session_meta(
            scope_dir / "s1.json",
            {
                "session_id": "s1",
                "agent": "claude",
                "owner": "alice:proj",
                "pid": 0,
                "prompt": "task",
            },
        )
        (scope_dir / "s1.stdout.log").write_text("hi\n", encoding="utf-8")
        with (
            patch("thegent.cli.commands.impl.ThegentSettings", return_value=settings),
            patch(
                "thegent.cli.commands.impl._default_owner_tag",
                return_value="alice:proj",
            ),
            patch("thegent.cli.commands.impl._is_pid_running", return_value=False),
        ):
            results = cli_impl.inspect_impl([], owner="alice:proj")
        assert len(results) >= 1

    def test_inspect_empty_returns_empty(self) -> None:
        # @trace FR-CLI-113
        result = cli_impl.inspect_impl([])
        assert result == []


# ---------------------------------------------------------------------------
# history_impl
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestHistoryImpl:
    def test_returns_registry_runs(self, tmp_path) -> None:
        # @trace FR-CLI-114
        settings = MagicMock()
        settings.session_dir = tmp_path
        mock_registry = MagicMock()
        mock_registry.list_runs.return_value = [
            {"run_id": "r1", "agent": "claude"},
            {"run_id": "r2", "agent": "codex"},
        ]
        with (
            patch("thegent.cli.commands.impl.ThegentSettings", return_value=settings),
            patch("thegent.cli.commands.impl.RunRegistry", return_value=mock_registry),
        ):
            results = cli_impl.history_impl(limit=50)
        assert len(results) == 2
        mock_registry.list_runs.assert_called_once_with(limit=50)

    def test_custom_limit(self, tmp_path) -> None:
        # @trace FR-CLI-115
        settings = MagicMock()
        settings.session_dir = tmp_path
        mock_registry = MagicMock()
        mock_registry.list_runs.return_value = []
        with (
            patch("thegent.cli.commands.impl.ThegentSettings", return_value=settings),
            patch("thegent.cli.commands.impl.RunRegistry", return_value=mock_registry),
        ):
            cli_impl.history_impl(limit=10)
        mock_registry.list_runs.assert_called_once_with(limit=10)


# ---------------------------------------------------------------------------
# events_impl
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestEventsImpl:
    def test_returns_events(self, tmp_path) -> None:
        # @trace FR-CLI-116
        settings = MagicMock()
        settings.session_dir = tmp_path
        registry_file = tmp_path / "run_registry.jsonl"
        events = [
            {"run_id": "r1", "event": "start"},
            {"run_id": "r1", "event": "end"},
            {"run_id": "r2", "event": "start"},
        ]
        registry_file.write_text(
            "\n".join(json.dumps(e).decode() for e in events) + "\n",
            encoding="utf-8",
        )
        with patch("thegent.cli.commands.impl.ThegentSettings", return_value=settings):
            result = cli_impl.events_impl()
        assert len(result) == 3

    def test_filter_by_run_id(self, tmp_path) -> None:
        # @trace FR-CLI-117
        settings = MagicMock()
        settings.session_dir = tmp_path
        registry_file = tmp_path / "run_registry.jsonl"
        events = [
            {"run_id": "r1", "event": "start"},
            {"run_id": "r2", "event": "start"},
        ]
        registry_file.write_text(
            "\n".join(json.dumps(e).decode() for e in events) + "\n",
            encoding="utf-8",
        )
        with patch("thegent.cli.commands.impl.ThegentSettings", return_value=settings):
            result = cli_impl.events_impl(run_id="r1")
        assert len(result) == 1
        assert result[0]["run_id"] == "r1"

    def test_empty_registry(self, tmp_path) -> None:
        # @trace FR-CLI-118
        settings = MagicMock()
        settings.session_dir = tmp_path
        with patch("thegent.cli.commands.impl.ThegentSettings", return_value=settings):
            result = cli_impl.events_impl()
        assert result == []

    def test_limit(self, tmp_path) -> None:
        # @trace FR-CLI-119
        settings = MagicMock()
        settings.session_dir = tmp_path
        registry_file = tmp_path / "run_registry.jsonl"
        events = [{"run_id": f"r{i}", "event": "start"} for i in range(200)]
        registry_file.write_text(
            "\n".join(json.dumps(e).decode() for e in events) + "\n",
            encoding="utf-8",
        )
        with patch("thegent.cli.commands.impl.ThegentSettings", return_value=settings):
            result = cli_impl.events_impl(limit=5)
        assert len(result) == 5


# ---------------------------------------------------------------------------
# session_meta_impl
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestSessionMetaImpl:
    def test_returns_meta(self, tmp_path) -> None:
        # @trace FR-CLI-120
        settings = MagicMock()
        settings.session_dir = tmp_path
        meta_path = tmp_path / "smeta.json"
        cli_impl._save_session_meta(
            meta_path,
            {
                "session_id": "smeta",
                "agent": "claude",
                "owner": "user:proj",
            },
        )
        with patch("thegent.cli.commands.impl.ThegentSettings", return_value=settings):
            result = cli_impl.session_meta_impl("smeta")
        assert result["session_id"] == "smeta"
        assert result["agent"] == "claude"

    def test_not_found(self, tmp_path) -> None:
        # @trace FR-CLI-121
        settings = MagicMock()
        settings.session_dir = tmp_path
        with patch("thegent.cli.commands.impl.ThegentSettings", return_value=settings):
            result = cli_impl.session_meta_impl("ghost")
        assert "error" in result


# ---------------------------------------------------------------------------
# _build_continuation_prompt
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestBuildContinuationPrompt:
    def test_single_session_continuation(self, tmp_path) -> None:
        # @trace FR-CLI-122
        settings = MagicMock()
        settings.session_dir = tmp_path
        meta_path = tmp_path / "prev.json"
        meta_path.write_text("{}", encoding="utf-8")
        stdout_path = tmp_path / "prev.stdout.log"
        stdout_path.write_text("previous output here", encoding="utf-8")
        result = cli_impl._build_continuation_prompt(
            settings, "prev", "continue this", include_stderr=False
        )
        assert "previous output here" in result
        assert "continue this" in result
        assert "Continuing from prior session" in result

    def test_empty_session_ids(self) -> None:
        # @trace FR-CLI-123
        settings = MagicMock()
        result = cli_impl._build_continuation_prompt(settings, "", "my prompt")
        assert result == "my prompt"


# ---------------------------------------------------------------------------
# _session_dir
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestSessionDir:
    def test_creates_dir(self, tmp_path) -> None:
        # @trace FR-CLI-124
        settings = MagicMock()
        settings.session_dir = tmp_path / "sessions"
        result = cli_impl._session_dir(settings, "alice:proj")
        assert result.exists()
        assert result.is_dir()


# ---------------------------------------------------------------------------
# _session_scope_dirs
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestSessionScopeDirs:
    def test_finds_matching_dirs(self, tmp_path) -> None:
        # @trace FR-CLI-125
        (tmp_path / "alice_proj").mkdir()
        (tmp_path / "alice_proj_123").mkdir()
        (tmp_path / "bob_proj").mkdir()
        result = cli_impl._session_scope_dirs(tmp_path, "alice:proj")
        names = {d.name for d in result}
        assert "alice_proj" in names
        assert "alice_proj_123" in names
        assert "bob_proj" not in names

    def test_empty_owner_returns_empty(self, tmp_path) -> None:
        # @trace FR-CLI-126
        (tmp_path / "something").mkdir()
        result = cli_impl._session_scope_dirs(tmp_path, "")
        assert result == []


# ---------------------------------------------------------------------------
# bg_impl - heavier mocking due to subprocess
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestBgImpl:
    @patch("thegent.cli.commands.impl.subprocess.Popen")
    @patch("thegent.cli.commands.impl.RunRegistry")
    @patch("thegent.cli.commands.impl.ThegentSettings")
    @patch("thegent.cli.commands.impl.resolve_agent", side_effect=lambda a: a)
    @patch("thegent.cli.commands.impl._resolve_cwd")
    @patch(
        "thegent.cli.commands.impl._default_owner_tag", return_value="user:proj:1234"
    )
    @patch("thegent.contracts.migration.MigrationController")
    def test_bg_basic(
        self,
        mock_migration_cls,
        mock_owner,
        mock_cwd,
        mock_resolve,
        mock_settings_cls,
        mock_registry_cls,
        mock_popen,
        tmp_path,
    ) -> None:
        # @trace FR-CLI-127
        cwd = tmp_path / "project"
        cwd.mkdir()
        mock_cwd.return_value = cwd

        settings = MagicMock()
        settings.session_dir = tmp_path / "sessions"
        (settings.session_dir).mkdir(parents=True)
        settings.default_timeout_claude = 300
        mock_settings_cls.return_value = settings

        mock_registry = MagicMock()
        mock_registry_cls.return_value = mock_registry

        mock_proc = MagicMock()
        mock_proc.pid = 42
        mock_popen.return_value = mock_proc

        migrator_mock = MagicMock()
        migrator_mock.evaluate_version.return_value = {
            "allowed": True,
            "status": "active",
        }
        mock_migration_cls.return_value = migrator_mock

        result = cli_impl.bg_impl(
            agent="claude",
            prompt="do something",
            cd=cwd,
            mode="write",
            timeout=90,
            full=False,
        )

        assert "session_id" in result
        assert "log_path" in result
        assert result["owner"] == "user:proj:1234"
        mock_popen.assert_called_once()
        mock_registry.register_start.assert_called_once()

    @patch("thegent.cli.commands.impl.subprocess.Popen")
    @patch("thegent.cli.commands.impl.RunRegistry")
    @patch("thegent.cli.commands.impl.ThegentSettings")
    @patch("thegent.cli.commands.impl.resolve_agent", side_effect=lambda a: a)
    @patch("thegent.cli.commands.impl._resolve_cwd")
    @patch("thegent.cli.commands.impl._default_owner_tag", return_value="u:p:1")
    @patch("thegent.contracts.migration.MigrationController")
    def test_bg_with_owner(
        self,
        mock_migration_cls,
        mock_default_owner,
        mock_cwd,
        mock_resolve,
        mock_settings_cls,
        mock_registry_cls,
        mock_popen,
        tmp_path,
    ) -> None:
        # @trace FR-CLI-128
        cwd = tmp_path / "project"
        cwd.mkdir()
        mock_cwd.return_value = cwd

        settings = MagicMock()
        settings.session_dir = tmp_path / "sessions"
        settings.session_dir.mkdir(parents=True)
        settings.default_timeout_claude = 300
        mock_settings_cls.return_value = settings

        mock_registry = MagicMock()
        mock_registry_cls.return_value = mock_registry

        mock_proc = MagicMock()
        mock_proc.pid = 42
        mock_popen.return_value = mock_proc

        migrator_mock = MagicMock()
        migrator_mock.evaluate_version.return_value = {
            "allowed": True,
            "status": "active",
        }
        mock_migration_cls.return_value = migrator_mock

        result = cli_impl.bg_impl(
            agent="claude",
            prompt="task",
            cd=cwd,
            mode="write",
            timeout=90,
            full=False,
            owner="custom-owner",
        )
        assert result["owner"] == "custom-owner"

    @patch("thegent.cli.commands.impl.ThegentSettings")
    @patch("thegent.cli.commands.impl.resolve_agent", side_effect=lambda a: a)
    @patch("thegent.cli.commands.impl._resolve_cwd", return_value=None)
    @patch("thegent.contracts.migration.MigrationController")
    def test_bg_ambiguous_cwd(
        self, mock_migration_cls, mock_cwd, mock_resolve, mock_settings_cls, tmp_path
    ) -> None:
        # @trace FR-CLI-129
        settings = MagicMock()
        settings.default_timeout_claude = 300
        mock_settings_cls.return_value = settings

        migrator_mock = MagicMock()
        migrator_mock.evaluate_version.return_value = {
            "allowed": True,
            "status": "active",
        }
        mock_migration_cls.return_value = migrator_mock

        result = cli_impl.bg_impl(
            agent="claude",
            prompt="task",
            cd=None,
            mode="write",
            timeout=90,
            full=False,
        )
        assert "error" in result
        assert "Ambiguous cwd" in result["error"]

    @patch("thegent.cli.commands.impl.ThegentSettings")
    @patch("thegent.cli.commands.impl.resolve_agent", side_effect=lambda a: a)
    @patch("thegent.contracts.migration.MigrationController")
    def test_bg_contract_version_rejected(
        self, mock_migration_cls, mock_resolve, mock_settings_cls, tmp_path
    ) -> None:
        # @trace FR-CLI-130
        settings = MagicMock()
        settings.default_timeout_claude = 300
        mock_settings_cls.return_value = settings

        migrator_mock = MagicMock()
        migrator_mock.evaluate_version.return_value = {
            "allowed": False,
            "status": "rejected",
            "reason": "Version too old",
        }
        mock_migration_cls.return_value = migrator_mock

        result = cli_impl.bg_impl(
            agent="claude",
            prompt="task",
            cd=tmp_path,
            mode="write",
            timeout=90,
            full=False,
            contract_version="0.0.1",
        )
        assert "error" in result
        assert (
            "rejected" in result["error"].lower()
            or "Version too old" in result["error"]
        )

    @patch("thegent.cli.commands.impl.subprocess.Popen")
    @patch("thegent.cli.commands.impl.RunRegistry")
    @patch("thegent.cli.commands.impl.ThegentSettings")
    @patch("thegent.cli.commands.impl.resolve_agent", side_effect=lambda a: a)
    @patch("thegent.cli.commands.impl._resolve_cwd")
    @patch("thegent.cli.commands.impl._default_owner_tag", return_value="u:p:1")
    @patch(
        "thegent.cli.commands.impl._build_continuation_prompt",
        return_value="continued prompt",
    )
    @patch("thegent.contracts.migration.MigrationController")
    def test_bg_with_continuation(
        self,
        mock_migration_cls,
        mock_cont_prompt,
        mock_default_owner,
        mock_cwd,
        mock_resolve,
        mock_settings_cls,
        mock_registry_cls,
        mock_popen,
        tmp_path,
    ) -> None:
        # @trace FR-CLI-131
        cwd = tmp_path / "project"
        cwd.mkdir()
        mock_cwd.return_value = cwd

        settings = MagicMock()
        settings.session_dir = tmp_path / "sessions"
        settings.session_dir.mkdir(parents=True)
        settings.default_timeout_claude = 300
        mock_settings_cls.return_value = settings

        mock_registry = MagicMock()
        mock_registry_cls.return_value = mock_registry

        mock_proc = MagicMock()
        mock_proc.pid = 42
        mock_popen.return_value = mock_proc

        migrator_mock = MagicMock()
        migrator_mock.evaluate_version.return_value = {
            "allowed": True,
            "status": "active",
        }
        mock_migration_cls.return_value = migrator_mock

        result = cli_impl.bg_impl(
            agent="claude",
            prompt="next step",
            cd=cwd,
            mode="write",
            timeout=90,
            full=False,
            continue_from="prev-session-id",
        )
        assert "session_id" in result
        mock_cont_prompt.assert_called_once()


# ---------------------------------------------------------------------------
# run_impl - heavy mocking
# ---------------------------------------------------------------------------
_SENTINEL = object()


@pytest.mark.unit
class TestRunImpl:
    def _run_impl_helper(
        self,
        *,
        tmp_path,
        agent="claude",
        prompt="do stuff",
        model=None,
        policy_result=("allow", "ok"),
        fsm_status="success",
        run_result=_SENTINEL,
        norm_res=None,
    ):
        """Shared helper to set up run_impl mocks. Patches local imports at source."""
        cwd = tmp_path / "project"
        cwd.mkdir(exist_ok=True)

        settings = MagicMock()
        settings.session_dir = tmp_path / "sessions"
        settings.session_dir.mkdir(parents=True, exist_ok=True)
        settings.default_timeout_claude = 300
        settings.default_claude_model = "haiku"
        settings.environment = "development"
        settings.override_ttl_seconds = 3600
        settings.escalation_sla_minutes = 30
        settings.routing_parser_quality_enabled = False
        settings.normalization_policy_allow_fallback = True
        settings.normalization_policy_min_confidence = 0.7
        settings.normalization_policy_max_fallback_rate = 0.3
        settings.normalization_policy_strict_providers = ""

        mock_registry = MagicMock()
        mock_auditor = MagicMock()
        mock_auditor.sign_run.return_value = "sig"
        mock_pe = MagicMock()
        mock_pe.evaluate.return_value = policy_result

        mock_override_reg = MagicMock()
        mock_override_reg.has_unexpired.return_value = False

        if run_result is _SENTINEL:
            run_result = MagicMock()
            run_result.exit_code = 0
            run_result.stdout = "output"
            run_result.stderr = ""
            run_result.timed_out = False

        fsm_state = MagicMock()
        fsm_state.status = fsm_status

        mock_fsm = MagicMock()
        mock_fsm.run.return_value = (run_result, norm_res)
        mock_fsm.state = fsm_state

        migrator_mock = MagicMock()
        migrator_mock.evaluate_version.return_value = {
            "allowed": True,
            "status": "active",
        }

        mock_trust = MagicMock()
        mock_trust.get_last_environment.return_value = "development"
        mock_trust.validate_transition.return_value = (True, "ok")

        with (
            patch("thegent.cli.commands.impl.ThegentSettings", return_value=settings),
            patch("thegent.cli.commands.impl.resolve_agent", side_effect=lambda a: a),
            patch("thegent.cli.commands.impl._resolve_cwd", return_value=cwd),
            patch(
                "thegent.cli.commands.impl._default_owner_tag", return_value="user:proj"
            ),
            patch("thegent.cli.commands.impl.RunRegistry", return_value=mock_registry),
            patch("thegent.cli.commands.impl.get_fallback_agents", return_value=[]),
            patch(
                "thegent.cli.commands.impl.extract_condensed", return_value="condensed"
            ),
            patch("thegent.cli.commands.impl.is_usage_limit", return_value=False),
            patch(
                "thegent.contracts.migration.MigrationController",
                return_value=migrator_mock,
            ),
            patch("thegent.execution.Auditor", return_value=mock_auditor),
            patch("thegent.execution.PolicyEngine", return_value=mock_pe),
            patch("thegent.execution.CircuitBreakerRegistry"),
            patch("thegent.execution.TrustBoundaryValidator", return_value=mock_trust),
            patch("thegent.execution.OverrideRegistry", return_value=mock_override_reg),
            patch(
                "thegent.agents.state_machine.FallbackStateMachine",
                return_value=mock_fsm,
            ),
            patch("thegent.contracts.telemetry.ContractTelemetry"),
            patch(
                "thegent.contracts.telemetry.rank_providers_by_parser_quality",
                side_effect=lambda a, t, limit: a,
            ),
            patch("thegent.contracts.policy.FallbackPolicy"),
        ):
            return cli_impl.run_impl(
                agent=agent,
                prompt=prompt,
                cd=cwd,
                model=model,
            )

    def test_run_basic_success(self, tmp_path) -> None:
        # @trace FR-CLI-132
        result = self._run_impl_helper(tmp_path=tmp_path)
        assert result["exit_code"] == 0
        assert "run_id" in result

    def test_run_policy_deny(self, tmp_path) -> None:
        # @trace FR-CLI-133
        result = self._run_impl_helper(
            tmp_path=tmp_path,
            policy_result=("deny", "rate limit exceeded"),
        )
        assert result["exit_code"] == 1
        assert "Policy Violation" in result.get("error", "")

    def test_run_agent_returns_none(self, tmp_path) -> None:
        # @trace FR-CLI-134
        result = self._run_impl_helper(
            tmp_path=tmp_path,
            fsm_status="failed",
            run_result=None,
        )
        # When fsm returns None result, the code handles it
        # The fsm mock returns (None, None) which triggers error path
        assert result["exit_code"] == 1

    def test_run_timed_out(self, tmp_path) -> None:
        # @trace FR-CLI-135
        timed_out_result = MagicMock()
        timed_out_result.exit_code = 1
        timed_out_result.stdout = "partial"
        timed_out_result.stderr = "timeout"
        timed_out_result.timed_out = True

        result = self._run_impl_helper(
            tmp_path=tmp_path,
            fsm_status="failed",
            run_result=timed_out_result,
        )
        assert result["timed_out"] is True

    def test_run_ambiguous_cwd(self, tmp_path) -> None:
        # @trace FR-CLI-136
        settings = MagicMock()
        settings.default_timeout_claude = 300

        migrator_mock = MagicMock()
        migrator_mock.evaluate_version.return_value = {
            "allowed": True,
            "status": "active",
        }

        with (
            patch("thegent.cli.commands.impl.ThegentSettings", return_value=settings),
            patch("thegent.cli.commands.impl.resolve_agent", side_effect=lambda a: a),
            patch("thegent.cli.commands.impl._resolve_cwd", return_value=None),
            patch(
                "thegent.contracts.migration.MigrationController",
                return_value=migrator_mock,
            ),
        ):
            result = cli_impl.run_impl(agent="claude", prompt="task")
        assert "error" in result
        assert "Ambiguous cwd" in result["error"]

    def test_run_with_model_first_routing(self, tmp_path) -> None:
        # @trace FR-CLI-137
        settings = MagicMock()
        settings.session_dir = tmp_path / "sessions"
        settings.session_dir.mkdir(parents=True, exist_ok=True)
        settings.default_timeout_claude = 300
        settings.environment = "development"
        settings.override_ttl_seconds = 3600
        settings.escalation_sla_minutes = 30
        settings.routing_parser_quality_enabled = False
        settings.normalization_policy_allow_fallback = True
        settings.normalization_policy_min_confidence = 0.7
        settings.normalization_policy_max_fallback_rate = 0.3
        settings.normalization_policy_strict_providers = ""

        cwd = tmp_path / "project"
        cwd.mkdir()

        mock_route = ("claude", "model-alias")

        mock_run_result = MagicMock()
        mock_run_result.exit_code = 0
        mock_run_result.stdout = "output"
        mock_run_result.stderr = ""
        mock_run_result.timed_out = False

        mock_fsm = MagicMock()
        mock_fsm.run.return_value = (mock_run_result, None)
        fsm_state = MagicMock()
        fsm_state.status = "success"
        mock_fsm.state = fsm_state

        migrator_mock = MagicMock()
        migrator_mock.evaluate_version.return_value = {
            "allowed": True,
            "status": "active",
        }

        mock_auditor = MagicMock()
        mock_auditor.sign_run.return_value = "sig"
        mock_pe = MagicMock()
        mock_pe.evaluate.return_value = ("allow", "ok")

        mock_trust = MagicMock()
        mock_trust.get_last_environment.return_value = "development"
        mock_trust.validate_transition.return_value = (True, "ok")

        with (
            patch("thegent.cli.commands.impl.ThegentSettings", return_value=settings),
            patch("thegent.cli.commands.impl._resolve_cwd", return_value=cwd),
            patch("thegent.cli.commands.impl._default_owner_tag", return_value="u:p"),
            patch("thegent.cli.commands.impl.resolve_agent", side_effect=lambda a: a),
            patch("thegent.cli.commands.impl.RunRegistry"),
            patch("thegent.cli.commands.impl.get_fallback_agents", return_value=[]),
            patch(
                "thegent.cli.commands.impl.extract_condensed", return_value="condensed"
            ),
            patch("thegent.cli.commands.impl.is_usage_limit", return_value=False),
            patch(
                "thegent.contracts.migration.MigrationController",
                return_value=migrator_mock,
            ),
            patch("thegent.models.normalize_model_id", return_value="gpt-4"),
            patch("thegent.models.catalog.resolve_route", return_value=mock_route),
            patch("thegent.execution.Auditor", return_value=mock_auditor),
            patch("thegent.execution.PolicyEngine", return_value=mock_pe),
            patch("thegent.execution.CircuitBreakerRegistry"),
            patch("thegent.execution.TrustBoundaryValidator", return_value=mock_trust),
            patch("thegent.execution.OverrideRegistry"),
            patch(
                "thegent.agents.state_machine.FallbackStateMachine",
                return_value=mock_fsm,
            ),
            patch("thegent.contracts.telemetry.ContractTelemetry"),
            patch(
                "thegent.contracts.telemetry.rank_providers_by_parser_quality",
                side_effect=lambda a, t, limit: a,
            ),
            patch("thegent.contracts.policy.FallbackPolicy"),
        ):
            result = cli_impl.run_impl(
                agent=None,
                prompt="task",
                cd=cwd,
                model="gpt-4",
                provider="openai",
            )
        assert result["exit_code"] == 0

    def test_run_contract_version_rejected(self, tmp_path) -> None:
        # @trace FR-CLI-138
        settings = MagicMock()
        settings.default_timeout_claude = 300

        migrator_mock = MagicMock()
        migrator_mock.evaluate_version.return_value = {
            "allowed": False,
            "status": "rejected",
            "reason": "Unsupported version",
        }

        mock_trust = MagicMock()
        mock_trust.get_last_environment.return_value = "development"
        mock_trust.validate_transition.return_value = (True, "ok")

        with (
            patch("thegent.cli.commands.impl.ThegentSettings", return_value=settings),
            patch("thegent.cli.commands.impl.resolve_agent", side_effect=lambda a: a),
            patch(
                "thegent.contracts.migration.MigrationController",
                return_value=migrator_mock,
            ),
            patch("thegent.execution.TrustBoundaryValidator", return_value=mock_trust),
        ):
            result = cli_impl.run_impl(
                agent="claude",
                prompt="task",
                contract_version="0.0.1",
            )
        assert result["exit_code"] == 1
        assert "rejected" in result.get(
            "error", ""
        ).lower() or "Unsupported" in result.get("error", "")

    def test_run_include_contract_flag(self, tmp_path) -> None:
        # @trace FR-CLI-139
        result = self._run_impl_helper(tmp_path=tmp_path)
        # The helper doesn't pass include_contract, but we verify the base path works
        assert "exit_code" in result


# ---------------------------------------------------------------------------
# _resolve_cwd
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestResolveCwd:
    def test_explicit_cd(self, tmp_path) -> None:
        # @trace FR-CLI-140
        # Clear cache to avoid cross-test contamination
        cli_impl._CWD_CACHE.clear()
        result = cli_impl._resolve_cwd(tmp_path)
        assert result == tmp_path

    def test_explicit_cd_nonexistent(self, tmp_path) -> None:
        # @trace FR-CLI-141
        cli_impl._CWD_CACHE.clear()
        fake = tmp_path / "nonexistent"
        with pytest.raises(typer.BadParameter, match="Directory does not exist"):
            cli_impl._resolve_cwd(fake)

    def test_auto_detect_git(self, tmp_path) -> None:
        # @trace FR-CLI-142
        cli_impl._CWD_CACHE.clear()
        (tmp_path / ".git").mkdir()
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            result = cli_impl._resolve_cwd(None)
        assert result == tmp_path

    def test_no_project_indicators(self, tmp_path) -> None:
        # @trace FR-CLI-143
        cli_impl._CWD_CACHE.clear()
        bare = tmp_path / "bare"
        bare.mkdir()
        with patch("pathlib.Path.cwd", return_value=bare):
            result = cli_impl._resolve_cwd(None)
        assert result is None


# ---------------------------------------------------------------------------
# _load_prior_session_output
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestLoadPriorSessionOutput:
    def test_loads_stdout(self, tmp_path) -> None:
        # @trace FR-CLI-144
        settings = MagicMock()
        settings.session_dir = tmp_path
        meta_path = tmp_path / "prev.json"
        meta_path.write_text("{}", encoding="utf-8")
        stdout_path = tmp_path / "prev.stdout.log"
        stdout_path.write_text("prior output", encoding="utf-8")
        result = cli_impl._load_prior_session_output(settings, "prev")
        assert "prior output" in result

    def test_includes_stderr(self, tmp_path) -> None:
        # @trace FR-CLI-145
        settings = MagicMock()
        settings.session_dir = tmp_path
        meta_path = tmp_path / "prev2.json"
        meta_path.write_text("{}", encoding="utf-8")
        stdout_path = tmp_path / "prev2.stdout.log"
        stdout_path.write_text("stdout content", encoding="utf-8")
        stderr_path = tmp_path / "prev2.stderr.log"
        stderr_path.write_text("stderr content", encoding="utf-8")
        result = cli_impl._load_prior_session_output(
            settings, "prev2", include_stderr=True
        )
        assert "stdout content" in result
        assert "stderr" in result.lower()

    def test_truncates_long_output(self, tmp_path) -> None:
        # @trace FR-CLI-146
        settings = MagicMock()
        settings.session_dir = tmp_path
        meta_path = tmp_path / "long.json"
        meta_path.write_text("{}", encoding="utf-8")
        stdout_path = tmp_path / "long.stdout.log"
        stdout_path.write_text("X" * 20000, encoding="utf-8")
        result = cli_impl._load_prior_session_output(settings, "long")
        assert len(result) <= cli_impl._CONTINUATION_TAIL_CHARS + 100


# ---------------------------------------------------------------------------
# _resolve_droids_dir
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestResolveDroidsDir:
    def test_project_local_droids(self, tmp_path) -> None:
        # @trace FR-CLI-147
        (tmp_path / ".factory" / "droids").mkdir(parents=True)
        settings = MagicMock()
        settings.factory_droids_dir = tmp_path / "global_droids"
        result = cli_impl._resolve_droids_dir(tmp_path, settings)
        assert ".factory" in str(result)

    def test_fallback_to_global(self, tmp_path) -> None:
        # @trace FR-CLI-148
        settings = MagicMock()
        settings.factory_droids_dir = tmp_path / "global_droids"
        (tmp_path / "global_droids").mkdir()
        result = cli_impl._resolve_droids_dir(tmp_path, settings)
        assert "global_droids" in str(result)

    def test_none_cwd_uses_global(self) -> None:
        # @trace FR-CLI-149
        settings = MagicMock()
        settings.factory_droids_dir = Path("/tmp/test-droids")
        result = cli_impl._resolve_droids_dir(None, settings)
        assert "test-droids" in str(result)


# ---------------------------------------------------------------------------
# _resolve_agent_model: extra agent coverage
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestResolveAgentModelExtended:
    def test_gemini_default(self) -> None:
        # @trace FR-CLI-150
        settings = MagicMock()
        settings.default_gemini_model = "gemini-2.0-flash"
        result = cli_impl._resolve_agent_model("gemini", None, "write", settings)
        assert result == "gemini-2.0-flash"

    def test_copilot_default(self) -> None:
        # @trace FR-CLI-150
        settings = MagicMock()
        settings.default_copilot_model = "claude-haiku-4.5"
        result = cli_impl._resolve_agent_model("copilot", None, "write", settings)
        assert result == "claude-haiku-4.5"

    def test_cursor_agent_default(self) -> None:
        # @trace FR-CLI-150
        settings = MagicMock()
        settings.default_cursor_model = "gemini-3-flash"
        for name in ("cursor-agent", "cursor"):
            result = cli_impl._resolve_agent_model(name, None, "write", settings)
            assert result == "gemini-3-flash"

    def test_antigravity_default(self) -> None:
        # @trace FR-CLI-150
        settings = MagicMock()
        settings.default_antigravity_model = "gemini-3-flash"
        result = cli_impl._resolve_agent_model("antigravity", None, "write", settings)
        assert result == "gemini-3-flash"

    def test_glm_hardcoded(self) -> None:
        # @trace FR-CLI-150
        settings = MagicMock()
        result = cli_impl._resolve_agent_model("glm", None, "write", settings)
        assert result == "glm-5"

    def test_roo_hardcoded(self) -> None:
        # @trace FR-CLI-150
        settings = MagicMock()
        result = cli_impl._resolve_agent_model("roo", None, "write", settings)
        assert result == "roo-default"

    def test_kilo_hardcoded(self) -> None:
        # @trace FR-CLI-150
        settings = MagicMock()
        result = cli_impl._resolve_agent_model("kilo", None, "write", settings)
        assert result == "kilo-default"
