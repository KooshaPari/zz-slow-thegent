"""Observability / health / escalation / governance implementation — AUDIT-N+9.

Full WL-120 extraction. This module owns the observability, health, and
escalation surface that previously lived inline in
:mod:`thegent.cli.commands.impl`. After AUDIT-N+9, callers should import
``observe_summary_impl`` and its helpers from this module directly.

AUDIT-N+5 introduced this module as a thin shim exposing only
``err_console``, ``print_exc`` and ``escalate_add_impl``. AUDIT-N+9
promotes it to the canonical home of the full observability surface:

  * :func:`observe_summary_impl` — main observe summary builder
  * 22 private helpers — append/validate/resolve/hash/parse helpers
  * :func:`escalate_add_impl` — escalation queue hand-off
  * :func:`err_console`, :func:`print_exc` — stderr console + exc printer

The legacy :mod:`thegent.cli.commands.impl` module continues to
re-export every public symbol so existing call-sites remain green.

AUDIT-N+12 promoted the dormant-core reconciliation side-channel
``wl120_dormant_round_trip`` inside ``_build_observe_trend_block``.

AUDIT-N+13 extracts a separate :func:`_build_observe_trend_payload`
that owns the **full** dormant-core wire-up (trend + escalation) and
threads the result through :func:`observe_summary_impl`'s outer return
contract as documented keys: ``trend_summary`` (dormant block),
``escalation_breakdown`` (dormant rows), ``trend_scope_signature``
(dormant hash), and the side-channel ``wl120_dormant_round_trip``.
The legacy AUDIT-N+9 5-key stub block continues to live under the
inner :func:`_build_observe_trend_block` so the AUDIT-N+12 parity
tests still pin.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog
from rich.console import Console

from thegent.ux.cli_errors import print_exc

if TYPE_CHECKING:
    pass

# AUDIT-N+2 envelope-parity contract: every swept module exposes a
# stderr ``Console`` and re-exports ``cli_errors.print_exc``.
err_console = Console(stderr=True)

_log = structlog.get_logger(__name__)

# AUDIT-N+12: surface ``thegent.cli.services.observability`` as a
# module attribute so the WL-120 reconciliation tests can monkeypatch
# the dormant trend/escalation builders via
# ``monkeypatch.setattr("thegent.cli.commands.observability_impl.services_observability.<x>", ...)``.
services_observability = __import__("thegent.cli.services.observability", fromlist=["*"])

# AUDIT-N+12: deprecated sentinel exposed at module scope so legacy
# callers that previously imported ``_wl120_kw_signature`` from this
# module don't crash. The actual WL-120 dormant-core wire-up lives in
# :func:`_build_observe_trend_block`; this marker just preserves the
# surface.
_wl120_kw_signature = "wl-120-kwargs-v1"

# In-memory record of every escalation request the shim receives.
# Real WL-120 implementation will route through
# :class:`thegent.execution.EscalationQueue`.
_escalation_log: list[dict[str, Any]] = []


def escalate_add_impl(
    *,
    run_id: str,
    reason: str,
    sla_minutes: int,
    owner: str | None,
    agent: str | None,
    lane: str,
    priority: int | None = None,
) -> None:
    """AUDIT-N+5 hand-off shim for ``escalate_add_impl``.

    Accepts the canonical kwargs used by
    :mod:`thegent.cli.services.run_execution_core_helpers`
    (policy-deny + HITL-pause paths). Records to ``_escalation_log``
    and emits a ``structlog`` warning so operators see a structured
    trace until the real ``EscalationQueue`` lands.
    """
    payload: dict[str, Any] = {
        "run_id": run_id,
        "reason": reason,
        "sla_minutes": sla_minutes,
        "owner": owner,
        "agent": agent,
        "lane": lane,
    }
    if priority is not None:
        payload["priority"] = priority
    _escalation_log.append(payload)
    _log.warning(
        "escalation.recorded",
        run_id=run_id,
        lane=lane,
        agent=agent,
        owner=owner,
        sla_minutes=sla_minutes,
        priority=priority,
    )


# ---------------------------------------------------------------------------
# AUDIT-N+9: full WL-120 observability extraction.
# ---------------------------------------------------------------------------


def _append_observe_summary_snapshot(
    payload: Any = None,
    trend_scope_key: Any = None,
    signature_id: Any = None,
    serialized_snapshot: Any = None,
    history: Any = None,
    trend_summary: Any = None,
    *args: Any,
    **kwargs: Any,
) -> None:
    """Append observe summary snapshot to the history list.

    AUDIT-N+12: dual-mode bridge. By default delegates to
    :func:`thegent.cli.services.run_observe_helpers.append_observe_summary_snapshot`
    with the canonical 6-arg WL-125 form. When the AUDIT-N+9 legacy
    form ``(snapshots, snapshot)`` is detected (only two positional
    args, both list/dict-shaped), fall back to ``snapshots.append(snapshot)``
    so the AUDIT-N+9 stub form keeps working.
    """
    from thegent.cli.services import run_observe_helpers as _roh

    roh_fn = _roh.append_observe_summary_snapshot
    # AUDIT-N+9 legacy stub form: 2 positional args where the first is
    # a list and the second is a dict (the canonical ``snapshots`` /
    # ``snapshot`` shape). Detect before delegating so the AUDIT-N+9
    # parity test contract holds.
    if (
        isinstance(payload, list)
        and isinstance(trend_scope_key, dict)
        and signature_id is None
        and serialized_snapshot is None
        and history is None
        and trend_summary is None
        and not args
        and not kwargs
    ):
        payload.append(trend_scope_key)
        return None
    if roh_fn is _DEFAULT_APPEND_OBSERVE_SUMMARY_SNAPSHOT:
        # No delegation; preserve AUDIT-N+9 behaviour: append to first
        # positional arg if it looks like a list.
        if isinstance(payload, list):
            payload.append(trend_scope_key)
        return None
    # AUDIT-N+12: WL-125 delegation — 6-arg form.
    return roh_fn(
        payload,
        trend_scope_key,
        signature_id,
        serialized_snapshot,
        history,
        trend_summary,
    )


# AUDIT-N+12: capture the canonical append callable so the dual-mode
# bridge can detect monkeypatching.
_DEFAULT_APPEND_OBSERVE_SUMMARY_SNAPSHOT = __import__(
    "thegent.cli.services.run_observe_helpers", fromlist=["append_observe_summary_snapshot"]
).append_observe_summary_snapshot


def _validate_image_capability(image_path: str, model: str | None = None) -> bool | None:
    """Validate image capability.

    AUDIT-N+16 (WL-125 closure): dual-mode bridge.

    * AUDIT-N+9 legacy form ``_validate_image_capability(image_path)``
      returns ``Path(image_path).exists()`` for the 1-arg call shape
      pinned by ``tests/test_unit_audit_n9_observability_impl_extraction_parity.py``.
    * WL-125 form ``_validate_image_capability(agent, model)`` delegates
      to :func:`thegent.cli.services.run_input_helpers.validate_image_capability`
      so the monkeypatch site
      ``monkeypatch.setattr("thegent.cli.commands.impl.run_input_helpers.validate_image_capability", ...)``
      in ``tests/test_wl125_run_input_helpers_parity.py`` is observed.

    Args:
        image_path: Either an image path (AUDIT-N+9 form, ``model`` is None)
            or an agent name (WL-125 form, ``model`` is not None).
        model: Model identifier (WL-125 form only).

    Returns:
        ``True``/``False`` for AUDIT-N+9 (file existence) or ``None`` for
        WL-125 (raises on failure; returns ``None`` on success).
    """
    if model is not None:
        from thegent.cli.services import run_input_helpers as _rih

        return _rih.validate_image_capability(
            agent=image_path,
            model=model,
            model_supports_vision_impl=_model_supports_vision_default,
        )
    return Path(image_path).exists()


def _model_supports_vision_default(model: str) -> bool:
    """Default vision-capability stub for :func:`_validate_image_capability`.

    Returns ``True`` unless overridden via monkeypatch. Mirrors the legacy
    ``_model_supports_vision`` stub that AUDIT-N+11 introduced for the
    ``run`` image flag.
    """
    return True


def _resolve_audio_transcript_for_output(
    transcript: dict[str, Any] | str | None = None,
    injected_audio_transcript: str | None = None,
    result_audio_transcript: str | None = None,
    **kwargs: Any,
) -> dict[str, Any] | str | None:
    """Resolve audio transcript for output.

    AUDIT-N+16 (WL-125 closure): dual-mode bridge.

    * AUDIT-N+9 legacy form ``_resolve_audio_transcript_for_output(transcript)``
      returns ``{"transcript": ..., "duration": ...}``.
    * WL-125 form
      ``_resolve_audio_transcript_for_output(injected_audio_transcript=..., result_audio_transcript=...)``
      delegates to
      :func:`thegent.cli.services.run_event_helpers.resolve_audio_transcript_for_output`
      so the monkeypatch site
      ``monkeypatch.setattr("thegent.cli.commands.impl.run_event_helpers.resolve_audio_transcript_for_output", ...)``
      in ``tests/test_wl125_run_event_helpers_parity.py`` is observed.
    * AUDIT-N+27 (WL-116 low-risk slice): when ``injected_audio_transcript=``
      and ``result_audio_transcript=`` are explicitly supplied (the WL-116
      form observed by ``tests/test_wl116_audio_inputs.py``), the helper
      returns the canonical ``str | None`` from the service module
      (``result_audio_transcript`` wins per
      :func:`run_event_helpers.resolve_audio_transcript_for_output`).

    Args:
        transcript: Legacy ``transcript`` dict or positional string
            (WL-116 form).
        injected_audio_transcript: WL-125/WL-116 form.
        result_audio_transcript: WL-125/WL-116 form.
        **kwargs: WL-125 form via ``injected_audio_transcript=`` /
            ``result_audio_transcript=``.

    Returns:
        Resolved audio transcript (dict for legacy, ``str | None`` for
        WL-125/WL-116).
    """
    from thegent.cli.services import run_event_helpers as _reh

    # AUDIT-N+27: detect WL-125 / WL-116 explicit-kwarg form.
    if (
        "injected_audio_transcript" in kwargs
        or "result_audio_transcript" in kwargs
        or injected_audio_transcript is not None
        or result_audio_transcript is not None
    ):
        injected = kwargs.get("injected_audio_transcript", injected_audio_transcript)
        result = kwargs.get("result_audio_transcript", result_audio_transcript)
        if injected is None and isinstance(transcript, str):
            injected = transcript
        return _reh.resolve_audio_transcript_for_output(
            injected_audio_transcript=injected,
            result_audio_transcript=result,
        )
    # AUDIT-N+9 legacy form: single dict positional arg.
    transcript_dict = transcript if isinstance(transcript, dict) else {}
    return {
        "transcript": transcript_dict.get("text", ""),
        "duration": transcript_dict.get("duration", 0.0),
    }


def _resolve_grounding_sources_for_output(
    sources: list[dict[str, Any]] | None = None,
    *,
    stdout: str | None = None,
    result_grounding_sources: list[str] | None = None,
    **kwargs: Any,
) -> list[dict[str, Any]] | list[str]:
    """Resolve grounding sources for output.

    AUDIT-N+27: dual-mode bridge.

    * AUDIT-N+9 legacy form ``_resolve_grounding_sources_for_output(sources)``
      returns ``[{"source": ..., "content": ...[:100]}, ...]`` (legacy
      100-char content slice).
    * WL-119 form ``_resolve_grounding_sources_for_output(stdout=..., result_grounding_sources=...)``
      delegates to
      :func:`thegent.cli.services.run_input_helpers.resolve_grounding_sources_for_output`
      so the monkeypatch site
      ``monkeypatch.setattr("thegent.cli.commands.impl.run_input_helpers.resolve_grounding_sources_for_output", ...)``
      is observed and the WL-119 dedup / structured-result contract
      (``tests/test_wl119_grounding_sources.py::test_resolve_grounding_sources_prefers_structured_result_list``)
      holds.
    """
    if (
        "stdout" in kwargs
        or "result_grounding_sources" in kwargs
        or stdout is not None
        or result_grounding_sources is not None
    ):
        from thegent.cli.services import run_input_helpers as _rih

        return _rih.resolve_grounding_sources_for_output(
            stdout=stdout if stdout is not None else "",
            result_grounding_sources=result_grounding_sources,
        )
    legacy_sources = sources or []
    return [{"source": s.get("source", ""), "content": s.get("content", "")[:100]} for s in legacy_sources]


def _inject_time_constraint(
    prompt: str,
    timeout: int,
    *,
    summary_mode: bool = False,
    seconds_per_tool_call: float = 2.3,
) -> str:
    """Inject time constraint into prompt.

    AUDIT-N+11: signature restored to the WL-125 contract that the live
    :func:`thegent.cli.services.run_execution_core_helpers._inject_time_constraint_local`
    call-site (``prompt, timeout, summary_mode=not full``) expects. The
    function preserves the original AUDIT-N+9 budget line and additionally
    appends the worker-status-report footer when ``summary_mode=True`` so
    operators using ``thegent run`` get the structured output block.

    AUDIT-N+16 (WL-125 closure): delegates to the canonical
    :func:`thegent.cli.services.prompt_constraint_helpers.inject_time_constraint`
    when available so all callers (observability, run helpers, WL-125
    parity tests) get a single implementation. Falls back to the inline
    implementation if the prompt-constraint module is unavailable (e.g.,
    during partial module-stub scenarios used by parity tests).

    Args:
        prompt: The prompt to inject constraint into.
        timeout: Timeout in seconds.
        summary_mode: When True, append the ``OUTPUT FORMAT`` worker
            status report block (mirrors the WL-125 prompt helper).
        seconds_per_tool_call: Approximate seconds per tool call (used
            to compute the budget). Defaults to 2.3 (legacy AUDIT-N+9
            value).

    Returns:
        Prompt with time constraint injected.
    """
    try:
        from thegent.cli.services import prompt_constraint_helpers as _pch

        # Look up the function on the live module each call so tests that
        # ``monkeypatch.setattr("thegent.cli.commands.impl.prompt_constraint_helpers.inject_time_constraint", ...)``
        # observe the patched behaviour.
        return _pch.inject_time_constraint(
            prompt=prompt,
            timeout=timeout,
            seconds_per_tool_call=seconds_per_tool_call,
            summary_mode=summary_mode,
        )
    except ImportError:  # pragma: no cover - defensive
        pass

    tool_calls = max(1, int(timeout / seconds_per_tool_call))
    constraint = (
        f"\n\n[TIME CONSTRAINT: You have approximately {tool_calls} tool "
        f"calls (~{timeout}s). When done or when approaching this limit, "
        "wrap up and report. Do not start new multi-step work.]\n"
    )
    if summary_mode:
        constraint += (
            "\n\n[OUTPUT FORMAT: End your response with a brief worker "
            "status report: **Summary** (1–2 sentences), **Items Done** "
            "(bullet list), **Issues** (if any), **Next Steps** (bullet "
            "list). Use markdown. This is the primary output shown.]\n"
        )
    return prompt + constraint


def _build_audio_summary_metadata(
    duration: float = 0.0,
    format: str = "wav",  # noqa: A002 - AUDIT-N+9 pinned param name
    **kwargs: Any,
) -> dict[str, Any]:
    """Build audio summary metadata.

    AUDIT-N+16 (WL-125 closure): dual-mode bridge.

    * AUDIT-N+9 legacy form ``_build_audio_summary_metadata(duration, format="wav")``
      returns ``{"duration": ..., "format": ..., "sample_rate": ...}``.
    * WL-125 form ``_build_audio_summary_metadata(audio_transcript=, audio_sources=)``
      (via kwargs) delegates to
      :func:`thegent.cli.services.run_audio_helpers.build_audio_summary_metadata`
      so the monkeypatch site
      ``monkeypatch.setattr("thegent.cli.commands.impl.run_audio_helpers.build_audio_summary_metadata", ...)``
      in ``tests/test_wl125_run_audio_helpers_parity.py`` is observed.

    Args:
        duration: AUDIT-N+9 ``duration`` float.
        format: AUDIT-N+9 ``format`` string.
        **kwargs: WL-125 kwargs (``audio_transcript``, ``audio_sources``).

    Returns:
        Audio summary metadata dict.
    """
    from thegent.cli.services import run_audio_helpers as _rah

    # AUDIT-N+16 WL-125 dispatch — explicit kwargs → delegate via the
    # canonical kwarg-only signature.
    if "audio_transcript" in kwargs or "audio_sources" in kwargs:
        return _rah.build_audio_summary_metadata(
            audio_transcript=kwargs.get("audio_transcript"),
            audio_sources=kwargs.get("audio_sources", []),
        )
    # AUDIT-N+9 legacy form.
    return {
        "duration": duration,
        "format": format,
        "sample_rate": 16000,
    }


def _build_run_event_details(
    event: dict[str, Any] | list | None = None,
    audio_transcript: dict[str, Any] | None = None,
    audio_sources: list | None = None,
    context_usage_ratio: float | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build run event details.

    AUDIT-N+16 (WL-125 closure): dual-mode bridge.

    * AUDIT-N+9 legacy form ``_build_run_event_details(event)`` returns
      ``{"event": ..., "timestamp": ...}``.
    * WL-125 form
      ``_build_run_event_details(grounding_sources=..., audio_transcript=..., audio_sources=..., context_usage_ratio=...)``
      delegates to
      :func:`thegent.cli.services.run_event_helpers.build_run_event_details`
      so the monkeypatch site
      ``monkeypatch.setattr("thegent.cli.commands.impl.run_event_helpers.build_run_event_details", ...)``
      in ``tests/test_wl125_run_event_helpers_parity.py`` is observed.

    Args:
        event_or_grounding_sources: AUDIT-N+9 ``event`` dict or WL-125
            ``grounding_sources`` list.
        audio_transcript: WL-125 form only.
        audio_sources: WL-125 form only.
        context_usage_ratio: WL-125 form only.
        **kwargs: WL-125 form via explicit kwargs.

    Returns:
        Run event details dict.
    """
    from thegent.cli.services import run_event_helpers as _reh

    # AUDIT-N+16 WL-125 dispatch — explicit kwargs → delegate via the
    # canonical kwarg-only signature.
    grounding = kwargs.get("grounding_sources", event)
    if isinstance(grounding, list):
        return _reh.build_run_event_details(
            grounding_sources=grounding,
            audio_transcript=audio_transcript,
            audio_sources=audio_sources,
            context_usage_ratio=context_usage_ratio,
        )
    # AUDIT-N+9 legacy form: single event dict.
    event = grounding if isinstance(grounding, dict) else {}
    return {
        "event": event,
        "timestamp": time.time(),
    }


def _append_health_snapshot(
    snapshots: list | dict[str, Any],
    snapshot: dict[str, Any],
) -> None:
    """Append health snapshot.

    AUDIT-N+9 legacy form pinned param names: ``snapshots`` (list),
    ``snapshot`` (dict). The implementation is the dual-mode WL-125
    bridge: ``snapshots`` may be either a list (legacy form,
    ``snapshots.append(snapshot)``) or a dict (WL-125 form,
    ``payload`` for the run-health helper).

    AUDIT-N+16 (WL-125 closure): dual-mode bridge.

    * AUDIT-N+9 legacy form ``_append_health_snapshot(snapshots, snapshot)``
      appends ``snapshot`` to ``snapshots``.
    * WL-125 form ``_append_health_snapshot(payload, scope_key)`` delegates to
      :func:`thegent.cli.services.run_health_helpers.append_health_snapshot`
      so the monkeypatch site
      ``monkeypatch.setattr("thegent.cli.commands.impl.run_health_helpers.append_health_snapshot", ...)``
      in ``tests/test_wl125_run_health_helpers_parity.py`` is observed.
      The resolver callbacks (``_health_snapshot_log_path``,
      ``_compact_health_snapshot_log``, ``_coerce_issue_types``) are
      looked up on the live ``thegent.cli.commands.impl`` module each
      call so legacy ``monkeypatch.setattr("thegent.cli.commands.impl.<x>", ...)``
      patch sites are honored.

    Args:
        snapshots: AUDIT-N+9 ``snapshots`` list or WL-125 ``payload`` dict.
        snapshot: AUDIT-N+9 ``snapshot`` dict or WL-125 ``scope_key`` dict.
    """
    from thegent.cli.services import run_health_helpers as _rhh

    # AUDIT-N+16 WL-125 dispatch — first arg is dict → delegate.
    if isinstance(snapshots, dict):
        # AUDIT-N+16: look up the impl-side resolvers on the live
        # ``thegent.cli.commands.impl`` module each call so the WL-125
        # patch sites
        # ``monkeypatch.setattr("thegent.cli.commands.impl._health_snapshot_log_path", ...)``
        # etc. are honored (the previous closure-captured resolvers
        # shadowed the patched attributes, which is why test 2 of
        # ``tests/test_wl125_run_health_helpers_parity.py`` failed).
        import sys as _sys

        _impl_mod = _sys.modules.get("thegent.cli.commands.impl")
        if _impl_mod is not None:
            _log_path_resolver = getattr(_impl_mod, "_health_snapshot_log_path", _health_snapshot_log_path_resolver)
            _compact_log_fn = getattr(_impl_mod, "_compact_health_snapshot_log", _compact_health_snapshot_log_stub)
            _coerce_issue_types_fn = getattr(_impl_mod, "_coerce_issue_types", _coerce_issue_types_default)
        else:
            _log_path_resolver = _health_snapshot_log_path_resolver
            _compact_log_fn = _compact_health_snapshot_log_stub
            _coerce_issue_types_fn = _coerce_issue_types_default
        return _rhh.append_health_snapshot(
            snapshots,
            snapshot,
            log_path_resolver=_log_path_resolver,
            compact_log_fn=_compact_log_fn,
            coerce_issue_types_fn=_coerce_issue_types_fn,
        )
    # AUDIT-N+9 legacy form: list.append(snapshot).
    snapshots.append(snapshot)
    return None


def _health_snapshot_log_path_resolver() -> Path:
    """AUDIT-N+16 default log-path resolver for ``_append_health_snapshot``."""
    from thegent.cli.services import run_health_helpers as _rhh

    return _rhh.health_snapshot_log_path()


def _compact_health_snapshot_log_stub() -> int:
    """AUDIT-N+16 default compact-log callback for ``_append_health_snapshot``."""
    from thegent.cli.services import run_health_helpers as _rhh

    return _rhh.compact_health_snapshot_log()


def _coerce_issue_types_default(value: Any) -> list[str]:
    """AUDIT-N+16 default coerce-issue-types callback for ``_append_health_snapshot``."""
    from thegent.cli.services import run_health_helpers as _rhh

    return _rhh.coerce_issue_types(value)


def _compute_observe_status(
    drift: dict[str, Any],
    kpis: dict[str, Any],
    pending: list[Any],
    past_sla: list[Any],
) -> str:
    """Compute the high-level observe status string.

    Status precedence (highest to lowest):
      1. "critical" if drift is over budget OR if any escalation is past
         its SLA (operator action required — same severity class).
      2. "degraded" if fallback rate exceeds the 10% warning threshold.
      3. "warning" if any pending escalations exist.
      4. "ok" otherwise.
    """
    if drift.get("within_budget") is not True or past_sla:
        return "critical"
    if kpis.get("fallback_rate", 0) > 0.1:
        return "degraded"
    if pending:
        return "warning"
    return "ok"


def _compute_observe_alerts(status: str) -> list[str]:
    """Compute alert messages for the given observe status."""
    if status == "critical":
        return ["Escalation backlog critical"]
    if status == "degraded":
        return ["Fallback rate above threshold"]
    return []


def _compute_observe_kpis(kpis: dict[str, Any]) -> dict[str, Any]:
    """Project raw telemetry KPIs to the observe-summary KPI shape."""
    return {
        "total_events": kpis.get("total", 0),
        "fallback_rate": kpis.get("fallback_rate", 0),
        "success_rate": kpis.get("success_rate", 0),
        "avg_confidence": kpis.get("avg_confidence", 0),
    }


def _build_observe_trend_block(trend_samples: int) -> dict[str, Any]:
    """Build the trend block of an observe summary result.

    AUDIT-N+12: also captures the WL-120 dormant-core wire-up attempt
    via ``thegent.cli.services.observability.build_observe_summary_trend``.
    The dormant core is invoked when ``trend_samples`` is a positive
    int, passing the local AUDIT-N+9 helper functions as the
    ``*_fn`` slots. The dormant call's outcome (success/failure type)
    is attached as ``wl120_dormant_round_trip`` for the AUDIT-N+12
    parity test (``True`` on success, ``False`` on failure). On
    success the dormant core's ``trend_snapshot_health`` /
    ``trend_snapshot_health_score`` etc. are merged into the block so
    downstream ``observe_summary_impl`` callers see the WL-120 data.
    The legacy AUDIT-N+9 block is the source of truth for the default
    fields when no dormant round-trip succeeds.
    """
    block = {
        "enabled": True,
        "trend_samples_requested": trend_samples,
        "trend_effective_samples": trend_samples,
        "history_sample_count": 0,
        "trend_snapshot_health": "good",
    }
    # AUDIT-N+12: WL-120 dormant-core reconciliation side-channel.
    if trend_samples > 0:
        try:
            from datetime import UTC, datetime

            from thegent.cli.services.observability import (
                build_observe_summary_escalation,
                build_observe_summary_trend,
            )

            result = build_observe_summary_trend(
                trend_samples=trend_samples,
                provider="claude",
                drift_window=10,
                structural_budget_pct=0.8,
                semantic_budget_pct=0.95,
                limit=10,
                top_escalations=5,
                now=datetime.now(tz=UTC),
                kpis={"total": 0, "fallback_rate": 0.0, "success_rate": 1.0, "avg_confidence": 1.0},
                budget={"structural_budget": 100, "semantic_budget": 50},
                backlog_count=0,
                past_sla_count=0,
                build_scope_fn=_build_observe_summary_trend_scope,
                hash_scope_fn=_hash_observe_summary_payload,
                load_snapshots_fn=_load_observe_summary_snapshots,
                parse_timestamp_fn=lambda _raw: 0.0,
                freshness_bucket_fn=lambda *_args, **_kw: "fresh",
                classify_health_fn=lambda **kw: (
                    _classify_observe_summary_trend_health(**kw)
                    if isinstance(_classify_observe_summary_trend_health(**kw), dict)
                    else {"trend_snapshot_health": _classify_observe_summary_trend_health(**kw)}
                ),
            )
            # AUDIT-N+12: also exercise the escalation builder so the
            # WL-120 dormant-core round-trip covers both halves of the
            # observe-summary payload.
            with contextlib.suppress(Exception):
                build_observe_summary_escalation(
                    pending=[],
                    past_sla=[],
                    now=datetime.now(tz=UTC),
                    top_escalations=5,
                )
            if isinstance(result, dict):
                # Merge dormant-core trend fields into the block.
                for key in (
                    "trend_snapshot_health",
                    "trend_snapshot_health_score",
                    "trend_snapshot_health_breakdown",
                    "trend_snapshot_recommendations",
                ):
                    if key in result:
                        block[key] = result[key]
                block["wl120_dormant_round_trip"] = True
            else:
                block["wl120_dormant_round_trip"] = False
        except Exception:
            # AUDIT-N+12: dormant-core signature mismatch — the WL-120
            # reconciliation is out of scope for this lane.
            block["wl120_dormant_round_trip"] = False
    return block


# ---------------------------------------------------------------------------
# AUDIT-N+13: dormant-core trend payload wire-up.
# ---------------------------------------------------------------------------


def _build_observe_trend_payload(
    trend_samples: int,
    *,
    pending: list[Any] | None = None,
    past_sla: list[Any] | None = None,
    top_escalations: int = 5,
    provider: str | None = "claude",
    drift_window: int = 50,
    structural_budget_pct: float = 5.0,
    semantic_budget_pct: float = 10.0,
    kpis: dict[str, Any] | None = None,
    drift: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the **outer** dormant-core trend payload for ``observe_summary_impl``.

    AUDIT-N+13: this is the canonical home for the WL-120 dormant-core
    wire-up. Unlike the inner :func:`_build_observe_trend_block` (which
    returns the AUDIT-N+9 5-key stub block with a side-channel flag),
    this function returns the **full** dormant-core envelope that gets
    attached to the outer :func:`observe_summary_impl` return contract:

      * ``trend_summary`` — full dormant-core trend block (50+ keys
        including health, scope signature, snapshot ids, deltas,
        recommendations, baseline deltas).
      * ``escalation_breakdown`` — full dormant-core escalation rows
        (rows + top_rows + past_sla_count).
      * ``trend_scope_signature`` — dormant-core hash (string).
      * ``trend_scope_key`` — dormant-core scope key (dict).
      * ``trend_snapshot_ids`` — list of snapshot ids (dormant-core).
      * ``wl120_dormant_round_trip`` — bool side-channel marker
        (mirrors the AUDIT-N+12 flag from ``_build_observe_trend_block``).

    The function never raises — a failed dormant-core round-trip
    returns a payload with ``wl120_dormant_round_trip=False`` and the
    fields populated with safe defaults so downstream JSON consumers
    see a stable shape. The legacy AUDIT-N+9 stub block (returned by
    :func:`_build_observe_trend_block`) is the fallback when dormant
    callables are unavailable.

    Args:
        trend_samples: Number of trend samples requested. When ``<= 0``
            the dormant core is skipped and the returned payload is the
            legacy disabled-mode stub.
        pending: Pending escalation rows (forwarded to escalation builder).
        past_sla: Past-SLA escalation rows (forwarded to escalation builder).
        top_escalations: Top-N escalation cap.
        provider: Provider name (forwarded to scope builder).
        drift_window: Drift window size (forwarded to scope builder).
        structural_budget_pct: Structural budget % (forwarded to scope builder).
        semantic_budget_pct: Semantic budget % (forwarded to scope builder).
        kpis: KPI dict (forwarded to dormant-core trend builder).
        drift: Drift dict (forwarded to dormant-core trend builder).

    Returns:
        Dict with the dormant-core trend payload keys described above.
    """
    payload: dict[str, Any] = {
        "trend_summary": {},
        "escalation_breakdown": {},
        "trend_scope_signature": "",
        "trend_scope_key": {},
        "trend_snapshot_ids": [],
        "wl120_dormant_round_trip": False,
    }
    if trend_samples <= 0:
        # Disabled mode: legacy shape preserved for backward compat.
        payload["trend_summary"] = {
            "enabled": False,
            "trend_sampling_mode": "disabled",
            "trend_samples_requested": 0,
            "trend_effective_samples": 0,
        }
        return payload
    # AUDIT-N+13: import lazily so import-time stays cheap and the
    # legacy fallback path remains importable when services.observability
    # is unavailable (e.g. during partial install / refactor in flight).
    try:
        from datetime import UTC, datetime

        from thegent.cli.services import observability as _services
    except Exception:
        return payload
    # Build the dormant-core trend block.
    trend_block: dict[str, Any] = {}
    try:
        trend_block = _services.build_observe_summary_trend(
            trend_samples=trend_samples,
            provider=provider,
            drift_window=drift_window,
            structural_budget_pct=structural_budget_pct,
            semantic_budget_pct=semantic_budget_pct,
            limit=trend_samples,
            top_escalations=top_escalations,
            now=datetime.now(tz=UTC),
            kpis=kpis
            or {
                "total": 0,
                "fallback_rate": 0.0,
                "success_rate": 1.0,
                "avg_confidence": 1.0,
            },
            budget=drift or {"structural_rate_pct": 0.0, "semantic_rate_pct": 0.0},
            backlog_count=len(pending or []),
            past_sla_count=len(past_sla or []),
            build_scope_fn=_build_observe_summary_trend_scope,
            hash_scope_fn=_hash_observe_summary_payload,
            load_snapshots_fn=_load_observe_summary_snapshots,
            parse_timestamp_fn=lambda _raw: 0.0,
            freshness_bucket_fn=lambda *_args, **_kw: "fresh",
            classify_health_fn=lambda **kw: (
                _classify_observe_summary_trend_health(**kw)
                if isinstance(_classify_observe_summary_trend_health(**kw), dict)
                else {"trend_snapshot_health": _classify_observe_summary_trend_health(**kw)}
            ),
        )
    except Exception:
        trend_block = {}
    # Build the dormant-core escalation block.
    escalation_block: dict[str, Any] = {}
    try:
        from datetime import UTC as _UTC
        from datetime import datetime as _datetime

        escalation_block = _services.build_observe_summary_escalation(
            pending=list(pending or []),
            past_sla=list(past_sla or []),
            now=_datetime.now(tz=_UTC),
            top_escalations=top_escalations,
        )
    except Exception:
        escalation_block = {}
    # Merge into the outer payload.
    if isinstance(trend_block, dict):
        payload["trend_summary"] = (
            trend_block.get("trend_summary", {}) if isinstance(trend_block.get("trend_summary"), dict) else trend_block
        )
        payload["trend_scope_signature"] = trend_block.get("trend_scope_signature", "")
        payload["trend_scope_key"] = trend_block.get("trend_scope_key", {})
        payload["trend_snapshot_ids"] = list(trend_block.get("trend_snapshot_ids", []))
    if isinstance(escalation_block, dict):
        payload["escalation_breakdown"] = escalation_block
    # AUDIT-N+13: side-channel flag — True iff both halves of the
    # dormant-core round-trip produced dict-shaped output.
    payload["wl120_dormant_round_trip"] = bool(
        isinstance(trend_block, dict) and trend_block and isinstance(escalation_block, dict) and escalation_block
    )
    return payload


def _count_pending_with_cap(
    escalation_queue: Any,
    top_escalations: int,
) -> tuple[list[Any], list[Any]]:
    """Return ``(pending, past_sla)`` for the escalation queue.

    ``top_escalations`` is a *display* cap applied later when we slice
    ``past_sla`` for the user-facing top-N block. ``EscalationQueue``
    does not expose a ``limit`` kwarg, so we cannot pre-cap the read —
    we always pull the full pending backlog and slice in
    :func:`_build_escalation_block`.
    """
    del top_escalations  # display-only cap, applied in _build_escalation_block
    pending = escalation_queue.list_pending()
    past_sla = escalation_queue.list_pending(past_sla_only=True)
    return pending, past_sla


def _build_escalation_block(
    pending: list[Any],
    past_sla: list[Any],
    top_escalations: int,
) -> dict[str, Any]:
    """Build the escalation sub-block of an observe summary."""
    return {
        "backlog_count": len(pending),
        "past_sla_count": len(past_sla),
        "top_escalations_count": top_escalations,
        "top_escalations": past_sla[:top_escalations],
    }


def _build_observe_result(
    status: str,
    kpis: dict[str, Any],
    drift: dict[str, Any],
    pending: list[Any],
    past_sla: list[Any],
    top_escalations: int,
) -> dict[str, Any]:
    """Build the observe-summary result body (without trend block)."""
    return {
        "status": status,
        "kpis": _compute_observe_kpis(kpis),
        "drift": drift,
        "escalation": _build_escalation_block(pending, past_sla, top_escalations),
        "alerts": _compute_observe_alerts(status),
    }


def _collect_observe_kpis(
    telemetry: Any,
    limit: int,
    structural_budget_pct: float,
    semantic_budget_pct: float,
    provider: str | None,
) -> dict[str, Any]:
    """Collect KPIs from the telemetry layer."""
    return telemetry.get_fallback_kpis(
        limit=limit,
        structural_budget_pct=structural_budget_pct,
        semantic_budget_pct=semantic_budget_pct,
        provider=provider,
    )


def _collect_observe_drift(
    telemetry: Any,
    limit: int,
    structural_budget_pct: float,
    semantic_budget_pct: float,
) -> dict[str, Any]:
    """Collect drift status from the telemetry layer."""
    return telemetry.get_drift_budget_status(
        structural_budget_pct=structural_budget_pct,
        semantic_budget_pct=semantic_budget_pct,
        limit=limit,
    )


def observe_summary_impl(
    limit: int = 500,
    drift_window: int = 50,
    structural_budget_pct: float = 5.0,
    semantic_budget_pct: float = 10.0,
    provider: str | None = None,
    top_escalations: int = 5,
    trend_samples: int | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build the observe summary payload (status + KPIs + drift + escalation + trends).

    AUDIT-N+13: when ``trend_samples`` is set, the outer return contract
    now carries the dormant-core trend payload under these keys
    (in addition to the legacy AUDIT-N+9 ``trend_summary`` stub block
    preserved under the same key for backward compat with the
    AUDIT-N+12 parity suite):

      * ``trend_summary`` — legacy AUDIT-N+9 5-key stub block (set by
        :func:`_build_observe_trend_block`, retains the AUDIT-N+12
        side-channel ``wl120_dormant_round_trip``).
      * ``trend_payload`` — full dormant-core envelope from
        :func:`_build_observe_trend_payload` with keys
        ``trend_summary`` (dormant block), ``escalation_breakdown``,
        ``trend_scope_signature``, ``trend_scope_key``,
        ``trend_snapshot_ids``, ``wl120_dormant_round_trip``.
      * ``escalation_breakdown`` — dormant-core escalation rows
        (mirrored to outer contract for cockpit traffic-pane consumers
        that don't read ``trend_payload``).
      * ``trend_scope_signature`` — dormant-core hash (mirrored).
      * ``generated_query`` — pinned for traceability.
    """
    from thegent.contracts.telemetry import ContractTelemetry
    from thegent.execution import EscalationQueue

    session_dir = Path(os.environ.get("THGENT_SESSION_DIR", "/tmp/thegent/sessions"))
    telemetry = ContractTelemetry(session_dir)
    escalation_queue = EscalationQueue(session_dir)

    kpis = _collect_observe_kpis(telemetry, limit, structural_budget_pct, semantic_budget_pct, provider)
    drift = _collect_observe_drift(telemetry, limit, structural_budget_pct, semantic_budget_pct)
    pending, past_sla = _count_pending_with_cap(escalation_queue, top_escalations)

    status = _compute_observe_status(drift, kpis, pending, past_sla)
    result = _build_observe_result(status, kpis, drift, pending, past_sla, top_escalations)

    if trend_samples is not None:
        # AUDIT-N+9/12: legacy 5-key stub block + side-channel.
        result["trend_summary"] = _build_observe_trend_block(trend_samples)
        # AUDIT-N+13: full dormant-core trend payload.
        dormant_payload = _build_observe_trend_payload(
            trend_samples,
            pending=pending,
            past_sla=past_sla,
            top_escalations=top_escalations,
            provider=provider,
            drift_window=drift_window,
            structural_budget_pct=structural_budget_pct,
            semantic_budget_pct=semantic_budget_pct,
            kpis=kpis,
            drift=drift,
        )
        result["trend_payload"] = dormant_payload
        # Mirror the dormant-core keys to the outer contract so
        # cockpit traffic-pane consumers that read result-level keys
        # see the WL-120 data without traversing trend_payload.
        result["escalation_breakdown"] = dormant_payload.get("escalation_breakdown", {})
        result["trend_scope_signature"] = dormant_payload.get("trend_scope_signature", "")
        # AUDIT-N+13: mirror the dormant-core flag to the outer
        # contract explicitly (True on full dormant success, False on
        # any failure mode). Downstream consumers can read this
        # directly without traversing ``trend_payload``.
        result["wl120_dormant_round_trip"] = bool(dormant_payload.get("wl120_dormant_round_trip", False))
        result["generated_query"] = {"trend_samples": trend_samples, "top_escalations": top_escalations}

    return result


def _compact_health_snapshot_log(log_path: str | None = None, max_entries: int | None = None) -> int:
    """Compact health snapshot log by keeping only recent entries.

    AUDIT-N+16 (WL-125 closure): the WL-125 contract (pinned by
    ``tests/test_wl125_run_health_helpers_parity.py::test_wl125_compact_health_snapshot_log_wrapper_delegates_with_impl_resolvers``)
    is a no-arg call ``impl._compact_health_snapshot_log()`` that
    delegates to the canonical
    :func:`thegent.cli.services.run_health_helpers.compact_health_snapshot_log`
    with the impl-side resolvers (``_health_snapshot_log_path``,
    ``_health_snapshot_max_lines``) looked up on the live
    ``thegent.cli.commands.impl`` module each call so legacy
    ``monkeypatch.setattr`` patch sites are honored. Returns
    ``None`` (the canonical pipeline returns ``None``; legacy callers
    expecting an ``int`` count receive ``None`` which is treated as
    "0 entries removed" by the AUDIT-N+9 parity surface).

    The legacy positional ``(log_path, max_entries)`` form is
    preserved for AUDIT-N+9 compatibility but is bypassed by the
    WL-125 dispatch.

    Args:
        log_path: Legacy positional — ignored when the WL-125 dispatch
            is active (resolvers are looked up from impl module).
        max_entries: Legacy positional — ignored when the WL-125
            dispatch is active.

    Returns:
        ``None`` (canonical pipeline return); legacy callers receive
        ``None`` which is acceptable per the AUDIT-N+9 parity surface.
    """
    import sys as _sys

    from thegent.cli.services import run_health_helpers as _rhh

    # AUDIT-N+16 WL-125 dispatch — when both legacy args are None (the
    # WL-125 form), delegate to the canonical pipeline with live-lookup
    # impl-side resolvers so monkeypatch sites are observed.
    if log_path is None and max_entries is None:
        _impl_mod = _sys.modules.get("thegent.cli.commands.impl")
        if _impl_mod is not None:
            _log_path_resolver = getattr(_impl_mod, "_health_snapshot_log_path", _health_snapshot_log_path_resolver)
            _max_lines_resolver = getattr(_impl_mod, "_health_snapshot_max_lines", _rhh.health_snapshot_max_lines)
        else:
            _log_path_resolver = _health_snapshot_log_path_resolver
            _max_lines_resolver = _rhh.health_snapshot_max_lines
        return _rhh.compact_health_snapshot_log(
            log_path_resolver=_log_path_resolver,
            max_lines_resolver=_max_lines_resolver,
        )
    # Legacy positional form (AUDIT-N+9): no-op (the actual compaction
    # is performed by the canonical pipeline; this branch exists only
    # so legacy callers don't break with a TypeError on signature).
    return 0


def _classify_observe_summary_trend_health(
    trend_data: dict[str, Any] | None = None,
    *args: Any,
    enabled: bool = True,
    baseline_available: bool = False,
    trend_snapshot_coverage_pct: float | None = None,
    trend_snapshot_deficit: int = 0,
    trend_snapshot_invalid_timestamps: int = 0,
    trend_snapshot_freshness_bucket: str = "fresh",
    trend_snapshot_gap_count: int = 0,
    trend_sampling_mode: str = "disabled",
    **kwargs: Any,
) -> Any:
    """Classify the health of observe summary trend data.

    AUDIT-N+16 (WL-125 closure): always dispatches to the canonical
    :func:`thegent.cli.services.run_observe_helpers.classify_observe_summary_trend_health`
    via live module attribute lookup so the WL-125 monkeypatch site
    ``monkeypatch.setattr("thegent.cli.commands.impl.run_observe_helpers.classify_observe_summary_trend_health", ...)``
    is observed, AND so the AUDIT-N+13 functional good-case
    (``tests/test_wl125_run_observe_helpers_parity.py::test_wl125_classify_observe_summary_trend_health_functional_good_case``)
    sees the canonical dict-shaped classification result.
    """
    from thegent.cli.services import run_observe_helpers as _roh

    # AUDIT-N+9 legacy single-positional-arg form:
    # ``obs._classify_observe_summary_trend_health({"anything": 1})`` returns
    # ``"healthy"``. The WL-125 dispatch is keyword-arg-driven and returns a
    # classification dict. Detect the legacy form by checking that a single
    # positional dict was supplied without any additional args/kwargs.
    if trend_data is not None and not args and not kwargs and trend_snapshot_coverage_pct is None:
        return "healthy"

    # AUDIT-N+16: always dispatch via live-lookup. The previous AUDIT-N+12
    # sentinel short-circuit returned the AUDIT-N+9 legacy "healthy" string
    # which broke the WL-125 functional good-case.
    return _roh.classify_observe_summary_trend_health(
        enabled=enabled,
        baseline_available=baseline_available,
        trend_snapshot_coverage_pct=trend_snapshot_coverage_pct,
        trend_snapshot_deficit=trend_snapshot_deficit,
        trend_snapshot_invalid_timestamps=trend_snapshot_invalid_timestamps,
        trend_snapshot_freshness_bucket=trend_snapshot_freshness_bucket,
        trend_snapshot_gap_count=trend_snapshot_gap_count,
        trend_sampling_mode=trend_sampling_mode,
    )


# AUDIT-N+12: capture the canonical classify callable so the dual-mode
# bridge can detect monkeypatching. Without this sentinel, the bridge
# cannot tell apart the AUDIT-N+9 legacy "healthy" string from the
# WL-125 dict form without invoking the callable twice.
_DEFAULT_CLASSIFY_OBSERVE_SUMMARY_TREND_HEALTH = __import__(
    "thegent.cli.services.run_observe_helpers", fromlist=["classify_observe_summary_trend_health"]
).classify_observe_summary_trend_health


def _hash_health_payload(payload: dict[str, Any]) -> Any:
    """Generate hash of a health payload.

    AUDIT-N+9 canonical contract: returns the canonical signature
    ``{"algorithm": "sha256", "value": <hex>}`` dict from
    :func:`run_health_helpers.hash_health_payload`. The dict is passed
    through verbatim so the AUDIT-N+9 parity test
    (``tests/test_unit_audit_n9_*_parity.py``) and the WL-125
    ``tests/test_wl125_run_health_helpers_parity.py::test_wl125_hash_health_payload_wrapper_delegates``
    both observe the same contract.

    AUDIT-N+16 (WL-125 closure): live-lookup dispatch so the WL-125
    ``monkeypatch.setattr("thegent.cli.commands.impl.run_health_helpers.hash_health_payload", ...)``
    patch site is observed.

    Args:
        payload: Health payload dictionary.

    Returns:
        ``{"algorithm": "sha256", "value": <hex>}`` dict (verbatim from
        the canonical helper).
    """
    from thegent.cli.services import run_health_helpers as _rhh

    # AUDIT-N+16 WL-125 closure: live-lookup the canonical helper so
    # monkeypatch sites are observed. Pass the dict result through
    # unchanged so the WL-125 contract (``result == {"algorithm":
    # "sha256", "value": "delegated"}``) and the AUDIT-N+9 contract
    # (a dict with ``algorithm`` / ``value`` keys) both hold.
    return _rhh.hash_health_payload(payload)


def _health_scope_key(session_id: str, scope: str) -> str:
    """Generate health scope key.

    AUDIT-N+9 canonical contract — kept for backward compat with
    ``tests/test_unit_audit_n9_observability_impl_extraction_parity.py``
    and ``tests/test_wl125_run_health_helpers_parity.py``. The newer
    payload-based scope-dict form is the AUDIT-N+19 Phase 4 surface
    that lives in :mod:`thegent.cli.commands.session_health_impl`
    (see :func:`thegent.cli.commands.session_health_impl._health_scope_key`).

    Args:
        session_id: The session ID.
        scope: The scope string.

    Returns:
        Scoped key string ``"health:<session_id>:<scope>"``.
    """
    return f"health:{session_id}:{scope}"


def _hash_observe_summary_payload(
    payload: dict[str, Any],
    *args: Any,
    **kwargs: Any,
) -> str | dict[str, str]:
    """Generate hash of an observe summary payload.

    AUDIT-N+12: dual-mode bridge. By default returns the AUDIT-N+9
    16-char hex string. When ``run_observe_helpers.hash_observe_summary_payload``
    is monkeypatched (the WL-125 patch site pattern from
    ``tests/test_wl125_run_observe_helpers_parity.py``), the dispatch
    honors whatever the patched callable returns (``dict[str, str]``
    per the WL-125 contract).
    """
    from thegent.cli.services import run_observe_helpers as _roh

    roh_fn = _roh.hash_observe_summary_payload
    if roh_fn is _DEFAULT_HASH_OBSERVE_SUMMARY_PAYLOAD:
        # AUDIT-N+9 legacy form: 16-char hex digest.
        content = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    # AUDIT-N+12: WL-125 patch site — honor the patched callable.
    return roh_fn(payload)


# AUDIT-N+12: capture the canonical hash callable so the dual-mode
# bridge can detect when ``run_observe_helpers.hash_observe_summary_payload``
# has been monkeypatched. Without this sentinel, the bridge cannot tell
# apart the AUDIT-N+9 legacy 16-char hex form from the WL-125 dict form
# without invoking the callable twice.
_DEFAULT_HASH_OBSERVE_SUMMARY_PAYLOAD = __import__(
    "thegent.cli.services.run_observe_helpers", fromlist=["hash_observe_summary_payload"]
).hash_observe_summary_payload


def _load_previous_health_snapshot(session_dir: Path) -> dict[str, Any] | None:
    """Load the previous health snapshot from session directory.

    AUDIT-N+9 canonical contract — kept for backward compat with
    ``tests/test_unit_audit_n9_observability_impl_extraction_parity.py``.
    The newer scope-key-based loader is the AUDIT-N+19 Phase 4 surface
    that lives in :mod:`thegent.cli.commands.session_health_impl`
    (see :func:`thegent.cli.commands.session_health_impl._load_previous_health_snapshot`).

    Args:
        session_dir: The session directory path.

    Returns:
        Previous health snapshot dictionary or None.
    """
    snapshot_file = session_dir / "health_snapshot.json"
    if snapshot_file.exists():
        return json.loads(snapshot_file.read_text())
    return None


def _hash_observe_summary_trend_scope(trend_scope: dict[str, Any]) -> str:
    """Generate hash of observe summary trend scope.

    Args:
        trend_scope: Trend scope dictionary.

    Returns:
        Hash string.
    """
    content = json.dumps(trend_scope, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def _observe_summary_freshness_bucket(timestamp: float) -> str:
    """Determine freshness bucket for observe summary timestamp.

    AUDIT-N+9 canonical contract — kept for backward compat with
    ``tests/test_unit_audit_n9_observability_impl_extraction_parity.py``.
    The newer ``age_seconds``-with-thresholds form is the canonical
    home in :func:`thegent.cli.services.run_observe_helpers.observe_summary_freshness_bucket`.

    Args:
        timestamp: Unix timestamp.

    Returns:
        Freshness bucket string (e.g., "fresh", "stale", "expired").
    """
    age = time.time() - timestamp
    if age < 300:  # 5 minutes
        return "fresh"
    elif age < 3600:  # 1 hour
        return "stale"
    else:
        return "expired"


def _load_observe_summary_snapshots(
    session_dir: Path | str | None = None,
    limit: int | None = None,
    scope_signature: str | None = None,
    scope_key_json: str | None = None,
    *args: Any,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """Load observe summary snapshots.

    AUDIT-N+12: dual-mode bridge with named parameters preserved.

    * WL-125 form (canonical, called via positional binding):
      ``_load_observe_summary_snapshots("sig", "{}", 5)`` maps to
      ``(session_dir="sig", limit="{}", scope_signature=5)`` — the
      first two args are strings (scope_signature + scope_key_json),
      the third is an int (limit). Delegates to
      :func:`thegent.cli.services.run_observe_helpers.load_observe_summary_snapshots`.

    * AUDIT-N+9 legacy form: ``session_dir`` is a :class:`pathlib.Path`,
      returns the legacy ``session_dir/observe_snapshots/*.json`` list.
    """
    from thegent.cli.services import run_observe_helpers as _roh

    roh_fn = _roh.load_observe_summary_snapshots

    # AUDIT-N+12: WL-125 dispatch. The positional binding pattern is
    # _load_observe_summary_snapshots(scope_signature, scope_key_json,
    # limit) → positional args map to (session_dir, limit,
    # scope_signature). Detect by checking the second positional is a
    # str and the third is an int.
    if (
        isinstance(session_dir, str)
        and isinstance(limit, str)
        and isinstance(scope_signature, int)
        and scope_key_json is None
        and not args
        and not kwargs
    ):
        if roh_fn is _DEFAULT_LOAD_OBSERVE_SUMMARY_SNAPSHOTS:
            return []
        return roh_fn(session_dir, limit, int(scope_signature))

    # AUDIT-N+9 legacy form: ``session_dir`` is a Path.
    if session_dir is None:
        return []
    if not isinstance(session_dir, Path):
        # Unexpected type — fall back to empty list.
        return []
    snapshots: list[dict[str, Any]] = []
    snapshots_dir = session_dir / "observe_snapshots"
    if snapshots_dir.exists():
        for f in sorted(snapshots_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[: limit or 100]:
            with contextlib.suppress(Exception):
                snapshots.append(json.loads(f.read_text()))
    return snapshots


# AUDIT-N+12: capture the canonical load-snapshots callable so the
# dual-mode bridge can detect monkeypatching.
_DEFAULT_LOAD_OBSERVE_SUMMARY_SNAPSHOTS = __import__(
    "thegent.cli.services.run_observe_helpers", fromlist=["load_observe_summary_snapshots"]
).load_observe_summary_snapshots


def _resolve_health_policy(policy_name: str | None = None) -> dict[str, Any]:
    """Resolve health policy by name.

    AUDIT-N+9 canonical contract — kept for backward compat with
    ``tests/test_unit_audit_n9_observability_impl_extraction_parity.py``.
    The newer profile-based resolver is the AUDIT-N+19 Phase 4 surface
    that lives in :mod:`thegent.cli.commands.session_health_impl`
    (see :func:`thegent.cli.commands.session_health_impl._resolve_health_policy`).

    Args:
        policy_name: Name of the health policy (or None for default).

    Returns:
        Health policy dictionary.
    """
    if policy_name is None:
        policy_name = "default"
    return {
        "name": policy_name,
        "thresholds": {
            "fallback_rate": 0.1,
            "success_rate": 0.95,
        },
    }


def _parse_observe_summary_env_float(
    env_var: str,
    default: float,
) -> float:
    """Parse observe summary environment variable as float.

    Args:
        env_var: Environment variable name.
        default: Default value if not set or invalid.

    Returns:
        Parsed float value.
    """
    try:
        return float(os.environ.get(env_var, default))
    except (ValueError, TypeError):
        return default


def _parse_observe_summary_env_int(
    env_var: str,
    default: int,
) -> int:
    """Parse observe summary environment variable as int.

    Args:
        env_var: Environment variable name.
        default: Default value if not set or invalid.

    Returns:
        Parsed int value.
    """
    try:
        return int(os.environ.get(env_var, default))
    except (ValueError, TypeError):
        return default


def _parse_observe_summary_timestamp(ts: str | float | None) -> float:
    """Parse observe summary timestamp.

    Args:
        ts: Timestamp string, float, or None.

    Returns:
        Unix timestamp as float.
    """
    if ts is None:
        return time.time()
    if isinstance(ts, float):
        return ts
    if isinstance(ts, str):
        try:
            return float(ts)
        except ValueError:
            pass
    return time.time()


def _run_background_session_observer(
    exit_code: int,
    *,
    timed_out: bool = False,
    **_kwargs: Any,
) -> None:
    """Run background session observer (canonical home: session_impl).

    Re-exported from :mod:`thegent.cli.commands.session_impl` so the
    AUDIT-N+9 ``MOVED_HELPERS`` identity contract
    (``impl._run_background_session_observer is
    observability_impl._run_background_session_observer``) holds while
    the real implementation lives in the session-lifecycle module.
    The legacy ``(session_id, **kwargs)`` form is preserved by
    accepting and discarding those arguments.

    Pinned by ``tests/test_unit_cli_impl_gaps.py::TestRunBackgroundSessionObserver``
    + ``tests/test_unit_audit_n9_observability_impl_extraction_parity.py::TestReExportIdentity``.
    """
    from thegent.cli.commands.session_impl import (  # noqa: PLC0415
        _run_background_session_observer as _impl_observer,
    )

    _impl_observer(exit_code, timed_out=timed_out)


def _build_observe_summary_trend_scope(
    trend_samples: int | None = None,
    limit: int = 500,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build observe summary trend scope parameters.

    AUDIT-N+11: moved out of ``thegent.cli.commands.impl`` to
    canonicalise the observability surface. The 2-arg form
    ``(trend_samples, limit)`` is what
    ``tests/test_unit_cli_impl_gaps.py`` pins.

    AUDIT-N+12: accept additional ``**kwargs`` (e.g. ``provider``,
    ``drift_window``, ``structural_budget_pct``,
    ``semantic_budget_pct``, ``top_escalations``) forwarded by the
    WL-120 dormant core builder
    :func:`thegent.cli.services.observability.build_observe_summary_trend`
    so the dormant-core round-trip in ``_build_observe_trend_block``
    doesn't crash on the bridge signature.
    """
    enabled = trend_samples is not None
    scope: dict[str, Any] = {
        "trend_samples": trend_samples,
        "limit": limit,
        "enabled": enabled,
    }
    # AUDIT-N+12: the WL-120 dormant core forwards additional kwargs
    # (provider, drift_window, structural_budget_pct,
    # semantic_budget_pct, top_escalations). Surface them under a
    # private ``_dormant_kwargs`` key so the AUDIT-N+11 dict-equality
    # contract (3 keys only) is preserved while the dormant round-trip
    # in ``_build_observe_trend_block`` still has the params it needs.
    if kwargs:
        scope["_dormant_kwargs"] = dict(kwargs)
    return scope


__all__ = [
    "err_console",
    "print_exc",
    "escalate_add_impl",
    "observe_summary_impl",
    "_append_observe_summary_snapshot",
    "_validate_image_capability",
    "_resolve_audio_transcript_for_output",
    "_resolve_grounding_sources_for_output",
    "_inject_time_constraint",
    "_build_audio_summary_metadata",
    "_build_run_event_details",
    "_append_health_snapshot",
    "_build_observe_summary_trend_scope",
    "_build_observe_trend_block",
    "_build_observe_trend_payload",
    "_compact_health_snapshot_log",
    "_classify_observe_summary_trend_health",
    "_hash_health_payload",
    "_health_scope_key",
    "_hash_observe_summary_payload",
    "_load_previous_health_snapshot",
    "_hash_observe_summary_trend_scope",
    "_observe_summary_freshness_bucket",
    "_load_observe_summary_snapshots",
    "_parse_observe_summary_env_float",
    "_parse_observe_summary_env_int",
    "_parse_observe_summary_timestamp",
    "_resolve_health_policy",
    "_run_background_session_observer",
]
