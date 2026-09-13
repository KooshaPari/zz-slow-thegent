from __future__ import annotations

import pytest

from thegent.cli.services.run_event_helpers import build_run_event_details


def test_build_run_event_details_omits_nan_context_usage_ratio() -> None:
    details = build_run_event_details(
        grounding_sources=[],
        audio_transcript=None,
        audio_sources=[],
        context_usage_ratio=float("nan"),
    )
    assert details is None


def test_build_run_event_details_rounds_finite_context_usage_ratio() -> None:
    details = build_run_event_details(
        grounding_sources=[],
        audio_transcript=None,
        audio_sources=[],
        context_usage_ratio=0.333339,
    )
    assert details == {"context_usage_ratio": 0.3333}


def test_build_run_event_details_omits_non_numeric_context_usage_ratio() -> None:
    details = build_run_event_details(
        grounding_sources=[],
        audio_transcript=None,
        audio_sources=[],
        context_usage_ratio="not-a-number",  # type: ignore[arg-type]
    )
    assert details is None


@pytest.mark.parametrize("ratio", [True, False])
def test_build_run_event_details_omits_boolean_context_usage_ratio(ratio: bool) -> None:
    details = build_run_event_details(
        grounding_sources=[],
        audio_transcript=None,
        audio_sources=[],
        context_usage_ratio=ratio,  # type: ignore[arg-type]
    )
    assert details is None


@pytest.mark.parametrize("ratio", [-0.1, 1.0001])
def test_build_run_event_details_omits_out_of_range_context_usage_ratio(
    ratio: float,
) -> None:
    details = build_run_event_details(
        grounding_sources=[],
        audio_transcript=None,
        audio_sources=[],
        context_usage_ratio=ratio,
    )
    assert details is None
