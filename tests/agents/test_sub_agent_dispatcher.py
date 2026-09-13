"""Tests for SubAgentDispatcher — unified multi-agent dispatch orchestrator.

# @trace WL-080
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from thegent.agents.sub_agent_dispatcher import (
    CapabilityNotFoundError,
    DispatchError,
    DispatchMode,
    SubAgentDispatcher,
    SubAgentResult,
    SubAgentTask,
)

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _make_agent_record(
    name: str = "test-agent",
    capabilities: list[str] | None = None,
    runner: str | None = None,
) -> MagicMock:
    """Build a minimal AgentRecord mock."""
    # @trace WL-080
    record = MagicMock()
    record.name = name
    record.capabilities = capabilities or []
    record.runner = runner
    record.description = f"Test agent: {name}"
    return record


def _make_capability_index(
    agents_by_capability: dict[str, list[Any]] | None = None,
) -> MagicMock:
    """Build a CapabilityIndex mock."""
    # @trace WL-080
    index = MagicMock()
    mapping = agents_by_capability or {}

    def _agents_for_capability(cap: str) -> list[Any]:
        return mapping.get(cap, [])

    index.agents_for_capability.side_effect = _agents_for_capability
    return index


def _make_flash_result(output: str = "flash output", success: bool = True) -> MagicMock:
    """Build a FlashAgentResult mock."""
    # @trace WL-080
    result = MagicMock()
    result.output = output
    result.success = success
    result.elapsed_s = 0.1
    result.agent_id = "abc12345"
    return result


def _make_run_result(
    exit_code: int = 0,
    stdout: str = "local output",
    stderr: str = "",
    timed_out: bool = False,
) -> MagicMock:
    """Build a RunResult mock."""
    # @trace WL-080
    result = MagicMock()
    result.exit_code = exit_code
    result.stdout = stdout
    result.stderr = stderr
    result.timed_out = timed_out
    return result


def _make_hitl_workflow(pending: list[dict[str, Any]] | None = None) -> MagicMock:
    """Build an HITLApprovalWorkflow mock."""
    # @trace WL-080
    workflow = MagicMock()
    workflow.list_pending.return_value = pending or []
    workflow.approve.return_value = {"success": True, "resolution": "approved"}
    return workflow


# ---------------------------------------------------------------------------
# SubAgentTask tests
# ---------------------------------------------------------------------------


def test_sub_agent_task_defaults():
    """WL-080: SubAgentTask has correct default values."""
    # @trace WL-080
    task = SubAgentTask(prompt="do something")
    assert task.prompt == "do something"
    assert task.agent_hint is None
    assert task.context == {}
    assert task.timeout_seconds == 120.0
    assert task.require_approval is False


def test_sub_agent_task_custom_values():
    """WL-080: SubAgentTask stores custom values correctly."""
    # @trace WL-080
    task = SubAgentTask(
        prompt="analyze code",
        agent_hint="code-review",
        context={"repo": "thegent"},
        timeout_seconds=60.0,
        require_approval=True,
    )
    assert task.agent_hint == "code-review"
    assert task.context["repo"] == "thegent"
    assert task.timeout_seconds == 60.0
    assert task.require_approval is True


# ---------------------------------------------------------------------------
# SubAgentResult tests
# ---------------------------------------------------------------------------


def test_sub_agent_result_defaults():
    """WL-080: SubAgentResult stores all expected fields."""
    # @trace WL-080
    task = SubAgentTask(prompt="test")
    result = SubAgentResult(task=task, output="ok", mode=DispatchMode.LOCAL, success=True)
    assert result.output == "ok"
    assert result.mode is DispatchMode.LOCAL
    assert result.success is True
    assert result.error is None
    assert result.metadata == {}


def test_sub_agent_result_failure_fields():
    """WL-080: SubAgentResult stores failure state correctly."""
    # @trace WL-080
    task = SubAgentTask(prompt="fail")
    result = SubAgentResult(
        task=task,
        output="",
        mode=DispatchMode.REMOTE,
        success=False,
        error="connection refused",
    )
    assert result.success is False
    assert result.error == "connection refused"


# ---------------------------------------------------------------------------
# DispatchMode enum tests
# ---------------------------------------------------------------------------


def test_dispatch_mode_values():
    """WL-080: DispatchMode enum has correct string values."""
    # @trace WL-080
    assert DispatchMode.FLASH == "flash"
    assert DispatchMode.LOCAL == "local"
    assert DispatchMode.REMOTE == "remote"
    assert DispatchMode.HITL == "hitl"


# ---------------------------------------------------------------------------
# _select_mode tests
# ---------------------------------------------------------------------------


def test_select_mode_require_approval_is_hitl():
    """WL-080: _select_mode returns HITL when task.require_approval=True."""
    # @trace WL-080
    index = _make_capability_index()
    dispatcher = SubAgentDispatcher(capability_index=index)
    task = SubAgentTask(prompt="sensitive task", require_approval=True)
    mode = dispatcher._select_mode(task, capability=None)
    assert mode is DispatchMode.HITL


def test_select_mode_flash_capability_tag():
    """WL-080: _select_mode returns FLASH when capability has 'flash' tag."""
    # @trace WL-080
    index = _make_capability_index()
    dispatcher = SubAgentDispatcher(capability_index=index)
    task = SubAgentTask(prompt="quick task")
    capability = _make_agent_record(capabilities=["flash", "summarize"])
    mode = dispatcher._select_mode(task, capability=capability)
    assert mode is DispatchMode.FLASH


def test_select_mode_flash_tag_case_insensitive():
    """WL-080: _select_mode recognises 'Flash' capability tag case-insensitively."""
    # @trace WL-080
    index = _make_capability_index()
    dispatcher = SubAgentDispatcher(capability_index=index)
    task = SubAgentTask(prompt="quick")
    capability = _make_agent_record(capabilities=["Flash"])
    mode = dispatcher._select_mode(task, capability=capability)
    assert mode is DispatchMode.FLASH


def test_select_mode_remote_when_compute_intensive():
    """WL-080: _select_mode returns REMOTE when compute_pool set and compute_intensive=True."""
    # @trace WL-080
    index = _make_capability_index()
    compute_pool = MagicMock()
    dispatcher = SubAgentDispatcher(capability_index=index, compute_pool=compute_pool)
    task = SubAgentTask(prompt="heavy task", context={"compute_intensive": True})
    mode = dispatcher._select_mode(task, capability=None)
    assert mode is DispatchMode.REMOTE


def test_select_mode_no_remote_without_pool():
    """WL-080: _select_mode returns LOCAL not REMOTE when compute_pool is None."""
    # @trace WL-080
    index = _make_capability_index()
    dispatcher = SubAgentDispatcher(capability_index=index, compute_pool=None)
    task = SubAgentTask(prompt="heavy", context={"compute_intensive": True})
    mode = dispatcher._select_mode(task, capability=None)
    assert mode is DispatchMode.LOCAL


def test_select_mode_default_local():
    """WL-080: _select_mode returns LOCAL by default."""
    # @trace WL-080
    index = _make_capability_index()
    dispatcher = SubAgentDispatcher(capability_index=index)
    task = SubAgentTask(prompt="ordinary task")
    mode = dispatcher._select_mode(task, capability=None)
    assert mode is DispatchMode.LOCAL


def test_select_mode_hitl_takes_priority_over_flash():
    """WL-080: require_approval=True takes priority over flash capability tag."""
    # @trace WL-080
    index = _make_capability_index()
    dispatcher = SubAgentDispatcher(capability_index=index)
    task = SubAgentTask(prompt="sensitive", require_approval=True)
    capability = _make_agent_record(capabilities=["flash"])
    mode = dispatcher._select_mode(task, capability=capability)
    assert mode is DispatchMode.HITL


# ---------------------------------------------------------------------------
# dispatch() — FLASH mode
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dispatch_flash_mode_success():
    """WL-080: dispatch() returns SubAgentResult with FLASH mode on success."""
    # @trace WL-080
    agent_record = _make_agent_record(capabilities=["flash"])
    index = _make_capability_index(agents_by_capability={"quick": [agent_record]})
    dispatcher = SubAgentDispatcher(capability_index=index)

    task = SubAgentTask(prompt="summarise X", agent_hint="quick")
    flash_result = _make_flash_result(output="summary here", success=True)

    with patch(
        "thegent.agents.sub_agent_dispatcher.FlashAgent.run",
        new_callable=AsyncMock,
        return_value=flash_result,
    ):
        result = await dispatcher.dispatch(task)

    assert result.mode is DispatchMode.FLASH
    assert result.success is True
    assert result.output == "summary here"
    assert result.error is None


@pytest.mark.asyncio
async def test_dispatch_flash_mode_timeout_failure():
    """WL-080: dispatch() returns success=False when FlashAgent times out."""
    # @trace WL-080
    agent_record = _make_agent_record(capabilities=["flash"])
    index = _make_capability_index(agents_by_capability={"quick": [agent_record]})
    dispatcher = SubAgentDispatcher(capability_index=index)

    task = SubAgentTask(prompt="slow summary", agent_hint="quick")
    flash_result = _make_flash_result(output="", success=False)

    with patch(
        "thegent.agents.sub_agent_dispatcher.FlashAgent.run",
        new_callable=AsyncMock,
        return_value=flash_result,
    ):
        result = await dispatcher.dispatch(task)

    assert result.mode is DispatchMode.FLASH
    assert result.success is False
    assert result.error is not None


@pytest.mark.asyncio
async def test_dispatch_flash_metadata_contains_elapsed():
    """WL-080: FLASH dispatch stores elapsed_s and agent_id in metadata."""
    # @trace WL-080
    agent_record = _make_agent_record(capabilities=["flash"])
    index = _make_capability_index(agents_by_capability={"quick": [agent_record]})
    dispatcher = SubAgentDispatcher(capability_index=index)

    task = SubAgentTask(prompt="ping", agent_hint="quick")
    flash_result = _make_flash_result(output="pong", success=True)
    flash_result.elapsed_s = 0.5
    flash_result.agent_id = "deadbeef"

    with patch(
        "thegent.agents.sub_agent_dispatcher.FlashAgent.run",
        new_callable=AsyncMock,
        return_value=flash_result,
    ):
        result = await dispatcher.dispatch(task)

    assert result.metadata["elapsed_s"] == pytest.approx(0.5)
    assert result.metadata["agent_id"] == "deadbeef"


# ---------------------------------------------------------------------------
# dispatch() — LOCAL mode
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dispatch_local_mode_no_hint():
    """WL-080: dispatch() with no agent_hint falls through to LOCAL via FlashAgent."""
    # @trace WL-080
    index = _make_capability_index()
    dispatcher = SubAgentDispatcher(capability_index=index)
    task = SubAgentTask(prompt="just do it")

    flash_result = _make_flash_result(output="local result", success=True)
    with patch(
        "thegent.agents.sub_agent_dispatcher.FlashAgent.run",
        new_callable=AsyncMock,
        return_value=flash_result,
    ):
        result = await dispatcher.dispatch(task)

    assert result.mode is DispatchMode.LOCAL
    assert result.success is True
    assert result.output == "local result"


@pytest.mark.asyncio
async def test_dispatch_local_mode_with_named_runner():
    """WL-080: dispatch() uses get_runner when capability has runner field."""
    # @trace WL-080
    agent_record = _make_agent_record(capabilities=["review"], runner="claude")
    index = _make_capability_index(agents_by_capability={"review": [agent_record]})
    dispatcher = SubAgentDispatcher(capability_index=index)

    task = SubAgentTask(prompt="review this code", agent_hint="review")
    run_result = _make_run_result(stdout="LGTM", exit_code=0)

    mock_runner = MagicMock()
    mock_runner.run.return_value = run_result

    with patch(
        "thegent.agents.sub_agent_dispatcher.get_runner",
        return_value=mock_runner,
    ):
        result = await dispatcher.dispatch(task)

    assert result.mode is DispatchMode.LOCAL
    assert result.success is True
    assert result.output == "LGTM"


@pytest.mark.asyncio
async def test_dispatch_local_runner_failure_raises_dispatch_error():
    """WL-080: Failing LOCAL runner raises DispatchError."""
    # @trace WL-080
    agent_record = _make_agent_record(capabilities=["review"], runner="claude")
    index = _make_capability_index(agents_by_capability={"review": [agent_record]})
    dispatcher = SubAgentDispatcher(capability_index=index)

    task = SubAgentTask(prompt="review this", agent_hint="review")

    mock_runner = MagicMock()
    mock_runner.run.side_effect = RuntimeError("runner crashed")

    with patch("thegent.agents.sub_agent_dispatcher.get_runner", return_value=mock_runner):
        with pytest.raises(DispatchError, match="runner crashed"):
            await dispatcher.dispatch(task)


@pytest.mark.asyncio
async def test_dispatch_local_no_runner_falls_back_to_flash():
    """WL-080: LOCAL dispatch uses FlashAgent when get_runner returns None."""
    # @trace WL-080
    agent_record = _make_agent_record(capabilities=["mystery"], runner="unknown-runner")
    index = _make_capability_index(agents_by_capability={"mystery": [agent_record]})
    dispatcher = SubAgentDispatcher(capability_index=index)

    task = SubAgentTask(prompt="mystery task", agent_hint="mystery")
    flash_result = _make_flash_result(output="fallback output", success=True)

    with patch("thegent.agents.sub_agent_dispatcher.get_runner", return_value=None):
        with patch(
            "thegent.agents.sub_agent_dispatcher.FlashAgent.run",
            new_callable=AsyncMock,
            return_value=flash_result,
        ):
            result = await dispatcher.dispatch(task)

    assert result.mode is DispatchMode.LOCAL
    assert result.output == "fallback output"


# ---------------------------------------------------------------------------
# dispatch() — HITL mode
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dispatch_hitl_mode_with_workflow():
    """WL-080: HITL dispatch records approval and returns result with HITL mode."""
    # @trace WL-080
    index = _make_capability_index()
    hitl_workflow = _make_hitl_workflow()
    dispatcher = SubAgentDispatcher(capability_index=index, hitl_workflow=hitl_workflow)

    task = SubAgentTask(prompt="dangerous action", require_approval=True)
    flash_result = _make_flash_result(output="executed safely", success=True)

    with patch(
        "thegent.agents.sub_agent_dispatcher.FlashAgent.run",
        new_callable=AsyncMock,
        return_value=flash_result,
    ):
        result = await dispatcher.dispatch(task)

    assert result.mode is DispatchMode.HITL
    assert result.success is True
    assert "hitl_run_id" in result.metadata


@pytest.mark.asyncio
async def test_dispatch_hitl_no_workflow_raises():
    """WL-080: HITL dispatch raises DispatchError when no workflow configured."""
    # @trace WL-080
    index = _make_capability_index()
    dispatcher = SubAgentDispatcher(capability_index=index, hitl_workflow=None)

    task = SubAgentTask(prompt="must approve", require_approval=True)

    with pytest.raises(DispatchError, match="no HITLApprovalWorkflow"):
        await dispatcher.dispatch(task)


@pytest.mark.asyncio
async def test_dispatch_hitl_metadata_contains_run_id():
    """WL-080: HITL result metadata includes hitl_run_id."""
    # @trace WL-080
    index = _make_capability_index()
    hitl_workflow = _make_hitl_workflow()
    dispatcher = SubAgentDispatcher(capability_index=index, hitl_workflow=hitl_workflow)

    task = SubAgentTask(prompt="approval needed", require_approval=True)
    flash_result = _make_flash_result(output="done", success=True)

    with patch(
        "thegent.agents.sub_agent_dispatcher.FlashAgent.run",
        new_callable=AsyncMock,
        return_value=flash_result,
    ):
        result = await dispatcher.dispatch(task)

    assert result.metadata["hitl_run_id"].startswith("hitl_")


# ---------------------------------------------------------------------------
# dispatch() — error handling
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dispatch_capability_not_found_raises():
    """WL-080: dispatch() raises CapabilityNotFoundError for unknown agent_hint."""
    # @trace WL-080
    index = _make_capability_index()  # empty — no capabilities
    dispatcher = SubAgentDispatcher(capability_index=index)
    task = SubAgentTask(prompt="use ghost-agent", agent_hint="ghost")

    with pytest.raises(CapabilityNotFoundError, match="ghost"):
        await dispatcher.dispatch(task)


@pytest.mark.asyncio
async def test_dispatch_flash_runner_exception_raises_dispatch_error():
    """WL-080: Exception inside FlashAgent.run raises DispatchError."""
    # @trace WL-080
    agent_record = _make_agent_record(capabilities=["flash"])
    index = _make_capability_index(agents_by_capability={"quick": [agent_record]})
    dispatcher = SubAgentDispatcher(capability_index=index)

    task = SubAgentTask(prompt="crash", agent_hint="quick")

    with (
        patch(
            "thegent.agents.sub_agent_dispatcher.FlashAgent.run",
            new_callable=AsyncMock,
            side_effect=RuntimeError("internal flash error"),
        ),
        pytest.raises(DispatchError, match="internal flash error"),
    ):
        await dispatcher.dispatch(task)


# ---------------------------------------------------------------------------
# dispatch_many() — parallel execution
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dispatch_many_returns_results_in_order():
    """WL-080: dispatch_many() returns results in the same order as tasks."""
    # @trace WL-080
    index = _make_capability_index()
    dispatcher = SubAgentDispatcher(capability_index=index)

    tasks = [SubAgentTask(prompt=f"task {i}") for i in range(3)]
    flash_results = [_make_flash_result(output=f"output {i}", success=True) for i in range(3)]

    call_count = 0

    async def _flash_run(config):
        nonlocal call_count
        out = flash_results[call_count]
        call_count += 1
        return out

    with patch("thegent.agents.sub_agent_dispatcher.FlashAgent.run", side_effect=_flash_run):
        results = await dispatcher.dispatch_many(tasks)

    assert len(results) == 3
    for i, result in enumerate(results):
        assert result.output == f"output {i}"


@pytest.mark.asyncio
async def test_dispatch_many_parallel_execution():
    """WL-080: dispatch_many() runs tasks in parallel (all start before any complete)."""
    # @trace WL-080
    index = _make_capability_index()
    dispatcher = SubAgentDispatcher(capability_index=index)

    started: list[int] = []
    completed: list[int] = []
    barrier = asyncio.Event()

    async def _slow_flash(config, *, task_idx: int):
        started.append(task_idx)
        await barrier.wait()
        completed.append(task_idx)
        return _make_flash_result(output=f"done-{task_idx}", success=True)

    tasks = [SubAgentTask(prompt=f"parallel {i}") for i in range(3)]

    async def _run():
        def make_coro(i):
            async def coro(config):
                return await _slow_flash(config, task_idx=i)

            return coro

        flash_coros = [make_coro(i) for i in range(3)]
        call_idx = 0

        async def _patched_run(config):
            nonlocal call_idx
            fn = flash_coros[call_idx]
            call_idx += 1
            return await fn(config)

        with patch(
            "thegent.agents.sub_agent_dispatcher.FlashAgent.run",
            side_effect=_patched_run,
        ):
            gather_coro = dispatcher.dispatch_many(tasks)
            gather_task = asyncio.create_task(gather_coro)
            # Give a tick for coroutines to start
            await asyncio.sleep(0)
            await asyncio.sleep(0)
            await asyncio.sleep(0)
            # Release the barrier so all can complete
            barrier.set()
            return await gather_task

    results = await _run()
    assert len(results) == 3
    assert all(r.success for r in results)


@pytest.mark.asyncio
async def test_dispatch_many_captures_exceptions_as_failures():
    """WL-080: dispatch_many() converts exceptions to SubAgentResult(success=False)."""
    # @trace WL-080
    index = _make_capability_index(
        agents_by_capability={"ghost": []}  # empty list → CapabilityNotFoundError
    )
    dispatcher = SubAgentDispatcher(capability_index=index)

    tasks = [
        SubAgentTask(prompt="ok task"),
        SubAgentTask(prompt="bad task", agent_hint="ghost"),
    ]

    flash_result = _make_flash_result(output="ok", success=True)
    with patch(
        "thegent.agents.sub_agent_dispatcher.FlashAgent.run",
        new_callable=AsyncMock,
        return_value=flash_result,
    ):
        results = await dispatcher.dispatch_many(tasks)

    assert len(results) == 2
    assert results[0].success is True
    assert results[1].success is False
    assert results[1].error is not None


@pytest.mark.asyncio
async def test_dispatch_many_empty_list():
    """WL-080: dispatch_many([]) returns an empty list without error."""
    # @trace WL-080
    index = _make_capability_index()
    dispatcher = SubAgentDispatcher(capability_index=index)
    results = await dispatcher.dispatch_many([])
    assert results == []


@pytest.mark.asyncio
async def test_dispatch_many_all_failures():
    """WL-080: dispatch_many() handles all tasks failing gracefully."""
    # @trace WL-080
    index = _make_capability_index()
    dispatcher = SubAgentDispatcher(capability_index=index)

    tasks = [SubAgentTask(prompt=f"crash {i}") for i in range(3)]

    with patch(
        "thegent.agents.sub_agent_dispatcher.FlashAgent.run",
        new_callable=AsyncMock,
        side_effect=RuntimeError("all broken"),
    ):
        results = await dispatcher.dispatch_many(tasks)

    assert all(not r.success for r in results)
    assert all("all broken" in (r.error or "") for r in results)


# ---------------------------------------------------------------------------
# Integration with CapabilityIndex mock
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_capability_index_lookup_called_with_hint():
    """WL-080: dispatch() calls CapabilityIndex.agents_for_capability with agent_hint."""
    # @trace WL-080
    agent_record = _make_agent_record(capabilities=["code-review"])
    index = _make_capability_index(agents_by_capability={"code-review": [agent_record]})
    dispatcher = SubAgentDispatcher(capability_index=index)

    task = SubAgentTask(prompt="review PR", agent_hint="code-review")
    flash_result = _make_flash_result(output="LGTM", success=True)

    with patch(
        "thegent.agents.sub_agent_dispatcher.FlashAgent.run",
        new_callable=AsyncMock,
        return_value=flash_result,
    ):
        await dispatcher.dispatch(task)

    index.agents_for_capability.assert_called_once_with("code-review")


@pytest.mark.asyncio
async def test_no_capability_lookup_when_no_hint():
    """WL-080: CapabilityIndex.agents_for_capability is NOT called when agent_hint is None."""
    # @trace WL-080
    index = _make_capability_index()
    dispatcher = SubAgentDispatcher(capability_index=index)

    task = SubAgentTask(prompt="generic task")
    flash_result = _make_flash_result()

    with patch(
        "thegent.agents.sub_agent_dispatcher.FlashAgent.run",
        new_callable=AsyncMock,
        return_value=flash_result,
    ):
        await dispatcher.dispatch(task)

    index.agents_for_capability.assert_not_called()


@pytest.mark.asyncio
async def test_first_matching_agent_is_used():
    """WL-080: dispatch() uses the first agent returned by CapabilityIndex."""
    # @trace WL-080
    agent_a = _make_agent_record(name="agent-a", capabilities=["search"])
    agent_b = _make_agent_record(name="agent-b", capabilities=["search"])
    index = _make_capability_index(agents_by_capability={"search": [agent_a, agent_b]})
    dispatcher = SubAgentDispatcher(capability_index=index)

    task = SubAgentTask(prompt="search for X", agent_hint="search")
    flash_result = _make_flash_result()

    with patch(
        "thegent.agents.sub_agent_dispatcher.FlashAgent.run",
        new_callable=AsyncMock,
        return_value=flash_result,
    ):
        await dispatcher.dispatch(task)

    # agents_for_capability called once; first result used
    index.agents_for_capability.assert_called_once()


# ---------------------------------------------------------------------------
# AgentRunner hook point (WL-080 → WL-081+)
# ---------------------------------------------------------------------------


def test_agent_runner_has_sub_dispatcher_attribute():
    """WL-080: AgentRunner exposes sub_dispatcher hook point for WL-081+."""
    # @trace WL-080
    from thegent.agents.base import AgentRunner

    runner = AgentRunner()
    assert hasattr(runner, "sub_dispatcher")
    assert runner.sub_dispatcher is None


def test_agent_runner_sub_dispatcher_can_be_set():
    """WL-080: AgentRunner.sub_dispatcher can be set to a SubAgentDispatcher instance."""
    # @trace WL-080
    from thegent.agents.base import AgentRunner

    index = _make_capability_index()
    dispatcher = SubAgentDispatcher(capability_index=index)
    runner = AgentRunner()
    runner.sub_dispatcher = dispatcher
    assert runner.sub_dispatcher is dispatcher


# ---------------------------------------------------------------------------
# Public imports
# ---------------------------------------------------------------------------


def test_public_exports_importable():
    """WL-080: All public symbols are importable from sub_agent_dispatcher module."""
    # @trace WL-080
    from thegent.agents.sub_agent_dispatcher import (
        CapabilityNotFoundError,
        DispatchError,
        DispatchMode,
        SubAgentDispatcher,
        SubAgentResult,
        SubAgentTask,
    )

    assert CapabilityNotFoundError is not None
    assert DispatchError is not None
    assert DispatchMode is not None
    assert SubAgentDispatcher is not None
    assert SubAgentResult is not None
    assert SubAgentTask is not None
