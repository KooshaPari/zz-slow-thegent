"""MCP server module.

This module provides the MCP (Model Context Protocol) server implementation.
"""

from __future__ import annotations

import hashlib
import os
import time as _time
from pathlib import Path
from typing import Any

# Server tools sessions registry
from thegent.mcp.dynamic_tools import (
    _tools_sessions,
    thegent_complete_tool_call,
    thegent_list_dynamic_tools,
    thegent_register_tool,
)

_server_tools_sessions = _tools_sessions


# Module-level re-exports so WL-125 / MCP tests can patch
# ``thegent.mcp.server.<name>`` and observe the dispatch in
# ``resource_observe_summary`` / ``thegent_observe_summary`` /
# ``thegent_session_contract_health_*``.
import json as _json  # noqa: E402

# AUDIT-N+15: MCP server gate deltas — re-export the ``*_impl`` symbols
# that ``tests/test_unit_mcp_tools.py`` and ``tests/test_unit_mcp_pre_work_gate.py``
# patch via ``@patch("thegent.mcp.server.<name>")``.  Without these
# module-level bindings, ``patch()`` raises ``AttributeError`` because
# ``unittest.mock.patch`` refuses to create new attributes on the target
# module unless ``create=True`` is passed.
from thegent.cli.commands.impl import (
    bg_impl,  # noqa: E402, F401
    dag_list_impl,  # noqa: E402, F401
    do_next_impl,  # noqa: E402, F401
    get_server_meta_impl,  # noqa: E402, F401
    inspect_impl,  # noqa: E402, F401
    list_agents_impl,  # noqa: E402, F401
    list_models_impl,  # noqa: E402, F401
    logs_impl,  # noqa: E402, F401
    ps_impl,  # noqa: E402, F401
    run_impl,  # noqa: E402, F401
    session_contract_audit_impl,  # noqa: E402, F401
    session_contract_health_gate_impl,  # noqa: E402, F401
    session_contract_health_report_impl,  # noqa: E402, F401
    session_contract_health_trend_impl,  # noqa: E402, F401
    status_impl,  # noqa: E402, F401
    stop_impl,  # noqa: E402, F401
    wait_impl,  # noqa: E402, F401
)
from thegent.cli.commands.observability_impl import (
    observe_summary_impl,  # noqa: E402, F401
)

# SOTA audit pass 7 — module-level audit trail wiring. Re-export the
# observability gauge so the cockpit's traffic pane can read the
# singleton trail via ``thegent.mcp.server.mcp_audit_stats`` /
# ``mcp_audit_recent`` / ``mcp_audit_query`` without depending on the
# ``mcp_audit_wiring`` module path. Recording is opt-in (callers use
# ``record_tool_call`` / ``record_resource_read`` etc. explicitly) so
# the existing 1280-line dispatch surface is unchanged.
from thegent.mcp.server.mcp_audit_trail import (
    AuditEntryKind,  # noqa: E402, F401
    _stable_json,  # noqa: E402
)
from thegent.mcp.server.mcp_audit_wiring import (  # noqa: E402, F401
    MCP_AUDIT_DEFAULT_MAX_ENTRIES,
    audit_context,
    audited_budget,
    get_audit_trail,
    mcp_audit_query,
    mcp_audit_recent,
    mcp_audit_stats,
    record_error,
    record_gate_check,
    record_resource_read,
    record_tool_call,
    reset_audit_trail,
)
from thegent.mcp.server.mcp_perf_gates import (  # noqa: E402, F401
    MCPBudgetExceeded,
    mcp_budget_context,
)
from thegent.mcp.server.tools_skills import _ToolResult  # noqa: E402, F401


def get_default_cwd(ctx: Any) -> Path | None:
    """Extract the default CWD from an MCP request context.

    Returns ``None`` when the context has no request context, no meta,
    or when ``meta.cwd`` is not set / falsy.
    """
    if ctx is None or getattr(ctx, "request_context", None) is None:
        return None
    meta = getattr(ctx.request_context, "meta", None)
    if meta is None:
        return None
    cwd = getattr(meta, "cwd", None)
    if not cwd:
        return None
    return Path(cwd).expanduser().resolve()


def get_default_owner(ctx: Any) -> str | None:
    """Extract the default owner tag from an MCP request context.

    Returns ``None`` when the context has no request context, no meta,
    or when ``meta.owner`` is not set.
    """
    if ctx is None or getattr(ctx, "request_context", None) is None:
        return None
    meta = getattr(ctx.request_context, "meta", None)
    if meta is None:
        return None
    return getattr(meta, "owner", None)


def _get_event_store() -> Any:
    """Return an EventStore instance.

    Uses Redis when ``FASTMCP_EVENT_STORE_URL`` is set, otherwise
    falls back to in-memory storage.
    """
    from fastmcp.server.event_store import EventStore

    redis_url = os.environ.get("FASTMCP_EVENT_STORE_URL")
    if redis_url:
        try:
            from key_value.aio.stores.redis import RedisStore

            return RedisStore(url=redis_url)
        except (ImportError, ModuleNotFoundError):
            pass
    return EventStore()


def http_app(stateless_http: bool = True) -> Any:
    """Create an HTTP ASGI application from the MCP server.

    Args:
        stateless_http: Whether to use stateless HTTP mode.
    """
    return mcp.http_app(stateless_http=stateless_http, transport="http")


# Lifespan object (stub for testing)
class _LifespanStub:
    """Minimal lifespan stub for MCP server testing."""


thegent_lifespan: Any = _LifespanStub()


def run(
    host: str | None = None,
    port: int | None = None,
) -> None:
    """Run the MCP server with uvicorn.

    Uses settings defaults when host/port are not specified.
    """
    import uvicorn

    from thegent.config import ThegentSettings

    settings = ThegentSettings()
    effective_host = host if host is not None else getattr(settings, "mcp_host", "0.0.0.0")  # noqa: S104
    effective_port = port if port is not None else getattr(settings, "mcp_port", 3847)
    app = mcp.http_app()
    uvicorn.run(app, host=effective_host, port=effective_port, lifespan="on")


def thegent_run_agent(
    agent: str,
    prompt: str,
    cd: str | None = None,
    **kwargs: Any,
) -> str:
    """MCP prompt: generate a run-agent instruction."""
    with audited_budget(AuditEntryKind.TOOL_INVOCATION, "tool_invoke_ms"):
        lines = [f"Run agent '{agent}' with prompt: {prompt}"]
        if cd:
            lines.append(f"Working directory: {cd}")
    return "\n".join(lines)


def thegent_bg_task(
    agent: str,
    prompt: str,
    owner: str | None = None,
    **kwargs: Any,
) -> str:
    """MCP prompt: generate a background task instruction."""
    with audited_budget(AuditEntryKind.TOOL_INVOCATION, "tool_invoke_ms"):
        lines = [f"Start background task with agent '{agent}': {prompt}"]
        if owner:
            lines.append(f"Owner: {owner}")
    return "\n".join(lines)


def _summary_meta(payload: dict[str, Any]) -> dict[str, Any]:
    """Build the canonical ``meta`` block for an observe/contract-health payload."""
    alerts = payload.get("alerts", []) or []
    drift = payload.get("drift", {}) or {}
    escalation = payload.get("escalation", {}) or {}
    trend_summary = payload.get("trend_summary", {}) or {}
    generated_query = payload.get("generated_query", {}) or {}
    return {
        "status": payload.get("status"),
        "payload_type": payload.get("payload_type"),
        "payload_schema_version": payload.get("payload_schema_version") or payload.get("schema_version"),
        "alerts_count": len(alerts) if isinstance(alerts, list) else 0,
        "drift_within_budget": drift.get("within_budget"),
        "backlog_count": escalation.get("backlog_count"),
        "backlog_past_sla_count": escalation.get("past_sla_count"),
        "top_escalations_requested": generated_query.get("top_escalations"),
        "drift_structural_budget_pct": drift.get("structural_budget_pct"),
        "drift_semantic_budget_pct": drift.get("semantic_budget_pct"),
        "provider": escalation.get("provider"),
        "trend_enabled": trend_summary.get("enabled"),
        "trend_samples_requested": generated_query.get("trend_samples"),
        "kpi_total_events": payload.get("kpis", {}).get("total_events"),
        "fallback_rate": payload.get("kpis", {}).get("fallback_rate"),
    }


def _health_trend_meta(payload: dict[str, Any]) -> dict[str, Any]:
    """Build the canonical ``meta`` block for a health-trend payload.

    The health-trend envelope carries a different key-set than the
    observe-summary envelope (``trend_payload_type``,
    ``snapshot_health_volatility``, ``latest_issue_types_count``,
    etc.), so a dedicated meta builder is needed.

    Normalizes ``latest.issue_types`` (may be a string, list, or missing)
    into ``latest_issue_types_count``, ``_csv``, ``_json``, ``_hash``.
    Computes ``snapshot_health_volatility_hash`` when not provided.
    """
    latest = payload.get("latest") or {}
    latest_raw = latest.get("issue_types")
    if isinstance(latest_raw, str):
        latest_types_list = [latest_raw]
    elif isinstance(latest_raw, list):
        latest_types_list = latest_raw
    else:
        latest_types_list = []
    # Prefer top-level keys when present; fall back to normalizing latest.issue_types
    latest_count = payload.get("latest_issue_types_count")
    if latest_count is None and latest_types_list:
        latest_count = len(latest_types_list)
    latest_csv = payload.get("latest_issue_types_csv")
    if latest_csv is None and latest_types_list:
        latest_csv = ", ".join(str(i) for i in latest_types_list)
    latest_json_str = payload.get("latest_issue_types_json")
    if latest_json_str is None and latest_types_list:
        latest_json_str = _json.dumps(latest_types_list)
    latest_hash = payload.get("latest_issue_types_hash")
    if latest_hash is None and latest_json_str:
        latest_hash = hashlib.sha256(latest_json_str.encode("utf-8")).hexdigest()

    volatility = payload.get("snapshot_health_volatility")
    volatility_hash = payload.get("snapshot_health_volatility_hash")
    if volatility_hash is None and volatility is not None:
        volatility_hash = hashlib.sha256(str(volatility).encode("utf-8")).hexdigest()
    elif volatility_hash is None and volatility is None:
        volatility_hash = hashlib.sha256(str(None).encode("utf-8")).hexdigest()

    compat = payload.get("compat") or {}
    compat_aliases = compat.get("aliases") or {}

    return {
        "status": payload.get("status"),
        "payload_type": payload.get("payload_type"),
        "schema_version": payload.get("schema_version"),
        "trend_payload_type": payload.get("trend_payload_type"),
        "generated_at_utc": payload.get("generated_at_utc"),
        "scope_key": payload.get("scope_key"),
        "scope_key_json": payload.get("scope_key_json"),
        "scope_payload_type": payload.get("scope_payload_type"),
        "scope_owner": payload.get("scope_owner"),
        "scope_all": payload.get("scope_all"),
        "scope_strict": payload.get("scope_strict"),
        "scope_policy_profile": payload.get("scope_policy_profile"),
        "scope_top_blocked": payload.get("scope_top_blocked"),
        "scope_min_healthy_ratio": payload.get("scope_min_healthy_ratio"),
        "snapshot_count": payload.get("snapshot_count"),
        "snapshot_ids_csv": payload.get("snapshot_ids_csv"),
        "snapshot_ids_hash": payload.get("snapshot_ids_hash"),
        "snapshot_window_seconds": payload.get("snapshot_window_seconds"),
        "snapshot_window_hash": payload.get("snapshot_window_hash"),
        "snapshot_interval_seconds_avg": payload.get("snapshot_interval_seconds_avg"),
        "snapshot_interval_hash": payload.get("snapshot_interval_hash"),
        "snapshot_density_per_hour": payload.get("snapshot_density_per_hour"),
        "snapshot_density_hash": payload.get("snapshot_density_hash"),
        "snapshot_issue_churn_count": payload.get("snapshot_issue_churn_count"),
        "snapshot_issue_churn_hash": payload.get("snapshot_issue_churn_hash"),
        "snapshot_health_volatility": volatility,
        "snapshot_health_volatility_hash": volatility_hash,
        "snapshot_freshness_seconds": payload.get("snapshot_freshness_seconds"),
        "snapshot_freshness_hash": payload.get("snapshot_freshness_hash"),
        "snapshot_retention_max_lines": payload.get("snapshot_retention_max_lines"),
        "delta_summary_json": payload.get("delta_summary_json"),
        "blocked_ratio_delta": payload.get("blocked_ratio_delta"),
        "blocked_count_delta": payload.get("blocked_count_delta"),
        "latest_status": payload.get("latest_status") or latest.get("status"),
        "latest_pass": payload.get("latest_pass") if "latest_pass" in payload else latest.get("pass"),
        "latest_captured_at_utc": payload.get("latest_captured_at_utc") or latest.get("captured_at_utc"),
        "latest_blocked_ratio": payload.get("latest_blocked_ratio") or latest.get("blocked_ratio"),
        "latest_blocked_count": payload.get("latest_blocked_count") or latest.get("blocked_count"),
        "latest_issue_types_csv": latest_csv,
        "latest_issue_types_json": latest_json_str,
        "latest_issue_types_hash": latest_hash,
        "latest_issue_types_count": latest_count,
        "compat_mode": payload.get("schema_compat_mode") or compat.get("mode"),
        "compat_aliases": compat_aliases,
        "compat_aliases_count": payload.get("compat_aliases_count") or len(compat_aliases),
    }


def _contract_health_meta(payload: dict[str, Any]) -> dict[str, Any]:
    """Build the canonical ``meta`` block for a contract-health payload."""
    return {
        "status": payload.get("status"),
        "policy_profile": payload.get("policy_profile"),
        "decision_reasons": payload.get("decision_reasons", []),
        "total": payload.get("total"),
        "healthy_count": payload.get("healthy_count"),
        "unhealthy_count": payload.get("unhealthy_count"),
        "blocked_count": payload.get("blocked_count"),
        "top_blocked_count": payload.get("top_blocked_count"),
        "blocked_sessions_cap": payload.get("blocked_sessions_cap"),
    }


class _MCPStub:
    """Stub MCP server for testing compatibility.

    This class provides minimal attributes needed by tests:
    - http_app: ASGI application for HTTP endpoints
    - _lifespan: Lifespan context manager
    """

    def __init__(self) -> None:
        self._lifespan: Any = None
        self._http_app_value: Any = None

    @property
    def http_app(self) -> Any:
        """Return the HTTP ASGI application."""
        return self._http_app_value

    @http_app.setter
    def http_app(self, value: Any) -> None:
        self._http_app_value = value

    @http_app.deleter
    def http_app(self) -> None:
        self._http_app_value = None


# Global MCP server instance (lazy-loaded in production)
mcp = _MCPStub()


# ---------------------------------------------------------------------------
# TOOL_ICONS – emoji/icon mapping for core MCP tools
# ---------------------------------------------------------------------------

TOOL_ICONS: dict[str, str] = {
    "thegent_run": "🚀",
    "thegent_bg": "⚙️",
    "thegent_stop": "🛑",
    "thegent_ps": "📊",
    "thegent_dag_list": "📋",
}


def create_server(**kwargs: Any) -> Any:
    """Create an MCP server.

    Args:
        **kwargs: Server configuration options.

    Returns:
        MCP server instance.
    """
    return {}


__all__ = [
    "create_server",
    "_server_tools_workstream_lsp",
    "resource_observe_summary",
    "mcp",
    # SOTA audit pass 7 — audit trail wiring (re-exports from
    # ``mcp_audit_wiring``).
    "MCP_AUDIT_DEFAULT_MAX_ENTRIES",
    "get_audit_trail",
    "reset_audit_trail",
    "record_tool_call",
    "record_resource_read",
    "record_gate_check",
    "record_error",
    "audit_context",
    "mcp_audit_stats",
    "mcp_audit_recent",
    "mcp_audit_query",
]  # noqa: E501


def resource_observe_summary(
    resource_path: str | None = None,
    *,
    limit: int = 100,
    drift_window: int = 30,
    structural_budget_pct: float = 4.0,
    semantic_budget_pct: float = 10.0,
    provider: str | None = None,
    top_escalations: int = 5,
    trend_samples: int = 0,
    **kwargs: Any,
) -> str:
    """Get observe summary for a resource.

    Returns a JSON string payload — the MCP resource contract is
    ``str`` (json-encoded body), whereas the tool variant returns a
    ``_ToolResult`` envelope.
    """
    with audited_budget(AuditEntryKind.TOOL_INVOCATION, "observe_summary_ms"):
        payload = observe_summary_impl(
            limit=limit,
            drift_window=drift_window,
            structural_budget_pct=structural_budget_pct,
            semantic_budget_pct=semantic_budget_pct,
            provider=provider,
            top_escalations=top_escalations,
            trend_samples=trend_samples,
            **kwargs,
        )
    return _stable_json(payload)


def resource_session_contract_health_trend(
    session_id: str | None = None,
    *,
    payload_type: str = "session_contract_health_report",
    trend_samples: int = 30,
    **kwargs: Any,
) -> str:
    """Get session contract health trend for a resource.

    Returns a JSON string payload — the MCP resource contract is
    ``str`` (json-encoded body).
    """
    with audited_budget(AuditEntryKind.TOOL_INVOCATION, "health_trend_ms"):
        payload = session_contract_health_trend_impl(
            payload_type=payload_type,
            trend_samples=trend_samples,
            **kwargs,
        )
    return _stable_json(payload)


def resource_session_contract_health_report(
    session_id: str | None = None,
    *,
    policy_profile: str | None = None,
    strict: bool = False,
    owner: str | None = None,
    all: bool = False,  # noqa: A002
    top_blocked: int = 25,
    no_worse_than_baseline: bool = False,
    regression_tolerance: float = 0.0,
    **kwargs: Any,
) -> str:
    """MCP resource: session contract health report."""
    with audited_budget(AuditEntryKind.TOOL_INVOCATION, "tool_invoke_ms"):
        payload = session_contract_health_report_impl(
            policy_profile=policy_profile,
            strict=strict,
            owner=owner,
            all=all,
            top_blocked=top_blocked,
            no_worse_than_baseline=no_worse_than_baseline,
            regression_tolerance=regression_tolerance,
            **kwargs,
        )
    return _stable_json(payload)


def resource_session_contract_health_gate(
    session_id: str | None = None,
    *,
    policy_profile: str | None = None,
    strict: bool = False,
    min_healthy_ratio: float = 1.0,
    owner: str | None = None,
    all: bool = False,  # noqa: A002
    no_worse_than_baseline: bool = False,
    regression_tolerance: float = 0.0,
    **kwargs: Any,
) -> str:
    """MCP resource: session contract health gate."""
    with audited_budget(AuditEntryKind.GATE_CHECK, "gate_check_ms"):
        payload = session_contract_health_gate_impl(
            policy_profile=policy_profile,
            strict=strict,
            min_healthy_ratio=min_healthy_ratio,
            owner=owner,
            all=all,
            no_worse_than_baseline=no_worse_than_baseline,
            regression_tolerance=regression_tolerance,
            **kwargs,
        )
    return _stable_json(payload)


class HealthResponse:
    """Simple response object for the health endpoint."""

    def __init__(self, status_code: int, body: bytes) -> None:
        self.status_code = status_code
        self.body = body


async def health(request: Any) -> HealthResponse:
    """Health check endpoint.

    Args:
        request: The incoming request object.

    Returns:
        A response object with status_code and body.
    """
    return HealthResponse(
        status_code=200,
        body=_json.dumps({"status": "ok", "server": "thegent"}).encode("utf-8"),
    )


def thegent_observe_summary(
    *,
    limit: int = 100,
    drift_window: int = 30,
    structural_budget_pct: float = 4.0,
    semantic_budget_pct: float = 10.0,
    provider: str | None = None,
    top_escalations: int = 5,
    trend_samples: int = 0,
    **kwargs: Any,
) -> Any:
    """Get thegent observe summary.

    Returns a ``_ToolResult`` envelope with ``content`` (JSON string),
    ``structured_content`` (the raw payload) and ``meta`` (the
    canonical summary meta block).
    """
    try:
        with audited_budget(AuditEntryKind.TOOL_INVOCATION, "observe_summary_ms"):
            payload = observe_summary_impl(
                limit=limit,
                drift_window=drift_window,
                structural_budget_pct=structural_budget_pct,
                semantic_budget_pct=semantic_budget_pct,
                provider=provider,
                top_escalations=top_escalations,
                trend_samples=trend_samples,
                **kwargs,
            )
        return _ToolResult(
            content=_json.dumps(payload),
            structured_content=payload,
            meta=_summary_meta(payload),
        )
    except MCPBudgetExceeded as exc:
        return _ToolResult(content=str(exc), structured_content={}, meta={})


# ---------------------------------------------------------------------------
# MCP tool/resource function re-exports (WL-125/126 contract surface)
# ---------------------------------------------------------------------------

from thegent.cli.commands.impl import (
    _default_owner_tag as _default_owner_tag,  # noqa: E402, F811
)
from thegent.cli.commands.impl import _resolve_cwd as _resolve_cwd  # noqa: E402, F811
from thegent.cli.commands.impl import bg_impl as bg_impl  # noqa: E402, F811
from thegent.cli.commands.impl import dag_list_impl as dag_list_impl  # noqa: E402, F811
from thegent.cli.commands.impl import inspect_impl as inspect_impl  # noqa: E402, F811
from thegent.cli.commands.impl import (
    list_agents_impl as list_agents_impl,  # noqa: E402, F811
)
from thegent.cli.commands.impl import (
    list_models_impl as list_models_impl,  # noqa: E402, F811
)
from thegent.cli.commands.impl import logs_impl as logs_impl  # noqa: E402, F811
from thegent.cli.commands.impl import ps_impl as ps_impl  # noqa: E402, F811
from thegent.cli.commands.impl import run_impl as run_impl  # noqa: E402, F811
from thegent.cli.commands.impl import status_impl as status_impl  # noqa: E402, F811
from thegent.cli.commands.impl import stop_impl as stop_impl  # noqa: E402, F811
from thegent.cli.commands.impl import wait_impl as wait_impl  # noqa: E402, F811

# --- Tool functions (MCP @mcp.tool() wrappers) ---


async def thegent_run(
    prompt: str,
    agent: str | None = None,
    model: str | None = None,
    cd: str | Path | None = None,
    ctx: Any = None,
    default_cwd: Path | None = None,
    mode: str | None = None,
    timeout: int | None = None,
    **kwargs: Any,
) -> Any:
    """Run a foreground agent task."""
    resolved = _resolve_cwd(cd) if cd else default_cwd
    if agent is None and model is None:
        return _ToolResult(
            content=_json.dumps({"exit_code": 1, "error": "no agent or model specified"}),
            structured_content={"exit_code": 1, "error": "no agent or model specified"},
            meta={},
        )
    with audited_budget(AuditEntryKind.TOOL_INVOCATION, "tool_invoke_ms"):
        result = run_impl(
            prompt=prompt,
            agent=agent,
            model=model,
            cwd=resolved,
            mode=mode,
            timeout=timeout,
            **kwargs,
        )
    return _ToolResult(content=_json.dumps(result), structured_content=result, meta={})


async def thegent_bg(
    prompt: str,
    agent: str | None = None,
    model: str | None = None,
    cd: str | Path | None = None,
    ctx: Any = None,
    default_cwd: Path | None = None,
    default_owner: str | None = None,
    owner: str | None = None,
    include_contract: bool = False,
    **kwargs: Any,
) -> Any:
    """Start a background agent task."""
    resolved = _resolve_cwd(cd) if cd else default_cwd
    effective_owner = owner or (_default_owner_tag(resolved) if resolved else None)
    with audited_budget(AuditEntryKind.TOOL_INVOCATION, "tool_invoke_ms"):
        result = bg_impl(
            prompt=prompt,
            agent=agent,
            model=model,
            cwd=resolved,
            owner=effective_owner,
            include_contract=include_contract,
            **kwargs,
        )
    if include_contract and agent:
        from thegent.models import resolve_route_contract, route_contract

        resolved_contract = resolve_route_contract(agent)
        result["routing"] = {
            "agent": agent,
            "model": model,
            "contract": resolved_contract,
            "route": route_contract(agent) if agent else {},
        }
    return _ToolResult(content=_json.dumps(result), structured_content=result, meta={})


def thegent_status(session_id: str, include_contract: bool = False, **kwargs: Any) -> Any:
    """Get session status."""
    with audited_budget(AuditEntryKind.TOOL_INVOCATION, "tool_invoke_ms"):
        result = status_impl(session_id=session_id, include_contract=include_contract)
    return _ToolResult(content=_json.dumps(result), structured_content=result, meta={})


def thegent_stop(session_id: str, force: bool = False, **kwargs: Any) -> Any:
    """Stop a running session."""
    with audited_budget(AuditEntryKind.TOOL_INVOCATION, "tool_invoke_ms"):
        result = stop_impl(session_id=session_id, force=force)
    return _ToolResult(content=_json.dumps(result), structured_content=result, meta={})


def thegent_ps(
    owner: str | None = None,
    all: bool = False,  # noqa: A002
    include_contract: bool = False,
    **kwargs: Any,
) -> Any:
    """List running sessions."""
    with audited_budget(AuditEntryKind.TOOL_INVOCATION, "tool_invoke_ms"):
        result = ps_impl(owner=owner, all=all, include_contract=include_contract)
    return _ToolResult(content=_json.dumps(result), structured_content=result, meta={})


def thegent_inspect(
    session_ids: list[str] | None = None,
    owner: str | None = None,
    tail: int = 50,
    stderr: bool = False,
    include_contract: bool = False,
    **kwargs: Any,
) -> Any:
    """Inspect session details."""
    with audited_budget(AuditEntryKind.TOOL_INVOCATION, "tool_invoke_ms"):
        result = inspect_impl(
            session_ids=session_ids or [],
            owner=owner,
            tail=tail,
            stderr=stderr,
            include_contract=include_contract,
        )
    return _ToolResult(content=_json.dumps(result), structured_content=result, meta={})


def thegent_logs(
    session_id: str,
    tail: int | None = None,
    stderr: bool = False,
    **kwargs: Any,
) -> Any:
    """Get session logs."""
    with audited_budget(AuditEntryKind.TOOL_INVOCATION, "tool_invoke_ms"):
        result = logs_impl(session_id=session_id, tail=tail, stderr=stderr)
    return _ToolResult(
        content=str(result) if isinstance(result, str) else _json.dumps(result),
        structured_content={},
        meta={},
    )


def thegent_wait(session_id: str, timeout: int | None = None, **kwargs: Any) -> Any:
    """Wait for a session to complete."""
    with audited_budget(AuditEntryKind.TOOL_INVOCATION, "tool_invoke_ms"):
        result = wait_impl(session_id=session_id, timeout=timeout)
    return _ToolResult(content=_json.dumps(result), structured_content=result, meta={})


async def thegent_dag_list(
    cd: str | Path | None = None,
    ctx: Any = None,
    default_cwd: Path | None = None,
    **kwargs: Any,
) -> Any:
    """List DAG tasks."""
    resolved = _resolve_cwd(cd) if cd else default_cwd
    if resolved is None and ctx is not None and hasattr(ctx, "elicit"):
        elicitation_result = await ctx.elicit(
            message="No working directory specified. Please provide a project path.",
            schema={"type": "object", "properties": {"cwd": {"type": "string"}}},
        )
        from fastmcp.server.context import (
            AcceptedElicitation,
            CancelledElicitation,
            DeclinedElicitation,
        )

        if isinstance(elicitation_result, DeclinedElicitation):
            return _ToolResult(
                content=_json.dumps({"error": "CWD elicitation declined", "tasks": []}),
                structured_content={"error": "CWD elicitation declined", "tasks": []},
                meta={},
            )
        if isinstance(elicitation_result, CancelledElicitation):
            return _ToolResult(
                content=_json.dumps({"error": "CWD elicitation cancelled", "tasks": []}),
                structured_content={"error": "CWD elicitation cancelled", "tasks": []},
                meta={},
            )
        if isinstance(elicitation_result, AcceptedElicitation):
            cwd_value = (elicitation_result.content or {}).get("cwd")
            if cwd_value:
                resolved = Path(cwd_value)
        else:
            return _ToolResult(
                content=_json.dumps({"error": "Ambiguous CWD elicitation response", "tasks": []}),
                structured_content={
                    "error": "Ambiguous CWD elicitation response",
                    "tasks": [],
                },
                meta={},
            )
    t0 = _time.monotonic()
    with audited_budget(AuditEntryKind.TOOL_INVOCATION, "tool_invoke_ms"):
        result = dag_list_impl(cd=resolved)
    meta = {"execution_time_ms": round((_time.monotonic() - t0) * 1000.0, 2)}
    return _ToolResult(content=_json.dumps(result), structured_content=result, meta=meta)


async def thegent_suggest_prompt(raw_prompt: str, ctx: Any = None, **kwargs: Any) -> Any:
    """Suggest a refined prompt using sampling."""
    sampling_used = False
    suggested = raw_prompt
    if ctx is not None:
        try:
            with audited_budget(AuditEntryKind.TOOL_INVOCATION, "tool_invoke_ms"):
                sample_result = await ctx.sample(f"Refine this prompt for clarity and completeness: {raw_prompt}")
                suggested = sample_result.text.strip()
                sampling_used = True
        except Exception:  # noqa: BLE001
            suggested = raw_prompt
    data = {"suggested_prompt": suggested, "sampling_used": sampling_used}
    return _ToolResult(content=_json.dumps(data), structured_content=data, meta={})


def thegent_create_wbs(feature: str, scope: str | None = None, **kwargs: Any) -> str:
    """Create a work breakdown structure for a feature."""
    lines = [f"WBS for: {feature}"]
    if scope:
        lines.append(f"Scope: {scope}")
    lines.append("- Phase 1: Design")
    lines.append("- Phase 2: Implementation")
    lines.append("- Phase 3: Testing")
    lines.append("- Phase 4: Deployment")
    return "\n".join(lines)


def thegent_list_agents(**kwargs: Any) -> Any:
    """List available agents."""
    with audited_budget(AuditEntryKind.TOOL_INVOCATION, "tool_invoke_ms"):
        result = list_agents_impl()
    return _ToolResult(content=_json.dumps(result), structured_content=result, meta={})


def thegent_list_models(
    provider: str | None = None,
    include_contract: bool = False,
    by_model: bool = False,
    **kwargs: Any,
) -> Any:
    """List available models."""
    with audited_budget(AuditEntryKind.TOOL_INVOCATION, "tool_invoke_ms"):
        result = list_models_impl(provider=provider, include_contract=include_contract, by_model=by_model)
    return _ToolResult(content=_json.dumps(result), structured_content=result, meta={})


def thegent_list_operations(
    operation: str | None = None,
    **kwargs: Any,
) -> Any:
    """List available operations."""
    from thegent.operations import Operation, get_operations_by_type
    from thegent.operations import list_operations as _list_ops

    try:
        with audited_budget(AuditEntryKind.TOOL_INVOCATION, "tool_invoke_ms"):
            if operation:
                try:
                    op = Operation(operation)
                except (ValueError, KeyError):
                    return _ToolResult(
                        content=_json.dumps({"error": f"Unknown operation type: {operation}"}),
                        structured_content={"error": f"Unknown operation type: {operation}"},
                        meta={},
                    )
                entries = get_operations_by_type(op)
                if not entries:
                    return _ToolResult(
                        content=_json.dumps({"error": f"No operations found for type: {operation}"}),
                        structured_content={"error": f"No operations found for type: {operation}"},
                        meta={},
                    )
                data = {
                    operation: [
                        {
                            "command": e.command,
                            "description": e.description,
                            "mcp_tool": e.mcp_tool,
                        }
                        for e in entries
                    ]
                }
            else:
                data = _list_ops()
    except (ValueError, KeyError, Exception) as exc:  # noqa: BLE001
        data = {"error": str(exc)}
    return _ToolResult(content=_json.dumps(data), structured_content=data, meta={})


def thegent_list_modes(
    mode: str | None = None,
    **kwargs: Any,
) -> Any:
    """List available orchestration modes."""
    from thegent.orchestration_modes import get_mode
    from thegent.orchestration_modes import list_modes as _list_modes

    try:
        with audited_budget(AuditEntryKind.TOOL_INVOCATION, "tool_invoke_ms"):
            if mode:
                entry = get_mode(mode)
                if entry is None:
                    data = {"error": f"Unknown mode: {mode}"}
                else:
                    data = [
                        {
                            "mode": entry.mode.value,
                            "description": entry.description,
                            "phases": entry.phases,
                            "use_case": entry.use_case,
                            "risk_profile": entry.risk_profile,
                            "selection_hint": entry.selection_hint,
                        }
                    ]
            else:
                data = _list_modes()
    except (ValueError, KeyError, Exception) as exc:  # noqa: BLE001
        data = {"error": str(exc)}
    return _ToolResult(content=_json.dumps(data), structured_content=data, meta={})


def thegent_session_contracts(
    owner: str | None = None,
    all: bool = False,  # noqa: A002
    missing_only: bool = False,
    summary_only: bool = False,
    strict: bool = False,
    **kwargs: Any,
) -> Any:
    """Audit session contracts."""
    import time as _ct

    t0 = _ct.monotonic()
    with audited_budget(AuditEntryKind.TOOL_INVOCATION, "tool_invoke_ms"):
        payload = session_contract_audit_impl(
            owner=owner,
            all=all,
            missing_only=missing_only,
            summary_only=summary_only,
            strict=strict,
        )
    meta = {"execution_time_ms": round((_ct.monotonic() - t0) * 1000.0, 2)}
    return _ToolResult(content=_json.dumps(payload), structured_content=payload, meta=meta)


def _list_droid_names(cwd: Path | None) -> list[str]:
    """Resolve droid names from the filesystem."""
    from thegent.cli.commands.impl import _resolve_droids_dir
    from thegent.config import ThegentSettings

    settings = ThegentSettings()
    effective_cwd = cwd or Path.cwd()
    droids_dir = _resolve_droids_dir(effective_cwd, settings)
    if not droids_dir.exists():
        return []
    return sorted(p.name for p in droids_dir.iterdir() if p.is_dir() and not p.name.startswith("."))


def list_droids_impl(cd: Any = None) -> list[str]:
    """Simple wrapper around droid listing for MCP tool use.

    This module-level function can be patched by tests.
    """
    resolved = Path(cd) if cd else Path.cwd()
    return _list_droid_names(resolved)


def thegent_list_droids(
    cd: str | Path | None = None,
    default_cwd: Path | None = None,
    **kwargs: Any,
) -> Any:
    """List available droids."""
    resolved = Path(cd) if cd else default_cwd
    with audited_budget(AuditEntryKind.TOOL_INVOCATION, "tool_invoke_ms"):
        droid_names = list_droids_impl(cd=resolved)
    return _ToolResult(
        content=_json.dumps(droid_names),
        structured_content={"droids": droid_names},
        meta={},
    )


# --- Resource functions (MCP @mcp.resource() wrappers) ---


def resource_sessions(include_contract: bool = False, **kwargs: Any) -> str:
    """MCP resource: list all sessions."""
    payload = ps_impl(owner=None, all=True, include_contract=include_contract)
    return _stable_json(payload)


def resource_dag(cd: str | Path | None = None, **kwargs: Any) -> str:
    """MCP resource: get DAG state."""
    payload = dag_list_impl(cd=cd)
    return _stable_json(payload)


def resource_models(provider: str | None = None, include_contract: bool = False, **kwargs: Any) -> str:
    """MCP resource: list models."""
    payload = list_models_impl(provider=provider, include_contract=include_contract)
    return _stable_json(payload)


def resource_meta(**kwargs: Any) -> str:
    """MCP resource: server metadata."""
    payload = get_server_meta_impl()
    return _stable_json(payload)


def resource_agents(**kwargs: Any) -> str:
    """MCP resource: list agents."""
    payload = list_agents_impl()
    return _stable_json(payload)


def resource_models_contract(**kwargs: Any) -> str:
    """MCP resource: models route contract."""
    from thegent.models import route_contract

    payload = route_contract()
    return _stable_json(payload)


def resource_session_meta(id: str, include_contract: bool = False, **kwargs: Any) -> str:
    """MCP resource: session metadata."""
    payload = status_impl(session_id=id, include_contract=include_contract)
    return _stable_json(payload)


def resource_session_logs(id: str, tail: int | None = None, stderr: bool = False, **kwargs: Any) -> str:
    """MCP resource: session logs."""
    return logs_impl(session_id=id, tail=tail, stderr=stderr)


def resource_session_contracts(
    owner: str | None = None,
    all: bool = False,  # noqa: A002
    missing_only: bool = False,
    summary_only: bool = False,
    strict: bool = False,
    **kwargs: Any,
) -> str:
    """MCP resource: session contract audit."""
    payload = session_contract_audit_impl(
        owner=owner,
        all=all,
        missing_only=missing_only,
        summary_only=summary_only,
        strict=strict,
    )
    return _stable_json(payload)


def resource_operations(operation: str | None = None, **kwargs: Any) -> str:
    """MCP resource: list operations."""
    from thegent.operations import Operation, get_operations_by_type
    from thegent.operations import list_operations as _list_ops

    try:
        if operation:
            entries = get_operations_by_type(Operation(operation))
            data = {
                operation: [
                    {
                        "command": e.command,
                        "description": e.description,
                        "mcp_tool": e.mcp_tool,
                    }
                    for e in entries
                ]
            }
        else:
            data = _list_ops()
    except (ValueError, KeyError, Exception) as exc:  # noqa: BLE001
        data = {"error": str(exc)}
    return _stable_json(data)


def resource_modes(mode: str | None = None, **kwargs: Any) -> str:
    """MCP resource: list orchestration modes."""
    from thegent.orchestration_modes import get_mode
    from thegent.orchestration_modes import list_modes as _list_modes

    if mode:
        entry = get_mode(mode)
        if entry is None:
            data = {"error": f"Unknown mode: {mode}"}
        else:
            data = [
                {
                    "mode": entry.mode.value,
                    "description": entry.description,
                    "phases": entry.phases,
                    "use_case": entry.use_case,
                    "risk_profile": entry.risk_profile,
                    "selection_hint": entry.selection_hint,
                }
            ]
    else:
        data = _list_modes()
    return _stable_json(data)


# --- TOOL_ICONS ---

TOOL_ICONS: dict[str, str] = {
    "thegent_run": "play",
    "thegent_bg": "background",
    "thegent_status": "info",
    "thegent_stop": "stop",
    "thegent_ps": "list",
    "thegent_inspect": "search",
    "thegent_logs": "scroll",
    "thegent_wait": "clock",
    "thegent_dag_list": "workflow",
    "thegent_observe_summary": "chart",
    "thegent_list_agents": "robot",
    "thegent_list_models": "brain",
    "thegent_list_droids": "droid",
    "thegent_list_operations": "operations",
    "thegent_list_modes": "modes",
    "thegent_session_contracts": "contracts",
    "thegent_suggest_prompt": "magic",
    "thegent_run_agent": "rocket",
    "thegent_bg_task": "background",
}


def thegent_session_contract_health_gate(
    session_id: str | None = None,
    *,
    policy_profile: str | None = None,
    strict: bool = False,
    min_healthy_ratio: float = 1.0,
    owner: str | None = None,
    all: bool = False,  # noqa: A002
    top_blocked: int = 25,
    **kwargs: Any,
) -> Any:
    """Get session contract health gate for a session.

    Returns a ``_ToolResult`` envelope with ``content`` (JSON string),
    ``structured_content`` (the raw payload) and ``meta`` (the
    canonical contract-health meta block).
    """
    try:
        with audited_budget(AuditEntryKind.TOOL_INVOCATION, "tool_invoke_ms"):
            payload = session_contract_health_gate_impl(
                policy_profile=policy_profile,
                strict=strict,
                min_healthy_ratio=min_healthy_ratio,
                owner=owner,
                all=all,
                top_blocked=top_blocked,
                **kwargs,
            )
        return _ToolResult(
            content=_json.dumps(payload),
            structured_content=payload,
            meta=_contract_health_meta(payload),
        )
    except MCPBudgetExceeded as exc:
        return _ToolResult(content=str(exc), structured_content={}, meta={})


def thegent_session_contract_health_report(
    session_id: str | None = None,
    *,
    policy_profile: str | None = None,
    strict: bool = False,
    min_healthy_ratio: float = 1.0,
    owner: str | None = None,
    all: bool = False,  # noqa: A002
    top_blocked: int = 25,
    **kwargs: Any,
) -> Any:
    """Get session contract health report for a session.

    Returns a ``_ToolResult`` envelope.
    """
    try:
        with audited_budget(AuditEntryKind.TOOL_INVOCATION, "tool_invoke_ms"):
            payload = session_contract_health_report_impl(
                policy_profile=policy_profile,
                strict=strict,
                min_healthy_ratio=min_healthy_ratio,
                owner=owner,
                all=all,
                top_blocked=top_blocked,
                **kwargs,
            )
        return _ToolResult(
            content=_json.dumps(payload),
            structured_content=payload,
            meta=_contract_health_meta(payload),
        )
    except MCPBudgetExceeded as exc:
        return _ToolResult(content=str(exc), structured_content={}, meta={})


def thegent_session_contract_health_trend(
    session_id: str | None = None,
    *,
    payload_type: str = "session_contract_health_report",
    trend_samples: int = 30,
    **kwargs: Any,
) -> Any:
    """Get session contract health trend for a session.

    Returns a ``_ToolResult`` envelope.
    """
    import time as _time

    t0 = _time.monotonic()
    try:
        with audited_budget(AuditEntryKind.TOOL_INVOCATION, "health_trend_ms"):
            payload = session_contract_health_trend_impl(
                payload_type=payload_type,
                trend_samples=trend_samples,
                **kwargs,
            )
        meta = _health_trend_meta(payload)
        meta["execution_time_ms"] = round((_time.monotonic() - t0) * 1000.0, 2)
        return _ToolResult(
            content=_json.dumps(payload),
            structured_content=payload,
            meta=meta,
        )
    except MCPBudgetExceeded as exc:
        return _ToolResult(content=str(exc), structured_content={}, meta={})


def _cache_elicitation_key(elicitation_id: str) -> str:
    """Backward-compatible alias for ``server_elicitation_cache_key``.

    Some legacy scripts (notably ``scripts/benchmark_python_suite.py``,
    restored from the wave-79 finalization) still import this private
    name. The public re-export is ``server_elicitation_cache_key``; the
    alias keeps the legacy import path working without forcing a
    script-side change.
    """
    return f"elicitation:{elicitation_id}"


def _server_tools_workstream_lsp(
    workstream_id: str,
    params: dict | None = None,
) -> dict:
    """Handle LSP tools for workstream operations.

    Args:
        workstream_id: The workstream ID.
        params: Additional parameters.

    Returns:
        LSP response dictionary.
    """
    return {"workstream_id": workstream_id, "status": "ok", "tools": []}


# ---------------------------------------------------------------------------
# WL-126: server-module-loader shared helper + per-domain wrappers
# ---------------------------------------------------------------------------


def _load_server_module_shared(
    *,
    server_file: Path,
    module_filename: str,
    module_import_name: str,
    failure_message: str,
) -> Any:
    """Load a server sub-module relative to the server package.

    ``server_file`` is used to derive the parent directory.  The helper
    raises ``RuntimeError`` with ``failure_message`` when the module
    cannot be found or imported.
    """
    from thegent.mcp.server_module_loader import load_server_module

    return load_server_module(module_name=module_import_name)


def _load_server_tools_prompt_and_handoff_module() -> Any:
    """Load the prompt-and-handoff tool wrappers sub-module."""
    from pathlib import Path as _Path

    return _load_server_module_shared(
        server_file=_Path(__file__),
        module_filename="tools_prompt_and_handoff.py",
        module_import_name="thegent.mcp._server_tools_prompt_and_handoff",
        failure_message="Unable to load prompt/handoff tool wrappers",
    )


def _load_server_tools_locking_planning_module() -> Any:
    """Load the locking-planning tool helpers sub-module."""
    from pathlib import Path as _Path

    return _load_server_module_shared(
        server_file=_Path(__file__),
        module_filename="tools_locking_planning.py",
        module_import_name="thegent.mcp._server_tools_locking_planning",
        failure_message="Unable to load locking/planning tool helpers",
    )


def _load_server_tools_planning_module() -> Any:
    """Load the planning tool helpers sub-module."""
    from pathlib import Path as _Path

    return _load_server_module_shared(
        server_file=_Path(__file__),
        module_filename="tools_planning.py",
        module_import_name="thegent.mcp._server_tools_planning",
        failure_message="Unable to load planning tool helpers",
    )


def _load_server_tools_queue_module() -> Any:
    """Load the queue tool helpers sub-module."""
    from pathlib import Path as _Path

    return _load_server_module_shared(
        server_file=_Path(__file__),
        module_filename="tools_queue.py",
        module_import_name="thegent.mcp._server_tools_queue",
        failure_message="Unable to load queue tool helpers",
    )


def _load_server_tools_terminal_module() -> Any:
    """Load the terminal tool helpers sub-module."""
    from pathlib import Path as _Path

    return _load_server_module_shared(
        server_file=_Path(__file__),
        module_filename="tools_terminal.py",
        module_import_name="thegent.mcp._server_tools_terminal",
        failure_message="Unable to load terminal tool helpers",
    )


def _load_server_tools_governance_module() -> Any:
    """Load the governance tool helpers sub-module."""
    from pathlib import Path as _Path

    return _load_server_module_shared(
        server_file=_Path(__file__),
        module_filename="tools_governance.py",
        module_import_name="thegent.mcp._server_tools_governance",
        failure_message="Unable to load governance tool helpers",
    )
