"""Tests for GW-22 (exact-match cache) and GW-26 (DualCache L1+L2).

All tests tagged with @pytest.mark.requirement("FR-CACHE-022") or
@pytest.mark.requirement("FR-CACHE-026").

# @trace FR-CACHE-022 FR-CACHE-026
"""

from __future__ import annotations

import threading
import time

import pytest

from thegent.utils.routing_impl.cache import (
    CacheEntry,
    DiskCache,
    DualCache,
    InMemoryCache,
    cache_get,
    cache_set,
    compute_cache_key,
    get_cache,
    reset_cache,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sample_response(content: str = "hello") -> dict:
    return {"choices": [{"message": {"content": content}}]}


def _sample_messages() -> list[dict]:
    return [{"role": "user", "content": "What is 2+2?"}]


# ---------------------------------------------------------------------------
# compute_cache_key
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-CACHE-022")
def test_cache_key_same_inputs_idempotent():
    """Same inputs must produce the same key every time."""
    messages = _sample_messages()
    k1 = compute_cache_key("gpt-4o", messages)
    k2 = compute_cache_key("gpt-4o", messages)
    assert k1 == k2


@pytest.mark.requirement("FR-CACHE-022")
def test_cache_key_different_model():
    """Different model names must produce different keys."""
    messages = _sample_messages()
    k1 = compute_cache_key("gpt-4o", messages)
    k2 = compute_cache_key("claude-opus-4.6", messages)
    assert k1 != k2


@pytest.mark.requirement("FR-CACHE-022")
def test_cache_key_different_messages():
    """Different messages must produce different keys."""
    k1 = compute_cache_key("gpt-4o", [{"role": "user", "content": "Hello"}])
    k2 = compute_cache_key("gpt-4o", [{"role": "user", "content": "Goodbye"}])
    assert k1 != k2


@pytest.mark.requirement("FR-CACHE-022")
def test_cache_key_kwargs_affect_key():
    """temperature and max_tokens must be included in the key."""
    messages = _sample_messages()
    k_base = compute_cache_key("gpt-4o", messages)
    k_temp = compute_cache_key("gpt-4o", messages, temperature=0.7)
    k_tokens = compute_cache_key("gpt-4o", messages, max_tokens=512)
    assert k_base != k_temp
    assert k_base != k_tokens
    assert k_temp != k_tokens


@pytest.mark.requirement("FR-CACHE-022")
def test_cache_key_length():
    """Cache key must be exactly 32 hex characters."""
    key = compute_cache_key("any-model", _sample_messages())
    assert len(key) == 32
    assert all(c in "0123456789abcdef" for c in key)


@pytest.mark.requirement("FR-CACHE-022")
def test_cache_key_tools_kwarg():
    """tools kwarg must affect the key."""
    messages = _sample_messages()
    k1 = compute_cache_key("gpt-4o", messages)
    k2 = compute_cache_key("gpt-4o", messages, tools=[{"name": "search"}])
    assert k1 != k2


@pytest.mark.requirement("FR-CACHE-022")
def test_cache_key_unrecognized_kwarg_ignored():
    """Unrecognized kwargs (e.g., stream) must NOT change the key."""
    messages = _sample_messages()
    k1 = compute_cache_key("gpt-4o", messages)
    k2 = compute_cache_key("gpt-4o", messages, stream=True)
    assert k1 == k2


# ---------------------------------------------------------------------------
# InMemoryCache
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-CACHE-022")
def test_inmemory_get_miss():
    """get() must return None on a cache miss."""
    cache = InMemoryCache()
    assert cache.get("nonexistent") is None


@pytest.mark.requirement("FR-CACHE-022")
def test_inmemory_set_get_roundtrip():
    """set() followed by get() must return the stored response."""
    cache = InMemoryCache()
    response = _sample_response("test content")
    entry = cache.set("key1", response)
    assert isinstance(entry, CacheEntry)
    retrieved = cache.get("key1")
    assert retrieved is not None
    assert retrieved.response == response


@pytest.mark.requirement("FR-CACHE-022")
def test_inmemory_expired_entry_returns_none():
    """An expired entry must return None and be evicted from the store."""
    cache = InMemoryCache()
    cache.set("expiring", _sample_response(), ttl=300.0)

    # Manually set created_at far in the past to force expiry
    full_key = "default:expiring"
    cache._store[full_key].created_at = time.monotonic() - 9999.0

    result = cache.get("expiring")
    assert result is None
    # Entry should have been evicted
    assert "default:expiring" not in cache._store


@pytest.mark.requirement("FR-CACHE-022")
def test_inmemory_eviction_when_max_size_exceeded():
    """When max_size is exceeded, the oldest entry must be evicted."""
    cache = InMemoryCache(max_size=3)
    cache.set("k1", _sample_response("1"))
    cache.set("k2", _sample_response("2"))
    cache.set("k3", _sample_response("3"))
    assert cache.size() == 3

    # Insert a 4th entry — k1 (oldest) should be evicted
    cache.set("k4", _sample_response("4"))
    assert cache.size() == 3
    assert cache.get("k1") is None  # evicted
    assert cache.get("k4") is not None


@pytest.mark.requirement("FR-CACHE-022")
def test_inmemory_clear_namespace():
    """clear(namespace) must clear only entries in that namespace."""
    cache = InMemoryCache()
    cache.set("a", _sample_response(), namespace="ns1")
    cache.set("b", _sample_response(), namespace="ns1")
    cache.set("c", _sample_response(), namespace="ns2")

    count = cache.clear(namespace="ns1")
    assert count == 2
    assert cache.get("a", namespace="ns1") is None
    assert cache.get("b", namespace="ns1") is None
    # ns2 untouched
    assert cache.get("c", namespace="ns2") is not None


@pytest.mark.requirement("FR-CACHE-022")
def test_inmemory_clear_all():
    """clear() with no namespace must clear every entry."""
    cache = InMemoryCache()
    cache.set("x", _sample_response(), namespace="ns1")
    cache.set("y", _sample_response(), namespace="ns2")

    count = cache.clear()
    assert count == 2
    assert cache.size() == 0


@pytest.mark.requirement("FR-CACHE-022")
def test_inmemory_delete():
    """delete() must remove the entry and return True; False if not found."""
    cache = InMemoryCache()
    cache.set("del_me", _sample_response())
    assert cache.delete("del_me") is True
    assert cache.get("del_me") is None
    assert cache.delete("del_me") is False


@pytest.mark.requirement("FR-CACHE-022")
def test_inmemory_thread_safety():
    """Concurrent set/get must not raise exceptions."""
    cache = InMemoryCache(max_size=100)
    errors: list[Exception] = []

    def worker(idx: int) -> None:
        try:
            for i in range(20):
                key = f"key-{idx}-{i}"
                cache.set(key, _sample_response(str(i)))
                cache.get(key)
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(t,)) for t in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Thread safety violations: {errors}"


# ---------------------------------------------------------------------------
# DiskCache
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-CACHE-022")
def test_diskcache_set_writes_file(tmp_path):
    """set() must write a JSON file at the expected path."""
    cache = DiskCache(cache_dir=str(tmp_path))
    key = "abcdef1234567890"
    cache.set(key, _sample_response())
    expected = tmp_path / "default" / key[:2] / f"{key}.json"
    assert expected.exists()


@pytest.mark.requirement("FR-CACHE-022")
def test_diskcache_set_get_roundtrip(tmp_path):
    """set() followed by get() must return the correct response."""
    cache = DiskCache(cache_dir=str(tmp_path))
    key = "roundtrip00000000"
    response = _sample_response("disk content")
    cache.set(key, response)
    entry = cache.get(key)
    assert entry is not None
    assert entry.response == response


@pytest.mark.requirement("FR-CACHE-022")
def test_diskcache_expired_returns_none_and_deletes(tmp_path):
    """An expired disk entry must return None and delete the file."""
    cache = DiskCache(cache_dir=str(tmp_path))
    key = "expiredkey000000"
    cache.set(key, _sample_response(), ttl=300.0)

    path = tmp_path / "default" / key[:2] / f"{key}.json"
    assert path.exists()

    # Rewrite file with a past created_at to force expiry
    import json as _json

    data = _json.loads(path.read_text())
    data["created_at"] = time.monotonic() - 9999.0
    path.write_text(_json.dumps(data).decode())

    result = cache.get(key)
    assert result is None
    assert not path.exists()


@pytest.mark.requirement("FR-CACHE-022")
def test_diskcache_get_miss(tmp_path):
    """get() must return None when the file does not exist."""
    cache = DiskCache(cache_dir=str(tmp_path))
    assert cache.get("doesnotexist12345") is None


@pytest.mark.requirement("FR-CACHE-022")
def test_diskcache_delete(tmp_path):
    """delete() must remove the file and return True; False if absent."""
    cache = DiskCache(cache_dir=str(tmp_path))
    key = "deletekey0000000"
    cache.set(key, _sample_response())
    assert cache.delete(key) is True
    assert cache.get(key) is None
    assert cache.delete(key) is False


@pytest.mark.requirement("FR-CACHE-022")
def test_diskcache_clear_namespace(tmp_path):
    """clear(namespace) must delete only files in that namespace."""
    cache = DiskCache(cache_dir=str(tmp_path))
    cache.set("aaaaaaaaaaaaaaaa", _sample_response(), namespace="ns1")
    cache.set("bbbbbbbbbbbbbbbb", _sample_response(), namespace="ns1")
    cache.set("cccccccccccccccc", _sample_response(), namespace="ns2")

    count = cache.clear(namespace="ns1")
    assert count == 2
    assert cache.get("aaaaaaaaaaaaaaaa", namespace="ns1") is None
    assert cache.get("cccccccccccccccc", namespace="ns2") is not None


@pytest.mark.requirement("FR-CACHE-022")
def test_diskcache_atomic_write(tmp_path):
    """set() must produce no partial files — final file must be valid JSON."""
    import json as _json

    cache = DiskCache(cache_dir=str(tmp_path))
    key = "atomickey0000000"
    cache.set(key, _sample_response("atomic"))
    path = tmp_path / "default" / key[:2] / f"{key}.json"
    # File must exist and be valid JSON (no .tmp files left behind)
    assert path.exists()
    data = _json.loads(path.read_text())
    assert data["key"] == key
    # No leftover .tmp files
    tmp_files = list(path.parent.glob("*.tmp"))
    assert not tmp_files


# ---------------------------------------------------------------------------
# DualCache
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-CACHE-026")
def test_dualcache_l1_hit():
    """get() must return L1 entry immediately without touching L2."""
    l1 = InMemoryCache()
    dual = DualCache(l1=l1, l2=None)
    dual.set("k", _sample_response("l1"))
    entry = dual.get("k")
    assert entry is not None
    assert entry.response == _sample_response("l1")


@pytest.mark.requirement("FR-CACHE-026")
def test_dualcache_l2_hit_backfills_l1(tmp_path):
    """An L2 hit must be backfilled into L1."""
    l1 = InMemoryCache()
    l2 = DiskCache(cache_dir=str(tmp_path))
    dual = DualCache(l1=l1, l2=l2)

    # Write only to L2 directly
    response = _sample_response("from l2")
    l2.set("backfill_key00000", response)

    # L1 should miss
    assert l1.get("backfill_key00000") is None

    # DualCache get must hit L2 and backfill L1
    entry = dual.get("backfill_key00000")
    assert entry is not None
    assert entry.response == response

    # L1 should now have the entry
    l1_entry = l1.get("backfill_key00000")
    assert l1_entry is not None
    assert l1_entry.response == response


@pytest.mark.requirement("FR-CACHE-026")
def test_dualcache_double_miss():
    """get() must return None when neither L1 nor L2 has the key."""
    dual = DualCache(l1=InMemoryCache(), l2=None)
    assert dual.get("absent_key") is None


@pytest.mark.requirement("FR-CACHE-026")
def test_dualcache_set_writes_both(tmp_path):
    """set() must write to both L1 and L2."""
    l1 = InMemoryCache()
    l2 = DiskCache(cache_dir=str(tmp_path))
    dual = DualCache(l1=l1, l2=l2)

    response = _sample_response("both")
    dual.set("both_key00000000", response)

    assert l1.get("both_key00000000") is not None
    assert l2.get("both_key00000000") is not None


@pytest.mark.requirement("FR-CACHE-026")
def test_dualcache_delete_removes_both(tmp_path):
    """delete() must remove the entry from both L1 and L2."""
    l1 = InMemoryCache()
    l2 = DiskCache(cache_dir=str(tmp_path))
    dual = DualCache(l1=l1, l2=l2)

    dual.set("del_both_0000000", _sample_response())
    result = dual.delete("del_both_0000000")
    assert result is True
    assert l1.get("del_both_0000000") is None
    assert l2.get("del_both_0000000") is None


@pytest.mark.requirement("FR-CACHE-026")
def test_dualcache_no_l2_works_fine():
    """DualCache(l1=..., l2=None) must operate correctly without L2."""
    dual = DualCache(l1=InMemoryCache(), l2=None)
    dual.set("no_l2_key", _sample_response("ok"))
    entry = dual.get("no_l2_key")
    assert entry is not None
    assert dual.delete("no_l2_key") is True
    assert dual.get("no_l2_key") is None


@pytest.mark.requirement("FR-CACHE-026")
def test_dualcache_clear_both(tmp_path):
    """clear() must clear both L1 and L2 and return the total count."""
    l1 = InMemoryCache()
    l2 = DiskCache(cache_dir=str(tmp_path))
    dual = DualCache(l1=l1, l2=l2)

    dual.set("a", _sample_response(), namespace="ns1")
    dual.set("b", _sample_response(), namespace="ns1")

    total = dual.clear(namespace="ns1")
    # 2 from L1 + 2 from L2 = 4
    assert total == 4
    assert l1.size() == 0


# ---------------------------------------------------------------------------
# Singleton: get_cache / reset_cache
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-CACHE-026")
def test_get_cache_returns_same_instance():
    """get_cache() must return the same DualCache object on repeated calls."""
    reset_cache()
    a = get_cache()
    b = get_cache()
    assert a is b
    reset_cache()


@pytest.mark.requirement("FR-CACHE-026")
def test_reset_cache_creates_new_instance():
    """reset_cache() must invalidate the singleton so next get_cache() is fresh."""
    reset_cache()
    first = get_cache()
    reset_cache()
    second = get_cache()
    assert first is not second
    reset_cache()


@pytest.mark.requirement("FR-CACHE-026")
def test_get_cache_l2_enabled(tmp_path, monkeypatch):
    """get_cache(l2_enabled=True) must attach a DiskCache L2."""
    reset_cache()
    # Create a new singleton with L2
    get_cache(l2_enabled=False)
    reset_cache()
    instance_l2 = get_cache(l2_enabled=True)
    assert instance_l2._l2 is not None
    assert isinstance(instance_l2._l2, DiskCache)
    reset_cache()


# ---------------------------------------------------------------------------
# Convenience functions: cache_get / cache_set
# ---------------------------------------------------------------------------


@pytest.mark.requirement("FR-CACHE-022")
def test_convenience_roundtrip():
    """cache_set then cache_get must return the stored response."""
    reset_cache()
    model = "gpt-4o"
    messages = _sample_messages()
    response = _sample_response("convenience")

    cache_set(model, messages, response, ttl=300.0)
    result = cache_get(model, messages)
    assert result == response
    reset_cache()


@pytest.mark.requirement("FR-CACHE-022")
def test_convenience_miss_returns_none():
    """cache_get must return None when the entry is not cached."""
    reset_cache()
    result = cache_get("never-cached-model", [{"role": "user", "content": "unique xyz123"}])
    assert result is None
    reset_cache()


@pytest.mark.requirement("FR-CACHE-022")
def test_convenience_key_stability():
    """Same model+messages must always map to the same cache entry."""
    reset_cache()
    model = "claude-sonnet-4.5"
    messages = [{"role": "user", "content": "Key stability test"}]
    response = _sample_response("stable")

    cache_set(model, messages, response)
    # Call cache_get multiple times — must always return the same response
    for _ in range(5):
        assert cache_get(model, messages) == response
    reset_cache()


@pytest.mark.requirement("FR-CACHE-022")
def test_convenience_different_inputs_different_keys():
    """Different model/messages must not collide in the cache."""
    reset_cache()
    r1 = _sample_response("r1")
    r2 = _sample_response("r2")
    m1 = [{"role": "user", "content": "question one"}]
    m2 = [{"role": "user", "content": "question two"}]

    cache_set("gpt-4o", m1, r1)
    cache_set("gpt-4o", m2, r2)

    assert cache_get("gpt-4o", m1) == r1
    assert cache_get("gpt-4o", m2) == r2
    reset_cache()


@pytest.mark.requirement("FR-CACHE-022")
def test_convenience_kwargs_affect_lookup():
    """cache_get with different temperature must miss even if model/messages match."""
    reset_cache()
    model = "gpt-4o"
    messages = _sample_messages()
    response = _sample_response("kwarg test")

    cache_set(model, messages, response, temperature=0.0)
    # Different temperature → different key → miss
    assert cache_get(model, messages, temperature=0.9) is None
    # Exact match → hit
    assert cache_get(model, messages, temperature=0.0) == response
    reset_cache()
