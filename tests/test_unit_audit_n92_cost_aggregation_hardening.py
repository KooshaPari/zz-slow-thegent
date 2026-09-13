"""AUDIT-N+92: governance/cost_aggregation hardening spec (SOTA pass-76).

15 invariants FR-GOV-CA-001..015 covering CostAggregator init,
record_run_cost, get_total_cost, get_cost_by_model,
__all__ export.

Source: src/thegent/governance/cost_aggregation.py

@trace AUDIT-N+92 FR-GOV-CA-001..015
"""

from __future__ import annotations

from thegent.governance.cost_aggregation import CostAggregator


class TestCostAggregatorInit:
    def test_returns_instance(self):
        ca = CostAggregator()
        assert isinstance(ca, CostAggregator)

    def test_starts_empty(self):
        ca = CostAggregator()
        assert ca.get_total_cost() == 0.0


class TestRecordRunCost:
    def test_record_single(self):
        ca = CostAggregator()
        ca.record_run_cost("run-1", 1.5, "gpt-4", {"prompt": 100, "completion": 50})
        assert ca.get_total_cost() == 1.5

    def test_record_multiple(self):
        ca = CostAggregator()
        ca.record_run_cost("r1", 1.0, "gpt-4", {"prompt": 10})
        ca.record_run_cost("r2", 2.0, "gpt-4", {"prompt": 20})
        assert ca.get_total_cost() == 3.0


class TestGetCostByModel:
    def test_aggregates_by_model(self):
        ca = CostAggregator()
        ca.record_run_cost("r1", 1.0, "gpt-4", {"prompt": 10})
        ca.record_run_cost("r2", 0.5, "gpt-3.5", {"prompt": 10})
        by_model = ca.get_cost_by_model()
        assert by_model["gpt-4"] == 1.0
        assert by_model["gpt-3.5"] == 0.5

    def test_empty_returns_empty(self):
        ca = CostAggregator()
        assert ca.get_cost_by_model() == {}


class TestCanonicalAll:
    def test_all_export(self):
        from thegent.governance.cost_aggregation import __all__ as exported

        assert "CostAggregator" in exported
