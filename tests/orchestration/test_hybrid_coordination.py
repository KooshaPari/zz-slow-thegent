"""Tests for HybridCoordinationStrategy (coordination-hybrid-strategy).

@trace FR-ORC-010 -- Adaptive hierarchical/P2P coordination mode selection.
@trace FR-ORC-011 -- HIERARCHICAL routing delegates to coordinator (agents[0]).
@trace FR-ORC-012 -- P2P routing distributes tasks round-robin.
@trace FR-ORC-013 -- ADAPTIVE routing blends modes based on avg_load.
@trace FR-ORC-014 -- Empty agent list raises ValueError.
@trace FR-ORC-015 -- THGENT_HIER_THRESHOLD env var overrides default threshold.
"""

from __future__ import annotations

import pytest

from thegent.coordination.hybrid_coordination import (
    CoordinationMetrics,
    CoordinationMode,
    HybridCoordinationStrategy,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def strategy() -> HybridCoordinationStrategy:
    """Return a HybridCoordinationStrategy with a fixed RNG seed for determinism."""
    return HybridCoordinationStrategy(seed=42)


AGENTS_3 = ["coordinator", "worker-1", "worker-2"]
AGENTS_5 = ["coord", "w1", "w2", "w3", "w4"]


# ---------------------------------------------------------------------------
# Mode selection — HIERARCHICAL branch
# ---------------------------------------------------------------------------


class TestSelectModeHierarchical:
    """select_mode returns HIERARCHICAL in appropriate conditions.

    @trace FR-ORC-010
    """

    def test_small_swarm_low_load(self, strategy):
        """Small swarm (< threshold) with low load → HIERARCHICAL."""
        mode = strategy.select_mode(swarm_size=1, avg_load=0.1)
        assert mode == CoordinationMode.HIERARCHICAL

    def test_small_swarm_medium_load(self, strategy):
        """Small swarm below threshold → HIERARCHICAL regardless of load."""
        mode = strategy.select_mode(swarm_size=4, avg_load=0.5)
        assert mode == CoordinationMode.HIERARCHICAL

    def test_small_swarm_high_load(self, strategy):
        """Small swarm (4 < 5 threshold) with high load → still HIERARCHICAL."""
        mode = strategy.select_mode(swarm_size=4, avg_load=0.9)
        assert mode == CoordinationMode.HIERARCHICAL

    def test_large_swarm_very_low_load(self, strategy):
        """Large swarm but avg_load < 0.3 → HIERARCHICAL."""
        mode = strategy.select_mode(swarm_size=10, avg_load=0.0)
        assert mode == CoordinationMode.HIERARCHICAL

    def test_large_swarm_exactly_low_threshold(self, strategy):
        """avg_load == LOW_LOAD_THRESHOLD (0.3) → HIERARCHICAL (boundary: exclusive above)."""
        # select_mode uses avg_load < 0.3 for HIERARCHICAL, so 0.3 is NOT hierarchical
        # when swarm_size >= threshold. Should be ADAPTIVE.
        mode = strategy.select_mode(swarm_size=10, avg_load=0.3)
        # 0.3 is NOT < 0.3, and 0.3 is NOT >= 0.7, so → ADAPTIVE
        assert mode == CoordinationMode.ADAPTIVE

    def test_threshold_boundary_below(self, strategy):
        """swarm_size == threshold - 1 → HIERARCHICAL."""
        mode = strategy.select_mode(swarm_size=4, avg_load=0.8)
        assert mode == CoordinationMode.HIERARCHICAL


# ---------------------------------------------------------------------------
# Mode selection — P2P branch
# ---------------------------------------------------------------------------


class TestSelectModeP2P:
    """select_mode returns P2P when swarm is large AND load is high.

    @trace FR-ORC-010
    """

    def test_large_swarm_high_load(self, strategy):
        """swarm_size >= threshold AND avg_load >= 0.7 → P2P."""
        mode = strategy.select_mode(swarm_size=5, avg_load=0.7)
        assert mode == CoordinationMode.P2P

    def test_large_swarm_max_load(self, strategy):
        """swarm_size >> threshold AND avg_load == 1.0 → P2P."""
        mode = strategy.select_mode(swarm_size=100, avg_load=1.0)
        assert mode == CoordinationMode.P2P

    def test_exactly_threshold_high_load(self, strategy):
        """swarm_size exactly at threshold with high load → P2P."""
        mode = strategy.select_mode(swarm_size=5, avg_load=0.8)
        assert mode == CoordinationMode.P2P

    def test_p2p_not_selected_when_small_swarm(self, strategy):
        """P2P never selected when swarm_size < threshold, even at max load."""
        mode = strategy.select_mode(swarm_size=4, avg_load=1.0)
        assert mode == CoordinationMode.HIERARCHICAL


# ---------------------------------------------------------------------------
# Mode selection — ADAPTIVE branch
# ---------------------------------------------------------------------------


class TestSelectModeAdaptive:
    """select_mode returns ADAPTIVE in the mid-load range.

    @trace FR-ORC-010
    """

    def test_mid_load_large_swarm(self, strategy):
        """avg_load in [0.3, 0.7) with large swarm → ADAPTIVE."""
        mode = strategy.select_mode(swarm_size=6, avg_load=0.5)
        assert mode == CoordinationMode.ADAPTIVE

    def test_just_above_low_threshold(self, strategy):
        """avg_load just above 0.3 → ADAPTIVE."""
        mode = strategy.select_mode(swarm_size=5, avg_load=0.31)
        assert mode == CoordinationMode.ADAPTIVE

    def test_just_below_high_threshold(self, strategy):
        """avg_load just below 0.7 → ADAPTIVE."""
        mode = strategy.select_mode(swarm_size=8, avg_load=0.69)
        assert mode == CoordinationMode.ADAPTIVE


# ---------------------------------------------------------------------------
# Env override for threshold
# ---------------------------------------------------------------------------


class TestHierThresholdEnvOverride:
    """THGENT_HIER_THRESHOLD env var changes the mode boundary.

    @trace FR-ORC-015
    """

    def test_env_threshold_smaller(self, monkeypatch, strategy):
        """Setting THGENT_HIER_THRESHOLD=2 makes swarm_size=2 route P2P at high load."""
        monkeypatch.setenv("THGENT_HIER_THRESHOLD", "2")
        mode = strategy.select_mode(swarm_size=2, avg_load=0.9)
        assert mode == CoordinationMode.P2P

    def test_env_threshold_larger(self, monkeypatch, strategy):
        """Setting THGENT_HIER_THRESHOLD=10 keeps swarm_size=5 as HIERARCHICAL."""
        monkeypatch.setenv("THGENT_HIER_THRESHOLD", "10")
        mode = strategy.select_mode(swarm_size=5, avg_load=0.9)
        assert mode == CoordinationMode.HIERARCHICAL

    def test_env_threshold_invalid_falls_back(self, monkeypatch, strategy):
        """Invalid env value falls back to default (5)."""
        monkeypatch.setenv("THGENT_HIER_THRESHOLD", "not-a-number")
        mode = strategy.select_mode(swarm_size=4, avg_load=0.9)
        # With default threshold=5, swarm_size=4 < 5 → HIERARCHICAL
        assert mode == CoordinationMode.HIERARCHICAL

    def test_env_threshold_zero_falls_back(self, monkeypatch, strategy):
        """Threshold < 1 falls back to default."""
        monkeypatch.setenv("THGENT_HIER_THRESHOLD", "0")
        mode = strategy.select_mode(swarm_size=4, avg_load=0.9)
        assert mode == CoordinationMode.HIERARCHICAL

    def test_env_threshold_negative_falls_back(self, monkeypatch, strategy):
        """Negative threshold falls back to default."""
        monkeypatch.setenv("THGENT_HIER_THRESHOLD", "-3")
        mode = strategy.select_mode(swarm_size=4, avg_load=0.9)
        assert mode == CoordinationMode.HIERARCHICAL


# ---------------------------------------------------------------------------
# HIERARCHICAL routing
# ---------------------------------------------------------------------------


class TestRoutingHierarchical:
    """HIERARCHICAL mode always routes to agents[0].

    @trace FR-ORC-011
    """

    def test_single_agent(self, strategy):
        """Single-agent list returns that agent."""
        agent = strategy.route_task("t1", ["solo"], CoordinationMode.HIERARCHICAL)
        assert agent == "solo"

    def test_coordinator_is_first(self, strategy):
        """First agent in list is always chosen."""
        agent = strategy.route_task("t2", AGENTS_3, CoordinationMode.HIERARCHICAL)
        assert agent == "coordinator"

    def test_coordinator_repeated(self, strategy):
        """Multiple calls all return agents[0]."""
        for _ in range(10):
            agent = strategy.route_task("t", AGENTS_5, CoordinationMode.HIERARCHICAL)
            assert agent == "coord"


# ---------------------------------------------------------------------------
# P2P routing (round-robin)
# ---------------------------------------------------------------------------


class TestRoutingP2P:
    """P2P mode distributes tasks round-robin.

    @trace FR-ORC-012
    """

    def test_round_robin_order(self):
        """Tasks cycle through agents in order."""
        s = HybridCoordinationStrategy(seed=0)
        agents = ["a0", "a1", "a2"]
        results = [
            s.route_task(f"t{i}", agents, CoordinationMode.P2P) for i in range(6)
        ]
        assert results == ["a0", "a1", "a2", "a0", "a1", "a2"]

    def test_single_agent_round_robin(self):
        """Single-agent P2P always returns that agent."""
        s = HybridCoordinationStrategy()
        for i in range(5):
            assert s.route_task(f"t{i}", ["only"], CoordinationMode.P2P) == "only"

    def test_all_agents_covered_evenly(self):
        """Each agent receives the same number of tasks over a full cycle."""
        s = HybridCoordinationStrategy()
        agents = ["x", "y", "z"]
        counts: dict[str, int] = dict.fromkeys(agents, 0)
        for i in range(30):
            chosen = s.route_task(f"task-{i}", agents, CoordinationMode.P2P)
            counts[chosen] += 1
        assert all(v == 10 for v in counts.values())

    def test_rr_counter_advances_across_calls(self):
        """The round-robin counter advances independently of mode arguments."""
        s = HybridCoordinationStrategy()
        agents = ["a", "b"]
        a0 = s.route_task("t0", agents, CoordinationMode.P2P)
        a1 = s.route_task("t1", agents, CoordinationMode.P2P)
        assert a0 != a1


# ---------------------------------------------------------------------------
# ADAPTIVE routing
# ---------------------------------------------------------------------------


class TestRoutingAdaptive:
    """ADAPTIVE mode blends hierarchical and P2P routing.

    @trace FR-ORC-013
    """

    def test_low_avg_load_favors_hierarchical(self):
        """Low avg_load (just above 0.3) should favour coordinator routing."""
        s = HybridCoordinationStrategy(seed=0)
        agents = ["coord", "w1", "w2"]
        # avg_load=0.31 → p2p_weight close to 0 → mostly coordinator
        results = [
            s.route_task(f"t{i}", agents, CoordinationMode.ADAPTIVE, avg_load=0.31)
            for i in range(20)
        ]
        coordinator_count = results.count("coord")
        # Should be the majority; with seed=0 and near-zero weight the rng
        # will rarely produce p2p choices.
        assert coordinator_count >= 15

    def test_high_avg_load_favors_p2p(self):
        """High avg_load (just below 0.7) should predominantly route via P2P round-robin.

        With avg_load=0.69, p2p_weight ≈ 0.975 so ~97.5% of decisions go to P2P.
        In P2P mode all agents share equally; in HIERARCHICAL only agents[0] is chosen.
        We verify that the non-coord agents (w1, w2) collectively receive roughly
        2/3 of P2P choices — i.e. they are present in more than half the results.
        """
        s = HybridCoordinationStrategy(seed=0)
        agents = ["coord", "w1", "w2"]
        results = [
            s.route_task(f"t{i}", agents, CoordinationMode.ADAPTIVE, avg_load=0.69)
            for i in range(100)
        ]
        non_coord_count = sum(1 for r in results if r != "coord")
        # In pure P2P all agents share equally (≈33% each), so non-coord ≈ 66%.
        # With p2p_weight≈0.975 the distribution should still be mostly P2P-style.
        # Non-coord agents should appear in well over half the results.
        assert non_coord_count >= 50

    def test_mid_avg_load_produces_both(self):
        """avg_load=0.5 should produce a mix of hierarchical and P2P choices."""
        s = HybridCoordinationStrategy(seed=99)
        agents = ["coord", "w1", "w2"]
        results = [
            s.route_task(f"t{i}", agents, CoordinationMode.ADAPTIVE, avg_load=0.5)
            for i in range(40)
        ]
        coordinator_count = results.count("coord")
        non_coord_count = len(results) - coordinator_count
        # Both should appear
        assert coordinator_count > 0
        assert non_coord_count > 0


# ---------------------------------------------------------------------------
# Empty agent list
# ---------------------------------------------------------------------------


class TestEmptyAgentList:
    """route_task raises ValueError when agents list is empty.

    @trace FR-ORC-014
    """

    @pytest.mark.parametrize("mode", list(CoordinationMode))
    def test_empty_agents_raises(self, strategy, mode):
        """Every mode raises ValueError on empty agent list."""
        with pytest.raises(ValueError, match="empty"):
            strategy.route_task("task-x", [], mode)


# ---------------------------------------------------------------------------
# CoordinationMetrics dataclass
# ---------------------------------------------------------------------------


class TestCoordinationMetrics:
    """CoordinationMetrics dataclass stores all fields correctly."""

    def test_fields_set_correctly(self):
        """All four fields are stored and accessible."""
        metrics = CoordinationMetrics(
            mode=CoordinationMode.P2P,
            swarm_size=10,
            avg_load=0.75,
            routed_to="worker-3",
        )
        assert metrics.mode == CoordinationMode.P2P
        assert metrics.swarm_size == 10
        assert metrics.avg_load == pytest.approx(0.75)
        assert metrics.routed_to == "worker-3"


# ---------------------------------------------------------------------------
# Convenience coordinate() method
# ---------------------------------------------------------------------------


class TestCoordinate:
    """HybridCoordinationStrategy.coordinate() integrates select + route."""

    def test_returns_metrics(self, strategy):
        """coordinate() returns a CoordinationMetrics instance."""
        result = strategy.coordinate("task-1", AGENTS_3, swarm_size=3, avg_load=0.1)
        assert isinstance(result, CoordinationMetrics)

    def test_hierarchical_metrics(self, strategy):
        """Small swarm → HIERARCHICAL; routed_to is coordinator."""
        result = strategy.coordinate("task-2", AGENTS_3, swarm_size=3, avg_load=0.1)
        assert result.mode == CoordinationMode.HIERARCHICAL
        assert result.routed_to == AGENTS_3[0]
        assert result.swarm_size == 3
        assert result.avg_load == pytest.approx(0.1)

    def test_p2p_metrics(self, strategy):
        """Large swarm + high load → P2P; routed_to is one of the agents."""
        result = strategy.coordinate("task-3", AGENTS_5, swarm_size=10, avg_load=0.9)
        assert result.mode == CoordinationMode.P2P
        assert result.routed_to in AGENTS_5

    def test_empty_agents_raises_via_coordinate(self, strategy):
        """coordinate() propagates ValueError from route_task."""
        with pytest.raises(ValueError, match="empty"):
            strategy.coordinate("t", [], swarm_size=0, avg_load=0.0)


# ---------------------------------------------------------------------------
# __init__ exports
# ---------------------------------------------------------------------------


def test_init_exports():
    """CoordinationMode, HybridCoordinationStrategy, CoordinationMetrics exported from __init__."""
    from thegent.orchestration import (
        CoordinationMetrics,
        CoordinationMode,
        HybridCoordinationStrategy,
    )

    assert CoordinationMode is not None
    assert HybridCoordinationStrategy is not None
    assert CoordinationMetrics is not None
