"""Tests for Redlock-based atomic acquire/release.

@trace FR-ORC-003 (swarm-redlock-atomic)
"""

from __future__ import annotations

import dataclasses
import time
import uuid
from unittest.mock import MagicMock, patch

import pytest

from thegent.orchestration.consensus.redlock_atomic import (
    RedlockAcquireResult,
    RedlockController,
    _InMemoryLockState,
    _parse_node_urls_from_env,
    _parse_redis_url,
    make_redlock_controller,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fallback_controller(key: str = "test-key", ttl_ms: int = 5000) -> RedlockController:
    """Create a RedlockController forced into in-memory fallback mode."""
    with patch("thegent.orchestration.redlock_atomic._import_redis_sync", return_value=None):
        return RedlockController(key, ttl_ms=ttl_ms, redis_nodes=["redis://localhost:6379"])


def _mock_redis_client(*, set_ok: bool = True, eval_result: int = 1, exists: bool = False) -> MagicMock:
    """Build a mock Redis client."""
    client = MagicMock()
    client.ping.return_value = True
    client.set.return_value = set_ok
    client.eval.return_value = eval_result
    client.exists.return_value = exists
    return client


def _redis_controller(
    key: str = "test-key",
    ttl_ms: int = 5000,
    clients: list[MagicMock] | None = None,
) -> RedlockController:
    """Create a RedlockController pre-wired with mock Redis clients."""
    ctrl = _fallback_controller(key, ttl_ms)
    # Swap to Redis mode with mock clients
    ctrl._fallback = None
    ctrl._redis_available = True
    ctrl._clients = clients if clients is not None else [_mock_redis_client()]
    return ctrl


# ---------------------------------------------------------------------------
# RedlockAcquireResult tests
# ---------------------------------------------------------------------------


class TestRedlockAcquireResult:
    """Tests for the result dataclass.  @trace FR-ORC-003"""

    def test_fields_success(self) -> None:  # @trace FR-ORC-003
        result = RedlockAcquireResult(acquired=True, lock_id="abc", expires_at=99.0)
        assert result.acquired is True
        assert result.lock_id == "abc"
        assert result.expires_at == pytest.approx(99.0)

    def test_fields_failure(self) -> None:  # @trace FR-ORC-003
        result = RedlockAcquireResult(acquired=False, lock_id="", expires_at=0.0)
        assert result.acquired is False
        assert result.lock_id == ""
        assert result.expires_at == 0.0

    def test_frozen_raises_on_setattr(self) -> None:  # @trace FR-ORC-003
        result = RedlockAcquireResult(acquired=True, lock_id="x", expires_at=1.0)
        # frozen dataclasses raise FrozenInstanceError on attribute mutation;
        # call the generated __setattr__ directly to trigger it without
        # triggering B010 (setattr with constant) or static-analysis type errors
        with pytest.raises(dataclasses.FrozenInstanceError):
            type(result).__setattr__(result, "acquired", False)

    def test_is_dataclass(self) -> None:  # @trace FR-ORC-003
        assert dataclasses.is_dataclass(RedlockAcquireResult)


# ---------------------------------------------------------------------------
# _InMemoryLockState tests
# ---------------------------------------------------------------------------


class TestInMemoryLockState:
    """Tests for the in-process fallback lock.  @trace FR-ORC-003"""

    @pytest.fixture
    def state(self) -> _InMemoryLockState:
        return _InMemoryLockState()

    def test_acquire_returns_true_when_free(self, state: _InMemoryLockState) -> None:  # @trace FR-ORC-003
        assert state.acquire("lock-1", 5000) is True

    def test_acquire_when_locked_returns_false(self, state: _InMemoryLockState) -> None:  # @trace FR-ORC-003
        state.acquire("lock-1", 5000)
        assert state.acquire("lock-2", 5000) is False

    def test_release_matching_returns_true(self, state: _InMemoryLockState) -> None:  # @trace FR-ORC-003
        state.acquire("lock-1", 5000)
        assert state.release("lock-1") is True

    def test_release_wrong_id_returns_false(self, state: _InMemoryLockState) -> None:  # @trace FR-ORC-003
        state.acquire("lock-1", 5000)
        assert state.release("wrong-id") is False

    def test_release_when_free_returns_false(self, state: _InMemoryLockState) -> None:  # @trace FR-ORC-003
        assert state.release("nonexistent") is False

    def test_acquire_after_release(self, state: _InMemoryLockState) -> None:  # @trace FR-ORC-003
        state.acquire("lock-1", 5000)
        state.release("lock-1")
        assert state.acquire("lock-2", 5000) is True

    def test_is_locked_when_held(self, state: _InMemoryLockState) -> None:  # @trace FR-ORC-003
        state.acquire("lock-1", 5000)
        assert state.is_locked() is True

    def test_is_locked_when_free(self, state: _InMemoryLockState) -> None:  # @trace FR-ORC-003
        assert state.is_locked() is False

    def test_is_locked_after_release(self, state: _InMemoryLockState) -> None:  # @trace FR-ORC-003
        state.acquire("lock-1", 5000)
        state.release("lock-1")
        assert state.is_locked() is False

    def test_extend_updates_expiry(self, state: _InMemoryLockState) -> None:  # @trace FR-ORC-003
        state.acquire("lock-1", 5000)
        before = state._expires_at
        time.sleep(0.05)
        assert state.extend("lock-1", 10000) is True
        assert state._expires_at > before

    def test_extend_wrong_id_returns_false(self, state: _InMemoryLockState) -> None:  # @trace FR-ORC-003
        state.acquire("lock-1", 5000)
        assert state.extend("wrong-id", 10000) is False

    def test_expired_lock_can_be_reacquired(self, state: _InMemoryLockState) -> None:  # @trace FR-ORC-003
        state.acquire("lock-1", 10)  # 10ms TTL — expires almost immediately
        time.sleep(0.05)
        assert state.acquire("lock-2", 5000) is True

    def test_is_locked_false_after_expiry(self, state: _InMemoryLockState) -> None:  # @trace FR-ORC-003
        state.acquire("lock-1", 10)  # 10ms TTL
        time.sleep(0.05)
        assert state.is_locked() is False


# ---------------------------------------------------------------------------
# _parse_redis_url tests
# ---------------------------------------------------------------------------


class TestParseRedisUrl:
    """Unit tests for URL parser.  @trace FR-ORC-003"""

    def test_default_url(self) -> None:  # @trace FR-ORC-003
        kw = _parse_redis_url("redis://localhost:6379")
        assert kw["host"] == "localhost"
        assert kw["port"] == 6379
        assert kw["db"] == 0
        assert "password" not in kw

    def test_custom_host_port_db(self) -> None:  # @trace FR-ORC-003
        kw = _parse_redis_url("redis://redis.prod.example.com:6380/2")
        assert kw["host"] == "redis.prod.example.com"
        assert kw["port"] == 6380
        assert kw["db"] == 2

    def test_password_in_url(self) -> None:  # @trace FR-ORC-003
        kw = _parse_redis_url("redis://:secret@localhost:6379")
        assert kw["password"] == "secret"


class TestParseNodeUrlsFromEnv:
    """Tests for env-based node URL parsing.  @trace FR-ORC-003"""

    def test_default_single_node(self, monkeypatch: pytest.MonkeyPatch) -> None:  # @trace FR-ORC-003
        monkeypatch.delenv("THGENT_REDLOCK_NODES", raising=False)
        urls = _parse_node_urls_from_env()
        assert urls == ["redis://localhost:6379"]

    def test_multiple_nodes(self, monkeypatch: pytest.MonkeyPatch) -> None:  # @trace FR-ORC-003
        monkeypatch.setenv("THGENT_REDLOCK_NODES", "redis://a:6379,redis://b:6380,redis://c:6381")
        urls = _parse_node_urls_from_env()
        assert urls == ["redis://a:6379", "redis://b:6380", "redis://c:6381"]

    def test_whitespace_stripped(self, monkeypatch: pytest.MonkeyPatch) -> None:  # @trace FR-ORC-003
        monkeypatch.setenv("THGENT_REDLOCK_NODES", "redis://a:6379 , redis://b:6380")
        urls = _parse_node_urls_from_env()
        assert urls == ["redis://a:6379", "redis://b:6380"]


# ---------------------------------------------------------------------------
# RedlockController — fallback mode tests
# ---------------------------------------------------------------------------


class TestRedlockControllerFallback:
    """Tests for fallback in-memory mode.  @trace FR-ORC-003"""

    @pytest.fixture
    def ctrl(self) -> RedlockController:
        return _fallback_controller()

    def test_is_available_false_in_fallback(self, ctrl: RedlockController) -> None:  # @trace FR-ORC-003
        assert ctrl.is_available() is False

    def test_acquire_returns_result(self, ctrl: RedlockController) -> None:  # @trace FR-ORC-003
        result = ctrl.acquire()
        assert isinstance(result, RedlockAcquireResult)

    def test_acquire_acquired_true(self, ctrl: RedlockController) -> None:  # @trace FR-ORC-003
        result = ctrl.acquire()
        assert result.acquired is True

    def test_acquire_lock_id_nonempty(self, ctrl: RedlockController) -> None:  # @trace FR-ORC-003
        result = ctrl.acquire()
        assert len(result.lock_id) > 0

    def test_acquire_expires_at_in_future(self, ctrl: RedlockController) -> None:  # @trace FR-ORC-003
        result = ctrl.acquire()
        assert result.expires_at > time.monotonic()

    def test_acquire_when_already_locked_returns_false(self, ctrl: RedlockController) -> None:  # @trace FR-ORC-003
        ctrl.acquire()
        second = ctrl.acquire()
        assert second.acquired is False
        assert second.lock_id == ""
        assert second.expires_at == 0.0

    def test_release_matching_lock_id_succeeds(self, ctrl: RedlockController) -> None:  # @trace FR-ORC-003
        result = ctrl.acquire()
        assert ctrl.release(result.lock_id) is True

    def test_release_wrong_lock_id_returns_false(self, ctrl: RedlockController) -> None:  # @trace FR-ORC-003
        ctrl.acquire()
        assert ctrl.release("wrong-id") is False

    def test_release_allows_re_acquire(self, ctrl: RedlockController) -> None:  # @trace FR-ORC-003
        first = ctrl.acquire()
        ctrl.release(first.lock_id)
        second = ctrl.acquire()
        assert second.acquired is True

    def test_extend_updates_ttl(self, ctrl: RedlockController) -> None:  # @trace FR-ORC-003
        result = ctrl.acquire()
        time.sleep(0.02)
        assert ctrl.extend(result.lock_id, 10000) is True

    def test_extend_wrong_id_returns_false(self, ctrl: RedlockController) -> None:  # @trace FR-ORC-003
        ctrl.acquire()
        assert ctrl.extend("wrong-id", 10000) is False

    def test_is_locked_true_when_held(self, ctrl: RedlockController) -> None:  # @trace FR-ORC-003
        ctrl.acquire()
        assert ctrl.is_locked() is True

    def test_is_locked_false_initially(self, ctrl: RedlockController) -> None:  # @trace FR-ORC-003
        assert ctrl.is_locked() is False

    def test_is_locked_false_after_release(self, ctrl: RedlockController) -> None:  # @trace FR-ORC-003
        result = ctrl.acquire()
        ctrl.release(result.lock_id)
        assert ctrl.is_locked() is False

    def test_unique_lock_ids_per_acquire(self) -> None:  # @trace FR-ORC-003
        ids = set()
        for _ in range(10):
            c = _fallback_controller(key=f"key-{uuid.uuid4().hex}")
            r = c.acquire()
            ids.add(r.lock_id)
        assert len(ids) == 10


# ---------------------------------------------------------------------------
# RedlockController — Redis mode tests (mocked)
# ---------------------------------------------------------------------------


class TestRedlockControllerRedis:
    """Tests for Redis-backed mode with mock clients.  @trace FR-ORC-003"""

    def test_is_available_true_with_clients(self) -> None:  # @trace FR-ORC-003
        ctrl = _redis_controller()
        assert ctrl.is_available() is True

    def test_acquire_success_single_node(self) -> None:  # @trace FR-ORC-003
        ctrl = _redis_controller(clients=[_mock_redis_client(set_ok=True)])
        result = ctrl.acquire()
        assert result.acquired is True
        assert len(result.lock_id) > 0
        assert result.expires_at > time.monotonic()

    def test_acquire_fails_when_set_returns_false(self) -> None:  # @trace FR-ORC-003
        ctrl = _redis_controller(clients=[_mock_redis_client(set_ok=False)])
        result = ctrl.acquire()
        assert result.acquired is False
        assert result.lock_id == ""
        assert result.expires_at == 0.0

    def test_acquire_quorum_three_nodes_two_succeed(self) -> None:  # @trace FR-ORC-003
        # 2 out of 3 succeed — quorum met
        clients = [
            _mock_redis_client(set_ok=True),
            _mock_redis_client(set_ok=True),
            _mock_redis_client(set_ok=False),
        ]
        ctrl = _redis_controller(clients=clients)
        result = ctrl.acquire()
        assert result.acquired is True

    def test_acquire_quorum_three_nodes_one_succeeds(self) -> None:  # @trace FR-ORC-003
        # 1 out of 3 — quorum NOT met (need 2)
        clients = [
            _mock_redis_client(set_ok=True),
            _mock_redis_client(set_ok=False),
            _mock_redis_client(set_ok=False),
        ]
        ctrl = _redis_controller(clients=clients)
        result = ctrl.acquire()
        assert result.acquired is False

    def test_release_matching_returns_true(self) -> None:  # @trace FR-ORC-003
        client = _mock_redis_client(eval_result=1)
        ctrl = _redis_controller(clients=[client])
        assert ctrl.release("some-lock-id") is True

    def test_release_wrong_lock_id_returns_false(self) -> None:  # @trace FR-ORC-003
        client = _mock_redis_client(eval_result=0)
        ctrl = _redis_controller(clients=[client])
        assert ctrl.release("wrong-id") is False

    def test_extend_success(self) -> None:  # @trace FR-ORC-003
        client = _mock_redis_client(eval_result=1)
        ctrl = _redis_controller(clients=[client])
        assert ctrl.extend("some-lock-id", 10000) is True

    def test_extend_fails_wrong_owner(self) -> None:  # @trace FR-ORC-003
        client = _mock_redis_client(eval_result=0)
        ctrl = _redis_controller(clients=[client])
        assert ctrl.extend("wrong-id", 10000) is False

    def test_is_locked_true_when_exists(self) -> None:  # @trace FR-ORC-003
        client = _mock_redis_client(exists=True)
        ctrl = _redis_controller(clients=[client])
        assert ctrl.is_locked() is True

    def test_is_locked_false_when_not_exists(self) -> None:  # @trace FR-ORC-003
        client = _mock_redis_client(exists=False)
        ctrl = _redis_controller(clients=[client])
        assert ctrl.is_locked() is False

    def test_acquire_calls_set_with_nx_px(self) -> None:  # @trace FR-ORC-003
        client = _mock_redis_client(set_ok=True)
        ctrl = _redis_controller(clients=[client])
        ctrl.acquire()
        client.set.assert_called_once()
        _, kwargs = client.set.call_args
        assert kwargs.get("nx") is True
        assert kwargs.get("px") == 5000

    def test_release_calls_eval_with_script(self) -> None:  # @trace FR-ORC-003
        client = _mock_redis_client(eval_result=1)
        ctrl = _redis_controller(clients=[client])
        ctrl.release("my-lock-id")
        client.eval.assert_called_once()
        args, _ = client.eval.call_args
        assert "get" in args[0].lower() or "del" in args[0].lower()

    def test_fallback_activated_when_no_redis_module(self) -> None:  # @trace FR-ORC-003
        ctrl = _fallback_controller()
        assert ctrl._fallback is not None
        assert ctrl._clients == []


# ---------------------------------------------------------------------------
# Factory function tests
# ---------------------------------------------------------------------------


class TestMakeRedlockController:
    """Tests for the factory function.  @trace FR-ORC-003"""

    def test_returns_redlock_controller(self) -> None:  # @trace FR-ORC-003
        with patch("thegent.orchestration.redlock_atomic._import_redis_sync", return_value=None):
            ctrl = make_redlock_controller("my-lock")
        assert isinstance(ctrl, RedlockController)

    def test_passes_ttl_ms(self) -> None:  # @trace FR-ORC-003
        with patch("thegent.orchestration.redlock_atomic._import_redis_sync", return_value=None):
            ctrl = make_redlock_controller("my-lock", ttl_ms=1234)
        assert ctrl._ttl_ms == 1234

    def test_passes_redis_nodes(self) -> None:  # @trace FR-ORC-003
        with patch("thegent.orchestration.redlock_atomic._import_redis_sync", return_value=None):
            ctrl = make_redlock_controller("my-lock", redis_nodes=["redis://a:6379"])
        assert ctrl._nodes_urls == ["redis://a:6379"]

    def test_factory_fallback_functional(self) -> None:  # @trace FR-ORC-003
        with patch("thegent.orchestration.redlock_atomic._import_redis_sync", return_value=None):
            ctrl = make_redlock_controller("factory-test")
        result = ctrl.acquire()
        assert result.acquired is True
        assert ctrl.release(result.lock_id) is True
