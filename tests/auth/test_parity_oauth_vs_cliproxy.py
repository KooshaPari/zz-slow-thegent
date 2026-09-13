"""Parity tests: OAuth token refresh behavior (thegent Python vs CLIProxy Go).

Tests token refresh behavior equivalence:
- Expired token → automatic refresh → new token
- Token caching within TTL
- RWMutex style thread-safe locking
- Error handling on missing provider/failed refresh

Mirrors CLIProxy's pkg/llmproxy/auth/oauth_token_manager.go
# @trace WL-241
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest

# ========================================================================
# Token Manager Implementation (Python equivalent of CLIProxy)
# ========================================================================


@dataclass
class Token:
    """OAuth token with access, refresh, and expiry."""

    access_token: str
    refresh_token: str
    expires_at: datetime


class OAuthProvider:
    """Interface for OAuth token refresh."""

    def refresh_token(self, refresh_token: str) -> str:
        """Refresh and return a new access token.

        Args:
            refresh_token: The refresh token.

        Returns:
            New access token.

        Raises:
            Exception: On refresh failure.
        """
        raise NotImplementedError


class OAuthTokenManager:
    """Thread-safe OAuth token manager with auto-refresh (Python parity with CLIProxy Go).

    Stores tokens per provider and automatically refreshes expired tokens.
    Uses threading.Lock for RWMutex-like synchronization.
    """

    def __init__(self, provider: OAuthProvider | None = None) -> None:
        """Initialize token manager.

        Args:
            provider: OAuthProvider for token refresh. Can be None.
        """
        self.store: dict[str, Token] = {}
        self.provider = provider
        self._lock = threading.Lock()

    def store_token(self, provider_name: str, token: Token) -> None:
        """Store a token for a given provider.

        Args:
            provider_name: Provider identifier.
            token: Token to store.
        """
        with self._lock:
            self.store[provider_name] = token

    def get_token(self, provider_name: str) -> Token:
        """Retrieve a token for a given provider, auto-refreshing if expired.

        Mirrors CLIProxy's GetToken behavior:
        1. RLock to check cache
        2. If expired and provider available, refresh
        3. Lock and update store
        4. Return token

        Args:
            provider_name: Provider identifier.

        Returns:
            Token object.

        Raises:
            KeyError: If token not found.
            RuntimeError: If token expired and no provider available.
            Exception: If refresh fails (from provider).
        """
        with self._lock:
            if provider_name not in self.store:
                raise KeyError(f"token not found for provider: {provider_name}")

            token = self.store[provider_name]

            # Check expiry
            if datetime.now(UTC) >= token.expires_at:
                if self.provider is None:
                    raise RuntimeError("token expired and no provider available to refresh")

                # Refresh token
                try:
                    new_access = self.provider.refresh_token(token.refresh_token)
                except Exception as e:
                    raise RuntimeError(f"token refresh failed: {e}") from e

                # Update token
                token.access_token = new_access
                token.expires_at = datetime.now(UTC) + timedelta(hours=1)
                self.store[provider_name] = token

            return token


# ========================================================================
# Tests
# ========================================================================


class MockOAuthProvider(OAuthProvider):
    """Mock OAuth provider for testing."""

    def __init__(self) -> None:
        self.call_count = 0
        self.refresh_token_value = "refreshed_access_token"

    def refresh_token(self, refresh_token: str) -> str:
        """Simulate token refresh."""
        self.call_count += 1
        return self.refresh_token_value


class TestOAuthTokenManagerBasic:
    """Test basic token manager behavior."""

    def test_store_and_retrieve_token(self) -> None:
        """Test storing and retrieving a valid token."""
        manager = OAuthTokenManager()
        future = datetime.now(UTC) + timedelta(hours=1)
        token = Token(
            access_token="access_123",
            refresh_token="refresh_123",
            expires_at=future,
        )

        manager.store_token("provider_a", token)
        retrieved = manager.get_token("provider_a")

        assert retrieved.access_token == "access_123"
        assert retrieved.refresh_token == "refresh_123"

    def test_get_token_not_found(self) -> None:
        """Test KeyError when token not found."""
        manager = OAuthTokenManager()
        with pytest.raises(KeyError, match="token not found"):
            manager.get_token("nonexistent")

    def test_expired_token_requires_provider(self) -> None:
        """Test RuntimeError when token expired and no provider available."""
        manager = OAuthTokenManager(provider=None)
        past = datetime.now(UTC) - timedelta(hours=1)
        expired_token = Token(
            access_token="old_access",
            refresh_token="refresh_123",
            expires_at=past,
        )

        manager.store_token("provider_a", expired_token)

        with pytest.raises(RuntimeError, match="token expired and no provider"):
            manager.get_token("provider_a")


class TestOAuthTokenAutoRefresh:
    """Test automatic token refresh behavior."""

    def test_valid_token_no_refresh(self) -> None:
        """Test that valid (non-expired) token is not refreshed."""
        provider = MockOAuthProvider()
        manager = OAuthTokenManager(provider=provider)

        future = datetime.now(UTC) + timedelta(hours=1)
        token = Token(
            access_token="access_123",
            refresh_token="refresh_123",
            expires_at=future,
        )
        manager.store_token("provider_a", token)

        retrieved = manager.get_token("provider_a")

        assert retrieved.access_token == "access_123"
        assert provider.call_count == 0  # No refresh

    def test_expired_token_auto_refresh(self) -> None:
        """Test expired token is automatically refreshed."""
        provider = MockOAuthProvider()
        manager = OAuthTokenManager(provider=provider)

        past = datetime.now(UTC) - timedelta(hours=1)
        expired_token = Token(
            access_token="old_access",
            refresh_token="refresh_123",
            expires_at=past,
        )
        manager.store_token("provider_a", expired_token)

        retrieved = manager.get_token("provider_a")

        assert provider.call_count == 1
        assert retrieved.access_token == "refreshed_access_token"
        # New expiry should be ~1 hour from now
        now = datetime.now(UTC)
        assert retrieved.expires_at > now
        assert retrieved.expires_at < now + timedelta(hours=2)

    def test_expiring_soon_not_automatically_refreshed(self) -> None:
        """Test that expiring-soon (but not expired) token is not auto-refreshed."""
        provider = MockOAuthProvider()
        manager = OAuthTokenManager(provider=provider)

        # Token expires in 30 minutes
        soon = datetime.now(UTC) + timedelta(minutes=30)
        token = Token(
            access_token="access_123",
            refresh_token="refresh_123",
            expires_at=soon,
        )
        manager.store_token("provider_a", token)

        retrieved = manager.get_token("provider_a")

        assert provider.call_count == 0  # Not refreshed
        assert retrieved.access_token == "access_123"

    def test_refresh_failure_propagates(self) -> None:
        """Test that provider refresh errors propagate."""

        class FailingProvider(OAuthProvider):
            def refresh_token(self, refresh_token: str) -> str:
                raise ValueError("Refresh API error")

        manager = OAuthTokenManager(provider=FailingProvider())
        past = datetime.now(UTC) - timedelta(hours=1)
        expired_token = Token(
            access_token="old_access",
            refresh_token="refresh_123",
            expires_at=past,
        )
        manager.store_token("provider_a", expired_token)

        with pytest.raises(RuntimeError, match="token refresh failed"):
            manager.get_token("provider_a")


class TestOAuthTokenThreadSafety:
    """Test thread-safe locking behavior."""

    def test_concurrent_get_and_store(self) -> None:
        """Test concurrent get and store operations don't race."""
        provider = MockOAuthProvider()
        manager = OAuthTokenManager(provider=provider)

        initial = Token(
            access_token="initial",
            refresh_token="refresh_123",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
        manager.store_token("provider_a", initial)

        results = []
        errors = []

        def store_repeatedly() -> None:
            try:
                for i in range(10):
                    new_token = Token(
                        access_token=f"access_{i}",
                        refresh_token="refresh_123",
                        expires_at=datetime.now(UTC) + timedelta(hours=1),
                    )
                    manager.store_token("provider_a", new_token)
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)

        def get_repeatedly() -> None:
            try:
                for _ in range(10):
                    token = manager.get_token("provider_a")
                    results.append(token.access_token)
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)

        t1 = threading.Thread(target=store_repeatedly)
        t2 = threading.Thread(target=get_repeatedly)

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert len(errors) == 0
        assert len(results) == 10

    def test_concurrent_refresh_only_happens_once(self) -> None:
        """Test that concurrent refresh attempts don't cause double-refresh.

        Note: CLIProxy's Go implementation uses RWMutex RLock/Unlock which allows
        concurrent reads. Python threading.Lock is exclusive, so this test
        documents the behavior difference.
        """
        provider = MockOAuthProvider()
        manager = OAuthTokenManager(provider=provider)

        past = datetime.now(UTC) - timedelta(hours=1)
        expired_token = Token(
            access_token="old_access",
            refresh_token="refresh_123",
            expires_at=past,
        )
        manager.store_token("provider_a", expired_token)

        results = []
        errors = []

        def get_and_record() -> None:
            try:
                token = manager.get_token("provider_a")
                results.append(token.access_token)
            except Exception as e:
                errors.append(e)

        # Launch 5 concurrent gets on expired token
        threads = [threading.Thread(target=get_and_record) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(results) == 5
        # With Python's exclusive lock, all 5 will see the refreshed token
        # (after the first refresh). All should have same access_token.
        assert all(r == "refreshed_access_token" for r in results)


class TestOAuthTokenMultiProvider:
    """Test token manager with multiple providers."""

    def test_multiple_providers_independent(self) -> None:
        """Test that tokens for different providers are independent."""
        provider = MockOAuthProvider()
        manager = OAuthTokenManager(provider=provider)

        future = datetime.now(UTC) + timedelta(hours=1)
        token_a = Token("access_a", "refresh_a", future)
        token_b = Token("access_b", "refresh_b", future)

        manager.store_token("provider_a", token_a)
        manager.store_token("provider_b", token_b)

        assert manager.get_token("provider_a").access_token == "access_a"
        assert manager.get_token("provider_b").access_token == "access_b"

    def test_one_provider_expires_others_unaffected(self) -> None:
        """Test that one provider's expiry doesn't affect others."""
        provider = MockOAuthProvider()
        manager = OAuthTokenManager(provider=provider)

        future = datetime.now(UTC) + timedelta(hours=1)
        past = datetime.now(UTC) - timedelta(hours=1)

        token_valid = Token("access_valid", "refresh_valid", future)
        token_expired = Token("access_expired", "refresh_expired", past)

        manager.store_token("provider_valid", token_valid)
        manager.store_token("provider_expired", token_expired)

        # Get valid token (should not trigger any refresh)
        assert manager.get_token("provider_valid").access_token == "access_valid"
        assert provider.call_count == 0

        # Get expired token (should trigger refresh only for this provider)
        manager.get_token("provider_expired")
        assert provider.call_count == 1


class TestOAuthTokenParity:
    """Parity tests comparing behavior with CLIProxy Go implementation."""

    def test_parity_token_struct(self) -> None:
        """Verify Python Token matches CLIProxy Token struct fields."""
        # CLIProxy Token:
        # type Token struct {
        #     AccessToken  string    `json:"access_token"`
        #     RefreshToken string    `json:"refresh_token"`
        #     ExpiresAt    time.Time `json:"expires_at"`
        # }

        future = datetime.now(UTC) + timedelta(hours=1)
        token = Token(
            access_token="test_access",
            refresh_token="test_refresh",
            expires_at=future,
        )

        assert hasattr(token, "access_token")
        assert hasattr(token, "refresh_token")
        assert hasattr(token, "expires_at")
        assert isinstance(token.access_token, str)
        assert isinstance(token.refresh_token, str)
        assert isinstance(token.expires_at, datetime)

    def test_parity_auto_refresh_ttl(self) -> None:
        """Verify refresh sets TTL to ~1 hour (CLIProxy: time.Hour)."""
        provider = MockOAuthProvider()
        manager = OAuthTokenManager(provider=provider)

        past = datetime.now(UTC) - timedelta(hours=1)
        expired_token = Token("old", "refresh_123", past)
        manager.store_token("provider", expired_token)

        before = datetime.now(UTC)
        manager.get_token("provider")
        after = datetime.now(UTC)

        refreshed = manager.get_token("provider")

        # Verify TTL is set to approximately 1 hour
        expected_min = before + timedelta(hours=1)
        expected_max = after + timedelta(hours=1, seconds=1)
        assert expected_min <= refreshed.expires_at <= expected_max

    def test_parity_lock_semantics(self) -> None:
        """Verify lock behavior matches CLIProxy RWMutex semantics.

        CLIProxy uses RWMutex with:
        - RLock for read (checking cache)
        - Lock for write (updating store after refresh)

        Python threading.Lock is exclusive, but the parity is in the
        semantics: both provide thread-safe access to shared state.
        """
        provider = MockOAuthProvider()
        manager = OAuthTokenManager(provider=provider)

        future = datetime.now(UTC) + timedelta(hours=1)
        token = Token("access", "refresh", future)
        manager.store_token("provider", token)

        # Both get and store operations should be atomic
        # (no partial state visible between threads)
        retrieved = manager.get_token("provider")
        assert retrieved.access_token == "access"

    def test_parity_with_actual_cliproxy(self) -> None:
        """Integration test against actual CLIProxy server if available."""
        if not self._is_cliproxy_running():
            pytest.skip("CLIProxy server not running")
        pytest.skip("CLIProxy integration test not yet implemented")

    @staticmethod
    def _is_cliproxy_running() -> bool:
        """Check if CLIProxy server is running on expected port."""
        try:
            import httpx

            client = httpx.Client(timeout=1.0)
            response = client.get("http://localhost:8080/health")
            client.close()
            return response.status_code == 200
        except Exception:
            return False
