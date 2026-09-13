"""Tests for WL-297 connector cost accounting."""

from __future__ import annotations

import pytest

from thegent.integrations.connector_cost_accounting import ConnectorCostLedger


@pytest.mark.requirement("WL-297")
def test_connector_cost_ledger_aggregates_by_connector() -> None:
    ledger = ConnectorCostLedger()
    ledger.record(
        connector="github",
        operation="pull",
        requests=2,
        tokens_in=10,
        tokens_out=20,
        usd_cost=0.05,
    )
    ledger.record(
        connector="github",
        operation="push",
        requests=1,
        tokens_in=5,
        tokens_out=5,
        usd_cost=0.02,
    )
    ledger.record(
        connector="linear",
        operation="pull",
        requests=3,
        tokens_in=7,
        tokens_out=8,
        usd_cost=0.03,
    )

    summary = {item.connector: item for item in ledger.summary_by_connector()}
    assert summary["github"].requests == 3
    assert summary["github"].usd_cost == pytest.approx(0.07)
    assert summary["linear"].requests == 3
    assert ledger.total_cost() == pytest.approx(0.10)


@pytest.mark.requirement("WL-297")
def test_connector_cost_ledger_rejects_negative_values() -> None:
    ledger = ConnectorCostLedger()
    with pytest.raises(ValueError, match="non-negative"):
        ledger.record(
            connector="github",
            operation="pull",
            requests=-1,
            tokens_in=0,
            tokens_out=0,
            usd_cost=0.0,
        )
