"""WL-089: Tests for RemoteDispatchBackend + SubAgentDispatcher remote integration.

ComputePoolManager.submit() wired into SubAgentDispatcher as optional remote backend.

# @trace FR-ORC-089
# @trace WL-089
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from thegent.orchestration.protocol import (
    SubAgentRequest,
    SubAgentStatus,
)
from thegent.orchestration.remote_dispatch import (
    RemoteDispatchBackend,
    RemoteDispatchConfig,
    adapt_request_to_agent_task,
    adapt_result_to_sub_agent_result,
)
from thegent.orchestration.sub_agent_dispatcher import (
    CapabilityIndex,
    SubAgentDispatcher,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_request(**kwargs: Any) -> SubAgentRequest:
    defaults = {
        "agent_type": "test-agent",
        "task": "do something",
        "request_id": "req-test-001",
    }
    defaults.update(kwargs)
    return SubAgentRequest(**defaults)


def _make_mock_pool_manager() -> MagicMock:
    mgr = MagicMock()
    fake_result = MagicMock()
    fake_result.task_id = "req-test-001"
    fake_result.exit_code = 0
    fake_result.stdout = "done"
    fake_result.stderr = ""
    fake_result.timed_out = False
    fake_result.duration_ms = 123.0
    mgr.submit = AsyncMock(return_value=fake_result)
    return mgr


# ---------------------------------------------------------------------------
# adapt_request_to_agent_task
# ---------------------------------------------------------------------------


class TestAdaptRequestToAgentTask:
    """# @trace FR-ORC-089"""

    def test_basic_mapping(self) -> None:
        req = _make_request()
        task = adapt_request_to_agent_task(req)
        assert task.task_id == req.request_id
        assert task.prompt == req.task
        assert task.agent_name == req.agent_type
        assert task.timeout == req.timeout_seconds

    def test_cwd_from_context(self) -> None:
        req = _make_request(context={"cwd": "/tmp/myproject"})
        task = adapt_request_to_agent_task(req)
        assert task.cwd == "/tmp/myproject"

    def test_cwd_default(self) -> None:
        req = _make_request()
        task = adapt_request_to_agent_task(req)
        assert task.cwd == "."

    def test_mode_from_context(self) -> None:
        req = _make_request(context={"mode": "read"})
        task = adapt_request_to_agent_task(req)
        assert task.mode == "read"

    def test_mode_default(self) -> None:
        req = _make_request()
        task = adapt_request_to_agent_task(req)
        assert task.mode == "write"

    def test_env_from_metadata(self) -> None:
        req = _make_request(metadata={"env": {"MY_VAR": "value"}})
        task = adapt_request_to_agent_task(req)
        assert task.env == {"MY_VAR": "value"}

    def test_env_default_empty(self) -> None:
        req = _make_request()
        task = adapt_request_to_agent_task(req)
        assert task.env == {}


# ---------------------------------------------------------------------------
# adapt_result_to_sub_agent_result
# ---------------------------------------------------------------------------


class TestAdaptResultToSubAgentResult:
    """# @trace FR-ORC-089"""

    def _make_agent_result(self, exit_code: int = 0, stdout: str = "ok", timed_out: bool = False) -> MagicMock:
        r = MagicMock()
        r.task_id = "req-001"
        r.exit_code = exit_code
        r.stdout = stdout
        r.stderr = ""
        r.timed_out = timed_out
        r.duration_ms = 50.0
        return r

    def test_success_maps_to_completed(self) -> None:
        req = _make_request(request_id="req-001")
        agent_res = self._make_agent_result(exit_code=0)
        result = adapt_result_to_sub_agent_result(req, agent_res)
        assert result.status == SubAgentStatus.COMPLETED
        assert result.request_id == "req-001"

    def test_nonzero_exit_maps_to_failed(self) -> None:
        req = _make_request(request_id="req-001")
        agent_res = self._make_agent_result(exit_code=1)
        result = adapt_result_to_sub_agent_result(req, agent_res)
        assert result.status == SubAgentStatus.FAILED

    def test_timed_out_maps_to_failed(self) -> None:
        req = _make_request(request_id="req-001")
        agent_res = self._make_agent_result(exit_code=0, timed_out=True)
        result = adapt_result_to_sub_agent_result(req, agent_res)
        assert result.status == SubAgentStatus.FAILED

    def test_output_captured(self) -> None:
        req = _make_request(request_id="req-001")
        agent_res = self._make_agent_result(stdout="my output")
        result = adapt_result_to_sub_agent_result(req, agent_res)
        assert result.output.get("stdout") == "my output"

    def test_agent_type_preserved(self) -> None:
        req = _make_request(request_id="req-001", agent_type="special-agent")
        agent_res = self._make_agent_result()
        result = adapt_result_to_sub_agent_result(req, agent_res)
        assert result.agent_type == "special-agent"

    def test_duration_in_metrics(self) -> None:
        req = _make_request(request_id="req-001")
        agent_res = self._make_agent_result()
        agent_res.duration_ms = 250.0
        result = adapt_result_to_sub_agent_result(req, agent_res)
        assert result.metrics.get("duration_ms") == 250.0


# ---------------------------------------------------------------------------
# RemoteDispatchConfig
# ---------------------------------------------------------------------------


class TestRemoteDispatchConfig:
    """# @trace FR-ORC-089"""

    def test_defaults(self) -> None:
        cfg = RemoteDispatchConfig()
        assert cfg.enable_remote is False
        assert cfg.fallback_to_local is True
        assert cfg.sync_workspace is False

    def test_custom_values(self) -> None:
        cfg = RemoteDispatchConfig(enable_remote=True, fallback_to_local=False, sync_workspace=True)
        assert cfg.enable_remote is True
        assert cfg.fallback_to_local is False
        assert cfg.sync_workspace is True


# ---------------------------------------------------------------------------
# RemoteDispatchBackend
# ---------------------------------------------------------------------------


class TestRemoteDispatchBackend:
    """# @trace FR-ORC-089"""

    def test_dispatch_delegates_to_pool_manager(self) -> None:
        mgr = _make_mock_pool_manager()
        backend = RemoteDispatchBackend(pool_manager=mgr)
        req = _make_request(request_id="req-test-001")
        result = backend.dispatch(req)
        assert mgr.submit.called
        assert result.request_id == "req-test-001"
        assert result.status == SubAgentStatus.COMPLETED

    def test_dispatch_failed_on_nonzero_exit(self) -> None:
        mgr = _make_mock_pool_manager()
        fail_result = MagicMock()
        fail_result.task_id = "req-test-001"
        fail_result.exit_code = 1
        fail_result.stdout = "error occurred"
        fail_result.stderr = "some error"
        fail_result.timed_out = False
        fail_result.duration_ms = 0.0
        mgr.submit = AsyncMock(return_value=fail_result)

        backend = RemoteDispatchBackend(pool_manager=mgr)
        req = _make_request(request_id="req-test-001")
        result = backend.dispatch(req)
        assert result.status == SubAgentStatus.FAILED

    def test_dispatch_raises_when_no_pool_manager(self) -> None:
        backend = RemoteDispatchBackend(pool_manager=None)
        req = _make_request()
        with pytest.raises(RuntimeError, match="no ComputePoolManager"):
            backend.dispatch(req)

    def test_available_when_pool_manager_set(self) -> None:
        mgr = _make_mock_pool_manager()
        backend = RemoteDispatchBackend(pool_manager=mgr)
        assert backend.is_available() is True

    def test_not_available_without_pool_manager(self) -> None:
        backend = RemoteDispatchBackend(pool_manager=None)
        assert backend.is_available() is False


# ---------------------------------------------------------------------------
# SubAgentDispatcher remote backend integration
# ---------------------------------------------------------------------------


class TestSubAgentDispatcherRemoteBackend:
    """WL-089: SubAgentDispatcher with remote_backend wired in.

    # @trace FR-ORC-089
    """

    def test_dispatch_uses_remote_backend_when_set(self) -> None:
        mgr = _make_mock_pool_manager()
        backend = RemoteDispatchBackend(pool_manager=mgr)
        index = CapabilityIndex()
        index.register("compute", "remote-agent")

        dispatcher = SubAgentDispatcher(
            capability_index=index,
            remote_backend=backend,
        )
        req = _make_request(request_id="req-remote-001", agent_type="remote-agent")
        result = dispatcher.dispatch(req)
        assert mgr.submit.called
        assert result.status == SubAgentStatus.COMPLETED

    def test_dispatch_falls_back_to_local_when_backend_not_available(self) -> None:
        backend = RemoteDispatchBackend(pool_manager=None)
        index = CapabilityIndex()
        index.register("compute", "local-agent")

        dispatcher = SubAgentDispatcher(
            capability_index=index,
            remote_backend=backend,
        )
        req = _make_request(request_id="req-local-001", agent_type="local-agent")
        # Should not raise — falls back to local dispatch
        result = dispatcher.dispatch(req)
        assert result.request_id == "req-local-001"
        assert result.status == SubAgentStatus.COMPLETED

    def test_dispatch_without_remote_backend_is_local(self) -> None:
        index = CapabilityIndex()
        dispatcher = SubAgentDispatcher(capability_index=index)
        req = _make_request(request_id="req-no-remote-001")
        result = dispatcher.dispatch(req)
        assert result.request_id == "req-no-remote-001"
        assert result.status == SubAgentStatus.COMPLETED

    def test_dispatch_concurrent_with_remote_backend(self) -> None:
        mgr = _make_mock_pool_manager()
        backend = RemoteDispatchBackend(pool_manager=mgr)
        index = CapabilityIndex()
        dispatcher = SubAgentDispatcher(capability_index=index, remote_backend=backend)

        requests = [_make_request(request_id=f"req-{i}", agent_type="batch-agent") for i in range(3)]
        results = dispatcher.dispatch_concurrent(requests)
        assert len(results) == 3
        assert all(r.status == SubAgentStatus.COMPLETED for r in results)
        assert mgr.submit.call_count == 3


__all__: list[str] = []
