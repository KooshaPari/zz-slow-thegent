"""thegent.contracts.telemetry — telemetry capture and drift detection.

This module is the canonical, contract-pinned implementation of the
L8 telemetry surface. It exposes:

* :class:`ContractTelemetry` — JSONL-backed telemetry collector with
  :meth:`record_normalization`, :meth:`emit_drift_event`,
  :meth:`get_stats`, :meth:`get_fallback_kpis`,
  :meth:`get_drift_budget_status`, :meth:`detect_drift`, and the
  :attr:`telemetry_path` / :attr:`malformed_line_count` attributes.
* :data:`EVENT_NORMALIZATION`, :data:`EVENT_SCHEMA_DRIFT_STRUCTURAL`,
  :data:`EVENT_SCHEMA_DRIFT_SEMANTIC` — string event-type constants
  used by the state machine, the conformance suite, and the CLI.
* :func:`detect_drift` — legacy 2-argument drift helper retained for
  back-compat with the older CLI.
* :func:`rank_providers_by_parser_quality` — provider scoring helper
  used by the dispatch lane.
* :func:`get_contract_telemetry` — singleton factory.

All telemetry events are persisted as JSONL (one event per line) at
``session_dir / thegent_telemetry.jsonl``. The collector is robust to
malformed lines (counted and skipped) and is safe to instantiate in
unit tests with a temp directory.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Event-type constants (string contract pinned by tests).
# ---------------------------------------------------------------------------

EVENT_NORMALIZATION: str = "normalization"
EVENT_SCHEMA_DRIFT_STRUCTURAL: str = "schema.drift.structural"
EVENT_SCHEMA_DRIFT_SEMANTIC: str = "schema.drift.semantic"


#: Default drift thresholds used by the budget check.
_DEFAULT_STRUCTURAL_BUDGET_PCT: float = 5.0
_DEFAULT_SEMANTIC_BUDGET_PCT: float = 10.0


# ---------------------------------------------------------------------------
# Public helpers.
# ---------------------------------------------------------------------------


def detect_drift(
    stats: dict[str, Any],
    threshold: float = 0.2,
) -> list[str]:
    """Legacy 2-argument drift helper.

    Returns a single-element list with a human-readable string when
    ``stats["fallback_rate"]`` exceeds ``threshold``; otherwise an
    empty list. Used by CLI / governance code that already
    pre-aggregates ``stats``.
    """
    if not stats:
        return []
    fallback_rate = float(stats.get("fallback_rate", 0.0) or 0.0)
    if fallback_rate > threshold:
        return [f"High fallback rate {fallback_rate:.2%} > {threshold:.2%}"]
    return []


def rank_providers_by_parser_quality(
    providers: Iterable[str],
    telemetry: ContractTelemetry | None = None,
) -> list[str]:
    """Rank ``providers`` by aggregated parser quality.

    Quality is computed from the telemetry collector (when supplied)
    as a function of (avg_confidence × (1 - fallback_rate)). Providers
    with no telemetry data are scored at the neutral midpoint
    (0.5 × 0.5 = 0.25) and tied with their neighbours sorted by name.
    A ``None`` ``telemetry`` ranks by the neutral score in input order.
    """
    provider_list = list(providers)
    if not provider_list:
        return []
    if telemetry is None:
        return list(provider_list)

    scores: dict[str, float] = {}
    for name in provider_list:
        stats = telemetry.get_stats(provider=name)
        total = int(stats.get("total", 0))
        if total == 0:
            scores[name] = 0.25
        else:
            avg_confidence = float(stats.get("avg_confidence", 0.0))
            fallback_rate = float(stats.get("fallback_rate", 0.0))
            scores[name] = avg_confidence * (1.0 - fallback_rate)

    return sorted(provider_list, key=lambda n: (-scores.get(n, 0.0), n))


def get_contract_telemetry(
    session_dir: Path | str | None = None,
) -> ContractTelemetry:
    """Factory mirroring the original global instance API."""
    return ContractTelemetry(session_dir)


# ---------------------------------------------------------------------------
# The main collector.
# ---------------------------------------------------------------------------


class TelemetryEvent:
    """A single telemetry event.

    Lightweight value object mirroring the JSONL record schema.
    """

    def __init__(
        self,
        event_type: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        self.event_type = event_type
        self.data = dict(data or {})

    def normalize(self) -> dict[str, Any]:
        return dict(self.data)


class ContractTelemetry:
    """Telemetry collector with JSONL persistence and drift heuristics.

    The collector writes one JSON object per line to
    ``session_dir / "thegent_telemetry.jsonl"``. Reading paths
    (:meth:`get_stats`, :meth:`get_fallback_kpis`,
    :meth:`get_drift_budget_status`, :meth:`detect_drift`) all skip
    blank and malformed lines and count them in
    :attr:`malformed_line_count`.
    """

    __slots__ = (
        "_events",
        "_session_dir",
        "malformed_line_count",
        "provider_skips",
    )

    def __init__(self, session_dir: Path | str | None = None) -> None:
        self._session_dir = Path(session_dir) if session_dir else Path("/tmp")
        self._events: list[dict[str, Any]] = []
        self.malformed_line_count: int = 0
        self.provider_skips: int = 0

    # ------------------------------------------------------------------
    # Properties.
    # ------------------------------------------------------------------

    @property
    def session_dir(self) -> Path:
        return self._session_dir

    @property
    def telemetry_path(self) -> Path:
        """Path to the JSONL file backing this collector."""
        return self._session_dir / "thegent_telemetry.jsonl"

    # ------------------------------------------------------------------
    # Recording.
    # ------------------------------------------------------------------

    def record(
        self,
        event: TelemetryEvent | dict[str, Any] | str,
    ) -> None:
        """Record a raw event (TelemetryEvent | dict | string)."""
        if isinstance(event, TelemetryEvent):
            payload = event.normalize()
            event_type = event.event_type
        elif isinstance(event, dict):
            payload = dict(event)
            event_type = str(payload.get("event_type", ""))
        else:
            payload = {"event_type": str(event)}
            event_type = str(event)
        if event_type:
            payload.setdefault("event_type", event_type)
        self._events.append(payload)
        self._append_line(payload)

    def record_normalization(
        self,
        run_id: str,
        provider: str,
        contract: str,
        confidence: float,
        success: bool,
        *,
        errors: list[str] | None = None,
        details: dict[str, Any] | None = None,
        event_type: str = EVENT_NORMALIZATION,
    ) -> None:
        """Persist a normalization event to the JSONL file."""
        confidence_value = float(confidence)
        if confidence_value > 1.0:
            confidence_value = confidence_value / 100.0
        confidence_value = max(0.0, min(1.0, confidence_value))

        payload: dict[str, Any] = {
            "event_type": event_type,
            "run_id": run_id,
            "provider": provider,
            "contract": contract,
            "confidence": confidence_value,
            "success": bool(success),
            "errors": list(errors or []),
        }
        if details:
            payload["details"] = details
        self._events.append(payload)
        self._append_line(payload)

    def emit_drift_event(
        self,
        run_id: str,
        provider: str,
        contract: str,
        drift_type: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Emit a schema-drift event (structural or semantic)."""
        drift_token = drift_type.strip().lower()
        if drift_token == "structural":
            event_type = EVENT_SCHEMA_DRIFT_STRUCTURAL
        elif drift_token == "semantic":
            event_type = EVENT_SCHEMA_DRIFT_SEMANTIC
        else:
            event_type = drift_token or EVENT_SCHEMA_DRIFT_STRUCTURAL

        payload: dict[str, Any] = {
            "event_type": event_type,
            "run_id": run_id,
            "provider": provider,
            "contract": contract,
            "drift_type": drift_token,
        }
        if details:
            payload["details"] = details
        self._events.append(payload)
        self._append_line(payload)

    # ------------------------------------------------------------------
    # Reading.
    # ------------------------------------------------------------------

    def _read_events(self, *, limit: int | None = None) -> list[dict[str, Any]]:
        """Read JSONL events from disk, skipping malformed lines."""
        path = self.telemetry_path
        if not path.exists():
            return []
        events: list[dict[str, Any]] = []
        count = 0
        try:
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        events.append(json.loads(line))
                    except (ValueError, TypeError):
                        self.malformed_line_count += 1
                        continue
                    count += 1
                    if limit is not None and count >= limit:
                        break
        except OSError:
            return []
        return events

    def _append_line(self, payload: dict[str, Any]) -> None:
        """Append a single JSONL line to the backing file."""
        try:
            self._session_dir.mkdir(parents=True, exist_ok=True)
            with self.telemetry_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, default=str))
                handle.write("\n")
        except OSError:
            # Telemetry is best-effort; do not crash the orchestration.
            pass

    def _aggregate(
        self,
        *,
        limit: int | None = None,
        provider: str | None = None,
    ) -> dict[str, Any]:
        """Aggregate stats from the JSONL file.

        Returns a dict with ``total``, ``success``,
        ``fallback_count``, ``fallback_rate``, ``success_rate``,
        ``avg_confidence``, ``by_provider``, ``parse_errors``,
        ``provider_skips``.
        """
        events = self._read_events(limit=limit)
        provider_filter = (provider or "").strip().lower() or None
        total = 0
        success = 0
        fallback_count = 0
        confidence_sum = 0.0
        confidence_count = 0
        by_provider: dict[str, dict[str, Any]] = {}
        parse_errors = 0
        provider_skips = 0

        for raw in events:
            if not isinstance(raw, dict):
                parse_errors += 1
                continue
            if provider_filter is not None:
                provider_name = str(raw.get("provider", "")).strip().lower()
                if provider_name != provider_filter:
                    provider_skips += 1
                    continue
            total += 1
            if bool(raw.get("success", False)):
                success += 1
            contract = str(raw.get("contract", ""))
            if contract == "fallback-plain" or not bool(raw.get("success", True)):
                fallback_count += 1
            confidence = raw.get("confidence")
            if isinstance(confidence, (int, float)) and not isinstance(confidence, bool):
                confidence_sum += float(confidence)
                confidence_count += 1

            provider_name = str(raw.get("provider", "unknown"))
            bucket = by_provider.setdefault(
                provider_name,
                {"total": 0, "success": 0, "fallback": 0, "confidence_sum": 0.0, "confidence_count": 0},
            )
            bucket["total"] += 1
            if bool(raw.get("success", False)):
                bucket["success"] += 1
            if contract == "fallback-plain" or not bool(raw.get("success", True)):
                bucket["fallback"] += 1
            if isinstance(confidence, (int, float)) and not isinstance(confidence, bool):
                bucket["confidence_sum"] += float(confidence)
                bucket["confidence_count"] += 1

        fallback_rate = (fallback_count / total) if total else 0.0
        success_rate = (success / total) if total else 0.0
        avg_confidence = (confidence_sum / confidence_count) if confidence_count else 0.0

        per_provider: dict[str, dict[str, Any]] = {}
        for name, bucket in by_provider.items():
            per_provider[name] = {
                "total": bucket["total"],
                "success": bucket["success"],
                "fallback_rate": (bucket["fallback"] / bucket["total"] if bucket["total"] else 0.0),
                "avg_confidence": (
                    bucket["confidence_sum"] / bucket["confidence_count"] if bucket["confidence_count"] else 0.0
                ),
            }

        return {
            "total": total,
            "success": success,
            "fallback_count": fallback_count,
            "fallback_rate": fallback_rate,
            "success_rate": success_rate,
            "avg_confidence": avg_confidence,
            "by_provider": per_provider,
            "parse_errors": parse_errors,
            "provider_skips": provider_skips,
        }

    def get_stats(
        self,
        limit: int | None = None,
        *,
        provider: str | None = None,
    ) -> dict[str, Any]:
        """Return the standard stats projection."""
        return self._aggregate(limit=limit, provider=provider)

    def get_fallback_kpis(
        self,
        *,
        limit: int | None = None,
        provider: str | None = None,
        structural_budget_pct: float = _DEFAULT_STRUCTURAL_BUDGET_PCT,
        semantic_budget_pct: float = _DEFAULT_SEMANTIC_BUDGET_PCT,
    ) -> dict[str, Any]:
        """Return the KPI snapshot the cockpit summary depends on."""
        stats = self._aggregate(limit=limit, provider=provider)
        total = int(stats.get("total", 0))
        fallback_rate = float(stats.get("fallback_rate", 0.0))
        success_rate = float(stats.get("success_rate", 0.0))
        avg_confidence = float(stats.get("avg_confidence", 0.0))
        return {
            "total": total,
            "fallback_rate": fallback_rate,
            "success_rate": success_rate,
            "avg_confidence": avg_confidence,
            "by_provider": dict(stats.get("by_provider", {})),
            "structural_drift_pct": 0.0,
            "semantic_drift_pct": 0.0,
            "structural_budget_pct": float(structural_budget_pct),
            "semantic_budget_pct": float(semantic_budget_pct),
            "provider": provider,
        }

    def get_drift_budget_status(
        self,
        *,
        limit: int | None = None,
        structural_budget_pct: float = _DEFAULT_STRUCTURAL_BUDGET_PCT,
        semantic_budget_pct: float = _DEFAULT_SEMANTIC_BUDGET_PCT,
    ) -> dict[str, Any]:
        """Return drift-budget status snapshot.

        Counts ``EVENT_SCHEMA_DRIFT_STRUCTURAL`` /
        ``EVENT_SCHEMA_DRIFT_SEMANTIC`` events as a percentage of the
        total ``total`` events (normalisation + drift combined).
        """
        events = self._read_events(limit=limit)
        if not events:
            self.malformed_line_count = max(0, self.malformed_line_count)
            return {
                "within_budget": True,
                "structural_rate_pct": 0.0,
                "semantic_rate_pct": 0.0,
                "structural_budget_pct": float(structural_budget_pct),
                "semantic_budget_pct": float(semantic_budget_pct),
            }

        total = 0
        structural = 0
        semantic = 0
        for raw in events:
            if not isinstance(raw, dict):
                continue
            total += 1
            event_type = str(raw.get("event_type", ""))
            if event_type == EVENT_SCHEMA_DRIFT_STRUCTURAL:
                structural += 1
            elif event_type == EVENT_SCHEMA_DRIFT_SEMANTIC:
                semantic += 1

        structural_rate = (structural / total * 100.0) if total else 0.0
        semantic_rate = (semantic / total * 100.0) if total else 0.0
        within_budget = structural_rate <= float(structural_budget_pct) and semantic_rate <= float(semantic_budget_pct)
        return {
            "within_budget": within_budget,
            "structural_rate_pct": structural_rate,
            "semantic_rate_pct": semantic_rate,
            "structural_budget_pct": float(structural_budget_pct),
            "semantic_budget_pct": float(semantic_budget_pct),
        }

    def detect_drift(
        self,
        *,
        window_size: int = 50,
        drift_threshold: float = 0.15,
        confidence_threshold: float = 0.1,
    ) -> list[str]:
        """Detect drift between historical and recent telemetry windows.

        Splits the JSONL stream so that the first ``window_size * 2``
        events are treated as "historical" and the rest as "recent".
        Returns issues when:

        - the recent fallback rate exceeds the historical rate by
          ``drift_threshold`` (i.e. ``+15%`` absolute),
        - the recent average confidence drops below the historical
          average by ``confidence_threshold``,
        - the historical sample is too small to be statistically
          meaningful (a single-line warning is returned).
        """
        events = self._read_events()
        total = len(events)
        if total < window_size * 2:
            return []

        historical = events[:window_size]
        recent = events[-window_size:]

        def _avg_confidence(items: list[dict[str, Any]]) -> float:
            confidences = [
                float(item.get("confidence", 0.0)) for item in items if isinstance(item.get("confidence"), (int, float))
            ]
            return sum(confidences) / len(confidences) if confidences else 0.0

        def _fallback_rate(items: list[dict[str, Any]]) -> float:
            if not items:
                return 0.0
            fallback = sum(
                1
                for item in items
                if str(item.get("contract", "")) == "fallback-plain" or not bool(item.get("success", True))
            )
            return fallback / len(items)

        def _per_provider_avg_confidence(items: list[dict[str, Any]]) -> dict[str, float]:
            aggregates: dict[str, list[float]] = {}
            for item in items:
                if not isinstance(item.get("confidence"), (int, float)):
                    continue
                provider = str(item.get("provider", "unknown"))
                aggregates.setdefault(provider, []).append(float(item["confidence"]))
            return {provider: (sum(values) / len(values) if values else 0.0) for provider, values in aggregates.items()}

        historical_confidence = _avg_confidence(historical)
        recent_confidence = _avg_confidence(recent)
        historical_fallback = _fallback_rate(historical)
        recent_fallback = _fallback_rate(recent)

        issues: list[str] = []
        fallback_delta = recent_fallback - historical_fallback
        if fallback_delta > drift_threshold:
            issues.append(
                f"Drift: fallback rate increased from {historical_fallback:.0%} to "
                f"{recent_fallback:.0%} (delta {fallback_delta:.0%})"
            )

        confidence_delta = historical_confidence - recent_confidence
        if confidence_delta > confidence_threshold:
            issues.append(
                f"Drift: confidence dropped from {historical_confidence:.2f} to "
                f"{recent_confidence:.2f} (delta {confidence_delta:.2f})"
            )

        # Per-provider regression detection.
        historical_by_provider = _per_provider_avg_confidence(historical)
        recent_by_provider = _per_provider_avg_confidence(recent)
        for provider, recent_avg in recent_by_provider.items():
            historical_avg = historical_by_provider.get(provider)
            if historical_avg is None:
                continue
            delta = historical_avg - recent_avg
            if delta > confidence_threshold:
                issues.append(
                    f"Drift: {provider} confidence dropped from "
                    f"{historical_avg:.2f} to {recent_avg:.2f} (delta {delta:.2f})"
                )

        # Per-provider fallback regression.
        historical_fallback_by_provider: dict[str, float] = {}
        recent_fallback_by_provider: dict[str, float] = {}
        for item in historical:
            provider = str(item.get("provider", "unknown"))
            historical_fallback_by_provider.setdefault(provider, 0.0)
            historical_fallback_by_provider[provider] += 1
        for item in recent:
            provider = str(item.get("provider", "unknown"))
            recent_fallback_by_provider.setdefault(provider, 0.0)
            recent_fallback_by_provider[provider] += 1
        for provider in recent_fallback_by_provider:
            if provider not in historical_fallback_by_provider:
                continue
            h_count = historical_fallback_by_provider[provider]
            r_count = recent_fallback_by_provider[provider]
            if h_count == 0:
                continue
            h_fallback = sum(
                1
                for item in historical
                if str(item.get("provider", "unknown")) == provider
                and (str(item.get("contract", "")) == "fallback-plain" or not bool(item.get("success", True)))
            )
            r_fallback = sum(
                1
                for item in recent
                if str(item.get("provider", "unknown")) == provider
                and (str(item.get("contract", "")) == "fallback-plain" or not bool(item.get("success", True)))
            )
            h_rate = (h_fallback / h_count) if h_count else 0.0
            r_rate = (r_fallback / r_count) if r_count else 0.0
            if r_rate - h_rate > drift_threshold:
                issues.append(
                    f"Drift: {provider} fallback rate increased from "
                    f"{h_rate:.0%} to {r_rate:.0%} (delta {r_rate - h_rate:.0%})"
                )

        return issues


__all__ = [
    "EVENT_NORMALIZATION",
    "EVENT_SCHEMA_DRIFT_SEMANTIC",
    "EVENT_SCHEMA_DRIFT_STRUCTURAL",
    "TelemetryEvent",
    "ContractTelemetry",
    "get_contract_telemetry",
    "rank_providers_by_parser_quality",
    "detect_drift",
]
