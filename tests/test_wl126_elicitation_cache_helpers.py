from __future__ import annotations

from thegent.mcp import (
    server_cache_elicitation_response,
    server_create_elicitation_cache,
    server_default_cwd_from_context,
    server_default_owner_from_context,
    server_elicitation_cache_key,
    server_get_cached_elicitation,
    server_resolve_cwd_elicitation,
    server_resolve_owner_elicitation,
)


def test_wl126_elicitation_cache_key_is_deterministic() -> None:
    key_a = server_elicitation_cache_key("cwd?", str)
    key_b = server_elicitation_cache_key("cwd?", str)

    assert key_a == key_b
    assert len(key_a) == 16


def test_wl126_elicitation_cache_roundtrip() -> None:
    cache = server_create_elicitation_cache(maxsize=10, ttl_seconds=60)
    assert server_get_cached_elicitation(cache, prompt="cwd?", response_type=str) is None

    server_cache_elicitation_response(
        cache,
        prompt="cwd?",
        response_type=str,
        response="~/repo",
    )

    assert server_get_cached_elicitation(cache, prompt="cwd?", response_type=str) == "~/repo"


class _Meta:
    def __init__(self, *, cwd: str | None = None, owner: str | None = None) -> None:
        self.cwd = cwd
        self.owner = owner


class _RequestContext:
    def __init__(self, *, meta: _Meta | None = None) -> None:
        self.meta = meta


class _Ctx:
    def __init__(self, *, request_context: _RequestContext | None = None) -> None:
        self.request_context = request_context


class _Accepted:
    def __init__(self, data: str) -> None:
        self.data = data


class _Declined:
    pass


class _Cancelled:
    pass


def test_wl126_meta_helpers_extract_owner_and_cwd() -> None:
    ctx = _Ctx(request_context=_RequestContext(meta=_Meta(cwd="~/repo", owner="agent-e")))

    cwd = server_default_cwd_from_context(ctx)
    owner = server_default_owner_from_context(ctx)

    assert cwd is not None
    assert cwd.name == "repo"
    assert owner == "agent-e"


def test_wl126_elicitation_response_helpers_handle_cwd_statuses() -> None:
    cwd, status = server_resolve_cwd_elicitation(
        _Accepted("~/repo"),
        accepted_elicitation_type=_Accepted,
        declined_elicitation_type=_Declined,
        cancelled_elicitation_type=_Cancelled,
    )
    assert cwd is not None
    assert cwd.name == "repo"
    assert status is None

    cwd, status = server_resolve_cwd_elicitation(
        _Declined(),
        accepted_elicitation_type=_Accepted,
        declined_elicitation_type=_Declined,
        cancelled_elicitation_type=_Cancelled,
    )
    assert cwd is None
    assert status == "declined"


def test_wl126_elicitation_response_helpers_handle_owner_statuses() -> None:
    owner, status = server_resolve_owner_elicitation(
        _Accepted("agent-e"),
        default_owner_tag="fallback-owner",
        accepted_elicitation_type=_Accepted,
        declined_elicitation_type=_Declined,
        cancelled_elicitation_type=_Cancelled,
    )
    assert owner == "agent-e"
    assert status is None

    owner, status = server_resolve_owner_elicitation(
        _Cancelled(),
        default_owner_tag="fallback-owner",
        accepted_elicitation_type=_Accepted,
        declined_elicitation_type=_Declined,
        cancelled_elicitation_type=_Cancelled,
    )
    assert owner is None
    assert status == "cancelled"
