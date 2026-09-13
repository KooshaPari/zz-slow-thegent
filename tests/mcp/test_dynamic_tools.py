from __future__ import annotations

import pytest

from thegent.mcp.dynamic_tools import DynamicToolRegistry, DynamicToolSpec


def _spec(name: str) -> DynamicToolSpec:
    return DynamicToolSpec(
        name=name,
        description=f"{name} tool",
        input_schema={"type": "object", "properties": {"x": {"type": "string"}}},
    )


def test_registry_is_per_session() -> None:
    registry = DynamicToolRegistry()
    registry.register_dynamic_tool("s1", _spec("alpha"))
    registry.register_dynamic_tool("s2", _spec("beta"))

    assert [tool.name for tool in registry.list_dynamic_tools("s1")] == ["alpha"]
    assert [tool.name for tool in registry.list_dynamic_tools("s2")] == ["beta"]


def test_rejects_duplicate_tool_names_per_session() -> None:
    registry = DynamicToolRegistry()
    registry.register_dynamic_tool("s1", _spec("alpha"))

    with pytest.raises(ValueError, match="already registered"):
        registry.register_dynamic_tool("s1", _spec("alpha"))


def test_rejects_blank_tool_description() -> None:
    registry = DynamicToolRegistry()
    with pytest.raises(ValueError, match=r"tool_spec.description must be non-empty"):
        registry.register_dynamic_tool(
            "s1",
            DynamicToolSpec(
                name="alpha", description="   ", input_schema={"type": "object"}
            ),
        )


def test_create_and_resolve_dynamic_tool_call() -> None:
    registry = DynamicToolRegistry()
    registry.register_dynamic_tool("s1", _spec("alpha"))

    call = registry.create_tool_call("s1", "alpha", {"x": "v1"})
    event = registry.tool_call_requested_event(call)
    assert event["event"] == "tool_call_requested"
    assert event["callId"] == call.call_id
    assert event["name"] == "alpha"
    assert event["arguments"] == {"x": "v1"}
    assert event["timeoutSeconds"] == 30.0
    assert "requestedAt" in event
    assert "expiresAt" in event

    pending = registry.get_pending_call(call.call_id)
    assert pending.call_id == call.call_id

    result = registry.resolve_tool_call(call.call_id, {"ok": True}, success=True)
    assert result.call_id == call.call_id
    assert result.success is True
    assert result.output == {"ok": True}
    event = registry.tool_call_completed_event(result)
    assert event["event"] == "tool_call_completed"
    assert event["callId"] == call.call_id
    assert event["output"] == {"ok": True}
    assert event["success"] is True

    with pytest.raises(KeyError, match="unknown dynamic call id"):
        registry.get_pending_call(call.call_id)


def test_pending_calls_for_session_filters_other_sessions() -> None:
    registry = DynamicToolRegistry()
    registry.register_dynamic_tool("s1", _spec("alpha"))
    registry.register_dynamic_tool("s2", _spec("beta"))
    registry.create_tool_call("s1", "alpha", {"x": "a"})
    registry.create_tool_call("s2", "beta", {"x": "b"})

    assert len(registry.pending_calls_for_session("s1")) == 1
    assert registry.pending_calls_for_session("s1")[0].session_id == "s1"


def test_resolve_tool_call_for_session_enforces_ownership() -> None:
    registry = DynamicToolRegistry()
    registry.register_dynamic_tool("s1", _spec("alpha"))
    call = registry.create_tool_call("s1", "alpha", {"x": "a"})

    with pytest.raises(KeyError, match="does not belong"):
        registry.resolve_tool_call_for_session(
            "s2", call.call_id, {"ok": True}, success=True
        )

    result = registry.resolve_tool_call_for_session(
        "s1", call.call_id, {"ok": True}, success=True
    )
    assert result.success is True


def test_resolve_tool_call_for_session_normalizes_session_id() -> None:
    registry = DynamicToolRegistry()
    registry.register_dynamic_tool("s1", _spec("alpha"))
    call = registry.create_tool_call("s1", "alpha", {"x": "a"})

    result = registry.resolve_tool_call_for_session(
        "  s1  ", call.call_id, {"ok": True}, success=True
    )
    assert result.success is True


def test_clear_session_removes_tools_and_pending_calls() -> None:
    registry = DynamicToolRegistry()
    registry.register_dynamic_tool("s1", _spec("alpha"))
    registry.register_dynamic_tool("s2", _spec("beta"))
    registry.create_tool_call("s1", "alpha", {"x": "a"})
    registry.create_tool_call("s2", "beta", {"x": "b"})

    registry.clear_session("s1")
    assert registry.list_dynamic_tools("s1") == []
    assert registry.pending_calls_for_session("s1") == []
    assert len(registry.pending_calls_for_session("s2")) == 1


def test_create_call_requires_registered_tool() -> None:
    registry = DynamicToolRegistry()
    with pytest.raises(KeyError, match="not registered"):
        registry.create_tool_call("s1", "unknown", {})


def test_create_call_rejects_non_positive_timeout() -> None:
    registry = DynamicToolRegistry()
    registry.register_dynamic_tool("s1", _spec("alpha"))
    with pytest.raises(ValueError, match="timeout_seconds must be > 0"):
        registry.create_tool_call("s1", "alpha", {"x": "a"}, timeout_seconds=0)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_create_call_rejects_non_finite_timeout(value: float) -> None:
    registry = DynamicToolRegistry()
    registry.register_dynamic_tool("s1", _spec("alpha"))
    with pytest.raises(ValueError, match="timeout_seconds must be > 0"):
        registry.create_tool_call("s1", "alpha", {"x": "a"}, timeout_seconds=value)


def test_create_call_rejects_non_object_arguments() -> None:
    registry = DynamicToolRegistry()
    registry.register_dynamic_tool("s1", _spec("alpha"))
    with pytest.raises(ValueError, match="arguments must be a JSON object"):
        registry.create_tool_call("s1", "alpha", ["not", "an", "object"])  # type: ignore[arg-type]


def test_resolve_tool_call_rejects_non_boolean_success_flag() -> None:
    registry = DynamicToolRegistry()
    registry.register_dynamic_tool("s1", _spec("alpha"))
    call = registry.create_tool_call("s1", "alpha", {"x": "a"})
    with pytest.raises(ValueError, match="success must be a boolean"):
        registry.resolve_tool_call(call.call_id, {"ok": True}, success="yes")  # type: ignore[arg-type]


def test_create_call_rejects_empty_session_id() -> None:
    registry = DynamicToolRegistry()
    registry.register_dynamic_tool("s1", _spec("alpha"))
    with pytest.raises(ValueError, match="session_id must be non-empty"):
        registry.create_tool_call("   ", "alpha", {"x": "a"})


def test_registry_normalizes_session_and_tool_names() -> None:
    registry = DynamicToolRegistry()
    registered = registry.register_dynamic_tool("  s1  ", _spec("  alpha  "))
    assert registered.name == "alpha"
    call = registry.create_tool_call("s1", "alpha", {"x": "a"})
    assert call.session_id == "s1"
    assert call.name == "alpha"
    assert len(registry.pending_calls_for_session("  s1  ")) == 1


def test_list_dynamic_tools_rejects_empty_session_id() -> None:
    registry = DynamicToolRegistry()
    with pytest.raises(ValueError, match="session_id must be non-empty"):
        registry.list_dynamic_tools("   ")


def test_list_dynamic_tools_rejects_non_string_session_id() -> None:
    registry = DynamicToolRegistry()
    with pytest.raises(ValueError, match="session_id must be a string"):
        registry.list_dynamic_tools(123)  # type: ignore[arg-type]


def test_pending_calls_for_session_rejects_empty_session_id() -> None:
    registry = DynamicToolRegistry()
    with pytest.raises(ValueError, match="session_id must be non-empty"):
        registry.pending_calls_for_session("")


def test_clear_session_rejects_empty_session_id() -> None:
    registry = DynamicToolRegistry()
    with pytest.raises(ValueError, match="session_id must be non-empty"):
        registry.clear_session("\t")


def test_expired_call_is_removed_and_raises_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = DynamicToolRegistry(default_timeout_seconds=0.1)
    registry.register_dynamic_tool("s1", _spec("alpha"))

    monotonic_values = iter([100.0, 100.2, 100.2])
    monkeypatch.setattr(
        "thegent.mcp.dynamic_tools.time.monotonic", lambda: next(monotonic_values)
    )
    call = registry.create_tool_call("s1", "alpha", {"x": "v1"})

    with pytest.raises(TimeoutError, match="expired"):
        registry.get_pending_call(call.call_id)

    assert registry.pending_calls_for_session("s1") == []
