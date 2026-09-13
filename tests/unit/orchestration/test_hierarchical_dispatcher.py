"""Tests for HierarchicalDispatcher L^N agent dispatch.

# @trace WL-138
"""

import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from thegent.orchestration.hierarchical_dispatcher import (
    MAX_HIERARCHY_DEPTH,
    AgentCapExceededError,
    AgentLifecycleState,
    HierarchicalAgent,
    HierarchicalAgentRegistry,
    HierarchicalDispatcher,
    HierarchicalDispatchRequest,
    MaxDepthExceededError,
    SessionAgentRegistry,
    get_global_registry,
    reset_global_registry,
)


@pytest.fixture(autouse=True)
def reset_registry():
    """Reset global registry before and after each test."""
    reset_global_registry()
    yield
    reset_global_registry()


@pytest.fixture
def registry():
    """Create a fresh registry for testing."""
    return HierarchicalAgentRegistry(system_cap=10, session_cap=5)


@pytest.fixture
def sample_agent():
    """Create a sample agent for testing."""
    return HierarchicalAgent(
        agent_id="agent-001",
        session_id="session-123",
        parent_id=None,
        depth=0,
        state=AgentLifecycleState.RUNNING,
        task_prompt="Test task",
    )


class TestHierarchicalAgent:
    """Tests for HierarchicalAgent dataclass."""

    def test_creation(self):
        """Test basic agent creation."""
        agent = HierarchicalAgent(
            agent_id="test-001",
            session_id="session-001",
        )
        assert agent.agent_id == "test-001"
        assert agent.session_id == "session-001"
        assert agent.state == AgentLifecycleState.PENDING
        assert agent.depth == 0

    def test_update_heartbeat(self, sample_agent):
        """Test heartbeat update."""
        old_heartbeat = sample_agent.last_heartbeat
        time.sleep(0.01)
        sample_agent.update_heartbeat()
        assert sample_agent.last_heartbeat > old_heartbeat

    def test_is_stale(self):
        """Test staleness detection."""
        # Fresh agent
        agent = HierarchicalAgent(
            agent_id="fresh",
            session_id="s1",
            state=AgentLifecycleState.RUNNING,
            last_heartbeat=time.time(),
        )
        assert not agent.is_stale(threshold=1.0)

        # Stale agent
        stale_agent = HierarchicalAgent(
            agent_id="stale",
            session_id="s1",
            state=AgentLifecycleState.RUNNING,
            last_heartbeat=time.time() - 100,
        )
        assert stale_agent.is_stale(threshold=1.0)

        # Finished agent is never stale
        finished_agent = HierarchicalAgent(
            agent_id="finished",
            session_id="s1",
            state=AgentLifecycleState.FINISHED,
            last_heartbeat=time.time() - 100,
        )
        assert not finished_agent.is_stale()


class TestSessionAgentRegistry:
    """Tests for session-level agent tracking."""

    def test_active_count(self):
        """Test active agent counting."""
        session = SessionAgentRegistry(session_cap=10)

        session.agents["a1"] = HierarchicalAgent(
            agent_id="a1", session_id="s1", state=AgentLifecycleState.RUNNING
        )
        session.agents["a2"] = HierarchicalAgent(
            agent_id="a2", session_id="s1", state=AgentLifecycleState.COMPLETED
        )
        session.agents["a3"] = HierarchicalAgent(
            agent_id="a3", session_id="s1", state=AgentLifecycleState.PRUNED
        )

        assert session.active_count() == 2  # RUNNING + COMPLETED
        assert session.running_count() == 1

    def test_can_spawn(self):
        """Test spawn capacity check."""
        session = SessionAgentRegistry(session_cap=10)
        # Use a smaller local cap for testing
        # SESSION_AGENT_CAP is 50, but we test the logic works
        for i in range(3):
            assert session.can_spawn()
            session.agents[f"a{i}"] = HierarchicalAgent(
                agent_id=f"a{i}",
                session_id="s1",
                state=AgentLifecycleState.RUNNING,
            )


class TestHierarchicalAgentRegistry:
    """Tests for the global agent registry."""

    def test_register_agent(self, registry):
        """Test agent registration."""
        agent = HierarchicalAgent(
            agent_id="a1",
            session_id="s1",
            depth=0,
        )
        registry.register_agent(agent)

        assert registry.get_agent("a1") == agent
        assert registry.total_active_count() == 1

    def test_register_with_parent(self, registry):
        """Test hierarchical parent-child registration."""
        parent = HierarchicalAgent(
            agent_id="parent",
            session_id="s1",
            depth=0,
        )
        registry.register_agent(parent)

        child = HierarchicalAgent(
            agent_id="child",
            session_id="s1",
            parent_id="parent",
            depth=1,
        )
        registry.register_agent(child)

        # Check parent has child
        assert "child" in registry.get_agent("parent").children

        # Check get_children works
        children = registry.get_children("parent")
        assert len(children) == 1
        assert children[0].agent_id == "child"

    def test_system_cap_enforcement(self):
        """Test system-wide agent cap."""
        registry = HierarchicalAgentRegistry(system_cap=3)

        # Register 3 agents
        for i in range(3):
            registry.register_agent(
                HierarchicalAgent(
                    agent_id=f"a{i}",
                    session_id="s1",
                )
            )

        # 4th should fail
        with pytest.raises(AgentCapExceededError) as exc_info:
            registry.register_agent(
                HierarchicalAgent(
                    agent_id="a3_dup",
                    session_id="s1",
                )
            )
        assert "System agent cap" in str(exc_info.value)

    def test_session_cap_enforcement(self):
        """Test per-session agent cap."""
        registry = HierarchicalAgentRegistry(system_cap=100, session_cap=2)

        # Register 2 agents in session
        for i in range(2):
            registry.register_agent(
                HierarchicalAgent(
                    agent_id=f"s1-a{i}",
                    session_id="s1",
                )
            )

        # 3rd in same session should fail
        with pytest.raises(AgentCapExceededError) as exc_info:
            registry.register_agent(
                HierarchicalAgent(
                    agent_id="s1-a2",
                    session_id="s1",
                )
            )
        assert "Session agent cap" in str(exc_info.value)

        # But different session should work
        registry.register_agent(
            HierarchicalAgent(
                agent_id="s2-a0",
                session_id="s2",
            )
        )
        assert registry.total_active_count() == 3

    def test_prune_finished_stale(self, registry):
        """Test pruning of finished and stale agents."""
        running = HierarchicalAgent(
            agent_id="running",
            session_id="s1",
            state=AgentLifecycleState.RUNNING,
            last_heartbeat=time.time(),
        )
        stale = HierarchicalAgent(
            agent_id="stale",
            session_id="s1",
            state=AgentLifecycleState.RUNNING,
            last_heartbeat=time.time() - 1000,
        )
        old_finished = HierarchicalAgent(
            agent_id="old_finished",
            session_id="s1",
            state=AgentLifecycleState.COMPLETED,
            last_heartbeat=time.time() - 1000,
        )
        new_finished = HierarchicalAgent(
            agent_id="new_finished",
            session_id="s1",
            state=AgentLifecycleState.COMPLETED,
            last_heartbeat=time.time(),
        )

        for a in [running, stale, old_finished, new_finished]:
            registry.register_agent(a)

        pruned_count = registry.prune_finished_stale()

        assert pruned_count == 2  # stale (marked PRUNED) and old_finished (removed)
        assert registry.get_agent("running").state == AgentLifecycleState.RUNNING
        assert registry.get_agent("stale").state == AgentLifecycleState.PRUNED
        assert registry.get_agent("old_finished") is None  # Removed

    def test_get_descendants(self, registry):
        """Test getting all descendants."""
        root = HierarchicalAgent(agent_id="root", session_id="s1", depth=0)
        registry.register_agent(root)

        child1 = HierarchicalAgent(
            agent_id="child1", session_id="s1", parent_id="root", depth=1
        )
        child2 = HierarchicalAgent(
            agent_id="child2", session_id="s1", parent_id="root", depth=1
        )
        registry.register_agent(child1)
        registry.register_agent(child2)

        grandchild = HierarchicalAgent(
            agent_id="grandchild", session_id="s1", parent_id="child1", depth=2
        )
        registry.register_agent(grandchild)

        descendants = registry.get_descendants("root")
        assert len(descendants) == 3
        assert {d.agent_id for d in descendants} == {"child1", "child2", "grandchild"}


class TestHierarchicalDispatcher:
    """Tests for the hierarchical dispatcher."""

    @pytest.mark.asyncio
    async def test_dispatch_root_agent(self, registry):
        """Test dispatching a root-level agent."""
        mock_base = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.output = "Task completed"
        mock_result.error = None
        mock_base.dispatch = AsyncMock(return_value=mock_result)

        mock_cap_index = MagicMock()

        dispatcher = HierarchicalDispatcher(
            capability_index=mock_cap_index,
            registry=registry,
            base_dispatcher=mock_base,
        )

        request = HierarchicalDispatchRequest(
            prompt="Test task",
            session_id="s1",
        )

        result = await dispatcher.dispatch_hierarchical(request)

        assert (
            result.state == AgentLifecycleState.PENDING
        )  # Dispatch creates agent in PENDING
        assert result.depth == 0
        assert result.task_prompt == "Test task"
        assert registry.total_active_count() == 1

    @pytest.mark.asyncio
    async def test_max_depth_enforcement(self, registry):
        """Test that depth limit is enforced based on request depth."""
        dispatcher = HierarchicalDispatcher(
            capability_index=MagicMock(),
            registry=registry,
            base_dispatcher=MagicMock(),
        )

        # Test that depth >= MAX_HIERARCHY_DEPTH raises error
        request = HierarchicalDispatchRequest(
            prompt="Too deep",
            session_id="s1",
            depth=MAX_HIERARCHY_DEPTH,  # At the limit
        )

        with pytest.raises(MaxDepthExceededError):
            await dispatcher.dispatch_hierarchical(request)

    def test_can_spawn_child(self, registry):
        """Test spawn child capability check."""
        running = HierarchicalAgent(
            agent_id="running",
            session_id="s1",
            depth=0,
            state=AgentLifecycleState.RUNNING,
        )
        registry.register_agent(running)

        dispatcher = HierarchicalDispatcher(
            capability_index=MagicMock(),
            registry=registry,
            base_dispatcher=MagicMock(),
        )

        assert dispatcher.can_spawn_child("running") is True

        at_max = HierarchicalAgent(
            agent_id="at_max",
            session_id="s1",
            depth=MAX_HIERARCHY_DEPTH,
            state=AgentLifecycleState.RUNNING,
        )
        registry.register_agent(at_max)
        assert dispatcher.can_spawn_child("at_max") is False

    def test_get_agent_tree(self, registry):
        """Test getting agent tree structure."""
        root = HierarchicalAgent(agent_id="root", session_id="s1", depth=0)
        child1 = HierarchicalAgent(
            agent_id="child1", session_id="s1", parent_id="root", depth=1
        )
        child2 = HierarchicalAgent(
            agent_id="child2", session_id="s1", parent_id="root", depth=1
        )
        registry.register_agent(root)
        registry.register_agent(child1)
        registry.register_agent(child2)

        dispatcher = HierarchicalDispatcher(
            capability_index=MagicMock(),
            registry=registry,
            base_dispatcher=MagicMock(),
        )

        tree = dispatcher.get_agent_tree("root")

        assert tree["agent_id"] == "root"
        assert len(tree["children"]) == 2

    def test_system_stats(self, registry):
        """Test system statistics."""
        for i in range(3):
            registry.register_agent(
                HierarchicalAgent(
                    agent_id=f"a{i}",
                    session_id="s1",
                    depth=i % 3,
                )
            )

        stats = registry.get_system_stats()

        assert stats["total_active"] == 3
        assert stats["system_cap"] == 10
        assert stats["session_cap"] == 5


class TestGlobalRegistry:
    """Tests for global registry singleton."""

    def test_singleton(self):
        """Test that get_global_registry returns same instance."""
        r1 = get_global_registry()
        r2 = get_global_registry()
        assert r1 is r2

    def test_reset(self):
        """Test that reset clears the registry."""
        r1 = get_global_registry()
        r1.register_agent(HierarchicalAgent(agent_id="test", session_id="s1"))
        assert r1.total_active_count() == 1
        reset_global_registry()
        assert r1.total_active_count() == 0
