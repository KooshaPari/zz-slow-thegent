"""Tests for ResultAggregator: merge sub-agent outputs with cost tracking.

@trace FR-ORC-083
"""

from __future__ import annotations

import pytest

from thegent.orchestration.protocol import SubAgentResult, SubAgentStatus
from thegent.orchestration.result_aggregator import AggregatedResult, ResultAggregator


def _make_result(
    *,
    request_id: str = "req-1",
    agent_type: str = "test-agent",
    status: SubAgentStatus = SubAgentStatus.COMPLETED,
    error: str | None = None,
    cost_usd: float = 0.0,
    tokens_used: int = 0,
) -> SubAgentResult:
    """Factory for SubAgentResult with cost/token metrics embedded."""
    return SubAgentResult(
        request_id=request_id,
        agent_type=agent_type,
        status=status,
        error=error,
        metrics={"cost_usd": cost_usd, "tokens_used": tokens_used},
    )


@pytest.mark.requirement("FR-ORC-083")
class TestResultAggregatorEmpty:
    def test_result_aggregator_empty_aggregate(self) -> None:
        """aggregate() on empty aggregator returns zero-value AggregatedResult."""
        agg = ResultAggregator()
        result = agg.aggregate()
        assert isinstance(result, AggregatedResult)
        assert result.results == []
        assert result.total_cost_usd == 0.0
        assert result.total_tokens_used == 0
        assert result.success_count == 0
        assert result.failure_count == 0
        assert result.all_passed is True
        assert result.errors == []


@pytest.mark.requirement("FR-ORC-083")
class TestResultAggregatorSingle:
    def test_result_aggregator_single_result(self) -> None:
        """aggregate() with one COMPLETED result yields correct counts."""
        agg = ResultAggregator()
        r = _make_result(request_id="req-1", status=SubAgentStatus.COMPLETED)
        agg.add(r)
        result = agg.aggregate()
        assert len(result.results) == 1
        assert result.success_count == 1
        assert result.failure_count == 0
        assert result.all_passed is True
        assert result.errors == []

    def test_result_aggregator_single_failed_result(self) -> None:
        """aggregate() with one FAILED result yields failure_count=1, all_passed=False."""
        agg = ResultAggregator()
        r = _make_result(
            request_id="req-1",
            status=SubAgentStatus.FAILED,
            error="something went wrong",
        )
        agg.add(r)
        result = agg.aggregate()
        assert result.success_count == 0
        assert result.failure_count == 1
        assert result.all_passed is False
        assert "something went wrong" in result.errors


@pytest.mark.requirement("FR-ORC-083")
class TestResultAggregatorMultiple:
    def test_result_aggregator_multiple_results_success(self) -> None:
        """All COMPLETED results produce all_passed=True."""
        agg = ResultAggregator()
        for i in range(3):
            agg.add(_make_result(request_id=f"req-{i}", status=SubAgentStatus.COMPLETED))
        result = agg.aggregate()
        assert result.success_count == 3
        assert result.failure_count == 0
        assert result.all_passed is True

    def test_result_aggregator_mixed_success_failure(self) -> None:
        """Mixed results produce correct success/failure counts and all_passed=False."""
        agg = ResultAggregator()
        agg.add(_make_result(request_id="req-1", status=SubAgentStatus.COMPLETED))
        agg.add(_make_result(request_id="req-2", status=SubAgentStatus.FAILED, error="err-A"))
        agg.add(_make_result(request_id="req-3", status=SubAgentStatus.COMPLETED))
        result = agg.aggregate()
        assert result.success_count == 2
        assert result.failure_count == 1
        assert result.all_passed is False
        assert "err-A" in result.errors


@pytest.mark.requirement("FR-ORC-083")
class TestResultAggregatorCostAndTokens:
    def test_result_aggregator_total_cost_sum(self) -> None:
        """total_cost_usd is the sum of cost_usd from all results."""
        agg = ResultAggregator()
        agg.add(_make_result(request_id="req-1", cost_usd=0.10))
        agg.add(_make_result(request_id="req-2", cost_usd=0.25))
        agg.add(_make_result(request_id="req-3", cost_usd=0.05))
        result = agg.aggregate()
        assert abs(result.total_cost_usd - 0.40) < 1e-9

    def test_result_aggregator_total_tokens_sum(self) -> None:
        """total_tokens_used is the sum of tokens_used from all results."""
        agg = ResultAggregator()
        agg.add(_make_result(request_id="req-1", tokens_used=100))
        agg.add(_make_result(request_id="req-2", tokens_used=250))
        result = agg.aggregate()
        assert result.total_tokens_used == 350

    def test_result_aggregator_zero_cost_and_tokens_when_missing_metrics(self) -> None:
        """Results with no cost/token metrics default to zero contribution."""
        agg = ResultAggregator()
        # Result with empty metrics dict (no cost_usd / tokens_used keys)
        r = SubAgentResult(
            request_id="req-1",
            agent_type="agent",
            status=SubAgentStatus.COMPLETED,
            metrics={},
        )
        agg.add(r)
        result = agg.aggregate()
        assert result.total_cost_usd == 0.0
        assert result.total_tokens_used == 0


@pytest.mark.requirement("FR-ORC-083")
class TestResultAggregatorErrors:
    def test_result_aggregator_errors_collected(self) -> None:
        """errors list collects error strings from all failed results."""
        agg = ResultAggregator()
        agg.add(_make_result(request_id="req-1", status=SubAgentStatus.FAILED, error="timeout"))
        agg.add(_make_result(request_id="req-2", status=SubAgentStatus.FAILED, error="oom"))
        result = agg.aggregate()
        assert "timeout" in result.errors
        assert "oom" in result.errors
        assert len(result.errors) == 2

    def test_result_aggregator_no_errors_when_all_pass(self) -> None:
        """errors list is empty when all results are COMPLETED."""
        agg = ResultAggregator()
        agg.add(_make_result(request_id="req-1", status=SubAgentStatus.COMPLETED))
        result = agg.aggregate()
        assert result.errors == []

    def test_result_aggregator_non_failed_statuses_count_as_failure(self) -> None:
        """CANCELLED and TIMEOUT statuses count as failures (not COMPLETED)."""
        agg = ResultAggregator()
        agg.add(_make_result(request_id="req-1", status=SubAgentStatus.CANCELLED))
        agg.add(_make_result(request_id="req-2", status=SubAgentStatus.TIMEOUT))
        result = agg.aggregate()
        assert result.failure_count == 2
        assert result.success_count == 0
        assert result.all_passed is False


@pytest.mark.requirement("FR-ORC-083")
class TestResultAggregatorModel:
    def test_aggregated_result_is_pydantic_model(self) -> None:
        """AggregatedResult is a Pydantic BaseModel."""
        from pydantic import BaseModel

        assert issubclass(AggregatedResult, BaseModel)

    def test_result_aggregator_aggregate_is_idempotent(self) -> None:
        """Calling aggregate() multiple times returns equivalent results."""
        agg = ResultAggregator()
        agg.add(_make_result(request_id="req-1", tokens_used=50))
        r1 = agg.aggregate()
        r2 = agg.aggregate()
        assert r1.total_tokens_used == r2.total_tokens_used
        assert r1.success_count == r2.success_count
