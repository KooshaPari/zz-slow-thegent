"""Tests for WL-086: BudgetTracker — Per-Node Token Budget Enforcement.

Covers:
- BudgetExceededError constructor and attributes
- BudgetExceededError message format
- BudgetTracker constructor with OrchestrationPlan
- track(): normal accumulation within budget
- track(): raises BudgetExceededError exactly at budget exceeded
- track(): raises KeyError for unknown node_id
- track(): nodes without budget_tokens metadata are tracked but not enforced
- track(): budget_tokens of wrong type raises TypeError
- track(): multiple incremental calls accumulate correctly
- get_usage(): returns 0 for untracked node
- get_usage(): returns correct cumulative total
- get_usage(): raises KeyError for unknown node_id
- reset_usage(): resets to zero, allows further tracking
- reset_usage(): raises KeyError for unknown node_id
- parse_tokens_from_result(): OpenAI prompt+completion style
- parse_tokens_from_result(): total_tokens fallback style
- parse_tokens_from_result(): mixed JSON/plain output
- parse_tokens_from_result(): empty string returns 0
- parse_tokens_from_result(): no usage key returns 0
- parse_tokens_from_result(): multiple usage lines are summed
- parse_tokens_from_result(): malformed JSON lines skipped
- track_result_stdout(): end-to-end parse + track
- track_result_stdout(): raises BudgetExceededError when over budget
- all_usage property: reflects current state
- Export from thegent.orchestration.__init__

# @trace WL-086
"""

from __future__ import annotations

import orjson as json
import pytest

from thegent.orchestration.budget_tracker import BudgetExceededError, BudgetTracker
from thegent.orchestration.plan import OrchestrationPlan

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_plan(goal: str = "test goal") -> OrchestrationPlan:
    return OrchestrationPlan(goal=goal)


def _make_jsonl_usage(prompt: int, completion: int, extra_text: str = "") -> str:
    """Build a JSONL stdout string with an OpenAI-style usage object."""
    obj = {"usage": {"prompt_tokens": prompt, "completion_tokens": completion}}
    lines = [json.dumps(obj).decode()]
    if extra_text:
        lines.append(extra_text)
    return "\n".join(lines)


def _make_jsonl_total(total: int) -> str:
    """Build a JSONL stdout string with a total_tokens usage object."""
    obj = {"usage": {"total_tokens": total}}
    return json.dumps(obj).decode()


# ---------------------------------------------------------------------------
# 1. BudgetExceededError
# ---------------------------------------------------------------------------


class TestBudgetExceededError:
    def test_attributes_stored(self) -> None:
        """BudgetExceededError must store node_id, budget, actual. # @trace WL-086"""
        err = BudgetExceededError(node_id="n1", budget=100, actual=150)
        assert err.node_id == "n1"
        assert err.budget == 100
        assert err.actual == 150

    def test_is_exception(self) -> None:
        """BudgetExceededError must be an Exception subclass. # @trace WL-086"""
        err = BudgetExceededError(node_id="n1", budget=100, actual=150)
        assert isinstance(err, Exception)

    def test_message_contains_node_id(self) -> None:
        """Error message must mention the node_id. # @trace WL-086"""
        err = BudgetExceededError(node_id="my-node", budget=500, actual=600)
        assert "my-node" in str(err)

    def test_message_contains_budget(self) -> None:
        """Error message must mention the budget. # @trace WL-086"""
        err = BudgetExceededError(node_id="n1", budget=500, actual=600)
        assert "500" in str(err)

    def test_message_contains_actual(self) -> None:
        """Error message must mention the actual usage. # @trace WL-086"""
        err = BudgetExceededError(node_id="n1", budget=500, actual=600)
        assert "600" in str(err)

    def test_message_shows_over_amount(self) -> None:
        """Error message must show how far over budget the node is. # @trace WL-086"""
        err = BudgetExceededError(node_id="n1", budget=100, actual=175)
        msg = str(err)
        assert "75" in msg  # over by 75


# ---------------------------------------------------------------------------
# 2. BudgetTracker construction
# ---------------------------------------------------------------------------


class TestBudgetTrackerConstruction:
    def test_accepts_orchestration_plan(self) -> None:
        """BudgetTracker must accept an OrchestrationPlan. # @trace WL-086"""
        plan = _make_plan()
        tracker = BudgetTracker(plan)
        assert tracker is not None

    def test_initial_all_usage_empty(self) -> None:
        """all_usage must be empty dict on fresh tracker. # @trace WL-086"""
        plan = _make_plan()
        tracker = BudgetTracker(plan)
        assert tracker.all_usage == {}


# ---------------------------------------------------------------------------
# 3. track()
# ---------------------------------------------------------------------------


class TestTrack:
    def test_track_within_budget_does_not_raise(self) -> None:
        """track() must not raise when usage is within budget. # @trace WL-086"""
        plan = _make_plan()
        node = plan.add_task("t1", budget_tokens=500)
        tracker = BudgetTracker(plan)
        tracker.track(node.id, 400)  # 400 <= 500, no error

    def test_track_at_exact_budget_does_not_raise(self) -> None:
        """track() at exactly the budget must not raise. # @trace WL-086"""
        plan = _make_plan()
        node = plan.add_task("t1", budget_tokens=300)
        tracker = BudgetTracker(plan)
        tracker.track(node.id, 300)  # exactly 300, no error

    def test_track_over_budget_raises(self) -> None:
        """track() must raise BudgetExceededError when usage exceeds budget. # @trace WL-086"""
        plan = _make_plan()
        node = plan.add_task("t1", budget_tokens=100)
        tracker = BudgetTracker(plan)
        with pytest.raises(BudgetExceededError) as exc_info:
            tracker.track(node.id, 101)
        assert exc_info.value.node_id == node.id
        assert exc_info.value.budget == 100
        assert exc_info.value.actual == 101

    def test_track_accumulates_across_calls(self) -> None:
        """track() must accumulate usage across multiple calls. # @trace WL-086"""
        plan = _make_plan()
        node = plan.add_task("t1", budget_tokens=300)
        tracker = BudgetTracker(plan)
        tracker.track(node.id, 100)
        tracker.track(node.id, 100)
        assert tracker.get_usage(node.id) == 200

    def test_track_accumulation_triggers_error(self) -> None:
        """Accumulated usage across calls must trigger BudgetExceededError. # @trace WL-086"""
        plan = _make_plan()
        node = plan.add_task("t1", budget_tokens=150)
        tracker = BudgetTracker(plan)
        tracker.track(node.id, 100)
        with pytest.raises(BudgetExceededError) as exc_info:
            tracker.track(node.id, 51)  # 100 + 51 = 151 > 150
        assert exc_info.value.actual == 151

    def test_track_unknown_node_raises_key_error(self) -> None:
        """track() must raise KeyError for a node_id not in the plan. # @trace WL-086"""
        plan = _make_plan()
        tracker = BudgetTracker(plan)
        with pytest.raises(KeyError):
            tracker.track("nonexistent-id", 10)

    def test_track_node_without_budget_no_enforcement(self) -> None:
        """track() must not raise for nodes that have no budget_tokens set. # @trace WL-086"""
        plan = _make_plan()
        node = plan.add_task("t1")  # no budget_tokens
        tracker = BudgetTracker(plan)
        tracker.track(node.id, 999_999)  # no enforcement, no error
        assert tracker.get_usage(node.id) == 999_999

    def test_track_wrong_budget_type_raises_type_error(self) -> None:
        """track() must raise TypeError when budget_tokens is not int. # @trace WL-086"""
        plan = _make_plan()
        node = plan.add_task("t1")
        node.metadata["budget_tokens"] = "not-an-int"  # type: ignore[assignment]
        tracker = BudgetTracker(plan)
        with pytest.raises(TypeError):
            tracker.track(node.id, 10)

    def test_track_two_nodes_independent(self) -> None:
        """track() for separate nodes must not interfere with each other. # @trace WL-086"""
        plan = _make_plan()
        n1 = plan.add_task("t1", budget_tokens=100)
        n2 = plan.add_task("t2", budget_tokens=200)
        tracker = BudgetTracker(plan)
        tracker.track(n1.id, 80)
        tracker.track(n2.id, 180)
        assert tracker.get_usage(n1.id) == 80
        assert tracker.get_usage(n2.id) == 180


# ---------------------------------------------------------------------------
# 4. get_usage()
# ---------------------------------------------------------------------------


class TestGetUsage:
    def test_get_usage_untracked_returns_zero(self) -> None:
        """get_usage() must return 0 for a node with no tracked usage. # @trace WL-086"""
        plan = _make_plan()
        node = plan.add_task("t1", budget_tokens=500)
        tracker = BudgetTracker(plan)
        assert tracker.get_usage(node.id) == 0

    def test_get_usage_returns_cumulative_total(self) -> None:
        """get_usage() must return the sum of all tracked calls. # @trace WL-086"""
        plan = _make_plan()
        node = plan.add_task("t1", budget_tokens=1000)
        tracker = BudgetTracker(plan)
        tracker.track(node.id, 100)
        tracker.track(node.id, 250)
        assert tracker.get_usage(node.id) == 350

    def test_get_usage_unknown_node_raises_key_error(self) -> None:
        """get_usage() must raise KeyError for unknown node_id. # @trace WL-086"""
        plan = _make_plan()
        tracker = BudgetTracker(plan)
        with pytest.raises(KeyError):
            tracker.get_usage("ghost-node")


# ---------------------------------------------------------------------------
# 5. reset_usage()
# ---------------------------------------------------------------------------


class TestResetUsage:
    def test_reset_sets_usage_to_zero(self) -> None:
        """reset_usage() must zero out the accumulated usage for the node. # @trace WL-086"""
        plan = _make_plan()
        node = plan.add_task("t1", budget_tokens=500)
        tracker = BudgetTracker(plan)
        tracker.track(node.id, 300)
        tracker.reset_usage(node.id)
        assert tracker.get_usage(node.id) == 0

    def test_reset_allows_reuse_after_reset(self) -> None:
        """After reset_usage(), track() must work within budget again. # @trace WL-086"""
        plan = _make_plan()
        node = plan.add_task("t1", budget_tokens=200)
        tracker = BudgetTracker(plan)
        tracker.track(node.id, 180)
        tracker.reset_usage(node.id)
        tracker.track(node.id, 150)  # 150 <= 200 after reset, no error
        assert tracker.get_usage(node.id) == 150

    def test_reset_unknown_node_raises_key_error(self) -> None:
        """reset_usage() must raise KeyError for unknown node_id. # @trace WL-086"""
        plan = _make_plan()
        tracker = BudgetTracker(plan)
        with pytest.raises(KeyError):
            tracker.reset_usage("ghost-node")


# ---------------------------------------------------------------------------
# 6. parse_tokens_from_result()
# ---------------------------------------------------------------------------


class TestParseTokensFromResult:
    def test_parse_prompt_plus_completion(self) -> None:
        """Must sum prompt_tokens + completion_tokens. # @trace WL-086"""
        stdout = _make_jsonl_usage(prompt=100, completion=50)
        assert BudgetTracker.parse_tokens_from_result(stdout) == 150

    def test_parse_total_tokens_fallback(self) -> None:
        """Must use total_tokens when prompt/completion split is absent. # @trace WL-086"""
        stdout = _make_jsonl_total(200)
        assert BudgetTracker.parse_tokens_from_result(stdout) == 200

    def test_parse_empty_string_returns_zero(self) -> None:
        """Empty string must return 0. # @trace WL-086"""
        assert BudgetTracker.parse_tokens_from_result("") == 0

    def test_parse_no_usage_key_returns_zero(self) -> None:
        """JSON without 'usage' key must return 0. # @trace WL-086"""
        stdout = json.dumps({"model": "gpt-5", "choices": []}).decode()
        assert BudgetTracker.parse_tokens_from_result(stdout) == 0

    def test_parse_multiple_usage_lines_summed(self) -> None:
        """Multiple usage lines must be summed together. # @trace WL-086"""
        line1 = json.dumps(
            {"usage": {"prompt_tokens": 80, "completion_tokens": 20}}
        ).decode()
        line2 = json.dumps(
            {"usage": {"prompt_tokens": 40, "completion_tokens": 10}}
        ).decode()
        stdout = f"{line1}\n{line2}"
        assert BudgetTracker.parse_tokens_from_result(stdout) == 150

    def test_parse_mixed_json_and_plain_text(self) -> None:
        """Plain text lines interspersed with JSON must not cause errors. # @trace WL-086"""
        usage_line = json.dumps(
            {"usage": {"prompt_tokens": 70, "completion_tokens": 30}}
        ).decode()
        stdout = f"Starting agent...\n{usage_line}\nDone."
        assert BudgetTracker.parse_tokens_from_result(stdout) == 100

    def test_parse_malformed_json_skipped(self) -> None:
        """Malformed JSON lines must be silently skipped. # @trace WL-086"""
        bad_line = "{this is not valid json}"
        good_line = json.dumps(
            {"usage": {"prompt_tokens": 50, "completion_tokens": 25}}
        ).decode()
        stdout = f"{bad_line}\n{good_line}"
        assert BudgetTracker.parse_tokens_from_result(stdout) == 75

    def test_parse_usage_not_dict_returns_zero(self) -> None:
        """When 'usage' is not a dict, it must be skipped. # @trace WL-086"""
        stdout = json.dumps({"usage": 42}).decode()
        assert BudgetTracker.parse_tokens_from_result(stdout) == 0

    def test_parse_zero_tokens_in_usage(self) -> None:
        """Usage object with all-zero tokens must return 0. # @trace WL-086"""
        stdout = json.dumps(
            {"usage": {"prompt_tokens": 0, "completion_tokens": 0}}
        ).decode()
        assert BudgetTracker.parse_tokens_from_result(stdout) == 0


# ---------------------------------------------------------------------------
# 7. track_result_stdout()
# ---------------------------------------------------------------------------


class TestTrackResultStdout:
    def test_end_to_end_parse_and_track(self) -> None:
        """track_result_stdout() must parse tokens and accumulate them. # @trace WL-086"""
        plan = _make_plan()
        node = plan.add_task("t1", budget_tokens=1000)
        tracker = BudgetTracker(plan)
        stdout = _make_jsonl_usage(prompt=200, completion=100)
        returned = tracker.track_result_stdout(node.id, stdout)
        assert returned == 300
        assert tracker.get_usage(node.id) == 300

    def test_track_result_stdout_raises_on_budget_exceeded(self) -> None:
        """track_result_stdout() must raise BudgetExceededError on budget breach. # @trace WL-086"""
        plan = _make_plan()
        node = plan.add_task("t1", budget_tokens=50)
        tracker = BudgetTracker(plan)
        stdout = _make_jsonl_usage(prompt=40, completion=20)  # 60 > 50
        with pytest.raises(BudgetExceededError) as exc_info:
            tracker.track_result_stdout(node.id, stdout)
        assert exc_info.value.budget == 50
        assert exc_info.value.actual == 60


# ---------------------------------------------------------------------------
# 8. all_usage property
# ---------------------------------------------------------------------------


class TestAllUsage:
    def test_all_usage_reflects_current_state(self) -> None:
        """all_usage must return a snapshot of all tracked nodes. # @trace WL-086"""
        plan = _make_plan()
        n1 = plan.add_task("t1", budget_tokens=500)
        n2 = plan.add_task("t2", budget_tokens=500)
        tracker = BudgetTracker(plan)
        tracker.track(n1.id, 100)
        tracker.track(n2.id, 200)
        usage = tracker.all_usage
        assert usage[n1.id] == 100
        assert usage[n2.id] == 200

    def test_all_usage_is_copy(self) -> None:
        """all_usage must return a copy, not a live reference. # @trace WL-086"""
        plan = _make_plan()
        node = plan.add_task("t1", budget_tokens=500)
        tracker = BudgetTracker(plan)
        tracker.track(node.id, 50)
        snapshot = tracker.all_usage
        tracker.track(node.id, 50)  # add more
        assert snapshot[node.id] == 50  # snapshot unchanged


# ---------------------------------------------------------------------------
# 9. Export from thegent.orchestration
# ---------------------------------------------------------------------------


class TestPublicExports:
    def test_budget_tracker_exported_from_orchestration(self) -> None:
        """BudgetTracker must be importable from thegent.orchestration. # @trace WL-086"""
        from thegent.orchestration import BudgetTracker as BT  # noqa: PLC0415, N817

        assert BT is BudgetTracker

    def test_budget_exceeded_error_exported_from_orchestration(self) -> None:
        """BudgetExceededError must be importable from thegent.orchestration. # @trace WL-086"""
        from thegent.orchestration import (
            BudgetExceededError as BEE,  # noqa: PLC0415, N817
        )

        assert BEE is BudgetExceededError
