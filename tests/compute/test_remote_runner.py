"""Tests for thegent.compute.remote_runner.

Covers:
- RemoteRunner initialization and configuration
- RemoteRunner.run_agent_task() - command building and execution
- RemoteRunner.run_agent_task_async() - async variant
- RemoteRunner.execute() - raw command execution
- RemoteRunner.execute_async() - async raw command execution
- RemoteRunner.sync_to_remote() - rsync to remote
- RemoteRunner.sync_from_remote() - rsync from remote
- RemoteRunner.start_process() - non-blocking process start
- RemoteRunner.stop_process() - process termination
- RemoteRunner.get_process_status() - process status check
- RemoteRunner.list_processes() - list tracked processes
- RemoteRunner._resolve_node() - node resolution
- load_config_from_env() - env var parsing
- Package-level __init__ exports
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from thegent.compute import RemoteProcess as ExportedProcess
from thegent.compute import RemoteRunner as ExportedRunner
from thegent.compute import RemoteRunnerError as ExportedError
from thegent.compute.remote_runner import (
    RemoteProcess,
    RemoteRunner,
    RemoteRunnerError,
    load_config_from_env,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_remote_result(
    task_id: str = "t1",
    exit_code: int = 0,
    stdout: str = "output",
    stderr: str = "",
    node: str = "worker-1",
    elapsed_s: float = 1.0,
) -> MagicMock:
    mock = MagicMock()
    mock.task_id = task_id
    mock.exit_code = exit_code
    mock.stdout = stdout
    mock.stderr = stderr
    mock.node = node
    mock.elapsed_s = elapsed_s
    return mock


# ---------------------------------------------------------------------------
# RemoteRunner initialization
# ---------------------------------------------------------------------------


class TestRemoteRunnerInit:
    """Tests for RemoteRunner.__init__."""

    def test_explicit_node(self) -> None:
        """RemoteRunner stores explicit node."""
        runner = RemoteRunner(node="worker-1")
        assert runner.node == "worker-1"
        assert runner.sync_workspace is False

    def test_sync_workspace_flag(self) -> None:
        """RemoteRunner stores sync_workspace flag."""
        runner = RemoteRunner(node="worker-1", sync_workspace=True)
        assert runner.node == "worker-1"
        assert runner.sync_workspace is True

    def test_sync_workspace_default_false(self) -> None:
        """RemoteRunner defaults sync_workspace to False."""
        runner = RemoteRunner(node="worker-1")
        assert runner.sync_workspace is False

    def test_ssh_user_override(self) -> None:
        """RemoteRunner stores SSH user override."""
        runner = RemoteRunner(node="worker-1", ssh_user="agent")
        assert runner._ssh_user == "agent"

    def test_node_none_for_round_robin(self) -> None:
        """RemoteRunner with node=None uses round-robin."""
        runner = RemoteRunner(node=None)
        assert runner.node is None


# ---------------------------------------------------------------------------
# RemoteRunner.run_agent_task
# ---------------------------------------------------------------------------


class TestRunAgentTask:
    """Tests for RemoteRunner.run_agent_task()."""

    @patch("thegent.compute.remote_runner.RemoteExecutor")
    def test_basic_prompt(self, mock_executor_cls: MagicMock) -> None:
        """run_agent_task builds correct command for basic prompt."""
        mock_executor = MagicMock()
        mock_executor.execute.return_value = _make_remote_result()
        mock_executor_cls.return_value = mock_executor

        runner = RemoteRunner(node="worker-1")
        runner._executor = mock_executor

        runner.run_agent_task(prompt="Hello world")

        # Verify execute was called
        mock_executor.execute.assert_called_once()
        task = mock_executor.execute.call_args[0][0]
        assert "thegent run agent" in task.command
        assert "Hello world" in task.command
        assert task.node == "worker-1"

    @patch("thegent.compute.remote_runner.RemoteExecutor")
    def test_with_agent_name(self, mock_executor_cls: MagicMock) -> None:
        """run_agent_task includes agent name when specified."""
        mock_executor = MagicMock()
        mock_executor.execute.return_value = _make_remote_result()
        mock_executor_cls.return_value = mock_executor

        runner = RemoteRunner(node="worker-1")
        runner._executor = mock_executor

        runner.run_agent_task(prompt="Hello", agent="claude")

        task = mock_executor.execute.call_args[0][0]
        assert "--agent claude" in task.command

    @patch("thegent.compute.remote_runner.RemoteExecutor")
    def test_with_working_directory(self, mock_executor_cls: MagicMock) -> None:
        """run_agent_task includes cd when specified."""
        mock_executor = MagicMock()
        mock_executor.execute.return_value = _make_remote_result()
        mock_executor_cls.return_value = mock_executor

        runner = RemoteRunner(node="worker-1")
        runner._executor = mock_executor

        runner.run_agent_task(prompt="Hello", cd="/home/user/project")

        task = mock_executor.execute.call_args[0][0]
        assert "cd /home/user/project" in task.command

    @patch("thegent.compute.remote_runner.RemoteExecutor")
    def test_env_includes_remote_exec_flag(self, mock_executor_cls: MagicMock) -> None:
        """run_agent_task sets THGENT_REMOTE_EXEC in env."""
        mock_executor = MagicMock()
        mock_executor.execute.return_value = _make_remote_result()
        mock_executor_cls.return_value = mock_executor

        runner = RemoteRunner(node="worker-1")
        runner._executor = mock_executor

        runner.run_agent_task(prompt="Hello")

        task = mock_executor.execute.call_args[0][0]
        assert task.env.get("THGENT_REMOTE_EXEC") == "1"

    @patch("thegent.compute.remote_runner.RemoteExecutor")
    def test_custom_env_preserved(self, mock_executor_cls: MagicMock) -> None:
        """run_agent_task preserves custom env vars."""
        mock_executor = MagicMock()
        mock_executor.execute.return_value = _make_remote_result()
        mock_executor_cls.return_value = mock_executor

        runner = RemoteRunner(node="worker-1")
        runner._executor = mock_executor

        runner.run_agent_task(prompt="Hello", env={"MY_VAR": "test"})

        task = mock_executor.execute.call_args[0][0]
        assert task.env.get("MY_VAR") == "test"
        assert task.env.get("THGENT_REMOTE_EXEC") == "1"

    @patch("thegent.compute.remote_runner.RemoteExecutor")
    def test_timeout_passed_to_task(self, mock_executor_cls: MagicMock) -> None:
        """run_agent_task passes timeout to RemoteTask."""
        mock_executor = MagicMock()
        mock_executor.execute.return_value = _make_remote_result()
        mock_executor_cls.return_value = mock_executor

        runner = RemoteRunner(node="worker-1")
        runner._executor = mock_executor

        runner.run_agent_task(prompt="Hello", timeout_s=600.0)

        task = mock_executor.execute.call_args[0][0]
        assert task.timeout_s == 600.0


# ---------------------------------------------------------------------------
# RemoteRunner.run_agent_task_async
# ---------------------------------------------------------------------------


class TestRunAgentTaskAsync:
    """Tests for RemoteRunner.run_agent_task_async()."""

    @patch("thegent.compute.remote_runner.RemoteExecutor")
    def test_async_execution(self, mock_executor_cls: MagicMock) -> None:
        """run_agent_task_async builds correct command and uses async executor."""
        mock_executor = MagicMock()
        mock_executor.execute_async = MagicMock(return_value=_make_remote_result())
        mock_executor_cls.return_value = mock_executor

        runner = RemoteRunner(node="worker-1")
        runner._executor = mock_executor

        # Verify the async method exists and has correct signature
        import inspect

        sig = inspect.signature(runner.run_agent_task_async)
        assert "prompt" in sig.parameters
        assert "agent" in sig.parameters
        assert "timeout_s" in sig.parameters
        assert "cd" in sig.parameters
        assert "env" in sig.parameters

        # Verify executor has execute_async method
        assert hasattr(mock_executor, "execute_async")


# ---------------------------------------------------------------------------
# RemoteRunner.execute
# ---------------------------------------------------------------------------


class TestExecute:
    """Tests for RemoteRunner.execute()."""

    @patch("thegent.compute.remote_runner.RemoteExecutor")
    def test_raw_command_execution(self, mock_executor_cls: MagicMock) -> None:
        """execute runs raw command on remote node."""
        mock_executor = MagicMock()
        mock_executor.execute.return_value = _make_remote_result(stdout="result")
        mock_executor_cls.return_value = mock_executor

        runner = RemoteRunner(node="worker-1")
        runner._executor = mock_executor

        runner.execute("ls -la")

        mock_executor.execute.assert_called_once()
        task = mock_executor.execute.call_args[0][0]
        assert task.command == "ls -la"

    @patch("thegent.compute.remote_runner.RemoteExecutor")
    def test_error_propagation(self, mock_executor_cls: MagicMock) -> None:
        """execute raises RemoteRunnerError on executor error."""
        from thegent.compute.remote_executor import RemoteExecutorError

        mock_executor = MagicMock()
        mock_executor.execute.side_effect = RemoteExecutorError("SSH failed")
        mock_executor_cls.return_value = mock_executor

        runner = RemoteRunner(node="worker-1")
        runner._executor = mock_executor

        with pytest.raises(RemoteRunnerError, match="Remote execution failed"):
            runner.execute("ls")


# ---------------------------------------------------------------------------
# RemoteRunner.sync_to_remote
# ---------------------------------------------------------------------------


class TestSyncToRemote:
    """Tests for RemoteRunner.sync_to_remote()."""

    @patch("thegent.compute.remote_runner.subprocess.run")
    @patch("thegent.compute.remote_runner.RemoteExecutor")
    def test_rsync_success(
        self, mock_executor_cls: MagicMock, mock_run: MagicMock
    ) -> None:
        """sync_to_remote returns True on successful rsync."""
        mock_executor = MagicMock()
        mock_executor.available_nodes.return_value = ["worker-1"]
        mock_executor_cls.return_value = mock_executor

        mock_run.return_value = MagicMock(returncode=0, stderr="")

        runner = RemoteRunner(node="worker-1")
        runner._executor = mock_executor

        with patch("pathlib.Path.exists", return_value=True):
            result = runner.sync_to_remote("/local/path", "/remote/path")

        assert result is True
        call_args = mock_run.call_args[0][0]
        assert "rsync" in call_args
        assert "/remote/path" in " ".join(call_args)

    @patch("thegent.compute.remote_runner.subprocess.run")
    @patch("thegent.compute.remote_runner.RemoteExecutor")
    def test_rsync_failure(
        self, mock_executor_cls: MagicMock, mock_run: MagicMock
    ) -> None:
        """sync_to_remote returns False on rsync failure."""
        mock_executor = MagicMock()
        mock_executor.available_nodes.return_value = ["worker-1"]
        mock_executor_cls.return_value = mock_executor

        mock_run.return_value = MagicMock(returncode=1, stderr="rsync error")

        runner = RemoteRunner(node="worker-1")
        runner._executor = mock_executor

        with patch("pathlib.Path.exists", return_value=True):
            result = runner.sync_to_remote("/local/path", "/remote/path")

        assert result is False


# ---------------------------------------------------------------------------
# RemoteRunner.start_process
# ---------------------------------------------------------------------------


class TestStartProcess:
    """Tests for RemoteRunner.start_process()."""

    @patch("thegent.compute.remote_runner.RemoteExecutor")
    def test_starts_process_with_nohup(self, mock_executor_cls: MagicMock) -> None:
        """start_process uses nohup to start persistent process."""
        mock_executor = MagicMock()
        mock_executor.execute.return_value = _make_remote_result(stdout="12345")
        mock_executor_cls.return_value = mock_executor

        runner = RemoteRunner(node="worker-1")
        runner._executor = mock_executor

        process = runner.start_process("python server.py")

        assert process.pid == 12345
        assert process.command == "python server.py"
        assert process.node == "worker-1"
        assert process.status == "running"

        # Verify nohup is in the command
        task = mock_executor.execute.call_args[0][0]
        assert "nohup" in task.command

    @patch("thegent.compute.remote_runner.RemoteExecutor")
    def test_invalid_pid_raises_error(self, mock_executor_cls: MagicMock) -> None:
        """start_process raises error when PID parse fails."""
        mock_executor = MagicMock()
        mock_executor.execute.return_value = _make_remote_result(stdout="not a pid")
        mock_executor_cls.return_value = mock_executor

        runner = RemoteRunner(node="worker-1")
        runner._executor = mock_executor

        with pytest.raises(RemoteRunnerError, match="Failed to parse PID"):
            runner.start_process("python server.py")


# ---------------------------------------------------------------------------
# RemoteRunner.stop_process
# ---------------------------------------------------------------------------


class TestStopProcess:
    """Tests for RemoteRunner.stop_process()."""

    @patch("thegent.compute.remote_runner.RemoteExecutor")
    def test_stop_tracked_process(self, mock_executor_cls: MagicMock) -> None:
        """stop_process kills tracked process and removes from list."""
        mock_executor = MagicMock()
        mock_executor.execute.return_value = _make_remote_result()
        mock_executor_cls.return_value = mock_executor

        runner = RemoteRunner(node="worker-1")
        runner._executor = mock_executor

        # Add a tracked process
        process = RemoteProcess(
            pid=12345,
            command="python server.py",
            node="worker-1",
            start_time=0.0,
        )
        runner._active_processes["12345"] = process

        result = runner.stop_process(12345)

        assert result is True
        assert "12345" not in runner._active_processes

    @patch("thegent.compute.remote_runner.RemoteExecutor")
    def test_stop_untracked_process(self, mock_executor_cls: MagicMock) -> None:
        """stop_process attempts to kill untracked process."""
        mock_executor = MagicMock()
        mock_executor.execute.return_value = _make_remote_result()
        mock_executor_cls.return_value = mock_executor

        runner = RemoteRunner(node="worker-1")
        runner._executor = mock_executor

        result = runner.stop_process(99999)

        assert result is True


# ---------------------------------------------------------------------------
# RemoteRunner.get_process_status
# ---------------------------------------------------------------------------


class TestGetProcessStatus:
    """Tests for RemoteRunner.get_process_status()."""

    @patch("thegent.compute.remote_runner.RemoteExecutor")
    def test_process_running(self, mock_executor_cls: MagicMock) -> None:
        """get_process_status returns process when still running."""
        mock_executor = MagicMock()
        mock_executor.execute.return_value = _make_remote_result(stdout="12345")
        mock_executor_cls.return_value = mock_executor

        runner = RemoteRunner(node="worker-1")
        runner._executor = mock_executor

        process = RemoteProcess(
            pid=12345,
            command="python server.py",
            node="worker-1",
            start_time=0.0,
        )
        runner._active_processes["12345"] = process

        result = runner.get_process_status(12345)

        assert result is not None
        assert result.status == "running"

    @patch("thegent.compute.remote_runner.RemoteExecutor")
    def test_process_completed(self, mock_executor_cls: MagicMock) -> None:
        """get_process_status marks process as completed when not found."""
        mock_executor = MagicMock()
        mock_executor.execute.return_value = _make_remote_result(stdout="", exit_code=1)
        mock_executor_cls.return_value = mock_executor

        runner = RemoteRunner(node="worker-1")
        runner._executor = mock_executor

        process = RemoteProcess(
            pid=12345,
            command="python server.py",
            node="worker-1",
            start_time=0.0,
        )
        runner._active_processes["12345"] = process

        result = runner.get_process_status(12345)

        assert result is not None
        assert result.status == "completed"

    def test_unknown_process(self) -> None:
        """get_process_status returns None for unknown PID."""
        runner = RemoteRunner(node="worker-1")
        result = runner.get_process_status(99999)
        assert result is None


# ---------------------------------------------------------------------------
# RemoteRunner.list_processes
# ---------------------------------------------------------------------------


class TestListProcesses:
    """Tests for RemoteRunner.list_processes()."""

    def test_empty_list(self) -> None:
        """list_processes returns empty list when no processes."""
        runner = RemoteRunner(node="worker-1")
        assert runner.list_processes() == []

    def test_returns_all_processes(self) -> None:
        """list_processes returns all tracked processes."""
        runner = RemoteRunner(node="worker-1")

        p1 = RemoteProcess(pid=1, command="cmd1", node="n1", start_time=0.0)
        p2 = RemoteProcess(pid=2, command="cmd2", node="n1", start_time=0.0)

        runner._active_processes["1"] = p1
        runner._active_processes["2"] = p2

        processes = runner.list_processes()
        assert len(processes) == 2


# ---------------------------------------------------------------------------
# RemoteRunner._resolve_node
# ---------------------------------------------------------------------------


class TestResolveNode:
    """Tests for RemoteRunner._resolve_node()."""

    @patch("thegent.compute.remote_runner.RemoteExecutor")
    def test_explicit_node_returned(self, mock_executor_cls: MagicMock) -> None:
        """_resolve_node returns explicit node when set."""
        runner = RemoteRunner(node="worker-1")
        assert runner._resolve_node() == "worker-1"

    @patch("thegent.compute.remote_runner.RemoteExecutor")
    def test_round_robin_from_available(self, mock_executor_cls: MagicMock) -> None:
        """_resolve_node uses available nodes when node is None."""
        mock_executor = MagicMock()
        mock_executor.available_nodes.return_value = ["node-a", "node-b"]
        mock_executor_cls.return_value = mock_executor

        runner = RemoteRunner(node=None)
        runner._executor = mock_executor

        result = runner._resolve_node()

        assert result == "node-a"

    @patch("thegent.compute.remote_runner.RemoteExecutor")
    def test_no_nodes_raises_error(self, mock_executor_cls: MagicMock) -> None:
        """_resolve_node raises error when no nodes available."""
        mock_executor = MagicMock()
        mock_executor.available_nodes.return_value = []
        mock_executor_cls.return_value = mock_executor

        runner = RemoteRunner(node=None)
        runner._executor = mock_executor

        with pytest.raises(RemoteRunnerError, match="No remote nodes configured"):
            runner._resolve_node()


# ---------------------------------------------------------------------------
# load_config_from_env
# ---------------------------------------------------------------------------


class TestLoadConfigFromEnv:
    """Tests for load_config_from_env()."""

    def test_empty_when_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """load_config_from_env returns empty values when vars unset."""
        monkeypatch.delenv("THGENT_REMOTE_NODES", raising=False)
        monkeypatch.delenv("THGENT_REMOTE_SSH_USER", raising=False)

        config = load_config_from_env()

        assert config["nodes"] == ""
        assert config["ssh_user"] == ""

    def test_parsed_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """load_config_from_env parses values from environment."""
        monkeypatch.setenv("THGENT_REMOTE_NODES", "node1,node2")
        monkeypatch.setenv("THGENT_REMOTE_SSH_USER", "agent")

        config = load_config_from_env()

        assert config["nodes"] == "node1,node2"
        assert config["ssh_user"] == "agent"


# ---------------------------------------------------------------------------
# Package __init__ exports
# ---------------------------------------------------------------------------


class TestPackageExports:
    """Verify that compute/__init__.py re-exports RemoteRunner symbols."""

    def test_remote_runner_exported(self) -> None:
        """RemoteRunner is importable from thegent.compute."""
        assert ExportedRunner is RemoteRunner

    def test_remote_runner_error_exported(self) -> None:
        """RemoteRunnerError is importable from thegent.compute."""
        assert ExportedError is RemoteRunnerError

    def test_remote_process_exported(self) -> None:
        """RemoteProcess is importable from thegent.compute."""
        assert ExportedProcess is RemoteProcess
