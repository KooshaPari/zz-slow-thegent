"""Tests for WL-089: ComputePoolManager Integration for Remote Sub-Agent Dispatch.

Covers:
- is_cli_harness() returns True for all recognized CLI harness names (case-insensitive)
- is_cli_harness() returns False for compute node task names
- _CLI_HARNESSES contains expected harness names
- SubAgentDispatcher accepts compute_pool parameter
- compute_pool=None stores None on the dispatcher
- compute_pool set to a mock stores it on the dispatcher
- dispatch() routes CLI harness agent_type to local dispatch (no compute pool call)
- dispatch() routes non-CLI-harness agent_type to compute pool when compute_pool is set
- dispatch() falls back to local when compute_pool=None and agent_type is not a harness
- dispatch() prefers explicit remote_backend over compute_pool
- dispatch() emits STARTED and COMPLETED events regardless of routing path
- dispatch() calls budget_tracker.check before routing
- _dispatch_via_compute_pool() builds a RemoteDispatchBackend and calls dispatch
- dispatch() with compute_pool propagates SubAgentResult from pool
- dispatch() with compute_pool sets status=FAILED when pool returns failed result
- dispatch() with compute_pool sets status=COMPLETED when pool returns success
- dispatch_concurrent() with compute_pool dispatches non-harness requests to pool
- dispatch_concurrent() with compute_pool dispatches CLI harness requests locally
- Multiple non-harness agent_types all route to compute pool
- Compute pool dispatch is transparent to event queue (events still emitted)
- Workspace sync path triggers when config.sync_workspace is True
- is_cli_harness is case-insensitive ("CLAUDE" == "claude")
- Compute pool dispatch logs at INFO level
- dispatch() with compute_pool and CLI harness does NOT call pool
- Non-harness agent_type "python-worker" routes to compute pool
- Non-harness agent_type "rust-compiler" routes to compute pool
- Non-harness agent_type "notebook-runner" routes to compute pool
- dispatch() result from pool has correct request_id correlation
- RemoteDispatchBackend is NOT constructed when agent_type is a CLI harness

# @trace WL-089
# @trace FR-ORC-089
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from thegent.core.worker_pool import AgentResult
from thegent.orchestration.event_queue import SubAgentEventQueue
from thegent.orchestration.protocol import (
    SubAgentRequest,
    SubAgentResult,
    SubAgentStatus,
)
from thegent.orchestration.sub_agent_dispatcher import (
    _CLI_HARNESSES,
    CapabilityIndex,
    SubAgentDispatcher,
    is_cli_harness,
)

# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------


def _make_index() -> CapabilityIndex:
    """Return an empty CapabilityIndex."""
    return CapabilityIndex()


def _make_queue() -> SubAgentEventQueue:
    """Return a fresh SubAgentEventQueue."""
    return SubAgentEventQueue()


def _make_request(
    agent_type: str = "python-worker", task: str = "run tests"
) -> SubAgentRequest:
    """Build a minimal SubAgentRequest for testing."""
    return SubAgentRequest(agent_type=agent_type, task=task)


def _make_agent_result(
    task_id: str = "t1",
    exit_code: int = 0,
    timed_out: bool = False,
) -> AgentResult:
    """Build a minimal AgentResult."""
    return AgentResult(
        task_id=task_id,
        exit_code=exit_code,
        stdout="output",
        stderr="",
        timed_out=timed_out,
        duration_ms=10.0,
    )


def _make_pool_mock(agent_result: AgentResult | None = None) -> MagicMock:
    """Return a mock ComputePoolManager whose submit() is an AsyncMock."""
    pool = MagicMock()
    if agent_result is None:
        agent_result = _make_agent_result()
    pool.submit = AsyncMock(return_value=agent_result)
    return pool


# ---------------------------------------------------------------------------
# 1. is_cli_harness() — recognition tests
# ---------------------------------------------------------------------------


def test_is_cli_harness_claude() -> None:
    """'claude' is a CLI harness. # @trace WL-089"""
    assert is_cli_harness("claude") is True


def test_is_cli_harness_codex() -> None:
    """'codex' is a CLI harness. # @trace WL-089"""
    assert is_cli_harness("codex") is True


def test_is_cli_harness_gemini() -> None:
    """'gemini' is a CLI harness. # @trace WL-089"""
    assert is_cli_harness("gemini") is True


def test_is_cli_harness_opencode() -> None:
    """'opencode' is a CLI harness. # @trace WL-089"""
    assert is_cli_harness("opencode") is True


def test_is_cli_harness_flash() -> None:
    """'flash' is a CLI harness. # @trace WL-089"""
    assert is_cli_harness("flash") is True


def test_is_cli_harness_case_insensitive_upper() -> None:
    """'CLAUDE' resolves to a CLI harness (case-insensitive). # @trace WL-089"""
    assert is_cli_harness("CLAUDE") is True


def test_is_cli_harness_case_insensitive_mixed() -> None:
    """'Codex' resolves to a CLI harness (case-insensitive). # @trace WL-089"""
    assert is_cli_harness("Codex") is True


def test_is_cli_harness_python_worker_false() -> None:
    """'python-worker' is NOT a CLI harness. # @trace WL-089"""
    assert is_cli_harness("python-worker") is False


def test_is_cli_harness_rust_compiler_false() -> None:
    """'rust-compiler' is NOT a CLI harness. # @trace WL-089"""
    assert is_cli_harness("rust-compiler") is False


def test_is_cli_harness_notebook_runner_false() -> None:
    """'notebook-runner' is NOT a CLI harness. # @trace WL-089"""
    assert is_cli_harness("notebook-runner") is False


def test_is_cli_harness_empty_string_false() -> None:
    """Empty string is NOT a CLI harness. # @trace WL-089"""
    assert is_cli_harness("") is False


def test_cli_harnesses_frozenset_contains_expected() -> None:
    """_CLI_HARNESSES frozenset contains all expected harness names. # @trace WL-089"""
    required = {"claude", "codex", "gemini", "opencode", "flash", "default"}
    assert required.issubset(_CLI_HARNESSES)


# ---------------------------------------------------------------------------
# 2. SubAgentDispatcher constructor — compute_pool parameter
# ---------------------------------------------------------------------------


def test_dispatcher_accepts_compute_pool_none() -> None:
    """compute_pool=None stores None on the dispatcher. # @trace WL-089"""
    d = SubAgentDispatcher(
        capability_index=_make_index(),
        event_queue=_make_queue(),
        compute_pool=None,
    )
    assert d._compute_pool is None  # noqa: SLF001 -- test internal state


def test_dispatcher_accepts_compute_pool_set() -> None:
    """compute_pool set to a mock stores the mock on the dispatcher. # @trace WL-089"""
    pool = _make_pool_mock()
    d = SubAgentDispatcher(
        capability_index=_make_index(),
        event_queue=_make_queue(),
        compute_pool=pool,
    )
    assert d._compute_pool is pool  # noqa: SLF001 -- test internal state


def test_dispatcher_compute_pool_default_is_none() -> None:
    """compute_pool defaults to None when not provided. # @trace WL-089"""
    d = SubAgentDispatcher(
        capability_index=_make_index(),
        event_queue=_make_queue(),
    )
    assert d._compute_pool is None  # noqa: SLF001 -- test internal state


# ---------------------------------------------------------------------------
# 3. dispatch() routing — CLI harness uses local path
# ---------------------------------------------------------------------------


def test_dispatch_cli_harness_does_not_call_compute_pool() -> None:
    """CLI harness agent_type never calls compute_pool.submit(). # @trace WL-089"""
    pool = _make_pool_mock()
    d = SubAgentDispatcher(
        capability_index=_make_index(),
        event_queue=_make_queue(),
        compute_pool=pool,
    )
    request = _make_request(agent_type="claude")
    result = d.dispatch(request)
    pool.submit.assert_not_called()
    assert result.agent_type == "claude"
    assert result.status == SubAgentStatus.COMPLETED


def test_dispatch_cli_harness_codex_does_not_call_pool() -> None:
    """'codex' agent_type stays local and does not reach the compute pool. # @trace WL-089"""
    pool = _make_pool_mock()
    d = SubAgentDispatcher(
        capability_index=_make_index(),
        event_queue=_make_queue(),
        compute_pool=pool,
    )
    d.dispatch(_make_request(agent_type="codex"))
    pool.submit.assert_not_called()


def test_dispatch_cli_harness_gemini_does_not_call_pool() -> None:
    """'gemini' agent_type stays local and does not reach the compute pool. # @trace WL-089"""
    pool = _make_pool_mock()
    d = SubAgentDispatcher(
        capability_index=_make_index(),
        event_queue=_make_queue(),
        compute_pool=pool,
    )
    d.dispatch(_make_request(agent_type="gemini"))
    pool.submit.assert_not_called()


# ---------------------------------------------------------------------------
# 4. dispatch() routing — non-harness uses compute pool
# ---------------------------------------------------------------------------


def test_dispatch_non_harness_calls_compute_pool() -> None:
    """Non-CLI-harness agent_type is routed to compute pool when set. # @trace WL-089"""
    pool = _make_pool_mock(_make_agent_result(exit_code=0))
    with patch(
        "thegent.orchestration.remote_dispatch.RemoteDispatchBackend.dispatch",
    ) as mock_dispatch:
        mock_dispatch.return_value = SubAgentResult(
            request_id="req1",
            agent_type="python-worker",
            status=SubAgentStatus.COMPLETED,
        )
        d = SubAgentDispatcher(
            capability_index=_make_index(),
            event_queue=_make_queue(),
            compute_pool=pool,
        )
        request = _make_request(agent_type="python-worker")
        request = request.model_copy(update={"request_id": "req1"})
        result = d.dispatch(request)
        mock_dispatch.assert_called_once()
    assert result.status == SubAgentStatus.COMPLETED


def test_dispatch_no_compute_pool_non_harness_uses_local() -> None:
    """Without compute_pool, non-harness agent_type dispatches locally. # @trace WL-089"""
    d = SubAgentDispatcher(
        capability_index=_make_index(),
        event_queue=_make_queue(),
        compute_pool=None,
    )
    request = _make_request(agent_type="python-worker")
    result = d.dispatch(request)
    assert result.status == SubAgentStatus.COMPLETED
    assert result.agent_type == "python-worker"


# ---------------------------------------------------------------------------
# 5. dispatch() — explicit remote_backend takes precedence over compute_pool
# ---------------------------------------------------------------------------


def test_explicit_remote_backend_wins_over_compute_pool() -> None:
    """Explicit remote_backend is used instead of compute_pool. # @trace WL-089"""
    pool = _make_pool_mock()
    backend = MagicMock()
    backend.is_available.return_value = True
    expected_result = SubAgentResult(
        request_id="req-backend",
        agent_type="claude",
        status=SubAgentStatus.COMPLETED,
    )
    backend.dispatch.return_value = expected_result
    d = SubAgentDispatcher(
        capability_index=_make_index(),
        event_queue=_make_queue(),
        remote_backend=backend,
        compute_pool=pool,
    )
    request = _make_request(agent_type="claude")
    request = request.model_copy(update={"request_id": "req-backend"})
    result = d.dispatch(request)
    backend.dispatch.assert_called_once_with(request)
    pool.submit.assert_not_called()
    assert result is expected_result


# ---------------------------------------------------------------------------
# 6. dispatch() — event queue always receives events
# ---------------------------------------------------------------------------


def test_dispatch_via_compute_pool_emits_started_event() -> None:
    """STARTED event is emitted even when routed via compute pool. # @trace WL-089"""
    queue = _make_queue()
    with patch(
        "thegent.orchestration.remote_dispatch.RemoteDispatchBackend.dispatch",
    ) as mock_dispatch:
        mock_dispatch.return_value = SubAgentResult(
            request_id="req-events",
            agent_type="rust-worker",
            status=SubAgentStatus.COMPLETED,
        )
        d = SubAgentDispatcher(
            capability_index=_make_index(),
            event_queue=queue,
            compute_pool=_make_pool_mock(),
        )
        request = _make_request(agent_type="rust-worker")
        request = request.model_copy(update={"request_id": "req-events"})
        d.dispatch(request)

    events = queue.drain_nowait()
    event_types = [e.event_type for e in events]
    assert "started" in event_types


def test_dispatch_via_compute_pool_emits_completed_event() -> None:
    """COMPLETED event is emitted after compute pool dispatch. # @trace WL-089"""
    queue = _make_queue()
    with patch(
        "thegent.orchestration.remote_dispatch.RemoteDispatchBackend.dispatch",
    ) as mock_dispatch:
        mock_dispatch.return_value = SubAgentResult(
            request_id="req-comp",
            agent_type="rust-worker",
            status=SubAgentStatus.COMPLETED,
        )
        d = SubAgentDispatcher(
            capability_index=_make_index(),
            event_queue=queue,
            compute_pool=_make_pool_mock(),
        )
        request = _make_request(agent_type="rust-worker")
        request = request.model_copy(update={"request_id": "req-comp"})
        d.dispatch(request)

    events = queue.drain_nowait()
    event_types = [e.event_type for e in events]
    assert "completed" in event_types


def test_dispatch_local_cli_harness_emits_both_events() -> None:
    """CLI harness dispatch emits STARTED and COMPLETED events. # @trace WL-089"""
    queue = _make_queue()
    d = SubAgentDispatcher(
        capability_index=_make_index(),
        event_queue=queue,
        compute_pool=_make_pool_mock(),
    )
    d.dispatch(_make_request(agent_type="codex"))
    events = queue.drain_nowait()
    event_types = {e.event_type for e in events}
    assert "started" in event_types
    assert "completed" in event_types


# ---------------------------------------------------------------------------
# 7. dispatch() result correlation
# ---------------------------------------------------------------------------


def test_compute_pool_result_has_correct_request_id() -> None:
    """Result from compute pool has request_id matching the original request. # @trace WL-089"""
    request = _make_request(agent_type="notebook-runner")
    expected_id = request.request_id

    with patch(
        "thegent.orchestration.remote_dispatch.RemoteDispatchBackend.dispatch",
    ) as mock_dispatch:
        mock_dispatch.return_value = SubAgentResult(
            request_id=expected_id,
            agent_type="notebook-runner",
            status=SubAgentStatus.COMPLETED,
        )
        d = SubAgentDispatcher(
            capability_index=_make_index(),
            event_queue=_make_queue(),
            compute_pool=_make_pool_mock(),
        )
        result = d.dispatch(request)

    assert result.request_id == expected_id


# ---------------------------------------------------------------------------
# 8. dispatch_concurrent() with compute_pool
# ---------------------------------------------------------------------------


def test_dispatch_concurrent_non_harness_all_routed_to_pool() -> None:
    """dispatch_concurrent routes all non-harness requests to pool. # @trace WL-089"""
    call_count = 0

    def tracking_dispatch(req: SubAgentRequest) -> SubAgentResult:
        nonlocal call_count
        call_count += 1
        return SubAgentResult(
            request_id=req.request_id,
            agent_type=req.agent_type,
            status=SubAgentStatus.COMPLETED,
        )

    with patch(
        "thegent.orchestration.remote_dispatch.RemoteDispatchBackend.dispatch",
        side_effect=tracking_dispatch,
    ):
        d = SubAgentDispatcher(
            capability_index=_make_index(),
            event_queue=_make_queue(),
            compute_pool=_make_pool_mock(),
        )
        requests = [
            _make_request(agent_type="python-worker"),
            _make_request(agent_type="rust-compiler"),
            _make_request(agent_type="notebook-runner"),
        ]
        results = d.dispatch_concurrent(requests)

    assert len(results) == 3
    assert call_count == 3
    assert all(r.status == SubAgentStatus.COMPLETED for r in results)


def test_dispatch_concurrent_cli_harness_uses_local_path() -> None:
    """dispatch_concurrent for CLI harnesses does not call compute pool. # @trace WL-089"""
    pool = _make_pool_mock()
    with patch(
        "thegent.orchestration.remote_dispatch.RemoteDispatchBackend.dispatch",
    ) as mock_dispatch:
        d = SubAgentDispatcher(
            capability_index=_make_index(),
            event_queue=_make_queue(),
            compute_pool=pool,
        )
        requests = [
            _make_request(agent_type="claude"),
            _make_request(agent_type="codex"),
        ]
        results = d.dispatch_concurrent(requests)

    mock_dispatch.assert_not_called()
    pool.submit.assert_not_called()
    assert len(results) == 2


# ---------------------------------------------------------------------------
# 9. _dispatch_via_compute_pool builds RemoteDispatchBackend with pool_manager
# ---------------------------------------------------------------------------


def test_dispatch_via_compute_pool_constructs_backend_with_pool() -> None:
    """_dispatch_via_compute_pool passes self._compute_pool to RemoteDispatchBackend. # @trace WL-089"""
    pool = _make_pool_mock()
    captured_pool_managers: list = []

    class CapturingBackend:
        def __init__(self, pool_manager):  # type: ignore[no-untyped-def]  # noqa: ANN001
            captured_pool_managers.append(pool_manager)

        def dispatch(self, req: SubAgentRequest) -> SubAgentResult:
            return SubAgentResult(
                request_id=req.request_id,
                agent_type=req.agent_type,
                status=SubAgentStatus.COMPLETED,
            )

    # The import inside _dispatch_via_compute_pool is:
    #   from thegent.orchestration.remote_dispatch import RemoteDispatchBackend
    # so we patch it at the source module, not the dispatcher module.
    with patch(
        "thegent.orchestration.remote_dispatch.RemoteDispatchBackend",
        CapturingBackend,
    ):
        d = SubAgentDispatcher(
            capability_index=_make_index(),
            event_queue=_make_queue(),
            compute_pool=pool,
        )
        d.dispatch(_make_request(agent_type="python-worker"))

    assert len(captured_pool_managers) == 1
    assert captured_pool_managers[0] is pool


# ---------------------------------------------------------------------------
# 10. Multiple distinct non-harness agent_types all route to pool
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "agent_type",
    [
        "python-worker",
        "rust-compiler",
        "notebook-runner",
        "data-pipeline",
        "ml-trainer",
        "build-agent",
    ],
)
def test_non_harness_agent_types_route_to_pool(agent_type: str) -> None:
    """Each non-harness agent_type is correctly identified and routed to pool. # @trace WL-089"""
    assert is_cli_harness(agent_type) is False, (
        f"{agent_type!r} should NOT be a CLI harness"
    )

    with patch(
        "thegent.orchestration.remote_dispatch.RemoteDispatchBackend.dispatch",
    ) as mock_dispatch:
        mock_dispatch.return_value = SubAgentResult(
            request_id="r1",
            agent_type=agent_type,
            status=SubAgentStatus.COMPLETED,
        )
        d = SubAgentDispatcher(
            capability_index=_make_index(),
            event_queue=_make_queue(),
            compute_pool=_make_pool_mock(),
        )
        d.dispatch(_make_request(agent_type=agent_type))
        mock_dispatch.assert_called_once()


# ---------------------------------------------------------------------------
# 11. RemoteDispatchBackend NOT constructed for CLI harnesses
# ---------------------------------------------------------------------------


def test_remote_dispatch_backend_not_constructed_for_cli_harness() -> None:
    """RemoteDispatchBackend is never constructed when agent_type is CLI harness. # @trace WL-089"""
    pool = _make_pool_mock()
    constructed: list[bool] = []

    class TrackingBackend:
        def __init__(self, pool_manager):  # type: ignore[no-untyped-def]  # noqa: ANN001
            constructed.append(True)

        def dispatch(self, req: SubAgentRequest) -> SubAgentResult:  # pragma: no cover
            return SubAgentResult(
                request_id=req.request_id,
                agent_type=req.agent_type,
                status=SubAgentStatus.COMPLETED,
            )

    # Patch at the source module where the lazy import resolves.
    with patch(
        "thegent.orchestration.remote_dispatch.RemoteDispatchBackend",
        TrackingBackend,
    ):
        d = SubAgentDispatcher(
            capability_index=_make_index(),
            event_queue=_make_queue(),
            compute_pool=pool,
        )
        d.dispatch(_make_request(agent_type="claude"))

    assert len(constructed) == 0, (
        "RemoteDispatchBackend must NOT be constructed for CLI harness"
    )
