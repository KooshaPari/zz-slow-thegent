"""Extracted execution cores for run/bg commands.

DEPRECATED: This module is now a thin shim for backward compatibility.
New code should use the decomposed modules:
- thegent.use_cases.execute_task — Pure orchestration logic
- thegent.adapters.execution_io — I/O and subprocess management

These helpers accept an injected impl module namespace to preserve existing
runtime wiring while avoiding circular imports from impl.py.
"""

import hashlib
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog
from rich.console import Console

from thegent.ux.cli_errors import print_exc

# AUDIT-N+2 envelope-parity contract: expose `err_console` (Rich
# Console(stderr=True)) on this module so the AUDIT-N+2..
# TestErrConsoleStderr parametrization closes.
err_console = Console(stderr=True)

# Import decomposed modules

from thegent.agents import get_fallback_agents, get_runner, resolve_agent
from thegent.agents.base import AgentRunner, RunResult
from thegent.agents.resilience import is_usage_limit


# Lazy import wrapper to avoid circular dependency
class _LazyImpl:
    _impl = None
    _spawn_with_eagain_retry = None

    def __getattr__(self, name):
        if name == "_spawn_with_eagain_retry":
            if self._spawn_with_eagain_retry is None:
                from thegent.cli.commands.impl import _spawn_with_eagain_retry

                self._spawn_with_eagain_retry = _spawn_with_eagain_retry
            return self._spawn_with_eagain_retry
        if self._impl is None:
            from thegent.cli.commands import impl

            self._impl = impl
        return getattr(self._impl, name)


_impl_lazy = _LazyImpl()

# These are now accessed via _impl_lazy._apply_pareto_routing etc.
import os
import platform
import socket
import subprocess

from thegent.agents.registry import list_agent_names
from thegent.cli.commands.observability_impl import escalate_add_impl
from thegent.cli.commands.session_meta_impl import (
    _build_continuation_prompt,
    _save_session_meta,
)
from thegent.cli.services import run_session_helpers as _rsh
from thegent.cli.services import run_session_helpers as _rsh_impl
from thegent.cli.services.run_session_helpers import resolve_cwd as _resolve_cwd
from thegent.config import ThegentSettings
from thegent.execution import (  # noqa: F401 — surfaced via _bind_impl_namespace
    AgentSource,
    Auditor,
    CircuitBreakerRegistry,
    ConcurrencyController,
    FreshnessValidator,
    InteractivityMode,
    InterruptionTracker,
    LoadClassifier,
    OverrideRegistry,
    PolicyEngine,
    RunMeta,
    RunRegistry,
    TrustBoundaryValidator,
)
from thegent.maif import MAIFRunner
from thegent.output_parser import condense_stream_to_display, extract_condensed

_log = structlog.get_logger(__name__)
console = Console()
_default_owner_tag = _rsh.default_owner_tag
_session_dir = _rsh_impl.session_dir
_new_session_id = _rsh_impl.new_session_id
_session_paths = _rsh_impl.session_paths

if TYPE_CHECKING:
    from thegent.config_provider import ConfigProvider


def _bind_impl_namespace(impl_ns: Any) -> None:
    """Expose impl module symbols as globals for extracted core parity."""
    module_globals = globals()
    for key, value in vars(impl_ns).items():
        if key.startswith("__"):
            continue
        module_globals[key] = value


def _apply_pareto_routing_local(
    agent: str | None,
    model: str | None,
    routing: str | None,
    include_contract: bool,
    route_contract: dict[str, Any] | None,
    route_request: dict[str, Any] | None,
) -> tuple[str | None, str | None, dict[str, Any] | None, dict[str, Any] | None]:
    from thegent.cli.commands.run.impl_core_runners import _apply_pareto_routing

    return _apply_pareto_routing(agent, model, routing, include_contract, route_contract, route_request)


def _inject_time_constraint_local(prompt: str, timeout: int, *, summary_mode: bool) -> str:
    from thegent.cli.commands.impl import _inject_time_constraint

    return _inject_time_constraint(prompt, timeout, summary_mode=summary_mode)


def _resolve_agent_model_local(
    agent_name: str,
    model: str | None,
    mode: str,
    settings: ThegentSettings,
) -> str | None:
    from thegent.cli.commands.impl import _resolve_agent_model

    return _resolve_agent_model(agent_name, model, mode, settings)


# ============================================================================
# Phase helpers extracted from run_impl_core / bg_impl_core (L9 hardening).
#
# Each helper owns exactly one execution phase. Both orchestrators call these
# helpers in sequence; branches inside a helper are short and pure
# (no closure over outer-scope state). All helpers return either:
#   - a failure payload dict that the caller short-circuits with, or
#   - None / value for success continuation.
#
# Cognitive complexity target: ≤ 12 per helper. Body length target: ≤ 40 lines.
# This keeps run_impl_core / bg_impl_core as thin orchestrators with CC ≤ 15.
# ============================================================================


def _phase_budget_gate(settings: ThegentSettings, rid: str) -> dict[str, Any] | None:
    """Pre-flight hourly + daily budget check (WP-Y4)."""
    from thegent.cost import BudgetAlertSystem

    alert_system = BudgetAlertSystem.from_settings(settings)
    hourly_spend = alert_system.get_hourly_spend()
    _alert, block = alert_system.check_budget(hourly_spend, context="hourly")
    if block:
        return {
            "error": f"Hourly budget EXCEEDED: ${hourly_spend:.2f} >= ${settings.budget_hourly_limit:.2f}",
            "exit_code": 1,
            "run_id": rid,
        }
    daily_spend = alert_system.get_daily_spend()
    _alert, block = alert_system.check_budget(daily_spend, context="daily")
    if block:
        return {
            "error": f"Daily budget EXCEEDED: ${daily_spend:.2f} >= ${settings.budget_daily_limit:.2f}",
            "exit_code": 1,
            "run_id": rid,
        }
    return None


def _phase_auto_route(
    settings: ThegentSettings,
    agent: str | None,
    model: str | None,
    prompt: str,
    include_contract: bool,
    route_contract: dict[str, Any] | None,
    route_request: dict[str, Any] | None,
) -> tuple[str | None, str | None, dict[str, Any] | None, dict[str, Any] | None]:
    """Auto-router for ``agent='auto'`` / ``model='auto'``."""
    if not (settings.auto_router_enabled and (agent == "auto" or model == "auto")):
        return agent, model, route_contract, route_request
    try:
        from thegent.utils.routing_impl.auto_router import auto_route

        ar = auto_route(
            prompt=prompt,
            classifier_model=settings.auto_router_classifier_model,
            use_classifier=settings.auto_router_use_classifier,
            min_quality=settings.auto_router_min_quality,
            max_cost_weight=settings.auto_router_max_cost_weight,
        )
        if ar:
            agent = ar.agent
            model = ar.model
            _log.info("Auto router: %s/%s (complexity=%s)", agent, model, ar.complexity)
            if ar.route_trace and include_contract:
                rt = ar.route_trace
                route_contract = {
                    "provider": rt.provider,
                    "model_alias": rt.model_alias,
                    "backend_type": "proxy",
                    "degraded_mode": getattr(rt, "degraded_mode", False),
                    "role": getattr(rt, "role", None),
                    "route_trace": {
                        "selected_offer_id": rt.selected_offer_id,
                        "pareto_set": rt.pareto_set,
                        "fallback_chain": [{"provider": p, "model": m} for p, m in (rt.fallback_chain or [])],
                        "scores": rt.scores,
                        "shadow_multiplier": rt.shadow_multiplier,
                    },
                }
                route_request = dict(route_request or {})
                route_request.update(
                    {
                        "requested_model": "auto",
                        "policy": "pareto",
                        "resolved_agent": ar.agent,
                        "resolved_model_alias": ar.model,
                        "complexity": ar.complexity,
                    }
                )
        else:
            agent = "antigravity"
            model = "gemini-3-flash"
            _log.warning("Auto router failed; fallback to antigravity/gemini-3-flash")
    except Exception as e:
        _log.warning("Auto router error: %s; fallback to antigravity/gemini-3-flash", e)
        agent = "antigravity"
        model = "gemini-3-flash"
    return agent, model, route_contract, route_request


def _phase_resolve_agent_from_model(
    model: str | None,
    provider: str | None,
    rid: str,
) -> tuple[str | None, dict[str, Any] | None]:
    """Resolve ``agent`` from a model alias when ``agent`` is ``None``."""
    if model is None:
        return None, None
    from thegent.models import normalize_model_id
    from thegent.models.catalog import ModelCatalog, resolve_route

    model_id = normalize_model_id(model)
    route = resolve_route(model_id, provider_hint=provider)
    if route is None:
        routes = ModelCatalog.routes_for(model_id)
        available = ", ".join(sorted({r.provider for r in routes})) if routes else "none"
        suffix = f" Available: {available}." if available != "none" else ""
        return None, {
            "error": f"Model '{model}' not available via provider '{provider or 'any'}'.{suffix}",
            "agents": available,
            "exit_code": 1,
            "run_id": rid,
        }
    return route[0], None


def _phase_evaluate_contract_version(
    contract_version: str | None,
    rid: str,
) -> tuple[bool, dict[str, Any] | None, str | None]:
    """Negotiate contract schema version (WP-X1/V7).

    Returns ``(allowed, error_payload, deprecation_warning)``.
    """
    from thegent.contracts.migration import MigrationController
    from thegent.contracts.registry import CONTRACT_SCHEMA_VERSION

    migrator = MigrationController()
    requested_version = contract_version or CONTRACT_SCHEMA_VERSION
    mig_res = migrator.evaluate_version("csm", requested_version)
    if not mig_res["allowed"]:
        return (
            False,
            {
                "error": f"Contract version rejected: {mig_res['reason']}",
                "exit_code": 1,
                "run_id": rid,
            },
            None,
        )
    if mig_res["status"] == "deprecated":
        warning = f"Contract version '{requested_version}' is deprecated: {mig_res.get('reason', 'no reason provided')}"
        _log.warning(warning)
        return True, None, warning
    return True, None, None


def _phase_resolve_effective_timeout(
    settings: ThegentSettings,
    config_provider: "ConfigProvider | None",
    timeout: int | None,
    agent: str | None,
    tenant_id: str | None,
) -> int:
    """Resolve effective timeout (config + claude floor)."""
    _config: dict[str, Any] | None = None
    if config_provider is not None:
        request_overrides: dict[str, Any] = {}
        if timeout is not None:
            request_overrides["default_timeout"] = timeout
        _config = config_provider.resolve(tenant_id=tenant_id, request_overrides=request_overrides)
    effective_timeout = (
        timeout
        if timeout is not None
        else (_config.get("default_timeout", settings.default_timeout) if _config else settings.default_timeout)
    )
    if agent == "claude":
        _min_claude = (
            _config.get(
                "default_timeout_claude",
                getattr(settings, "default_timeout_claude", 300),
            )
            if _config
            else getattr(settings, "default_timeout_claude", 300)
        )
        try:
            _min_claude = float(_min_claude)
            effective_timeout = max(float(effective_timeout), _min_claude)
        except (TypeError, ValueError) as exc:
            _log.debug(
                "Invalid claude timeout override '%s'; using existing timeout: %s",
                _min_claude,
                exc,
            )
    return int(effective_timeout)


def _phase_resolve_cwd(cd: Path | None, rid: str) -> tuple[Path | None, dict[str, Any] | None]:
    """Resolve the working directory or short-circuit with a failure payload."""
    cwd = _resolve_cwd(cd)
    if cwd is None:
        return None, {
            "error": "Ambiguous cwd detected. Run inside a project directory or pass --cd with a valid project path.",
            "exit_code": 1,
            "run_id": rid,
        }
    return cwd, None


def _phase_terminal_discovery(settings: ThegentSettings, cwd: Path) -> None:
    """Best-effort hint that an existing terminal session is alive."""
    if not settings.terminal_management_enabled:
        return
    try:
        import importlib

        routing_mod = importlib.import_module("thegent.utils.routing_impl")
        TaskRouter = getattr(routing_mod, "TaskRouter", None)
        if not TaskRouter:
            return
        router = TaskRouter(settings)
        existing_pane = router.find_active_terminal_for_path(str(cwd))
        if existing_pane:
            console.print(f"[bold yellow]Found existing terminal session for this path: {existing_pane}[/bold yellow]")
            console.print(f"[dim]You can attach with: thegent terminal attach {existing_pane}[/dim]")
    except Exception as e:
        _log.debug(f"Terminal discovery failed: {e}")


def _phase_input_guardrails(
    prompt: str, agent: str | None, model: str | None, cwd: Path, rid: str
) -> dict[str, Any] | None:
    """Input guardrails pre-flight (G-GP-02)."""
    settings = ThegentSettings()
    if not settings.input_guardrails_enabled:
        return None
    try:
        from thegent.governance.input_guardrails import guardrails_from_env

        guardrails = guardrails_from_env()
        gr = guardrails.check(prompt=prompt, agent=agent or "", model=model, cwd=cwd)
        if not gr.passed:
            return {
                "error": f"Input guardrail failed ({gr.rail_id}): {gr.reason}",
                "remediation": gr.remediation,
                "exit_code": 1,
                "run_id": rid,
            }
    except Exception as exc:
        _log.debug("Input guardrail check failed; continuing without guardrail result: %s", exc)
    return None


def _phase_acquire_concurrency(
    settings: ThegentSettings,
    lane: str,
    task_id: str | None,
    rid: str,
) -> dict[str, Any] | None:
    """Concurrency controller acquisition (WP-5001)."""

    cc = ConcurrencyController(
        settings.session_dir,
        max_concurrency=settings.max_concurrency,
        use_load_based=settings.concurrency_load_based,
    )
    if cc.acquire(lane=lane, priority=lane):
        return None
    if task_id:
        try:
            from thegent.governance.teammates import TeammateManager

            mgr = TeammateManager(settings.cache_dir / "teammates.json")
            mgr.update_status(
                task_id,
                "failed",
                summary="Run blocked: Concurrency limit reached (resource contention).",
            )
        except Exception as e:
            _log.debug("Failed to update teammate delegation status: %s", e)
    if settings.concurrency_load_based:
        from thegent.orchestration.resource.load_based_limits import (
            LimitGateConfig,
            compute_dynamic_limit,
            sample_resources,
        )

        snapshot = sample_resources()
        config = LimitGateConfig.from_dict(settings.model_dump())
        effective_limit, _details = compute_dynamic_limit(snapshot, config)
        bottlenecks = cc.get_bottlenecks() if hasattr(cc, "get_bottlenecks") else {}
        bottleneck_msg = ""
        if bottlenecks.get("resource_contention"):
            bottleneck_msg = f" Resource contention detected: {len(bottlenecks['resource_contention'])} issue(s)."
        return {
            "error": f"Resource-based concurrency limit reached (current: {effective_limit} slots).{bottleneck_msg} Task queued or blocked.",
            "exit_code": 1,
            "run_id": rid,
            "bottlenecks": bottlenecks,
        }
    return {
        "error": f"Concurrency limit reached ({settings.max_concurrency}). Task queued or blocked.",
        "exit_code": 1,
        "run_id": rid,
    }


def _phase_idempotency_replay(
    registry: RunRegistry,
    idempotency_token: str | None,
) -> dict[str, Any] | None:
    """Replay detection (WP-1003 / WP-1008)."""
    if not idempotency_token:
        return None
    session_id_from_token = f"run_{hashlib.sha256(idempotency_token.encode()).hexdigest()[:8]}"
    if not registry.session_exists(session_id_from_token):
        return None
    existing = registry.find_by_token(idempotency_token)
    if existing and existing.get("status") == "completed":
        _log.info("Replay detected for token %s; skipping execution.", idempotency_token)
        return {
            "stdout": existing.get("stdout", ""),
            "stderr": existing.get("stderr", ""),
            "exit_code": existing.get("exit_code", 0),
            "run_id": existing.get("run_id"),
            "replayed": True,
        }
    return None


def _phase_trust_boundary(settings: ThegentSettings, trust_boundary: TrustBoundaryValidator) -> dict[str, Any] | None:
    """Environment transition check (WP-3007)."""
    last_env = trust_boundary.get_last_environment()
    allowed, boundary_reason = trust_boundary.validate_transition(last_env, settings.environment.lower())
    if not allowed:
        return {"error": f"Trust boundary violation: {boundary_reason}", "exit_code": 1}
    return None


def _phase_fatigue_freshness_burst(
    settings: ThegentSettings,
    registry_path: Path | None,
    lane: str,
    rid: str,
) -> dict[str, Any] | None:
    """Combined fatigue + freshness + burst checks (WP-4004 / WP-4005 / WP-5002)."""
    from thegent.execution import (
        DeferralQueue,
    )

    it = InterruptionTracker(settings.session_dir)
    fatigue = it.get_fatigue_score()
    if fatigue > 0.8:
        _log.warning("High fatigue detected (%.2f); recommending non-critical deferral.", fatigue)
        if lane != "critical":
            console.print("[bold yellow]ADVISORY:[/bold yellow] High system fatigue. Deferring non-critical task.")
            return {
                "error": "System fatigue limit reached. Task deferred.",
                "exit_code": 1,
            }
    fv = FreshnessValidator(settings.session_dir)
    freshness_issues: list[str] = []
    if registry_path is not None:
        freshness_issues = fv.validate_action([registry_path])
    if freshness_issues:
        _log.warning("Freshness issues detected: %s", freshness_issues)
        if lane == "critical":
            return {
                "error": f"ROB-011: State freshness violation in critical lane: {freshness_issues}",
                "exit_code": 1,
            }
    lc = LoadClassifier(settings.session_dir)
    load_level = lc.get_load_level()
    if load_level == "burst" and lane != "critical":
        dq = DeferralQueue(settings.session_dir)
        burst_rid = rid or f"run_def_{uuid.uuid4().hex[:8]}"
        dq.defer(burst_rid, "System in burst mode; non-critical deferral active")
        console.print("[bold yellow]BURST MODE:[/bold yellow] Non-critical task deferred to queue.")
        return {
            "error": "System in burst mode. Task deferred.",
            "exit_code": 1,
            "run_id": burst_rid,
        }
    return None


def _phase_evaluate_policy_with_override(
    policy_engine: PolicyEngine,
    override_registry: OverrideRegistry,
    run_meta: RunMeta,
    registry: RunRegistry,
    effective_owner: str,
    override_reason: str | None,
) -> tuple[str, str]:
    """Policy evaluation + override-TTL application (WP-3001 / WP-3003)."""
    pol_res, pol_reason = policy_engine.evaluate(run_meta, registry=registry)
    if pol_res == "deny":
        if override_reason:
            console.print(f"[bold yellow]Policy OVERRIDE applied:[/bold yellow] {override_reason}")
            settings = ThegentSettings()
            override_registry.record(effective_owner, override_reason, settings.override_ttl_seconds)
            return "allow", f"Overridden: {pol_reason}"
        if override_registry.has_unexpired(effective_owner):
            console.print("[dim]Policy override (cached, within TTL)[/dim]")
            return "allow", f"Overridden (cached): {pol_reason}"
    return pol_res, pol_reason


def _phase_register_policy_denial(
    run_meta: RunMeta,
    escalation_sla_minutes: int,
    pol_reason: str,
    registry: RunRegistry,
) -> dict[str, Any]:
    """Register policy denial: escalate + register start/end (WP-3008)."""
    escalate_add_impl(
        run_id=run_meta.run_id,
        reason=pol_reason,
        sla_minutes=escalation_sla_minutes,
        owner=run_meta.owner,
        agent=run_meta.agent,
        lane=run_meta.lane,
    )
    registry.register_start(run_meta)
    registry.register_end(
        run_id=run_meta.run_id,
        exit_code=1,
        status="failed",
        ended_at_utc=datetime.now(UTC).isoformat(),
        duration_s=0.0,
        error_class="policy_violation",
    )
    return {"error": f"Policy Violation: {pol_reason}", "exit_code": 1}


def _phase_register_hitl_pause(
    settings: ThegentSettings,
    run_meta: RunMeta,
    registry: RunRegistry,
    escalation_sla_minutes: int,
    pol_reason: str,
    suffix: str = "",
    priority: int = 1,
) -> dict[str, Any]:
    """Register HITL pause: checkpoint + escalate (G-GP-05)."""
    from thegent.execution import CheckpointRegistry

    registry.register_start(run_meta)
    registry.register_pause(run_meta.run_id, reason=pol_reason)
    ckpt_registry = CheckpointRegistry(settings.session_dir)
    ckpt_registry.create_checkpoint(
        reason=f"HITL Pause{suffix}: {pol_reason}",
        dag_content=run_meta.model_dump_json(),
        owner=run_meta.owner,
    )
    escalate_add_impl(
        run_id=run_meta.run_id,
        reason=f"HITL Pause{suffix}: {pol_reason}",
        sla_minutes=escalation_sla_minutes,
        owner=run_meta.owner,
        agent=run_meta.agent,
        lane=run_meta.lane,
        priority=priority,
    )
    return {
        "error": f"HITL PAUSE: {pol_reason}{suffix}. Escalated for approval.",
        "exit_code": 0,
        "status": "paused",
        "run_id": run_meta.run_id,
    }


def _phase_load_l3_memory_context(agent: str | None, prompt: str) -> tuple[str, bool]:
    """Inject L3 memory context into ``prompt`` when enabled."""
    import asyncio as _asyncio

    from thegent.memory.memory_manager import MemoryManager as _MemoryManager

    try:
        _mem_mgr = _MemoryManager()
    except Exception as _mem_exc:
        _log.debug("L3 memory init skipped: %s", _mem_exc)
        return prompt, False
    if not getattr(_mem_mgr, "enabled", False):
        return prompt, False
    try:
        _mem_ctx = _asyncio.get_event_loop().run_until_complete(_mem_mgr.load_context(agent or "unknown"))
        if not _mem_ctx:
            return prompt, False
        ctx_block = "\n".join(f"- {c}" for c in _mem_ctx[:5])
        new_prompt = f"[Past context from memory]\n{ctx_block}\n\n[Task]\n{prompt}"
        _log.debug("L3 memory: injected %d context entries", len(_mem_ctx))
        return new_prompt, True
    except Exception as _mem_exc:
        _log.debug("L3 memory load_context failed: %s", _mem_exc)
        return prompt, False


def _phase_setup_shadow_workspace(
    settings: ThegentSettings,
    cwd: Path | None,
    run_id: str,
    requested_shadow: bool,
) -> tuple[Path | None, dict[str, str] | None, Any]:
    """Optionally create a shadow workspace (MTSP-12).

    Resolves ``cwd or Path.cwd()`` internally and returns
    ``(agent_cwd, shadow_env, shadow_ws)``.
    """
    original_cwd = cwd or Path.cwd()
    use_shadow = bool(requested_shadow or getattr(settings, "shadow_workspaces_enabled", False))
    if not use_shadow:
        return original_cwd, None, None
    try:
        from thegent.orchestration.shadow import ShadowWorkspace

        shadow_ws = ShadowWorkspace(original_cwd, run_id)
        if shadow_ws.create():
            shadow_env = shadow_ws.get_env()
            _log.info("Running in shadow workspace: %s", shadow_ws.shadow_root)
            return shadow_ws.shadow_root, shadow_env, shadow_ws
        _log.warning("Failed to create shadow workspace; falling back to main project.")
        return original_cwd, None, None
    except ImportError as _shadow_exc:
        _log.debug(
            "shadow workspace module unavailable in this revision (%s); running in main project",
            _shadow_exc,
        )
        return original_cwd, None, None


def _phase_acquire_resource_leases(
    settings: ThegentSettings,
    lock: list[str] | None,
    original_cwd: Path,
    run_id: str,
    effective_timeout: int,
) -> list[tuple[Path, Any]] | dict[str, Any]:
    """Acquire non-worktree file leases (MTSP-15).

    Returns either a list of ``(path, token)`` tuples on success or a
    failure payload dict when a lease cannot be acquired.
    """
    if not lock:
        return []
    from thegent.coordination.file_coordination import FileLeaseRegistry

    lease_registry = FileLeaseRegistry(settings.session_dir / "leases")
    acquired: list[tuple[Path, Any]] = []
    for resource in lock:
        path = Path(resource)
        if not path.is_absolute():
            path = original_cwd / path
        token = lease_registry.claim_lease(path, run_id, ttl=int(effective_timeout))
        if token:
            acquired.append((path, token))
            _log.info("Acquired lease for %s", resource)
        else:
            _log.error(
                "Failed to acquire lease for %s; already locked by another agent.",
                resource,
            )
            return {
                "error": f"Resource {resource} is locked by another agent.",
                "exit_code": 1,
            }
    return acquired


def _phase_release_resource_leases(
    settings: ThegentSettings,
    locked_tokens: list[tuple[Path, Any]],
    run_id: str,
) -> None:
    """Release previously acquired leases."""
    if not locked_tokens:
        return
    from thegent.coordination.file_coordination import FileLeaseRegistry

    lease_registry = FileLeaseRegistry(settings.session_dir / "leases")
    for path, token in locked_tokens:
        lease_registry.release_lease(path, run_id, token)
        _log.info("Released lease for %s", path)


def _phase_finalize_shadow(shadow_ws: Any, settings: ThegentSettings, status: str) -> None:
    """Auto-merge or destroy the shadow workspace based on status."""
    if shadow_ws is None:
        return
    if status == "success" and bool(getattr(settings, "shadow_workspaces_auto_merge", False)):
        if shadow_ws.merge_back():
            _log.info("Shadow changes merged successfully.")
        else:
            _log.error("Failed to merge shadow changes back to main project.")
    shadow_ws.destroy()


def _phase_estimate_run_cost(run_meta: RunMeta) -> float | None:
    """Estimate cost for the run (WP-Y4 cost tracking)."""
    settings = ThegentSettings()
    if not settings.cost_tracking_enabled:
        return None
    try:
        from thegent.cost.aggregator import CostEstimator

        est = CostEstimator()
        return est.estimate(
            model=run_meta.model,
            prompt_length=len(run_meta.prompt or ""),
        )
    except Exception as exc:
        _log.debug("Failed to estimate run cost: %s", exc)
        return None


def _phase_register_run_end(
    registry: RunRegistry,
    run_id: str,
    exit_code: int,
    status: str,
    duration: float,
    error_class: str | None,
    cost_usd: float | None,
    maif_runner: Any = None,
    output_summary: str = "",
) -> None:
    """Register run end + final MAIF record_run_end."""
    registry.register_end(
        run_id=run_id,
        exit_code=exit_code,
        status=status,
        ended_at_utc=datetime.now(UTC).isoformat(),
        duration_s=duration,
        error_class=error_class,
        cost_usd=cost_usd,
    )
    if maif_runner is not None:
        maif_runner.record_run_end(
            run_id=run_id,
            status=status,
            output_summary=output_summary,
        )


def _phase_record_success_postlude(
    settings: ThegentSettings,
    run_meta: RunMeta,
    result: Any,
    norm_res: Any,
    auditor: Auditor,
) -> None:
    """Post-success: trust boundary record + evidence lint + MAIF artifact (WP-3007/3002)."""
    from thegent.execution import EvidenceLinter

    trust_boundary = TrustBoundaryValidator(settings.session_dir)
    trust_boundary.record_environment(settings.environment.lower())
    if norm_res and norm_res.csm:
        linter = EvidenceLinter(settings.session_dir)
        lint_issues = linter.lint(norm_res.csm)
        if lint_issues:
            _log.warning("Evidence lint issues for %s: %s", run_meta.run_id, lint_issues)
            if run_meta.lane == "critical":
                console.print(f"[bold red]LINT FAILURE:[/bold red] Evidence incomplete: {lint_issues}")
    try:
        artifact = auditor.generate_maif_artifact(run_meta, output=result.stdout if result else None)
        auditor.persist_maif_artifact(settings.session_dir, artifact)
    except Exception as exc:
        _log.warning("Failed to generate/persist MAIF artifact: %s", exc)


def _phase_update_teammate_status(
    settings: ThegentSettings,
    task_id: str | None,
    status: str,
    result: Any,
) -> None:
    """Update teammate delegation status (WP-16002).

    No-op when ``task_id`` is falsy so the orchestrator can always
    call this without a guard. Exceptions are swallowed + logged at
    debug level to avoid poisoning the run on telemetry failure.
    """
    if not task_id:
        return
    try:
        from thegent.governance.teammates import TeammateManager

        mgr = TeammateManager(settings.cache_dir / "teammates.json")
        _stdout = (result.stdout or "") if result else ""
        _stderr = (result.stderr or "") if result else ""
        summary = _stdout[:500] if status == "completed" else (_stderr[:500] or "Failed without stderr")
        mgr.update_status(task_id, status, summary=summary)
    except Exception as e:
        _log.debug("Failed to update teammate delegation status: %s", e)


def _phase_write_run_dumps(
    settings: ThegentSettings,
    run_id: str,
    cwd: Path,
    prompt: str,
    stdout: str,
    result: Any,
) -> None:
    """Always write conversation dumps + session snapshot (WP-DX-024)."""
    try:
        from thegent.research.always_write_dumps import ConversationDumper

        docs_dir = Path("docs/dumps")
        if not docs_dir.parent.exists():
            docs_dir = settings.session_dir / "dumps"
        is_error = bool(result.exit_code) or bool(result.timed_out)
        dumper = ConversationDumper(docs_dir=docs_dir)
        dumper.dump_conversation(
            run_id,
            stdout,
            prompt=prompt,
            synthesis=stdout,
            category="error" if is_error else "execution",
            tags=["auto-dump", "session-memory"],
            metadata={
                "run_id": run_id,
                "exit_code": result.exit_code,
                "timed_out": result.timed_out,
            },
        )
        try:
            from thegent.orchestration.state.session_scraper import SessionScraper

            SessionScraper(cwd).persist_snapshot(trigger="error" if is_error else "tool_use")
        except Exception as e:
            _log.debug(f"Failed to persist session snapshot: {e}")
    except Exception as e:
        _log.debug(f"Failed to write conversation dump: {e}")


def _phase_assemble_payload(
    *,
    result: Any,
    norm_res: Any,
    use_stream: bool,
    csm: Any = None,
    stdout: str,
    stderr: str,
    run_meta: RunMeta,
    contract_deprecation_warning: str | None,
    include_contract: bool,
    route_contract: dict[str, Any] | None,
    route_request: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build the final run payload from the result + normalized stream.

    ``csm`` is derived from ``norm_res`` when not explicitly provided.
    """
    if csm is None:
        csm = norm_res.csm if norm_res else None
    if use_stream:
        if csm:
            stdout = csm.summary
        else:
            condensed = condense_stream_to_display(stdout)
            stdout = condensed or extract_condensed(stdout)
    payload: dict[str, Any] = {
        "stdout": stdout,
        "stderr": stderr,
        "exit_code": result.exit_code,
        "timed_out": result.timed_out,
        "run_id": run_meta.run_id,
    }
    if csm and norm_res:
        payload["csm"] = csm.to_dict()
        payload["normalization_confidence"] = norm_res.confidence
    if contract_deprecation_warning:
        payload["contract_warning"] = contract_deprecation_warning
    if include_contract:
        payload["route_contract"] = route_contract
        payload["route_request"] = route_request
    return payload


def _phase_resolve_task_metadata(
    task_id: str | None,
    cwd: Path | None,
    prompt: str,
    agent: str | None,
    model: str | None,
    lane: str,
    effective_owner: str,
    correlation_id: str | None,
    idempotency_token: str | None,
) -> tuple[Any | None, Any | None]:
    """Build a TaskSpec from the project tasks/ directory (WP-?/task-io).

    Returns ``(task_spec, task_metadata)``. Both are ``None`` when ``task_id``
    is falsy or the task file is missing; both propagate when present. The
    import dance for ``TaskInput``/``TaskSpec``/``parse_task_file`` lives
    inside this helper so the orchestrator does not have to repeat it.
    """
    if not task_id:
        return None, None
    try:
        from thegent.models.task_io import TaskInput, TaskSpec
        from thegent.task import parse_task_file
    except Exception as exc:  # pragma: no cover - defensive
        _log.warning(
            "TaskSpec imports unavailable; skipping task metadata for %s: %s",
            task_id,
            exc,
        )
        return None, None

    tasks_dir = cwd / "tasks" if cwd else Path("tasks")
    task_file = tasks_dir / f"{task_id}.md"
    if not task_file.exists():
        _log.warning("Task file not found for task_id %s: %s", task_id, task_file)
        return None, None

    task_metadata = parse_task_file(task_file)
    raw_prompt = task_metadata.get("description") or task_metadata.get("task") or prompt
    spec = TaskSpec(
        task_id=task_id,
        input=TaskInput(
            task=raw_prompt,
            context={k: v for k, v in task_metadata.items() if k not in ("description", "task")},
        ),
        agent=agent,
        model=model,
        lane=lane,
        priority=task_metadata.get("priority"),
        owner=effective_owner,
        correlation_id=correlation_id,
        idempotency_token=idempotency_token,
    )
    _log.info("Loaded task metadata for %s (TaskSpec validated)", task_id)
    return spec, task_metadata


def _phase_dispatch_grounded_run(
    *,
    agent: str | None,
    prompt: str,
    model: str | None,
    effective_timeout: int,
    run_id: str,
    google_grounding: bool,
) -> dict[str, Any] | None:
    """Run the Gemini grounding path (returns payload or ``None`` to skip).

    Accepts ``run_id`` and ``google_grounding`` directly; builds the
    internal proxy internally. Returns ``None`` when ``google_grounding``
    is false or the agent is not in ``GEMINI_GROUNDING_AGENTS``. Returns
    a complete success payload when grounding succeeded, and an error
    payload when the upstream raised.
    """
    if not google_grounding:
        return None
    from types import SimpleNamespace

    run_meta = SimpleNamespace(
        run_id=run_id,
        _google_grounding_requested=google_grounding,
    )
    from thegent.agents.grounding import (
        GEMINI_GROUNDING_AGENTS,
        run_gemini_with_grounding,
    )

    if agent not in GEMINI_GROUNDING_AGENTS:
        return {
            "error": "Google grounding requires a Gemini-compatible agent.",
            "exit_code": 1,
            "run_id": run_meta.run_id,
        }
    try:
        grounded = run_gemini_with_grounding(
            prompt=prompt,
            model=model,
            timeout=int(effective_timeout),
        )
    except (ValueError, RuntimeError) as exc:
        return {
            "error": str(exc),
            "run_id": run_meta.run_id,
            "exit_code": 1,
        }
    payload: dict[str, Any] = {
        "stdout": grounded.stdout,
        "stderr": grounded.stderr,
        "exit_code": grounded.exit_code,
        "timed_out": grounded.timed_out,
        "run_id": run_meta.run_id,
    }
    if grounded.grounding_sources is not None:
        payload["grounding_sources"] = grounded.grounding_sources
    return payload


def _phase_build_fallback_plan(
    *,
    agent: str,
    model: str | None,
    full: bool,
    settings: ThegentSettings,
) -> tuple[list[str], "ContractTelemetry", "FallbackStateMachine"]:
    """Build the fallback plan: providers list + telemetry + state machine.

    Inline order is preserved: provider-fallbacks → catalog routes →
    ranking by parser quality → wrap in ``FallbackPolicy`` and
    ``FallbackStateMachine``.
    """
    from thegent.agents.state_machine import FallbackStateMachine
    from thegent.contracts.policy import FallbackPolicy
    from thegent.contracts.telemetry import (
        ContractTelemetry,
        rank_providers_by_parser_quality,
    )

    agents_to_try: list[str] = [agent] if agent else []
    if model:
        try:
            from thegent.models import ModelCatalog, normalize_model_id

            model_id = normalize_model_id(model)
            if hasattr(ModelCatalog, "routes_for"):
                routes = ModelCatalog.routes_for(model_id)
                agents_to_try.extend(r.provider for r in routes if r.provider != agent)
        except (ImportError, AttributeError) as _cat_exc:
            _log.debug("ModelCatalog lookup skipped (%s)", _cat_exc)

    provider_fallbacks = get_fallback_agents(agent or "unknown")
    for pf in provider_fallbacks:
        if pf not in agents_to_try:
            agents_to_try.append(pf)

    telemetry = ContractTelemetry(settings.session_dir)
    if settings.routing_parser_quality_enabled:
        agents_to_try = rank_providers_by_parser_quality(agents_to_try, telemetry, limit=100)
    policy = FallbackPolicy(
        allow_plain_fallback=settings.normalization_policy_allow_fallback,
        min_confidence_threshold=settings.normalization_policy_min_confidence,
        max_fallback_rate=settings.normalization_policy_max_fallback_rate,
        strict_providers=[p.strip() for p in settings.normalization_policy_strict_providers.split(",") if p.strip()],
    )
    fsm = FallbackStateMachine(
        providers=agents_to_try,
        run_id=getattr(settings, "_current_run_id", "unknown"),
        policy=policy,
        telemetry=telemetry,
        max_retries_per_provider=3,
    )
    return agents_to_try, telemetry, fsm


def _phase_build_runner_factory(
    *,
    circuit_breaker: Any,
    model: str | None,
    mode: str,
    settings: ThegentSettings,
    run_id: str,
) -> Callable[[str], AgentRunner | None]:
    """Return the ``runner_factory`` closure that wraps ``Runner.run``.

    Stashes ``run_id`` on settings so ``_phase_build_fallback_plan``
    can find it without a separate parameter. Honors G-GP-04 (skip
    providers with an open circuit) and injects ``agent_model`` so
    downstream runners can resolve the canonical backend.
    """
    settings._current_run_id = run_id

    def runner_factory(agent_name: str) -> AgentRunner | None:
        if circuit_breaker.is_open(agent_name):
            _log.warning("Circuit open for %s; skipping", agent_name)
            return None
        runner = get_runner(agent_name)
        if runner is None:
            return None
        original_run = runner.run
        agent_model = _resolve_agent_model_local(agent_name, model, mode, settings)

        def wrapped_run(**kwargs) -> RunResult:
            if agent_model:
                kwargs["agent_model"] = agent_model
            res = original_run(**kwargs)
            if res.exit_code != 0:
                circuit_breaker.record_failure(agent_name)
            return res

        @dataclass
        class RunnerProxy(AgentRunner):
            def run(
                self,
                prompt: str,
                cwd: Path | None,
                mode: str,
                timeout: int,
                *,
                use_stream: bool = True,
                live_output: bool = False,
                on_stdout: Callable[[str], None] | None = None,
                on_stderr: Callable[[str], None] | None = None,
                env: dict[str, str] | None = None,
                image_paths: list[str] | None = None,
            ) -> RunResult:
                return wrapped_run(
                    prompt=prompt,
                    cwd=cwd,
                    mode=mode,
                    timeout=timeout,
                    use_stream=use_stream,
                    live_output=live_output,
                    on_stdout=on_stdout,
                    on_stderr=on_stderr,
                    env=env,
                    image_paths=image_paths,
                )

        return RunnerProxy()

    return runner_factory


def _classify_error_class(result: Any) -> str | None:
    """Map ``result`` attributes to an error-class: timeout / usage_limit / api_error / None."""
    if result.timed_out:
        return "timeout"
    if is_usage_limit(result):
        return "usage_limit"
    if result.exit_code != 0:
        return "api_error"
    return None


def _enqueue_critical_dlq(
    settings: ThegentSettings,
    run_meta: RunMeta,
    status: str,
    result: Any,
) -> None:
    """Best-effort DLQ enqueue for critical-lane runs (WP-2008)."""
    try:
        from thegent.execution import DLQManager

        DLQManager(settings.session_dir).enqueue(
            run_meta,
            f"Run {status}: {result.stderr or 'No result'}",
        )
        _log.info("Critical run %s; enqueued to DLQ.", status)
    except Exception as exc:  # pragma: no cover - DLQ best-effort
        _log.debug("DLQ enqueue skipped: %s", exc)


def _check_unknown_contract(lane: str, norm_res: Any, error_class: str | None) -> bool:
    """Return True when a critical-lane run has an unrecognised source contract."""
    if lane != "critical":
        return False
    if norm_res is None:
        return False
    _known = ("csm-v1", "task-tool-18", "zen-rich-v1", "xml-tags", "plain")
    return norm_res.csm.source_contract == "fallback-plain" or norm_res.csm.source_contract not in _known


def _phase_classify_run_result(
    *,
    result: Any,
    pol_res: str,
    pol_reason: str,
    norm_res: Any,
    lane: str,
    settings: ThegentSettings,
    run_meta: RunMeta,
    fsm_status: str,
    start_time: float,
    registry: RunRegistry,
    maif_runner: Any,
) -> tuple[int, str, str | None, str]:
    """Classify a finished run: exit_code, final status, error_class, output_summary.

    Owns the post-failure housekeeping that previously lived inline in
    ``run_impl_core``:

    * Critical-lane DLQ enqueue (WP-2008)
    * G-CA-03 C3 unknown-contract reclassification
    * error-class mapping (timeout / usage_limit / api_error)
    * MAIF ``record_run_end`` output summary build
    * Cost + register_run_end wiring inputs
    """
    if result is None:
        return 1, "failed", None, "Unknown agent or no result"

    error_class = _classify_error_class(result)
    status = fsm_status
    exit_code = result.exit_code

    if status == "success":
        exit_code = 0
        status = "completed"
    else:
        status = "timed_out" if result.timed_out else "failed"
        if lane == "critical":
            _enqueue_critical_dlq(settings, run_meta, status, result)

    if _check_unknown_contract(lane, norm_res, error_class):
        status = "failed"
        exit_code = 1
        error_class = error_class or "unknown_contract"

    output_summary = (result.stdout or result.stderr or "")[:500]
    return exit_code, status, error_class, output_summary


def _phase_release_idle_and_publish(
    *,
    cwd: Path | None,
    runner: Any = None,
    run_id: str,
    start_ts: float,
    exit_code: int,
) -> None:
    """Release idle eye state + publish ``run.end`` bus event (best-effort).

    ``runner`` defaults to ``None`` so legacy call sites that omitted the
    kwarg (e.g. ``run_impl_core`` before WL137) continue to work without a
    TypeError. Failures inside the helper are non-fatal; the orchestrator
    must continue assembling the payload even if the UX bus is unreachable.
    """
    try:
        from thegent.cli.shared.eye_state import EyeState

        EyeState(cwd).release_idle()
    except Exception as exc:  # pragma: no cover - UX best-effort
        _log.debug("EyeState.release_idle skipped: %s", exc)
    try:
        from thegent.cli.resources.bus_client import publish_bus_event

        publish_bus_event(
            cwd,
            "run.end",
            {
                "run_id": run_id,
                "runner": runner,
                "exit_code": exit_code,
                "duration_ms": (time.monotonic() - start_ts) * 1000,
            },
        )
    except Exception as exc:  # pragma: no cover - bus best-effort
        _log.debug("Failed to publish run.end bus event: %s", exc)


def _phase_finalize_run_outcome(
    *,
    shadow_ws: Any,
    settings: ThegentSettings,
    status: str,
    run_meta: RunMeta,
    exit_code: int,
    duration: float,
    error_class: str | None,
    cost_usd: float | None,
    registry: RunRegistry,
    maif_runner: Any,
    output_summary: str,
    result: Any,
    norm_res: Any,
    auditor: Any,
    agent: str | None,
    cwd: Path | None,
    start_time: float,
    use_stream: bool,
    stdout: str,
    stderr: str,
    contract_deprecation_warning: str | None,
    include_contract: bool,
    route_contract: dict[str, Any] | None,
    route_request: dict[str, Any] | None,
    tracker: Any,
    prompt: str,
) -> dict[str, Any]:
    """Finalize a finished run: shadow, cost, register, postlude, payload.

    Consolidates the ~74-line post-classification cleanup chain into a single
    helper so the orchestrator body can shrink from 405L to ~332L (WL147
    stretch target: 350L). Owns:

    * MTSP-12 shadow workspace finalize (auto-merge / destroy)
    * WP-Y4 cost estimation
    * WP-3xxx run-end registration + MAIF record_run_end
    * WP-16002 teammate delegation status update
    * WP-3007/WP-2007/WP-3002 success postlude (trust record + evidence + MAIF)
    * Unknown-agent payload short-circuit
    * stdout/stderr normalization
    * Eye idle release + ``run.end`` bus event
    * Payload assembly
    * Cost tracker finalization
    * WP-DX-024 conversation dumps

    Returns the final ``payload`` dict the orchestrator returns directly.
    """
    # MTSP-12: Shadow finalize (auto-merge + destroy on success / destroy-only
    # on failure).
    _phase_finalize_shadow(shadow_ws, settings, status)

    # WP-Y4: cost estimate.
    cost_usd = _phase_estimate_run_cost(run_meta) if cost_usd is None else cost_usd

    # WP-3xxx: register run end + MAIF record_run_end.
    _phase_register_run_end(
        registry,
        run_meta.run_id,
        exit_code,
        status,
        duration,
        error_class,
        cost_usd,
        maif_runner=maif_runner,
        output_summary=output_summary,
    )

    # WP-16002: Update teammate delegation status (no-op when task_id is falsy).
    _phase_update_teammate_status(settings, getattr(run_meta, "task_id", None), status, result)

    # WP-3007/WP-2007/WP-3002: trust boundary record + evidence lint + MAIF.
    _phase_record_success_postlude(settings, run_meta, result, norm_res, auditor)

    if not result:
        return _phase_assemble_unknown_agent_payload(agent, run_meta.run_id)

    stdout, stderr = _phase_normalize_result_strings(result)

    # Free the eye idle state + publish ``run.end`` bus event.
    _phase_release_idle_and_publish(
        cwd=cwd,
        run_id=run_meta.run_id,
        start_ts=start_time,
        exit_code=exit_code,
    )

    # Assemble payload
    payload = _phase_assemble_payload(
        result=result,
        norm_res=norm_res,
        use_stream=use_stream,
        stdout=stdout,
        stderr=stderr,
        run_meta=run_meta,
        contract_deprecation_warning=contract_deprecation_warning,
        include_contract=include_contract,
        route_contract=route_contract,
        route_request=route_request,
    )

    # End cost tracking.
    _phase_finalize_tracker(tracker)

    # WP-DX-024: Always write conversation dumps to docs/.
    _phase_write_run_dumps(settings, run_meta.run_id, cwd, prompt, stdout, result)

    return payload


# ----------------------------------------------------------------------------
# WL137 — Composite phase helpers (L9 final hardening pass).
#
# These helpers own bundle-extraction blocks that were inline inside
# ``run_impl_core``. Each helper keeps CC ≤ 8 and body ≤ 40 lines so the
# orchestrator can shrink to a thin composer (target: CC ≤ 18, body ≤ 280L).
# ----------------------------------------------------------------------------


@dataclass
class _ExecutionServices:
    """Bundle of per-run execution helpers resolved once by the orchestrator.

    The dataclass exists so ``run_impl_core`` can stay a thin composer
    instead of constructing six registries inline. Fields are typed as
    ``Any`` because the canonical home of these types is the
    ``thegent.execution`` package which is expensive to import eagerly.
    """

    circuit_breaker: Any
    trust_boundary: Any
    override_registry: Any
    policy_engine: Any
    auditor: Any
    maif_runner: Any
    escalation_sla_minutes: int


def _phase_init_tracker(
    settings: ThegentSettings,  # noqa: ARG001  # reserved for future adapter wiring
    run_id: str | None,
) -> tuple[str, Any]:
    """Initialize the cost tracker and resolve the canonical run_id.

    Returns ``(rid, tracker)`` where ``rid`` is the user-supplied
    ``run_id`` or a fresh ``run_<8-hex>``. The tracker is the canonical
    cost singleton from ``thegent.cost.tracker``.
    """
    from thegent.cost.tracker import get_run_cost_tracker

    tracker = get_run_cost_tracker()
    rid = run_id or f"run_{uuid.uuid4().hex[:8]}"
    tracker.start_run(rid)
    return rid, tracker


def _phase_finalize_tracker(tracker: Any) -> None:
    """End the cost-tracker run (best-effort).

    Symmetric companion to :func:`_phase_init_tracker`; named separately so
    the orchestrator's end-of-run block stays one delegated line. Failures
    here are non-fatal — they only affect cost telemetry.
    """
    if tracker is None:
        return
    try:
        tracker.end_run()
    except Exception as exc:  # pragma: no cover - cost tracking best-effort
        _log.debug("Cost tracker end_run failed: %s", exc)


def _phase_resolve_grounded_agent(
    *,
    agent_name: str | None,
    model: str | None,
    provider: str | None,
    google_grounding: bool,
    rid: str,
) -> tuple[str | None, dict[str, Any] | None]:
    """Resolve ``agent`` (from model alias when needed) and enforce grounding.

    Returns ``(agent, error_payload)``. When the input requires model-based
    resolution and that resolution raises, ``error_payload`` is non-None
    and the orchestrator short-circuits with it. When ``google_grounding``
    is True and the resolved agent is not Gemini-backed, ``error_payload``
    is also non-None. ``agent`` may be ``None`` only when a short-circuit
    occurred; on success it is the canonical agent name (or ``""``).
    """
    agent = agent_name
    if agent is None and model:
        agent_or_error, err_payload = _phase_resolve_agent_from_model(model, provider, rid)
        if err_payload is not None:
            return None, err_payload
        agent = agent_or_error
    agent = resolve_agent(agent or "")

    if google_grounding:
        from thegent.agents.grounding import GEMINI_GROUNDING_AGENTS

        if agent not in GEMINI_GROUNDING_AGENTS:
            return (
                None,
                {
                    "error": (
                        f"Google grounding requires a Gemini-backed agent; received '{agent}'."
                        " Use a Gemini or antigravity agent."
                    ),
                    "exit_code": 1,
                    "run_id": rid,
                },
            )
    return agent, None


def _phase_build_execution_services(
    settings: ThegentSettings,
    registry: RunRegistry,
) -> _ExecutionServices:
    """Construct the per-run execution service bundle.

    Returns the ``_ExecutionServices`` dataclass with one instance of each
    per-run registry (audit, circuit-breaker, override, policy, trust-
    boundary) plus the MAIFRunner and the resolved escalation SLA minutes.
    """
    from thegent.execution import (
        Auditor,
        OverrideRegistry,
        PolicyEngine,
        TrustBoundaryValidator,
    )

    circuit_breaker = CircuitBreakerRegistry(settings.session_dir)
    trust_boundary = TrustBoundaryValidator(settings.session_dir)
    override_registry = OverrideRegistry(settings.session_dir)
    policy_engine = PolicyEngine(settings)
    auditor = Auditor(registry.registry_path)
    maif_runner = MAIFRunner()
    escalation_sla_minutes = 30
    try:
        escalation_sla_minutes = int(settings.escalation_sla_minutes)
    except (TypeError, ValueError):
        escalation_sla_minutes = 30
    return _ExecutionServices(
        circuit_breaker=circuit_breaker,
        trust_boundary=trust_boundary,
        override_registry=override_registry,
        policy_engine=policy_engine,
        auditor=auditor,
        maif_runner=maif_runner,
        escalation_sla_minutes=escalation_sla_minutes,
    )


def _phase_publish_run_start(
    *,
    registry: RunRegistry,
    maif_runner: Any,
    run_meta: RunMeta,
    prompt: str,
) -> None:
    """Publish the run-start event to both registry + MAIF runners.

    Combines ``registry.register_start`` and ``maif_runner.record_run_start``
    into one auditable place so the orchestrator's CC stays low.
    """
    registry.register_start(run_meta)
    maif_runner.record_run_start(
        run_id=run_meta.run_id,
        owner=run_meta.owner or "unknown",
        prompt=prompt or "",
        agent=run_meta.agent or "unknown",
    )


def _phase_run_under_keepalive(
    *,
    fsm: Any,
    runner_factory: Any,
    prompt: str,
    agent_cwd: Path,
    mode: str,
    effective_timeout: int,
    use_stream: bool,
    shadow_env: dict[str, str] | None,
    settings: ThegentSettings,
    locked_tokens: list[tuple[Path, Any]],
    rid: str,
) -> tuple[Any, Any]:
    """Execute ``fsm.run`` inside a keepalive context, releasing leases.

    The ``try/finally`` ensures the non-worktree leases are released even
    when the keepalive context or the FSM crashes. ``settings`` resolves
    the keepalive interval (default 30s) so the orchestrator can hand in
    any settings instance. Returns ``(result, norm_res)`` so the
    orchestrator can keep classifying the outcome.
    """
    from thegent.ux.keepalive import keepalive as _keepalive

    keepalive_interval = float(getattr(settings, "keepalive_interval", 30.0))
    try:
        with _keepalive(interval_s=keepalive_interval):
            result, norm_res = fsm.run(
                runner_factory=runner_factory,
                prompt=prompt,
                cwd=agent_cwd,
                mode=mode,
                timeout=effective_timeout,
                use_stream=use_stream,
                env=shadow_env,
            )
    finally:
        _phase_release_resource_leases(settings, locked_tokens, rid)
    return result, norm_res


def _phase_dispatch_policy_outcome(
    *,
    pol_res: str,
    pol_reason: str,
    run_meta: RunMeta,
    settings: ThegentSettings,
    registry: RunRegistry,
    services: _ExecutionServices,
) -> dict[str, Any] | None:
    """Dispatch ``pol_res`` to deny / pause / warn side-effects.

    ``deny`` and ``pause`` short-circuit with a return payload; ``warn``
    prints the warning to the operator console and returns ``None`` so
    the orchestrator can continue. Any other ``pol_res`` value also
    returns ``None`` (allowed).
    """
    if pol_res == "deny":
        return _phase_register_policy_denial(
            run_meta,
            services.escalation_sla_minutes,
            pol_reason,
            registry,
        )
    if pol_res == "pause":
        return _phase_register_hitl_pause(
            settings,
            run_meta,
            registry,
            services.escalation_sla_minutes,
            pol_reason,
        )
    if pol_res == "warn":
        # AUDIT-N+2: route through ``print_exc`` so a malicious
        # policy-engine payload (``[red]pwned[/red]``) cannot inject
        # Rich markup into the operator's terminal. The helper
        # accepts any ``object`` (not just ``Exception``) per F-15's
        # signature widening.
        print_exc(console, "Policy Warning:", pol_reason, style="yellow")
    return None


# ---------------------------------------------------------------------------
# WL140 stretch helpers (CC 27 → ≤18 for run_impl_core).
#
# Three additional extractions collapse the orchestrator's remaining inline
# branches into single delegations:
#   - ``_phase_normalize_registry_path`` (CC 2) absorbs the isinstance + elif
#     normalization of ``RunRegistry.registry_path`` (was 2 branches inline).
#   - ``_phase_run_preflight`` (CC ≤ 12) chains eleven early-validation helpers
#     and returns the resolved state via ``_PreflightOutcome`` (was 11 branches
#     + several side-effecting assignments inline).
#   - ``_phase_assemble_unknown_agent_payload`` (CC 1) absorbs the final
#     ``if not result`` unknown-agent error path.
# ---------------------------------------------------------------------------


def _phase_normalize_registry_path(registry: RunRegistry) -> Path | None:
    """Normalize ``RunRegistry.registry_path`` for freshness validation.

    Returns ``Path`` when ``registry_path`` is a string/Path/PathLike,
    ``None`` otherwise. The pre-extraction inline block warned on
    unexpected types so we preserve that behavior.
    """
    raw = getattr(registry, "registry_path", None)
    if isinstance(raw, (str, Path, os.PathLike)):
        return Path(raw)
    if raw is not None:
        _log.warning("Skipping freshness check; unexpected registry path type: %r", type(raw))
    return None


@dataclass
class _PreflightOutcome:
    """Resolved state from the pre-flight pipeline (WL140).

    ``payload`` is non-None when the run should short-circuit (caller
    returns it as the run output). When ``payload`` is None, the caller
    continues with the resolved state in the other fields.
    """

    payload: dict[str, Any] | None
    agent: str | None
    model: str | None
    route_contract: dict[str, Any] | None
    route_request: dict[str, Any] | None
    prompt: str
    effective_timeout: int
    cwd: Path | None
    contract_deprecation_warning: str | None
    services: _ExecutionServices | None


def _phase_run_preflight(
    *,
    settings: ThegentSettings,
    rid: str,
    agent: str | None,
    model: str | None,
    routing: str | None,
    include_contract: bool,
    route_contract: dict[str, Any] | None,
    route_request: dict[str, Any] | None,
    prompt: str,
    contract_version: str | None,
    config_provider: "ConfigProvider | None",
    timeout: int | None,
    tenant_id: str | None,
    cd: Path | None,
    registry: RunRegistry,
    idempotency_token: str | None,
) -> _PreflightOutcome:
    """Run the early-validation + normalization pipeline (WL140 stretch).

    Handles the eight early-exit sub-steps that own their own canonical
    payload shapes (budget gate, contract version, cwd resolution,
    terminal discovery, input guardrails, idempotency replay, trust
    boundary, registry-path normalization). Returns the resolved state
    via :class:`_PreflightOutcome` so ``run_impl_core`` stays a thin
    composer (CC ≤ 18 stretch target).

    The four mid-phase helpers (``_phase_resolve_grounded_agent``,
    ``_phase_build_execution_services``, ``_phase_acquire_concurrency``,
    ``_phase_fatigue_freshness_burst``) remain DIRECT calls from
    ``run_impl_core`` because WL131 / WL137 wiring contracts assert
    that delegation. Inline ordering is preserved verbatim from the
    pre-extraction body so all WL131–WL137 contract suites continue
    to pass without edits.
    """
    budget_block = _phase_budget_gate(settings, rid)
    if budget_block is not None:
        return _PreflightOutcome(
            payload=budget_block,
            agent=agent,
            model=model,
            route_contract=route_contract,
            route_request=route_request,
            prompt=prompt,
            effective_timeout=int(timeout or 0),
            cwd=None,
            contract_deprecation_warning=None,
            services=None,
        )

    agent, model, route_contract, route_request = _apply_pareto_routing_local(
        agent, model, routing, include_contract, route_contract, route_request
    )
    agent, model, route_contract, route_request = _phase_auto_route(
        settings, agent, model, prompt, include_contract, route_contract, route_request
    )

    _allowed, _contract_error, contract_deprecation_warning = _phase_evaluate_contract_version(contract_version, rid)
    if _contract_error is not None:
        return _PreflightOutcome(
            payload=_contract_error,
            agent=agent,
            model=model,
            route_contract=route_contract,
            route_request=route_request,
            prompt=prompt,
            effective_timeout=int(timeout or 0),
            cwd=None,
            contract_deprecation_warning=None,
            services=None,
        )

    effective_timeout = _phase_resolve_effective_timeout(settings, config_provider, timeout, agent, tenant_id)

    cwd, cwd_error = _phase_resolve_cwd(cd, rid)
    if cwd_error is not None:
        return _PreflightOutcome(
            payload=cwd_error,
            agent=agent,
            model=model,
            route_contract=route_contract,
            route_request=route_request,
            prompt=prompt,
            effective_timeout=effective_timeout,
            cwd=None,
            contract_deprecation_warning=contract_deprecation_warning,
            services=None,
        )

    _phase_terminal_discovery(settings, cwd)

    guardrail_error = _phase_input_guardrails(prompt, agent, model, cwd, rid)
    if guardrail_error is not None:
        return _PreflightOutcome(
            payload=guardrail_error,
            agent=agent,
            model=model,
            route_contract=route_contract,
            route_request=route_request,
            prompt=prompt,
            effective_timeout=effective_timeout,
            cwd=cwd,
            contract_deprecation_warning=contract_deprecation_warning,
            services=None,
        )

    replay_payload = _phase_idempotency_replay(registry, idempotency_token)
    if replay_payload is not None:
        return _PreflightOutcome(
            payload=replay_payload,
            agent=agent,
            model=model,
            route_contract=route_contract,
            route_request=route_request,
            prompt=prompt,
            effective_timeout=effective_timeout,
            cwd=cwd,
            contract_deprecation_warning=contract_deprecation_warning,
            services=None,
        )

    return _PreflightOutcome(
        payload=None,
        agent=agent,
        model=model,
        route_contract=route_contract,
        route_request=route_request,
        prompt=prompt,
        effective_timeout=effective_timeout,
        cwd=cwd,
        contract_deprecation_warning=contract_deprecation_warning,
        services=None,
    )


def _phase_apply_trust_boundary(services: "_ExecutionServices", rid: str) -> dict[str, Any] | None:
    """Apply the trust-boundary gate to a built services bundle (WL140 stretch).

    Returns ``None`` on success, or the canonical failure payload (with
    ``run_id`` populated) when the boundary denies the run. Extracted so
    ``run_impl_core`` does not own the 4-line + branch shape.
    """
    trust_error = _phase_trust_boundary(services.settings, services.trust_boundary)
    if trust_error is None:
        return None
    trust_error["run_id"] = rid
    return trust_error


def _phase_build_run_meta(
    *,
    run_id: str | None,
    agent: str | None,
    model: str | None,
    prompt: str,
    cwd: Path | None,
    effective_owner: str,
    lane: str,
    confidence: float | None,
    idempotency_token: str | None,
    resolved_domain_tag: str,
) -> RunMeta:
    """Build the canonical ``RunMeta`` for a run with all defaults applied (WL140 stretch).

    Centralizes the five ``x or default`` short-circuits that the orchestrator
    previously owned inline (run_id / agent / model / idempotency_token /
    confidence) so ``run_impl_core`` stays a thin composer (CC ≤ 18 stretch
    target).
    """
    return RunMeta(
        run_id=run_id or f"run_{uuid.uuid4().hex[:8]}",
        agent=agent or "unknown",
        model=model or "",
        prompt=prompt,
        cwd=str(cwd) if cwd is not None else "",
        owner=effective_owner,
        lane=lane,
        confidence=confidence if confidence is not None else 1.0,
        idempotency_token=idempotency_token or "",
        domain_tag=resolved_domain_tag,
    )


def _phase_normalize_result_strings(result: Any) -> tuple[str, str]:
    """Normalize ``result.stderr`` / ``result.stdout`` to strings (WL140 stretch).

    Returns ``(stdout, stderr)``. Both fall back to empty strings when the
    underlying ``Result`` is missing either field (historically the case for
    some sparse error paths). Extracted so ``run_impl_core`` does not own two
    ``x or ""`` short-circuits inline.
    """
    return result.stdout or "", result.stderr or ""


def _phase_assemble_unknown_agent_payload(agent: str | None, run_id: str) -> dict[str, Any]:
    """Build the canonical "unknown agent" failure payload (WL140 stretch).

    The pre-extraction inline branch returned
    ``{"error": f"Unknown agent: {agent}", "agents": ", ".join(list_agent_names()), ...}``
    inside ``run_impl_core``. Promoting it to a helper drops one more
    branch from the orchestrator and centralizes the canonical error
    payload (helpful when multiple run paths converge on the same error).
    """
    return {
        "error": f"Unknown agent: {agent}",
        "agents": ", ".join(list_agent_names()),
        "exit_code": 1,
        "run_id": run_id,
    }


def run_impl_core(
    agent: str | None,
    prompt: str,
    cd: Path | None = None,
    mode: str = "write",
    timeout: int | None = None,
    full: bool = False,
    live: bool = True,
    model: str | None = None,
    provider: str | None = None,
    run_id: str | None = None,
    owner: str | None = None,
    include_contract: bool = False,
    route_contract: dict[str, Any] | None = None,
    route_request: dict[str, Any] | None = None,
    lane: str = "standard",
    confidence: float | None = None,
    override_reason: str | None = None,
    contract_version: str | None = None,
    domain: str | None = None,
    idempotency_token: str | None = None,
    correlation_id: str | None = None,
    speculative: bool = False,
    arbitration: str | None = None,
    routing: str | None = None,
    enable_search: bool = False,
    debug: bool = False,
    task_id: str | None = None,
    shadow: bool = False,
    lock: list[str] | None = None,
    remote: str | None = None,
    config_provider: "ConfigProvider | None" = None,
    tenant_id: str | None = None,
    previous_session_id: str | None = None,
    reasoning_effort: str | None = None,
    output_schema: str | None = None,
    image_paths: list[str] | None = None,
    audio_files: list[str] | None = None,
    google_grounding: bool = False,
    failover: bool = False,
    impl_ns: Any | None = None,
) -> dict[str, Any]:
    """
    Run an agent or droid with the given prompt.
    Returns dict with keys: stdout, stderr, exit_code, timed_out.
    Model-first: agent=None, model set; provider hint for routing.

    ``failover`` is accepted for parity with the CLI surface
    (``--failover`` is forwarded by ``run_app._run_callback``) and
    with :func:`bg_impl_core` which consumes it when building a
    subprocess command.  Foreground runs do not spawn a subprocess
    so the flag has no direct effect here; downstream callers may
    inspect the value via the contract layer if needed.
    """
    if impl_ns is None:
        raise ValueError("impl_ns is required")
    _bind_impl_namespace(impl_ns)

    settings = ThegentSettings()
    # WL137: bundle tracker init + rid generation into a single helper so the
    # orchestrator stays a thin composer (CC stays low).
    rid, tracker = _phase_init_tracker(settings, run_id)

    # Registry integration
    registry = RunRegistry(settings.session_dir)

    # WL140 stretch: the eight early-exit sub-steps (budget gate, contract
    # version, cwd resolution, terminal discovery, input guardrails,
    # idempotency replay, trust boundary, registry-path normalization)
    # consolidated into ``_phase_run_preflight``. The helper owns all the
    # canonical ``payload`` shapes for those sub-steps and returns the
    # resolved state via ``_PreflightOutcome``. The four mid-phase helpers
    # (``_phase_resolve_grounded_agent``, ``_phase_acquire_concurrency``,
    # ``_phase_build_execution_services``, ``_phase_fatigue_freshness_burst``)
    # remain DIRECT calls below because WL131 / WL137 wiring contracts
    # assert that delegation.
    _preflight = _phase_run_preflight(
        settings=settings,
        rid=rid,
        agent=agent,
        model=model,
        routing=routing,
        include_contract=include_contract,
        route_contract=route_contract,
        route_request=route_request,
        prompt=prompt,
        contract_version=contract_version,
        config_provider=config_provider,
        timeout=timeout,
        tenant_id=tenant_id,
        cd=cd,
        registry=registry,
        idempotency_token=idempotency_token,
    )
    if _preflight.payload is not None:
        return _preflight.payload

    agent = _preflight.agent
    model = _preflight.model
    route_contract = _preflight.route_contract
    route_request = _preflight.route_request
    prompt = _preflight.prompt
    effective_timeout = _preflight.effective_timeout
    cwd = _preflight.cwd
    contract_deprecation_warning = _preflight.contract_deprecation_warning

    # WP-5001: Concurrency control — DIRECT call (WL131 contract).
    concurrency_error = _phase_acquire_concurrency(settings, lane, task_id, rid)
    if concurrency_error is not None:
        return concurrency_error

    # WP-5001: Speculative Execution Mode (no-op until thread-pool race lands).
    if speculative:
        _log.info("Speculative execution active; racing multiple providers.")

    # WL137: bundle the per-run execution services into a single dataclass so
    # the orchestrator stays a thin composer (CC ↓, inlined 18 lines).
    services = _phase_build_execution_services(settings, registry)
    circuit_breaker = services.circuit_breaker
    override_registry = services.override_registry
    policy_engine = services.policy_engine
    auditor = services.auditor
    maif_runner = services.maif_runner

    # WP-3007: Trust Boundary Checks — delegated to ``_phase_apply_trust_boundary``
    # so the canonical failure-payload shape (with ``run_id``) lives in one
    # auditable place (WL140 stretch).
    trust_error = _phase_apply_trust_boundary(services, rid)
    if trust_error is not None:
        return trust_error

    # WP-4004/WP-4005/WP-5002: Combined fatigue + freshness + burst checks
    # DIRECT call (WL131 contract). ``registry_path`` is resolved here
    # (orchestrator owns the registry) so the helper stays storage-agnostic.
    _registry_path = _phase_normalize_registry_path(registry)
    fatigue_error = _phase_fatigue_freshness_burst(settings, _registry_path, lane, rid)
    if fatigue_error is not None:
        return fatigue_error

    # Phase: agent-from-model resolution + Google-grounding precondition.
    _agent, _grounding_err = _phase_resolve_grounded_agent(
        agent_name=agent,
        model=model,
        provider=provider,
        google_grounding=google_grounding,
        rid=rid,
    )
    if _grounding_err is not None:
        return _grounding_err
    agent = _agent

    # Resolve TaskSpec + metadata (task-file import / file-check / delegation).
    resolved_domain_tag = str(domain) if domain else str(settings.default_domain_tag)
    effective_owner = owner or _default_owner_tag(cwd)
    _task_spec, _task_metadata = _phase_resolve_task_metadata(  # noqa: RUF059 (documented contract)
        task_id=task_id,
        cwd=cwd,
        prompt=prompt,
        agent=agent,
        model=model,
        lane=lane,
        effective_owner=effective_owner,
        correlation_id=correlation_id,
        idempotency_token=idempotency_token,
    )

    run_meta = _phase_build_run_meta(
        run_id=run_id,
        agent=agent,
        model=model,
        prompt=prompt,
        cwd=cwd,
        effective_owner=effective_owner,
        lane=lane,
        confidence=confidence,
        idempotency_token=idempotency_token,
        resolved_domain_tag=resolved_domain_tag,
    )

    # G-GP-02: Google grounding dispatch — delegated to
    # ``_phase_dispatch_grounded_run``. The helper returns a complete payload
    # when grounding succeeded or short-circuits with an error payload when
    # the agent is not Gemini-compatible. ``None`` means "continue the
    # non-grounded pipeline".
    grounded_payload = _phase_dispatch_grounded_run(
        agent=agent,
        prompt=prompt,
        model=model,
        effective_timeout=int(effective_timeout),
        run_id=run_meta.run_id,
        google_grounding=google_grounding,
    )
    if grounded_payload is not None:
        return grounded_payload

    # WP-3001: Policy Evaluation + WP-3003: Override TTL — delegated to
    # _phase_evaluate_policy_with_override so the override-cached branch
    # lives in one auditable place.
    pol_res, pol_reason = _phase_evaluate_policy_with_override(
        policy_engine,
        override_registry,
        run_meta,
        registry,
        effective_owner,
        override_reason,
    )

    run_meta.policy_result = pol_res
    run_meta.policy_reason = pol_reason

    # WP-3002: Signing
    run_meta.signature = auditor.sign_run(run_meta)

    # WL137: deny/pause/warn dispatch (was three inline branches) + the
    # subsequent register_start + record_run_start pair both moved into
    # standalone helpers so the orchestrator's CC ↓. ``policy_payload``
    # is non-None only when the policy engine short-circuits.
    policy_payload = _phase_dispatch_policy_outcome(
        pol_res=pol_res,
        pol_reason=pol_reason,
        run_meta=run_meta,
        settings=settings,
        registry=registry,
        services=services,
    )
    if policy_payload is not None:
        return policy_payload

    _phase_publish_run_start(
        registry=registry,
        maif_runner=maif_runner,
        run_meta=run_meta,
        prompt=prompt,
    )
    start_time = time.time()

    # L3 Memory: load past context for this agent (MTSP-?/mem-tier-3). Delegated
    # to ``_phase_load_l3_memory_context`` so the MemoryManager instantiation,
    # asyncio.run_until_complete dance, and ctx_block formatting live in one
    # auditable place. Returns ``(prompt, injected_flag)``; we accept the
    # augmented prompt back when injection succeeded.
    prompt, _mem_injected = _phase_load_l3_memory_context(agent, prompt)

    use_stream = not full

    # WP-X6: Fallback Control Plane + G-CA-02 B2 Parser-quality routing —
    # delegated to ``_phase_build_fallback_plan`` so the provider-fallbacks,
    # catalog routes, parser-quality ranking, and ``FallbackStateMachine``
    # construction live in one auditable place.
    _agents_to_try, _telemetry, fsm = _phase_build_fallback_plan(  # noqa: RUF059 (documented contract)
        agent=agent or "",
        model=model,
        full=full,
        settings=settings,
    )

    runner_factory = _phase_build_runner_factory(
        circuit_breaker=circuit_breaker,
        model=model,
        mode=mode,
        settings=settings,
        run_id=run_meta.run_id,
    )

    # MTSP-12: Shadow Workspace Integration — delegated to
    # ``_phase_setup_shadow_workspace`` so ShadowWorkspace.create() + env
    # export + ImportError fallback all live in one auditable place.
    agent_cwd, shadow_env, shadow_ws = _phase_setup_shadow_workspace(settings, cwd, run_meta.run_id, shadow)

    # MTSP-15: Resource Locking (Non-worktree coordination) — delegated to
    # ``_phase_acquire_resource_leases`` so the FileLeaseRegistry claim loop
    # + failure short-circuit live in one auditable place.
    lease_result = _phase_acquire_resource_leases(
        settings, lock, cwd or Path.cwd(), run_meta.run_id, int(effective_timeout)
    )
    if isinstance(lease_result, dict):
        return lease_result
    locked_tokens: list[tuple[Path, Any]] = lease_result

    # WL137: keepalive-wrapped fsm.run + lease release consolidated into
    # ``_phase_run_under_keepalive``. The duplicate ``_bind_impl_namespace``
    # + ``settings = ThegentSettings()`` re-bind was a no-op (already done
    # at the top of the orchestrator) so it is removed.
    result, norm_res = _phase_run_under_keepalive(
        fsm=fsm,
        runner_factory=runner_factory,
        prompt=prompt,
        agent_cwd=agent_cwd,
        mode=mode,
        effective_timeout=effective_timeout,
        use_stream=use_stream,
        shadow_env=shadow_env,
        settings=settings,
        locked_tokens=locked_tokens,
        rid=run_meta.run_id,
    )

    # WP-X6: classify run outcome (status, exit_code, error_class, output_summary).
    # WP-2008 (DLQ), G-CA-03 C3 (unknown contract), and the error-class mapping
    # all live in ``_phase_classify_run_result`` so the orchestrator stays a thin
    # composer. The DLQ + known-contract + class-mapping block used to be 50+
    # lines of inline branching.
    duration = time.time() - start_time

    exit_code, status, error_class, output_summary = _phase_classify_run_result(
        result=result,
        pol_res=pol_res,
        pol_reason=pol_reason,
        norm_res=norm_res,
        lane=lane,
        settings=settings,
        run_meta=run_meta,
        fsm_status=fsm.state.status,
        start_time=start_time,
        registry=registry,
        maif_runner=maif_runner,
    )

    return _phase_finalize_run_outcome(
        shadow_ws=shadow_ws,
        settings=settings,
        status=status,
        run_meta=run_meta,
        exit_code=exit_code,
        duration=duration,
        error_class=error_class,
        cost_usd=cost_usd,
        registry=registry,
        maif_runner=maif_runner,
        output_summary=output_summary,
        result=result,
        norm_res=norm_res,
        auditor=auditor,
        agent=agent,
        cwd=cwd,
        start_time=start_time,
        use_stream=use_stream,
        stdout=stdout,
        stderr=stderr,
        contract_deprecation_warning=contract_deprecation_warning,
        include_contract=include_contract,
        route_contract=route_contract,
        route_request=route_request,
        tracker=tracker,
        prompt=prompt,
    )


# ----------------------------------------------------------------------------
# WL141 — bg_impl_core phase helpers (L9 final hardening pass).
#
# These helpers extract sub-segments from ``bg_impl_core`` so the orchestrator
# can shrink to a thin composer (target: CC ≤ 30, body ≤ 280 lines — mirror of
# WL137's run_impl_core extraction). Each helper owns exactly one phase,
# keeps CC ≤ 12 (≤ 18 for composite), and body ≤ 40 lines.
# ----------------------------------------------------------------------------


def _phase_bg_init_tracker(
    settings: ThegentSettings,  # noqa: ARG001 — reserved for adapter wiring
    run_id: str | None,
) -> tuple[str, Any]:
    """Initialize the cost tracker + resolve the canonical ``bg_<8-hex>`` rid.

    Mirrors :func:`_phase_init_tracker` but uses the ``bg_`` prefix so the
    background-launcher tracks cost independently of any nested foreground
    run spawned via ``run agent`` later.
    """
    from thegent.cost.tracker import get_run_cost_tracker

    tracker = get_run_cost_tracker()
    rid = run_id or f"bg_{uuid.uuid4().hex[:8]}"
    tracker.start_run(rid)
    return rid, tracker


def _phase_bg_resolve_agent_from_model(
    agent: str | None,
    model: str | None,
    provider: str | None,
    rid: str,
) -> tuple[str | None, dict[str, Any] | None]:
    """Resolve ``agent`` from a model alias or fail with the bg-shaped payload.

    Returns ``(agent, error_payload)``. Error payload uses ``session_id``
    + ``exit_code`` keys (not ``run_id``) to match ``bg_impl_core``'s
    contract; callers short-circuit by returning ``error_payload`` directly.
    """
    if agent is not None:
        return agent, None
    if model is None:
        return None, None
    agent_or_error, err_payload = _phase_resolve_agent_from_model(model, provider, rid)
    if err_payload is not None:
        # Re-shape error payload to bg's session_id contract.
        bg_err = dict(err_payload)
        bg_err["session_id"] = "failed"
        return None, bg_err
    return agent_or_error, None


def _phase_bg_evaluate_contract(
    contract_version: str | None,
    lane: str | None,
    rid: str,
) -> tuple[dict[str, Any] | None, str | None]:
    """Contract migration + ROB-010 downgrade prevention (WP-X1/V7).

    Returns ``(error_payload, requested_version)``. ``error_payload`` is
    non-None when the request must short-circuit; ``requested_version``
    is the version forwarded to the spawned subprocess.
    """
    from thegent.contracts.migration import MigrationController
    from thegent.contracts.registry import CONTRACT_SCHEMA_VERSION

    migrator = MigrationController()
    requested_version = contract_version or CONTRACT_SCHEMA_VERSION
    mig_res = migrator.evaluate_version("csm", requested_version)

    if not mig_res["allowed"]:
        return (
            {
                "error": f"Contract version rejected: {mig_res['reason']}",
                "exit_code": 1,
                "session_id": "failed",
                "run_id": rid,
            },
            requested_version,
        )

    if lane == "critical" and requested_version != CONTRACT_SCHEMA_VERSION:
        from thegent.contracts.registry import get_registry

        registry = get_registry()
        if not registry.is_compatible(requested_version, CONTRACT_SCHEMA_VERSION):
            return (
                {
                    "error": (
                        f"ROB-010: Contract version downgrade prevented in critical lane. "
                        f"Requested: {requested_version}, Current: {CONTRACT_SCHEMA_VERSION}"
                    ),
                    "exit_code": 1,
                    "session_id": "failed",
                    "remediation": f"Use --contract-version {CONTRACT_SCHEMA_VERSION} or remove --lane critical",
                    "run_id": rid,
                },
                requested_version,
            )
    return None, requested_version


def _phase_bg_resolve_effective_timeout(
    settings: ThegentSettings,
    config_provider: "ConfigProvider | None",
    timeout: int,
    agent: str | None,
    tenant_id: str | None,
) -> int:
    """Effective timeout with ConfigProvider override + Claude floor (bg)."""
    _bg_config: dict[str, Any] | None = None
    if config_provider is not None:
        _bg_config = config_provider.resolve(
            tenant_id=tenant_id,
            request_overrides={"default_timeout": timeout},
        )
    effective_timeout = _bg_config.get("default_timeout", timeout) if _bg_config else timeout
    if agent == "claude":
        _min_claude = (
            _bg_config.get("default_timeout_claude", settings.default_timeout_claude)
            if _bg_config
            else settings.default_timeout_claude
        )
        try:
            effective_timeout = max(int(effective_timeout), int(_min_claude))
        except (TypeError, ValueError):
            _log.debug("Invalid claude timeout override %r; using existing", _min_claude)
    return int(effective_timeout)


def _phase_bg_idempotency_replay(
    registry: RunRegistry,
    idempotency_token: str | None,
) -> dict[str, Any] | None:
    """Idempotency token replay detection with bg-shaped payload.

    Bloom-filter fast path (WP-1003 / WP-1008 / OPT-019) + full lookup
    fallback. Returns ``None`` when the token is missing or no replay
    exists; otherwise returns the bg-shaped replay payload (with
    ``session_id`` / ``run_id`` keys, no stdout/stderr).
    """
    if not idempotency_token:
        return None
    session_id_from_token = f"run_{hashlib.sha256(idempotency_token.encode()).hexdigest()[:8]}"
    if not registry.session_exists(session_id_from_token):
        return None
    existing = registry.find_by_token(idempotency_token)
    if existing and existing.get("status") == "completed":
        _log.info("Replay detected for token %s in bg; skipping.", idempotency_token)
        return {
            "session_id": existing.get("correlation_id") or "replayed",
            "run_id": existing.get("run_id"),
            "replayed": True,
        }
    return None


def _phase_bg_init_services(
    settings: ThegentSettings,
    registry: RunRegistry,
    owner: str | None,
    cwd: Path,
) -> tuple[Any, str, int, dict[str, Any] | None]:
    """Init per-run services bundle + trust boundary check (WP-3007).

    Returns ``(services, effective_owner, escalation_sla_minutes, err)``.
    ``services`` is the bg-shaped bundle (no MAIF — bg only registers
    lifecycle events). ``err`` is non-None when the trust boundary
    rejects the environment transition.
    """
    from thegent.execution import (
        Auditor,
        OverrideRegistry,
        PolicyEngine,
        TrustBoundaryValidator,
    )

    services = {
        "circuit_breaker": CircuitBreakerRegistry(settings.session_dir),
        "trust_boundary": TrustBoundaryValidator(settings.session_dir),
        "override_registry": OverrideRegistry(settings.session_dir),
        "policy_engine": PolicyEngine(settings),
        "auditor": Auditor(registry.registry_path),
    }
    effective_owner = owner or _default_owner_tag(cwd)
    escalation_sla_minutes = 30
    try:
        escalation_sla_minutes = int(settings.escalation_sla_minutes)
    except (TypeError, ValueError):
        escalation_sla_minutes = 30

    last_env = services["trust_boundary"].get_last_environment()
    allowed, boundary_reason = services["trust_boundary"].validate_transition(last_env, settings.environment.lower())
    if not allowed:
        return (
            services,
            effective_owner,
            escalation_sla_minutes,
            {
                "error": f"Trust boundary violation: {boundary_reason}",
                "exit_code": 1,
                "session_id": "failed",
            },
        )
    return services, effective_owner, escalation_sla_minutes, None


def _phase_bg_evaluate_policy(
    *,
    policy_engine: Any,
    override_registry: Any,
    auditor: Any,
    run_meta: RunMeta,
    registry: RunRegistry,
    effective_owner: str,
    override_reason: str | None,
) -> tuple[str, str]:
    """Policy + override-TTL + audit signature (WP-3001 / WP-3003 / G-GP-05).

    Applies the override-TTL semantics for background runs (cached-only;
    no fresh-record path because override_reason handling lives in the
    CLI entry). Signs the run_meta after the policy decision so the
    audit trail is intact.
    """
    pol_res, pol_reason = policy_engine.evaluate(run_meta, registry=registry)
    if pol_res == "deny" and override_registry.has_unexpired(effective_owner):
        _log.info("Policy override (cached, within TTL) for background run")
        pol_res = "allow"
        pol_reason = f"Overridden (cached): {pol_reason}"
    run_meta.policy_result = pol_res
    run_meta.policy_reason = pol_reason
    run_meta.signature = auditor.sign_run(run_meta)
    return pol_res, pol_reason


def _bg_ambig_cwd_error(run_id: str | None) -> dict[str, Any]:
    """Return canonical 'ambiguous cwd' error dict."""
    return {
        "error": "Ambiguous cwd detected. Run inside a project directory or pass --cd with a valid project path.",
        "exit_code": 1,
        "session_id": "failed",
        "run_id": run_id or f"bg_err_{uuid.uuid4().hex[:8]}",
    }


def _bg_handle_policy_result(
    pol_res: str,
    run_meta: RunMeta,
    escalation_sla_minutes: int,
    pol_reason: str,
    registry: RunRegistry,
    settings: ThegentSettings,
) -> dict[str, Any] | None:
    """Handle deny/pause policy outcomes; return error payload or None to continue."""
    if pol_res == "deny":
        return _phase_register_policy_denial(run_meta, escalation_sla_minutes, pol_reason, registry)
    if pol_res == "pause":
        return _phase_register_hitl_pause(
            settings,
            run_meta,
            registry,
            escalation_sla_minutes,
            pol_reason,
            suffix=" (bg)",
        )
    return None


def _phase_bg_remote_dispatch(
    *,
    remote: str | None,
    cwd: Path,
    run_meta: RunMeta,
) -> dict[str, Any] | None:
    """Remote compute offload (WP-RC-01). Returns bg payload or ``None``.

    ``None`` means: not a remote dispatch (caller continues local spawn).
    Any non-None payload is the bg-shaped return value the orchestrator
    should propagate to the CLI immediately (success or error).
    """
    if not remote:
        return None
    import sys
    import tempfile

    from thegent.research.remote_compute import RemoteComputeClient

    client = RemoteComputeClient(remote)
    remote_path = Path(tempfile.gettempdir()) / f"thegent-run-{run_meta.run_id}"
    _log.info("Offloading background execution to remote host: %s", remote)
    if not client.transfer_files(cwd, str(remote_path)):
        return {
            "error": f"Failed to sync project to remote host: {remote}",
            "exit_code": 1,
        }
    remote_args = [a for a in sys.argv if not a.startswith("--remote")]
    remote_command = " ".join(f'"{a}"' if " " in a else a for a in remote_args)
    _log.info("Running remote background command in %s", remote_path)
    bg_remote_command = f"nohup {remote_command} > {remote_path}/remote_bg.log 2>&1 & echo $!"
    remote_res = client.execute_remote(bg_remote_command, cwd=Path(remote_path))
    if remote_res.get("status") == "success":
        remote_pid = remote_res.get("stdout", "").strip()
        return {
            "session_id": f"remote-{remote_pid}",
            "run_id": run_meta.run_id,
            "remote_host": remote,
            "remote_path": remote_path,
            "status": "started_remote",
        }
    return remote_res


def _phase_bg_build_command(
    *,
    settings: ThegentSettings,
    agent: str | None,
    model: str | None,
    effective_prompt: str,
    cwd: Path,
    effective_timeout: int,
    lane: str | None,
    full: bool,
    routing: str | None,
    failover: bool,
    requested_version: str | None,
    domain: str | None,
    task_id: str | None,
    idempotency_token: str | None,
    speculative: bool,
    effective_run_id: str,
    session_id: str,
    p: dict[str, Path],
) -> list[str]:
    """Build the Thegent 3.0 ``run agent`` command (with optional holdpty).

    Returns the final argv list. The ``holdpty`` wrapper is prepended in
    place when ``settings.use_holdpty`` is True; the canonical sock path
    is derived from the ``in`` session path.
    """
    cmd: list[str] = [
        sys.executable,
        "-m",
        "thegent.main",
        "run",
        "agent",
        effective_prompt,
    ]
    cmd.extend(
        [
            "--cd",
            str(cwd),
            "--timeout",
            str(effective_timeout),
            "--lane",
            lane or "standard",
        ]
    )
    if agent:
        cmd.extend(["--agent", agent])
    if full:
        cmd.append("--full")
    if routing:
        cmd.extend(["--routing", routing])
    if failover:
        cmd.append("--failover")
    if model:
        cmd.extend(["--model", model])
    if requested_version:
        cmd.extend(["--contract-version", requested_version])
    if domain:
        cmd.extend(["--domain", domain])
    if task_id:
        cmd.extend(["--task-id", task_id])
    if idempotency_token:
        cmd.extend(["--idempotency-token", idempotency_token])
    if speculative:
        cmd.append("--speculative")
    cmd.extend(["--run-id", effective_run_id])
    if settings.use_holdpty is True:
        in_path = p.get("in")
        if in_path is None:
            raise RuntimeError("Session paths missing 'in' key")
        socket_path = in_path.with_suffix(".sock")
        holdpty_cmd = [
            sys.executable,
            "-m",
            "thegent.main",
            "holdpty",
            "--socket",
            str(socket_path),
            "--session-id",
            session_id,
            "--",
        ]
        cmd = holdpty_cmd + cmd
    return cmd


def _phase_bg_apply_sandbox(
    *,
    settings: ThegentSettings,
    cmd: list[str],
    cwd: Path,
) -> list[str]:
    """Apply macOS sandbox level to the agent command (THGENT_SANDBOX_LEVEL).

    Defensive: when ``MacOSSandbox.from_env`` / ``level_from_settings`` are
    unavailable (CI / bare-metal), fall back to a no-op BASIC instance so
    bg_impl keeps working. Returns the (possibly-mutated) ``cmd``.
    """
    from thegent.security.macos_sandbox import MacOSSandbox, SandboxLevel

    _sandbox = MacOSSandbox.from_env() if hasattr(MacOSSandbox, "from_env") else MacOSSandbox(SandboxLevel.BASIC)
    _sandbox_level = (
        MacOSSandbox.level_from_settings() if hasattr(MacOSSandbox, "level_from_settings") else _sandbox.level
    )
    if _sandbox_level not in (SandboxLevel.NONE, SandboxLevel.FULL):
        apply_to_command = getattr(_sandbox, "apply_to_command", None)
        if callable(apply_to_command):
            cmd = apply_to_command(cmd, _sandbox_level, project_root=cwd)
        _log.debug("macOS sandbox level %r applied to agent command", _sandbox_level.value)
    return cmd


def _phase_bg_filter_env(
    *,
    settings: ThegentSettings,
    owner_tag: str,
    session_id: str,
    p: dict[str, Path],
) -> dict[str, str]:
    """Build the subprocess env: allowlist filter + THGENT_* injection (G-GP-08)."""
    if settings.sandbox_env_filter:
        allowlist = settings.sandbox_env_allowlist
        env = {k: v for k, v in os.environ.items() if k in allowlist or k.startswith("THGENT_")}
    else:
        env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env.update(
        {
            "THGENT_SESSION_ID": session_id,
            "THGENT_SESSION_META_PATH": str(p["meta"]),
            "THGENT_SESSION_RC_PATH": str(p["rc"]),
            "THGENT_SESSION_STDOUT_PATH": str(p["stdout"]),
            "THGENT_SESSION_STDERR_PATH": str(p["stderr"]),
            "THGENT_OWNER_TAG": owner_tag,
        }
    )
    return env


def _phase_bg_open_fifo(
    *,
    settings: ThegentSettings,
    p: dict[str, Path],
) -> Any:
    """Open the FIFO stdin handle or fall back to ``subprocess.DEVNULL``.

    Non-blocking open on POSIX so bg_impl never hangs waiting for a
    writer. On any failure (platform / permission / already-exists) the
    helper returns ``subprocess.DEVNULL`` after logging at warning level.
    """
    stdin_handle = subprocess.DEVNULL
    if settings.use_fifo is not True:
        return stdin_handle
    try:
        if platform.system() == "Windows":
            _log.warning("FIFO not supported on Windows; falling back to DEVNULL.")
            return stdin_handle
        in_path = p.get("in")
        if in_path is None:
            raise RuntimeError("Session paths missing 'in' key")
        if not in_path.exists():
            os.mkfifo(str(in_path))
        return os.open(str(in_path), os.O_RDONLY | os.O_NONBLOCK)
    except Exception as exc:
        _log.warning("Failed to create FIFO: %s", exc)
        return stdin_handle


def _phase_bg_spawn(
    *,
    cmd: list[str],
    cwd: Path,
    env: dict[str, str],
    stdin_handle: Any,
    stdout_handle: Any,
    stderr_handle: Any,
) -> Any:
    """Spawn the agent subprocess with EAGAIN retry + Popen fallback.

    Honours the AUDIT-N+14 contract: prefer the canonical
    ``_spawn_with_eagain_retry`` from the impl namespace; fall back to
    ``subprocess.Popen`` (resolved through ``_impl_lazy.subprocess`` so
    ``@patch("thegent.cli.commands.impl.subprocess.Popen")`` still wins)
    when the canonical helper is unavailable (test environments).

    Stream handles are always closed before this returns so the parent
    process cannot deadlock on a full pipe; FIFO FDs are intentionally
    left open for child inheritance.
    """
    try:
        spawn_with_eagain_retry = _impl_lazy._spawn_with_eagain_retry
        if spawn_with_eagain_retry is None:
            raise RuntimeError("spawn helper is unavailable")
        proc = spawn_with_eagain_retry(
            cmd,
            cwd=str(cwd),
            env=env,
            stdin=stdin_handle,
            stdout=stdout_handle,
            stderr=stderr_handle,
        )
    except RuntimeError:
        # AUDIT-N+14 fallback — honour impl.subprocess.Popen patches.
        _impl_subprocess = _impl_lazy.subprocess
        popen = getattr(_impl_subprocess, "Popen", None)
        if popen is None:
            raise
        proc = popen(
            cmd,
            cwd=str(cwd),
            env=env,
            stdin=stdin_handle,
            stdout=stdout_handle,
            stderr=stderr_handle,
        )
    finally:
        try:
            stdout_handle.close()
        except Exception as exc:
            _log.debug("stdout_handle close failed: %s", exc)
        try:
            stderr_handle.close()
        except Exception as exc:
            _log.debug("stderr_handle close failed: %s", exc)
    return proc


def _phase_bg_persist_meta(
    *,
    p: dict[str, Path],
    session_id: str,
    agent: str | None,
    owner_tag: str,
    cwd: Path,
    prompt: str,
    mode: str,
    effective_timeout: int,
    cmd: list[str],
    proc: Any,
    include_contract: bool,
    route_contract: dict[str, Any] | None,
    route_request: dict[str, str] | None,
    continue_from: str | None,
) -> None:
    """Build + persist the per-session meta JSON (WP-?/session-meta)."""
    meta: dict[str, Any] = {
        "version": 1,
        "session_id": session_id,
        "agent": agent,
        "owner": owner_tag,
        "cwd": str(cwd),
        "prompt": prompt,
        "mode": mode,
        "timeout_hint_s": effective_timeout,
        "host": socket.gethostname(),
        "launcher_pid": os.getpid(),
        "launcher_ppid": os.getppid(),
        "launcher_uid": os.getuid(),
        "status": "running",
        "started_at_utc": datetime.now(UTC).isoformat(),
        "pid": proc.pid,
        "command": cmd,
        "paths": {k: str(v) for k, v in p.items()},
    }
    if include_contract:
        if route_contract is not None:
            meta["route_contract"] = route_contract
        if route_request is not None:
            meta["route_request"] = route_request
    if continue_from:
        meta["continued_from"] = continue_from.split(",")[0].strip()
    _save_session_meta(p["meta"], meta)


def bg_impl_core(
    *,
    agent: str | None,
    prompt: str,
    cd: Path | None,
    mode: str,
    timeout: int,
    full: bool,
    droid: str | None = None,
    model: str | None = None,
    provider: str | None = None,
    owner: str | None = None,
    continue_from: str | None = None,
    continuation_include_stderr: bool = False,
    include_contract: bool = False,
    route_contract: dict[str, Any] | None = None,
    route_request: dict[str, str] | None = None,
    routing: str | None = None,
    failover: bool = False,
    run_id: str | None = None,
    lane: str | None = None,
    confidence: float | None = None,
    contract_version: str | None = None,
    domain: str | None = None,
    idempotency_token: str | None = None,
    speculative: bool = False,
    arbitration: str | None = None,
    override_reason: str | None = None,
    debug: bool = False,
    task_id: str | None = None,
    remote: str | None = None,
    image_paths: list[str] | None = None,
    config_provider: "ConfigProvider | None" = None,
    tenant_id: str | None = None,
    impl_ns: Any | None = None,
) -> dict[str, Any]:
    """
    Start a background run. Returns dict with keys: session_id, log_path, owner.

    Thin composer (WL141): every sub-phase is delegated to a ``_phase_bg_*``
    helper so this orchestrator stays CC ≤ 30, body ≤ 280 lines. The
    helper section above owns the actual logic; this body only sequences
    the phase calls and propagates short-circuit payloads.
    """
    if impl_ns is None:
        raise ValueError("impl_ns is required")
    _bind_impl_namespace(impl_ns)

    settings = ThegentSettings()
    rid, _tracker = _phase_bg_init_tracker(settings, run_id)
    agent, model, route_contract, route_request = _apply_pareto_routing_local(
        agent, model, routing, include_contract, route_contract, route_request
    )
    agent, model, route_contract, route_request = _phase_auto_route(
        settings, agent, model, prompt, include_contract, route_contract, route_request
    )
    agent_or_error, err = _phase_bg_resolve_agent_from_model(agent, model, provider, rid)
    if err is not None:
        return err
    agent = resolve_agent(agent_or_error) or "unknown"

    contract_err, requested_version = _phase_bg_evaluate_contract(contract_version, lane, rid)
    if contract_err is not None:
        return contract_err

    cwd = _resolve_cwd(cd)
    if cwd is None:
        return _bg_ambig_cwd_error(run_id)

    effective_timeout = _phase_bg_resolve_effective_timeout(settings, config_provider, timeout, agent, tenant_id)
    full = full or True

    effective_prompt = prompt
    if continue_from:
        effective_prompt = _build_continuation_prompt(
            settings, continue_from, prompt, include_stderr=continuation_include_stderr
        )

    owner_tag = owner or _default_owner_tag(cwd, include_process_id=True)
    base = _session_dir(settings, owner_tag)
    session_id = _new_session_id(agent=agent, owner=owner_tag)
    p = _rsh_impl.session_paths(base=base, session_id=session_id)

    registry = RunRegistry(settings.session_dir)
    replay = _phase_bg_idempotency_replay(registry, idempotency_token)
    if replay is not None:
        return replay

    effective_run_id = run_id or f"run_{uuid.uuid4().hex[:8]}"
    if speculative:
        _log.info("Speculative execution active in background.")

    services, effective_owner, escalation_sla_minutes, tb_err = _phase_bg_init_services(settings, registry, owner, cwd)
    if tb_err is not None:
        return tb_err

    resolved_domain_tag = str(domain) if domain else str(settings.default_domain_tag)
    run_meta = RunMeta(
        run_id=effective_run_id,
        agent=agent or "",
        model=model or "",
        prompt=prompt,
        cwd=str(cwd),
        owner=owner_tag,
        domain_tag=resolved_domain_tag,
        lane=lane or "standard",
        confidence=confidence if confidence is not None else 1.0,
        idempotency_token=idempotency_token or "",
    )

    pol_res, pol_reason = _phase_bg_evaluate_policy(
        policy_engine=services["policy_engine"],
        override_registry=services["override_registry"],
        auditor=services["auditor"],
        run_meta=run_meta,
        registry=registry,
        effective_owner=effective_owner,
        override_reason=override_reason,
    )

    policy_payload = _bg_handle_policy_result(pol_res, run_meta, escalation_sla_minutes, pol_reason, registry, settings)
    if policy_payload is not None:
        return policy_payload

    registry.register_start(run_meta)

    remote_payload = _phase_bg_remote_dispatch(remote=remote, cwd=cwd, run_meta=run_meta)
    if remote_payload is not None:
        return remote_payload

    cmd = _phase_bg_build_command(
        settings=settings,
        agent=agent,
        model=model,
        effective_prompt=effective_prompt,
        cwd=cwd,
        effective_timeout=effective_timeout,
        lane=lane,
        full=full,
        routing=routing,
        failover=failover,
        requested_version=requested_version,
        domain=domain,
        task_id=task_id,
        idempotency_token=idempotency_token,
        speculative=speculative,
        effective_run_id=effective_run_id,
        session_id=session_id,
        p=p,
    )
    cmd = _phase_bg_apply_sandbox(settings=settings, cmd=cmd, cwd=cwd)

    stdout_handle = p["stdout"].open("wb")
    stderr_handle = p["stderr"].open("wb")
    env = _phase_bg_filter_env(settings=settings, owner_tag=owner_tag, session_id=session_id, p=p)
    stdin_handle = _phase_bg_open_fifo(settings=settings, p=p)

    proc = _phase_bg_spawn(
        cmd=cmd,
        cwd=cwd,
        env=env,
        stdin_handle=stdin_handle,
        stdout_handle=stdout_handle,
        stderr_handle=stderr_handle,
    )

    _phase_bg_persist_meta(
        p=p,
        session_id=session_id,
        agent=agent,
        owner_tag=owner_tag,
        cwd=cwd,
        prompt=prompt,
        mode=mode,
        effective_timeout=effective_timeout,
        cmd=cmd,
        proc=proc,
        include_contract=include_contract,
        route_contract=route_contract,
        route_request=route_request,
        continue_from=continue_from,
    )

    return {
        "session_id": session_id,
        "log_path": str(p["stdout"]),
        "owner": owner_tag,
    }
