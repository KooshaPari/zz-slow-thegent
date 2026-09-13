"""Tests for WL-082: SubAgentDispatcher.

Covers:
- Constructor accepts MessageBus and OrchestrationPlan
- dispatch(plan_node) creates an InterAgentMessage with message_type="task_request"
- dispatch(plan_node) publishes message to the MessageBus
- dispatch(plan_node) returns the message id (string)
- dispatch_all(plan) dispatches all nodes in dependency order (parents before children)
- dispatch_all(plan) returns list of message ids
- collect_results(agent_id, timeout_s) drains messages for a given agent
- Fail-fast: KeyError on unsubscribed recipient/agent
- dispatch_all handles plans with no nodes (empty list)
- dispatch_all handles single-node plans
- dispatch_all handles linear chains (A -> B -> C)
- dispatch_all handles diamond DAG (A -> B,C -> D)
- dispatch_all handles multiple independent roots
- Message payload includes task description
- Message sender_id is set from dispatcher
- Message recipient_id is derived from plan node metadata (agent_hint) or node id
- Returned message ids are unique across multiple dispatches
- collect_results returns empty list when no messages queued
- collect_results returns all queued messages for agent
- Dispatcher uses MessageBus.subscribe when dispatching to ensure recipient registered
- dispatch_all respects dependency ordering (parent dispatched before child)
- dispatch_all with plan containing metadata agent_hint routes to that agent
- Multiple dispatch calls on same node each produce unique message ids
- dispatch raises if node's recipient is not subscribed and no auto-subscribe
- collect_results with zero timeout still drains existing messages synchronously
- dispatch_all on plan with two parallel leaf nodes dispatches both
- Message correlation_id links dispatched messages to plan id
- Dispatcher attribute bus is the MessageBus passed in constructor
- Dispatcher attribute plan is the OrchestrationPlan passed in constructor
- dispatch includes node id in payload

# @trace WL-082
"""

from __future__ import annotations

import uuid

from thegent.orchestration.inter_agent_protocol import InterAgentMessage, MessageBus
from thegent.orchestration.plan import OrchestrationPlan
from thegent.orchestration.sub_agent_dispatcher import SubAgentDispatcher

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_bus() -> MessageBus:
    return MessageBus()


def _make_plan(goal: str = "test goal") -> OrchestrationPlan:
    return OrchestrationPlan(goal=goal)


def _make_dispatcher(
    bus: MessageBus | None = None,
    plan: OrchestrationPlan | None = None,
) -> SubAgentDispatcher:
    if bus is None:
        bus = _make_bus()
    if plan is None:
        plan = _make_plan()
    return SubAgentDispatcher(bus=bus, plan=plan)


# ---------------------------------------------------------------------------
# 1. Constructor
# ---------------------------------------------------------------------------


def test_dispatcher_stores_bus() -> None:
    """Dispatcher exposes bus attribute equal to the one passed in. # @trace WL-082"""
    bus = _make_bus()
    plan = _make_plan()
    dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
    assert dispatcher.bus is bus


def test_dispatcher_stores_plan() -> None:
    """Dispatcher exposes plan attribute equal to the one passed in. # @trace WL-082"""
    bus = _make_bus()
    plan = _make_plan()
    dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
    assert dispatcher.plan is plan


# ---------------------------------------------------------------------------
# 2. dispatch(plan_node) — message creation
# ---------------------------------------------------------------------------


def test_dispatch_returns_string_id() -> None:
    """dispatch must return a non-empty string. # @trace WL-082"""
    bus = _make_bus()
    plan = _make_plan()
    dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
    node = plan.add_task("step 1", agent_hint="agent-alpha")
    bus.subscribe("agent-alpha")
    msg_id = dispatcher.dispatch(node)
    assert isinstance(msg_id, str)
    assert len(msg_id) > 0


def test_dispatch_returns_uuid4_id() -> None:
    """dispatch return value must be a valid UUID4. # @trace WL-082"""
    bus = _make_bus()
    plan = _make_plan()
    dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
    node = plan.add_task("step 1", agent_hint="agent-alpha")
    bus.subscribe("agent-alpha")
    msg_id = dispatcher.dispatch(node)
    parsed = uuid.UUID(msg_id, version=4)
    assert str(parsed) == msg_id


def test_dispatch_message_type_is_task_request() -> None:
    """Published message must have message_type='task_request'. # @trace WL-082"""
    bus = _make_bus()
    plan = _make_plan()
    dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
    node = plan.add_task("step 1", agent_hint="agent-alpha")
    bus.subscribe("agent-alpha")
    msg_id = dispatcher.dispatch(node)
    messages = bus.drain("agent-alpha")
    assert len(messages) == 1
    assert messages[0].message_type == "task_request"
    assert messages[0].id == msg_id


def test_dispatch_publishes_to_bus() -> None:
    """dispatch must put exactly one message in the bus queue for the recipient. # @trace WL-082"""
    bus = _make_bus()
    plan = _make_plan()
    dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
    node = plan.add_task("step 1", agent_hint="worker")
    bus.subscribe("worker")
    dispatcher.dispatch(node)
    messages = bus.drain("worker")
    assert len(messages) == 1


def test_dispatch_payload_contains_task() -> None:
    """Message payload must contain the node's task description. # @trace WL-082"""
    bus = _make_bus()
    plan = _make_plan()
    dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
    node = plan.add_task("analyse the codebase", agent_hint="worker")
    bus.subscribe("worker")
    dispatcher.dispatch(node)
    messages = bus.drain("worker")
    assert messages[0].payload["task"] == "analyse the codebase"


def test_dispatch_payload_contains_node_id() -> None:
    """Message payload must include the dispatched node's id. # @trace WL-082"""
    bus = _make_bus()
    plan = _make_plan()
    dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
    node = plan.add_task("task A", agent_hint="worker")
    bus.subscribe("worker")
    dispatcher.dispatch(node)
    messages = bus.drain("worker")
    assert messages[0].payload["node_id"] == node.id


def test_dispatch_message_has_correlation_id_equal_to_plan_id() -> None:
    """correlation_id must be set to the plan's id. # @trace WL-082"""
    bus = _make_bus()
    plan = _make_plan()
    dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
    node = plan.add_task("step", agent_hint="worker")
    bus.subscribe("worker")
    dispatcher.dispatch(node)
    messages = bus.drain("worker")
    assert messages[0].correlation_id == plan.id


def test_dispatch_message_sender_id_is_set() -> None:
    """dispatcher.sender_id must appear as sender_id in the message. # @trace WL-082"""
    bus = _make_bus()
    plan = _make_plan()
    dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
    node = plan.add_task("step", agent_hint="worker")
    bus.subscribe("worker")
    dispatcher.dispatch(node)
    messages = bus.drain("worker")
    assert messages[0].sender_id == dispatcher.sender_id


def test_dispatch_message_recipient_is_agent_hint() -> None:
    """recipient_id must be the node's agent_hint when set. # @trace WL-082"""
    bus = _make_bus()
    plan = _make_plan()
    dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
    node = plan.add_task("step", agent_hint="special-agent")
    bus.subscribe("special-agent")
    dispatcher.dispatch(node)
    messages = bus.drain("special-agent")
    assert messages[0].recipient_id == "special-agent"


def test_dispatch_multiple_calls_produce_unique_ids() -> None:
    """Dispatching the same node twice must yield two distinct message ids. # @trace WL-082"""
    bus = _make_bus()
    plan = _make_plan()
    dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
    node = plan.add_task("step", agent_hint="worker")
    bus.subscribe("worker")
    id1 = dispatcher.dispatch(node)
    id2 = dispatcher.dispatch(node)
    assert id1 != id2


def test_dispatch_auto_subscribes_recipient() -> None:
    """dispatch must subscribe the recipient if not already subscribed, then publish. # @trace WL-082"""
    bus = _make_bus()
    plan = _make_plan()
    dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
    node = plan.add_task("step", agent_hint="new-agent")
    # Do NOT pre-subscribe; dispatcher must handle it
    msg_id = dispatcher.dispatch(node)
    messages = bus.drain("new-agent")
    assert len(messages) == 1
    assert messages[0].id == msg_id


def test_dispatch_without_agent_hint_uses_node_id_as_recipient() -> None:
    """When agent_hint is absent, recipient_id falls back to node.id. # @trace WL-082"""
    bus = _make_bus()
    plan = _make_plan()
    dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
    node = plan.add_task("step with no hint")
    msg_id = dispatcher.dispatch(node)
    messages = bus.drain(node.id)
    assert len(messages) == 1
    assert messages[0].id == msg_id
    assert messages[0].recipient_id == node.id


# ---------------------------------------------------------------------------
# 3. dispatch_all(plan)
# ---------------------------------------------------------------------------


def test_dispatch_all_returns_list() -> None:
    """dispatch_all must return a list. # @trace WL-082"""
    bus = _make_bus()
    plan = _make_plan()
    dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
    result = dispatcher.dispatch_all(plan)
    assert isinstance(result, list)


def test_dispatch_all_empty_plan_returns_empty_list() -> None:
    """dispatch_all on a plan with no nodes returns []. # @trace WL-082"""
    bus = _make_bus()
    plan = _make_plan()
    dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
    result = dispatcher.dispatch_all(plan)
    assert result == []


def test_dispatch_all_single_node_returns_one_id() -> None:
    """dispatch_all on a single-node plan returns a list with one message id. # @trace WL-082"""
    bus = _make_bus()
    plan = _make_plan()
    plan.add_task("solo task", agent_hint="worker")
    dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
    result = dispatcher.dispatch_all(plan)
    assert len(result) == 1
    assert isinstance(result[0], str)


def test_dispatch_all_returns_id_per_node() -> None:
    """dispatch_all must return one id per node in the plan. # @trace WL-082"""
    bus = _make_bus()
    plan = _make_plan()
    plan.add_task("task 1", agent_hint="worker")
    plan.add_task("task 2", agent_hint="worker")
    plan.add_task("task 3", agent_hint="worker")
    dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
    result = dispatcher.dispatch_all(plan)
    assert len(result) == 3


def test_dispatch_all_ids_are_unique() -> None:
    """All ids returned by dispatch_all must be unique. # @trace WL-082"""
    bus = _make_bus()
    plan = _make_plan()
    for i in range(5):
        plan.add_task(f"task {i}", agent_hint="worker")
    dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
    result = dispatcher.dispatch_all(plan)
    assert len(result) == len(set(result))


def test_dispatch_all_linear_chain_respects_order() -> None:
    """In a linear chain A->B->C, A must be dispatched before B, B before C. # @trace WL-082"""
    bus = _make_bus()
    plan = _make_plan()
    node_a = plan.add_task("task A", agent_hint="worker")
    node_b = plan.add_task("task B", agent_hint="worker", depends_on=[node_a.id])
    plan.add_task("task C", agent_hint="worker", depends_on=[node_b.id])
    dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
    ids = dispatcher.dispatch_all(plan)
    # All 3 nodes dispatched
    assert len(ids) == 3
    # Verify by draining and checking order
    messages = bus.drain("worker")
    tasks_in_order = [m.payload["task"] for m in messages]
    assert tasks_in_order.index("task A") < tasks_in_order.index("task B")
    assert tasks_in_order.index("task B") < tasks_in_order.index("task C")


def test_dispatch_all_diamond_dag() -> None:
    """Diamond DAG (A->B,C->D) must dispatch A first and D last. # @trace WL-082"""
    bus = _make_bus()
    plan = _make_plan()
    node_a = plan.add_task("task A", agent_hint="worker")
    node_b = plan.add_task("task B", agent_hint="worker", depends_on=[node_a.id])
    node_c = plan.add_task("task C", agent_hint="worker", depends_on=[node_a.id])
    plan.add_task("task D", agent_hint="worker", depends_on=[node_b.id, node_c.id])
    dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
    ids = dispatcher.dispatch_all(plan)
    assert len(ids) == 4
    messages = bus.drain("worker")
    tasks = [m.payload["task"] for m in messages]
    assert tasks.index("task A") < tasks.index("task B")
    assert tasks.index("task A") < tasks.index("task C")
    assert tasks.index("task B") < tasks.index("task D")
    assert tasks.index("task C") < tasks.index("task D")


def test_dispatch_all_multiple_independent_roots() -> None:
    """Plans with multiple independent roots dispatch all roots before their children. # @trace WL-082"""
    bus = _make_bus()
    plan = _make_plan()
    root1 = plan.add_task("root 1", agent_hint="worker")
    root2 = plan.add_task("root 2", agent_hint="worker")
    plan.add_task("child", agent_hint="worker", depends_on=[root1.id, root2.id])
    dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
    ids = dispatcher.dispatch_all(plan)
    assert len(ids) == 3
    messages = bus.drain("worker")
    tasks = [m.payload["task"] for m in messages]
    assert tasks.index("root 1") < tasks.index("child")
    assert tasks.index("root 2") < tasks.index("child")


def test_dispatch_all_parallel_leaves_both_dispatched() -> None:
    """Plan with two parallel leaves after one root dispatches all three. # @trace WL-082"""
    bus = _make_bus()
    plan = _make_plan()
    root = plan.add_task("root", agent_hint="worker")
    plan.add_task("leaf 1", agent_hint="worker", depends_on=[root.id])
    plan.add_task("leaf 2", agent_hint="worker", depends_on=[root.id])
    dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
    ids = dispatcher.dispatch_all(plan)
    assert len(ids) == 3
    messages = bus.drain("worker")
    assert len(messages) == 3


# ---------------------------------------------------------------------------
# 4. collect_results(agent_id, timeout_s)
# ---------------------------------------------------------------------------


def test_collect_results_returns_list() -> None:
    """collect_results must return a list. # @trace WL-082"""
    bus = _make_bus()
    plan = _make_plan()
    dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
    bus.subscribe("collector")
    result = dispatcher.collect_results("collector")
    assert isinstance(result, list)


def test_collect_results_empty_queue_returns_empty_list() -> None:
    """collect_results with empty queue returns []. # @trace WL-082"""
    bus = _make_bus()
    plan = _make_plan()
    dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
    bus.subscribe("empty-agent")
    result = dispatcher.collect_results("empty-agent")
    assert result == []


def test_collect_results_returns_queued_messages() -> None:
    """collect_results drains all queued messages for the agent. # @trace WL-082"""
    bus = _make_bus()
    plan = _make_plan()
    dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
    bus.subscribe("collector")
    # Manually publish two messages to collector
    for i in range(2):
        msg = InterAgentMessage(
            sender_id="sender",
            recipient_id="collector",
            message_type="result",
            payload={"index": i},
        )
        bus.publish(msg)
    results = dispatcher.collect_results("collector")
    assert len(results) == 2


def test_collect_results_returns_inter_agent_message_instances() -> None:
    """collect_results must return InterAgentMessage instances. # @trace WL-082"""
    bus = _make_bus()
    plan = _make_plan()
    dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
    bus.subscribe("collector")
    msg = InterAgentMessage(
        sender_id="s",
        recipient_id="collector",
        message_type="result",
        payload={},
    )
    bus.publish(msg)
    results = dispatcher.collect_results("collector")
    assert all(isinstance(r, InterAgentMessage) for r in results)


def test_collect_results_zero_timeout_drains_existing() -> None:
    """collect_results with timeout_s=0.0 still drains synchronously queued messages. # @trace WL-082"""
    bus = _make_bus()
    plan = _make_plan()
    dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
    bus.subscribe("agent-x")
    msg = InterAgentMessage(
        sender_id="s",
        recipient_id="agent-x",
        message_type="status_update",
        payload={"info": "ok"},
    )
    bus.publish(msg)
    results = dispatcher.collect_results("agent-x", timeout_s=0.0)
    assert len(results) == 1


def test_collect_results_auto_subscribes_agent() -> None:
    """collect_results must subscribe the agent if not already subscribed. # @trace WL-082"""
    bus = _make_bus()
    plan = _make_plan()
    dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
    # Do NOT pre-subscribe "brand-new"
    result = dispatcher.collect_results("brand-new")
    assert result == []


# ---------------------------------------------------------------------------
# 5. Additional edge-case and integration tests
# ---------------------------------------------------------------------------


def test_dispatch_all_different_agents_routed_correctly() -> None:
    """dispatch_all routes each node to its own agent_hint queue. # @trace WL-082"""
    bus = _make_bus()
    plan = _make_plan()
    plan.add_task("research", agent_hint="researcher")
    plan.add_task("code", agent_hint="coder")
    dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
    dispatcher.dispatch_all(plan)
    research_msgs = bus.drain("researcher")
    coder_msgs = bus.drain("coder")
    assert len(research_msgs) == 1
    assert research_msgs[0].payload["task"] == "research"
    assert len(coder_msgs) == 1
    assert coder_msgs[0].payload["task"] == "code"


def test_dispatch_all_messages_have_plan_correlation_id() -> None:
    """Every message dispatched by dispatch_all must carry the plan's id. # @trace WL-082"""
    bus = _make_bus()
    plan = _make_plan()
    plan.add_task("t1", agent_hint="worker")
    plan.add_task("t2", agent_hint="worker")
    dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
    dispatcher.dispatch_all(plan)
    messages = bus.drain("worker")
    for msg in messages:
        assert msg.correlation_id == plan.id


def test_dispatch_all_sender_id_consistent_across_messages() -> None:
    """All messages from dispatch_all share the same sender_id. # @trace WL-082"""
    bus = _make_bus()
    plan = _make_plan()
    plan.add_task("t1", agent_hint="worker")
    plan.add_task("t2", agent_hint="worker")
    dispatcher = SubAgentDispatcher(bus=bus, plan=plan)
    dispatcher.dispatch_all(plan)
    messages = bus.drain("worker")
    sender_ids = {m.sender_id for m in messages}
    assert len(sender_ids) == 1
    assert next(iter(sender_ids)) == dispatcher.sender_id
