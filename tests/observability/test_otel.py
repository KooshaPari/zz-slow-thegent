"""Tests for GW-37: OTel OTLP span export.

# @trace FR-OBS-037
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

import thegent.observability.otel as otel_mod
from thegent.observability.otel import (
    OtelConfig,
    _NoOpSpan,
    configure_otel,
    finish_llm_span,
    get_otel_config,
    get_tracer,
    record_llm_call,
    reset_otel_config,
    start_llm_span,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset singleton and tracer state before and after every test."""
    reset_otel_config()
    yield
    reset_otel_config()


# ---------------------------------------------------------------------------
# 1. Import guard
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-OBS-037")
def test_otel_available_or_noop() -> None:
    """Module imports without error regardless of opentelemetry availability."""
    # The fact that this test runs means the import succeeded.
    assert hasattr(otel_mod, "_OTEL_AVAILABLE")
    assert isinstance(otel_mod._OTEL_AVAILABLE, bool)


# ---------------------------------------------------------------------------
# 2. No-op when unavailable
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-OBS-037")
def test_record_llm_call_noop_when_unavailable() -> None:
    """record_llm_call does not raise when _OTEL_AVAILABLE is False."""
    with patch.object(otel_mod, "_OTEL_AVAILABLE", False):
        # Must not raise
        record_llm_call(
            model="gpt-4o",
            provider="openai",
            prompt_tokens=10,
            completion_tokens=5,
        )


# ---------------------------------------------------------------------------
# 3. OtelConfig defaults
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-OBS-037")
def test_otel_config_defaults() -> None:
    """OtelConfig has the correct default field values."""
    cfg = OtelConfig()
    assert cfg.endpoint == "http://localhost:4317"
    assert cfg.service_name == "thegent-gateway"
    assert cfg.enabled is True
    assert cfg.insecure is True


# ---------------------------------------------------------------------------
# 4. configure_otel stores config
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-OBS-037")
def test_configure_otel_sets_config() -> None:
    """configure_otel fails loudly when enabled but OTEL deps are unavailable."""
    cfg = OtelConfig(endpoint="http://collector:4317", service_name="my-service")
    with patch.object(otel_mod, "_OTEL_AVAILABLE", False):
        with pytest.raises(RuntimeError, match="OTel bootstrap failed"):
            configure_otel(cfg)

    stored = get_otel_config()
    assert stored.endpoint == "http://collector:4317"
    assert stored.service_name == "my-service"


# ---------------------------------------------------------------------------
# 5. Singleton identity
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-OBS-037")
def test_get_otel_config_singleton() -> None:
    """get_otel_config returns the same instance on repeated calls."""
    a = get_otel_config()
    b = get_otel_config()
    assert a is b


# ---------------------------------------------------------------------------
# 6. Reset causes new instance
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-OBS-037")
def test_reset_otel_config() -> None:
    """reset_otel_config causes the next get_otel_config call to return a new instance."""
    first = get_otel_config()
    reset_otel_config()
    second = get_otel_config()
    assert first is not second


# ---------------------------------------------------------------------------
# 7. finish_llm_span with None is safe
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-OBS-037")
def test_finish_llm_span_with_none_is_safe() -> None:
    """finish_llm_span(None, ...) must not raise."""
    finish_llm_span(
        None,
        prompt_tokens=10,
        completion_tokens=5,
        finish_reason="stop",
        cost_usd=0.001,
        cache_hit=False,
        status_code=200,
        error="",
    )


# ---------------------------------------------------------------------------
# 8. Complete no-op path (no otel)
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-OBS-037")
def test_record_llm_call_no_error_no_otel() -> None:
    """When otel is unavailable, record_llm_call is a silent no-op end-to-end."""
    with patch.object(otel_mod, "_OTEL_AVAILABLE", False):
        with patch.object(otel_mod, "_tracer", None):
            record_llm_call(
                model="claude-opus-4-6",
                provider="anthropic",
                event_id="evt-abc123",
                prompt_tokens=200,
                completion_tokens=50,
                finish_reason="stop",
                cost_usd=0.005,
                cache_hit=True,
                status_code=200,
                error="",
                duration_sec=1.23,
            )
    # Reaching here without exception means the test passes


# ---------------------------------------------------------------------------
# 9. Custom endpoint stored correctly
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-OBS-037")
def test_otel_config_custom_endpoint() -> None:
    """Custom endpoint is stored and retrievable from OtelConfig."""
    cfg = OtelConfig(endpoint="http://my-collector.internal:4317")
    assert cfg.endpoint == "http://my-collector.internal:4317"

    with patch.object(otel_mod, "_OTEL_AVAILABLE", False):
        with pytest.raises(RuntimeError, match="OTel bootstrap failed"):
            configure_otel(cfg)

    stored = get_otel_config()
    assert stored.endpoint == "http://my-collector.internal:4317"


# ---------------------------------------------------------------------------
# 10. record_llm_call with error string does not raise
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-OBS-037")
def test_record_llm_call_with_error() -> None:
    """An error string passed to record_llm_call must not cause any exception."""
    with patch.object(otel_mod, "_OTEL_AVAILABLE", False):
        record_llm_call(
            model="gemini-3-flash",
            provider="google",
            status_code=500,
            error="Internal server error",
        )


# ---------------------------------------------------------------------------
# Bonus: start_llm_span returns _NoOpSpan when tracer is None
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-OBS-037")
def test_start_llm_span_returns_noop_when_no_tracer() -> None:
    """start_llm_span returns a _NoOpSpan when otel is unavailable."""
    with patch.object(otel_mod, "_OTEL_AVAILABLE", False):
        with patch.object(otel_mod, "_tracer", None):
            span = start_llm_span("gpt-4o", "openai")
    assert isinstance(span, _NoOpSpan)


# ---------------------------------------------------------------------------
# Bonus: finish_llm_span with _NoOpSpan does not raise
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-OBS-037")
def test_finish_llm_span_with_noop_span_is_safe() -> None:
    """finish_llm_span with a _NoOpSpan completes without error."""
    span = _NoOpSpan()
    finish_llm_span(
        span,
        prompt_tokens=1,
        completion_tokens=1,
        finish_reason="stop",
        cost_usd=0.0,
        cache_hit=False,
        status_code=200,
        error="",
    )


# ---------------------------------------------------------------------------
# Bonus: get_tracer returns None before configure_otel is called
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-OBS-037")
def test_get_tracer_before_configure_returns_none() -> None:
    """get_tracer returns None when configure_otel has not been called."""
    assert get_tracer() is None


# ---------------------------------------------------------------------------
# Bonus: configure_otel with enabled=False stays in no-op mode
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-OBS-037")
def test_configure_otel_disabled_stays_noop() -> None:
    """When config.enabled=False, configure_otel does not set up a tracer."""
    cfg = OtelConfig(enabled=False)
    with patch.object(otel_mod, "_OTEL_AVAILABLE", True):
        configure_otel(cfg)
    # Tracer should remain None since enabled=False
    assert get_tracer() is None


# ---------------------------------------------------------------------------
# Bonus: OtelConfig with insecure=False
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-OBS-037")
def test_otel_config_insecure_false() -> None:
    """OtelConfig can be created with insecure=False."""
    cfg = OtelConfig(insecure=False)
    assert cfg.insecure is False


# ---------------------------------------------------------------------------
# Bonus: record_llm_call with cache_hit=True does not raise
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-OBS-037")
def test_record_llm_call_cache_hit_true() -> None:
    """cache_hit=True is handled without error."""
    with patch.object(otel_mod, "_OTEL_AVAILABLE", False):
        record_llm_call(
            model="gpt-4o",
            provider="openai",
            cache_hit=True,
            cost_usd=0.0,
        )


# ---------------------------------------------------------------------------
# Bonus: _NoOpSpan context manager protocol
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-OBS-037")
def test_noop_span_context_manager() -> None:
    """_NoOpSpan supports the context manager protocol."""
    with _NoOpSpan() as span:
        assert isinstance(span, _NoOpSpan)
        span.set_attribute("key", "value")
        span.end()
