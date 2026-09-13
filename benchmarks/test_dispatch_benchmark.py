"""Benchmark tests for hierarchical agent dispatcher.

Run with: pytest benchmarks/test_dispatch_benchmark.py --benchmark-only
"""

import time

import pytest

from thegent.orchestration.hierarchical_dispatcher import (
    AgentLifecycleState,
    HierarchicalAgent,
    HierarchicalAgentRegistry,
    reset_global_registry,
)


@pytest.fixture(autouse=True)
def reset_registry():
    """Reset global registry before and after each test."""
    reset_global_registry()
    yield
    reset_global_registry()


class TestDispatchBenchmark:
    """Benchmarks for hierarchical dispatch performance."""

    @pytest.mark.benchmark
    def test_registry_registration_benchmark(self, benchmark):
        """Benchmark agent registration speed."""
        registry = HierarchicalAgentRegistry(system_cap=10000, session_cap=5000)

        def register_1000():
            for i in range(1000):
                agent = HierarchicalAgent(
                    agent_id=f"agent-{i}",
                    session_id="session-1",
                    depth=i % 3,
                )
                registry.register_agent(agent)
            return len(registry._agents)

        result = benchmark.pedantic(register_1000, rounds=5, iterations=1)
        assert result == 1000

    @pytest.mark.benchmark
    def test_registry_update_benchmark(self, benchmark):
        """Benchmark state update speed."""
        registry = HierarchicalAgentRegistry(system_cap=10000, session_cap=5000)

        # Pre-register 1000 agents
        for i in range(1000):
            agent = HierarchicalAgent(
                agent_id=f"agent-{i}",
                session_id="session-1",
                depth=i % 3,
            )
            registry.register_agent(agent)

        def update_1000():
            for i in range(1000):
                registry.update_agent_state(
                    f"agent-{i}",
                    AgentLifecycleState.FINISHED,
                    result=f"Result {i}",
                )

        benchmark.pedantic(update_1000, rounds=5, iterations=1)

    @pytest.mark.benchmark
    def test_registry_prune_benchmark(self, benchmark):
        """Benchmark pruning speed."""
        registry = HierarchicalAgentRegistry(system_cap=10000, session_cap=5000)

        def setup_prune_test():
            reset_global_registry()
            # Create 1000 agents, half stale
            for i in range(1000):
                agent = HierarchicalAgent(
                    agent_id=f"agent-{i}",
                    session_id="session-1",
                    depth=i % 3,
                    state=AgentLifecycleState.FINISHED,
                    last_heartbeat=time.time() - 1000 if i < 500 else time.time(),
                )
                registry.register_agent(agent)

        def prune():
            return registry.prune_finished_stale()

        result = benchmark.pedantic(prune, setup=setup_prune_test, rounds=5, iterations=1)
        assert result >= 500  # At least half should be pruned

    @pytest.mark.benchmark
    def test_get_descendants_benchmark(self, benchmark):
        """Benchmark descendants retrieval."""
        registry = HierarchicalAgentRegistry(system_cap=10000, session_cap=5000)

        # Create a tree with 3 levels
        root = HierarchicalAgent(agent_id="root", session_id="s1", depth=0)
        registry.register_agent(root)

        # 10 children per parent, 3 levels = 1110 agents
        for i in range(10):
            child = HierarchicalAgent(
                agent_id=f"child-{i}",
                session_id="s1",
                parent_id="root",
                depth=1,
            )
            registry.register_agent(child)

            for j in range(10):
                grandchild = HierarchicalAgent(
                    agent_id=f"grandchild-{i}-{j}",
                    session_id="s1",
                    parent_id=f"child-{i}",
                    depth=2,
                )
                registry.register_agent(grandchild)

        def get_descendants():
            return registry.get_descendants("root")

        result = benchmark(get_descendants)
        assert len(result) == 110  # 10 children + 100 grandchildren

    @pytest.mark.benchmark
    def test_system_stats_benchmark(self, benchmark):
        """Benchmark stats calculation."""
        registry = HierarchicalAgentRegistry(system_cap=10000, session_cap=5000)

        # Register 1000 agents across 10 sessions
        for s in range(10):
            for i in range(100):
                agent = HierarchicalAgent(
                    agent_id=f"agent-s{s}-{i}",
                    session_id=f"session-{s}",
                    depth=i % 3,
                    state=AgentLifecycleState.RUNNING if i % 2 == 0 else AgentLifecycleState.FINISHED,
                )
                registry.register_agent(agent)

        def get_stats():
            return registry.get_system_stats()

        result = benchmark(get_stats)
        assert result["total_active"] == 1000


# Benchmark configuration
def pytest_configure(config):
    """Configure benchmark settings."""
    config.addinivalue_line("markers", "benchmark: mark test as a benchmark")
