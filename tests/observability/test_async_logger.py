"""Tests for GW-39: AsyncObservabilityLogger.

# @trace FR-OBS-039
"""

from __future__ import annotations

import threading
import time

import pytest

from thegent.observability.async_logger import (
    AsyncObservabilityLogger,
    ObservabilityEvent,
    _default_log_handler,
    get_obs_logger,
    reset_obs_logger,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _wait_for(condition: threading.Event, timeout: float = 2.0) -> bool:
    """Wait up to timeout seconds for condition to be set. Returns True if set."""
    return condition.wait(timeout=timeout)


def _make_event(
    event_type: str = "request_complete",
    model: str = "gpt-4o",
    provider: str = "openai",
    event_id: str = "tg-abc12345",
) -> ObservabilityEvent:
    return ObservabilityEvent(
        timestamp=time.time(),
        event_type=event_type,
        model=model,
        provider=provider,
        event_id=event_id,
        metadata={"status": "ok"},
    )


# ---------------------------------------------------------------------------
# GW-39: AsyncObservabilityLogger
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-OBS-039")
def test_async_logger_processes_event() -> None:
    """log() enqueues an event; the background worker calls the handler."""
    received: list[ObservabilityEvent] = []
    done = threading.Event()

    def handler(ev: ObservabilityEvent) -> None:
        received.append(ev)
        done.set()

    logger = AsyncObservabilityLogger(handlers=[handler])
    try:
        event = _make_event()
        logger.log(event)
        assert _wait_for(done), "Handler was not called within timeout"
        assert len(received) == 1
        assert received[0].event_id == event.event_id
    finally:
        logger.stop()


@pytest.mark.requirement("FR-OBS-039")
def test_async_logger_log_request_convenience() -> None:
    """log_request() enqueues a request_complete event that the handler receives."""
    received: list[ObservabilityEvent] = []
    done = threading.Event()

    def handler(ev: ObservabilityEvent) -> None:
        received.append(ev)
        done.set()

    logger = AsyncObservabilityLogger(handlers=[handler])
    try:
        logger.log_request(
            model="claude-sonnet-4-6",
            provider="anthropic",
            event_id="tg-deadbeef",
            status="ok",
            duration_sec=0.42,
            prompt_tokens=100,
            completion_tokens=50,
            cost_usd=0.001,
            error_type="",
        )
        assert _wait_for(done), "Handler was not called within timeout"
        assert len(received) == 1
        ev = received[0]
        assert ev.event_type == "request_complete"
        assert ev.model == "claude-sonnet-4-6"
        assert ev.provider == "anthropic"
        assert ev.event_id == "tg-deadbeef"
        assert ev.metadata["status"] == "ok"
        assert ev.metadata["duration_sec"] == pytest.approx(0.42)
    finally:
        logger.stop()


@pytest.mark.requirement("FR-OBS-039")
def test_async_logger_queue_full_drops_silently() -> None:
    """When the queue is full, log() drops events without raising an exception."""
    # Use a tiny queue size so we can fill it easily
    logger = AsyncObservabilityLogger.__new__(AsyncObservabilityLogger)
    import queue as _queue

    logger._queue = _queue.Queue(maxsize=2)
    logger._handlers = [_default_log_handler]
    logger._running = threading.Event()
    logger._running.set()
    # Do NOT start the worker thread so the queue stays full
    logger._thread = threading.Thread(
        target=lambda: None, daemon=True, name="obs-logger-noop"
    )

    event = _make_event()
    # Fill the queue
    logger._queue.put_nowait(event)
    logger._queue.put_nowait(event)
    # This should drop silently, not raise
    logger.log(event)
    logger.log(event)
    # Verify queue size didn't exceed maxsize
    assert logger._queue.qsize() == 2
    diag = logger.diagnostics()
    assert diag["dropped_events"] == 2


@pytest.mark.requirement("FR-OBS-039")
def test_async_logger_handler_error_doesnt_kill_worker() -> None:
    """A handler that raises must not kill the background worker."""
    second_event_received = threading.Event()
    call_count = [0]

    def flaky_handler(_ev: ObservabilityEvent) -> None:
        call_count[0] += 1
        if call_count[0] == 1:
            raise RuntimeError("handler boom")
        second_event_received.set()

    logger = AsyncObservabilityLogger(handlers=[flaky_handler])
    try:
        logger.log(_make_event(event_id="tg-first111"))
        logger.log(_make_event(event_id="tg-second22"))
        assert _wait_for(second_event_received), "Worker died after handler error"
        assert call_count[0] == 2
        diag = logger.diagnostics()
        assert diag["handler_failures"] >= 1
    finally:
        logger.stop()


@pytest.mark.requirement("FR-OBS-039")
def test_async_logger_queue_size() -> None:
    """queue_size() returns a non-negative integer."""
    logger = AsyncObservabilityLogger()
    try:
        size = logger.queue_size()
        assert isinstance(size, int)
        assert size >= 0
    finally:
        logger.stop()


@pytest.mark.requirement("FR-OBS-039")
def test_async_logger_stop() -> None:
    """stop() terminates the worker thread within the given timeout."""
    logger = AsyncObservabilityLogger()
    logger.stop(timeout=3.0)
    # After stop, the thread should no longer be alive
    assert not logger._thread.is_alive()


@pytest.mark.requirement("FR-OBS-039")
def test_default_log_handler_doesnt_raise() -> None:
    """_default_log_handler must not raise for any well-formed event."""
    event = _make_event()
    # Should complete without raising
    _default_log_handler(event)


@pytest.mark.requirement("FR-OBS-039")
def test_singleton_returns_same_instance() -> None:
    """get_obs_logger() must return the same instance on repeated calls."""
    reset_obs_logger()
    try:
        inst1 = get_obs_logger()
        inst2 = get_obs_logger()
        assert inst1 is inst2
    finally:
        reset_obs_logger()


@pytest.mark.requirement("FR-OBS-039")
def test_reset_obs_logger() -> None:
    """reset_obs_logger() must cause the next get_obs_logger() call to create a new instance."""
    reset_obs_logger()
    try:
        inst1 = get_obs_logger()
        reset_obs_logger()
        inst2 = get_obs_logger()
        assert inst1 is not inst2
    finally:
        reset_obs_logger()
