"""Tests for McpStorage and McpEventStore.

Covers:
- McpStorage get / set / delete / list_keys / clear
- McpStorage TTL expiry
- McpEventStore emit / replay / subscribe / get_event
- Singleton identity for get_mcp_storage() and get_mcp_event_store()
- MCP tool registration and round-trip for thegent_storage_get,
  thegent_storage_set, thegent_events_emit, thegent_events_replay

FR Traceability: @trace FR-MCP-STORAGE-001
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

import orjson as json
import pytest

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _json_content(result: Any) -> Any:
    """Extract JSON from a ToolResult.content (handles list[TextContent] or str)."""
    if isinstance(result, str):
        return json.loads(result)
    content = result.content
    if isinstance(content, str):
        return json.loads(content)
    if isinstance(content, list) and len(content) > 0:
        text = getattr(content[0], "text", str(content[0]))
        return json.loads(text)
    return json.loads(str(content))


# ---------------------------------------------------------------------------
# McpStorage — unit tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestMcpStorageGetSet:
    """Basic get/set operations. @trace FR-MCP-STORAGE-001"""

    def test_set_and_get_string(self, tmp_path: Path) -> None:
        """set then get returns the same string value."""
        from thegent.mcp_storage import McpStorage

        s = McpStorage(cache_dir=tmp_path / "kv")
        s.set("hello", "world")
        assert s.get("hello") == "world"

    def test_set_and_get_dict(self, tmp_path: Path) -> None:
        """set then get returns the same dict."""
        from thegent.mcp_storage import McpStorage

        s = McpStorage(cache_dir=tmp_path / "kv")
        s.set("cfg", {"a": 1, "b": [True, None]})
        assert s.get("cfg") == {"a": 1, "b": [True, None]}

    def test_get_missing_returns_default(self, tmp_path: Path) -> None:
        """get on a missing key returns the default value."""
        from thegent.mcp_storage import McpStorage

        s = McpStorage(cache_dir=tmp_path / "kv")
        assert s.get("no-such-key") is None
        assert s.get("no-such-key", default="fallback") == "fallback"

    def test_overwrite_value(self, tmp_path: Path) -> None:
        """set overwrites an existing value."""
        from thegent.mcp_storage import McpStorage

        s = McpStorage(cache_dir=tmp_path / "kv")
        s.set("k", "v1")
        s.set("k", "v2")
        assert s.get("k") == "v2"

    def test_set_none_value(self, tmp_path: Path) -> None:
        """None is a valid JSON value and can be stored."""
        from thegent.mcp_storage import McpStorage

        s = McpStorage(cache_dir=tmp_path / "kv")
        s.set("nil", None)
        # None is stored as JSON "null"; key is still present in list_keys
        assert "nil" in s.list_keys()

    def test_set_non_json_value_raises(self, tmp_path: Path) -> None:
        """Non-JSON-serialisable value raises TypeError."""
        from thegent.mcp_storage import McpStorage

        s = McpStorage(cache_dir=tmp_path / "kv")
        with pytest.raises(TypeError):
            s.set("bad", object())

    def test_empty_key_raises(self, tmp_path: Path) -> None:
        """Empty key raises ValueError."""
        from thegent.mcp_storage import McpStorage

        s = McpStorage(cache_dir=tmp_path / "kv")
        with pytest.raises(ValueError, match="non-empty"):
            s.set("", "value")
        with pytest.raises(ValueError, match="non-empty"):
            s.get("")


@pytest.mark.unit
class TestMcpStorageDelete:
    """delete() operations. @trace FR-MCP-STORAGE-001"""

    def test_delete_existing_key_returns_true(self, tmp_path: Path) -> None:
        """delete() returns True when the key existed."""
        from thegent.mcp_storage import McpStorage

        s = McpStorage(cache_dir=tmp_path / "kv")
        s.set("k", "v")
        assert s.delete("k") is True

    def test_delete_missing_key_returns_false(self, tmp_path: Path) -> None:
        """delete() returns False when the key does not exist."""
        from thegent.mcp_storage import McpStorage

        s = McpStorage(cache_dir=tmp_path / "kv")
        assert s.delete("ghost") is False

    def test_deleted_key_is_gone(self, tmp_path: Path) -> None:
        """After delete() the key is no longer present."""
        from thegent.mcp_storage import McpStorage

        s = McpStorage(cache_dir=tmp_path / "kv")
        s.set("k", "v")
        s.delete("k")
        assert s.get("k") is None
        assert "k" not in s.list_keys()

    def test_empty_key_on_delete_raises(self, tmp_path: Path) -> None:
        """delete("") raises ValueError."""
        from thegent.mcp_storage import McpStorage

        s = McpStorage(cache_dir=tmp_path / "kv")
        with pytest.raises(ValueError, match="non-empty"):
            s.delete("")


@pytest.mark.unit
class TestMcpStorageListKeys:
    """list_keys() operations. @trace FR-MCP-STORAGE-001"""

    def test_list_keys_returns_all(self, tmp_path: Path) -> None:
        """list_keys() with no prefix returns all stored keys."""
        from thegent.mcp_storage import McpStorage

        s = McpStorage(cache_dir=tmp_path / "kv")
        s.set("a", 1)
        s.set("b", 2)
        s.set("c", 3)
        assert sorted(s.list_keys()) == ["a", "b", "c"]

    def test_list_keys_with_prefix(self, tmp_path: Path) -> None:
        """list_keys(prefix=...) returns only matching keys."""
        from thegent.mcp_storage import McpStorage

        s = McpStorage(cache_dir=tmp_path / "kv")
        s.set("foo:1", 1)
        s.set("foo:2", 2)
        s.set("bar:1", 3)
        keys = s.list_keys(prefix="foo:")
        assert sorted(keys) == ["foo:1", "foo:2"]

    def test_list_keys_empty_store(self, tmp_path: Path) -> None:
        """list_keys() on an empty store returns []."""
        from thegent.mcp_storage import McpStorage

        s = McpStorage(cache_dir=tmp_path / "kv")
        assert s.list_keys() == []

    def test_clear_empties_store(self, tmp_path: Path) -> None:
        """clear() removes all keys."""
        from thegent.mcp_storage import McpStorage

        s = McpStorage(cache_dir=tmp_path / "kv")
        s.set("x", 1)
        s.set("y", 2)
        s.clear()
        assert s.list_keys() == []


@pytest.mark.unit
class TestMcpStorageTTL:
    """TTL expiry for McpStorage. @trace FR-MCP-STORAGE-001"""

    def test_expired_key_returns_default(self, tmp_path: Path) -> None:
        """A key with ttl=0.05 expires and get() returns the default."""
        from thegent.mcp_storage import McpStorage

        s = McpStorage(cache_dir=tmp_path / "kv")
        s.set("tmp", "gone-soon", ttl=0.05)
        # Before expiry: should be present
        assert s.get("tmp") == "gone-soon"
        time.sleep(0.15)
        # After expiry: should be gone
        assert s.get("tmp", default="EXPIRED") == "EXPIRED"

    def test_no_ttl_key_persists(self, tmp_path: Path) -> None:
        """A key with no TTL is still present after a short sleep."""
        from thegent.mcp_storage import McpStorage

        s = McpStorage(cache_dir=tmp_path / "kv")
        s.set("perm", "stays", ttl=None)
        time.sleep(0.05)
        assert s.get("perm") == "stays"


# ---------------------------------------------------------------------------
# McpEventStore — unit tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestMcpEventStoreEmit:
    """emit() operations. @trace FR-MCP-STORAGE-001"""

    def test_emit_returns_string_uuid(self, tmp_path: Path) -> None:
        """emit() returns a non-empty string (UUID4)."""
        from thegent.mcp_storage import McpEventStore

        store = McpEventStore(events_path=tmp_path / "events.jsonl")
        eid = store.emit("test.event", {"x": 1})
        assert isinstance(eid, str)
        assert len(eid) == 36  # UUID4 canonical length

    def test_emit_different_ids_each_call(self, tmp_path: Path) -> None:
        """Each emit() call produces a unique event_id."""
        from thegent.mcp_storage import McpEventStore

        store = McpEventStore(events_path=tmp_path / "events.jsonl")
        ids = {store.emit("t", {}) for _ in range(5)}
        assert len(ids) == 5

    def test_emit_empty_event_type_raises(self, tmp_path: Path) -> None:
        """emit() with empty event_type raises ValueError."""
        from thegent.mcp_storage import McpEventStore

        store = McpEventStore(events_path=tmp_path / "events.jsonl")
        with pytest.raises(ValueError, match="non-empty"):
            store.emit("", {"k": "v"})

    def test_emit_non_dict_payload_raises(self, tmp_path: Path) -> None:
        """emit() with non-dict payload raises TypeError."""
        from thegent.mcp_storage import McpEventStore

        store = McpEventStore(events_path=tmp_path / "events.jsonl")
        with pytest.raises(TypeError, match="dict"):
            store.emit("t", "not-a-dict")  # passing a str where dict is required

    def test_emit_non_serialisable_payload_raises(self, tmp_path: Path) -> None:
        """emit() with non-JSON-serialisable payload raises TypeError."""
        from thegent.mcp_storage import McpEventStore

        store = McpEventStore(events_path=tmp_path / "events.jsonl")
        with pytest.raises(TypeError, match="JSON-serialisable"):
            store.emit("t", {"bad": object()})


@pytest.mark.unit
class TestMcpEventStoreReplay:
    """replay() operations. @trace FR-MCP-STORAGE-001"""

    def test_replay_all_events(self, tmp_path: Path) -> None:
        """replay() with no since_id returns all events in order."""
        from thegent.mcp_storage import McpEventStore

        store = McpEventStore(events_path=tmp_path / "events.jsonl")
        id1 = store.emit("a", {"n": 1})
        id2 = store.emit("b", {"n": 2})
        id3 = store.emit("c", {"n": 3})
        events = store.replay()
        assert len(events) == 3
        assert events[0]["event_id"] == id1
        assert events[1]["event_id"] == id2
        assert events[2]["event_id"] == id3

    def test_replay_since_id(self, tmp_path: Path) -> None:
        """replay(since_id) returns events strictly after that id."""
        from thegent.mcp_storage import McpEventStore

        store = McpEventStore(events_path=tmp_path / "events.jsonl")
        id1 = store.emit("a", {})
        id2 = store.emit("b", {})
        store.emit("c", {})
        events = store.replay(since_event_id=id2)
        # Only the third event should appear
        assert len(events) == 1
        assert events[0]["event_id"] != id1
        assert events[0]["event_id"] != id2

    def test_replay_since_unknown_id_returns_all(self, tmp_path: Path) -> None:
        """replay(since_id=<unknown>) returns all events."""
        from thegent.mcp_storage import McpEventStore

        store = McpEventStore(events_path=tmp_path / "events.jsonl")
        store.emit("a", {})
        store.emit("b", {})
        events = store.replay(since_event_id="not-a-real-id")
        assert len(events) == 2

    def test_replay_empty_store(self, tmp_path: Path) -> None:
        """replay() on empty store returns []."""
        from thegent.mcp_storage import McpEventStore

        store = McpEventStore(events_path=tmp_path / "events.jsonl")
        assert store.replay() == []


@pytest.mark.unit
class TestMcpEventStoreGetEvent:
    """get_event() operations. @trace FR-MCP-STORAGE-001"""

    def test_get_event_by_id(self, tmp_path: Path) -> None:
        """get_event() returns the correct event dict."""
        from thegent.mcp_storage import McpEventStore

        store = McpEventStore(events_path=tmp_path / "events.jsonl")
        eid = store.emit("my.event", {"key": "val"})
        ev = store.get_event(eid)
        assert ev is not None
        assert ev["event_id"] == eid
        assert ev["event_type"] == "my.event"
        assert ev["payload"] == {"key": "val"}
        assert isinstance(ev["ts"], float)

    def test_get_event_missing_id_returns_none(self, tmp_path: Path) -> None:
        """get_event() returns None for an unknown event_id."""
        from thegent.mcp_storage import McpEventStore

        store = McpEventStore(events_path=tmp_path / "events.jsonl")
        store.emit("x", {})
        assert store.get_event("does-not-exist") is None

    def test_get_event_empty_id_returns_none(self, tmp_path: Path) -> None:
        """get_event("") returns None without raising."""
        from thegent.mcp_storage import McpEventStore

        store = McpEventStore(events_path=tmp_path / "events.jsonl")
        assert store.get_event("") is None


@pytest.mark.unit
class TestMcpEventStoreSubscribe:
    """subscribe() iterator. @trace FR-MCP-STORAGE-001"""

    def test_subscribe_filters_by_type(self, tmp_path: Path) -> None:
        """subscribe() yields only events matching event_type."""
        from thegent.mcp_storage import McpEventStore

        store = McpEventStore(events_path=tmp_path / "events.jsonl")
        store.emit("type.a", {"n": 1})
        store.emit("type.b", {"n": 2})
        store.emit("type.a", {"n": 3})
        results = list(store.subscribe("type.a"))
        assert len(results) == 2
        assert all(r["event_type"] == "type.a" for r in results)

    def test_subscribe_no_match_returns_empty(self, tmp_path: Path) -> None:
        """subscribe() on a type with no events returns no items."""
        from thegent.mcp_storage import McpEventStore

        store = McpEventStore(events_path=tmp_path / "events.jsonl")
        store.emit("other", {})
        results = list(store.subscribe("not.present"))
        assert results == []


# ---------------------------------------------------------------------------
# Singleton tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSingletons:
    """get_mcp_storage() and get_mcp_event_store() return consistent instances."""

    def test_storage_singleton_identity(self) -> None:
        """Two calls to get_mcp_storage() return the same object."""
        from thegent.mcp_storage import get_mcp_storage

        s1 = get_mcp_storage()
        s2 = get_mcp_storage()
        assert s1 is s2

    def test_event_store_singleton_identity(self) -> None:
        """Two calls to get_mcp_event_store() return the same object."""
        from thegent.mcp_storage import get_mcp_event_store

        e1 = get_mcp_event_store()
        e2 = get_mcp_event_store()
        assert e1 is e2

    def test_reset_singletons_replaces_instances(self, tmp_path: Path) -> None:
        """_reset_singletons_for_testing() replaces the singleton instances."""
        from thegent.mcp_storage import (
            McpEventStore,
            McpStorage,
            _reset_singletons_for_testing,
            get_mcp_event_store,
            get_mcp_storage,
        )

        new_storage = McpStorage(cache_dir=tmp_path / "kv")
        new_store = McpEventStore(events_path=tmp_path / "ev.jsonl")
        _reset_singletons_for_testing(storage=new_storage, event_store=new_store)
        assert get_mcp_storage() is new_storage
        assert get_mcp_event_store() is new_store
        # Restore originals after test
        _reset_singletons_for_testing()


# ---------------------------------------------------------------------------
# MCP tool integration tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestStorageMcpTools:
    """thegent_storage_get / thegent_storage_set round-trip via mcp_server."""

    def _make_isolated_storage(self, tmp_path: Path) -> Any:
        from thegent.mcp_storage import McpStorage, _reset_singletons_for_testing

        st = McpStorage(cache_dir=tmp_path / "kv")
        _reset_singletons_for_testing(storage=st)
        return st

    def test_storage_set_and_get_roundtrip(self, tmp_path: Path) -> None:
        """thegent_storage_set followed by thegent_storage_get returns the value."""
        # @trace FR-MCP-STORAGE-001
        self._make_isolated_storage(tmp_path)

        import thegent.mcp_server as srv

        set_result = srv.thegent_storage_set(key="greet", value='"hello"')
        set_data = _json_content(set_result)
        assert set_data["ok"] is True

        get_result = srv.thegent_storage_get(key="greet")
        get_data = _json_content(get_result)
        assert get_data["found"] is True
        assert get_data["value"] == "hello"

    def test_storage_get_missing_key(self, tmp_path: Path) -> None:
        """thegent_storage_get on missing key returns found=False, value=null."""
        self._make_isolated_storage(tmp_path)
        import thegent.mcp_server as srv

        result = srv.thegent_storage_get(key="missing-key")
        data = _json_content(result)
        assert data["found"] is False
        assert data["value"] is None

    def test_storage_set_invalid_json_value(self, tmp_path: Path) -> None:
        """thegent_storage_set with non-JSON value returns ok=False."""
        self._make_isolated_storage(tmp_path)
        import thegent.mcp_server as srv

        result = srv.thegent_storage_set(key="k", value="not-json{{{")
        data = _json_content(result)
        assert data["ok"] is False
        assert "error" in data

    def test_storage_set_with_ttl(self, tmp_path: Path) -> None:
        """thegent_storage_set with ttl_seconds is accepted without error."""
        self._make_isolated_storage(tmp_path)
        import thegent.mcp_server as srv

        result = srv.thegent_storage_set(key="temp", value='"bye"', ttl_seconds=60)
        data = _json_content(result)
        assert data["ok"] is True


@pytest.mark.unit
class TestEventsMcpTools:
    """thegent_events_emit / thegent_events_replay round-trip via mcp_server."""

    def _make_isolated_event_store(self, tmp_path: Path) -> Any:
        from thegent.mcp_storage import McpEventStore, _reset_singletons_for_testing

        es = McpEventStore(events_path=tmp_path / "ev.jsonl")
        _reset_singletons_for_testing(event_store=es)
        return es

    def test_emit_and_replay_roundtrip(self, tmp_path: Path) -> None:
        """thegent_events_emit followed by thegent_events_replay returns the event."""
        # @trace FR-MCP-STORAGE-001
        self._make_isolated_event_store(tmp_path)
        import thegent.mcp_server as srv

        emit_result = srv.thegent_events_emit(
            event_type="test.event",
            payload='{"msg": "hello"}',
        )
        emit_data = _json_content(emit_result)
        assert emit_data["ok"] is True
        event_id = emit_data["event_id"]

        replay_result = srv.thegent_events_replay(since_id=None)
        replay_data = _json_content(replay_result)
        assert replay_data["count"] >= 1
        ids = [e["event_id"] for e in replay_data["events"]]
        assert event_id in ids

    def test_emit_invalid_json_payload(self, tmp_path: Path) -> None:
        """thegent_events_emit with non-JSON payload returns ok=False."""
        self._make_isolated_event_store(tmp_path)
        import thegent.mcp_server as srv

        result = srv.thegent_events_emit(event_type="t", payload="not-json{")
        data = _json_content(result)
        assert data["ok"] is False
        assert "error" in data

    def test_emit_non_dict_json_payload(self, tmp_path: Path) -> None:
        """thegent_events_emit with JSON list payload returns ok=False."""
        self._make_isolated_event_store(tmp_path)
        import thegent.mcp_server as srv

        result = srv.thegent_events_emit(event_type="t", payload="[1,2,3]")
        data = _json_content(result)
        assert data["ok"] is False

    def test_replay_since_id(self, tmp_path: Path) -> None:
        """thegent_events_replay with since_id excludes earlier events."""
        self._make_isolated_event_store(tmp_path)
        import thegent.mcp_server as srv

        srv.thegent_events_emit(event_type="e1", payload="{}")
        r2 = srv.thegent_events_emit(event_type="e2", payload="{}")
        r2_data = _json_content(r2)
        srv.thegent_events_emit(event_type="e3", payload="{}")

        replay_result = srv.thegent_events_replay(since_id=r2_data["event_id"])
        replay_data = _json_content(replay_result)
        assert replay_data["count"] == 1
        assert replay_data["events"][0]["event_type"] == "e3"

    def test_replay_empty_returns_empty_list(self, tmp_path: Path) -> None:
        """thegent_events_replay on empty store returns count=0."""
        self._make_isolated_event_store(tmp_path)
        import thegent.mcp_server as srv

        result = srv.thegent_events_replay(since_id=None)
        data = _json_content(result)
        assert data["count"] == 0
        assert data["events"] == []
