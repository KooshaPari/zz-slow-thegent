"""Tests for perf_budget module (P-090 — SOTA hardening audit).

Covers:
  - PerformanceBudgetError contract
  - check_module_load_budget success / failure / idempotency
  - check_memory_budget success / failure / platform handling
  - get_perf_summary shape and correctness
  - budget_context timing and memory tracking
  - Thread-safety under concurrent checks
"""

from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch

import pytest

from thegent.infra.perf_budget import (
    BudgetResult,
    PerformanceBudgetError,
    _current_rss_bytes,
    budget_context,
    check_memory_budget,
    check_module_load_budget,
    get_perf_summary,
)

# ---------------------------------------------------------------------------
# Fixtures — reset module-level state between tests
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_perf_state():
    """Reset global perf_budget state before each test."""
    import thegent.infra.perf_budget as mod

    with mod._lock:
        mod._checked_modules.clear()
        mod._violations.clear()
        mod._peak_memory = 0
    yield
    with mod._lock:
        mod._checked_modules.clear()
        mod._violations.clear()
        mod._peak_memory = 0


# ---------------------------------------------------------------------------
# PerformanceBudgetError contract
# ---------------------------------------------------------------------------


class TestPerformanceBudgetError:
    """Verify the custom exception carries all expected fields."""

    def test_load_time_fields(self):
        err = PerformanceBudgetError(
            message="too slow",
            module_name="json",
            actual_ms=120.5,
            budget_ms=50.0,
        )
        assert err.module_name == "json"
        assert err.actual_ms == 120.5
        assert err.budget_ms == 50.0
        assert err.actual_bytes is None
        assert err.budget_bytes is None
        assert err.label is None
        assert str(err) == "too slow"

    def test_memory_fields(self):
        err = PerformanceBudgetError(
            message="oom",
            actual_bytes=20_000_000,
            budget_bytes=10_000_000,
            label="post-import",
        )
        assert err.actual_bytes == 20_000_000
        assert err.budget_bytes == 10_000_000
        assert err.label == "post-import"
        assert err.module_name is None
        assert err.actual_ms is None
        assert err.budget_ms is None

    def test_is_exception_subclass(self):
        err = PerformanceBudgetError(message="fail")
        assert isinstance(err, Exception)


# ---------------------------------------------------------------------------
# check_module_load_budget
# ---------------------------------------------------------------------------


class TestCheckModuleLoadBudget:
    """Load-time gate: success, failure, and idempotency."""

    def test_success_within_budget(self):
        """stdlib 'json' should load well within 1 000 ms."""
        ms = check_module_load_budget("json", max_load_ms=1000.0)
        assert ms >= 0
        assert ms < 1000.0

    def test_failure_exceeds_budget(self):
        """Mock a slow import to trigger PerformanceBudgetError."""
        with patch(
            "thegent.infra.perf_budget.time.perf_counter", side_effect=[0.0, 100.0]
        ):
            with pytest.raises(PerformanceBudgetError, match="exceeds budget"):
                check_module_load_budget("json", max_load_ms=50.0)

    def test_idempotent_caching(self):
        """Second call for the same module returns cached result."""
        import thegent.infra.perf_budget as mod

        ms1 = check_module_load_budget("json", max_load_ms=1000.0)
        # Directly verify it's in the cache
        assert "json" in mod._checked_modules
        ms2 = check_module_load_budget("json", max_load_ms=1000.0)
        assert ms1 == ms2

    def test_cached_exceeding_raises(self):
        """If a module was slow, cached repeat still raises."""
        import thegent.infra.perf_budget as mod

        with mod._lock:
            mod._checked_modules["slow_mod"] = 999.0

        with pytest.raises(PerformanceBudgetError, match="cached"):
            check_module_load_budget("slow_mod", max_load_ms=50.0)


# ---------------------------------------------------------------------------
# check_memory_budget
# ---------------------------------------------------------------------------


class TestCheckMemoryBudget:
    """Memory gate: success, failure, and platform handling."""

    def test_success_within_budget(self):
        """Real RSS is typically < 100 MB — should pass."""
        rss = check_memory_budget("baseline", max_bytes=500_000_000)
        assert rss > 0

    def test_failure_exceeds_budget(self):
        """Mock RSS well above budget."""
        with patch(
            "thegent.infra.perf_budget._current_rss_bytes", return_value=20_000_000
        ):
            with pytest.raises(PerformanceBudgetError, match="Memory budget exceeded"):
                check_memory_budget("big-block", max_bytes=10_000_000)

    def test_failure_fields(self):
        """PerformanceBudgetError should carry actual/budget bytes and label."""
        with patch("thegent.infra.perf_budget._current_rss_bytes", return_value=99_999):
            with pytest.raises(PerformanceBudgetError) as exc_info:
                check_memory_budget("my-label", max_bytes=1)
            err = exc_info.value
            assert err.actual_bytes == 99_999
            assert err.budget_bytes == 1
            assert err.label == "my-label"

    def test_platform_linux_kb_conversion(self):
        """On Linux ru_maxrss is in KB — verify conversion."""
        usage_mock = MagicMock()
        usage_mock.ru_maxrss = 1024  # 1 KB
        with patch("thegent.infra.perf_budget.sys.platform", "linux"):
            with patch(
                "thegent.infra.perf_budget.resource.getrusage", return_value=usage_mock
            ):
                rss = _current_rss_bytes()
                assert rss == 1024 * 1024  # 1 MB in bytes

    def test_platform_darwin_bytes(self):
        """On macOS ru_maxrss is already in bytes."""
        usage_mock = MagicMock()
        usage_mock.ru_maxrss = 2_000_000
        with patch("thegent.infra.perf_budget.sys.platform", "darwin"):
            with patch(
                "thegent.infra.perf_budget.resource.getrusage", return_value=usage_mock
            ):
                rss = _current_rss_bytes()
                assert rss == 2_000_000


# ---------------------------------------------------------------------------
# get_perf_summary
# ---------------------------------------------------------------------------


class TestGetPerfSummary:
    """Verify summary shape and correctness."""

    def test_shape(self):
        summary = get_perf_summary()
        assert "checked_modules" in summary
        assert "total_load_ms" in summary
        assert "peak_memory_bytes" in summary
        assert "violations" in summary
        assert isinstance(summary["checked_modules"], dict)
        assert isinstance(summary["violations"], list)

    def test_after_load_check(self):
        check_module_load_budget("json", max_load_ms=1000.0)
        summary = get_perf_summary()
        assert "json" in summary["checked_modules"]
        assert summary["total_load_ms"] > 0

    def test_violations_recorded(self):
        with patch(
            "thegent.infra.perf_budget._current_rss_bytes", return_value=50_000_000
        ):
            with pytest.raises(PerformanceBudgetError):
                check_memory_budget("over", max_bytes=10_000_000)
        summary = get_perf_summary()
        assert len(summary["violations"]) == 1
        assert summary["violations"][0]["type"] == "memory"


# ---------------------------------------------------------------------------
# budget_context
# ---------------------------------------------------------------------------


class TestBudgetContext:
    """Context manager: timing, memory, and result shape."""

    def test_yields_budget_result(self):
        with budget_context("test-block") as result:
            pass
        assert isinstance(result, BudgetResult)
        assert result.label == "test-block"

    def test_elapsed_ms_non_negative(self):
        with budget_context("timing") as result:
            pass
        assert result.elapsed_ms >= 0

    def test_peak_memory_positive(self):
        with budget_context("mem") as result:
            pass
        assert result.peak_memory_bytes > 0

    def test_within_budget_default_true(self):
        with budget_context("default") as result:
            pass
        assert result.within_budget is True


# ---------------------------------------------------------------------------
# Thread-safety
# ---------------------------------------------------------------------------


class TestThreadSafety:
    """Concurrent checks should not corrupt shared state."""

    def test_concurrent_load_checks(self):
        """Multiple threads checking the same module should not crash."""
        import thegent.infra.perf_budget as mod

        errors: list[Exception] = []

        def _worker():
            try:
                check_module_load_budget("json", max_load_ms=10000.0)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=_worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread errors: {errors}"
        assert "json" in mod._checked_modules

    def test_concurrent_memory_checks(self):
        """Multiple threads calling check_memory_budget should not crash."""
        errors: list[Exception] = []

        def _worker():
            try:
                check_memory_budget("thread-test", max_bytes=10_000_000_000)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=_worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread errors: {errors}"
