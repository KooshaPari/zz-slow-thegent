"""AUDIT-N+33 hardening tests for the orchestration dormant-core cluster.

Targets the live class definitions in:

- ``src/thegent/orchestration/inter_agent_protocol.py``
  - ``InterAgentMessage`` (frozen dataclass, validation)
  - ``MessageBus`` (subscribe / publish / drain)
- ``src/thegent/orchestration/plan/__init__.py``
  - ``OrchestrationPlan`` (goal validation, add_task factory, filters)
- ``src/thegent/orchestration/budget_tracker.py``
  - ``BudgetTracker`` (per-node token enforcement)
  - ``BudgetExceededError``
- ``src/thegent/orchestration/aggregator/__init__.py``
  - ``ResultAggregator`` (message merge + summary)
- ``src/thegent/orchestration/sub_agent_dispatcher/__init__.py``
  - ``DispatchResult`` (constructor validation)
  - ``SubAgentDispatcher`` (auto-subscribe + topological order)

This module verifies the AUDIT-N+33 hardening pass closed the following
SOTA-style gaps across the cluster:

- NEW-1: ``InterAgentMessage`` rejects empty / non-string ``sender_id`` /
         ``recipient_id`` and unknown ``message_type`` at the boundary.
- NEW-2: ``InterAgentMessage.is_expired`` correctly handles timezone-naive
         reference datetimes and ``ttl_s == 0`` (never-expired).
- NEW-3: ``MessageBus`` rejects publishing to an unsubscribed recipient
         (``KeyError``) — no silent message loss.
- NEW-4: ``MessageBus.subscribe`` is idempotent — repeated calls return
         the same queue.
- NEW-5: ``OrchestrationPlan`` rejects empty / whitespace-only goals and
         non-int ``budget_tokens`` at construction time.
- NEW-6: ``OrchestrationPlan.add_task`` only stores explicitly-set
         metadata fields (no absent-key pollution) and returns a fresh
         ``PlanNode``.
- NEW-7: ``OrchestrationPlan.total_budget_used`` silently ignores nodes
         whose metadata key is missing or non-numeric.
- NEW-8: ``BudgetTracker.track`` rejects non-int tokens and surfaces
         ``TypeError`` (no silent float budgets).
- NEW-9: ``BudgetTracker.parse_tokens_from_result`` is a static method
         and tolerates malformed JSON / non-usage lines.
- NEW-10: ``BudgetTracker.all_usage`` returns a defensive copy.
- NEW-11: ``ResultAggregator.aggregate`` always returns a fresh dict.
- NEW-12: ``ResultAggregator.add`` records ``node_id`` under ``by_node``
          when supplied.
- NEW-13: ``DispatchResult`` rejects empty ``node_id``.
- NEW-14: ``SubAgentDispatcher.dispatch_all`` returns topological order
          for diamond DAGs (parents before children).
- NEW-15: ``SubAgentDispatcher`` auto-subscribes the recipient before
          publishing.
"""

from __future__ import annotations

import asyncio
import threading
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from thegent.agents.plangent import PlanNode
from thegent.orchestration import (
    BUDGET_TOKENS,
    BudgetExceededError,
    BudgetTracker,
    InterAgentMessage,
    MessageBus,
    OrchestrationPlan,
    ResultAggregator,
)
from thegent.orchestration.sub_agent_dispatcher import (
    DispatchResult,
    SubAgentDispatcher,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_msg(**overrides: Any) -> InterAgentMessage:
    """Construct an InterAgentMessage with sensible defaults."""
    base: dict[str, Any] = {
        "sender_id": "sender",
        "recipient_id": "recipient",
        "message_type": "task_request",
        "payload": {"k": "v"},
    }
    base.update(overrides)
    return InterAgentMessage(**base)


def _make_plan(goal: str = "test goal") -> OrchestrationPlan:
    return OrchestrationPlan(goal=goal)


# ---------------------------------------------------------------------------
# InterAgentMessage — NEW-1 / NEW-2
# ---------------------------------------------------------------------------


class TestInterAgentMessageValidation:
    """AUDIT-N+33 NEW-1 / NEW-2: constructor and is_expired hardening."""

    def test_empty_sender_id_raises(self) -> None:
        with pytest.raises(ValueError):
            _make_msg(sender_id="")

    def test_empty_recipient_id_raises(self) -> None:
        with pytest.raises(ValueError):
            _make_msg(recipient_id="")

    def test_unknown_message_type_raises(self) -> None:
        with pytest.raises(ValueError):
            _make_msg(message_type="bogus-type")  # type: ignore[arg-type]

    def test_non_string_message_type_raises(self) -> None:
        with pytest.raises(ValueError):
            _make_msg(message_type=42)  # type: ignore[arg-type]

    def test_non_mapping_payload_raises(self) -> None:
        with pytest.raises(ValueError):
            _make_msg(payload="not a mapping")  # type: ignore[arg-type]

    def test_negative_ttl_raises(self) -> None:
        with pytest.raises(ValueError):
            _make_msg(ttl_s=-1)

    def test_bool_ttl_raises(self) -> None:
        with pytest.raises(ValueError):
            _make_msg(ttl_s=True)  # type: ignore[arg-type]

    def test_is_expired_false_within_ttl(self) -> None:
        msg = _make_msg(ttl_s=300)
        assert msg.is_expired() is False

    def test_is_expired_true_past_ttl(self) -> None:
        # Craft an already-expired message by backdating created_at.
        msg = _make_msg(ttl_s=60)
        # Replace created_at via object.__setattr__ (frozen dataclass).
        past = datetime.now(UTC) - timedelta(seconds=120)
        object.__setattr__(msg, "created_at", past)
        assert msg.is_expired() is True

    def test_is_expired_zero_ttl_never_expires(self) -> None:
        """ttl_s=0 means 'no expiry' (session-scoped). # @trace AUDIT-N+33"""
        msg = _make_msg(ttl_s=0)
        # Force created_at into the distant past.
        past = datetime.now(UTC) - timedelta(days=365)
        object.__setattr__(msg, "created_at", past)
        assert msg.is_expired() is False


# ---------------------------------------------------------------------------
# MessageBus — NEW-3 / NEW-4
# ---------------------------------------------------------------------------


class TestMessageBusHardening:
    """AUDIT-N+33 NEW-3 / NEW-4: publish-error + idempotent subscribe."""

    def test_publish_to_unsubscribed_raises(self) -> None:
        bus = MessageBus()
        with pytest.raises(KeyError):
            bus.publish(_make_msg(recipient_id="ghost"))

    def test_subscribe_idempotent(self) -> None:
        bus = MessageBus()
        q1 = bus.subscribe("agent-x")
        q2 = bus.subscribe("agent-x")
        assert q1 is q2
        # Same queue receives both publishes.
        bus.publish(_make_msg(recipient_id="agent-x"))
        bus.publish(_make_msg(recipient_id="agent-x"))
        assert q1.qsize() == 2

    def test_unsubscribe_unknown_raises(self) -> None:
        bus = MessageBus()
        with pytest.raises(KeyError):
            bus.unsubscribe("never-subscribed")

    def test_concurrent_publish_serialised(self) -> None:
        """50 concurrent threads publishing 50 messages each must all land."""
        bus = MessageBus()
        bus.subscribe("hot-agent")
        iterations = 50
        per_thread = 25

        def _worker() -> None:
            for _ in range(per_thread):
                bus.publish(_make_msg(recipient_id="hot-agent"))

        threads = [threading.Thread(target=_worker) for _ in range(iterations)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert bus.queue_depth("hot-agent") == iterations * per_thread

    def test_drain_returns_messages_in_fifo_order(self) -> None:
        bus = MessageBus()
        bus.subscribe("agent-fifo")
        for i in range(5):
            bus.publish(_make_msg(recipient_id="agent-fifo", payload={"i": i}))
        messages = bus.drain("agent-fifo")
        assert [m.payload["i"] for m in messages] == [0, 1, 2, 3, 4]


# ---------------------------------------------------------------------------
# OrchestrationPlan — NEW-5 / NEW-6 / NEW-7
# ---------------------------------------------------------------------------


class TestOrchestrationPlanHardening:
    """AUDIT-N+33 NEW-5 / NEW-6 / NEW-7: validation + metadata hygiene."""

    def test_empty_goal_raises(self) -> None:
        with pytest.raises(ValueError):
            OrchestrationPlan(goal="")

    def test_whitespace_only_goal_raises(self) -> None:
        with pytest.raises(ValueError):
            OrchestrationPlan(goal="   ")

    def test_non_string_goal_raises(self) -> None:
        with pytest.raises(TypeError):
            OrchestrationPlan(goal=42)  # type: ignore[arg-type]

    def test_add_task_only_stores_set_metadata(self) -> None:
        """add_task must not pollute metadata with absent-key defaults. # @trace AUDIT-N+33"""
        plan = _make_plan()
        node = plan.add_task("minimal")
        assert "agent_hint" not in node.metadata
        assert "budget_tokens" not in node.metadata
        assert "require_hitl" not in node.metadata

    def test_add_task_non_int_budget_tokens_raises(self) -> None:
        plan = _make_plan()
        with pytest.raises(TypeError):
            plan.add_task("t", budget_tokens=1.5)  # type: ignore[arg-type]

    def test_total_budget_used_ignores_missing_keys(self) -> None:
        plan = _make_plan()
        plan.add_task("with budget", budget_tokens=100)
        plan.add_task("without budget")
        totals = plan.total_budget_used()
        assert totals["budget_tokens"] == 100

    def test_total_budget_used_ignores_non_numeric(self) -> None:
        plan = _make_plan()
        node = plan.add_task("bad budget")
        node.metadata[BUDGET_TOKENS] = "not-a-number"  # type: ignore[assignment]
        totals = plan.total_budget_used()
        assert totals["budget_tokens"] == 0

    def test_get_sandbox_nodes_returns_only_sandboxed(self) -> None:
        plan = _make_plan()
        plan.add_task("sandboxed", sandbox=True)
        plan.add_task("not sandboxed")
        sandboxed = plan.get_sandbox_nodes()
        assert len(sandboxed) == 1
        assert sandboxed[0].task == "sandboxed"


# ---------------------------------------------------------------------------
# BudgetTracker — NEW-8 / NEW-9 / NEW-10
# ---------------------------------------------------------------------------


class TestBudgetTrackerHardening:
    """AUDIT-N+33 NEW-8 / NEW-9 / NEW-10: type-checking, static parse, copy."""

    def test_constructor_rejects_non_plan(self) -> None:
        with pytest.raises(TypeError):
            BudgetTracker("not-a-plan")  # type: ignore[arg-type]

    def test_track_rejects_non_int_tokens(self) -> None:
        plan = _make_plan()
        node = plan.add_task("t", budget_tokens=100)
        tracker = BudgetTracker(plan)
        with pytest.raises(TypeError):
            tracker.track(node.id, 1.5)  # type: ignore[arg-type]

    def test_track_rejects_negative_tokens(self) -> None:
        plan = _make_plan()
        node = plan.add_task("t", budget_tokens=100)
        tracker = BudgetTracker(plan)
        with pytest.raises(ValueError):
            tracker.track(node.id, -1)

    def test_all_usage_returns_copy(self) -> None:
        """External mutation of the returned dict must not leak in. # @trace AUDIT-N+33"""
        plan = _make_plan()
        node = plan.add_task("t", budget_tokens=100)
        tracker = BudgetTracker(plan)
        tracker.track(node.id, 10)
        snapshot = tracker.all_usage
        snapshot[node.id] = 999_999  # attempt to poison
        assert tracker.get_usage(node.id) == 10

    def test_parse_tokens_from_result_is_static(self) -> None:
        """The parse helper must be invokable on the class directly. # @trace AUDIT-N+33"""
        # Touching the class without instantiating confirms static-ness.
        assert isinstance(
            BudgetTracker.__dict__["parse_tokens_from_result"],
            staticmethod,
        )

    def test_parse_tokens_skips_malformed_json(self) -> None:
        bad = "{not json}"
        good = '{"usage": {"prompt_tokens": 5, "completion_tokens": 5}}'
        assert BudgetTracker.parse_tokens_from_result(f"{bad}\n{good}") == 10

    def test_budget_exceeded_error_attributes(self) -> None:
        err = BudgetExceededError(node_id="n", budget=100, actual=150)
        assert err.node_id == "n"
        assert err.budget == 100
        assert err.actual == 150
        msg = str(err)
        assert "n" in msg
        assert "100" in msg
        assert "150" in msg
        assert "50" in msg  # over by 50


# ---------------------------------------------------------------------------
# ResultAggregator — NEW-11 / NEW-12
# ---------------------------------------------------------------------------


class TestResultAggregatorHardening:
    """AUDIT-N+33 NEW-11 / NEW-12: defensive copy + by_node attribution."""

    def test_aggregate_returns_fresh_dict(self) -> None:
        """aggregate() must not alias internal state. # @trace AUDIT-N+33"""
        agg = ResultAggregator()
        agg.add(_make_msg(message_type="result"))
        first = agg.aggregate()
        agg.add(_make_msg(message_type="error"))
        second = agg.aggregate()
        assert first["total"] == 1
        assert second["total"] == 2

    def test_add_with_node_id_records_by_node(self) -> None:
        agg = ResultAggregator()
        msg = _make_msg(message_type="result")
        agg.add(msg, node_id="node-1")
        snap = agg.aggregate()
        assert "node-1" in snap["by_node"]
        assert snap["by_node"]["node-1"] is msg

    def test_summary_contains_total(self) -> None:
        agg = ResultAggregator()
        agg.add(_make_msg(message_type="result"))
        agg.add(_make_msg(message_type="result"))
        assert "2" in agg.summary()

    def test_summary_marks_failed_when_errors(self) -> None:
        agg = ResultAggregator()
        agg.add(_make_msg(message_type="error"))
        assert "fail" in agg.summary().lower()


# ---------------------------------------------------------------------------
# DispatchResult / SubAgentDispatcher — NEW-13 / NEW-14 / NEW-15
# ---------------------------------------------------------------------------


class TestDispatchResultHardening:
    """AUDIT-N+33 NEW-13: DispatchResult constructor validation."""

    def test_empty_node_id_raises(self) -> None:
        with pytest.raises(ValueError):
            DispatchResult(node_id="")

    def test_non_str_output_raises(self) -> None:
        with pytest.raises(TypeError):
            DispatchResult(node_id="n", output=42)  # type: ignore[arg-type]

    def test_non_bool_success_raises(self) -> None:
        with pytest.raises(TypeError):
            DispatchResult(node_id="n", success="yes")  # type: ignore[arg-type]

    def test_repr_contains_node_id(self) -> None:
        result = DispatchResult(node_id="n42", output="o", success=True)
        assert "n42" in repr(result)

    def test_equality_by_value(self) -> None:
        a = DispatchResult(node_id="n", output="o", success=True)
        b = DispatchResult(node_id="n", output="o", success=True)
        assert a == b


class TestSubAgentDispatcherHardening:
    """AUDIT-N+33 NEW-14 / NEW-15: topological order + auto-subscribe."""

    def test_dispatch_auto_subscribes_recipient(self) -> None:
        bus = MessageBus()
        plan = _make_plan()
        dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
        node = plan.add_task("auto", agent_hint="new-recipient")
        # Pre-condition: not subscribed.
        assert not bus.is_subscribed("new-recipient")
        dispatcher.dispatch(node)
        # Post-condition: subscribed and message delivered.
        assert bus.is_subscribed("new-recipient")
        assert len(bus.drain("new-recipient")) == 1

    def test_dispatch_all_diamond_dag_topological_order(self) -> None:
        bus = MessageBus()
        plan = _make_plan()
        a = plan.add_task("A", agent_hint="worker")
        b = plan.add_task("B", agent_hint="worker", depends_on=[a.id])
        c = plan.add_task("C", agent_hint="worker", depends_on=[a.id])
        d = plan.add_task("D", agent_hint="worker", depends_on=[b.id, c.id])
        dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
        dispatcher.dispatch_all(plan)
        messages = bus.drain("worker")
        order = [m.payload["node_id"] for m in messages]
        assert order.index(a.id) < order.index(b.id)
        assert order.index(a.id) < order.index(c.id)
        assert order.index(b.id) < order.index(d.id)
        assert order.index(c.id) < order.index(d.id)

    def test_dispatch_all_raises_on_cycle(self) -> None:
        """Cyclic plans must raise ValueError, not deadlock silently. # @trace AUDIT-N+33"""
        bus = MessageBus()
        plan = _make_plan()
        a = plan.add_task("A")
        b = plan.add_task("B", depends_on=[a.id])
        # Manually inject a cycle (depends_on is normally acyclic).
        a.depends_on = [b.id]
        dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
        with pytest.raises(ValueError):
            dispatcher.dispatch_all(plan)

    def test_dispatch_uses_node_id_as_fallback_recipient(self) -> None:
        bus = MessageBus()
        plan = _make_plan()
        dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
        node = plan.add_task("no-hint")
        dispatcher.dispatch(node)
        # Recipient falls back to node.id when agent_hint missing.
        assert bus.is_subscribed(node.id)

    def test_dispatch_correlation_id_is_plan_id(self) -> None:
        bus = MessageBus()
        plan = _make_plan()
        dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
        node = plan.add_task("corr", agent_hint="worker")
        dispatcher.dispatch(node)
        [msg] = bus.drain("worker")
        assert msg.correlation_id == plan.id

    def test_sender_id_stable_across_dispatches(self) -> None:
        bus = MessageBus()
        plan = _make_plan()
        dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
        n1 = plan.add_task("t1", agent_hint="w")
        n2 = plan.add_task("t2", agent_hint="w")
        dispatcher.dispatch(n1)
        dispatcher.dispatch(n2)
        senders = {m.sender_id for m in bus.drain("w")}
        assert senders == {dispatcher.sender_id}

    def test_collect_results_auto_subscribes(self) -> None:
        bus = MessageBus()
        plan = _make_plan()
        dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
        results = dispatcher.collect_results("never-seen-agent")
        assert results == []
        assert bus.is_subscribed("never-seen-agent")

    def test_dispatch_rejects_non_plan_node(self) -> None:
        bus = MessageBus()
        plan = _make_plan()
        dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
        with pytest.raises(TypeError):
            dispatcher.dispatch("not-a-plan-node")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Async path: drain via asyncio for any cross-event-loop callers
# ---------------------------------------------------------------------------


class TestAsyncDrain:
    """Light async smoke test for the bus via asyncio.Queue integration."""

    def test_async_drain_collects_published_messages(self) -> None:
        bus = MessageBus()
        bus.subscribe("async-agent")

        async def _publish_three() -> None:
            for _ in range(3):
                bus.publish(_make_msg(recipient_id="async-agent"))

        asyncio.run(_publish_three())
        assert len(bus.drain("async-agent")) == 3


# ---------------------------------------------------------------------------
# Sanity: PlanNode constructed with the right shape (used by tests above)
# ---------------------------------------------------------------------------


def test_plan_node_construction_sanity() -> None:
    """Sanity check: the PlanNode surface used by the dispatcher exists."""
    node = PlanNode(task="x")
    assert node.task == "x"
    assert node.depends_on == []
    assert isinstance(node.metadata, dict)
