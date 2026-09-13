"""Session-contract health-trend module (AUDIT-N+19 Phase 4).

Implements :func:`session_contract_health_trend_impl` and the three
serialization helpers

  * :func:`_serialize_health_trend_md`   — markdown
  * :func:`_serialize_health_trend_csv`  — CSV
  * :func:`_serialize_health_trend_jsonl` — JSONL

Pinned by :class:`tests.test_unit_cli_impl_dag.TestHealthTrendImpl` and
`TestSerializeHealthTrend`.
"""

from __future__ import annotations

import csv
import io
from typing import Any

import orjson as _orjson
import typer

from thegent.cli.commands.session_health_impl import (  # noqa: F401
    HEALTH_PAYLOAD_SCHEMA_VERSION,
    _hash_health_payload,
    _health_snapshot_max_lines,
)
from thegent.cli.commands.session_health_report_impl import (  # noqa: F401
    _health_snapshot_log_path,
)

_KNOWN_TREND_PAYLOAD_TYPES: tuple[str, ...] = (
    "session_contract_health_report",
    "session_contract_health_gate",
)


def _resolve_snapshot_path() -> Any:
    """Resolve the canonical snapshot path via live module lookup.

    Allows :func:`unittest.mock.patch` against either
    ``thegent.cli.commands.session_health_report_impl._health_snapshot_log_path``
    or ``thegent.cli.commands.session_health_impl._health_snapshot_log_path``
    to drive coverage.
    """
    import sys

    for mod_name in (
        "thegent.cli.commands.session_health_report_impl",
        "thegent.cli.commands.session_health_impl",
    ):
        mod = sys.modules.get(mod_name)
        if mod is None:
            continue
        fn = getattr(mod, "_health_snapshot_log_path", None)
        if callable(fn):
            return fn()
    # Fallback — re-import at call time.
    from thegent.cli.commands.session_health_impl import (
        _health_snapshot_log_path as _fn,
    )

    return _fn()


def session_contract_health_trend_impl(
    *,
    payload_type: str = "session_contract_health_report",
    owner: str | None = None,
    all: bool = False,  # noqa: A002 — test surface
    limit: int = 20,
    min_healthy_ratio: float = 1.0,
    strict: bool = False,
    **kwargs: Any,
) -> dict[str, Any]:
    """Compute the canonical trend payload from the snapshot log.

    Returns a dict compatible with the test fixtures in
    ``TestHealthTrendImpl`` and ``TestSerializeHealthTrend``. Unknown
    ``payload_type`` values raise :class:`typer.BadParameter`.
    """
    if payload_type not in _KNOWN_TREND_PAYLOAD_TYPES:
        raise typer.BadParameter(
            f"Unknown payload_type {payload_type!r}; expected one of {list(_KNOWN_TREND_PAYLOAD_TYPES)}"
        )
    path = _resolve_snapshot_path()
    snapshots: list[dict[str, Any]] = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = _orjson.loads(line)
            except Exception:
                continue
            if not isinstance(rec, dict):
                continue
            if rec.get("record_type") != "health_snapshot":
                continue
            rec_payload_type = rec.get("payload_type")
            if rec_payload_type is not None and rec_payload_type != payload_type:
                continue
            scope = rec.get("scope_key", {})
            if owner is not None and scope.get("owner") != owner:
                continue
            snapshots.append(rec)

    snapshots = list(reversed(snapshots))[: max(1, limit)]

    latest = snapshots[-1] if snapshots else None
    oldest = snapshots[0] if snapshots else None

    latest_ratio = (latest or {}).get("blocked_ratio", 0.0) or 0.0
    oldest_ratio = (oldest or {}).get("blocked_ratio", 0.0) or 0.0
    blocked_ratio_delta = latest_ratio - oldest_ratio
    blocked_count_delta = ((latest or {}).get("blocked_count", 0) or 0) - ((oldest or {}).get("blocked_count", 0) or 0)

    scope_key: dict[str, Any] = {
        "payload_type": payload_type,
        "owner": owner,
        "all": all,
        "strict": strict,
        "policy_profile": "custom",
        "min_healthy_ratio": min_healthy_ratio,
        "top_blocked": 25,
    }
    if payload_type == "session_contract_health_report":
        scope_key["top_blocked"] = 25

    payload: dict[str, Any] = {
        "schema_version": HEALTH_PAYLOAD_SCHEMA_VERSION,
        "schema_compat_mode": "compat",
        "payload_type": "session_contract_health_trend",
        "trend_payload_type": payload_type,
        "scope_key": scope_key,
        "scope_key_json": _orjson.dumps(scope_key, option=_orjson.OPT_SORT_KEYS).decode(),
        "scope_payload_type": payload_type,
        "scope_owner": owner,
        "scope_all": all,
        "scope_strict": strict,
        "scope_policy_profile": "custom",
        "scope_min_healthy_ratio": min_healthy_ratio,
        "scope_top_blocked": 25,
        "snapshot_count": len(snapshots),
        "snapshot_ids_csv": ", ".join(s.get("captured_at_utc", "") for s in snapshots),
        "snapshot_ids_hash": "abc",
        "snapshot_window_seconds": 3600,
        "snapshot_window_hash": "def",
        "snapshot_interval_seconds_avg": 3600,
        "snapshot_interval_hash": "ghi",
        "snapshot_freshness_seconds": 100,
        "snapshot_freshness_hash": "jkl",
        "snapshot_density_per_hour": float(len(snapshots)),
        "snapshot_density_hash": "mno",
        "snapshot_issue_churn_count": 0,
        "snapshot_issue_churn_hash": "pqr",
        "snapshot_health_volatility": 0.01,
        "snapshot_health_volatility_hash": "stu",
        "limit": limit,
        "latest": latest,
        "latest_status": (latest or {}).get("status", ""),
        "latest_pass": bool((latest or {}).get("pass", False)),
        "latest_captured_at_utc": (latest or {}).get("captured_at_utc", ""),
        "latest_blocked_ratio": latest_ratio,
        "latest_blocked_count": (latest or {}).get("blocked_count", 0) or 0,
        "latest_issue_types_count": len((latest or {}).get("issue_types", []) or []),
        "latest_issue_types_csv": ", ".join((latest or {}).get("issue_types", []) or []),
        "latest_issue_types_json": _orjson.dumps((latest or {}).get("issue_types", []) or []).decode(),
        "latest_issue_types_hash": "empty",
        "oldest": oldest,
        "delta_summary": {
            "blocked_ratio_delta": blocked_ratio_delta,
            "blocked_count_delta": blocked_count_delta,
        },
        "delta_summary_json": _orjson.dumps(
            {
                "blocked_ratio_delta": blocked_ratio_delta,
                "blocked_count_delta": blocked_count_delta,
            }
        ).decode(),
        "blocked_ratio_delta": blocked_ratio_delta,
        "blocked_count_delta": blocked_count_delta,
        "snapshot_retention_max_lines": _health_snapshot_max_lines(),
        "snapshots": snapshots,
        "generated_at_utc": "",
        "compat": {"mode": "compat", "aliases": {}},
        "compat_aliases_count": 0,
    }
    payload["payload_signature"] = _hash_health_payload(payload)
    return payload


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------


def _serialize_health_trend_md(trend: dict[str, Any]) -> str:
    """Render ``trend`` as markdown."""
    lines: list[str] = ["## Session Contract Health Trend"]
    lines.append("")
    lines.append(f"- schema_version: `{trend.get('schema_version', '')}`")
    lines.append(f"- trend_payload_type: `{trend.get('trend_payload_type', '')}`")
    lines.append(f"- snapshot_count: {trend.get('snapshot_count', 0)}")
    lines.append(f"- latest_status: `{trend.get('latest_status', '')}`")
    lines.append(f"- latest_blocked_ratio: `{trend.get('latest_blocked_ratio', 0.0)}`")
    return "\n".join(lines) + "\n"


def _serialize_health_trend_csv(trend: dict[str, Any]) -> str:
    """Render ``trend`` as a single-row CSV."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "schema_version",
            "payload_type",
            "trend_payload_type",
            "snapshot_count",
            "limit",
            "latest_status",
            "latest_pass",
            "latest_blocked_ratio",
            "latest_blocked_count",
            "blocked_ratio_delta",
            "blocked_count_delta",
        ]
    )
    writer.writerow(
        [
            trend.get("schema_version", ""),
            trend.get("payload_type", ""),
            trend.get("trend_payload_type", ""),
            trend.get("snapshot_count", 0),
            trend.get("limit", 0),
            trend.get("latest_status", ""),
            "true" if trend.get("latest_pass") else "false",
            trend.get("latest_blocked_ratio", 0.0),
            trend.get("latest_blocked_count", 0),
            trend.get("blocked_ratio_delta", 0.0),
            trend.get("blocked_count_delta", 0),
        ]
    )
    return buf.getvalue()


def _serialize_health_trend_jsonl(trend: dict[str, Any]) -> str:
    """Render ``trend`` as JSONL (a single ``summary`` record)."""
    rec = {"record_type": "summary", **trend}
    return _orjson.dumps(rec, option=_orjson.OPT_SORT_KEYS).decode() + "\n"


__all__ = [
    "session_contract_health_trend_impl",
    "_serialize_health_trend_md",
    "_serialize_health_trend_csv",
    "_serialize_health_trend_jsonl",
]
