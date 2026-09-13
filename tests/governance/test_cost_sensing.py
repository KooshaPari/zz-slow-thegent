import pytest

from thegent.agents.registry import LearningRegistry
from thegent.cost.aggregators import BudgetAlert, CostCap, CostTracker
from thegent.governance.policy import LearningSession, PolicyManager
from thegent.planning.cost_predictor import CostPredictor
from thegent.planning.selector import ObjectiveSelector, ObjectiveWeights


@pytest.fixture
def cost_cap():
    return CostCap(max_cost=5.0)


@pytest.fixture
def selector():
    return ObjectiveSelector()


@pytest.fixture
def registry():
    return LearningRegistry()


def test_al001_cost_bounding(cost_cap):
    """AL-001: Set cost cap to $5. Attempt a learning action that might exceed it."""
    action_cost = 6.0
    assert not cost_cap.check(action_cost)

    action_cost = 4.0
    assert cost_cap.check(action_cost)


def test_al002_objective_selection(selector):
    """AL-002: Provide objectives: 'Cheapest' vs 'Fastest'."""
    cheapest_profile = ObjectiveWeights(latency=0.1, quality=0.3, cost=0.6)
    fastest_profile = ObjectiveWeights(latency=0.7, quality=0.2, cost=0.1)

    models = [
        {"id": "fast", "latency": 0.1, "quality": 0.9, "cost": 0.5},
        {"id": "cheap", "latency": 0.5, "quality": 0.7, "cost": 0.1},
    ]

    cheapest_selection = selector.select(models, cheapest_profile)
    fastest_selection = selector.select(models, fastest_profile)

    assert cheapest_selection["id"] == "cheap"
    assert fastest_selection["id"] == "fast"


def test_al003_canary_rollback(registry):
    """AL-003: Simulate a canary model failure (e.g., latency > 2s)."""
    registry.register_canary("canary-v1", "baseline-v1")

    # Simulate failure
    registry.record_metric("canary-v1", "latency", 2.5)

    assert registry.should_rollback("canary-v1")
    assert registry.get_active_model() == "baseline-v1"


def test_al004_hitl_promotion_block(registry):
    """AL-004: Attempt to promote a canary model to 'default' without approval."""
    # Attempt promotion without approval (default is require_approval=True)
    result = registry.promote("canary-v1", require_approval=True)
    assert not result


def test_al005_policy_drift():
    """AL-005: Policy changes during a learning session."""
    policy = PolicyManager({"cost_cap": 5.0})
    learning_session = LearningSession(policy)
    learning_session.start()

    assert learning_session.cost_cap == 5.0

    # Change policy mid-session
    policy.update({"cost_cap": 3.0})

    assert learning_session.is_valid()
    assert learning_session.cost_cap == 3.0


def test_al006_feedback_recording(registry):
    """AL-006: Record feedback on a learning action."""
    registry.register_canary("canary-v1", "baseline-v1")

    # Record feedback
    registry.record_feedback(model_id="canary-v1", success=True, quality_score=0.95)

    candidate = registry.get_candidate("canary-v1")
    assert candidate.trust_score > 0
    assert candidate.calibration > 0


def test_realtime_cost_tracking():
    tracker = CostTracker()
    tracker.start_session("s1")
    tracker.record_cost("s1", 0.50)
    tracker.record_cost("s1", 0.25)

    assert tracker.get_session_cost("s1") == 0.75
    assert tracker.is_within_budget("s1", budget=1.0)


def test_budget_alert_threshold():
    alert = BudgetAlert(threshold=0.8)
    alert.set_budget(100.0)

    assert not alert.should_alert(70.0)
    assert alert.should_alert(85.0)


def test_cost_prediction_accuracy():
    predictor = CostPredictor()
    predicted = predictor.predict_cost(model="claude-sonnet-4.5", tokens_estimate=10000, action_type="learning")
    # 10k * 0.015 * 1.2 = 0.18
    assert 0.1 <= predicted <= 1.0
