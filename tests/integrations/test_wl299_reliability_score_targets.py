"""Tests for WL-299 reliability score targets."""

from __future__ import annotations

import pytest

from thegent.integrations.reliability_score_targets import (
    ReliabilityInputs,
    ReliabilityTargets,
    classify_reliability,
    compute_reliability_score,
)


@pytest.mark.requirement("WL-299")
def test_compute_reliability_score_and_classification() -> None:
    score = compute_reliability_score(
        ReliabilityInputs(success_rate=0.9, low_conflict_rate=0.8, sla_hit_rate=0.85)
    )
    assert score > 80
    assert classify_reliability(score, ReliabilityTargets()) in {"healthy", "excellent"}


@pytest.mark.requirement("WL-299")
def test_compute_reliability_score_rejects_out_of_range_inputs() -> None:
    with pytest.raises(ValueError, match=r"\[0,1\]"):
        compute_reliability_score(
            ReliabilityInputs(success_rate=1.2, low_conflict_rate=0.8, sla_hit_rate=0.8)
        )
