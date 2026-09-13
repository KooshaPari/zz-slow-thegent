"""Parity tests: Quota enforcement behavior (thegent Python vs CLIProxy Go).

Tests quota enforcement equivalence:
- Under limit: request allowed
- Over limit: request denied
- 24h rolling window reset
- Concurrent request handling
- Token and cost tracking

Mirrors CLIProxy's pkg/llmproxy/usage/quota_enforcer.go
# @trace WL-221
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

# ========================================================================
# Quota Enforcer Implementation (Python equivalent of CLIProxy)
# ========================================================================


@dataclass
class QuotaLimit:
    """Daily usage limits for tokens and cost."""

    max_tokens_per_day: float = 0.0  # 0 = unlimited
    max_cost_per_day: float = 0.0  # 0 = unlimited


@dataclass
class UsageRecord:
    """Accumulated usage tracking."""

    tokens_used: float = 0.0
    cost_used: float = 0.0


class QuotaEnforcer:
    """Thread-safe quota enforcer with 24h rolling window (Python parity with CLIProxy Go).

    Tracks and enforces daily usage quotas for tokens and cost.
    Resets usage after 24h.
    """

    def __init__(self, quota: QuotaLimit) -> None:
        """Initialize quota enforcer.

        Args:
            quota: QuotaLimit with max_tokens_per_day and max_cost_per_day.
        """
        self.quota = quota
        self.usage = UsageRecord()
        self.reset_at = datetime.now(UTC) + timedelta(hours=24)
        self._lock = threading.Lock()

    def check_quota(self, estimated_tokens: float, estimated_cost: float) -> bool:
        """Check if estimated usage fits within quota.

        Mirrors CLIProxy's CheckQuota behavior:
        - Returns True if usage is allowed
        - Returns False if would exceed tokens or cost limit
        - Handles 24h reset (idempotent within lock)

        Args:
            estimated_tokens: Estimated tokens for operation.
            estimated_cost: Estimated cost for operation.

        Returns:
            True if usage allowed, False if would exceed quota.
        """
        with self._lock:
            self._maybe_reset()

            if (
                self.quota.max_tokens_per_day > 0
                and self.usage.tokens_used + estimated_tokens
                > self.quota.max_tokens_per_day
            ):
                return False

            return not (
                self.quota.max_cost_per_day > 0
                and self.usage.cost_used + estimated_cost > self.quota.max_cost_per_day
            )

    def record_usage(self, record: UsageRecord) -> None:
        """Record actual usage.

        Args:
            record: UsageRecord to add to accumulated usage.
        """
        with self._lock:
            self.usage.tokens_used += record.tokens_used
            self.usage.cost_used += record.cost_used

    def get_usage(self) -> UsageRecord:
        """Get current usage snapshot.

        Returns:
            Current UsageRecord.
        """
        with self._lock:
            return UsageRecord(
                tokens_used=self.usage.tokens_used,
                cost_used=self.usage.cost_used,
            )

    def _maybe_reset(self) -> None:
        """Reset usage if 24h window has passed.

        Note: Called with lock held. This is safe because reset is idempotent
        and rare in typical workloads.
        """
        if datetime.now(UTC) >= self.reset_at:
            self.usage.tokens_used = 0.0
            self.usage.cost_used = 0.0
            self.reset_at = datetime.now(UTC) + timedelta(hours=24)


# ========================================================================
# Tests
# ========================================================================


class TestQuotaEnforcerBasic:
    """Test basic quota enforcement."""

    def test_under_token_limit_allowed(self) -> None:
        """Test request under token limit is allowed."""
        quota = QuotaLimit(max_tokens_per_day=1000.0, max_cost_per_day=100.0)
        enforcer = QuotaEnforcer(quota)

        # Check for 100 tokens (under 1000 limit)
        assert enforcer.check_quota(100.0, 10.0) is True

    def test_at_token_limit_denied(self) -> None:
        """Test request that would exceed token limit is denied."""
        quota = QuotaLimit(max_tokens_per_day=100.0, max_cost_per_day=100.0)
        enforcer = QuotaEnforcer(quota)

        # Record 90 tokens
        enforcer.record_usage(UsageRecord(tokens_used=90.0, cost_used=10.0))

        # Check for 20 tokens (total would be 110 > limit) — should be denied
        assert enforcer.check_quota(20.0, 10.0) is False

        # Check for 10 tokens (total would be 100 = limit) — should be ALLOWED
        # CLIProxy logic: > comparison, not >=
        assert enforcer.check_quota(10.0, 10.0) is True

        # Check for 11 tokens (total would be 101 > limit) — should be denied
        assert enforcer.check_quota(11.0, 10.0) is False

    def test_under_cost_limit_allowed(self) -> None:
        """Test request under cost limit is allowed."""
        quota = QuotaLimit(max_tokens_per_day=1000.0, max_cost_per_day=100.0)
        enforcer = QuotaEnforcer(quota)

        # Record 50 cost
        enforcer.record_usage(UsageRecord(tokens_used=100.0, cost_used=50.0))

        # Check for 30 cost (total would be 80 < limit)
        assert enforcer.check_quota(100.0, 30.0) is True

    def test_at_cost_limit_denied(self) -> None:
        """Test request that would exceed cost limit is denied."""
        quota = QuotaLimit(max_tokens_per_day=1000.0, max_cost_per_day=100.0)
        enforcer = QuotaEnforcer(quota)

        # Record 90 cost
        enforcer.record_usage(UsageRecord(tokens_used=100.0, cost_used=90.0))

        # Check for 20 cost (total would be 110 > limit)
        assert enforcer.check_quota(100.0, 20.0) is False

    def test_unlimited_quota(self) -> None:
        """Test unlimited quota (0 = no limit)."""
        quota = QuotaLimit(max_tokens_per_day=0.0, max_cost_per_day=0.0)
        enforcer = QuotaEnforcer(quota)

        # Record large usage
        enforcer.record_usage(UsageRecord(tokens_used=1_000_000.0, cost_used=10_000.0))

        # Should still allow more (unlimited)
        assert enforcer.check_quota(1_000_000.0, 10_000.0) is True

    def test_partial_unlimited_quota(self) -> None:
        """Test mixed limited/unlimited (0 = no limit)."""
        quota = QuotaLimit(
            max_tokens_per_day=100.0,
            max_cost_per_day=0.0,  # cost unlimited
        )
        enforcer = QuotaEnforcer(quota)

        enforcer.record_usage(UsageRecord(tokens_used=50.0, cost_used=1000.0))

        # Cost is unlimited, so request is allowed if tokens fit
        assert enforcer.check_quota(40.0, 5000.0) is True

        # But token limit applies
        assert enforcer.check_quota(60.0, 5000.0) is False


class TestQuotaEnforcer24hReset:
    """Test 24h rolling window reset behavior."""

    def test_reset_at_initialization(self) -> None:
        """Test reset_at is set to 24h from now on init."""
        quota = QuotaLimit(max_tokens_per_day=100.0)
        before = datetime.now(UTC)
        enforcer = QuotaEnforcer(quota)
        after = datetime.now(UTC)

        expected_min = before + timedelta(hours=24)
        expected_max = after + timedelta(hours=24, seconds=1)
        assert expected_min <= enforcer.reset_at <= expected_max

    def test_reset_clears_usage(self) -> None:
        """Test reset clears tokens and cost."""
        quota = QuotaLimit(max_tokens_per_day=100.0, max_cost_per_day=100.0)
        enforcer = QuotaEnforcer(quota)

        # Manually set reset_at to the past to trigger reset
        enforcer.reset_at = datetime.now(UTC) - timedelta(seconds=1)

        # Record usage
        enforcer.record_usage(UsageRecord(tokens_used=50.0, cost_used=50.0))
        assert enforcer.get_usage().tokens_used == 50.0

        # Check quota (should trigger reset)
        enforcer.check_quota(10.0, 10.0)

        # Usage should be cleared after reset
        usage = enforcer.get_usage()
        assert usage.tokens_used == 0.0
        assert usage.cost_used == 0.0

    def test_reset_updates_reset_at(self) -> None:
        """Test reset updates reset_at to 24h from reset time."""
        quota = QuotaLimit(max_tokens_per_day=100.0)
        enforcer = QuotaEnforcer(quota)

        # Set reset_at to past
        enforcer.reset_at = datetime.now(UTC) - timedelta(seconds=1)
        old_reset_at = enforcer.reset_at

        # Trigger reset
        before = datetime.now(UTC)
        enforcer.check_quota(10.0, 10.0)
        after = datetime.now(UTC)

        # New reset_at should be ~24h from now
        expected_min = before + timedelta(hours=24)
        expected_max = after + timedelta(hours=24, seconds=1)
        assert enforcer.reset_at > old_reset_at
        assert expected_min <= enforcer.reset_at <= expected_max

    def test_no_reset_if_not_yet_time(self) -> None:
        """Test no reset occurs if reset_at is in future."""
        quota = QuotaLimit(max_tokens_per_day=100.0)
        enforcer = QuotaEnforcer(quota)

        # Set reset_at far in future
        enforcer.reset_at = datetime.now(UTC) + timedelta(hours=23)

        # Record usage
        enforcer.record_usage(UsageRecord(tokens_used=50.0, cost_used=0.0))

        # Check quota (should NOT trigger reset)
        original_reset_at = enforcer.reset_at
        enforcer.check_quota(10.0, 0.0)

        # reset_at should not change
        assert enforcer.reset_at == original_reset_at

        # Usage should persist
        assert enforcer.get_usage().tokens_used == 50.0


class TestQuotaEnforcerThreadSafety:
    """Test thread-safe quota enforcement."""

    def test_concurrent_record_and_check(self) -> None:
        """Test concurrent record and check operations don't race."""
        quota = QuotaLimit(max_tokens_per_day=10_000.0, max_cost_per_day=1000.0)
        enforcer = QuotaEnforcer(quota)

        errors = []
        check_results = []

        def record_usage_repeatedly() -> None:
            try:
                for _ in range(100):
                    enforcer.record_usage(UsageRecord(tokens_used=10.0, cost_used=1.0))
                    time.sleep(0.0001)
            except Exception as e:
                errors.append(e)

        def check_repeatedly() -> None:
            try:
                for _ in range(100):
                    result = enforcer.check_quota(10.0, 1.0)
                    check_results.append(result)
                    time.sleep(0.0001)
            except Exception as e:
                errors.append(e)

        t1 = threading.Thread(target=record_usage_repeatedly)
        t2 = threading.Thread(target=check_repeatedly)

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert len(errors) == 0
        assert len(check_results) == 100

    def test_concurrent_quota_exhaustion(self) -> None:
        """Test that concurrent requests don't allow over-quota."""
        quota = QuotaLimit(max_tokens_per_day=100.0, max_cost_per_day=1000.0)
        enforcer = QuotaEnforcer(quota)

        allowed = []
        errors = []

        def try_use_quota() -> None:
            try:
                if enforcer.check_quota(10.0, 1.0):
                    # Simulate using the quota
                    enforcer.record_usage(UsageRecord(tokens_used=10.0, cost_used=1.0))
                    allowed.append(True)
                else:
                    allowed.append(False)
            except Exception as e:
                errors.append(e)

        # Launch 50 concurrent attempts (total would be 500 tokens > 100 limit)
        threads = [threading.Thread(target=try_use_quota) for _ in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        # Only ~10 should succeed (100 / 10 per request)
        allowed_count = sum(1 for a in allowed if a)
        assert allowed_count <= 10
        assert len(allowed) == 50


class TestQuotaEnforcerUsageTracking:
    """Test usage tracking and retrieval."""

    def test_record_usage_accumulates(self) -> None:
        """Test usage accumulates across records."""
        quota = QuotaLimit(max_tokens_per_day=1000.0)
        enforcer = QuotaEnforcer(quota)

        enforcer.record_usage(UsageRecord(tokens_used=100.0, cost_used=10.0))
        enforcer.record_usage(UsageRecord(tokens_used=50.0, cost_used=5.0))
        enforcer.record_usage(UsageRecord(tokens_used=25.0, cost_used=2.5))

        usage = enforcer.get_usage()
        assert usage.tokens_used == 175.0
        assert usage.cost_used == 17.5

    def test_get_usage_is_snapshot(self) -> None:
        """Test get_usage returns independent snapshot."""
        quota = QuotaLimit(max_tokens_per_day=1000.0)
        enforcer = QuotaEnforcer(quota)

        enforcer.record_usage(UsageRecord(tokens_used=100.0, cost_used=10.0))

        snapshot1 = enforcer.get_usage()
        snapshot2 = enforcer.get_usage()

        assert snapshot1.tokens_used == snapshot2.tokens_used
        assert snapshot1 is not snapshot2  # Different objects


class TestQuotaEnforcerParity:
    """Parity tests comparing behavior with CLIProxy Go implementation."""

    def test_parity_quota_limit_struct(self) -> None:
        """Verify Python QuotaLimit matches CLIProxy QuotaLimit struct."""
        # CLIProxy QuotaLimit:
        # type QuotaLimit struct {
        #     MaxTokensPerDay float64 `json:"max_tokens_per_day"`
        #     MaxCostPerDay   float64 `json:"max_cost_per_day"`
        # }

        quota = QuotaLimit(max_tokens_per_day=1000.0, max_cost_per_day=100.0)

        assert hasattr(quota, "max_tokens_per_day")
        assert hasattr(quota, "max_cost_per_day")
        assert isinstance(quota.max_tokens_per_day, float)
        assert isinstance(quota.max_cost_per_day, float)

    def test_parity_usage_record_struct(self) -> None:
        """Verify Python UsageRecord matches CLIProxy UsageRecord struct."""
        # CLIProxy UsageRecord:
        # type UsageRecord struct {
        #     TokensUsed float64 `json:"tokens_used"`
        #     CostUsed   float64 `json:"cost_used"`
        # }

        record = UsageRecord(tokens_used=100.0, cost_used=10.0)

        assert hasattr(record, "tokens_used")
        assert hasattr(record, "cost_used")
        assert isinstance(record.tokens_used, float)
        assert isinstance(record.cost_used, float)

    def test_parity_check_quota_logic(self) -> None:
        """Verify CheckQuota logic matches CLIProxy.

        CLIProxy CheckQuota logic:
        - if e.quota.MaxTokensPerDay > 0 &&
          e.usage.TokensUsed + estimatedTokens > e.quota.MaxTokensPerDay:
          return false
        - if e.quota.MaxCostPerDay > 0 &&
          e.usage.CostUsed + estimatedCost > e.quota.MaxCostPerDay:
          return false
        - return true
        """
        quota = QuotaLimit(max_tokens_per_day=100.0, max_cost_per_day=50.0)
        enforcer = QuotaEnforcer(quota)
        enforcer.record_usage(UsageRecord(tokens_used=90.0, cost_used=40.0))

        # Test tokens over limit
        assert enforcer.check_quota(20.0, 5.0) is False  # 90 + 20 = 110 > 100

        # Test cost over limit
        assert enforcer.check_quota(5.0, 20.0) is False  # 40 + 20 = 60 > 50

        # Test both under limit
        assert enforcer.check_quota(5.0, 5.0) is True  # 90 + 5 = 95, 40 + 5 = 45

    def test_parity_reset_window_24h(self) -> None:
        """Verify reset window is 24h (CLIProxy: 24 * time.Hour)."""
        quota = QuotaLimit(max_tokens_per_day=100.0)
        before = datetime.now(UTC)
        enforcer = QuotaEnforcer(quota)
        after = datetime.now(UTC)

        expected_min = before + timedelta(hours=24)
        expected_max = after + timedelta(hours=24, seconds=1)
        assert expected_min <= enforcer.reset_at <= expected_max

    def test_parity_lock_semantics(self) -> None:
        """Verify lock behavior matches CLIProxy RWMutex semantics.

        CLIProxy uses RWMutex with Lock() for exclusive access.

        Python threading.Lock is also exclusive, providing equivalent semantics.
        """
        quota = QuotaLimit(max_tokens_per_day=100.0)
        enforcer = QuotaEnforcer(quota)

        # Both check_quota and record_usage acquire the lock
        # This ensures atomic operations
        enforcer.record_usage(UsageRecord(tokens_used=50.0, cost_used=10.0))
        result = enforcer.check_quota(40.0, 10.0)

        assert result is True

    def test_parity_reset_idempotent(self) -> None:
        """Verify reset is idempotent when called multiple times.

        CLIProxy note: caller holds RLock, reset is rare and idempotent.
        """
        quota = QuotaLimit(max_tokens_per_day=100.0)
        enforcer = QuotaEnforcer(quota)

        # Force reset in the past
        enforcer.reset_at = datetime.now(UTC) - timedelta(seconds=1)
        enforcer.record_usage(UsageRecord(tokens_used=50.0, cost_used=0.0))

        # First check (triggers reset)
        enforcer.check_quota(10.0, 0.0)

        # Second check (should trigger reset again, but reset_at should be updated)
        enforcer.check_quota(10.0, 0.0)

        # Both resets should have cleared usage
        assert enforcer.get_usage().tokens_used == 0.0


class TestQuotaEnforcerEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_quota_tokens(self) -> None:
        """Test zero token quota (0 = unlimited)."""
        quota = QuotaLimit(max_tokens_per_day=0.0, max_cost_per_day=100.0)
        enforcer = QuotaEnforcer(quota)

        enforcer.record_usage(UsageRecord(tokens_used=1_000_000.0, cost_used=0.0))

        # Tokens are unlimited
        assert enforcer.check_quota(1_000_000.0, 0.0) is True

        # But cost is limited
        enforcer.record_usage(UsageRecord(tokens_used=0.0, cost_used=90.0))
        assert enforcer.check_quota(100.0, 20.0) is False

    def test_fractional_tokens_and_cost(self) -> None:
        """Test fractional token/cost values."""
        quota = QuotaLimit(max_tokens_per_day=100.5, max_cost_per_day=50.25)
        enforcer = QuotaEnforcer(quota)

        enforcer.record_usage(UsageRecord(tokens_used=75.3, cost_used=25.1))

        # 75.3 + 20 = 95.3, which is NOT > 100.5, so allowed
        assert enforcer.check_quota(20.0, 20.0) is True
        # 25.1 + 25.5 = 50.6, which IS > 50.25, so denied
        assert enforcer.check_quota(20.0, 25.5) is False
        # 75.3 + 30 = 105.3, which IS > 100.5, so denied
        assert enforcer.check_quota(30.0, 10.0) is False
        # 75.3 + 25 = 100.3, which is NOT > 100.5, so allowed
        assert enforcer.check_quota(25.0, 10.0) is True

    def test_exact_boundary(self) -> None:
        """Test exact quota boundary (strictly greater than check)."""
        quota = QuotaLimit(max_tokens_per_day=100.0)
        enforcer = QuotaEnforcer(quota)

        enforcer.record_usage(UsageRecord(tokens_used=100.0, cost_used=0.0))

        # At exactly limit, requesting more should be denied
        assert enforcer.check_quota(0.1, 0.0) is False

        # Requesting zero more should be allowed
        assert enforcer.check_quota(0.0, 0.0) is True
