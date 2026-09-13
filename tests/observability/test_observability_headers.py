"""Tests for GW-35, GW-36, GW-38 observability header helpers.

# @trace FR-OBS-035 FR-OBS-036 FR-OBS-038
"""

from __future__ import annotations

import time

import pytest

from thegent.cliproxy_adapter import (
    TTFTTracker,
    build_event_id_header,
    build_fallback_step_header,
    generate_event_id,
)

# ---------------------------------------------------------------------------
# GW-35: generate_event_id
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-OBS-035")
def test_generate_event_id_format() -> None:
    """Event ID must start with 'tg-' and have total length of 11 chars."""
    event_id = generate_event_id()
    assert event_id.startswith("tg-")
    # "tg-" (3) + 8 hex chars = 11 total
    assert len(event_id) == 11


@pytest.mark.requirement("FR-OBS-035")
def test_generate_event_id_unique() -> None:
    """Two consecutive calls must return different values."""
    id1 = generate_event_id()
    id2 = generate_event_id()
    assert id1 != id2


# ---------------------------------------------------------------------------
# GW-35: build_event_id_header
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-OBS-035")
def test_build_event_id_header_key() -> None:
    """Returned dict must contain the 'tg-event-id' key."""
    header = build_event_id_header()
    assert "tg-event-id" in header


@pytest.mark.requirement("FR-OBS-035")
def test_build_event_id_header_value_format() -> None:
    """tg-event-id value must have the correct format (starts with 'tg-', length 11)."""
    header = build_event_id_header()
    value = header["tg-event-id"]
    assert value.startswith("tg-")
    assert len(value) == 11


# ---------------------------------------------------------------------------
# GW-36: build_fallback_step_header
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-OBS-036")
def test_build_fallback_step_header_zero() -> None:
    """step=0 (primary succeeded) must yield '0'."""
    header = build_fallback_step_header(0)
    assert header["tg-fallback-step"] == "0"


@pytest.mark.requirement("FR-OBS-036")
def test_build_fallback_step_header_nonzero() -> None:
    """step=2 must yield '2'."""
    header = build_fallback_step_header(2)
    assert header["tg-fallback-step"] == "2"


@pytest.mark.requirement("FR-OBS-036")
def test_build_fallback_step_header_key() -> None:
    """Returned dict must contain the 'tg-fallback-step' key."""
    header = build_fallback_step_header(1)
    assert "tg-fallback-step" in header


# ---------------------------------------------------------------------------
# GW-38: TTFTTracker
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-OBS-038")
def test_ttft_tracker_initial_state() -> None:
    """Before start(), ttft_seconds must be None."""
    tracker = TTFTTracker()
    assert tracker.ttft_seconds is None


@pytest.mark.requirement("FR-OBS-038")
def test_ttft_tracker_not_started_record_noop() -> None:
    """record_first_token() before start() must be a no-op (ttft_seconds stays None)."""
    tracker = TTFTTracker()
    tracker.record_first_token()
    assert tracker.ttft_seconds is None


@pytest.mark.requirement("FR-OBS-038")
def test_ttft_tracker_measures_ttft() -> None:
    """start() then record_first_token() must yield a positive TTFT."""
    tracker = TTFTTracker()
    tracker.start()
    time.sleep(0.01)  # ensure measurable elapsed time
    tracker.record_first_token()
    ttft = tracker.ttft_seconds
    assert ttft is not None
    assert ttft > 0.0


@pytest.mark.requirement("FR-OBS-038")
def test_ttft_tracker_idempotent_first_token() -> None:
    """A second call to record_first_token() must not change the recorded value."""
    tracker = TTFTTracker()
    tracker.start()
    time.sleep(0.005)
    tracker.record_first_token()
    first = tracker.ttft_seconds
    time.sleep(0.01)
    tracker.record_first_token()
    second = tracker.ttft_seconds
    assert first == second


@pytest.mark.requirement("FR-OBS-038")
def test_ttft_tracker_build_ttft_header_before_measured() -> None:
    """build_ttft_header() before measurement must return an empty dict."""
    tracker = TTFTTracker()
    assert tracker.build_ttft_header() == {}


@pytest.mark.requirement("FR-OBS-038")
def test_ttft_tracker_build_ttft_header_after_measured() -> None:
    """build_ttft_header() after measurement must return {'tg-ttft-ms': '<value>'}."""
    tracker = TTFTTracker()
    tracker.start()
    time.sleep(0.01)
    tracker.record_first_token()
    header = tracker.build_ttft_header()
    assert "tg-ttft-ms" in header
    # Value must be a string representing a non-negative float
    value_str = header["tg-ttft-ms"]
    value = float(value_str)
    assert value > 0.0
