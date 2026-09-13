"""Tests for WL-083: ResultAggregator — Merge Sub-Agent Outputs.

# @trace WL-083
"""

from __future__ import annotations

from thegent.orchestration.aggregator import ResultAggregator
from thegent.orchestration.inter_agent_protocol import InterAgentMessage

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_msg(
    message_type: str,
    sender_id: str = "agent-a",
    recipient_id: str = "agent-b",
    payload: dict | None = None,
    correlation_id: str | None = None,
) -> InterAgentMessage:
    return InterAgentMessage(
        sender_id=sender_id,
        recipient_id=recipient_id,
        message_type=message_type,  # type: ignore[arg-type]
        payload=payload or {},
        correlation_id=correlation_id,
    )


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


class TestResultAggregatorConstruction:
    """ResultAggregator can be instantiated with no arguments."""

    def test_instantiates_with_no_args(self):
        # @trace WL-083
        agg = ResultAggregator()
        assert agg is not None

    def test_initial_aggregate_is_empty(self):
        # @trace WL-083
        agg = ResultAggregator()
        result = agg.aggregate()
        assert result["total"] == 0
        assert result["by_type"] == {}
        assert result["results"] == []
        assert result["errors"] == []
        assert result["passed"] is True

    def test_initial_summary_mentions_zero(self):
        # @trace WL-083
        agg = ResultAggregator()
        summary = agg.summary()
        assert "0" in summary


# ---------------------------------------------------------------------------
# add()
# ---------------------------------------------------------------------------


class TestResultAggregatorAdd:
    """ResultAggregator.add() stores messages without mutation."""

    def test_add_single_result_message(self):
        # @trace WL-083
        agg = ResultAggregator()
        msg = _make_msg("result")
        agg.add(msg)
        result = agg.aggregate()
        assert result["total"] == 1

    def test_add_single_error_message(self):
        # @trace WL-083
        agg = ResultAggregator()
        msg = _make_msg("error")
        agg.add(msg)
        result = agg.aggregate()
        assert result["total"] == 1

    def test_add_multiple_messages_accumulates(self):
        # @trace WL-083
        agg = ResultAggregator()
        for _ in range(5):
            agg.add(_make_msg("result"))
        assert agg.aggregate()["total"] == 5

    def test_add_preserves_message_identity(self):
        # @trace WL-083
        agg = ResultAggregator()
        msg = _make_msg("result", payload={"value": 42})
        agg.add(msg)
        stored = agg.aggregate()["results"][0]
        assert stored.id == msg.id
        assert stored.payload == {"value": 42}

    def test_add_does_not_mutate_original_message(self):
        # @trace WL-083
        agg = ResultAggregator()
        msg = _make_msg("result")
        original_id = msg.id
        agg.add(msg)
        assert msg.id == original_id

    def test_add_all_five_message_types(self):
        # @trace WL-083
        agg = ResultAggregator()
        for mtype in ("task_request", "status_update", "result", "error", "heartbeat"):
            agg.add(_make_msg(mtype))
        assert agg.aggregate()["total"] == 5


# ---------------------------------------------------------------------------
# aggregate()
# ---------------------------------------------------------------------------


class TestResultAggregatorAggregate:
    """aggregate() returns correct counts, lists, and passed flag."""

    def test_total_counts_all_message_types(self):
        # @trace WL-083
        agg = ResultAggregator()
        agg.add(_make_msg("result"))
        agg.add(_make_msg("error"))
        agg.add(_make_msg("heartbeat"))
        assert agg.aggregate()["total"] == 3

    def test_by_type_single_result(self):
        # @trace WL-083
        agg = ResultAggregator()
        agg.add(_make_msg("result"))
        assert agg.aggregate()["by_type"] == {"result": 1}

    def test_by_type_single_error(self):
        # @trace WL-083
        agg = ResultAggregator()
        agg.add(_make_msg("error"))
        assert agg.aggregate()["by_type"] == {"error": 1}

    def test_by_type_mixed_messages(self):
        # @trace WL-083
        agg = ResultAggregator()
        agg.add(_make_msg("result"))
        agg.add(_make_msg("result"))
        agg.add(_make_msg("error"))
        agg.add(_make_msg("heartbeat"))
        by_type = agg.aggregate()["by_type"]
        assert by_type["result"] == 2
        assert by_type["error"] == 1
        assert by_type["heartbeat"] == 1

    def test_results_list_contains_only_result_messages(self):
        # @trace WL-083
        agg = ResultAggregator()
        agg.add(_make_msg("result"))
        agg.add(_make_msg("error"))
        agg.add(_make_msg("status_update"))
        results = agg.aggregate()["results"]
        assert len(results) == 1
        assert results[0].message_type == "result"

    def test_errors_list_contains_only_error_messages(self):
        # @trace WL-083
        agg = ResultAggregator()
        agg.add(_make_msg("result"))
        agg.add(_make_msg("error"))
        agg.add(_make_msg("status_update"))
        errors = agg.aggregate()["errors"]
        assert len(errors) == 1
        assert errors[0].message_type == "error"

    def test_passed_true_when_no_errors(self):
        # @trace WL-083
        agg = ResultAggregator()
        agg.add(_make_msg("result"))
        agg.add(_make_msg("heartbeat"))
        assert agg.aggregate()["passed"] is True

    def test_passed_false_when_errors_present(self):
        # @trace WL-083
        agg = ResultAggregator()
        agg.add(_make_msg("result"))
        agg.add(_make_msg("error"))
        assert agg.aggregate()["passed"] is False

    def test_passed_false_with_only_errors(self):
        # @trace WL-083
        agg = ResultAggregator()
        agg.add(_make_msg("error"))
        assert agg.aggregate()["passed"] is False

    def test_passed_true_when_empty(self):
        # @trace WL-083
        agg = ResultAggregator()
        assert agg.aggregate()["passed"] is True

    def test_aggregate_returns_dict(self):
        # @trace WL-083
        agg = ResultAggregator()
        result = agg.aggregate()
        assert isinstance(result, dict)

    def test_aggregate_has_required_keys(self):
        # @trace WL-083
        agg = ResultAggregator()
        result = agg.aggregate()
        for key in ("total", "by_type", "results", "errors", "passed"):
            assert key in result

    def test_aggregate_is_idempotent(self):
        # @trace WL-083
        agg = ResultAggregator()
        agg.add(_make_msg("result"))
        first = agg.aggregate()
        second = agg.aggregate()
        assert first["total"] == second["total"]
        assert first["passed"] == second["passed"]


# ---------------------------------------------------------------------------
# clear()
# ---------------------------------------------------------------------------


class TestResultAggregatorClear:
    """clear() resets all internal state."""

    def test_clear_resets_total_to_zero(self):
        # @trace WL-083
        agg = ResultAggregator()
        agg.add(_make_msg("result"))
        agg.clear()
        assert agg.aggregate()["total"] == 0

    def test_clear_resets_by_type(self):
        # @trace WL-083
        agg = ResultAggregator()
        agg.add(_make_msg("result"))
        agg.clear()
        assert agg.aggregate()["by_type"] == {}

    def test_clear_resets_results_list(self):
        # @trace WL-083
        agg = ResultAggregator()
        agg.add(_make_msg("result"))
        agg.clear()
        assert agg.aggregate()["results"] == []

    def test_clear_resets_errors_list(self):
        # @trace WL-083
        agg = ResultAggregator()
        agg.add(_make_msg("error"))
        agg.clear()
        assert agg.aggregate()["errors"] == []

    def test_clear_resets_passed_to_true(self):
        # @trace WL-083
        agg = ResultAggregator()
        agg.add(_make_msg("error"))
        agg.clear()
        assert agg.aggregate()["passed"] is True

    def test_add_after_clear_works_correctly(self):
        # @trace WL-083
        agg = ResultAggregator()
        agg.add(_make_msg("error"))
        agg.clear()
        agg.add(_make_msg("result"))
        result = agg.aggregate()
        assert result["total"] == 1
        assert result["passed"] is True


# ---------------------------------------------------------------------------
# summary()
# ---------------------------------------------------------------------------


class TestResultAggregatorSummary:
    """summary() returns a non-empty human-readable string."""

    def test_summary_returns_string(self):
        # @trace WL-083
        agg = ResultAggregator()
        assert isinstance(agg.summary(), str)

    def test_summary_non_empty(self):
        # @trace WL-083
        agg = ResultAggregator()
        assert len(agg.summary()) > 0

    def test_summary_reflects_total(self):
        # @trace WL-083
        agg = ResultAggregator()
        agg.add(_make_msg("result"))
        agg.add(_make_msg("result"))
        assert "2" in agg.summary()

    def test_summary_mentions_passed_when_no_errors(self):
        # @trace WL-083
        agg = ResultAggregator()
        agg.add(_make_msg("result"))
        summary = agg.summary().lower()
        assert "pass" in summary

    def test_summary_mentions_failed_when_errors_present(self):
        # @trace WL-083
        agg = ResultAggregator()
        agg.add(_make_msg("error"))
        summary = agg.summary().lower()
        assert "fail" in summary or "error" in summary
