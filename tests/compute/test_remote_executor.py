"""Tests for thegent.compute.remote_executor.

Covers:
- RemoteTask dataclass construction and defaults
- RemoteResult dataclass construction
- _load_nodes_from_env() env-var parsing
- _load_ssh_user_from_env() env-var parsing
- RemoteExecutor.__init__ env-var integration
- RemoteExecutor.execute() — success, timeout, OSError, non-zero exit
- RemoteExecutor.execute() — node selection from task vs round-robin
- RemoteExecutor.execute() — SSH user included/excluded in destination
- RemoteExecutor.execute() — extra env vars merged and passed
- RemoteExecutor.execute() — no nodes configured raises error
- RemoteExecutor.execute_async() — wraps execute correctly
- RemoteExecutor.available_nodes() — reachable / unreachable filtering
- RemoteExecutor.available_nodes() — ping exceptions handled gracefully
- Package-level __init__ exports
"""

from __future__ import annotations

import asyncio
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from thegent.compute import RemoteExecutor as ExportedExecutor
from thegent.compute import RemoteExecutorError as ExportedError
from thegent.compute import RemoteResult as ExportedResult
from thegent.compute import RemoteTask as ExportedTask
from thegent.compute.remote_executor import (
    RemoteExecutor,
    RemoteExecutorError,
    RemoteResult,
    RemoteTask,
    _load_nodes_from_env,
    _load_ssh_user_from_env,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_task(
    task_id: str = "t1",
    command: str = "echo hello",
    *,
    env: dict[str, str] | None = None,
    timeout_s: float = 30.0,
    node: str | None = None,
) -> RemoteTask:
    return RemoteTask(
        task_id=task_id,
        command=command,
        env=env or {},
        timeout_s=timeout_s,
        node=node,
    )


def _make_completed_process(
    returncode: int = 0,
    stdout: str = "output",
    stderr: str = "",
) -> MagicMock:
    mock = MagicMock()
    mock.returncode = returncode
    mock.stdout = stdout
    mock.stderr = stderr
    return mock


# ---------------------------------------------------------------------------
# RemoteTask
# ---------------------------------------------------------------------------


class TestRemoteTask:
    """Unit tests for the RemoteTask dataclass."""

    # @trace FR-COMPUTE-010
    def test_defaults(self) -> None:
        """RemoteTask defaults are applied correctly."""
        task = RemoteTask(task_id="abc", command="ls")
        assert task.task_id == "abc"
        assert task.command == "ls"
        assert task.env == {}
        assert task.timeout_s == 300.0
        assert task.node is None

    # @trace FR-COMPUTE-010
    def test_all_fields(self) -> None:
        """RemoteTask stores all explicitly set fields."""
        task = RemoteTask(
            task_id="xyz",
            command="uname -a",
            env={"FOO": "bar"},
            timeout_s=60.0,
            node="worker-1",
        )
        assert task.env == {"FOO": "bar"}
        assert task.timeout_s == 60.0
        assert task.node == "worker-1"

    # @trace FR-COMPUTE-010
    def test_env_default_factory_is_independent(self) -> None:
        """Each RemoteTask gets its own env dict (no shared mutable default)."""
        t1 = RemoteTask(task_id="a", command="x")
        t2 = RemoteTask(task_id="b", command="y")
        t1.env["KEY"] = "val"
        assert "KEY" not in t2.env


# ---------------------------------------------------------------------------
# RemoteResult
# ---------------------------------------------------------------------------


class TestRemoteResult:
    """Unit tests for the RemoteResult dataclass."""

    # @trace FR-COMPUTE-011
    def test_construction(self) -> None:
        """RemoteResult stores all fields correctly."""
        result = RemoteResult(
            task_id="t1",
            exit_code=0,
            stdout="hello\n",
            stderr="",
            node="worker-1",
            elapsed_s=1.23,
        )
        assert result.task_id == "t1"
        assert result.exit_code == 0
        assert result.stdout == "hello\n"
        assert result.stderr == ""
        assert result.node == "worker-1"
        assert result.elapsed_s == pytest.approx(1.23)


# ---------------------------------------------------------------------------
# Environment helpers
# ---------------------------------------------------------------------------


class TestEnvHelpers:
    """Tests for _load_nodes_from_env and _load_ssh_user_from_env."""

    # @trace FR-COMPUTE-012
    def test_nodes_empty_when_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """_load_nodes_from_env returns [] when THGENT_REMOTE_NODES is unset."""
        monkeypatch.delenv("THGENT_REMOTE_NODES", raising=False)
        assert _load_nodes_from_env() == []

    # @trace FR-COMPUTE-012
    def test_nodes_parsed_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """_load_nodes_from_env splits comma-separated hostnames."""
        monkeypatch.setenv("THGENT_REMOTE_NODES", "node1,node2,node3")
        assert _load_nodes_from_env() == ["node1", "node2", "node3"]

    # @trace FR-COMPUTE-012
    def test_nodes_strips_whitespace(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """_load_nodes_from_env trims whitespace around entries."""
        monkeypatch.setenv("THGENT_REMOTE_NODES", " host-a , host-b ")
        assert _load_nodes_from_env() == ["host-a", "host-b"]

    # @trace FR-COMPUTE-012
    def test_nodes_ignores_empty_tokens(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """_load_nodes_from_env ignores empty tokens from trailing commas."""
        monkeypatch.setenv("THGENT_REMOTE_NODES", "node1,,node2,")
        assert _load_nodes_from_env() == ["node1", "node2"]

    # @trace FR-COMPUTE-012
    def test_ssh_user_none_when_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """_load_ssh_user_from_env returns None when THGENT_REMOTE_SSH_USER is unset."""
        monkeypatch.delenv("THGENT_REMOTE_SSH_USER", raising=False)
        assert _load_ssh_user_from_env() is None

    # @trace FR-COMPUTE-012
    def test_ssh_user_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """_load_ssh_user_from_env returns the env variable value."""
        monkeypatch.setenv("THGENT_REMOTE_SSH_USER", "agent")
        assert _load_ssh_user_from_env() == "agent"

    # @trace FR-COMPUTE-012
    def test_ssh_user_empty_string_treated_as_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """_load_ssh_user_from_env returns None when env var is an empty string."""
        monkeypatch.setenv("THGENT_REMOTE_SSH_USER", "")
        assert _load_ssh_user_from_env() is None


# ---------------------------------------------------------------------------
# RemoteExecutor initialisation
# ---------------------------------------------------------------------------


class TestRemoteExecutorInit:
    """Tests for RemoteExecutor.__init__ and env-var wiring."""

    # @trace FR-COMPUTE-013
    def test_nodes_from_constructor(self) -> None:
        """Nodes passed to constructor take priority over env."""
        executor = RemoteExecutor(nodes=["n1", "n2"])
        assert executor._nodes == ["n1", "n2"]

    # @trace FR-COMPUTE-013
    def test_nodes_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Nodes are loaded from THGENT_REMOTE_NODES when not passed."""
        monkeypatch.setenv("THGENT_REMOTE_NODES", "env-node1,env-node2")
        executor = RemoteExecutor()
        assert executor._nodes == ["env-node1", "env-node2"]

    # @trace FR-COMPUTE-013
    def test_ssh_user_from_constructor(self) -> None:
        """ssh_user passed to constructor takes priority over env."""
        executor = RemoteExecutor(nodes=["n1"], ssh_user="myuser")
        assert executor._ssh_user == "myuser"

    # @trace FR-COMPUTE-013
    def test_ssh_user_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """ssh_user is loaded from THGENT_REMOTE_SSH_USER when not passed."""
        monkeypatch.setenv("THGENT_REMOTE_SSH_USER", "remote-agent")
        executor = RemoteExecutor(nodes=["n1"])
        assert executor._ssh_user == "remote-agent"

    # @trace FR-COMPUTE-013
    def test_rr_none_when_no_nodes(self) -> None:
        """Round-robin iterator is None when no nodes are configured."""
        executor = RemoteExecutor(nodes=[])
        assert executor._rr is None


# ---------------------------------------------------------------------------
# RemoteExecutor.execute — success cases
# ---------------------------------------------------------------------------


class TestExecuteSuccess:
    """Happy-path tests for RemoteExecutor.execute()."""

    # @trace FR-COMPUTE-014
    @patch("thegent.compute.remote_executor.subprocess.run")
    def test_returns_remote_result(self, mock_run: MagicMock) -> None:
        """execute() returns a properly populated RemoteResult."""
        mock_run.return_value = _make_completed_process(0, "hello\n", "")
        executor = RemoteExecutor(nodes=["worker-1"])
        task = _make_task(task_id="t1", command="echo hello", node="worker-1")

        result = executor.execute(task)

        assert isinstance(result, RemoteResult)
        assert result.task_id == "t1"
        assert result.exit_code == 0
        assert result.stdout == "hello\n"
        assert result.stderr == ""
        assert result.node == "worker-1"
        assert result.elapsed_s >= 0.0

    # @trace FR-COMPUTE-014
    @patch("thegent.compute.remote_executor.subprocess.run")
    def test_ssh_command_structure(self, mock_run: MagicMock) -> None:
        """execute() calls SSH with the correct arguments."""
        mock_run.return_value = _make_completed_process()
        executor = RemoteExecutor(nodes=["node-a"], ssh_user="alice")
        task = _make_task(command="uname", node="node-a")

        executor.execute(task)

        args, _kwargs = mock_run.call_args
        cmd = args[0]
        assert cmd[0] == "ssh"
        assert "-o" in cmd
        assert "StrictHostKeyChecking=no" in cmd
        assert "alice@node-a" in cmd
        assert "uname" in cmd

    # @trace FR-COMPUTE-014
    @patch("thegent.compute.remote_executor.subprocess.run")
    def test_destination_without_user(self, mock_run: MagicMock) -> None:
        """When ssh_user is None the destination is just the node address."""
        mock_run.return_value = _make_completed_process()
        executor = RemoteExecutor(nodes=["worker-2"], ssh_user=None)
        task = _make_task(node="worker-2")

        executor.execute(task)

        cmd = mock_run.call_args[0][0]
        assert "worker-2" in cmd
        assert "@worker-2" not in " ".join(cmd)

    # @trace FR-COMPUTE-014
    @patch("thegent.compute.remote_executor.subprocess.run")
    def test_nonzero_exit_code_is_not_raised(self, mock_run: MagicMock) -> None:
        """Non-zero exit codes are returned in RemoteResult, not raised."""
        mock_run.return_value = _make_completed_process(returncode=1, stderr="error")
        executor = RemoteExecutor(nodes=["n1"])
        result = executor.execute(_make_task(node="n1"))
        assert result.exit_code == 1
        assert result.stderr == "error"


# ---------------------------------------------------------------------------
# RemoteExecutor.execute — env forwarding
# ---------------------------------------------------------------------------


class TestExecuteEnv:
    """Tests for environment variable forwarding in execute()."""

    # @trace FR-COMPUTE-015
    @patch("thegent.compute.remote_executor.subprocess.run")
    def test_extra_env_merged_into_process_env(self, mock_run: MagicMock) -> None:
        """Extra env vars from RemoteTask are merged into the subprocess env."""
        mock_run.return_value = _make_completed_process()
        executor = RemoteExecutor(nodes=["n1"])
        task = _make_task(env={"MY_VAR": "my_value"}, node="n1")

        executor.execute(task)

        _, kwargs = mock_run.call_args
        env_passed = kwargs.get("env")
        assert env_passed is not None
        assert env_passed["MY_VAR"] == "my_value"

    # @trace FR-COMPUTE-015
    @patch("thegent.compute.remote_executor.subprocess.run")
    def test_no_extra_env_passes_none(self, mock_run: MagicMock) -> None:
        """When task.env is empty, subprocess env kwarg is None (inherit)."""
        mock_run.return_value = _make_completed_process()
        executor = RemoteExecutor(nodes=["n1"])
        task = _make_task(env={}, node="n1")

        executor.execute(task)

        _, kwargs = mock_run.call_args
        assert kwargs.get("env") is None


# ---------------------------------------------------------------------------
# RemoteExecutor.execute — timeout and error handling
# ---------------------------------------------------------------------------


class TestExecuteErrors:
    """Tests for error conditions in RemoteExecutor.execute()."""

    # @trace FR-COMPUTE-016
    @patch(
        "thegent.compute.remote_executor.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="ssh", timeout=30),
    )
    def test_timeout_raises_remote_executor_error(self, _run: MagicMock) -> None:
        """execute() raises RemoteExecutorError when subprocess times out."""
        executor = RemoteExecutor(nodes=["n1"])
        task = _make_task(timeout_s=30.0, node="n1")

        with pytest.raises(RemoteExecutorError, match=r"timed out after 30\.0s"):
            executor.execute(task)

    # @trace FR-COMPUTE-016
    @patch(
        "thegent.compute.remote_executor.subprocess.run",
        side_effect=OSError("No such file"),
    )
    def test_os_error_raises_remote_executor_error(self, _run: MagicMock) -> None:
        """execute() raises RemoteExecutorError when SSH binary cannot be spawned."""
        executor = RemoteExecutor(nodes=["n1"])
        task = _make_task(node="n1")

        with pytest.raises(RemoteExecutorError, match="failed to spawn SSH process"):
            executor.execute(task)

    # @trace FR-COMPUTE-016
    def test_no_nodes_raises_error(self) -> None:
        """execute() raises RemoteExecutorError when no nodes are configured."""
        executor = RemoteExecutor(nodes=[])
        task = _make_task()  # node=None triggers auto-selection

        with pytest.raises(RemoteExecutorError, match="no remote nodes configured"):
            executor.execute(task)


# ---------------------------------------------------------------------------
# RemoteExecutor.execute — node selection (round-robin)
# ---------------------------------------------------------------------------


class TestNodeSelection:
    """Tests for round-robin and explicit node selection."""

    # @trace FR-COMPUTE-017
    @patch("thegent.compute.remote_executor.subprocess.run")
    def test_explicit_node_used(self, mock_run: MagicMock) -> None:
        """When task.node is set, that node is used regardless of round-robin."""
        mock_run.return_value = _make_completed_process()
        executor = RemoteExecutor(nodes=["rr-node-1", "rr-node-2"])
        task = _make_task(node="explicit-node")

        result = executor.execute(task)

        assert result.node == "explicit-node"

    # @trace FR-COMPUTE-017
    @patch("thegent.compute.remote_executor.subprocess.run")
    def test_round_robin_cycles_nodes(self, mock_run: MagicMock) -> None:
        """Auto-selected nodes cycle through the configured list."""
        mock_run.return_value = _make_completed_process()
        executor = RemoteExecutor(nodes=["alpha", "beta", "gamma"])

        nodes_used = [executor.execute(_make_task()).node for _ in range(6)]

        assert nodes_used == ["alpha", "beta", "gamma", "alpha", "beta", "gamma"]

    # @trace FR-COMPUTE-017
    @patch("thegent.compute.remote_executor.subprocess.run")
    def test_single_node_always_selected(self, mock_run: MagicMock) -> None:
        """With one node, every task lands on that node."""
        mock_run.return_value = _make_completed_process()
        executor = RemoteExecutor(nodes=["solo"])

        for _ in range(3):
            assert executor.execute(_make_task()).node == "solo"


# ---------------------------------------------------------------------------
# RemoteExecutor.execute_async
# ---------------------------------------------------------------------------


class TestExecuteAsync:
    """Tests for the async execute_async wrapper."""

    # @trace FR-COMPUTE-018
    @patch("thegent.compute.remote_executor.subprocess.run")
    def test_execute_async_returns_remote_result(self, mock_run: MagicMock) -> None:
        """execute_async() resolves to a RemoteResult."""
        mock_run.return_value = _make_completed_process(0, "async-out", "")
        executor = RemoteExecutor(nodes=["async-node"])
        task = _make_task(task_id="async-1", node="async-node")

        result = asyncio.get_event_loop().run_until_complete(executor.execute_async(task))

        assert isinstance(result, RemoteResult)
        assert result.task_id == "async-1"
        assert result.stdout == "async-out"

    # @trace FR-COMPUTE-018
    @patch(
        "thegent.compute.remote_executor.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="ssh", timeout=5),
    )
    def test_execute_async_propagates_error(self, _run: MagicMock) -> None:
        """execute_async() propagates RemoteExecutorError from execute()."""
        executor = RemoteExecutor(nodes=["n1"])
        task = _make_task(node="n1")

        with pytest.raises(RemoteExecutorError):
            asyncio.get_event_loop().run_until_complete(executor.execute_async(task))


# ---------------------------------------------------------------------------
# RemoteExecutor.available_nodes
# ---------------------------------------------------------------------------


class TestAvailableNodes:
    """Tests for RemoteExecutor.available_nodes()."""

    # @trace FR-COMPUTE-019
    @patch("thegent.compute.remote_executor.subprocess.run")
    def test_all_reachable(self, mock_run: MagicMock) -> None:
        """available_nodes returns all nodes when ping succeeds for each."""
        mock_run.return_value = _make_completed_process(returncode=0)
        executor = RemoteExecutor(nodes=["n1", "n2", "n3"])

        assert executor.available_nodes() == ["n1", "n2", "n3"]

    # @trace FR-COMPUTE-019
    @patch("thegent.compute.remote_executor.subprocess.run")
    def test_unreachable_nodes_excluded(self, mock_run: MagicMock) -> None:
        """available_nodes filters out nodes whose ping returns non-zero."""
        # ping n1 OK, n2 fails, n3 OK
        mock_run.side_effect = [
            _make_completed_process(returncode=0),
            _make_completed_process(returncode=1),
            _make_completed_process(returncode=0),
        ]
        executor = RemoteExecutor(nodes=["n1", "n2", "n3"])

        assert executor.available_nodes() == ["n1", "n3"]

    # @trace FR-COMPUTE-019
    @patch("thegent.compute.remote_executor.subprocess.run")
    def test_all_unreachable_returns_empty(self, mock_run: MagicMock) -> None:
        """available_nodes returns [] when no nodes respond to ping."""
        mock_run.return_value = _make_completed_process(returncode=1)
        executor = RemoteExecutor(nodes=["dead1", "dead2"])

        assert executor.available_nodes() == []

    # @trace FR-COMPUTE-019
    def test_no_nodes_returns_empty(self) -> None:
        """available_nodes returns [] when executor has no configured nodes."""
        executor = RemoteExecutor(nodes=[])
        assert executor.available_nodes() == []

    # @trace FR-COMPUTE-019
    @patch(
        "thegent.compute.remote_executor.subprocess.run",
        side_effect=OSError("ping not found"),
    )
    def test_ping_os_error_treated_as_unreachable(self, _run: MagicMock) -> None:
        """OSError from ping subprocess marks the node as unreachable (no raise)."""
        executor = RemoteExecutor(nodes=["n1"])
        assert executor.available_nodes() == []

    # @trace FR-COMPUTE-019
    @patch(
        "thegent.compute.remote_executor.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="ping", timeout=5),
    )
    def test_ping_timeout_treated_as_unreachable(self, _run: MagicMock) -> None:
        """TimeoutExpired from ping marks the node as unreachable (no raise)."""
        executor = RemoteExecutor(nodes=["slow-node"])
        assert executor.available_nodes() == []

    # @trace FR-COMPUTE-019
    @patch("thegent.compute.remote_executor.subprocess.run")
    def test_ping_uses_correct_command(self, mock_run: MagicMock) -> None:
        """available_nodes calls ping with -c 1 -W 2 flags."""
        mock_run.return_value = _make_completed_process(returncode=0)
        executor = RemoteExecutor(nodes=["target"])
        executor.available_nodes()

        cmd = mock_run.call_args[0][0]
        assert cmd == ["ping", "-c", "1", "-W", "2", "target"]


# ---------------------------------------------------------------------------
# Package __init__ exports
# ---------------------------------------------------------------------------


class TestPackageExports:
    """Verify that compute/__init__.py re-exports RemoteExecutor symbols."""

    # @trace FR-COMPUTE-020
    def test_remote_executor_exported(self) -> None:
        """RemoteExecutor is importable from thegent.compute."""
        assert ExportedExecutor is RemoteExecutor

    # @trace FR-COMPUTE-020
    def test_remote_executor_error_exported(self) -> None:
        """RemoteExecutorError is importable from thegent.compute."""
        assert ExportedError is RemoteExecutorError

    # @trace FR-COMPUTE-020
    def test_remote_result_exported(self) -> None:
        """RemoteResult is importable from thegent.compute."""
        assert ExportedResult is RemoteResult

    # @trace FR-COMPUTE-020
    def test_remote_task_exported(self) -> None:
        """RemoteTask is importable from thegent.compute."""
        assert ExportedTask is RemoteTask
