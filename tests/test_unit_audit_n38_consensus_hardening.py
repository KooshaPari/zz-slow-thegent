"""Spec-only hardening tests for the dormant consensus cluster (SOTA pass-22).

Covers three dormant orchestration/consensus modules that have never
been audited in the dormant-core chain:

  * ``thegent.orchestration.consensus.omega_consensus``
    — ``OmegaConsensus`` quorum/finalize semantics (FR-CON-001, WP-45003).
  * ``thegent.orchestration.consensus.redis_concurrency``
    — synchronous ``RedisConcurrencyController`` slot counter (FR-ORC-002).
  * ``thegent.orchestration.consensus.redlock_atomic``
    — ``RedlockController`` quorum acquire/release/extend (FR-ORC-003).

This file is the AUDIT-N+38 contract spec (SOTA pass-22).  It is
committed first (spec-first pattern, mirrors AUDIT-N+33 / N+34 / N+35
/ N+36 / N+37) so the next step is to make every assertion here pass
without breaking any dormant test corridor (test_unit_omega_consensus,
test_redlock_atomic, test_redis_concurrency) or any other SOTA
audit-N+ invariant cluster.

@trace FR-ORC-CON-060 -- ``RedlockController.__init__`` accepts
                       ``(key, ttl_ms, redis_nodes)`` and exposes
                       ``is_available()`` / ``_fallback`` / ``_clients``
                       / ``_redis_available`` / ``_ttl_ms`` /
                       ``_nodes_urls`` so callers and tests can
                       reason about the controller's mode.
@trace FR-ORC-CON-061 -- ``RedlockController.acquire()`` returns a
                       ``RedlockAcquireResult(acquired, lock_id,
                       expires_at)`` that is ``frozen=True`` so
                       downstream code can rely on immutable
                       acquire results.
@trace FR-ORC-CON-062 -- ``RedlockController.acquire()`` uses Redis
                       quorum (majority of ``_clients``) for
                       acquire; ``acquired`` is ``True`` only when
                       at least half (rounded up) of the nodes
                       returned a positive ``SET NX PX`` result.
@trace FR-ORC-CON-063 -- ``RedlockController.acquire()`` returns
                       ``acquired=False, lock_id="", expires_at=0.0``
                       when the quorum is not met (1/3, 0/3, etc.)
                       and never raises — fallback acquires remain
                       a single in-process lock.
@trace FR-ORC-CON-064 -- ``RedlockController.acquire()`` falls back
                       to the in-process ``_InMemoryLockState``
                       when no Redis nodes are reachable; the
                       fallback path always returns
                       ``acquired=True`` for the first caller and
                       ``acquired=False`` thereafter until released.
@trace FR-ORC-CON-065 -- ``RedlockController.release(lock_id)`` is
                       a no-op when ``lock_id`` does not match
                       the active lock; matching lock_ids release
                       cleanly.  Redis mode runs a Lua ``GET+DEL``
                       script so only the original owner can
                       release; fallback mode compares lock_ids
                       in-process.
@trace FR-ORC-CON-066 -- ``RedlockController.extend(lock_id,
                       ttl_ms)`` re-ups the TTL on the active
                       lock; returns ``False`` when ``lock_id``
                       does not match or the Redis Lua script
                       returns 0.  Extending an expired lock
                       returns ``False``.
@trace FR-ORC-CON-067 -- ``RedlockController.is_locked()`` returns
                       ``True`` when the controller currently
                       holds any lock (Redis ``EXISTS`` or
                       in-process state).
@trace FR-ORC-CON-068 -- ``RedlockController.is_available()``
                       returns ``True`` when at least one Redis
                       client is reachable and ``False`` when
                       the controller is in fallback mode.
@trace FR-ORC-CON-069 -- ``make_redlock_controller(key, ttl_ms,
                       redis_nodes)`` returns a ``RedlockController``
                       configured from the supplied arguments
                       (the env-based ``_import_redis_sync`` hook
                       is patched to ``None`` so the factory
                       falls back to in-process mode).
@trace FR-ORC-CON-070 -- ``_InMemoryLockState.acquire(lock_id,
                       ttl_ms)`` returns ``False`` when the lock
                       is currently held by any owner; ``release(
                       lock_id)`` only succeeds when the supplied
                       ``lock_id`` matches the active lock.
@trace FR-ORC-CON-071 -- ``_InMemoryLockState.extend(lock_id,
                       ttl_ms)`` extends the expiry and returns
                       ``True``; ``is_locked()`` (no-arg) returns
                       ``True`` when the lock is currently held
                       and not yet expired.
@trace FR-ORC-CON-072 -- ``_InMemoryLockState`` honours TTL:
                       an expired lock is treated as released;
                       ``acquire`` returns ``True`` again after
                       the TTL has elapsed and ``is_locked()``
                       returns ``False``.
@trace FR-ORC-CON-073 -- ``_parse_redis_url(url)`` returns
                       ``{host, port, db}`` when no password is
                       present and ``{host, port, db, password}``
                       when the URL embeds ``:password@``; the
                       returned dict never carries a ``"password"``
                       key when the URL has no auth.
@trace FR-ORC-CON-074 -- ``_parse_node_urls_from_env()`` reads
                       the ``THGENT_REDLOCK_NODES`` env var,
                       splits on comma, strips whitespace, drops
                       empty entries, and falls back to
                       ``["redis://localhost:6379"]`` when the
                       env var is unset or empty.
@trace FR-ORC-CON-075 -- ``OmegaConsensus(swarm_size, threshold)``
                       stores both as instance attributes and
                       rejects non-positive ``swarm_size`` /
                       non-in-``[0, 1]`` ``threshold`` with
                       ``ValueError`` so a misconfigured swarm
                       cannot silently disable quorum.
@trace FR-ORC-CON-076 -- ``OmegaConsensus.propose_state(proposer_id,
                       state, metadata)`` returns a unique
                       ``proposal_id`` (``str``), stores the
                       proposal internally with the
                       ``proposer_id`` / ``state`` /
                       ``metadata``, and starts at zero YES/NO
                       votes.
@trace FR-ORC-CON-077 -- ``OmegaConsensus.cast_vote(proposal_id,
                       voter_id, vote, signature)`` records a
                       vote for the supplied ``proposal_id``,
                       ignores duplicate ``voter_id`` votes on
                       the same proposal (idempotent), and
                       returns ``False`` when the proposal_id
                       is unknown.
@trace FR-ORC-CON-078 -- ``OmegaConsensus.finalize_consensus(
                       proposal_id)`` returns ``True`` when the
                       YES votes meet the configured threshold
                       (YES / swarm_size >= threshold) and
                       ``False`` otherwise; calling finalize on
                       an unknown proposal returns ``False``
                       without raising.
@trace FR-ORC-CON-079 -- ``OmegaConsensus.get_final_state()``
                       returns ``None`` before any proposal has
                       been finalized and a dataclass-like
                       ``FinalState(proposal_id=…)`` object
                       after a successful ``finalize_consensus``;
                       a failed finalize leaves ``get_final_state``
                       returning ``None``.
@trace FR-ORC-CON-080 -- ``RedisConcurrencyController`` is
                       concurrency-safe under threading contention:
                       ``acquire()`` increments ``current`` and
                       never exceeds ``max_concurrent``; the
                       ``release()`` path is paired with the
                       matching ``acquire()`` so a leaked
                       release cannot underflow ``current``.
@trace FR-ORC-CON-081 -- ``RedisConcurrencyController`` exposes
                       ``current`` and ``max_concurrent`` as
                       plain attributes (set in ``__init__``)
                       and ``make_redis_concurrency_controller(
                       config)`` clones the ``max_concurrent``
                       from the config but does NOT touch
                       ``host`` / ``port`` / ``db`` /
                       ``password`` on the controller.
@trace FR-ORC-CON-082 -- ``_InMemoryStore`` exposes a synchronous
                       key/value interface (``get`` / ``set`` /
                       ``delete`` / ``exists`` / ``set(ex=…)``)
                       that round-trips values, returns ``None``
                       on miss, and ``0`` for delete/exists of
                       missing keys without raising.
"""

from __future__ import annotations

import dataclasses
import threading
import time
from unittest.mock import MagicMock, patch

import pytest

from thegent.orchestration.consensus.omega_consensus import OmegaConsensus
from thegent.orchestration.consensus.redis_concurrency import (
    RedisConcurrencyController,
    RedisConfig,
    _InMemoryStore,
    make_redis_concurrency_controller,
)
from thegent.orchestration.consensus.redlock_atomic import (
    RedlockAcquireResult,
    RedlockController,
    _InMemoryLockState,
    _parse_node_urls_from_env,
    _parse_redis_url,
    make_redlock_controller,
)

# ---------------------------------------------------------------------------
# Helpers — mirrored from the dormant test clusters so the spec is
# hermetic.
# ---------------------------------------------------------------------------


def _mock_redis_client(*, set_ok: bool = True, eval_result: int = 1, exists: bool = False) -> MagicMock:
    """Build a mock Redis client (mirrors ``test_redlock_atomic.py``)."""
    client = MagicMock()
    client.ping.return_value = True
    client.set.return_value = set_ok
    client.eval.return_value = eval_result
    client.exists.return_value = exists
    return client


def _fallback_controller(key: str = "test-key", ttl_ms: int = 5000) -> RedlockController:
    """Create a RedlockController forced into in-memory fallback mode."""
    with patch("thegent.orchestration.redlock_atomic._import_redis_sync", return_value=None):
        return RedlockController(key, ttl_ms=ttl_ms, redis_nodes=["redis://localhost:6379"])


def _redis_controller(
    key: str = "test-key",
    ttl_ms: int = 5000,
    clients: list[MagicMock] | None = None,
) -> RedlockController:
    """Create a RedlockController pre-wired with mock Redis clients."""
    ctrl = _fallback_controller(key, ttl_ms)
    ctrl._fallback = None
    ctrl._redis_available = True
    ctrl._clients = clients if clients is not None else [_mock_redis_client()]
    return ctrl


# ---------------------------------------------------------------------------
# FR-ORC-CON-060 -- RedlockController.__init__ contract
# ---------------------------------------------------------------------------


class TestRedlockControllerInit:
    """@trace FR-ORC-CON-060"""

    def test_init_stores_ttl_and_nodes(self) -> None:
        """``ttl_ms`` and ``redis_nodes`` are stored as ``_ttl_ms`` / ``_nodes_urls``."""
        with patch("thegent.orchestration.redlock_atomic._import_redis_sync", return_value=None):
            ctrl = RedlockController("k", ttl_ms=4321, redis_nodes=["redis://a:6379", "redis://b:6380"])
        assert ctrl._ttl_ms == 4321
        assert ctrl._nodes_urls == ["redis://a:6379", "redis://b:6380"]

    def test_init_redis_module_unavailable_sets_fallback(self) -> None:
        """When the redis module import returns ``None`` the controller is in fallback mode."""
        with patch("thegent.orchestration.redlock_atomic._import_redis_sync", return_value=None):
            ctrl = RedlockController("k")
        assert ctrl._fallback is not None
        assert ctrl._clients == []
        assert ctrl._redis_available is False

    def test_init_is_available_false_in_fallback(self) -> None:
        with patch("thegent.orchestration.redlock_atomic._import_redis_sync", return_value=None):
            ctrl = RedlockController("k")
        assert ctrl.is_available() is False


# ---------------------------------------------------------------------------
# FR-ORC-CON-061 -- RedlockAcquireResult is frozen
# ---------------------------------------------------------------------------


class TestRedlockAcquireResultFrozen:
    """@trace FR-ORC-CON-061"""

    def test_is_dataclass(self) -> None:
        assert dataclasses.is_dataclass(RedlockAcquireResult)

    def test_is_frozen(self) -> None:
        """The result is immutable: ``frozen=True`` raises ``FrozenInstanceError`` on setattr.

        Uses ``type(result).__setattr__`` (matching the dormant
        ``test_redlock_atomic.py::test_frozen_raises_on_setattr`` pattern)
        so the assertion holds on Python 3.13 *and* 3.14 — Python 3.14
        bypasses ``object.__setattr__`` for frozen dataclasses but the
        generated descriptor still raises via ``type.__setattr__``.
        """
        result = RedlockAcquireResult(acquired=True, lock_id="x", expires_at=1.0)
        with pytest.raises(dataclasses.FrozenInstanceError):
            type(result).__setattr__(result, "acquired", False)

    def test_fields_success(self) -> None:
        result = RedlockAcquireResult(acquired=True, lock_id="abc", expires_at=99.0)
        assert result.acquired is True
        assert result.lock_id == "abc"
        assert result.expires_at == pytest.approx(99.0)

    def test_fields_failure(self) -> None:
        result = RedlockAcquireResult(acquired=False, lock_id="", expires_at=0.0)
        assert result.acquired is False
        assert result.lock_id == ""
        assert result.expires_at == 0.0


# ---------------------------------------------------------------------------
# FR-ORC-CON-062 / 063 / 064 -- RedlockController.acquire semantics
# ---------------------------------------------------------------------------


class TestRedlockControllerAcquire:
    """@trace FR-ORC-CON-062 .. FR-ORC-CON-064"""

    def test_fallback_acquire_returns_acquired_true(self) -> None:
        """Fallback acquire always succeeds for the first caller."""
        ctrl = _fallback_controller()
        result = ctrl.acquire()
        assert isinstance(result, RedlockAcquireResult)
        assert result.acquired is True
        assert len(result.lock_id) > 0
        assert result.expires_at > time.monotonic()

    def test_fallback_second_acquire_returns_false(self) -> None:
        ctrl = _fallback_controller()
        ctrl.acquire()
        second = ctrl.acquire()
        assert second.acquired is False
        assert second.lock_id == ""
        assert second.expires_at == 0.0

    def test_fallback_lock_ids_are_unique(self) -> None:
        ids = set()
        for _ in range(10):
            ctrl = _fallback_controller()
            ids.add(ctrl.acquire().lock_id)
        assert len(ids) == 10

    def test_redis_acquire_success_single_node(self) -> None:
        """A single-node Redis controller acquires when ``SET NX PX`` returns truthy."""
        ctrl = _redis_controller(clients=[_mock_redis_client(set_ok=True)])
        result = ctrl.acquire()
        assert result.acquired is True
        assert len(result.lock_id) > 0
        assert result.expires_at > time.monotonic()

    def test_redis_acquire_set_returns_false(self) -> None:
        """``SET`` returning falsy propagates to ``acquired=False``."""
        ctrl = _redis_controller(clients=[_mock_redis_client(set_ok=False)])
        result = ctrl.acquire()
        assert result.acquired is False
        assert result.lock_id == ""
        assert result.expires_at == 0.0

    def test_redis_acquire_quorum_two_of_three(self) -> None:
        """2/3 nodes succeed → quorum met."""
        clients = [
            _mock_redis_client(set_ok=True),
            _mock_redis_client(set_ok=True),
            _mock_redis_client(set_ok=False),
        ]
        ctrl = _redis_controller(clients=clients)
        result = ctrl.acquire()
        assert result.acquired is True

    def test_redis_acquire_quorum_one_of_three_fails(self) -> None:
        """1/3 nodes succeed → quorum NOT met."""
        clients = [
            _mock_redis_client(set_ok=True),
            _mock_redis_client(set_ok=False),
            _mock_redis_client(set_ok=False),
        ]
        ctrl = _redis_controller(clients=clients)
        result = ctrl.acquire()
        assert result.acquired is False

    def test_acquire_calls_set_with_nx_and_px(self) -> None:
        """The acquire path issues ``SET key value NX PX ttl_ms`` to every Redis client."""
        client = _mock_redis_client(set_ok=True)
        ctrl = _redis_controller(clients=[client])
        ctrl.acquire()
        client.set.assert_called_once()
        _, kwargs = client.set.call_args
        assert kwargs.get("nx") is True
        assert kwargs.get("px") == 5000


# ---------------------------------------------------------------------------
# FR-ORC-CON-065 -- RedlockController.release
# ---------------------------------------------------------------------------


class TestRedlockControllerRelease:
    """@trace FR-ORC-CON-065"""

    def test_fallback_release_matching_lock_id_succeeds(self) -> None:
        ctrl = _fallback_controller()
        result = ctrl.acquire()
        assert ctrl.release(result.lock_id) is True

    def test_fallback_release_wrong_lock_id_returns_false(self) -> None:
        ctrl = _fallback_controller()
        ctrl.acquire()
        assert ctrl.release("wrong-id") is False

    def test_fallback_release_allows_re_acquire(self) -> None:
        """Releasing the active lock and acquiring again returns ``acquired=True``."""
        ctrl = _fallback_controller()
        first = ctrl.acquire()
        ctrl.release(first.lock_id)
        second = ctrl.acquire()
        assert second.acquired is True

    def test_redis_release_matching_returns_true(self) -> None:
        client = _mock_redis_client(eval_result=1)
        ctrl = _redis_controller(clients=[client])
        assert ctrl.release("some-lock-id") is True

    def test_redis_release_wrong_lock_id_returns_false(self) -> None:
        client = _mock_redis_client(eval_result=0)
        ctrl = _redis_controller(clients=[client])
        assert ctrl.release("wrong-id") is False

    def test_redis_release_runs_lua_script(self) -> None:
        client = _mock_redis_client(eval_result=1)
        ctrl = _redis_controller(clients=[client])
        ctrl.release("my-lock-id")
        client.eval.assert_called_once()
        args, _ = client.eval.call_args
        script = args[0].lower()
        assert "get" in script and "del" in script


# ---------------------------------------------------------------------------
# FR-ORC-CON-066 -- RedlockController.extend
# ---------------------------------------------------------------------------


class TestRedlockControllerExtend:
    """@trace FR-ORC-CON-066"""

    def test_fallback_extend_updates_ttl(self) -> None:
        ctrl = _fallback_controller()
        result = ctrl.acquire()
        time.sleep(0.02)
        assert ctrl.extend(result.lock_id, 10000) is True

    def test_fallback_extend_wrong_lock_id_returns_false(self) -> None:
        ctrl = _fallback_controller()
        ctrl.acquire()
        assert ctrl.extend("wrong-id", 10000) is False

    def test_redis_extend_success(self) -> None:
        client = _mock_redis_client(eval_result=1)
        ctrl = _redis_controller(clients=[client])
        assert ctrl.extend("some-lock-id", 10000) is True

    def test_redis_extend_fails_wrong_owner(self) -> None:
        client = _mock_redis_client(eval_result=0)
        ctrl = _redis_controller(clients=[client])
        assert ctrl.extend("wrong-id", 10000) is False


# ---------------------------------------------------------------------------
# FR-ORC-CON-067 / 068 -- is_locked / is_available
# ---------------------------------------------------------------------------


class TestRedlockControllerQueries:
    """@trace FR-ORC-CON-067 .. FR-ORC-CON-068"""

    def test_is_locked_false_initially(self) -> None:
        assert _fallback_controller().is_locked() is False

    def test_is_locked_true_when_held(self) -> None:
        ctrl = _fallback_controller()
        ctrl.acquire()
        assert ctrl.is_locked() is True

    def test_is_locked_false_after_release(self) -> None:
        ctrl = _fallback_controller()
        result = ctrl.acquire()
        ctrl.release(result.lock_id)
        assert ctrl.is_locked() is False

    def test_redis_is_locked_true_when_exists(self) -> None:
        client = _mock_redis_client(exists=True)
        ctrl = _redis_controller(clients=[client])
        assert ctrl.is_locked() is True

    def test_redis_is_locked_false_when_not_exists(self) -> None:
        client = _mock_redis_client(exists=False)
        ctrl = _redis_controller(clients=[client])
        assert ctrl.is_locked() is False

    def test_is_available_true_with_clients(self) -> None:
        ctrl = _redis_controller()
        assert ctrl.is_available() is True


# ---------------------------------------------------------------------------
# FR-ORC-CON-069 -- make_redlock_controller factory
# ---------------------------------------------------------------------------


class TestMakeRedlockController:
    """@trace FR-ORC-CON-069"""

    def test_returns_redlock_controller(self) -> None:
        with patch("thegent.orchestration.redlock_atomic._import_redis_sync", return_value=None):
            ctrl = make_redlock_controller("my-lock")
        assert isinstance(ctrl, RedlockController)

    def test_passes_ttl_ms(self) -> None:
        with patch("thegent.orchestration.redlock_atomic._import_redis_sync", return_value=None):
            ctrl = make_redlock_controller("my-lock", ttl_ms=1234)
        assert ctrl._ttl_ms == 1234

    def test_passes_redis_nodes(self) -> None:
        with patch("thegent.orchestration.redlock_atomic._import_redis_sync", return_value=None):
            ctrl = make_redlock_controller("my-lock", redis_nodes=["redis://a:6379"])
        assert ctrl._nodes_urls == ["redis://a:6379"]

    def test_factory_fallback_functional(self) -> None:
        with patch("thegent.orchestration.redlock_atomic._import_redis_sync", return_value=None):
            ctrl = make_redlock_controller("factory-test")
        result = ctrl.acquire()
        assert result.acquired is True
        assert ctrl.release(result.lock_id) is True


# ---------------------------------------------------------------------------
# FR-ORC-CON-070 / 071 / 072 -- _InMemoryLockState
# ---------------------------------------------------------------------------


class TestInMemoryLockStateHardening:
    """@trace FR-ORC-CON-070 .. FR-ORC-CON-072"""

    @pytest.fixture
    def state(self) -> _InMemoryLockState:
        return _InMemoryLockState()

    def test_acquire_returns_true_when_free(self, state: _InMemoryLockState) -> None:
        assert state.acquire("lock-1", 5000) is True

    def test_acquire_when_locked_returns_false(self, state: _InMemoryLockState) -> None:
        state.acquire("lock-1", 5000)
        assert state.acquire("lock-2", 5000) is False

    def test_release_matching_returns_true(self, state: _InMemoryLockState) -> None:
        state.acquire("lock-1", 5000)
        assert state.release("lock-1") is True

    def test_release_wrong_id_returns_false(self, state: _InMemoryLockState) -> None:
        state.acquire("lock-1", 5000)
        assert state.release("wrong-id") is False

    def test_release_when_free_returns_false(self, state: _InMemoryLockState) -> None:
        assert state.release("nonexistent") is False

    def test_acquire_after_release(self, state: _InMemoryLockState) -> None:
        state.acquire("lock-1", 5000)
        state.release("lock-1")
        assert state.acquire("lock-2", 5000) is True

    def test_is_locked_when_held(self, state: _InMemoryLockState) -> None:
        state.acquire("lock-1", 5000)
        assert state.is_locked() is True

    def test_is_locked_when_free(self, state: _InMemoryLockState) -> None:
        assert state.is_locked() is False

    def test_is_locked_after_release(self, state: _InMemoryLockState) -> None:
        state.acquire("lock-1", 5000)
        state.release("lock-1")
        assert state.is_locked() is False

    def test_extend_updates_expiry(self, state: _InMemoryLockState) -> None:
        state.acquire("lock-1", 5000)
        before = state._expires_at
        time.sleep(0.05)
        assert state.extend("lock-1", 10000) is True
        assert state._expires_at > before

    def test_extend_wrong_id_returns_false(self, state: _InMemoryLockState) -> None:
        state.acquire("lock-1", 5000)
        assert state.extend("wrong-id", 10000) is False

    def test_expired_lock_can_be_reacquired(self, state: _InMemoryLockState) -> None:
        state.acquire("lock-1", 10)
        time.sleep(0.05)
        assert state.acquire("lock-2", 5000) is True

    def test_is_locked_false_after_expiry(self, state: _InMemoryLockState) -> None:
        state.acquire("lock-1", 10)
        time.sleep(0.05)
        assert state.is_locked() is False


# ---------------------------------------------------------------------------
# FR-ORC-CON-073 -- _parse_redis_url
# ---------------------------------------------------------------------------


class TestParseRedisUrlHardening:
    """@trace FR-ORC-CON-073"""

    def test_default_url(self) -> None:
        kw = _parse_redis_url("redis://localhost:6379")
        assert kw["host"] == "localhost"
        assert kw["port"] == 6379
        assert kw["db"] == 0
        assert "password" not in kw

    def test_custom_host_port_db(self) -> None:
        kw = _parse_redis_url("redis://redis.prod.example.com:6380/2")
        assert kw["host"] == "redis.prod.example.com"
        assert kw["port"] == 6380
        assert kw["db"] == 2

    def test_password_in_url(self) -> None:
        kw = _parse_redis_url("redis://:secret@localhost:6379")
        assert kw["password"] == "secret"


# ---------------------------------------------------------------------------
# FR-ORC-CON-074 -- _parse_node_urls_from_env
# ---------------------------------------------------------------------------


class TestParseNodeUrlsFromEnvHardening:
    """@trace FR-ORC-CON-074"""

    def test_default_single_node(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("THGENT_REDLOCK_NODES", raising=False)
        urls = _parse_node_urls_from_env()
        assert urls == ["redis://localhost:6379"]

    def test_multiple_nodes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("THGENT_REDLOCK_NODES", "redis://a:6379,redis://b:6380,redis://c:6381")
        urls = _parse_node_urls_from_env()
        assert urls == ["redis://a:6379", "redis://b:6380", "redis://c:6381"]

    def test_whitespace_stripped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("THGENT_REDLOCK_NODES", "redis://a:6379 , redis://b:6380")
        urls = _parse_node_urls_from_env()
        assert urls == ["redis://a:6379", "redis://b:6380"]


# ---------------------------------------------------------------------------
# FR-ORC-CON-075 .. 079 -- OmegaConsensus
# ---------------------------------------------------------------------------


class TestOmegaConsensusHardening:
    """@trace FR-ORC-CON-075 .. FR-ORC-CON-079"""

    def test_constructor_stores_swarm_size_and_threshold(self) -> None:
        c = OmegaConsensus(swarm_size=5, threshold=0.6)
        assert c.swarm_size == 5
        assert c.threshold == pytest.approx(0.6)

    def test_constructor_rejects_zero_swarm_size(self) -> None:
        with pytest.raises(ValueError):
            OmegaConsensus(swarm_size=0, threshold=0.5)

    def test_constructor_rejects_negative_swarm_size(self) -> None:
        with pytest.raises(ValueError):
            OmegaConsensus(swarm_size=-1, threshold=0.5)

    def test_constructor_rejects_threshold_above_one(self) -> None:
        with pytest.raises(ValueError):
            OmegaConsensus(swarm_size=3, threshold=1.5)

    def test_constructor_rejects_negative_threshold(self) -> None:
        with pytest.raises(ValueError):
            OmegaConsensus(swarm_size=3, threshold=-0.1)

    def test_propose_state_returns_string_id(self) -> None:
        c = OmegaConsensus(swarm_size=3, threshold=0.5)
        pid = c.propose_state(proposer_id="agent-master", state={"status": "x"}, metadata={})
        assert isinstance(pid, str)
        assert len(pid) > 0

    def test_proposal_ids_are_unique(self) -> None:
        c = OmegaConsensus(swarm_size=3, threshold=0.5)
        ids = {c.propose_state(proposer_id="a", state={}, metadata={}) for _ in range(10)}
        assert len(ids) == 10

    def test_cast_vote_unknown_proposal_returns_false(self) -> None:
        c = OmegaConsensus(swarm_size=3)
        assert c.cast_vote("unknown", "agent-1", True, "sig") is False

    def test_cast_vote_duplicate_voter_id_is_idempotent(self) -> None:
        """A second vote from the same ``voter_id`` on the same proposal is ignored."""
        c = OmegaConsensus(swarm_size=3, threshold=0.5)
        pid = c.propose_state(proposer_id="p", state={}, metadata={})
        assert c.cast_vote(pid, "v1", True, "s") is True
        # Duplicate vote from the same voter must not double-count.
        assert c.cast_vote(pid, "v1", True, "s") is True
        # A second voter flipping to NO should still leave the tally at 1 YES.
        assert c.finalize_consensus(pid) is False

    def test_consensus_reached_above_threshold(self) -> None:
        """4/5 YES at 60% threshold → quorum."""
        c = OmegaConsensus(swarm_size=5, threshold=0.6)
        pid = c.propose_state(proposer_id="agent-master", state={"status": "done"}, metadata={})
        for i in range(4):
            assert c.cast_vote(pid, f"voter-{i}", True, f"sig-{i}") is True
        assert c.finalize_consensus(pid) is True
        final = c.get_final_state()
        assert final is not None
        assert final.proposal_id == pid

    def test_consensus_fails_below_threshold(self) -> None:
        """7/10 YES at 80% threshold → fail."""
        c = OmegaConsensus(swarm_size=10, threshold=0.8)
        pid = c.propose_state(proposer_id="agent-master", state={"status": "failed"}, metadata={})
        for i in range(7):
            c.cast_vote(pid, f"voter-{i}", True, "sig")
        assert c.finalize_consensus(pid) is False
        assert c.get_final_state() is None

    def test_finalize_unknown_proposal_returns_false(self) -> None:
        c = OmegaConsensus(swarm_size=3)
        assert c.finalize_consensus("nope") is False

    def test_get_final_state_none_before_finalize(self) -> None:
        c = OmegaConsensus(swarm_size=3, threshold=0.5)
        assert c.get_final_state() is None


# ---------------------------------------------------------------------------
# FR-ORC-CON-080 -- RedisConcurrencyController thread safety
# ---------------------------------------------------------------------------


class TestRedisConcurrencyControllerThreadSafety:
    """@trace FR-ORC-CON-080"""

    def test_concurrent_acquires_never_exceed_max(self) -> None:
        """N threads racing on ``acquire`` cannot collectively exceed ``max_concurrent``."""
        ctrl = RedisConcurrencyController()
        ctrl.max_concurrent = 5
        barrier = threading.Barrier(20)
        results: list[bool] = []
        lock = threading.Lock()

        def _worker() -> None:
            barrier.wait()
            ok = ctrl.acquire()
            with lock:
                results.append(ok)

        threads = [threading.Thread(target=_worker) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert sum(results) == 5
        assert ctrl.current == 5

    def test_release_never_underflows_current(self) -> None:
        """Calling ``release`` without a matching ``acquire`` is a no-op."""
        ctrl = RedisConcurrencyController()
        ctrl.release()
        ctrl.release()
        assert ctrl.current == 0


# ---------------------------------------------------------------------------
# FR-ORC-CON-081 -- RedisConcurrencyController + factory surface
# ---------------------------------------------------------------------------


class TestRedisConcurrencyControllerSurface:
    """@trace FR-ORC-CON-081"""

    def test_defaults(self) -> None:
        c = RedisConcurrencyController()
        assert c.max_concurrent == 10
        assert c.current == 0

    def test_acquire_release_round_trip(self) -> None:
        c = RedisConcurrencyController()
        c.max_concurrent = 3
        for _ in range(3):
            assert c.acquire() is True
        assert c.acquire() is False
        c.release()
        assert c.acquire() is True

    def test_release_at_zero_is_noop(self) -> None:
        c = RedisConcurrencyController()
        c.release()
        assert c.current == 0

    def test_factory_clones_max_concurrent_only(self) -> None:
        cfg = RedisConfig(host="redis.example.com", port=6390, max_concurrent=7)
        ctrl = make_redis_concurrency_controller(cfg)
        assert ctrl.max_concurrent == 7
        assert cfg.host == "redis.example.com"
        assert cfg.port == 6390


# ---------------------------------------------------------------------------
# FR-ORC-CON-082 -- _InMemoryStore
# ---------------------------------------------------------------------------


class TestInMemoryStoreSurface:
    """@trace FR-ORC-CON-082"""

    @pytest.fixture
    def store(self) -> _InMemoryStore:
        return _InMemoryStore()

    def test_get_missing_returns_none(self, store: _InMemoryStore) -> None:
        assert store.get("nope") is None

    def test_set_then_get_round_trips(self, store: _InMemoryStore) -> None:
        store.set("k", "v")
        assert store.get("k") == "v"

    def test_set_with_ex_does_not_raise(self, store: _InMemoryStore) -> None:
        store.set("k", "v", ex=60)
        assert store.get("k") == "v"

    def test_delete_existing_returns_one(self, store: _InMemoryStore) -> None:
        store.set("k", "v")
        assert store.delete("k") == 1
        assert store.get("k") is None

    def test_delete_missing_returns_zero(self, store: _InMemoryStore) -> None:
        assert store.delete("nope") == 0

    def test_exists_returns_one(self, store: _InMemoryStore) -> None:
        store.set("k", "v")
        assert store.exists("k") == 1

    def test_exists_returns_zero(self, store: _InMemoryStore) -> None:
        assert store.exists("nope") == 0
