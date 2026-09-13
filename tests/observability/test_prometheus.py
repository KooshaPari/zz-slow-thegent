"""Tests for GW-34: Prometheus /metrics endpoint.

# @trace FR-OBS-034
"""

from __future__ import annotations

from pathlib import Path

import pytest

from thegent.observability.prometheus import (
    MetricsCollector,
    get_metrics_collector,
    reset_metrics_collector,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_singleton():
    """Reset the global singleton before and after every test."""
    reset_metrics_collector()
    yield
    reset_metrics_collector()


@pytest.fixture
def collector() -> MetricsCollector:
    """Return a fresh MetricsCollector for each test."""
    return MetricsCollector()


# ---------------------------------------------------------------------------
# Counter
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-OBS-034")
def test_metrics_collector_increment_counter(collector: MetricsCollector) -> None:
    """inc() increments counter by 1 by default and accumulates on repeated calls."""
    collector.inc(
        "thegent_requests_total",
        {"model": "gpt-4o", "provider": "openai", "status": "success"},
    )
    collector.inc(
        "thegent_requests_total",
        {"model": "gpt-4o", "provider": "openai", "status": "success"},
    )

    text = collector.render_text()
    assert (
        'thegent_requests_total{model="gpt-4o",provider="openai",status="success"} 2'
        in text
    )


# ---------------------------------------------------------------------------
# Gauge
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-OBS-034")
def test_metrics_collector_set_gauge(collector: MetricsCollector) -> None:
    """set_gauge() overwrites the previous value rather than accumulating."""
    collector.set_gauge("thegent_circuit_breaker_open", {"provider": "openai"}, 1.0)
    collector.set_gauge("thegent_circuit_breaker_open", {"provider": "openai"}, 0.0)

    text = collector.render_text()
    assert 'thegent_circuit_breaker_open{provider="openai"} 0' in text


# ---------------------------------------------------------------------------
# Histogram
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-OBS-034")
def test_metrics_collector_observe_histogram(collector: MetricsCollector) -> None:
    """observe() stores observations; render produces _bucket, _count, _sum."""
    collector.observe(
        "thegent_request_duration_seconds",
        {"model": "gpt-4o", "provider": "openai"},
        0.3,
    )
    collector.observe(
        "thegent_request_duration_seconds",
        {"model": "gpt-4o", "provider": "openai"},
        0.7,
    )

    text = collector.render_text()
    assert "thegent_request_duration_seconds_count" in text
    assert "thegent_request_duration_seconds_sum" in text
    assert "thegent_request_duration_seconds_bucket" in text


# ---------------------------------------------------------------------------
# record_request — success path
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-OBS-034")
def test_record_request_success(collector: MetricsCollector) -> None:
    """record_request() with status='success' increments all relevant counters."""
    collector.record_request(
        model="gpt-4o",
        provider="openai",
        status="success",
        duration_sec=0.5,
        prompt_tokens=100,
        completion_tokens=50,
        cost_usd=0.002,
    )

    text = collector.render_text()

    # requests_total
    assert (
        'thegent_requests_total{model="gpt-4o",provider="openai",status="success"} 1'
        in text
    )
    # prompt tokens
    assert (
        'thegent_tokens_total{model="gpt-4o",provider="openai",type="prompt"} 100'
        in text
    )
    # completion tokens
    assert (
        'thegent_tokens_total{model="gpt-4o",provider="openai",type="completion"} 50'
        in text
    )
    # cost
    assert 'thegent_cost_usd_total{model="gpt-4o",provider="openai"} 0.002' in text
    # duration histogram present
    assert "thegent_request_duration_seconds_count" in text
    # no errors counter for a success
    assert "thegent_errors_total" not in text


# ---------------------------------------------------------------------------
# record_request — error path
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-OBS-034")
def test_record_request_error(collector: MetricsCollector) -> None:
    """record_request() with status='error' increments thegent_errors_total."""
    collector.record_request(
        model="gpt-4o",
        provider="openai",
        status="error",
        duration_sec=1.2,
        error_type="RateLimitError",
    )

    text = collector.render_text()

    assert (
        'thegent_requests_total{model="gpt-4o",provider="openai",status="error"} 1'
        in text
    )
    assert (
        'thegent_errors_total{error_type="RateLimitError",model="gpt-4o",provider="openai"} 1'
        in text
    )


# ---------------------------------------------------------------------------
# record_request — circuit_open path
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-OBS-034")
def test_record_request_circuit_open(collector: MetricsCollector) -> None:
    """record_request() with status='circuit_open' is recorded correctly."""
    collector.record_request(
        model="claude-opus-4-6",
        provider="anthropic",
        status="circuit_open",
        duration_sec=0.0,
    )

    text = collector.render_text()
    assert (
        'thegent_requests_total{model="claude-opus-4-6",provider="anthropic",status="circuit_open"} 1'
        in text
    )


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-OBS-034")
def test_record_cache_hit(collector: MetricsCollector) -> None:
    """record_cache_hit() increments thegent_cache_hits_total."""
    collector.record_cache_hit("exact")
    collector.record_cache_hit("exact")

    text = collector.render_text()
    assert 'thegent_cache_hits_total{cache_type="exact"} 2' in text


@pytest.mark.requirement("FR-OBS-034")
def test_record_cache_miss(collector: MetricsCollector) -> None:
    """record_cache_miss() increments thegent_cache_misses_total."""
    collector.record_cache_miss("semantic")

    text = collector.render_text()
    assert 'thegent_cache_misses_total{cache_type="semantic"} 1' in text


# ---------------------------------------------------------------------------
# Circuit breaker gauge
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-OBS-034")
def test_set_circuit_breaker_open(collector: MetricsCollector) -> None:
    """set_circuit_breaker(is_open=True) sets gauge to 1."""
    collector.set_circuit_breaker("openai", is_open=True)

    text = collector.render_text()
    assert 'thegent_circuit_breaker_open{provider="openai"} 1' in text


@pytest.mark.requirement("FR-OBS-034")
def test_set_circuit_breaker_closed(collector: MetricsCollector) -> None:
    """set_circuit_breaker(is_open=False) sets gauge to 0."""
    collector.set_circuit_breaker("openai", is_open=True)
    collector.set_circuit_breaker("openai", is_open=False)

    text = collector.render_text()
    assert 'thegent_circuit_breaker_open{provider="openai"} 0' in text


# ---------------------------------------------------------------------------
# render_text format verification
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-OBS-034")
def test_render_text_counter_format(collector: MetricsCollector) -> None:
    """Counter output must have '# HELP', '# TYPE counter', and a metric line."""
    collector.inc(
        "thegent_requests_total", {"model": "m", "provider": "p", "status": "success"}
    )

    text = collector.render_text()
    assert "# HELP thegent_requests_total" in text
    assert "# TYPE thegent_requests_total counter" in text
    assert "thegent_requests_total{" in text


@pytest.mark.requirement("FR-OBS-034")
def test_render_text_gauge_format(collector: MetricsCollector) -> None:
    """Gauge output must have '# HELP', '# TYPE gauge', and a metric line."""
    collector.set_gauge("thegent_circuit_breaker_open", {"provider": "openai"}, 1.0)

    text = collector.render_text()
    assert "# HELP thegent_circuit_breaker_open" in text
    assert "# TYPE thegent_circuit_breaker_open gauge" in text
    assert "thegent_circuit_breaker_open{" in text


@pytest.mark.requirement("FR-OBS-034")
def test_render_text_histogram_format(collector: MetricsCollector) -> None:
    """Histogram output must include _bucket, _count, and _sum lines."""
    collector.observe(
        "thegent_request_duration_seconds", {"model": "m", "provider": "p"}, 0.1
    )

    text = collector.render_text()
    assert "thegent_request_duration_seconds_bucket{" in text
    assert 'le="+Inf"' in text
    assert "thegent_request_duration_seconds_count{" in text
    assert "thegent_request_duration_seconds_sum{" in text
    assert "# HELP thegent_request_duration_seconds" in text
    assert "# TYPE thegent_request_duration_seconds histogram" in text


@pytest.mark.requirement("FR-OBS-034")
def test_render_text_label_sorting(collector: MetricsCollector) -> None:
    """Labels in metric lines must appear in alphabetical order."""
    # Insert labels in reverse alphabetical order; output must still sort them
    collector.inc(
        "thegent_requests_total",
        {"status": "success", "provider": "openai", "model": "gpt-4o"},
    )

    text = collector.render_text()
    # model < provider < status alphabetically
    assert (
        'thegent_requests_total{model="gpt-4o",provider="openai",status="success"}'
        in text
    )


@pytest.mark.requirement("WL-196")
def test_record_autosync_cycle_and_export_file(
    collector: MetricsCollector, tmp_path: Path
) -> None:
    """Autosync metrics are emitted and can be exported to a text file."""
    collector.record_autosync_cycle(items_count=5, ignored_count=2, had_error=False)
    collector.record_autosync_connector_operation(
        connector="github",
        direction="write",
        result="success",
        duration_seconds=0.12,
    )
    collector.record_autosync_circuit_open(connector="linear", direction="read")

    output_path = tmp_path / "metrics.prom"
    collector.export_text_file(output_path)
    text = output_path.read_text(encoding="utf-8")

    assert "thegent_autosync_cycles_total 1" in text
    assert 'thegent_autosync_items_total{kind="ignored"} 2' in text
    assert (
        'thegent_autosync_connector_operations_total{connector="github",direction="write",result="success"} 1'
        in text
    )
    assert (
        'thegent_autosync_circuit_open_total{connector="linear",direction="read"} 1'
        in text
    )


@pytest.mark.requirement("WL-159")
def test_record_board_sync_cycle(collector: MetricsCollector) -> None:
    """Board sync cycle counters and duration histogram are exported."""
    collector.record_board_sync_cycle(
        source="github",
        status="success",
        duration_seconds=0.42,
    )

    text = collector.render_text()
    assert 'thegent_board_sync_cycles_total{source="github",status="success"} 1' in text
    assert "thegent_board_sync_cycle_duration_seconds_count" in text


@pytest.mark.requirement("WL-160")
def test_record_autosync_cycle_result(collector: MetricsCollector) -> None:
    """Autosync cycle outcomes emit labeled counters and duration histograms."""
    collector.record_autosync_cycle_result(status="failed", duration_seconds=0.31)

    text = collector.render_text()
    assert 'thegent_autosync_cycle_outcomes_total{status="failed"} 1' in text
    assert "thegent_autosync_cycle_duration_seconds_count" in text


@pytest.mark.requirement("FR-OBS-034")
def test_render_text_empty_metrics(collector: MetricsCollector) -> None:
    """render_text() on an empty collector must return a string without crashing."""
    text = collector.render_text()
    assert isinstance(text, str)
    # No metrics registered — output is empty or just whitespace/newline
    assert text.strip() == ""


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-OBS-034")
def test_singleton_same_instance() -> None:
    """get_metrics_collector() must return the same object on repeated calls."""
    a = get_metrics_collector()
    b = get_metrics_collector()
    assert a is b


@pytest.mark.requirement("FR-OBS-034")
def test_reset_metrics_collector() -> None:
    """reset_metrics_collector() must cause get_metrics_collector() to return a new instance."""
    first = get_metrics_collector()
    reset_metrics_collector()
    second = get_metrics_collector()
    assert first is not second
