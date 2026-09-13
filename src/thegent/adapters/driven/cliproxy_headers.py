"""Per-request tg-* control header parsing and response header builders.

Extracted from cliproxy_adapter.py as part of L1 architecture hardening.

GW-20, GW-35, GW-36, GW-43, GW-48, GW-49 namespaces are covered here.
"""

from __future__ import annotations

import contextlib
import uuid
from dataclasses import dataclass


# @trace FR-CACHE-024 FR-CACHE-025 FR-CACHE-027
@dataclass
class CacheControl:
    """Per-request cache control extracted from tg-* headers."""

    namespace: str = "default"
    force_refresh: bool = False
    skip_cache: bool = False  # set by tg-skip-cache: true


def extract_cache_control(request_headers) -> CacheControl:  # type: ignore[no-untyped-def]
    """Extract cache control directives from tg-* request headers.

    Headers:
        tg-cache-namespace: <string>   (default: "default")
        tg-cache-force-refresh: true   (default: false)
        tg-skip-cache: true            (default: false)

    Args:
        request_headers: A mapping exposing .get() (e.g. Request.headers or dict).
    """
    headers = request_headers
    return CacheControl(
        namespace=headers.get("tg-cache-namespace", "default"),
        force_refresh=headers.get("tg-cache-force-refresh", "").lower() == "true",
        skip_cache=headers.get("tg-skip-cache", "").lower() == "true",
    )


# GW-20: tg-* per-request control headers namespace
_TG_HEADER_NAMES: frozenset[str] = frozenset(
    {
        "tg-cache-ttl",
        "tg-skip-cache",
        "tg-cache-namespace",
        "tg-cache-force-refresh",
        "tg-event-id",
        "tg-fallback-step",
        "tg-ttft-ms",
        "tg-response-cost",
        "tg-custom-cost",
    }
)


@dataclass
class TgHeaders:
    """Parsed tg-* per-request control headers (GW-20).

    # @trace FR-ROUTE-020
    """

    cache_ttl: float | None = None  # tg-cache-ttl: <seconds>
    skip_cache: bool = False  # tg-skip-cache: true
    cache_namespace: str = "default"  # tg-cache-namespace: <ns>
    cache_force_refresh: bool = False  # tg-cache-force-refresh: true
    custom_cost: float | None = None  # tg-custom-cost: <usd>


def extract_tg_headers(request_headers: dict) -> TgHeaders:
    """Extract and parse all tg-* control headers from the request (GW-20).

    # @trace FR-ROUTE-020
    """
    headers = {k.lower(): v for k, v in request_headers.items()}

    cache_ttl = None
    raw_ttl = headers.get("tg-cache-ttl")
    if raw_ttl is not None:
        with contextlib.suppress(ValueError):
            cache_ttl = float(raw_ttl)

    custom_cost = None
    raw_cost = headers.get("tg-custom-cost")
    if raw_cost is not None:
        with contextlib.suppress(ValueError):
            custom_cost = float(raw_cost)

    return TgHeaders(
        cache_ttl=cache_ttl,
        skip_cache=headers.get("tg-skip-cache", "").lower() == "true",
        cache_namespace=headers.get("tg-cache-namespace", "default"),
        cache_force_refresh=headers.get("tg-cache-force-refresh", "").lower() == "true",
        custom_cost=custom_cost,
    )


def build_cache_response_headers(hit: bool, ttl: float, namespace: str) -> dict[str, str]:
    """Build x-cache-* response headers for a cache HIT or MISS.

    Args:
        hit: True if response came from cache.
        ttl: Remaining TTL in seconds (for HIT) or configured TTL (for MISS).
        namespace: Cache namespace used.

    Returns:
        Dict of header name -> value to merge into response headers.
    """
    return {
        "x-cache-status": "HIT" if hit else "MISS",
        "x-cache-ttl": str(int(ttl)),
        "x-cache-namespace": namespace,
    }


# @trace FR-COST-032 FR-COST-033
def build_cost_response_header(response_body: dict) -> dict[str, str]:
    """Build tg-response-cost header from response JSON body.

    Returns {'tg-response-cost': '<cost>'} or empty dict if cost unavailable.

    On the hot response path — exceptions are swallowed to prevent crashing the gateway.

    # @trace FR-COST-032
    """
    try:
        # Local import to keep this module lightweight
        from thegent.utils.routing_impl.cost_calculator import (
            calculate_cost_from_response,
            format_cost_header_value,
        )

        cost = calculate_cost_from_response(response_body)
        if cost > 0.0:
            return {"tg-response-cost": format_cost_header_value(cost)}
    except Exception:
        pass
    return {}


# ---------------------------------------------------------------------------
# GW-48: inject usage.cost into every response body
# ---------------------------------------------------------------------------


def inject_usage_cost(response_body: dict) -> dict:
    """Inject cost into response body's usage object (GW-48).

    Adds usage.cost = <usd_float> computed from token counts and model pricing.
    If usage or pricing unavailable, returns body unchanged.

    Returns modified copy of response_body (does not mutate).

    # @trace FR-REQEXT-048
    """
    try:
        from thegent.utils.routing_impl.cost_calculator import (
            calculate_cost_from_response,
        )

        cost = calculate_cost_from_response(response_body)
        if cost <= 0.0:
            return response_body
        result = dict(response_body)
        usage = dict(result.get("usage", {}))
        usage["cost"] = cost
        result["usage"] = usage
        return result
    except Exception:
        return response_body


# ---------------------------------------------------------------------------
# GW-49: native_finish_reason alongside normalized finish_reason
# ---------------------------------------------------------------------------

# Mapping of provider-native finish reasons to normalized OpenAI-compatible reasons
_FINISH_REASON_NORMALIZATION: dict[str, str] = {
    # Anthropic
    "end_turn": "stop",
    "max_tokens": "length",
    "stop_sequence": "stop",
    "tool_use": "tool_calls",
    # Google Gemini
    "STOP": "stop",
    "MAX_TOKENS": "length",
    "SAFETY": "content_filter",
    "RECITATION": "content_filter",
    "OTHER": "stop",
    # OpenAI (already normalized — identity mapping)
    "stop": "stop",
    "length": "length",
    "content_filter": "content_filter",
    "tool_calls": "tool_calls",
    "function_call": "tool_calls",
}


def normalize_finish_reason(native_reason: str | None) -> str:
    """Normalize a provider-native finish reason to OpenAI-compatible value (GW-49).

    Returns the normalized reason, or "stop" as default for unknown values.

    # @trace FR-REQEXT-049
    """
    if native_reason is None:
        return "stop"
    return _FINISH_REASON_NORMALIZATION.get(native_reason, "stop")


def inject_native_finish_reason(response_body: dict) -> dict:
    """Inject native_finish_reason alongside normalized finish_reason in choices (GW-49).

    For each choice in response_body["choices"]:
    - Reads the existing finish_reason
    - Sets native_finish_reason = finish_reason (the original from provider)
    - Sets finish_reason = normalize_finish_reason(native_finish_reason)

    Returns modified copy of response_body (does not mutate).

    # @trace FR-REQEXT-049
    """
    choices = response_body.get("choices")
    if not choices:
        return response_body
    result = dict(response_body)
    new_choices = []
    for choice in choices:
        new_choice = dict(choice)
        native = choice.get("finish_reason")
        new_choice["native_finish_reason"] = native
        new_choice["finish_reason"] = normalize_finish_reason(native)
        new_choices.append(new_choice)
    result["choices"] = new_choices
    return result


# ---------------------------------------------------------------------------
# GW-35: tg-event-id — unique per-request trace ID
# ---------------------------------------------------------------------------


def generate_event_id() -> str:
    """Generate a unique event ID for request tracing (GW-35).

    Format: tg-<8-char-hex> for brevity and readability.
    # @trace FR-OBS-035
    """
    return f"tg-{uuid.uuid4().hex[:8]}"


def build_event_id_header() -> dict[str, str]:
    """Build tg-event-id response header (GW-35).

    Returns {'tg-event-id': 'tg-<8hex>'}.
    """
    return {"tg-event-id": generate_event_id()}


# ---------------------------------------------------------------------------
# GW-36: tg-fallback-step — which fallback provider was used
# ---------------------------------------------------------------------------


def build_fallback_step_header(step: int) -> dict[str, str]:
    """Build tg-fallback-step response header (GW-36).

    step=0 means primary model succeeded.
    step=1+ means Nth fallback was used.

    Returns {'tg-fallback-step': '<step>'}.
    # @trace FR-OBS-036
    """
    return {"tg-fallback-step": str(step)}
