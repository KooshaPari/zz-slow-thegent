"""Tests for SubAgentDispatcher: capability-backed dispatch with budget enforcement.

@trace FR-ORC-082
"""

from __future__ import annotations

import logging

import pytest

from thegent.orchestration.budget_tracker import BudgetExceededError, BudgetTracker
from thegent.orchestration.protocol import (
    SubAgentRequest,
    SubAgentResult,
    SubAgentStatus,
)
from thegent.orchestration.sub_agent_dispatcher import (
    CapabilityIndex,
    SubAgentDispatcher,
)


def _make_request(
    *,
    request_id: str = "req-1",
    agent_type: str = "test-agent",
    task: str = "do something",
    capabilities: list[str] | None = None,
) -> SubAgentRequest:
    return SubAgentRequest(
        request_id=request_id,
        agent_type=agent_type,
        task=task,
        capabilities=capabilities or [],
    )


@pytest.mark.requirement("FR-ORC-082")
class TestCapabilityIndex:
    def test_capability_index_register_and_lookup(self) -> None:
        """register() then lookup() returns the registered agent_name."""
        index = CapabilityIndex()
        index.register("code_review", "reviewer-agent")
        assert index.lookup("code_review") == "reviewer-agent"

    def test_capability_index_lookup_unknown_raises(self) -> None:
        """lookup() raises KeyError for an unregistered capability."""
        index = CapabilityIndex()
        with pytest.raises(KeyError):
            index.lookup("unknown-capability")

    def test_capability_index_register_overwrites(self) -> None:
        """Registering the same capability twice replaces the first agent_name."""
        index = CapabilityIndex()
        index.register("cap-a", "agent-1")
        index.register("cap-a", "agent-2")
        assert index.lookup("cap-a") == "agent-2"

    def test_capability_index_multiple_capabilities(self) -> None:
        """Multiple capabilities can be registered independently."""
        index = CapabilityIndex()
        index.register("cap-x", "agent-x")
        index.register("cap-y", "agent-y")
        assert index.lookup("cap-x") == "agent-x"
        assert index.lookup("cap-y") == "agent-y"


@pytest.mark.requirement("FR-ORC-082")
class TestSubAgentDispatcherDispatch:
    def test_sub_agent_dispatcher_dispatch_returns_result(self) -> None:
        """dispatch() returns a SubAgentResult with COMPLETED status."""
        index = CapabilityIndex()
        dispatcher = SubAgentDispatcher(capability_index=index)
        request = _make_request()
        result = dispatcher.dispatch(request)
        assert isinstance(result, SubAgentResult)
        assert result.request_id == request.request_id
        assert result.status == SubAgentStatus.COMPLETED

    def test_sub_agent_dispatcher_dispatch_result_has_agent_type(self) -> None:
        """dispatch() result carries the agent_type from the request."""
        index = CapabilityIndex()
        dispatcher = SubAgentDispatcher(capability_index=index)
        request = _make_request(agent_type="my-agent")
        result = dispatcher.dispatch(request)
        assert result.agent_type == "my-agent"


@pytest.mark.requirement("FR-ORC-082")
class TestSubAgentDispatcherBudget:
    def test_sub_agent_dispatcher_budget_check_called(self) -> None:
        """dispatch() calls budget_tracker.check() when budget_tracker provided."""
        tracker = BudgetTracker(budgets={"req-1": 10_000})
        index = CapabilityIndex()
        dispatcher = SubAgentDispatcher(capability_index=index, budget_tracker=tracker)
        request = _make_request(request_id="req-1")
        result = dispatcher.dispatch(request)
        # Should succeed without raising
        assert result.status == SubAgentStatus.COMPLETED

    def test_sub_agent_dispatcher_budget_exceeded_raises(self) -> None:
        """dispatch() raises BudgetExceededError when request_id budget is zero."""
        tracker = BudgetTracker(budgets={"req-1": 0})
        # Pre-exhaust the budget by recording 1 token (1 > 0 raises on record,
        # so we use check() path: budget=0, any tokens>0 will exceed)
        index = CapabilityIndex()
        dispatcher = SubAgentDispatcher(capability_index=index, budget_tracker=tracker)
        request = _make_request(request_id="req-1")
        with pytest.raises(BudgetExceededError):
            dispatcher.dispatch(request)

    def test_sub_agent_dispatcher_no_budget_tracker_no_check(self) -> None:
        """dispatch() without budget_tracker succeeds regardless of token count."""
        index = CapabilityIndex()
        dispatcher = SubAgentDispatcher(capability_index=index, budget_tracker=None)
        request = _make_request(request_id="req-1")
        result = dispatcher.dispatch(request)
        assert result.status == SubAgentStatus.COMPLETED


@pytest.mark.requirement("FR-ORC-082")
class TestSubAgentDispatcherConcurrent:
    def test_sub_agent_dispatcher_dispatch_concurrent_multiple(self) -> None:
        """dispatch_concurrent() dispatches multiple requests and returns all results."""
        index = CapabilityIndex()
        dispatcher = SubAgentDispatcher(capability_index=index)
        requests = [_make_request(request_id=f"req-{i}") for i in range(5)]
        results = dispatcher.dispatch_concurrent(requests)
        assert len(results) == 5
        assert all(isinstance(r, SubAgentResult) for r in results)
        assert all(r.status == SubAgentStatus.COMPLETED for r in results)

    def test_sub_agent_dispatcher_dispatch_concurrent_empty(self) -> None:
        """dispatch_concurrent() with empty list returns empty list."""
        index = CapabilityIndex()
        dispatcher = SubAgentDispatcher(capability_index=index)
        results = dispatcher.dispatch_concurrent([])
        assert results == []

    def test_sub_agent_dispatcher_dispatch_concurrent_preserves_order(self) -> None:
        """dispatch_concurrent() results correspond to the order of requests."""
        index = CapabilityIndex()
        dispatcher = SubAgentDispatcher(capability_index=index)
        request_ids = [f"req-{i}" for i in range(3)]
        requests = [_make_request(request_id=rid) for rid in request_ids]
        results = dispatcher.dispatch_concurrent(requests)
        result_ids = [r.request_id for r in results]
        assert result_ids == request_ids


@pytest.mark.requirement("FR-ORC-082")
class TestSubAgentDispatcherEvents:
    def test_sub_agent_dispatcher_emits_started_event(self, caplog: pytest.LogCaptureFixture) -> None:
        """dispatch() logs a STARTED event at INFO level."""
        index = CapabilityIndex()
        dispatcher = SubAgentDispatcher(capability_index=index)
        request = _make_request(request_id="req-start")
        with caplog.at_level(logging.INFO):
            dispatcher.dispatch(request)
        # At least one log record should mention the start of dispatch
        log_text = " ".join(caplog.messages)
        assert "req-start" in log_text or "started" in log_text.lower()

    def test_sub_agent_dispatcher_emits_completed_event(self, caplog: pytest.LogCaptureFixture) -> None:
        """dispatch() logs a COMPLETED event at INFO level on success."""
        index = CapabilityIndex()
        dispatcher = SubAgentDispatcher(capability_index=index)
        request = _make_request(request_id="req-done")
        with caplog.at_level(logging.INFO):
            dispatcher.dispatch(request)
        log_text = " ".join(caplog.messages)
        assert "req-done" in log_text or "completed" in log_text.lower()
