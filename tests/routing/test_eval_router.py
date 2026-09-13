"""Tests for GW-70: Online eval routing.

# @trace FR-EVAL-070
"""

from __future__ import annotations

import threading

import pytest

from thegent.utils.routing_impl.eval_router import (
    EvalRouter,
    get_eval_router,
    reset_eval_router,
)

pytestmark = pytest.mark.requirement("FR-EVAL-070")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def clean_singleton():
    """Reset the module-level singleton before and after each test."""
    reset_eval_router()
    yield
    reset_eval_router()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_record_and_get_score():
    """Recording an observation means get_score returns that score."""
    router = EvalRouter()
    router.record_eval("gpt-4", "summarize", 0.9)
    score = router.get_score("gpt-4", "summarize")
    assert score == pytest.approx(0.9)


def test_ewma_update():
    """Second observation applies EWMA formula: new = alpha*new + (1-alpha)*old."""
    alpha = 0.3
    router = EvalRouter(alpha=alpha)
    router.record_eval("gpt-4", "summarize", 0.8)
    router.record_eval("gpt-4", "summarize", 0.4)
    expected = alpha * 0.4 + (1 - alpha) * 0.8
    score = router.get_score("gpt-4", "summarize")
    assert score == pytest.approx(expected)


def test_get_score_no_data_returns_none():
    """get_score for an unobserved (model, task_type) returns None."""
    router = EvalRouter()
    assert router.get_score("unknown-model", "classification") is None


def test_route_returns_highest_scored_model():
    """route() returns the model with the highest score for the task type."""
    router = EvalRouter()
    router.record_eval("model-a", "qa", 0.6)
    router.record_eval("model-b", "qa", 0.9)
    result = router.route("qa")
    assert result is not None
    assert result.selected_model == "model-b"
    assert result.score == pytest.approx(0.9)
    assert result.task_type == "qa"


def test_route_no_data_returns_none():
    """route() returns None when no models have been scored for the task type."""
    router = EvalRouter()
    assert router.route("summarize") is None


def test_route_available_models_filter():
    """route() restricts candidates to available_models when provided."""
    router = EvalRouter()
    router.record_eval("model-a", "code", 0.95)
    router.record_eval("model-b", "code", 0.75)
    # model-a has higher score but is not in available_models
    result = router.route("code", available_models=["model-b"])
    assert result is not None
    assert result.selected_model == "model-b"


def test_route_result_all_scores():
    """EvalRouteResult.all_scores contains entries for all competing models."""
    router = EvalRouter()
    router.record_eval("m1", "classify", 0.7)
    router.record_eval("m2", "classify", 0.5)
    router.record_eval("m3", "classify", 0.85)
    result = router.route("classify")
    assert result is not None
    assert set(result.all_scores.keys()) == {"m1", "m2", "m3"}
    assert result.all_scores["m3"] == pytest.approx(0.85)


def test_route_no_overlap_returns_none():
    """route() returns None when available_models has no scored models."""
    router = EvalRouter()
    router.record_eval("model-x", "translate", 0.8)
    result = router.route("translate", available_models=["model-y"])
    assert result is None


def test_list_scores_all():
    """list_scores() returns all recorded EvalScore objects."""
    router = EvalRouter()
    router.record_eval("a", "t1", 0.5)
    router.record_eval("b", "t2", 0.7)
    scores = router.list_scores()
    assert len(scores) == 2
    models = {s.model for s in scores}
    assert models == {"a", "b"}


def test_list_scores_filtered_by_task_type():
    """list_scores(task_type=X) returns only scores for task type X."""
    router = EvalRouter()
    router.record_eval("a", "summarize", 0.5)
    router.record_eval("b", "summarize", 0.7)
    router.record_eval("c", "translate", 0.9)
    scores = router.list_scores(task_type="summarize")
    assert len(scores) == 2
    assert all(s.task_type == "summarize" for s in scores)


def test_reset_clears_all():
    """reset() removes all scores from the router."""
    router = EvalRouter()
    router.record_eval("model-a", "qa", 0.8)
    router.reset()
    assert router.get_score("model-a", "qa") is None
    assert router.list_scores() == []


def test_thread_safety():
    """Concurrent record_eval calls do not corrupt internal state."""
    router = EvalRouter(alpha=0.5)
    n_threads = 20
    n_records = 50
    errors: list = []

    def worker(model_name: str) -> None:
        try:
            for _ in range(n_records):
                router.record_eval(model_name, "load_test", 0.5)
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(f"model-{i}",)) for i in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Thread errors: {errors}"
    scores = router.list_scores(task_type="load_test")
    assert len(scores) == n_threads
    for s in scores:
        assert s.sample_count == n_records


def test_singleton_get_eval_router():
    """get_eval_router() returns the same instance on repeated calls."""
    r1 = get_eval_router()
    r2 = get_eval_router()
    assert r1 is r2


def test_singleton_reset_eval_router():
    """reset_eval_router() causes get_eval_router() to return a new instance."""
    r1 = get_eval_router()
    reset_eval_router()
    r2 = get_eval_router()
    assert r1 is not r2


def test_alpha_default():
    """EvalRouter default alpha is 0.3."""
    router = EvalRouter()
    assert router._alpha == pytest.approx(0.3)


def test_ewma_first_observation_is_raw_score():
    """The very first observation sets EWMA directly to the raw score."""
    router = EvalRouter(alpha=0.5)
    router.record_eval("model-z", "task", 0.42)
    assert router.get_score("model-z", "task") == pytest.approx(0.42)


def test_route_multiple_task_types_isolated():
    """Scores for one task type do not contaminate another task type's routing."""
    router = EvalRouter()
    router.record_eval("model-a", "summarize", 0.9)
    router.record_eval("model-b", "translate", 0.95)
    result = router.route("summarize")
    assert result is not None
    assert result.selected_model == "model-a"


def test_eval_score_sample_count():
    """sample_count increments correctly with each observation."""
    router = EvalRouter()
    for _ in range(5):
        router.record_eval("m", "t", 0.5)
    scores = router.list_scores()
    assert scores[0].sample_count == 5
