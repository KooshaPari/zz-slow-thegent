"""Unit tests for Recursive Reward Model (WP-39003)."""

import pytest

from thegent.agents.reward_model import RecursiveRewardModel


class TestRecursiveRewardModel:
    """Test RecursiveRewardModel functionality (WP-39003)."""

    @pytest.fixture
    def model(self):
        """Create a RecursiveRewardModel instance."""
        return RecursiveRewardModel()

    def test_initialization(self, model):
        """Test model initialization."""
        assert model._optimization_epoch == 0
        assert len(model._reward_history) == 0

    def test_record_reward(self, model):
        """Test recording a reward signal."""
        model.record_reward(
            agent_id="agent-1",
            task_id="task-1",
            reward_value=0.85,
            metadata={"source": "test"},
        )

        assert len(model._reward_history) == 1
        signal = model._reward_history[0]
        assert signal.agent_id == "agent-1"
        assert signal.task_id == "task-1"
        assert signal.reward_value == 0.85
        assert signal.metadata == {"source": "test"}

    def test_record_multiple_rewards(self, model):
        """Test recording multiple rewards."""
        model.record_reward("agent-1", "task-1", 0.8)
        model.record_reward("agent-2", "task-2", 0.9)
        model.record_reward("agent-1", "task-3", 0.75)

        assert len(model._reward_history) == 3

    def test_optimize_with_no_data(self, model):
        """Test optimization with no reward data."""
        result = model.optimize()
        assert result["status"] == "no_data"
        assert result["epoch"] == 0  # No optimization occurred, epoch starts at 0

    def test_optimize_with_data(self, model):
        """Test optimization with reward data."""
        model.record_reward("agent-1", "task-1", 0.8)
        model.record_reward("agent-2", "task-2", 0.9)
        model.record_reward("agent-1", "task-3", 0.7)

        result = model.optimize()

        assert result["status"] == "optimized"
        assert result["epoch"] == 1
        assert result["avg_reward"] == pytest.approx(0.8, abs=0.01)
        assert result["total_signals"] == 3
        assert result["agent_count"] == 2

    def test_get_reward_statistics_empty(self, model):
        """Test getting statistics with no rewards."""
        stats = model.get_reward_statistics()
        assert stats["total"] == 0
        assert stats["average"] == 0.0

    def test_get_reward_statistics_with_data(self, model):
        """Test getting statistics with reward data."""
        model.record_reward("agent-1", "task-1", 0.8)
        model.record_reward("agent-2", "task-2", 0.9)
        model.record_reward("agent-1", "task-3", 0.7)

        stats = model.get_reward_statistics()

        assert stats["total"] == 3
        assert stats["average"] == pytest.approx(0.8, abs=0.01)
        assert stats["min"] == 0.7
        assert stats["max"] == 0.9

    def test_optimize_increments_epoch(self, model):
        """Test that optimize increments the epoch counter."""
        model.record_reward("agent-1", "task-1", 0.8)
        assert model._optimization_epoch == 0

        model.optimize()
        assert model._optimization_epoch == 1

        model.optimize()
        assert model._optimization_epoch == 2
