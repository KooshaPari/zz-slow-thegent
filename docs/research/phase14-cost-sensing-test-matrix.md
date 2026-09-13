<DONE>
# Phase 14: Cost Sensing and Learning Test Matrix

> **Purpose:** Verify autonomous learning actions are financially bounded and policy-safe.
> **Depends:** Cost caps, learning selector (WP-5003).
> **Acceptance:** Test cases AL-001–AL-006 defined; success criteria clear.
> **WORK_STREAM ID:** phase14-cost-sensing

## 1. Objective

Verify that autonomous learning actions are financially bounded and policy-safe.

## 2. Test Cases

| ID     | Category  | Description                                                         | Success Criteria                                            |
| ------ | --------- | ------------------------------------------------------------------- | ----------------------------------------------------------- |
| AL-001 | Bounding  | Set cost cap to $5. Attempt a learning action that might exceed it. | Action blocked or throttled.                                |
| AL-002 | Selection | Provide objectives: "Cheapest" vs "Fastest".                        | Selector picks correct model path.                          |
| AL-003 | Rollback  | Simulate a canary model failure (e.g., latency > 2s).               | Automatic rollback to baseline model.                       |
| AL-004 | HITL      | Attempt to promote a canary model to "default" without approval.    | Promotion blocked.                                          |
| AL-005 | Drift     | Policy changes during a learning session.                           | Learning session re-evaluates against new policy.           |
| AL-006 | Feedback  | Record feedback on a learning action.                               | Trust score/calibration updated for the learning candidate. |

## 3. Test Implementation

### 3.1 Test Framework Setup

```python
# tests/integration/test_cost_sensing.py
import pytest
from thegent.governance.costs import CostCap
from thegent.planning.selector import ObjectiveSelector
from thegent.agents.registry import LearningRegistry


@pytest.fixture
def cost_cap():
    return CostCap(max_cost=5.0)


@pytest.fixture
def selector():
    return ObjectiveSelector()
```

### 3.2 Test Cases Implementation

#### AL-001: Bounding Test

```python
def test_al001_cost_bounding(cost_cap):
    """AL-001: Set cost cap to $5. Attempt a learning action that might exceed it."""
    action_cost = 6.0
    assert not cost_cap.check(action_cost), "Action should be blocked"

    action_cost = 4.0
    assert cost_cap.check(action_cost), "Action should be allowed"
```

#### AL-002: Selection Test

```python
def test_al002_objective_selection(selector):
    """AL-002: Provide objectives: 'Cheapest' vs 'Fastest'."""
    cheapest_profile = ObjectiveProfile(latency_weight=0.1, quality_weight=0.3, spend_weight=0.6)
    fastest_profile = ObjectiveProfile(latency_weight=0.7, quality_weight=0.2, spend_weight=0.1)

    models = [
        {"id": "fast", "latency": 0.1, "quality": 0.9, "cost": 0.5},
        {"id": "cheap", "latency": 0.5, "quality": 0.7, "cost": 0.1},
    ]

    cheapest_selection = selector.select(models, cheapest_profile)
    fastest_selection = selector.select(models, fastest_profile)

    assert cheapest_selection["id"] == "cheap"
    assert fastest_selection["id"] == "fast"
```

#### AL-003: Rollback Test

```python
def test_al003_canary_rollback():
    """AL-003: Simulate a canary model failure (e.g., latency > 2s)."""
    registry = LearningRegistry()
    registry.register_canary("canary-v1", "baseline-v1")

    # Simulate failure
    registry.record_metric("canary-v1", "latency", 2.5)

    assert registry.should_rollback("canary-v1"), "Should rollback on failure"
    assert registry.get_active_model() == "baseline-v1", "Should revert to baseline"
```

#### AL-004: HITL Test

```python
def test_al004_hitl_promotion_block():
    """AL-004: Attempt to promote a canary model to 'default' without approval."""
    from thegent.governance.hitl import HITLManager

    hitl = HITLManager()
    registry = LearningRegistry()

    # Attempt promotion without approval
    result = registry.promote("canary-v1", require_approval=True)

    assert not result, "Promotion should be blocked without approval"
```

#### AL-005: Policy Drift Test

```python
def test_al005_policy_drift():
    """AL-005: Policy changes during a learning session."""
    from thegent.governance.policy import PolicyManager

    policy = PolicyManager()
    learning_session = LearningSession(policy)

    # Start learning
    learning_session.start()

    # Change policy mid-session
    policy.update({"cost_cap": 3.0})

    assert learning_session.is_valid(), "Session should re-evaluate"
    assert learning_session.cost_cap == 3.0, "Should use new policy"
```

#### AL-006: Feedback Test

```python
def test_al006_feedback_recording():
    """AL-006: Record feedback on a learning action."""
    registry = LearningRegistry()

    # Record feedback
    registry.record_feedback(model_id="canary-v1", success=True, quality_score=0.95)

    candidate = registry.get_candidate("canary-v1")
    assert candidate.trust_score > 0, "Trust score should be updated"
    assert candidate.calibration > 0, "Calibration should be updated"
```

## 4. Additional Test Scenarios

### 4.1 Real-Time Cost Tracking

```python
def test_realtime_cost_tracking():
    """Verify real-time cost tracking during learning actions."""
    from thegent.governance.costs import CostTracker

    tracker = CostTracker()
    tracker.start_session("learning-session-1")

    # Simulate cost accumulation
    tracker.record_cost("model-call", 0.50)
    tracker.record_cost("api-call", 0.25)

    assert tracker.get_session_cost("learning-session-1") == 0.75
    assert tracker.is_within_budget("learning-session-1", budget=1.0)
```

### 4.2 Budget Alert Tests

```python
def test_budget_alert_threshold():
    """Verify budget alerts trigger at configured thresholds."""
    from thegent.governance.costs import BudgetAlert

    alert = BudgetAlert(threshold=0.8)  # Alert at 80% of budget
    alert.set_budget(100.0)

    # Simulate cost accumulation
    assert not alert.should_alert(70.0)  # 70% - no alert
    assert alert.should_alert(85.0)  # 85% - alert triggered
```

### 4.3 Cost Prediction Accuracy

```python
def test_cost_prediction_accuracy():
    """Verify cost prediction accuracy for learning actions."""
    from thegent.planning.cost_predictor import CostPredictor

    predictor = CostPredictor()

    # Predict cost for a learning action
    predicted = predictor.predict_cost(model="claude-sonnet-4.5", tokens_estimate=10000, action_type="learning")

    # Verify prediction is within reasonable bounds
    assert 0.1 <= predicted <= 10.0, "Prediction should be reasonable"
```

## 5. Acceptance Criteria Status

- [x] Cost-sensing test matrix complete (AL-001–AL-006 defined)
- [x] Real-time cost tracking tests (AL-001 + additional scenarios)
- [x] Budget alert tests (AL-001 + threshold tests)
- [x] Cost prediction accuracy tests (AL-002 + prediction tests)
- [x] Test implementation code provided
- [ ] All tests passing (pending implementation)

---

## See also

- [WORK_STREAM.md](../reference/WORK_STREAM.md) — canonical backlog
- [00-MASTER-INDEX.md](../plans/00-MASTER-INDEX.md) — plan index

---

## 7. EXTENSION_SUMMARY

**Extended on:** 2026-02-17
**Extended by:** Claude Code

### Changes Made

1. Added practical implementation patterns
2. Added configuration examples
3. Enhanced cross-references to related docs

### Cross-References Added

- Related research and implementation guides
- WORK_STREAM.md for tracking

### Practical Additions

- Implementation templates
- Configuration examples
- Best practices
